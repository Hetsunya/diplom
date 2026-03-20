import asyncio
import base64
import io
import json

import websockets
from PIL import Image

from handlers import handle_message
from ws_client import SessionWSClient


PORT = 8765
SESSION_ID = 1
PARTICIPANT_ID = "p_smoke"


clients: set[websockets.WebSocketServerProtocol] = set()


async def broadcast_server_handler(ws: websockets.WebSocketServerProtocol):
    clients.add(ws)
    try:
        async for raw in ws:
            # Broadcast everything (mimics backend hub broadcast).
            dead = []
            for c in clients:
                try:
                    if c.open:
                        await c.send(raw)
                except Exception:
                    dead.append(c)
            for c in dead:
                clients.discard(c)
    finally:
        clients.discard(ws)


async def main():
    server = await websockets.serve(broadcast_server_handler, "127.0.0.1", PORT)

    # Start ai-gateway client (connects as a WS consumer of incoming messages).
    gateway_url = f"ws://127.0.0.1:{PORT}/ws/sessions/{SESSION_ID}"
    gateway = SessionWSClient(url=gateway_url, on_message=handle_message)
    gateway_task = asyncio.create_task(gateway.connect())

    # Test client.
    emotion_msg = None

    async with websockets.connect(gateway_url) as test_ws:
        # join (not required for emotion inference, but keeps state consistent)
        await test_ws.send(
            json.dumps(
                {
                    "type": "join",
                    "session_id": SESSION_ID,
                    "participant_id": PARTICIPANT_ID,
                    "payload": {"name": "Smoke"},
                    "timestamp": "2026-01-01T00:00:00Z",
                }
            )
        )

        # Create a tiny JPEG and send as data URL.
        img = Image.new("RGB", (224, 224), (0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        data_url = "data:image/jpeg;base64," + b64

        await test_ws.send(
            json.dumps(
                {
                    "type": "frame",
                    "session_id": SESSION_ID,
                    "participant_id": PARTICIPANT_ID,
                    "payload": {"frame": data_url},
                    "timestamp": "2026-01-01T00:00:00Z",
                }
            )
        )

        # Wait for an emotion message that came from ai-gateway.
        for _ in range(50):
            raw = await asyncio.wait_for(test_ws.recv(), timeout=2.0)
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "emotion":
                emotion_msg = msg
                break

    # Stop server (and gateway task best-effort).
    server.close()
    await server.wait_closed()
    gateway_task.cancel()
    try:
        await gateway_task
    except Exception:
        pass

    if not emotion_msg:
        raise RuntimeError("No emotion message received from ai-gateway.")

    payload = emotion_msg.get("payload") or {}
    print("OK: received emotion:", emotion_msg.get("participant_id"), payload.get("emotion"), payload.get("confidence"))


if __name__ == "__main__":
    asyncio.run(main())

