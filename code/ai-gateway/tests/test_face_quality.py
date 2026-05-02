"""Unit tests for face module params, schema helpers, report face path, and blur (optional cv2)."""

from __future__ import annotations

import unittest

from modules.face.params import FaceRuntimeParams
from modules.face.schema import (
    build_face_features_guard,
    build_face_features_positive,
    is_no_face_deepface_error,
    normalize_deepface_result,
)
from report_loop import _stub_report

try:
    import numpy as np

    from modules.face.frame_quality import should_skip_blurry_frame

    _HAS_CV = True
except ImportError:
    _HAS_CV = False


class TestFaceRuntimeParams(unittest.TestCase):
    def test_defaults(self) -> None:
        p = FaceRuntimeParams.from_dict({})
        self.assertEqual(p.detector_backend, "opencv")
        self.assertFalse(p.enforce_detection)
        self.assertEqual(p.min_face_side_px, 0)


@unittest.skipUnless(_HAS_CV, "requires numpy and opencv")
class TestFaceBlur(unittest.TestCase):
    def test_blur_skip_uniform(self) -> None:
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        self.assertTrue(should_skip_blurry_frame(img, min_laplacian_var=1.0))

    def test_blur_disabled(self) -> None:
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        self.assertFalse(should_skip_blurry_frame(img, min_laplacian_var=0.0))


class TestFaceSchema(unittest.TestCase):
    def test_normalize_dict(self) -> None:
        n = normalize_deepface_result(
            {
                "dominant_emotion": "happy",
                "emotion": {"happy": 80.0, "sad": 20.0},
            }
        )
        assert n is not None
        self.assertEqual(n["dominant_emotion"], "happy")
        self.assertEqual(n["confidence"], 80.0)

    def test_small_region_filtered(self) -> None:
        ff = build_face_features_positive(
            dominant="neutral",
            probs={"neutral": 50.0},
            confidence=50.0,
            region_w=10,
            region_h=10,
            min_face_side_px=32,
        )
        self.assertIsNone(ff)

    def test_guard_payload(self) -> None:
        g = build_face_features_guard(reason="no_face")
        self.assertFalse(g["face_detected"])
        self.assertEqual(g["guard_reason"], "no_face")

    def test_no_face_error_heuristic(self) -> None:
        self.assertTrue(is_no_face_deepface_error(ValueError("Face could not be detected")))
        self.assertFalse(is_no_face_deepface_error(RuntimeError("CUDA OOM")))


class TestReportFaceFeaturePath(unittest.TestCase):
    def test_stub_reads_top_level_face_features(self) -> None:
        features = [
            {
                "kind": "face",
                "participant_id": "p1",
                "data": {
                    "face_features": {
                        "dominant_emotion": "happy",
                        "face_detected": True,
                        "confidence": 0.9,
                    }
                },
            }
        ]
        rep = _stub_report(1, features)
        parts = rep.get("participants", [])
        self.assertTrue(any(p.get("last_emotion") == "happy" for p in parts if isinstance(p, dict)))


if __name__ == "__main__":
    unittest.main()
