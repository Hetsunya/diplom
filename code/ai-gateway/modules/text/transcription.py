"""Build `text_analysis` WS payloads from speech-service responses."""

from __future__ import annotations

import asyncio
import functools
import json
from typing import Any, Literal, cast

from adapters.speech_service import transcribe_audio_chunk
from contracts import analysis_envelope, has_required_envelope_fields
from feature_store import get_feature_store
from gateway_config import ModuleCfg
from modules.text.features import enrich_text_features
from modules.text.normalize import has_transcript_content, normalize_asr_response
from observability import incr, log_event


async def transcribe_and_emit_text_analysis(
    *,
    msg: dict[str, Any],
    ws: Any,
    text_mod: ModuleCfg,
    trace_id: str,
) -> None:
    """POST audio to speech-service and emit `text_analysis` + feature_store push."""
    session_id = msg.get("session_id")
    participant_id = msg.get("participant_id")
    ts = msg.get("timestamp")
    payload = msg.get("payload") if isinstance(msg.get("payload"), dict) else {}

    base_url = str(text_mod.params.get("speech_service_url") or "").strip()
    if not base_url:
        log_event("speech_skip", module="text", extra={"reason": "no speech_service_url"})
        return

    timeout_sec = float(text_mod.params.get("timeout_sec", 15))
    retries = int(text_mod.params.get("retries", 2))
    backoff_sec = float(text_mod.params.get("backoff_sec", 0.5))
    cb_failures = int(text_mod.params.get("circuit_failure_threshold", 5))
    cb_open_sec = float(text_mod.params.get("circuit_open_sec", 30.0))
    text_ver = text_mod.model or "stub-v1"

    result = await asyncio.to_thread(
        functools.partial(
            transcribe_audio_chunk,
            base_url,
            session_id=int(session_id),
            participant_id=str(participant_id),
            trace_id=trace_id,
            audio_payload=payload,
            timeout_sec=timeout_sec,
            retries=retries,
            backoff_sec=backoff_sec,
            circuit_failure_threshold=cb_failures,
            circuit_open_sec=cb_open_sec,
        )
    )
    if not isinstance(result, dict):
        incr("text_analysis_errors")
        return

    if result.get("_error"):
        log_event("speech_error", trace_id=trace_id, module="text", extra={"err": result["_error"]})
        incr("text_analysis_errors")
        if result.get("_circuit_open"):
            incr("speech_service_circuit_open")
        return

    norm = normalize_asr_response(result)
    if not has_transcript_content(norm):
        log_event("speech_skip", module="text", trace_id=trace_id, extra={"reason": "empty_transcript"})
        return

    transcript_partial = norm.get("transcript_partial")
    transcript_final = norm.get("transcript_final")
    text_features = enrich_text_features(
        transcript_partial=transcript_partial if isinstance(transcript_partial, str) else None,
        transcript_final=transcript_final if isinstance(transcript_final, str) else None,
        text_features=norm.get("text_features") if isinstance(norm.get("text_features"), dict) else {},
    )
    stage_name = cast(
        Literal["partial", "final"],
        "final" if transcript_final else "partial",
    )
    text_out = {
        "type": "text_analysis",
        "session_id": session_id,
        "participant_id": participant_id,
        "payload": {
            **analysis_envelope(
                module="text",
                version=text_ver,
                stage=stage_name,
                trace_id=trace_id,
                extra={
                    "transcript_partial": transcript_partial,
                    "transcript_final": transcript_final,
                    "language": norm.get("language"),
                    "text_features": text_features,
                },
            ),
        },
        "timestamp": ts,
    }
    if not has_required_envelope_fields(text_out["payload"]):
        incr("text_contract_invalid")
        return
    await ws.send(json.dumps(text_out))
    get_feature_store().push(
        int(session_id),
        kind="text",
        participant_id=str(participant_id),
        trace_id=trace_id,
        data={"payload": text_out["payload"]},
    )
    incr("text_analysis_sent")
    log_event("text_analysis", trace_id=trace_id, module="text")
