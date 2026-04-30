# Analysis pipeline — observability & SLO hints

## ai-gateway

- **Logs**: `observability.log_event(event, trace_id=..., module=..., extra=...)`.
- **Counters**: `observability.incr("metric_name")` — use `snapshot_metrics()` for periodic dumps or health.
- **Correlation**: every v1 outbound message should include `payload.trace_id` (UUID). Propagate the same `trace_id` when a module chains work (e.g. audio chunk → speech-service → `text_analysis`).
- **Latency**: wrap ML / HTTP calls with `t0 = monotonic_ms()` and log `latency_ms` on completion (see `report_loop`).

## Suggested SLO targets (tune per deployment)

| Stage | Target | Notes |
|-------|--------|--------|
| `face_analysis` partial | \< 500 ms p95 | depends on DeepFace / GPU |
| `audio_analysis` partial | \< 100 ms p95 | DSP-only baseline |
| `text_analysis` partial | \< 2 s p95 | ASR network + model |
| `analysis_report_partial` | interval-based | default 30 s; min 5 s in code |
| End-to-end final report | post-meeting async | own NN `POST /v1/report` timeout default 60 s |

## emeeting-backend

- Persist failures are logged as `[ANALYSIS] validate skipped store: ...` (invalid v1 payload) without closing the WS.
- REST: use `GET /sessions/:id/analysis/events` for debugging timelines.
