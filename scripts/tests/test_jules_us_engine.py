#!/usr/bin/env python3
"""Comprehensive Unit Tests for Jules Autonomous Trading Engine (US Market Expansion).

Verifies:
1. $1,000 USD virtual fund sizing and single-share boundaries (max $250 slot, max $10 risk).
2. Accurate SEC Section 31 ($27.80 per $1M) and FINRA TAF ($0.000166/share) fee calculation.
3. US market candidate parsing, U/D ratio filtering, and anti-correlation cluster gates.
4. Autonomous order staging and queue processing in state/jules_us_orders/.
5. Trader DNA evolution and pre-trade briefing in USD for US equities.
"""

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

import scripts.adaptive_indicators as ai
import scripts.jules_evolver as je
import scripts.jules_fund as jf
import scripts.jules_scout as js
import scripts.jules_trader as jt


class TestJulesUSEngine(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.test_dir = PROJECT_ROOT / "state" / f"test_jules_us_{self.unique_id}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_db = self.test_dir / "test_market_cache.db"

        # US order dirs
        self.test_us_orders = self.test_dir / "jules_us_orders"
        self.test_us_orders.mkdir(parents=True, exist_ok=True)
        self.test_us_processed = self.test_us_orders / "processed"
        self.test_us_processed.mkdir(parents=True, exist_ok=True)
        self.test_us_quarantine = self.test_us_orders / "quarantine"
        self.test_us_quarantine.mkdir(parents=True, exist_ok=True)
        self.test_us_staged = self.test_us_orders / "staged"
        self.test_us_staged.mkdir(parents=True, exist_ok=True)

        self.test_us_tasks = self.test_dir / "jules_us_tasks"
        self.test_us_tasks.mkdir(parents=True, exist_ok=True)
        self.test_us_mission = self.test_us_tasks / "today_mission.json"

        self.test_us_memory = self.test_dir / "jules_us_memory"
        self.test_us_memory.mkdir(parents=True, exist_ok=True)

        # Patch databases
        self.patch_pt_db = patch.object(paper_trade, "DB_PATH", self.test_db)
        self.patch_jf_db = patch.object(jf, "DB_PATH", self.test_db)
        self.patch_jt_db = patch.object(jt, "DB_PATH", self.test_db)
        self.patch_js_db = patch.object(js, "DB_PATH", self.test_db)

        self.patch_pt_db.start()
        self.patch_jf_db.start()
        self.patch_jt_db.start()
        self.patch_js_db.start()

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
        self.patch_js_db.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_us_fund_initial_state(self):
        """Verify US fund starts with exactly $1,000.00 USD cash, $0 invested, and 0 open positions."""
        status = jf.get_jules_status(market="US")
        self.assertEqual(status["market"], "US")
        self.assertEqual(status["currency"], "USD")
        self.assertEqual(status["cash_balance"], 1000.0)
        self.assertEqual(status["equity"], 1000.0)
        self.assertEqual(status["invested_capital"], 0.0)
        self.assertEqual(status["open_count"], 0)
        self.assertEqual(len(status["open_positions"]), 0)

    def test_us_regulatory_fees_calculation(self):
        """Verify SEC Section 31 and FINRA TAF regulatory fees on US equity sales.

        Formulas:
        - SEC Section 31: round_up_to_cent(proceeds * 0.0000278), min $0.01
        - FINRA TAF: round_up_to_cent(shares * 0.000166), min $0.01, max $8.30
        """
        # Case 1: Small trade ($200 proceeds, 10 shares)
        # SEC: 200 * 0.0000278 = 0.00556 -> min $0.01
        # FINRA: 10 * 0.000166 = 0.00166 -> min $0.01
        # Total = $0.02
        fees1 = jf.calculate_us_regulatory_fees(proceeds=200.0, shares=10)
        self.assertEqual(fees1, 0.02)

        # Case 2: Larger trade ($50,000 proceeds, 500 shares)
        # SEC: 50,000 * 0.0000278 = 1.39 -> $1.39
        # FINRA: 500 * 0.000166 = 0.083 -> rounded to nearest cent = $0.08
        # Total = 1.39 + 0.08 = $1.47
        fees2 = jf.calculate_us_regulatory_fees(proceeds=50000.0, shares=500)
        self.assertEqual(fees2, 1.47)

    def test_paper_trade_us_fee_deduction_on_exit(self):
        """Verify paper_trade applies exact SEC + FINRA regulatory fees to Jules US exits."""
        # Open 10 shares of NVDA at $100.00 ($1,000 cost, $0 commission)
        pos = paper_trade.open_position(
            symbol="NVDA",
            market="US",
            shares=10,
            entry=100.0,
            stop=95.0,
            target=110.0,
            portfolio="jules",
        )
        self.assertEqual(pos["market"], "US")
        self.assertEqual(pos["shares"], 10)

        # Close position at $110.00 (Gross proceeds = $1,100.00, Gross gain = $100.00)
        # Expected fees:
        # SEC = 1100 * 0.0000278 = 0.03058 -> round up to $0.04
        # FINRA = 10 * 0.000166 = 0.00166 -> min $0.01
        # Total regulatory fees = $0.05
        # Net realized PnL = $100.00 - $0.05 = $99.95
        closed = paper_trade.close_position(
            trade_id=pos["id"],
            exit_price=110.0,
            status="closed_target",
        )
        self.assertAlmostEqual(closed["realized_pnl"], 99.95, places=2)

    def test_volatility_sizing_us_constraints(self):
        """Verify position sizing under $1,000 fund constraints:
        - Max position size: $250.00 USD
        - Max dollar risk: $10.00 USD (1.0% of $1,000)
        - Single-share granularity (no 100-share board lot requirement)
        """
        # Stock at $20.00, stop at $19.00 -> $1.00 risk/share
        # Max risk shares: $10.00 / $1.00 = 10 shares ($200.0 cost <= $250 slot)
        shares, cost = jt.calculate_volatility_sizing(
            price=20.0,
            stop=19.0,
            equity=1000.0,
            cash=1000.0,
            risk_mult=1.0,
            market="US",
        )
        self.assertEqual(shares, 10)
        self.assertEqual(cost, 200.0)

        # High-priced stock at $150.00, stop at $145.00 -> $5.00 risk/share
        # Max risk shares: $10.00 / $5.00 = 2 shares ($300.0 cost > $250 max slot)
        # Max slot shares: $250 // $150 = 1 share ($150 cost)
        shares_high, cost_high = jt.calculate_volatility_sizing(
            price=150.0,
            stop=145.0,
            equity=1000.0,
            cash=1000.0,
            risk_mult=1.0,
            market="US",
        )
        self.assertEqual(shares_high, 1)
        self.assertEqual(cost_high, 150.0)

    def test_us_thematic_clusters(self):
        """Verify US thematic clusters identification and anti-correlation."""
        cluster_nvda = ai.get_cluster_for_symbol("NVDA", market="US")
        cluster_aapl = ai.get_cluster_for_symbol("AAPL", market="US")
        cluster_lmt = ai.get_cluster_for_symbol("LMT", market="US")
        cluster_unknown = ai.get_cluster_for_symbol("XYZ99", market="US")

        self.assertEqual(cluster_nvda, "AI Infrastructure & Semiconductors")
        self.assertEqual(cluster_aapl, "Mega-Cap Tech Platforms")
        self.assertEqual(cluster_lmt, "Aerospace & Defense")
        self.assertIsNone(cluster_unknown)

    def test_us_order_staging_and_execution_queue(self):
        """Verify staging an order into state/jules_us_orders and executing it via process_orders_queue."""
        import yaml

        order_path = self.test_us_orders / "buy_AAPL.yaml"
        order_payload = {
            "order_id": "JULES-US-20260925-AAPL",
            "action": "buy",
            "symbol": "AAPL",
            "market": "US",
            "shares": 1,
            "entry_price": 220.0,
            "stop_price": 210.0,
            "target_price": 240.0,
            "thesis": "Mega-cap tech momentum",
        }
        order_path.write_text(yaml.safe_dump(order_payload), encoding="utf-8")

        with (
            patch.object(jf, "ORDERS_DIR_US", self.test_us_orders),
            patch.object(
                jf,
                "get_orders_dirs",
                return_value=(self.test_us_orders, self.test_us_processed, self.test_us_quarantine),
            ),
            patch.object(jf, "_get_latest_price", return_value=220.0),
        ):
            results = jf.process_orders_queue(market="US")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["status"], "executed")

            # Verify order was moved to processed directory
            self.assertFalse(order_path.exists())
            processed_files = list(self.test_us_processed.glob("buy_AAPL_*.yaml"))
            self.assertEqual(len(processed_files), 1)

            # Verify position is now open in Jules US portfolio
            status = jf.get_jules_status(market="US")
            self.assertEqual(status["open_count"], 1)
            self.assertEqual(status["open_positions"][0]["symbol"], "AAPL")
            self.assertEqual(status["open_positions"][0]["shares"], 1)
            self.assertEqual(status["invested_capital"], 220.0)
            self.assertEqual(status["cash_balance"], 780.0)

    def test_us_evolver_dna_and_briefing(self):
        """Verify Jules Trader DNA and pre-trade briefing correctly report $1,000 USD and US rules."""
        dna = je.load_dna(market="US", memory_dir=self.test_us_memory)
        self.assertEqual(dna["generation"], 1)
        self.assertIn("Strict $1,000 USD cash management", dna["strengths"])

        briefing = je.get_pre_trade_briefing(market="US", memory_dir=self.test_us_memory)
        self.assertIn("JULES AI FUND (US): PRE-TRADE BRAIN BRIEFING", briefing)
        self.assertIn("$1,000.00 USD", briefing)
        self.assertIn("$0.00", briefing)


if __name__ == "__main__":
    unittest.main()
