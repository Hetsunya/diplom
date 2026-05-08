"""Local stub report body (multimodal aggregate + fusion meta)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from modules.report.face_behavior import build_face_behavior_summary
from modules.report.windowing import compute_fusion_meta


def _mean(vals: list[float]) -> float | None:
    if not vals:
        return None
    return round(sum(vals) / len(vals), 3)


def build_stub_report(session_id: int, features: list[dict[str, Any]], *, bucket_sec: float = 30.0) -> dict[str, Any]:
    """Aggregate audio / face / text feature rows into the stable stub `report` object."""
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
        if isinstance(k, str):
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
            ff = data.get("face_features") if isinstance(data.get("face_features"), dict) else {}
            if not ff:
                payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
                ff = payload.get("face_features") if isinstance(payload.get("face_features"), dict) else {}
            if ff.get("face_detected") is False:
                continue
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

    report: dict[str, Any] = {
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
    face_behavior_summary = build_face_behavior_summary(features)
    if face_behavior_summary is not None:
        report["face_behavior_summary"] = face_behavior_summary
    report["fusion"] = compute_fusion_meta(features, bucket_sec)
    return report
