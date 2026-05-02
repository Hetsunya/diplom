"""Baseline audio chunk descriptors without full PCM decode (proxy features)."""

from __future__ import annotations

import base64
from typing import Any


def extract_audio_features(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Proxy metrics from chunk metadata/size:
    chunk_size_bytes, duration_ms, bitrate_kbps_est, speech_activity_proxy.
    """
    b64_raw = payload.get("chunk_base64") or payload.get("data_base64") or payload.get("base64")
    chunk_size_bytes = 0
    if isinstance(b64_raw, str) and b64_raw.strip():
        try:
            chunk_size_bytes = len(base64.b64decode(b64_raw, validate=False))
        except Exception:
            chunk_size_bytes = 0

    timeslice_ms_raw = payload.get("timeslice_ms")
    if isinstance(timeslice_ms_raw, (int, float)) and timeslice_ms_raw > 0:
        duration_ms = float(timeslice_ms_raw)
    else:
        duration_ms = 3500.0

    bitrate_kbps_est = 0.0
    if duration_ms > 0:
        bitrate_kbps_est = round((chunk_size_bytes * 8.0) / duration_ms, 2)

    speech_proxy = min(1.0, round(chunk_size_bytes / 12000.0, 3))
    if chunk_size_bytes < 400:
        speech_proxy = 0.0

    final_chunk = bool(payload.get("final_chunk") or payload.get("is_final"))
    mime = payload.get("mime")

    return {
        "chunk_size_bytes": chunk_size_bytes,
        "duration_ms": duration_ms,
        "bitrate_kbps_est": bitrate_kbps_est,
        "speech_activity_proxy": speech_proxy,
        "final_chunk": final_chunk,
        "mime": str(mime) if isinstance(mime, str) else "audio/webm",
        "note": "proxy-features-v2; replace with DSP/SER model later",
    }
