import asyncio
import os

from ws_client import SessionWSClient
from handlers import handle_message


async def main():
    session_id = os.getenv("SESSION_ID", "2")
    ws_base_url = os.getenv("BACKEND_WS_BASE_URL", "ws://localhost:8080")
    ws_url = f"{ws_base_url}/ws/sessions/{session_id}"

    client = SessionWSClient(
        url=ws_url,
        on_message=handle_message,
    )

    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())
