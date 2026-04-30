"""HTTP client for external speech-service (ASR)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def transcribe_audio_chunk(
    base_url: str,
    *,
    session_id: int,
    participant_id: str,
    trace_id: str,
    audio_payload: dict[str, Any],
    timeout_sec: float = 15.0,
) -> dict[str, Any] | None:
    """
    POST {base_url}/v1/transcribe

    Expected JSON body:
      { "session_id", "participant_id", "trace_id", "audio": { ... same as WS audio payload ... } }

    Expected JSON response (stub or real):
      {
        "transcript_partial": "...",
        "transcript_final": "...",
        "language": "ru",
        "text_features": { ... }
      }
    """
    url = base_url.rstrip("/") + "/v1/transcribe"
    body = {
        "session_id": session_id,
        "participant_id": participant_id,
        "trace_id": trace_id,
        "audio": audio_payload,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        return {"_error": str(e)}
