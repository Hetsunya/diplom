import json
from typing import Any, Literal, cast

from adapters.speech_service import transcribe_audio_chunk
from contracts import analysis_envelope, build_trace_id
from feature_store import get_feature_store
from gateway_config import get_gateway_config
from observability import incr, log_event


class AudioPlugin:
    name = "audio"
    priority = 150

    def can_handle(self, msg: dict[str, Any]) -> bool:
        return msg.get("type") == "audio"

    async def process(self, msg: dict[str, Any], ws: Any) -> None:
        cfg = get_gateway_config()
        audio_mod = cfg.module("audio")
        text_mod = cfg.module("text")

        session_id = msg.get("session_id")
        participant_id = msg.get("participant_id")
        if session_id is None or not participant_id:
            return

        trace_id = build_trace_id()
        ts = msg.get("timestamp")
        payload = msg.get("payload") if isinstance(msg.get("payload"), dict) else {}

        # Optional low-level audio features (baseline stub).
        if audio_mod and audio_mod.enabled:
            audio_ver = audio_mod.model or "audio-features-v1"
            audio_features = {
                "energy_rms": 0.0,
                "pause_ratio": 0.0,
                "note": "baseline stub — replace with DSP / model output",
            }
            audio_out = {
                "type": "audio_analysis",
                "session_id": session_id,
                "participant_id": participant_id,
                "payload": {
                    **analysis_envelope(
                        module="audio",
                        version=audio_ver,
                        stage="partial",
                        trace_id=trace_id,
                    ),
                    "audio_features": audio_features,
                },
                "timestamp": ts,
            }
            await ws.send(json.dumps(audio_out))
            get_feature_store().push(
                int(session_id),
                kind="audio",
                participant_id=str(participant_id),
                trace_id=trace_id,
                data={"audio_features": audio_features},
            )
            incr("audio_analysis_sent")

        if not text_mod or not text_mod.enabled:
            return

        base_url = str(text_mod.params.get("speech_service_url") or "").strip()
        if not base_url:
            log_event("speech_skip", module="text", extra={"reason": "no speech_service_url"})
            return

        timeout_sec = float(text_mod.params.get("timeout_sec", 15))
        text_ver = text_mod.model or "stub-v1"

        result = transcribe_audio_chunk(
            base_url,
            session_id=int(session_id),
            participant_id=str(participant_id),
            trace_id=trace_id,
            audio_payload=payload,
            timeout_sec=timeout_sec,
        )
        if not isinstance(result, dict):
            incr("text_analysis_errors")
            return

        if result.get("_error"):
            log_event("speech_error", trace_id=trace_id, module="text", extra={"err": result["_error"]})
            incr("text_analysis_errors")
            return

        transcript_partial = result.get("transcript_partial")
        transcript_final = result.get("transcript_final")
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
                        "language": result.get("language"),
                        "text_features": result.get("text_features") or {},
                    },
                ),
            },
            "timestamp": ts,
        }
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


plugin = AudioPlugin()
