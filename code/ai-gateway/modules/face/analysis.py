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
from modules.face.region_util import clamp_face_region, ema_bbox
from modules.shared.session_modules import is_module_enabled_for_session
from modules.face.schema import (
    build_face_features_guard,
    build_face_behavior_v1,
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
        self._last_debug_bbox: dict[str, tuple[int, int, int, int]] = {}

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
        face_behavior: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            **analysis_envelope(
                module="face",
                version=model_ver,
                stage="partial",
                trace_id=trace_id,
            ),
            "face_features": face_features,
        }
        if face_behavior is not None:
            payload["face_behavior"] = face_behavior
        face_out = {
            "type": "face_analysis",
            "session_id": session_id,
            "participant_id": participant_id,
            "payload": payload,
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
            data={
                "face_features": face_features,
                **({"face_behavior": face_behavior} if face_behavior is not None else {}),
            },
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

    async def _emit_face_debug(
        self,
        *,
        ws: Any,
        session_id: Any,
        participant_id: Any,
        ts: Any,
        trace_id: str,
        frame_w: int,
        frame_h: int,
        dominant: str,
        model_confidence: float,
        gate_passed: bool,
        skip_reason: str | None,
        min_confidence: float,
        region_x: int | None,
        region_y: int | None,
        region_w: int | None,
        region_h: int | None,
    ) -> None:
        region = None
        landmarks: list[dict[str, int]] = []
        if (
            region_x is not None
            and region_y is not None
            and region_w is not None
            and region_h is not None
            and region_w > 0
            and region_h > 0
        ):
            region = {"x": region_x, "y": region_y, "w": region_w, "h": region_h}
            # DeepFace does not return dense landmarks; expose stable anchor points for UI overlay.
            landmarks = [
                {"x": region_x, "y": region_y},
                {"x": region_x + region_w, "y": region_y},
                {"x": region_x, "y": region_y + region_h},
                {"x": region_x + region_w, "y": region_y + region_h},
                {"x": region_x + region_w // 2, "y": region_y + region_h // 2},
            ]
        dbg = {
            "type": "face_debug",
            "session_id": session_id,
            "participant_id": participant_id,
            "payload": {
                "trace_id": trace_id,
                "frame_width": frame_w,
                "frame_height": frame_h,
                "region": region,
                "landmarks": landmarks,
                "dominant_emotion": dominant,
                "model_confidence": round(float(model_confidence), 4),
                "gate_passed": gate_passed,
                "skip_reason": skip_reason,
                "min_confidence": float(min_confidence),
            },
            "timestamp": ts,
        }
        await ws.send(json.dumps(dbg))
        incr("face_debug_sent")

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
        if not is_module_enabled_for_session(int(session_id), "face"):
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
            region_x = norm.get("region_x")
            region_y = norm.get("region_y")
            rx_i = region_x if isinstance(region_x, int) else None
            ry_i = region_y if isinstance(region_y, int) else None
            rw_i = region_w if isinstance(region_w, int) else None
            rh_i = region_h if isinstance(region_h, int) else None

            fh, fw = int(img_bgr.shape[0]), int(img_bgr.shape[1])
            clamp_plain: tuple[int, int, int, int] | None = None
            if rx_i is not None and ry_i is not None and rw_i is not None and rh_i is not None:
                clamp_plain = clamp_face_region(
                    rx_i,
                    ry_i,
                    rw_i,
                    rh_i,
                    fw,
                    fh,
                    max_area_frac=fp.debug_max_face_area_frac,
                )
            rv_w = clamp_plain[2] if clamp_plain else None
            rv_h = clamp_plain[3] if clamp_plain else None

            skip_reason: str | None = None
            face_features = None
            if confidence_val < fp.min_confidence:
                skip_reason = "low_confidence"
            else:
                face_features = build_face_features_positive(
                    dominant=str(dominant),
                    probs=probs,
                    confidence=confidence_val,
                    region_w=rv_w,
                    region_h=rv_h,
                    min_face_side_px=fp.min_face_side_px,
                )
                if face_features is None:
                    skip_reason = "small_region"

            gate_passed = face_features is not None
            face_behavior: dict[str, Any] | None = None
            if fp.emit_face_behavior:
                provider_name = mod.provider or "deepface"
                face_behavior = build_face_behavior_v1(
                    provider=provider_name,
                    schema_version=fp.face_behavior_schema_version,
                    confidence=confidence_val,
                    probs=probs,
                    face_detected=gate_passed,
                    guard_reason=skip_reason,
                    min_face_side_px=fp.min_face_side_px if fp.min_face_side_px > 0 else None,
                )

            if fp.emit_debug_face:
                dx = dy = dw = dh = None
                if clamp_plain:
                    bx = clamp_plain
                    alpha = fp.debug_bbox_smooth_alpha
                    if alpha > 0:
                        bx = ema_bbox(self._last_debug_bbox.get(key), clamp_plain, alpha)
                        self._last_debug_bbox[key] = bx
                    else:
                        self._last_debug_bbox[key] = bx
                    dx, dy, dw, dh = bx
                await self._emit_face_debug(
                    ws=ws,
                    session_id=session_id,
                    participant_id=participant_id,
                    ts=ts,
                    trace_id=trace_id,
                    frame_w=fw,
                    frame_h=fh,
                    dominant=str(dominant),
                    model_confidence=confidence_val,
                    gate_passed=gate_passed,
                    skip_reason=skip_reason,
                    min_confidence=fp.min_confidence,
                    region_x=dx,
                    region_y=dy,
                    region_w=dw,
                    region_h=dh,
                )

            if skip_reason == "low_confidence":
                incr("face_low_confidence_skipped")
                log_event(
                    "face_low_confidence",
                    trace_id=trace_id,
                    module="face",
                    extra={"confidence": round(float(confidence_val), 4)},
                )
                return

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
                face_behavior=face_behavior,
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
            if fp.log_face_inference:
                log_event("face_inference", trace_id=trace_id, module="face")
        except Exception as e:
            incr("face_inference_errors")
            log_event("face_pipeline_failed", trace_id=trace_id, module="face", extra={"err": str(e)[:200]})
            print("[FRAME] emotion inference failed:", e)


plugin = FaceAnalysisPlugin()
