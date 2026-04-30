from __future__ import annotations

import asyncio
import json
import os
import urllib.request
import urllib.error
import websockets
from typing import Awaitable, Callable, Any


class SessionWSClient:
    def __init__(
        self,
        url: str,
        on_message: Callable[[dict, websockets.WebSocketClientProtocol], Awaitable[None]],
        session_id: int = 0,
        enable_report_loop: bool = True,
    ):
        self.url = url
        self.on_message = on_message
        self.session_id = session_id
        self.enable_report_loop = enable_report_loop
        self.access_token: str | None = None

    def _http_base(self) -> str:
        # ws://backend:8080 -> http://backend:8080
        if self.url.startswith("ws://"):
            return "http://" + self.url[len("ws://") :].split("/ws/")[0]
        if self.url.startswith("wss://"):
            return "https://" + self.url[len("wss://") :].split("/ws/")[0]
        # fallback
        return "http://backend:8080"

    def _fetch_access_token(self) -> str | None:
        email = os.getenv("AI_GATEWAY_EMAIL", "demo1@example.com")
        password = os.getenv("AI_GATEWAY_PASSWORD", "demo1pass")
        body = json.dumps({"email": email, "password": password}).encode("utf-8")

        req = urllib.request.Request(
            self._http_base() + "/auth/token",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("accessToken")
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"[AUTH] failed to fetch token: {e}")
            return None

    async def connect(self):
        backoff = 1
        while True:
            try:
                if not self.access_token:
                    self.access_token = self._fetch_access_token()

                headers = None
                if self.access_token:
                    headers = {"Authorization": f"Bearer {self.access_token}"}

                async with websockets.connect(self.url, additional_headers=headers) as ws:
                    print(f"[WS] connected to {self.url}")
                    backoff = 1

                    bg_tasks: list[asyncio.Task[Any]] = []
                    if self.enable_report_loop and self.session_id > 0:
                        from report_loop import report_loop

                        holder: list[Any] = [ws]
                        bg_tasks.append(
                            asyncio.create_task(
                                report_loop(holder, self.session_id),
                                name="report_loop",
                            )
                        )

                    try:
                        async for raw in ws:
                            try:
                                msg = json.loads(raw)
                            except json.JSONDecodeError:
                                print("[WS] invalid json:", raw)
                                continue

                            await self.on_message(msg, ws)
                    finally:
                        for t in bg_tasks:
                            t.cancel()
                        if bg_tasks:
                            await asyncio.gather(*bg_tasks, return_exceptions=True)
            except Exception as e:
                print(f"[WS] connect failed: {e} (retry in {backoff}s)")
                self.access_token = None
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
