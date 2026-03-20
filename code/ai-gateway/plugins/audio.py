from typing import Any


class AudioPlugin:
    name = "audio"

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "audio"

    async def process(self, msg: dict[str, Any], ws: Any) -> None:
        payload = msg.get("payload")
        _ = payload
        print("[AUDIO] received audio chunk")


plugin = AudioPlugin()

