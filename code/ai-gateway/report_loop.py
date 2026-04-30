"""Periodic hybrid partial reports + stub final NN when HTTP URL unset."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from contracts import analysis_envelope, build_trace_id
from feature_store import get_feature_store
from gateway_config import config_snapshot, get_gateway_config
from observability import incr, log_event, monotonic_ms
from own_nn_client import generate_report


def _stub_report(session_id: int, features: list[dict[str, Any]]) -> dict[str, Any]:
    kinds: dict[str, int] = {}
    for f in features:
        k = f.get("kind") or "unknown"
        kinds[k] = kinds.get(k, 0) + 1
    return {
        "session_id": session_id,
        "summary": "stub aggregate from ai-gateway",
        "feature_counts": kinds,
        "participants": [],
    }


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
        remote = generate_report(
            own_url,
            session_id=session_id,
            features=feats,
            config_snapshot=snap,
            stage="partial",
        )
        if isinstance(remote, dict) and remote.get("report"):
            report_body = remote["report"]
        else:
            report_body = _stub_report(session_id, feats)

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
