import asyncio
import json
import websockets
from typing import Awaitable, Callable, Any


class SessionWSClient:
    def __init__(
        self,
        url: str,
        on_message: Callable[[dict, websockets.WebSocketClientProtocol], Awaitable[None]],
    ):
        self.url = url
        self.on_message = on_message

    async def connect(self):
        backoff = 1
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    print(f"[WS] connected to {self.url}")
                    backoff = 1

                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            print("[WS] invalid json:", raw)
                            continue

                        await self.on_message(msg, ws)
            except Exception as e:
                print(f"[WS] connect failed: {e} (retry in {backoff}s)")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
