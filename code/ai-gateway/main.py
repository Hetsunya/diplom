import asyncio

from ws_client import SessionWSClient
from handlers import handle_message


async def main():
    session_id = 2
    ws_url = f"ws://localhost:8080/ws/sessions/{session_id}"

    client = SessionWSClient(
        url=ws_url,
        on_message=handle_message,
    )

    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())
