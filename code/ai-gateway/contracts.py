"""v1 analysis envelope helpers (see docs/ANALYSIS_WS_CONTRACTS.md)."""

from __future__ import annotations

import uuid
from typing import Any, Literal

ModuleName = Literal["text", "audio", "face", "report"]
StageName = Literal["partial", "final"]


def build_trace_id() -> str:
    return str(uuid.uuid4())


def analysis_envelope(
    *,
    module: ModuleName,
    version: str,
    stage: StageName,
    trace_id: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "module": module,
        "version": version,
        "stage": stage,
        "trace_id": trace_id,
    }
    if extra:
        out.update(extra)
    return out
