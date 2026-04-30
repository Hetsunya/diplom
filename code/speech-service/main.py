"""Minimal ASR stub for ai-gateway integration tests."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="emeeting-speech-service", version="0.1.0")


class TranscribeRequest(BaseModel):
    session_id: int
    participant_id: str
    trace_id: str
    audio: dict[str, Any] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/transcribe")
def transcribe(req: TranscribeRequest) -> dict[str, Any]:
    # Stub: real deployment would stream PCM/WebM to ASR.
    return {
        "transcript_partial": f"[stub] session={req.session_id} participant={req.participant_id}",
        "transcript_final": None,
        "language": "ru",
        "text_features": {"confidence": 0.42, "sentiment": "neutral"},
    }
