"""Unit tests for report fusion windowing."""

from __future__ import annotations

import time
import unittest

from modules.report.stub_builder import build_stub_report
from modules.report.windowing import compute_fusion_meta


class TestComputeFusionMeta(unittest.TestCase):
    def test_trace_ids_by_participant(self) -> None:
        now = time.time()
        feats = [
            {"kind": "audio", "participant_id": "a", "trace_id": "t1", "ts": now, "data": {}},
            {"kind": "text", "participant_id": "a", "trace_id": "t1", "ts": now, "data": {"payload": {}}},
            {"kind": "face", "participant_id": "b", "trace_id": "t2", "ts": now, "data": {"face_features": {}}},
        ]
        m = compute_fusion_meta(feats, bucket_sec=3600.0)
        self.assertIn("a", m["trace_ids_by_participant"])
        self.assertIn("t1", m["trace_ids_by_participant"]["a"])
        self.assertEqual(len(m["buckets"]), 2)

    def test_bucket_sec_zero_skips_buckets(self) -> None:
        feats = [{"kind": "audio", "participant_id": "x", "trace_id": "z", "ts": 1.0, "data": {}}]
        m = compute_fusion_meta(feats, bucket_sec=0.0)
        self.assertEqual(m["buckets"], [])
        self.assertEqual(m["bucket_sec"], 0.0)


class TestBuildStubReportFusion(unittest.TestCase):
    def test_stub_includes_fusion(self) -> None:
        rep = build_stub_report(99, [], bucket_sec=10.0)
        self.assertIn("fusion", rep)
        self.assertEqual(rep["fusion"]["bucket_sec"], 10.0)


if __name__ == "__main__":
    unittest.main()
