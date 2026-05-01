"""ASR HTTP service for ai-gateway (stub or faster-whisper)."""

from __future__ import annotations

import asyncio
import base64
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from asr_whisper import suffix_from_mime, transcribe_media_bytes

app = FastAPI(title="emeeting-speech-service", version="0.2.0")

_engine = os.getenv("SPEECH_ASR_ENGINE", "stub").strip().lower()
_executor = ThreadPoolExecutor(max_workers=int(os.getenv("SPEECH_ASR_WORKERS", "1")))


class TranscribeRequest(BaseModel):
    session_id: int
    participant_id: str
    trace_id: str
    audio: dict[str, Any] = {}


def _stub_response(req: TranscribeRequest) -> dict[str, Any]:
    return {
        "transcript_partial": f"[stub] session={req.session_id} participant={req.participant_id}",
        "transcript_final": None,
        "language": "ru",
        "text_features": {"confidence": 0.42, "sentiment": "neutral"},
    }


def _whisper_sync(req: TranscribeRequest) -> dict[str, Any]:
    audio = req.audio or {}
    b64 = audio.get("chunk_base64") or audio.get("data_base64") or audio.get("base64")
    if not isinstance(b64, str) or not b64.strip():
        return {
            "transcript_partial": "",
            "transcript_final": None,
            "language": audio.get("language") or "unknown",
            "text_features": {"confidence": 0.0, "note": "empty_chunk"},
        }

    mime = str(audio.get("mime") or audio.get("mime_type") or "audio/webm")
    lang_in = audio.get("language")
    lang = str(lang_in) if isinstance(lang_in, str) and lang_in else None

    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception:
        return {
            "transcript_partial": "",
            "transcript_final": None,
            "language": "unknown",
            "text_features": {"confidence": 0.0, "note": "base64_decode_failed"},
        }

    if len(raw) < 256:
        return {
            "transcript_partial": "",
            "transcript_final": None,
            "language": lang or "unknown",
            "text_features": {"confidence": 0.0, "note": "chunk_too_small"},
        }

    suffix = suffix_from_mime(mime)
    text, meta = transcribe_media_bytes(raw, suffix, language=lang)
    final_marker = bool(audio.get("final_chunk")) or bool(audio.get("is_final"))
    return {
        "transcript_partial": text,
        "transcript_final": text if final_marker and text else None,
        "language": meta.get("language") or lang or "unknown",
        "text_features": {
            "confidence": meta.get("confidence"),
            "model_size": meta.get("model_size"),
            "sentiment": "neutral",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": _engine}


@app.post("/v1/transcribe")
async def transcribe(req: TranscribeRequest) -> dict[str, Any]:
    if _engine in ("stub", "", "none"):
        return _stub_response(req)
    if _engine in ("whisper", "faster-whisper"):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, _whisper_sync, req)
    return _stub_response(req)
