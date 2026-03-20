from typing import Any


class PingPlugin:
    name = "ping"

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "ping"

    async def process(self, msg: dict[str, Any]) -> None:
        # Backend sends: { type: "ping", session_id: <id>, timestamp: ... }
        session_id = msg.get("session_id")
        print(f"[PING] session={session_id}")


plugin = PingPlugin()

