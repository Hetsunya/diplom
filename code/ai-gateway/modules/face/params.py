"""Typed defaults for `modules.face.params` (see modules.default.json)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FaceRuntimeParams:
    min_interval_sec: float
    min_confidence: float
    enforce_detection: bool
    detector_backend: str
    align: bool
    min_laplacian_var: float
    min_face_side_px: int
    emit_no_face_face_analysis: bool

    @staticmethod
    def from_dict(p: dict[str, Any]) -> FaceRuntimeParams:
        return FaceRuntimeParams(
            min_interval_sec=float(p.get("min_interval_sec", 0.2)),
            min_confidence=float(p.get("min_confidence", 0.0)),
            enforce_detection=bool(p.get("enforce_detection", False)),
            detector_backend=str(p.get("detector_backend", "opencv") or "opencv"),
            align=bool(p.get("align", False)),
            min_laplacian_var=float(p.get("min_laplacian_var", 0.0)),
            min_face_side_px=int(p.get("min_face_side_px", 0)),
            emit_no_face_face_analysis=bool(p.get("emit_no_face_face_analysis", False)),
        )
