# Analysis WebSocket contracts (v1)

All analysis-related messages use the shared envelope compatible with `emeeting-backend` `WSMessage`:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Event type (see below) |
| `session_id` | number | Meeting session id |
| `participant_id` | string | Optional participant key |
| `payload` | object | Type-specific body |
| `timestamp` | RFC3339 string | Event time (may be propagated from source) |

## Envelope fields inside `payload` (required for new analytics types)

Legacy `emotion` events are exempt.

| Field | Type | Description |
|-------|------|-------------|
| `module` | `text` \| `audio` \| `face` \| `report` | Source module |
| `stage` | `partial` \| `final` | Hybrid pipeline stage |
| `trace_id` | string | Correlation id across modules |
| `version` | string | Model / algorithm version |

## Event types

### `text_analysis`

ASR + NLP (produced by speech pipeline / `ai-gateway` after speech-service).

`payload` extensions:

- `transcript_partial` (string, optional)
- `transcript_final` (string, optional)
- `language` (string, optional)
- `text_features` (object, optional): e.g. `sentiment`, `topics`, `confidence`

### `audio_analysis`

Low-level voice / prosody features (not raw transcript).

- `audio_features` (object): energy, tempo, pause_ratio, etc.

### `face_analysis`

Facial emotion / presence.

- `face_features` (object): `dominant_emotion`, `probs`, `face_detected`, `confidence`

### `emotion` (legacy alias)

Same semantics as dominant face emotion for UI backwards compatibility.

Gateways **may** emit both `face_analysis` and `emotion` for the same frame.

### `analysis_report` / `analysis_report_partial`

Aggregated report from the report orchestrator / own NN.

- `report` (object): meeting-level + per-participant sections
- `model_version` (string)
- `generated_at` (RFC3339)
- `config_snapshot` (object, optional): effective `modules.*` config at generation time
- `report_source` (`remote` | `local_fallback` | `local_stub`): origin of report body

Current stub orchestrator may include inside `report` (optional):

- `pipeline_stage` (`idle` | `listening` | `transcribing` | `visual_only`)
- `speech_ratio` (number, 0..1 proxy)
- `participants[]` entries with fields such as
  `audio_chunks`, `avg_speech_activity_proxy`, `avg_bitrate_kbps`, `last_emotion`, `last_transcript`

## trace_id

Clients and services should attach one `trace_id` per logical utterance or per batch (e.g. UUID). The report orchestrator uses it to join partial features before calling the final NN.
