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
from observability import incr, log_event


class FramePlugin:
    name = "frame"
    priority = 100

    def __init__(self) -> None:
        self._last_inference_ts: dict[str, float] = {}

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "frame"

    async def process(self, msg: dict[str, Any], ws: Any) -> None:
        cfg = get_gateway_config()
        mod = cfg.module("face")
        if not mod or not mod.enabled:
            return
        params = mod.params or {}

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

        # Throttle inference frequency per participant to reduce CPU/GPU load.
        min_interval_sec = float(params.get("min_interval_sec", 0.0))
        key = f"{session_id}:{participant_id}"
        now = time.monotonic()
        last_ts = self._last_inference_ts.get(key, 0.0)
        if min_interval_sec > 0 and (now - last_ts) < min_interval_sec:
            incr("face_throttled")
            return
        self._last_inference_ts[key] = now

        trace_id = build_trace_id()
        model_ver = mod.model or "emotion-v1"

        try:
            b64_part = frame_data_url.split(",", 1)[1]
            frame_bytes = base64.b64decode(b64_part)

            img_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img_bgr is None:
                return

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            result = DeepFace.analyze(
                img_rgb,
                actions=["emotion"],
                enforce_detection=False,
                detector_backend="opencv",
                align=False,
                silent=True,
            )

            if not isinstance(result, list) or not result:
                return

            obj = result[0]
            dominant = obj.get("dominant_emotion")
            probs = obj.get("emotion")

            if not isinstance(dominant, str) or not isinstance(probs, dict):
                return

            confidence_val = probs.get(dominant, 0)
            if not isinstance(confidence_val, (int, float)):
                confidence_val = 0

            min_confidence = float(params.get("min_confidence", 0.0))
            if confidence_val < min_confidence:
                incr("face_low_confidence_skipped")
                log_event(
                    "face_low_confidence",
                    trace_id=trace_id,
                    module="face",
                    extra={"confidence": round(float(confidence_val), 4)},
                )
                return

            face_features = {
                "dominant_emotion": dominant,
                "probs": probs,
                "face_detected": True,
                "confidence": confidence_val,
            }

            get_feature_store().push(
                int(session_id),
                kind="face",
                participant_id=str(participant_id),
                trace_id=trace_id,
                data={"face_features": face_features},
            )

            ts = msg.get("timestamp")
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
            log_event("face_inference", trace_id=trace_id, module="face")
        except Exception as e:
            incr("face_inference_errors")
            print("[FRAME] emotion inference failed:", e)


plugin = FramePlugin()
