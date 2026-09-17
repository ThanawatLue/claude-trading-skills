#!/usr/bin/env python3
"""Comprehensive Unit Tests for Jules Autonomous Decision Engine & Order Queue Safeguards."""

import json
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

import scripts.jules_fund as jf
import scripts.jules_trader as jt


class TestJulesTrader(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.test_dir = PROJECT_ROOT / "state" / f"test_jules_trader_{self.unique_id}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_db = self.test_dir / "test_market_cache.db"
        self.test_orders = self.test_dir / "orders"
        self.test_orders.mkdir(parents=True, exist_ok=True)
        self.test_processed = self.test_orders / "processed"
        self.test_processed.mkdir(parents=True, exist_ok=True)
        self.test_quarantine = self.test_orders / "quarantine"
        self.test_quarantine.mkdir(parents=True, exist_ok=True)
        self.test_staged = self.test_orders / "staged"
        self.test_staged.mkdir(parents=True, exist_ok=True)

        self.test_mission_file = self.test_dir / "today_mission.json"

        # Patch paths
        self.patch_pt_db = patch.object(paper_trade, "DB_PATH", self.test_db)
        self.patch_jf_db = patch.object(jf, "DB_PATH", self.test_db)
        self.patch_jt_db = patch.object(jt, "DB_PATH", self.test_db)
        self.patch_jf_pt_db = patch.object(jf.paper_trade, "DB_PATH", self.test_db)
        self.patch_jt_pt_db = patch.object(jt.paper_trade, "DB_PATH", self.test_db)

        self.patch_jf_orders = patch.object(jf, "ORDERS_DIR", self.test_orders)
        self.patch_jf_processed = patch.object(jf, "PROCESSED_ORDERS_DIR", self.test_processed)
        self.patch_jf_quarantine = patch.object(jf, "QUARANTINE_ORDERS_DIR", self.test_quarantine)

        self.patch_jt_orders = patch.object(jt, "ORDERS_DIR", self.test_orders)
        self.patch_jt_staged = patch.object(jt, "STAGED_ORDERS_DIR", self.test_staged)
        self.patch_jt_mission = patch.object(jt, "MISSION_JSON", self.test_mission_file)

        self.patch_pt_db.start()
        self.patch_jf_db.start()
        self.patch_jt_db.start()
        self.patch_jf_pt_db.start()
        self.patch_jt_pt_db.start()
        self.patch_jf_orders.start()
        self.patch_jf_processed.start()
        self.patch_jf_quarantine.start()
        self.patch_jt_orders.start()
        self.patch_jt_staged.start()
        self.patch_jt_mission.start()

        # Initialize schema
        with sqlite3.connect(self.test_db) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS price_bar (
                    symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL
                )"""
            )
        jt.init_decision_ledger(self.test_db)

    def tearDown(self):
        self.patch_pt_db.stop()
        self.patch_jf_db.stop()
        self.patch_jt_db.stop()
        self.patch_jf_pt_db.stop()
        self.patch_jt_pt_db.stop()
        self.patch_jf_orders.stop()
        self.patch_jf_processed.stop()
        self.patch_jf_quarantine.stop()
        self.patch_jt_orders.stop()
        self.patch_jt_staged.stop()
        self.patch_jt_mission.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_set_tick_ladder(self):
        """Verify SET tick ladder rules and discretization."""
        self.assertEqual(jt.round_to_set_tick(1.537, "up"), 1.54)
        self.assertEqual(jt.round_to_set_tick(1.537, "down"), 1.53)

        # 5.00 - 10.00 tick is 0.05
        self.assertEqual(jt.round_to_set_tick(8.87, "down"), 8.85)
        self.assertEqual(jt.round_to_set_tick(8.87, "up"), 8.90)

        # 10.00 - 25.00 tick is 0.10
        self.assertEqual(jt.round_to_set_tick(13.43, "down"), 13.40)
        self.assertEqual(jt.round_to_set_tick(13.43, "up"), 13.50)

    def test_idempotency_ledger(self):
        """Verify that calling run_autonomous_decision twice does not duplicate actions."""
        # Create dummy mission
        mission = {
            "candidates": [
                {
                    "symbol": "SPRC.BK",
                    "price": 13.40,
                    "stop": 12.90,
                    "target": 14.40,
                    "sector": "Energy Minerals",
                    "score": 75.0,
                    "highlights": "Refinery momentum",
                }
            ]
        }
        self.test_mission_file.write_text(json.dumps(mission), encoding="utf-8")

        with patch.object(
            jt,
            "get_latest_exposure_posture",
            return_value={"recommendation": "NORMAL", "exposure_ceiling_pct": 75},
        ):
            res1 = jt.run_autonomous_decision(market="TH")
            self.assertEqual(res1["status"], "ORDER_STAGED")
            self.assertEqual(res1["symbol"], "SPRC.BK")

            # Second run without force should return the existing decision without modifying files
            res2 = jt.run_autonomous_decision(market="TH")
            self.assertEqual(res2["status"], "ORDER_STAGED")
            self.assertEqual(res2["symbol"], "SPRC.BK")

    def test_circuit_breaker_consecutive_losses(self):
        """Verify that 3 consecutive closed losses halts trading."""
        # Insert 3 losing closed trades in paper_trade
        for i in range(1, 4):
            paper_trade.open_position(
                symbol=f"LOSS{i}.BK",
                market="TH",
                shares=100,
                entry=10.0,
                stop=9.0,
                target=12.0,
                portfolio="jules",
            )
            # Close with loss
            paper_trade.close_position(i, exit_price=9.0, status="closed_stop")

        allowed, risk_mult, reason = jt.check_circuit_breakers(market="TH")
        self.assertFalse(allowed)
        self.assertEqual(risk_mult, 0.0)
        self.assertIn("3 consecutive closed losses", reason)

        res = jt.run_autonomous_decision(force=True, market="TH")
        self.assertEqual(res["status"], "BLOCKED_CIRCUIT")

    def test_anti_correlation_sector_filter(self):
        """Verify that Jules rejects candidates in sectors already active in portfolio."""
        # Open an Energy position
        paper_trade.open_position(
            symbol="PTTEP.BK",
            market="TH",
            shares=100,
            entry=150.0,
            stop=140.0,
            target=170.0,
            portfolio="jules",
            decision_trace={"sector": "Energy Minerals"},
        )

        candidates = [
            {
                "symbol": "SPRC.BK",
                "price": 13.40,
                "stop": 12.90,
                "target": 14.40,
                "sector": "Energy Minerals",
                "score": 85.0,
            },
            {
                "symbol": "KCE.BK",
                "price": 65.00,
                "stop": 62.00,
                "target": 71.00,
                "sector": "Electronic Technology",
                "score": 75.0,
            },
        ]

        open_pos = paper_trade.list_positions(status_filter="open", portfolio="jules")
        # Ensure open_pos has sector populated
        open_pos[0]["sector"] = "Energy Minerals"

        winner, reason = jt.evaluate_and_select_trade(
            candidates=candidates,
            open_positions=open_pos,
            sector_mods={},
            equity=30000.0,
            cash=15000.0,
        )

        # SPRC should be skipped because Energy Minerals is active; KCE should be chosen!
        self.assertIsNotNone(winner)
        self.assertEqual(winner["symbol"], "KCE.BK")

    def test_dead_letter_quarantine_on_invalid_order(self):
        """Verify that invalid/failing orders are quarantined and do not cause infinite loops."""
        bad_order = self.test_orders / "buy_BAD.yaml"
        # Write invalid order: shares violation (15 shares not divisible by 100)
        import yaml

        bad_order.write_text(
            yaml.safe_dump({"action": "buy", "symbol": "BAD.BK", "shares": 15, "entry_price": 10.0})
        )

        results = jf.process_orders_queue(market="TH")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "error")

        # Original order file must be moved OUT of active orders dir
        self.assertFalse(bad_order.exists())

        # Must be in quarantine directory
        quarantined = list(self.test_quarantine.glob("buy_BAD_*"))
        self.assertTrue(len(quarantined) >= 1)
        # Error log must be written
        err_file = list(self.test_quarantine.glob("*.error.json"))
        self.assertTrue(len(err_file) >= 1)

    def test_chase_limit_guard(self):
        """Verify that orders where current market price exceeds chase limit (+1.0%) are rejected and quarantined."""
        order_path = self.test_orders / "buy_CHASE.yaml"
        import yaml

        order_path.write_text(
            yaml.safe_dump(
                {
                    "action": "buy",
                    "symbol": "CHASE.BK",
                    "shares": 100,
                    "entry_price": 10.00,
                    "stop_price": 9.50,
                    "target_price": 11.00,
                    "max_chase_pct": 0.01,
                }
            )
        )

        # Mock market price to 10.30 (+3.0% above 10.00 entry)
        with patch.object(jf, "_get_latest_price", return_value=10.30):
            results = jf.process_orders_queue(market="TH")

        self.assertEqual(results[0]["status"], "error")
        self.assertIn("Chase limit exceeded", results[0]["error"])
        # File should be quarantined
        self.assertFalse(order_path.exists())
        self.assertTrue(len(list(self.test_quarantine.glob("buy_CHASE_*"))) >= 1)

    def test_ttl_expiration_guard(self):
        """Verify that orders past their expires_at timestamp are rejected and quarantined."""
        order_path = self.test_orders / "buy_EXPIRED.yaml"
        import yaml

        past_time = "2026-09-17T01:00:00+00:00"  # in the past
        order_path.write_text(
            yaml.safe_dump(
                {
                    "action": "buy",
                    "symbol": "EXP.BK",
                    "shares": 100,
                    "entry_price": 10.00,
                    "stop_price": 9.50,
                    "target_price": 11.00,
                    "expires_at": past_time,
                }
            )
        )

        results = jf.process_orders_queue(market="TH")
        self.assertEqual(results[0]["status"], "error")
        self.assertIn("Order expired", results[0]["error"])
        self.assertFalse(order_path.exists())
        self.assertTrue(len(list(self.test_quarantine.glob("buy_EXPIRED_*"))) >= 1)

    def test_prudence_gate_reduce_only(self):
        """Verify that when exposure posture is REDUCE_ONLY, Jules decides to HOLD_CASH."""
        mission = {
            "candidates": [
                {
                    "symbol": "SPRC.BK",
                    "price": 13.40,
                    "stop": 12.90,
                    "target": 14.40,
                    "sector": "Energy Minerals",
                    "score": 75.0,
                }
            ]
        }
        self.test_mission_file.write_text(json.dumps(mission), encoding="utf-8")

        with patch.object(
            jt,
            "get_latest_exposure_posture",
            return_value={"recommendation": "REDUCE_ONLY", "exposure_ceiling_pct": 20},
        ):
            res = jt.run_autonomous_decision(force=True, market="TH")

        self.assertEqual(res["status"], "HOLD_CASH")
        self.assertIn("Prudence gate: holding 100% cash", res["reason"])


if __name__ == "__main__":
    unittest.main()
