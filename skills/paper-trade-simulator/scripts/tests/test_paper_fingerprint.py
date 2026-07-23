import gc
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import paper_trade


class TestPaperFingerprint(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.test_db = Path(self.temp_file.name)
        self.temp_file.close()
        self.db_path_patcher = patch("paper_trade.DB_PATH", self.test_db)
        self.db_path_patcher.start()

    def tearDown(self):
        self.db_path_patcher.stop()
        gc.collect()
        try:
            os.unlink(self.test_db)
        except FileNotFoundError:
            pass

    def test_fingerprint_tracks_forward_outcomes_after_exit(self):
        with patch("paper_trade._now_iso", return_value="2026-07-01T09:00:00+00:00"):
            trade = paper_trade.open_position(
                symbol="ABC.BK",
                market="TH",
                shares=100,
                entry=100.0,
                stop=95.0,
                target=110.0,
                source="thai-swing-dip",
            )

        with patch("paper_trade._now_iso", return_value="2026-07-01T10:00:00+00:00"):
            paper_trade.close_position(trade["id"], 105.0, "closed_manual")

        paper_trade.record_mark(trade["id"], 110.0, "2026-07-02T10:00:00+00:00")
        paper_trade.record_mark(trade["id"], 112.0, "2026-07-03T10:00:00+00:00")
        paper_trade.record_mark(trade["id"], 115.0, "2026-07-04T10:00:00+00:00")
        paper_trade.record_mark(trade["id"], 120.0, "2026-07-07T10:00:00+00:00")
        paper_trade.record_mark(trade["id"], 95.0, "2026-07-08T10:00:00+00:00")

        result = paper_trade.compute_fingerprints("TH")
        profile = result["profiles"][0]

        self.assertEqual(profile["symbol"], "ABC.BK")
        self.assertEqual(profile["source"], "thai-swing-dip")
        self.assertEqual(profile["closed_trades"], 1)
        self.assertEqual(profile["sample_status"], "research_only")
        self.assertAlmostEqual(profile["forward"]["1"]["avg_r"], 1.0)
        self.assertAlmostEqual(profile["forward"]["3"]["avg_r"], 2.0)
        self.assertAlmostEqual(profile["forward"]["5"]["avg_r"], -2.0)
        self.assertIn("post_exit_continuation", profile["flags"])

    def test_record_mark_is_idempotent_for_same_timestamp(self):
        with patch("paper_trade._now_iso", return_value="2026-07-01T09:00:00+00:00"):
            trade = paper_trade.open_position(
                symbol="XYZ.BK",
                market="TH",
                shares=100,
                entry=10.0,
                stop=9.0,
                target=12.0,
            )

        timestamp = "2026-07-02T10:00:00+00:00"
        paper_trade.record_mark(trade["id"], 10.5, timestamp)
        paper_trade.record_mark(trade["id"], 11.0, timestamp)

        self.assertEqual(len(paper_trade.list_marks(trade["id"])), 2)
