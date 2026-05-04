"""ASR HTTP service for ai-gateway (stub or faster-whisper)."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from asr_whisper import suffix_from_mime, transcribe_media_bytes

app = FastAPI(title="emeeting-speech-service", version="0.2.0")

def _canonical_asr_engine(raw: str | None) -> str:
    """Normalize env values: `faster_whisper`, `FAST-WHISPER` → whisper (faster-whisper path)."""
    if raw is None or not str(raw).strip():
        return "stub"
    e = str(raw).strip().lower().replace("_", "-")
    if e in ("", "none"):
        return "stub"
    if e in ("faster-whisper", "fast-whisper"):
        return "whisper"
    return e


_ENGINE_RAW = os.getenv("SPEECH_ASR_ENGINE", "stub")
_engine = _canonical_asr_engine(_ENGINE_RAW)
_executor = ThreadPoolExecutor(max_workers=int(os.getenv("SPEECH_ASR_WORKERS", "1")))
_logger = logging.getLogger("speech_service")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)
_logger.info(
    "speech_service engine=%r (raw SPEECH_ASR_ENGINE=%r)",
    _engine,
    _ENGINE_RAW,
)


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
    if meta.get("error"):
        _logger.warning(
            "whisper_transcribe_failed trace_id=%s participant=%s error=%s msg=%s",
            req.trace_id,
            req.participant_id,
            meta.get("error"),
            meta.get("message"),
        )
    final_marker = bool(audio.get("final_chunk")) or bool(audio.get("is_final"))
    text_features: dict[str, object] = {
        "confidence": meta.get("confidence"),
        "model_size": meta.get("model_size"),
        "sentiment": "neutral",
    }
    if meta.get("error"):
        text_features["error"] = meta["error"]
        text_features["message"] = meta.get("message")
    return {
        "transcript_partial": text,
        "transcript_final": text if final_marker and text else None,
        "language": meta.get("language") or lang or "unknown",
        "text_features": text_features,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "engine": _engine, "engine_env": _ENGINE_RAW}


@app.post("/v1/transcribe")
async def transcribe(req: TranscribeRequest) -> dict[str, Any]:
    if _engine in ("stub", "", "none"):
        return _stub_response(req)
    if _engine == "whisper":
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, _whisper_sync, req)
    _logger.warning("unknown SPEECH_ASR_ENGINE=%r → stub", _ENGINE_RAW)
    return _stub_response(req)
