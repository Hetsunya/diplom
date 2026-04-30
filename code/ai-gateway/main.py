import asyncio
import os

from gateway_config import get_gateway_config, set_gateway_config, load_gateway_config
from ws_client import SessionWSClient
from handlers import handle_message


async def main():
    set_gateway_config(load_gateway_config())
    cfg = get_gateway_config()
    report_on = bool(cfg.module("report") and cfg.module("report").enabled)

    session_id = int(os.getenv("SESSION_ID", "2"))
    ws_base_url = os.getenv("BACKEND_WS_BASE_URL", "ws://localhost:8080")
    ws_url = f"{ws_base_url}/ws/sessions/{session_id}"

    client = SessionWSClient(
        url=ws_url,
        on_message=handle_message,
        session_id=session_id,
        enable_report_loop=report_on,
    )

    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())
