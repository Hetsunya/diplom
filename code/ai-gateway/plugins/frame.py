from typing import Any


class FramePlugin:
    name = "frame"

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "frame"

    async def process(self, msg: dict[str, Any]) -> None:
        payload = msg.get("payload") or {}
        # payload example:
        # { "participant_id": "...", "frame": "base64..." }
        print("[FRAME] received frame")
        # TODO: decode -> inference using payload


plugin = FramePlugin()

