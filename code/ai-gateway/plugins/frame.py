import base64
import io
import json
from typing import Any

import cv2
import numpy as np
from deepface import DeepFace


class FramePlugin:
    name = "frame"

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "frame"

    async def process(self, msg: dict[str, Any], ws: Any) -> None:
        payload = msg.get("payload") or {}
        # payload example:
        # { "participant_id": "...", "frame": "data:image/jpeg;base64,..." }
        frame_data_url = None
        if isinstance(payload, dict):
            frame_data_url = payload.get("frame")

        if not isinstance(frame_data_url, str) or "," not in frame_data_url:
            return

        session_id = msg.get("session_id")
        participant_id = msg.get("participant_id")
        if session_id is None or participant_id is None:
            return

        try:
            b64_part = frame_data_url.split(",", 1)[1]
            frame_bytes = base64.b64decode(b64_part)

            # Decode into an image (OpenCV uses BGR by default)
            img_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img_bgr is None:
                return

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # DeepFace returns: [{ 'dominant_emotion': ..., 'emotion': {..}, ... }]
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

            # Send back to backend as an `emotion` event. Backend will broadcast to UI.
            out = {
                "type": "emotion",
                "session_id": session_id,
                "participant_id": participant_id,
                "payload": {
                    "emotion": dominant,
                    "confidence": confidence_val,
                    "probs": probs,
                },
                "timestamp": msg.get("timestamp"),
            }
            await ws.send(json.dumps(out))
        except Exception as e:
            # Never crash the gateway due to ML errors.
            print("[FRAME] emotion inference failed:", e)


plugin = FramePlugin()

