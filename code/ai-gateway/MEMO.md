# AI Gateway Memo

## Purpose

`ai-gateway` is a standalone WebSocket worker that subscribes to meeting session events, runs AI processing, and sends analysis events back to the backend broadcast channel.

Current source entrypoint: `main.py`.

## Configuration (modular)

- Default module toggles and providers: [`modules.default.json`](modules.default.json).
- Override path: env `AI_GATEWAY_MODULES_CONFIG` → path to JSON with the same `modules` shape.
- Keys: `text`, `audio`, `face`, `report` — each has `enabled`, `provider`, `model`, `params`.
- Text/ASR: set `modules.text.enabled=true` and `modules.text.params.speech_service_url` to a running [`speech-service`](../speech-service/) (or your ASR HTTP API compatible with `adapters/speech_service.py`).
- Text/ASR retry controls:
  - `modules.text.params.timeout_sec`
  - `modules.text.params.retries`
  - `modules.text.params.backoff_sec`
- Report: `modules.report.params.interval_sec` (min 5s enforced in code), `own_nn_url` optional (`POST {url}/v1/report`).
- Face quality/performance controls:
  - `modules.face.params.min_interval_sec` (throttling per participant)
  - `modules.face.params.min_confidence` (skip low-confidence inference results)

Loader: [`gateway_config.py`](gateway_config.py). Snapshot for reports: `config_snapshot()`.

## Current Runtime Flow

1. `main.py` loads config (`load_gateway_config` / `set_gateway_config`), builds WS URL from `BACKEND_WS_BASE_URL` + `SESSION_ID`.
2. `SessionWSClient` (`ws_client.py`): token via `POST /auth/token`, `Authorization` on WS, reconnect backoff.
3. If `report` module enabled: background `report_loop` sends periodic `analysis_report_partial` on the same socket.
4. `handle_message` (`handlers.py`): runs **all** plugins whose `can_handle` matches, sorted by `priority` (lower runs first).
5. Plugins send results with `ws.send(...)`; see v1 contracts in [`../docs/ANALYSIS_WS_CONTRACTS.md`](../docs/ANALYSIS_WS_CONTRACTS.md) and [`CONTRACTS.md`](CONTRACTS.md).
6. Before sending `face_analysis` / `audio_analysis` / `text_analysis`, gateway validates required v1 envelope fields: `module`, `version`, `stage`, `trace_id`.

## Implemented Plugins

| Plugin | Priority | Behavior |
|--------|----------|----------|
| `ping.py` | 50 | Metrics + log for backend heartbeats |
| `frame.py` | 100 | DeepFace → `face_analysis` (v1 envelope) + legacy `emotion` |
| `audio.py` | 150 | Optional `audio_analysis` stub; optional speech HTTP → `text_analysis` |

## Observability

- [`observability.py`](observability.py): counters (`incr`), structured `log_event`, `snapshot_metrics()`.
- Use `trace_id` from v1 payloads for correlation (see contracts).

## Backend Integration

- WS: `GET /ws/sessions/:id` (auth). Analytics inbound types are registered for **persist + broadcast**: `text_analysis`, `audio_analysis`, `face_analysis`, `analysis_report`, `analysis_report_partial`, `emotion` (legacy).
- REST (after migration `007_analysis`): `GET /sessions/:id/analysis/report`, `GET /sessions/:id/analysis/events?limit=`.

## Local Run Checklist

1. Env (see `.env.example`): `BACKEND_WS_BASE_URL`, `SESSION_ID`, `AI_GATEWAY_EMAIL`, `AI_GATEWAY_PASSWORD`, optional `AI_GATEWAY_MODULES_CONFIG`.
2. `pip install -r requirements.txt`
3. Apply DB migration `007_analysis` on Postgres.
4. `python main.py`
5. Optional: `python smoke_ws_emotion_test.py` → expects both `face_analysis` and legacy `emotion`.

## How To Add a New Plugin

1. Add `plugins/<name>.py` exporting `plugin = ...` with `name`, `priority`, `can_handle`, `async process`.
2. Follow v1 envelope in outbound `payload` (`module`, `stage`, `trace_id`, `version`) — document in `docs/ANALYSIS_WS_CONTRACTS.md`.
3. Register new `type` on backend in `internal/session/ws_handler.go` + `internal/analysis` if it should be persisted.
