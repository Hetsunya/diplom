"""DeepFace output normalization and face_features payloads (no OpenCV import)."""

from __future__ import annotations

from typing import Any


def is_no_face_deepface_error(exc: BaseException) -> bool:
    s = str(exc).lower()
    needles = (
        "face could not be detected",
        "detected face is too small",
        "there is no face",
        "no face detected",
    )
    return any(n in s for n in needles)


def normalize_deepface_result(result: Any) -> dict[str, Any] | None:
    """Pick first face dict from DeepFace `analyze` return value."""
    if isinstance(result, dict):
        obj = result
    elif isinstance(result, list) and result:
        first = result[0]
        if not isinstance(first, dict):
            return None
        obj = first
    else:
        return None

    dominant = obj.get("dominant_emotion")
    probs = obj.get("emotion")
    if not isinstance(dominant, str) or not isinstance(probs, dict):
        return None

    confidence_val = probs.get(dominant, 0)
    if not isinstance(confidence_val, (int, float)):
        confidence_val = 0.0

    region = obj.get("region")
    region_w = region_h = region_x = region_y = None
    if isinstance(region, dict):
        rw = region.get("w")
        rh = region.get("h")
        if isinstance(rw, (int, float)) and isinstance(rh, (int, float)):
            region_w, region_h = int(rw), int(rh)
        rx = region.get("x", region.get("left"))
        ry = region.get("y", region.get("top"))
        if isinstance(rx, (int, float)) and isinstance(ry, (int, float)):
            region_x, region_y = int(rx), int(ry)

    return {
        "dominant_emotion": dominant,
        "probs": probs,
        "confidence": float(confidence_val),
        "region_w": region_w,
        "region_h": region_h,
        "region_x": region_x,
        "region_y": region_y,
    }


def build_face_features_positive(
    *,
    dominant: str,
    probs: dict[str, Any],
    confidence: float,
    region_w: int | None,
    region_h: int | None,
    min_face_side_px: int,
) -> dict[str, Any] | None:
    """
    Build `face_features` for a confident detection.

    Returns None if region is present and too small (noisy partial detections).
    """
    if min_face_side_px > 0 and region_w is not None and region_h is not None:
        if min(region_w, region_h) < min_face_side_px:
            return None

    return {
        "dominant_emotion": dominant,
        "probs": probs,
        "face_detected": True,
        "confidence": confidence,
    }


def build_face_features_guard(*, reason: str) -> dict[str, Any]:
    """Structured payload when we intentionally emit a negative / guard outcome."""
    return {
        "face_detected": False,
        "dominant_emotion": None,
        "probs": {},
        "confidence": 0.0,
        "guard_reason": reason,
    }
