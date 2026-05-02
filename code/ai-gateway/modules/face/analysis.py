import asyncio
import base64
import json
import time
from typing import Any

import cv2
import numpy as np
from deepface import DeepFace

from contracts import analysis_envelope, build_trace_id, has_required_envelope_fields
from feature_store import get_feature_store
from gateway_config import get_gateway_config
from modules.face.frame_quality import should_skip_blurry_frame
from modules.face.params import FaceRuntimeParams
from modules.face.schema import (
    build_face_features_guard,
    build_face_features_positive,
    is_no_face_deepface_error,
    normalize_deepface_result,
)
from observability import incr, log_event, monotonic_ms, observe_module_latency

_face_sem: asyncio.Semaphore | None = None
_face_sem_capacity: int = -1


def _ensure_face_sem(capacity: int) -> asyncio.Semaphore:
    global _face_sem, _face_sem_capacity
    cap = max(1, int(capacity))
    if _face_sem is None or _face_sem_capacity != cap:
        _face_sem = asyncio.Semaphore(cap)
        _face_sem_capacity = cap
    return _face_sem


def _deepface_emotion_sync(img_rgb: Any, fp: FaceRuntimeParams) -> Any:
    return DeepFace.analyze(
        img_rgb,
        actions=["emotion"],
        enforce_detection=fp.enforce_detection,
        detector_backend=fp.detector_backend,
        align=fp.align,
        silent=True,
    )


class FaceAnalysisPlugin:
    name = "face"
    priority = 100

    def __init__(self) -> None:
        self._last_inference_ts: dict[str, float] = {}

    def metadata(self) -> dict[str, str]:
        cfg = get_gateway_config()
        m = cfg.module("face")
        return {
            "module": self.name,
            "provider": (m.provider if m else ""),
            "model": (m.model if m else ""),
            "version": (m.model if m else "emotion-v1"),
        }

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "frame"

    async def _emit_face_analysis(
        self,
        *,
        ws: Any,
        session_id: Any,
        participant_id: Any,
        ts: Any,
        model_ver: str,
        trace_id: str,
        face_features: dict[str, Any],
    ) -> None:
        face_out = {
            "type": "face_analysis",
            "session_id": session_id,
            "participant_id": participant_id,
            "payload": {
                **analysis_envelope(
                    module="face",
                    version=model_ver,
                    stage="partial",
                    trace_id=trace_id,
                ),
                "face_features": face_features,
            },
            "timestamp": ts,
        }
        if not has_required_envelope_fields(face_out["payload"]):
            incr("face_contract_invalid")
            return
        await ws.send(json.dumps(face_out))
        incr("face_analysis_sent")
        get_feature_store().push(
            int(session_id),
            kind="face",
            participant_id=str(participant_id),
            trace_id=trace_id,
            data={"face_features": face_features},
        )

    async def _emit_legacy_emotion(
        self,
        *,
        ws: Any,
        session_id: Any,
        participant_id: Any,
        ts: Any,
        dominant: str,
        confidence_val: float,
        probs: dict[str, Any],
    ) -> None:
        legacy = {
            "type": "emotion",
            "session_id": session_id,
            "participant_id": participant_id,
            "payload": {
                "emotion": dominant,
                "confidence": confidence_val,
                "probs": probs,
            },
            "timestamp": ts,
        }
        await ws.send(json.dumps(legacy))
        incr("emotion_legacy_sent")

    async def process(self, msg: dict[str, Any], ws: Any) -> None:
        cfg = get_gateway_config()
        mod = cfg.module("face")
        if not mod or not mod.enabled:
            return
        fp = FaceRuntimeParams.from_dict(mod.params or {})

        payload = msg.get("payload") or {}
        frame_data_url = None
        if isinstance(payload, dict):
            frame_data_url = payload.get("frame")

        if not isinstance(frame_data_url, str) or "," not in frame_data_url:
            return

        session_id = msg.get("session_id")
        participant_id = msg.get("participant_id")
        if session_id is None or participant_id is None:
            return

        key = f"{session_id}:{participant_id}"
        now = time.monotonic()
        last_ts = self._last_inference_ts.get(key, 0.0)
        if fp.min_interval_sec > 0 and (now - last_ts) < fp.min_interval_sec:
            incr("face_throttled")
            return
        self._last_inference_ts[key] = now

        trace_id = build_trace_id()
        model_ver = mod.model or "emotion-v1"
        ts = msg.get("timestamp")

        try:
            b64_part = frame_data_url.split(",", 1)[1]
            frame_bytes = base64.b64decode(b64_part)

            img_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img_bgr is None:
                incr("face_decode_failed")
                return

            if should_skip_blurry_frame(img_bgr, fp.min_laplacian_var):
                incr("face_blur_skipped")
                log_event("face_blur_skip", trace_id=trace_id, module="face")
                return

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            try:
                sem = _ensure_face_sem(fp.max_concurrent_inferences)
                t0 = monotonic_ms()
                async with sem:
                    result = await asyncio.to_thread(_deepface_emotion_sync, img_rgb, fp)
                observe_module_latency("face", monotonic_ms() - t0)
            except Exception as exc:
                if fp.emit_no_face_face_analysis and is_no_face_deepface_error(exc):
                    ff = build_face_features_guard(reason="no_face")
                    await self._emit_face_analysis(
                        ws=ws,
                        session_id=session_id,
                        participant_id=participant_id,
                        ts=ts,
                        model_ver=model_ver,
                        trace_id=trace_id,
                        face_features=ff,
                    )
                    incr("face_no_face_event")
                    log_event("face_no_face", trace_id=trace_id, module="face")
                else:
                    incr("face_inference_errors")
                    log_event(
                        "face_inference_failed",
                        trace_id=trace_id,
                        module="face",
                        extra={"err": str(exc)[:200]},
                    )
                    print("[FRAME] emotion inference failed:", exc)
                return

            norm = normalize_deepface_result(result)
            if not norm:
                incr("face_invalid_result")
                return

            dominant = norm["dominant_emotion"]
            probs = norm["probs"]
            confidence_val = float(norm["confidence"])
            region_w = norm.get("region_w")
            region_h = norm.get("region_h")

            if confidence_val < fp.min_confidence:
                incr("face_low_confidence_skipped")
                log_event(
                    "face_low_confidence",
                    trace_id=trace_id,
                    module="face",
                    extra={"confidence": round(float(confidence_val), 4)},
                )
                return

            face_features = build_face_features_positive(
                dominant=str(dominant),
                probs=probs,
                confidence=confidence_val,
                region_w=region_w if isinstance(region_w, int) else None,
                region_h=region_h if isinstance(region_h, int) else None,
                min_face_side_px=fp.min_face_side_px,
            )
            if face_features is None:
                incr("face_small_region_skipped")
                log_event("face_small_region", trace_id=trace_id, module="face")
                return

            await self._emit_face_analysis(
                ws=ws,
                session_id=session_id,
                participant_id=participant_id,
                ts=ts,
                model_ver=model_ver,
                trace_id=trace_id,
                face_features=face_features,
            )

            await self._emit_legacy_emotion(
                ws=ws,
                session_id=session_id,
                participant_id=participant_id,
                ts=ts,
                dominant=str(dominant),
                confidence_val=confidence_val,
                probs=probs,
            )
            log_event("face_inference", trace_id=trace_id, module="face")
        except Exception as e:
            incr("face_inference_errors")
            log_event("face_pipeline_failed", trace_id=trace_id, module="face", extra={"err": str(e)[:200]})
            print("[FRAME] emotion inference failed:", e)


plugin = FaceAnalysisPlugin()
