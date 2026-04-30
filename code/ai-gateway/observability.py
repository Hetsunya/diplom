"""Lightweight metrics + structured logs for the hybrid analysis pipeline."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

_log = logging.getLogger("ai_gateway")
if not _log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    _log.addHandler(h)
    _log.setLevel(logging.INFO)

_lock = threading.Lock()
_counters: dict[str, int] = {}


def incr(metric: str, n: int = 1) -> None:
    with _lock:
        _counters[metric] = _counters.get(metric, 0) + n


def snapshot_metrics() -> dict[str, int]:
    with _lock:
        return dict(_counters)


def log_event(
    event: str,
    *,
    trace_id: str | None = None,
    module: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    parts = [f"event={event}"]
    if trace_id:
        parts.append(f"trace_id={trace_id}")
    if module:
        parts.append(f"module={module}")
    if extra:
        for k, v in extra.items():
            parts.append(f"{k}={v}")
    _log.info(" ".join(parts))


def monotonic_ms() -> float:
    return time.monotonic() * 1000.0
