#!/usr/bin/env python3
"""Unit tests for Jules AI Fund MFE Ratchet stop and Resistance-Aware target calculation."""

import shutil
import sqlite3
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

import paper_trade
import update_marks

import scripts.jules_fund as jf
import scripts.jules_scout as js


class TestJulesRatchetAndResistance(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.test_dir = PROJECT_ROOT / "state" / f"test_jules_ratchet_{self.unique_id}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_db = self.test_dir / "test_market_cache.db"
        self.test_orders = self.test_dir / "orders"
        self.test_orders.mkdir(parents=True, exist_ok=True)

        # Patch paths in paper_trade, update_marks, jules_fund, and jules_scout
        self.patch_pt_db = patch.object(paper_trade, "DB_PATH", self.test_db)
        self.patch_um_db = patch.object(update_marks, "DB_PATH", self.test_db)
        self.patch_jf_db = patch.object(jf, "DB_PATH", self.test_db)
        self.patch_js_db = patch.object(js, "DB_PATH", self.test_db)
        self.patch_jf_pt_db = patch.object(jf.paper_trade, "DB_PATH", self.test_db)
        self.patch_jf_orders = patch.object(jf, "ORDERS_DIR", self.test_orders)
        self.patch_jf_processed = patch.object(
            jf, "PROCESSED_ORDERS_DIR", self.test_orders / "processed"
        )

        self.patch_pt_db.start()
        self.patch_um_db.start()
        self.patch_jf_db.start()
        self.patch_js_db.start()
        self.patch_jf_pt_db.start()
        self.patch_jf_orders.start()
        self.patch_jf_processed.start()

        # Initialize schema
        with sqlite3.connect(self.test_db) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS price_bar (
                    symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL
                )"""
            )

    def tearDown(self):
        self.patch_pt_db.stop()
        self.patch_um_db.stop()
        self.patch_jf_db.stop()
        self.patch_js_db.stop()
        self.patch_jf_pt_db.stop()
        self.patch_jf_orders.stop()
        self.patch_jf_processed.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_jules_ratchet_breakeven_trigger(self):
        """Verify that when a jules_ai trade reaches +0.55R, the stop is moved to breakeven (entry price),
        and subsequent reversal closes it as closed_ratchet without capital loss."""
        trade = jf.execute_buy(
            symbol="TEST.BK",
            shares=500,
            entry=10.0,
            stop=9.0,  # Risk = 1.0 THB per share
            target=12.0,
            thesis="Testing breakeven ratchet",
        )
        self.assertEqual(trade["symbol"], "TEST.BK")
        self.assertEqual(trade["source"], "jules_ai")

        # Check that ratchet_tiers is registered in decision_trace
        pos = paper_trade.list_positions(status_filter="open")[0]
        self.assertEqual(pos["stop_price"], 9.0)

        # Step 1: Price rises to 10.55 (+0.55R) -> should trigger Tier 1 [0.5, 0.0] -> stop moved to 10.0 (entry)
        with patch("update_marks._now_iso", return_value="2026-09-15T09:30:00+00:00"):
            with patch("update_marks._fetch_price", return_value=10.55):
                res1 = update_marks.update_all()

        self.assertEqual(res1[0]["action"], "marked")
        pos_after_rise = paper_trade.list_positions(status_filter="open")[0]
        # Stop should now be ratcheted to entry price (10.0)
        self.assertAlmostEqual(pos_after_rise["stop_price"], 10.0)

        # Step 2: Market maker dumps price back to 9.80 (below ratcheted stop 10.0)
        with patch("update_marks._now_iso", return_value="2026-09-15T10:00:00+00:00"):
            with patch("update_marks._fetch_price", return_value=9.80):
                res2 = update_marks.update_all()

        self.assertEqual(res2[0]["action"], "auto_closed_ratchet")
        closed_pos = paper_trade.list_positions(status_filter="closed")[0]
        self.assertEqual(closed_pos["status"], "closed_ratchet")
        self.assertAlmostEqual(closed_pos["exit_price"], 10.0)
        # Gross loss is 0 (exited at entry price 10.0), net loss is only tiny transaction fees
        self.assertGreaterEqual(closed_pos["realized_pnl"], -25.0)

    def test_jules_ratchet_tier2_lock_profit(self):
        """Verify that reaching +1.1R raises stop to +0.5R."""
        jf.execute_buy(
            symbol="TEST2.BK",
            shares=500,
            entry=10.0,
            stop=9.0,  # Risk = 1.0 THB
            target=12.0,
            thesis="Testing tier 2 ratchet",
        )

        # Price rises to 11.10 (+1.1R) -> triggers Tier 2 [1.0, 0.5] -> stop moves to 10.0 + 0.5*1.0 = 10.5
        with patch("update_marks._now_iso", return_value="2026-09-15T09:30:00+00:00"):
            with patch("update_marks._fetch_price", return_value=11.10):
                update_marks.update_all()

        pos = paper_trade.list_positions(status_filter="open")[0]
        self.assertAlmostEqual(pos["stop_price"], 10.5)

        # Price drops to 10.30 -> auto-closes at 10.5 with locked profit
        with patch("update_marks._now_iso", return_value="2026-09-15T10:00:00+00:00"):
            with patch("update_marks._fetch_price", return_value=10.30):
                res = update_marks.update_all()

        self.assertEqual(res[0]["action"], "auto_closed_ratchet")
        closed = paper_trade.list_positions(status_filter="closed")[0]
        self.assertAlmostEqual(closed["exit_price"], 10.5)
        self.assertGreater(closed["realized_pnl"], 200.0)

    def test_resistance_aware_target_calculation(self):
        """Verify that find_nearest_resistance detects swing high and caps target at resistance pivot."""
        # Insert historical price bars for MOMO.BK
        with sqlite3.connect(self.test_db) as conn:
            conn.execute(
                "INSERT INTO price_bar VALUES ('MOMO.BK', '2026-09-10', 9.5, 10.75, 9.4, 10.2, 1000000)"
            )

        nearest = js.find_nearest_resistance("MOMO.BK", current_price=10.0)
        self.assertAlmostEqual(nearest, 10.75)

        levels = js.calculate_sizing_and_levels(price=10.0, symbol="MOMO.BK", suggested_stop=9.50)
        # 10.0 + 0.5 * 1.1 = 10.55 <= 10.75 <= 11.0 (default 2.0R)
        self.assertAlmostEqual(levels["target"], 10.75)
        self.assertIn("Resistance Pivot", levels["target_note"])


if __name__ == "__main__":
    unittest.main()
