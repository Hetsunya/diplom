"""Optional faster-whisper backend for speech-service."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

_model_cache: dict[str, Any] = {}


def _get_model(model_size: str):
    """Lazy singleton per model size."""
    from faster_whisper import WhisperModel

    global _model_cache
    if model_size not in _model_cache:
        device = os.getenv("WHISPER_DEVICE", "cpu")
        ctype = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        _model_cache[model_size] = WhisperModel(model_size, device=device, compute_type=ctype)
    return _model_cache[model_size]


def transcribe_media_bytes(data: bytes, suffix: str, *, language: str | None) -> tuple[str, dict[str, Any]]:
    """
    Write bytes to a temp file and run Whisper. suffix should match mime (.webm, .wav, …).
    Returns (text, info dict for text_features).
    """
    model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
    model = _get_model(model_size)

    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    path = Path(tmp.name)
    try:
        tmp.write(data)
        tmp.close()

        kwargs: dict[str, Any] = {"beam_size": int(os.getenv("WHISPER_BEAM_SIZE", "5"))}
        lang = language or os.getenv("WHISPER_LANGUAGE") or None
        if lang:
            kwargs["language"] = lang

        vad_env = os.getenv("WHISPER_VAD_FILTER", "false").strip().lower()
        kwargs["vad_filter"] = vad_env in ("1", "true", "yes", "on")

        try:
            segments, info = model.transcribe(str(path), **kwargs)
        except Exception as exc:
            return "", {
                "confidence": 0.0,
                "language": lang or "unknown",
                "model_size": model_size,
                "error": type(exc).__name__,
                "message": str(exc)[:240],
            }

        parts: list[str] = []
        for seg in segments:
            t = (seg.text or "").strip()
            if t:
                parts.append(t)
        text = " ".join(parts).strip()

        meta = {
            "confidence": float(getattr(info, "language_probability", 0.5) or 0.5),
            "language": getattr(info, "language", None) or lang or "unknown",
            "duration_after_vad": getattr(info, "duration", None),
            "model_size": model_size,
        }
        return text, meta
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def suffix_from_mime(mime: str) -> str:
    m = (mime or "").split(";")[0].strip().lower()
    if "wav" in m:
        return ".wav"
    if "ogg" in m:
        return ".ogg"
    if "mp4" in m or "m4a" in m:
        return ".m4a"
    return ".webm"
