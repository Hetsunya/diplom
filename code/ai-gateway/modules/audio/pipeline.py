"""WS `type: audio` → optional `audio_analysis` + optional `text_analysis` (ASR)."""

from __future__ import annotations

import json
from typing import Any

from contracts import analysis_envelope, build_trace_id, has_required_envelope_fields
from feature_store import get_feature_store
from gateway_config import get_gateway_config
from modules.audio.signal import extract_audio_features
from modules.text.transcription import transcribe_and_emit_text_analysis
from observability import incr


class AudioPipelinePlugin:
    name = "audio"
    priority = 150

    def metadata(self) -> dict[str, str]:
        cfg = get_gateway_config()
        m = cfg.module("audio")
        return {
            "module": self.name,
            "provider": (m.provider if m else ""),
            "model": (m.model if m else ""),
            "version": (m.model if m else "audio-features-v1"),
        }

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

        if audio_mod and audio_mod.enabled:
            audio_ver = audio_mod.model or "audio-features-v1"
            audio_features = extract_audio_features(payload)
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
            if not has_required_envelope_fields(audio_out["payload"]):
                incr("audio_contract_invalid")
                return
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

        await transcribe_and_emit_text_analysis(
            msg=msg,
            ws=ws,
            text_mod=text_mod,
            trace_id=trace_id,
        )


plugin = AudioPipelinePlugin()
