# Speech service (ASR stub)

HTTP service expected by `ai-gateway` (`adapters/speech_service.py`).

## API

`POST /v1/transcribe`

Request JSON:

```json
{
  "session_id": 1,
  "participant_id": "p1",
  "trace_id": "uuid",
  "audio": { }
}
```

Response JSON (example):

```json
{
  "transcript_partial": "…",
  "transcript_final": null,
  "language": "ru",
  "text_features": { "confidence": 0.5 }
}
```

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8090
```

Configure gateway `modules.default.json` → `modules.text.params.speech_service_url`.
