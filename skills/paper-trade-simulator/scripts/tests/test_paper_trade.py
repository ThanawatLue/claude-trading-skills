import gc
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import paper_trade
import update_marks


class TestPaperTrade(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.test_db = Path(self.temp_file.name)
        self.temp_file.close()

        # Patch the database path in the modules
        self.db_path_patcher1 = patch("paper_trade.DB_PATH", self.test_db)
        self.db_path_patcher2 = patch("update_marks.DB_PATH", self.test_db)
        self.db_path_patcher1.start()
        self.db_path_patcher2.start()

    def tearDown(self):
        self.db_path_patcher1.stop()
        self.db_path_patcher2.stop()
        gc.collect()
        try:
            if os.path.exists(self.test_db):
                os.unlink(self.test_db)
        except PermissionError:
            pass  # Windows file lock

    def test_open_and_list_position(self):
        # Open a long position
        res = paper_trade.open_position(
            symbol="AAPL",
            market="US",
            shares=10,
            entry=150.0,
            stop=140.0,
            target=170.0,
            notes="Breakout test",
            emotion="confident",
        )
        self.assertEqual(res["symbol"], "AAPL")
        self.assertEqual(res["shares"], 10)
        self.assertEqual(res["status"], "open")
        self.assertEqual(res["journal_emotion"], "confident")
        self.assertRegex(res["entry_at"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}")
        self.assertIsNotNone(datetime.fromisoformat(res["entry_at"].replace("Z", "+00:00")))
        self.assertRegex(res["last_updated"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}")
        self.assertIsNotNone(datetime.fromisoformat(res["last_updated"].replace("Z", "+00:00")))

        # List positions
        positions = paper_trade.list_positions(status_filter="open")
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["symbol"], "AAPL")

    def test_initial_risk_calculation(self):
        # Test long position
        long_pos = paper_trade.open_position(
            symbol="TESTL",
            market="US",
            shares=10,
            entry=100.0,
            stop=90.0,
            target=120.0,
            side="long",
        )
        expected_long_risk = abs(100.0 - 90.0) * 10
        self.assertAlmostEqual(long_pos["initial_risk"], expected_long_risk)

        # Test short position
        short_pos = paper_trade.open_position(
            symbol="TESTS",
            market="US",
            shares=10,
            entry=100.0,
            stop=110.0,
            target=80.0,
            side="short",
        )
        expected_short_risk = abs(100.0 - 110.0) * 10
        self.assertAlmostEqual(short_pos["initial_risk"], expected_short_risk)

    def test_close_position(self):
        # Open a long position
        trade = paper_trade.open_position(
            symbol="AAPL", market="US", shares=10, entry=150.0, stop=140.0, target=170.0
        )
        trade_id = trade["id"]

        # Close position manually
        res = paper_trade.close_position(
            trade_id=trade_id,
            exit_price=160.0,
            status="closed_manual",
            emotion="calm",
            notes="Exited early",
        )
        self.assertEqual(res["status"], "closed_manual")
        self.assertEqual(res["exit_price"], 160.0)
        self.assertEqual(res["realized_pnl"], 100.0)  # (160 - 150) * 10
        self.assertEqual(res["realized_r"], 1.0)  # 100 / ((150 - 140) * 10)
        self.assertRegex(res["exit_at"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}")
        self.assertIsNotNone(datetime.fromisoformat(res["exit_at"].replace("Z", "+00:00")))
        self.assertRegex(res["last_updated"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}")
        self.assertIsNotNone(datetime.fromisoformat(res["last_updated"].replace("Z", "+00:00")))

    def test_close_position_records_net_result_after_estimated_costs(self):
        trade = paper_trade.open_position(
            symbol="COST.BK",
            market="TH",
            shares=100,
            entry=10.0,
            stop=9.5,
            target=11.0,
            transaction_cost_bps=15,
        )

        res = paper_trade.close_position(trade["id"], 10.5, "closed_manual")

        self.assertAlmostEqual(res["gross_realized_pnl"], 50.0)
        self.assertAlmostEqual(res["entry_cost"], 1.5)
        self.assertAlmostEqual(res["exit_cost"], 1.575)
        self.assertAlmostEqual(res["realized_pnl"], 46.925)
        self.assertAlmostEqual(res["realized_r"], 0.9385)
        stats = paper_trade.compute_stats(market="TH")
        self.assertAlmostEqual(stats["total_gross_realized_pnl"], 50.0)
        self.assertAlmostEqual(stats["total_closed_cost"], 3.08)

    def test_add_journal(self):
        trade = paper_trade.open_position(
            symbol="MSFT", market="US", shares=5, entry=300.0, stop=280.0, target=340.0
        )
        trade_id = trade["id"]

        res = paper_trade.add_journal(trade_id, "Holding firm", "calm")
        self.assertEqual(res["journal_emotion"], "calm")
        self.assertIn("Holding firm", res["journal_text"])

    def test_stats(self):
        # Create a win and a loss
        t1 = paper_trade.open_position(
            symbol="AAPL",
            market="US",
            shares=10,
            entry=150.0,
            stop=140.0,
            target=170.0,
            source="vcp",
            source_score=82,
        )
        paper_trade.close_position(t1["id"], 160.0, "closed_manual")

        t2 = paper_trade.open_position(
            symbol="MSFT",
            market="US",
            shares=10,
            entry=300.0,
            stop=290.0,
            target=330.0,
            source="vcp",
            source_score=65,
        )
        paper_trade.close_position(t2["id"], 290.0, "closed_stop")

        stats = paper_trade.compute_stats()
        self.assertEqual(stats["total_trades"], 2)
        self.assertEqual(stats["wins"], 1)
        self.assertEqual(stats["losses"], 1)
        self.assertEqual(stats["win_rate"], 0.5)
        self.assertEqual(stats["by_source"]["vcp-screener"]["closed_trades"], 2)
        self.assertEqual(stats["by_source"]["vcp-screener"]["win_rate"], 0.5)
        self.assertEqual(stats["by_score_bucket"]["70-84"]["closed_trades"], 1)
        self.assertEqual(stats["by_score_bucket"]["50-69"]["closed_trades"], 1)

    def test_check_discipline_warnings(self):
        # Initial: no closed trades
        status = paper_trade.check_discipline_warnings()
        self.assertIsNone(status["stop_respect_rate"])
        self.assertFalse(status["fomo_streak"])
        self.assertEqual(len(status["warnings"]), 0)

        # 1. Low stop respect rate and fomo streak test
        # We need at least 1 closed_stop and closed_manual with loss.
        # Let's open and close 2 manual loss trades with fomo/greedy emotions:
        # stop respect rate = 0 / 2 = 0% < 80% -> should warn
        t1 = paper_trade.open_position("AAPL", "US", 10, 150.0, 140.0, 170.0)
        paper_trade.close_position(t1["id"], 145.0, "closed_manual", emotion="fomo")

        t2 = paper_trade.open_position("MSFT", "US", 10, 300.0, 290.0, 330.0)
        paper_trade.close_position(t2["id"], 295.0, "closed_manual", emotion="greedy")

        status = paper_trade.check_discipline_warnings()
        self.assertEqual(status["stop_respect_rate"], 0.0)
        self.assertTrue(status["fomo_streak"])
        self.assertIn("Low Stop Respect Rate", status["warnings"][0])
        self.assertIn("Emotional Risk", status["warnings"][1])

        # Verify warnings are injected into new position output
        t3 = paper_trade.open_position("GOOG", "US", 10, 100.0, 90.0, 120.0)
        self.assertIn("discipline_warnings", t3)
        self.assertEqual(len(t3["discipline_warnings"]), 2)

    def test_check_discipline_warnings_db_error(self):
        with patch("paper_trade._db", side_effect=sqlite3.Error("Mock DB Error")):
            with self.assertLogs("paper_trade", level="ERROR") as cm:
                warnings = paper_trade.open_position("AMZN", "US", 10, 100.0, 90.0, 110.0)[
                    "discipline_warnings"
                ]
                self.assertIn("Error checking discipline warnings from DB", cm.output[0])
                self.assertIn("An error occurred while checking discipline warnings", warnings[0])

    def test_expectancy_warning(self):
        # Open and close some trades with vcp source
        # Let's create a negative expectancy: 1 win (+0.5R), 2 losses (-1.0R each)
        t1 = paper_trade.open_position(
            symbol="AAPL",
            market="US",
            shares=10,
            entry=150.0,
            stop=140.0,
            target=170.0,
            source="vcp-screener",
        )
        paper_trade.close_position(t1["id"], 155.0, "closed_manual")  # realized R = +0.5

        t2 = paper_trade.open_position(
            symbol="MSFT",
            market="US",
            shares=10,
            entry=300.0,
            stop=290.0,
            target=330.0,
            source="vcp-screener",
        )
        paper_trade.close_position(t2["id"], 290.0, "closed_stop")  # realized R = -1.0

        t3 = paper_trade.open_position(
            symbol="GOOG",
            market="US",
            shares=10,
            entry=100.0,
            stop=90.0,
            target=120.0,
            source="vcp",
        )
        paper_trade.close_position(t3["id"], 90.0, "closed_stop")  # realized R = -1.0

        # Import screen_vcp dynamically
        import sys

        sys_path_backup = sys.path.copy()
        vcp_script_dir = Path(__file__).resolve().parents[4] / "skills" / "vcp-screener" / "scripts"
        sys.path.insert(0, str(vcp_script_dir))
        try:
            import screen_vcp

            original_connect = sqlite3.connect

            def mock_connect(database, *args, **kwargs):
                return original_connect(str(self.test_db), *args, **kwargs)

            with patch("sqlite3.connect", side_effect=mock_connect):
                exp, count = screen_vcp.get_recent_expectancy("vcp-screener")

            self.assertEqual(count, 3)
            self.assertAlmostEqual(exp, -0.5)
        finally:
            sys.path = sys_path_backup

    def test_update_marks_tradingview_fallback(self):
        # Open a TH paper position
        paper_trade.open_position(
            symbol="PTT.BK", market="TH", shares=100, entry=30.0, stop=28.0, target=35.0
        )

        mock_tv_stock = {
            "symbol": "PTT.BK",
            "price": 32.5,
            "volume": 1000000,
            "average_volume_10d_calc": 1000000,
        }

        from unittest.mock import MagicMock

        mock_tv_client = MagicMock()
        mock_tv_client.is_available.return_value = True
        mock_tv_client.get_thai_stocks.return_value = [mock_tv_stock]

        import sys

        sys.modules["tv_client"] = mock_tv_client

        try:
            with patch("update_marks._fetch_price", return_value=None):
                results = update_marks.update_all()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["action"], "marked")
            self.assertEqual(results[0]["price"], 32.5)
            self.assertEqual(results[0]["pnl"], 250.0)

            # Check db state
            positions = paper_trade.list_positions(status_filter="open")
            self.assertEqual(positions[0]["last_price"], 32.5)
            self.assertEqual(positions[0]["unrealized_pnl"], 250.0)
        finally:
            if "tv_client" in sys.modules:
                del sys.modules["tv_client"]

    def test_update_marks_cached_price_fallback(self):
        paper_trade.open_position(
            symbol="KISS.BK", market="TH", shares=100, entry=3.46, stop=3.36, target=3.54
        )

        with (
            patch("update_marks._fetch_price", return_value=None),
            patch("update_marks._cached_price", return_value=3.48),
        ):
            results = update_marks.update_all()

        self.assertEqual(results[0]["action"], "marked")
        self.assertEqual(results[0]["price"], 3.48)
        self.assertAlmostEqual(results[0]["pnl"], 2.0)
        position = paper_trade.list_positions(status_filter="open")[0]
        self.assertEqual(position["last_price"], 3.48)

    def test_update_marks_closes_short_profit_target(self):
        with patch("paper_trade._now_iso", return_value="2026-07-01T09:00:00+00:00"):
            paper_trade.open_position(
                symbol="MOMO.BK",
                market="TH",
                shares=100,
                entry=100.0,
                stop=96.0,
                target=108.0,
                source="thai-swing-momentum",
            )

        with patch("update_marks._fetch_price", return_value=104.2):
            results = update_marks.update_all()

        self.assertEqual(results[0]["action"], "auto_closed_short_target")
        positions = paper_trade.list_positions(status_filter="closed")
        self.assertEqual(positions[0]["status"], "closed_target")
        self.assertAlmostEqual(positions[0]["exit_price"], 104.0)
        self.assertAlmostEqual(positions[0]["realized_r"], 1.0)

    def test_update_marks_closes_time_stop(self):
        with patch("paper_trade._now_iso", return_value="2026-07-01T09:00:00+00:00"):
            paper_trade.open_position(
                symbol="SLOW.BK",
                market="TH",
                shares=100,
                entry=100.0,
                stop=96.0,
                target=108.0,
                source="thai-swing-momentum",
            )

        with patch("update_marks._now_iso", return_value="2026-07-05T09:00:00+00:00"):
            with patch("paper_trade._now_iso", return_value="2026-07-05T09:00:00+00:00"):
                with patch("update_marks._fetch_price", return_value=99.0):
                    results = update_marks.update_all()

        self.assertEqual(results[0]["action"], "auto_closed_time")
        positions = paper_trade.list_positions(status_filter="closed")
        self.assertEqual(positions[0]["status"], "closed_time")
        self.assertAlmostEqual(positions[0]["exit_price"], 99.0)
        self.assertLess(positions[0]["realized_r"], 0)


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
