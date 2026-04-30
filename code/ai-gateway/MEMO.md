# AI Gateway Memo

## Purpose

`ai-gateway` is a standalone WebSocket worker that subscribes to meeting session events, runs AI processing, and sends analysis events back to the backend broadcast channel.

Current source entrypoint: `main.py`.

## Current Runtime Flow

1. `main.py` builds WS URL:
   - `BACKEND_WS_BASE_URL` (default `ws://localhost:8080`)
   - `SESSION_ID` (default `2`)
   - final URL: `/ws/sessions/{SESSION_ID}`
2. `SessionWSClient` (`ws_client.py`):
   - requests access token via `POST /auth/token`
   - uses `Authorization: Bearer <token>` for WS connect
   - reconnects with exponential backoff (`1s -> ... -> 30s`)
3. Every incoming WS message is passed into `handle_message` (`handlers.py`).
4. `handlers.py` auto-discovers `plugins/*` and routes message to the first plugin where `can_handle(msg) == true`.
5. Plugin can send analysis result back to backend through the same socket (`ws.send(...)`).

## Implemented Plugins

- `plugins/frame.py`
  - Handles `type == "frame"`.
  - Expects payload with image Data URL: `payload.frame = "data:image/jpeg;base64,..."`.
  - Runs DeepFace emotion inference.
  - Sends event back:
    - `type: "emotion"`
    - `session_id`, `participant_id`, `timestamp`
    - `payload: { emotion, confidence, probs }`

- `plugins/audio.py`
  - Handles `type == "audio"`.
  - Stub only; no analysis yet.

- `plugins/ping.py`
  - Handles `type == "ping"`.
  - Logs heartbeat only.

## Message Contract (in practice)

Incoming frame message:

```json
{
  "type": "frame",
  "session_id": 1,
  "participant_id": "p1",
  "payload": {
    "frame": "data:image/jpeg;base64,..."
  },
  "timestamp": "2026-01-01T00:00:00Z"
}
```

Outgoing emotion message:

```json
{
  "type": "emotion",
  "session_id": 1,
  "participant_id": "p1",
  "payload": {
    "emotion": "neutral",
    "confidence": 75.2,
    "probs": {
      "neutral": 75.2
    }
  },
  "timestamp": "2026-01-01T00:00:00Z"
}
```

## Backend Integration Notes

- Backend WS endpoint: `GET /ws/sessions/:id`.
- Backend broadcasts most message types by default, including:
  - `frame`
  - unknown custom types (fallback broadcast path)
- This means new analysis modules can publish their own event types without backend code changes, as long as frontend can consume them.
- WS endpoint is auth-protected; gateway authenticates with `/auth/token`.

## Local Run Checklist

1. Configure env variables (example in `.env.example`):
   - `BACKEND_WS_BASE_URL`
   - `SESSION_ID`
   - plus credentials expected by `ws_client.py`:
     - `AI_GATEWAY_EMAIL`
     - `AI_GATEWAY_PASSWORD`
2. Install dependencies from `requirements.txt`.
3. Start gateway:
   - `python main.py`
4. Optional smoke test:
   - `python smoke_ws_emotion_test.py`
   - should print `OK: received emotion: ...`

## Notes from Current Verification

- In this environment, runtime execution is blocked because Python package manager and runtime deps are not available (`websockets` missing, no `pip` installed).
- Code-level verification confirms:
  - reconnect/auth logic is wired
  - plugin auto-discovery works
  - `frame -> emotion` path is implemented end-to-end in code

## How To Add New Analysis Module

1. Create `plugins/<module_name>.py`.
2. Implement plugin object with:
   - `can_handle(msg) -> bool`
   - `async process(msg, ws) -> None`
3. Export instance as module-level `plugin = <PluginClass>()`.
4. Pick a unique outgoing `type` (example: `speech_sentiment`, `attention_score`, `summary_chunk`).
5. Keep processing exception-safe (do not crash gateway loop).
6. Keep payload schema stable and document it for frontend.

