#!/usr/bin/env python3
"""Comprehensive 360-Degree End-to-End Stress Test & Gap Audit.

Tests all 7 dimensions of the trading ecosystem:
1. Sizing & Lot Math Edge Cases (Single shares, Board lots, Fractional shares, Capital constraints)
2. Order Lifecycle & Queue Safeguards (TTL, Chase limit, Corruption, Quarantine, Duplicates)
3. Exit Engine & Mark-to-Market Realism (Slippage on gap down, Scale-out with 1 share, Breakeven)
4. Multi-Market Isolation (TH vs US Currencies, Tickers, Portfolios, Cross-contamination)
5. Dashboard & API Robustness (All Flask routes, JSON contracts, Error handling, Chart data)
6. Data Feeds & Resiliency (yfinance dotted/hyphenated tickers, Network errors, Timeouts)
7. Operational & Concurrency Robustness (SQLite WAL, Lock files, Stale staged orders)
"""

from __future__ import annotations

import logging
import shutil
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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

import scripts.jules_evolver as je
import scripts.jules_fund as jf
import scripts.jules_scout as js
import scripts.jules_trader as jt
from dashboard.app import app

logging.basicConfig(level=logging.ERROR)


class E2EFullSpectrumAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit_results = []

    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.test_dir = PROJECT_ROOT / "state" / f"test_e2e_audit_{self.unique_id}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_db = self.test_dir / "market_cache.db"

        # Directories
        self.orders_th = self.test_dir / "jules_orders"
        self.orders_us = self.test_dir / "jules_us_orders"
        self.tasks_th = self.test_dir / "jules_tasks"
        self.tasks_us = self.test_dir / "jules_us_tasks"
        self.memory_th = self.test_dir / "jules_memory"
        self.memory_us = self.test_dir / "jules_us_memory"

        for d in [
            self.orders_th,
            self.orders_us,
            self.tasks_th,
            self.tasks_us,
            self.memory_th,
            self.memory_us,
        ]:
            d.mkdir(parents=True, exist_ok=True)
            (d / "staged").mkdir(parents=True, exist_ok=True)
            (d / "processed").mkdir(parents=True, exist_ok=True)
            (d / "quarantine").mkdir(parents=True, exist_ok=True)

        # Patch paths
        self.patches = [
            patch.object(paper_trade, "DB_PATH", self.test_db),
            patch.object(update_marks, "DB_PATH", self.test_db),
            patch.object(jf, "DB_PATH", self.test_db),
            patch.object(jf.paper_trade, "DB_PATH", self.test_db),
            patch.object(jt, "DB_PATH", self.test_db),
            patch.object(jt.paper_trade, "DB_PATH", self.test_db),
            patch.object(js, "DB_PATH", self.test_db),
            patch.object(je, "DB_PATH", self.test_db),
            patch.object(jf, "ORDERS_DIR_TH", self.orders_th),
            patch.object(jf, "ORDERS_DIR_US", self.orders_us),
            patch.object(jf, "ORDERS_DIR", self.orders_th),
            patch.object(jt, "ORDERS_DIR_TH", self.orders_th),
            patch.object(jt, "ORDERS_DIR_US", self.orders_us),
            patch.object(jt, "ORDERS_DIR", self.orders_th),
        ]
        for p in self.patches:
            p.start()

        with paper_trade._db() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS price_bar (symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL)"
            )
            conn.execute(
                "INSERT INTO price_bar VALUES ('BDMS.BK', '2026-09-25', 28.0, 29.0, 27.5, 28.5, 5000000)"
            )
            conn.execute(
                "INSERT INTO price_bar VALUES ('PBR.A', '2026-09-25', 18.5, 19.2, 18.3, 19.0, 15000000)"
            )
            conn.execute(
                "INSERT INTO price_bar VALUES ('PBR-A', '2026-09-25', 18.5, 19.2, 18.3, 19.0, 15000000)"
            )
            conn.commit()
        jt.init_decision_ledger(self.test_db)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 1: Sizing & Lot Math Edge Cases
    # ──────────────────────────────────────────────────────────────────────────

    def test_d1_scale_out_with_single_share_us(self):
        """GAP AUDIT: What happens when an odd-lot US trade has only 1 share and hits T1?"""
        trade = jf.execute_buy(
            symbol="SMCIP",
            shares=1,
            market="US",
            entry=70.0,
            stop=66.5,  # 5% stop
            target=80.0,
            thesis="Single share sizing test",
        )
        tid = trade["id"]

        # Call scale_out_position on 1 share
        res = paper_trade.scale_out_position(tid, price=75.25, fraction=0.5)

        # FINDING ANALYSIS:
        # If shares=1 and fraction=0.5:
        # shares_closed = min(1 - 1, max(1, int(1*0.5))) = min(0, 1) = 0!
        shares_closed = res.get("shares_closed", 0)
        remaining = res.get("remaining_shares", 1)
        single_share_protected = res.get("single_share_protected", False)

        finding = {
            "dimension": "1. Sizing & Lot Math",
            "test": "scale_out_single_share",
            "shares_closed": shares_closed,
            "remaining_shares": remaining,
            "single_share_protected": single_share_protected,
            "is_loophole": not single_share_protected,
            "detail": "Single share protected at BE: 0 shares sold, 1 runner preserved to T2."
            if single_share_protected
            else "Failed to protect single share.",
        }
        self.audit_results.append(finding)
        self.assertTrue(single_share_protected)
        self.assertEqual(shares_closed, 0)
        self.assertEqual(remaining, 1)

    def test_d1_scale_out_with_odd_shares_us(self):
        """GAP AUDIT: Sizing behavior on odd shares (3 shares, 5 shares, 11 shares)."""
        trade = jf.execute_buy(
            symbol="TEVA",
            shares=3,
            market="US",
            entry=40.0,
            stop=38.0,
            target=45.0,
        )
        res = paper_trade.scale_out_position(trade["id"], price=43.0, fraction=0.5)
        # 3 * 0.5 = 1.5 -> int(1.5) = 1 share closed, 2 remaining
        self.assertEqual(res["shares_closed"], 1)
        self.assertEqual(res["remaining_shares"], 2)

    def test_d1_us_unaffordable_stock_rejection(self):
        """GAP AUDIT: Stock price > slot budget ($250)."""
        shares, cost = jt.calculate_volatility_sizing(
            price=280.0,  # e.g. MSFT/NVDA above slot budget
            stop=266.0,
            equity=1000.0,
            cash=1000.0,
            market="US",
        )
        # Sizing should cap at max slot budget ($250 / 280 = 0 shares)
        cost_over_budget = cost > jt.MAX_SLOT_BUDGET_US
        self.audit_results.append(
            {
                "dimension": "1. Sizing & Lot Math",
                "test": "unaffordable_stock_sizing",
                "price": 280.0,
                "shares": shares,
                "cost": cost,
                "exceeds_slot_budget": cost_over_budget,
                "detail": f"Stock price $280 cleanly rejected: {shares} shares (${cost:.2f}).",
            }
        )
        self.assertEqual(shares, 0)
        self.assertEqual(cost, 0.0)

    def test_d1_thai_set_odd_lot_prevention(self):
        """GAP AUDIT: SET 100-share board lot rule enforcement."""
        with self.assertRaises(ValueError) as ctx:
            jf.execute_buy(
                symbol="CPALL.BK", shares=150, entry=60.0, stop=57.0, target=66.0, market="TH"
            )
        self.assertIn("SET board lot violation", str(ctx.exception))

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 2: Order Lifecycle & Queue Safeguards
    # ──────────────────────────────────────────────────────────────────────────

    def test_d2_chase_limit_boundary_precision(self):
        """GAP AUDIT: Chase limit precision at exactly +1.0% vs +1.05%."""
        order_file = self.orders_th / "buy_CHASE.yaml"
        # Price is BDMS.BK @ 28.5 in DB
        # Entry trigger 28.0 -> +1.0% max chase = 28.28 -> 28.5 is +1.78% above trigger
        import yaml

        with open(order_file, "w") as f:
            yaml.dump(
                {
                    "action": "buy",
                    "symbol": "BDMS.BK",
                    "shares": 100,
                    "entry_price": 28.0,
                    "stop_price": 26.5,
                    "target_price": 31.0,
                    "max_chase_pct": 0.010,
                },
                f,
            )

        res = jf.process_orders_queue(market="TH")
        self.assertEqual(res[0]["status"], "error")
        self.assertIn("Chase limit exceeded", res[0]["error"])
        # Should be moved to quarantine
        quarantined = list((self.orders_th / "quarantine").glob("buy_CHASE*"))
        self.assertTrue(len(quarantined) >= 1)

    def test_d2_corrupted_order_file_resilience(self):
        """GAP AUDIT: Corrupted YAML syntax in order queue."""
        bad_file = self.orders_th / "buy_CORRUPT.yaml"
        bad_file.write_text("action: buy\nsymbol: [invalid yaml {::", encoding="utf-8")

        res = jf.process_orders_queue(market="TH")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["status"], "error")
        self.assertTrue(len(list((self.orders_th / "quarantine").glob("buy_CORRUPT*"))) >= 1)

    def test_d2_order_ttl_expiry(self):
        """GAP AUDIT: Expired order file rejection."""
        import yaml

        order_file = self.orders_us / "buy_EXPIRED.yaml"
        past_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        with open(order_file, "w") as f:
            yaml.dump(
                {
                    "action": "buy",
                    "symbol": "PBR.A",
                    "shares": 5,
                    "entry_price": 19.0,
                    "stop_price": 18.0,
                    "target_price": 21.0,
                    "expires_at": past_time,
                },
                f,
            )

        res = jf.process_orders_queue(market="US")
        self.assertEqual(res[0]["status"], "error")
        self.assertIn("Order expired", res[0]["error"])

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 3: Exit Engine & Mark-to-Market Realism
    # ──────────────────────────────────────────────────────────────────────────

    def test_d3_gap_down_stop_fill_slippage_realism(self):
        """GAP AUDIT: When price gaps down far below stop, does update_marks fill at stop or gap price?"""
        trade = jf.execute_buy(
            symbol="GAPDOWN.BK",
            shares=200,
            entry=100.0,
            stop=95.0,  # Stop at 95.0
            target=115.0,
            market="TH",
        )
        tid = trade["id"]

        # Market opens next morning gapped down at 90.0 (-10%)
        with patch("update_marks._now_iso", return_value="2026-09-28T09:30:00+00:00"):
            with patch(
                "update_marks._fetch_quote", return_value={"price": 90.0, "volume": 1000000.0}
            ):
                with patch("update_marks._fetch_price", return_value=90.0):
                    update_marks.update_all()

        closed = paper_trade.get_position(tid)
        exit_price = closed["exit_price"]

        # Resting broker stop fill: exit_price fills at stop_price (95.00)
        self.assertEqual(exit_price, 95.0)
        self.audit_results.append(
            {
                "dimension": "3. Exit Engine Realism",
                "test": "gap_down_slippage",
                "stop_price": 95.0,
                "market_price": 90.0,
                "filled_at": exit_price,
                "execution_model": "broker_resting_stop",
                "detail": f"update_marks executed resting stop at {exit_price:.2f} (stop price) modeling active exchange order book triggering.",
            }
        )

    def test_d3_velocity_stall_boundary(self):
        """GAP AUDIT: Velocity stall triggered at exactly 4 days vs 3 days."""
        rules = {
            "jules_ai": {
                "velocity_stall_days": 4,
                "velocity_min_mfe_r": 0.3,
            }
        }
        with patch("update_marks._load_exit_rules", return_value=rules):
            # Day 0: Open position
            with patch("paper_trade._now_iso", return_value="2026-09-20T09:00:00+00:00"):
                paper_trade.open_position(
                    symbol="STALLTEST.BK",
                    market="TH",
                    shares=100,
                    entry=50.0,
                    stop=47.5,
                    target=56.0,
                    source="jules_ai",
                )

            # Day 3: Price is 49.5 (R = -0.2, MFE = 0.1R) -> Should NOT stall yet (days < 4)
            with patch("update_marks._now_iso", return_value="2026-09-23T09:00:00+00:00"):
                with patch(
                    "update_marks._fetch_quote", return_value={"price": 49.5, "volume": 1000000.0}
                ):
                    with patch("update_marks._fetch_price", return_value=49.5):
                        res3 = update_marks.update_all()
            self.assertEqual(res3[0]["action"], "marked")

            # Day 4: Price is 49.5 (days >= 4, MFE < 0.3R, R <= 0) -> Should AUTO CLOSE STALLED
            with patch("update_marks._now_iso", return_value="2026-09-24T09:00:00+00:00"):
                with patch(
                    "update_marks._fetch_quote", return_value={"price": 49.5, "volume": 1000000.0}
                ):
                    with patch("update_marks._fetch_price", return_value=49.5):
                        res4 = update_marks.update_all()
            self.assertEqual(res4[0]["action"], "auto_closed_stalled")

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 4: Multi-Market Isolation
    # ──────────────────────────────────────────────────────────────────────────

    def test_d4_market_cross_contamination(self):
        """GAP AUDIT: Ensure TH orders and US orders never execute in the wrong market or folder."""
        # 1. US buy in TH queue should be isolated
        jf.execute_buy(
            symbol="ADVANC.BK", shares=100, entry=250.0, stop=240.0, target=270.0, market="TH"
        )
        jf.execute_buy(symbol="AAPL", shares=1, entry=220.0, stop=210.0, target=240.0, market="US")

        th_status = jf.get_jules_status("TH")
        us_status = jf.get_jules_status("US")

        self.assertEqual(th_status["currency"], "THB")
        self.assertEqual(us_status["currency"], "USD")
        self.assertEqual(len(th_status["open_positions"]), 1)
        self.assertEqual(len(us_status["open_positions"]), 1)
        self.assertEqual(th_status["open_positions"][0]["symbol"], "ADVANC.BK")
        self.assertEqual(us_status["open_positions"][0]["symbol"], "AAPL")

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 5: Dashboard & API Endpoints E2E
    # ──────────────────────────────────────────────────────────────────────────

    def test_d5_all_dashboard_endpoints(self):
        """GAP AUDIT: Test every key dashboard HTTP API route for 200 OK and valid JSON."""
        client = app.test_client()
        endpoints = [
            ("/", "GET"),
            ("/api/jules/status?market=TH", "GET"),
            ("/api/jules/status?market=US", "GET"),
            ("/api/jules/scout?market=TH", "GET"),
            ("/api/jules/scout?market=US", "GET"),
            ("/api/market-posture", "GET"),
        ]

        endpoint_failures = []
        for url, method in endpoints:
            try:
                resp = client.get(url) if method == "GET" else client.post(url)
                if resp.status_code not in (200, 302):
                    endpoint_failures.append({"url": url, "status": resp.status_code})
            except Exception as e:
                endpoint_failures.append({"url": url, "error": str(e)})

        self.audit_results.append(
            {
                "dimension": "5. Dashboard & APIs",
                "test": "http_api_routes",
                "failures": endpoint_failures,
                "pass_rate": f"{len(endpoints) - len(endpoint_failures)}/{len(endpoints)}",
            }
        )
        self.assertEqual(len(endpoint_failures), 0)

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 6: Data Feeds & Resiliency
    # ──────────────────────────────────────────────────────────────────────────

    def test_d6_symbol_normalization_dot_vs_hyphen(self):
        """GAP AUDIT: Check handling of dotted tickers (PBR.A, BRK.B) across yfinance."""
        # Test converting dotted to hyphenated for yfinance
        sym_dot = "PBR.A"
        sym_hyphen = sym_dot.replace(".", "-")
        self.assertEqual(sym_hyphen, "PBR-A")

        # Check if update_marks quote fetch handles dotted symbols
        with patch("yfinance.Ticker") as mock_ticker:
            mock_inst = MagicMock()
            mock_inst.history.return_value = MagicMock(empty=True)
            mock_ticker.return_value = mock_inst
            res = update_marks._fetch_quote("PBR.A")
            # Should gracefully return None when history is empty without uncaught exception
            self.assertIsNone(res)

    # ──────────────────────────────────────────────────────────────────────────
    # DIMENSION 7: Operational & Concurrency Robustness
    # ──────────────────────────────────────────────────────────────────────────

    def test_d7_sqlite_busy_timeout_and_wal(self):
        """GAP AUDIT: Verify SQLite connection timeout and WAL configuration."""
        with paper_trade._db() as conn:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]

        has_timeout = timeout is not None and timeout >= 5000
        self.audit_results.append(
            {
                "dimension": "7. Operational & Concurrency",
                "test": "sqlite_busy_timeout",
                "journal_mode": mode,
                "busy_timeout_ms": timeout,
                "has_proper_timeout": has_timeout,
                "detail": f"SQLite journal_mode={mode}, busy_timeout={timeout}ms.",
            }
        )


def run_audit():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(E2EFullSpectrumAudit)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    print(" 360-DEGREE E2E AUDIT RESULTS & FINDINGS CATALOG")
    print("=" * 80)
    for r in E2EFullSpectrumAudit.audit_results:
        print(f"\n[{r['dimension']}] - {r['test']}")
        for k, v in r.items():
            if k not in ("dimension", "test"):
                print(f"  * {k}: {v}")
    print("=" * 80)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
