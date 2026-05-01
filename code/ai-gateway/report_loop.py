"""Periodic hybrid partial reports + stub final NN when HTTP URL unset."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from contracts import analysis_envelope, build_trace_id
from feature_store import get_feature_store
from gateway_config import config_snapshot, get_gateway_config
from observability import incr, log_event, monotonic_ms
from own_nn_client import generate_report


_PIPELINE_STAGES = {"idle", "listening", "transcribing", "visual_only"}


def _mean(vals: list[float]) -> float | None:
    if not vals:
        return None
    return round(sum(vals) / len(vals), 3)


def _stub_report(session_id: int, features: list[dict[str, Any]]) -> dict[str, Any]:
    kinds: dict[str, int] = {}
    participants: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "audio_chunks": 0,
            "avg_speech_activity_proxy": None,
            "avg_bitrate_kbps": None,
            "last_emotion": None,
            "last_transcript": None,
        }
    )
    audio_activity_acc: dict[str, list[float]] = defaultdict(list)
    audio_bitrate_acc: dict[str, list[float]] = defaultdict(list)

    total_audio_chunks = 0
    speech_chunks = 0

    for f in features:
        k = f.get("kind") or "unknown"
        kinds[k] = kinds.get(k, 0) + 1
        pid = str(f.get("participant_id") or "unknown")
        data = f.get("data") if isinstance(f.get("data"), dict) else {}

        if k == "audio":
            total_audio_chunks += 1
            participants[pid]["audio_chunks"] += 1
            af = data.get("audio_features") if isinstance(data.get("audio_features"), dict) else {}
            sap = af.get("speech_activity_proxy")
            bitrate = af.get("bitrate_kbps_est")
            if isinstance(sap, (int, float)):
                sapf = float(sap)
                audio_activity_acc[pid].append(sapf)
                if sapf >= 0.35:
                    speech_chunks += 1
            if isinstance(bitrate, (int, float)):
                audio_bitrate_acc[pid].append(float(bitrate))

        elif k == "face":
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
            ff = payload.get("face_features") if isinstance(payload.get("face_features"), dict) else {}
            dom = ff.get("dominant_emotion")
            if isinstance(dom, str) and dom.strip():
                participants[pid]["last_emotion"] = dom

        elif k == "text":
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
            transcript = payload.get("transcript_final") or payload.get("transcript_partial")
            if isinstance(transcript, str) and transcript.strip():
                participants[pid]["last_transcript"] = transcript.strip()[:180]

    for pid, p in participants.items():
        p["avg_speech_activity_proxy"] = _mean(audio_activity_acc[pid])
        p["avg_bitrate_kbps"] = _mean(audio_bitrate_acc[pid])

    talk_ratio = 0.0
    if total_audio_chunks > 0:
        talk_ratio = round(speech_chunks / total_audio_chunks, 3)

    if kinds.get("text", 0) > 0:
        stage_label = "transcribing"
    elif total_audio_chunks > 0:
        stage_label = "listening"
    elif kinds.get("face", 0) > 0:
        stage_label = "visual_only"
    else:
        stage_label = "idle"

    summary = (
        f"pipeline={stage_label}; audio_chunks={total_audio_chunks}; "
        f"text_events={kinds.get('text', 0)}; face_events={kinds.get('face', 0)}; "
        f"speech_ratio={talk_ratio}"
    )

    return {
        "session_id": session_id,
        "summary": summary,
        "pipeline_stage": stage_label,
        "speech_ratio": talk_ratio,
        "feature_counts": kinds,
        "participants": [
            {"participant_id": pid, **pdata}
            for pid, pdata in sorted(participants.items(), key=lambda kv: kv[1]["audio_chunks"], reverse=True)
        ],
    }


def _to_non_empty_str(v: Any, default: str) -> str:
    if isinstance(v, str) and v.strip():
        return v.strip()
    return default


def _to_float(v: Any, default: float, *, lo: float | None = None, hi: float | None = None) -> float:
    if isinstance(v, (int, float)):
        out = float(v)
        if lo is not None and out < lo:
            out = lo
        if hi is not None and out > hi:
            out = hi
        return round(out, 3)
    return default


def _sanitize_feature_counts(v: Any) -> dict[str, int]:
    if not isinstance(v, dict):
        return {}
    out: dict[str, int] = {}
    for k, val in v.items():
        if not isinstance(k, str):
            continue
        if isinstance(val, (int, float)):
            out[k] = max(0, int(val))
    return out


def _sanitize_participants(v: Any) -> list[dict[str, Any]]:
    if not isinstance(v, list):
        return []
    out: list[dict[str, Any]] = []
    for raw in v:
        if not isinstance(raw, dict):
            continue
        pid = _to_non_empty_str(raw.get("participant_id"), "unknown")
        item = {
            "participant_id": pid,
            "audio_chunks": int(_to_float(raw.get("audio_chunks"), 0.0, lo=0)),
            "avg_speech_activity_proxy": _to_float(raw.get("avg_speech_activity_proxy"), 0.0, lo=0.0, hi=1.0),
            "avg_bitrate_kbps": _to_float(raw.get("avg_bitrate_kbps"), 0.0, lo=0.0),
            "last_emotion": _to_non_empty_str(raw.get("last_emotion"), ""),
            "last_transcript": _to_non_empty_str(raw.get("last_transcript"), "")[:180],
        }
        out.append(item)
    return out


def sanitize_report_shape(raw: Any, *, session_id: int) -> dict[str, Any]:
    """
    Keep report JSON shape stable for UI regardless of remote model output.
    Unknown fields are dropped in this baseline implementation.
    """
    if not isinstance(raw, dict):
        return _stub_report(session_id, [])

    stage = _to_non_empty_str(raw.get("pipeline_stage"), "idle")
    if stage not in _PIPELINE_STAGES:
        stage = "idle"

    return {
        "session_id": int(_to_float(raw.get("session_id"), float(session_id), lo=0)),
        "summary": _to_non_empty_str(raw.get("summary"), "report generated"),
        "pipeline_stage": stage,
        "speech_ratio": _to_float(raw.get("speech_ratio"), 0.0, lo=0.0, hi=1.0),
        "feature_counts": _sanitize_feature_counts(raw.get("feature_counts")),
        "participants": _sanitize_participants(raw.get("participants")),
    }


def _is_report_substantial(report: dict[str, Any]) -> bool:
    summary = report.get("summary")
    if isinstance(summary, str) and summary.strip() and summary.strip().lower() != "report generated":
        return True

    fc = report.get("feature_counts")
    if isinstance(fc, dict) and any(isinstance(v, int) and v > 0 for v in fc.values()):
        return True

    participants = report.get("participants")
    if isinstance(participants, list) and len(participants) > 0:
        for p in participants:
            if not isinstance(p, dict):
                continue
            if isinstance(p.get("audio_chunks"), int) and p.get("audio_chunks", 0) > 0:
                return True
            if isinstance(p.get("last_transcript"), str) and p.get("last_transcript", "").strip():
                return True
    return False


async def report_loop(ws_holder: list[Any], session_id: int) -> None:
    """ws_holder[0] is the active websocket client protocol (mutated by SessionWSClient)."""
    cfg = get_gateway_config()
    mod = cfg.module("report")
    if not mod or not mod.enabled:
        return
    interval = float(mod.params.get("interval_sec", 30))
    own_url = str(mod.params.get("own_nn_url", "") or "")
    model_ver = mod.model or "report-v1"

    while True:
        await asyncio.sleep(max(interval, 5.0))
        ws = ws_holder[0] if ws_holder else None
        if ws is None or not getattr(ws, "open", True):
            continue
        t0 = monotonic_ms()
        feats = get_feature_store().snapshot_session(session_id)
        trace = build_trace_id()
        snap = config_snapshot()
        report_body: dict[str, Any]
        report_source = "local_stub"
        remote = generate_report(
            own_url,
            session_id=session_id,
            features=feats,
            config_snapshot=snap,
            stage="partial",
        )
        if isinstance(remote, dict) and remote.get("report"):
            sanitized = sanitize_report_shape(remote.get("report"), session_id=session_id)
            if _is_report_substantial(sanitized):
                report_body = sanitized
                report_source = "remote"
            else:
                # Remote returned a structurally valid but effectively empty report.
                report_body = _stub_report(session_id, feats)
                report_source = "local_fallback"
                incr("report_remote_empty_fallback")
            incr("report_shape_validated")
        else:
            report_body = _stub_report(session_id, feats)
            report_source = "local_stub"

        now = datetime.now(timezone.utc).isoformat()
        out = {
            "type": "analysis_report_partial",
            "session_id": session_id,
            "participant_id": "",
            "payload": {
                **analysis_envelope(
                    module="report",
                    version=model_ver,
                    stage="partial",
                    trace_id=trace,
                ),
                "report": report_body,
                "report_source": report_source,
                "model_version": model_ver,
                "generated_at": now,
                "config_snapshot": snap,
            },
            "timestamp": now,
        }
        try:
            await ws.send(json.dumps(out))
            incr("report_partial_sent")
            log_event(
                "report_partial",
                trace_id=trace,
                module="report",
                extra={"latency_ms": round(monotonic_ms() - t0, 2)},
            )
        except Exception as e:
            incr("report_partial_errors")
            log_event("report_partial_failed", extra={"error": str(e)})
