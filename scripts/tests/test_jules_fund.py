import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

import paper_trade

import scripts.jules_fund as jf


class TestJulesFund(unittest.TestCase):
    def setUp(self):
        import uuid

        self.unique_id = uuid.uuid4().hex[:8]
        self.test_dir = PROJECT_ROOT / "state" / f"test_jules_env_{self.unique_id}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_db = self.test_dir / "test_market_cache.db"
        self.test_orders = self.test_dir / "orders"
        self.test_orders.mkdir(parents=True, exist_ok=True)

        # Patch paths
        self.patch_db = patch.object(jf, "DB_PATH", self.test_db)
        self.patch_pt_db = patch.object(paper_trade, "DB_PATH", self.test_db)
        self.patch_jf_pt_db = patch.object(jf.paper_trade, "DB_PATH", self.test_db)
        self.patch_orders = patch.object(jf, "ORDERS_DIR", self.test_orders)
        self.patch_processed = patch.object(
            jf, "PROCESSED_ORDERS_DIR", self.test_orders / "processed"
        )

        self.patch_db.start()
        self.patch_pt_db.start()
        self.patch_jf_pt_db.start()
        self.patch_orders.start()
        self.patch_processed.start()

        # Init DB schema
        with paper_trade._db() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS price_bar (symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume REAL)"
            )
            conn.execute(
                "INSERT INTO price_bar VALUES ('BDMS.BK', '2026-09-14', 28.0, 29.0, 27.5, 28.5, 5000000)"
            )

    def tearDown(self):
        self.patch_db.stop()
        self.patch_pt_db.stop()
        self.patch_jf_pt_db.stop()
        self.patch_orders.stop()
        self.patch_processed.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_status_initial(self):
        status = jf.get_jules_status()
        self.assertEqual(status["initial_capital"], 30000.0)
        self.assertEqual(status["cash_balance"], 30000.0)
        self.assertEqual(status["open_count"], 0)
        self.assertEqual(status["net_pnl"], 0.0)

    def test_buy_board_lot_violation(self):
        with self.assertRaises(ValueError) as ctx:
            jf.execute_buy(symbol="BDMS.BK", shares=150, entry=28.0, stop=26.0, target=32.0)
        self.assertIn("SET board lot violation", str(ctx.exception))

    def test_buy_insufficient_cash(self):
        with self.assertRaises(ValueError) as ctx:
            # 2000 shares * 28.0 = 56,000 THB > 30,000 THB capital
            jf.execute_buy(symbol="BDMS.BK", shares=2000, entry=28.0, stop=26.0, target=32.0)
        self.assertIn("Insufficient cash", str(ctx.exception))

    def test_buy_and_sell_lifecycle(self):
        # Buy 500 shares @ 28.0 (cost = 14,000 THB + fees)
        trade = jf.execute_buy(
            symbol="BDMS.BK",
            shares=500,
            entry=28.0,
            stop=26.0,
            target=32.0,
            thesis="Medical tourism rebound",
        )
        self.assertEqual(trade["symbol"], "BDMS.BK")
        self.assertEqual(trade["portfolio"], "jules")

        status_after_buy = jf.get_jules_status()
        self.assertEqual(status_after_buy["open_count"], 1)
        self.assertLess(status_after_buy["cash_balance"], 30000.0)

        # Sell @ target 32.0 (profit = (32 - 28) * 500 = 2000 gross)
        closed = jf.execute_sell(symbol="BDMS.BK", price=32.0, reason="Hit target")
        self.assertEqual(closed["status"], "closed_target")
        self.assertGreater(closed["realized_pnl"], 1900.0)  # Gross 2000 minus fees

        status_after_sell = jf.get_jules_status()
        self.assertEqual(status_after_sell["open_count"], 0)
        self.assertEqual(status_after_sell["closed_count"], 1)
        self.assertEqual(status_after_sell["win_rate"], 1.0)
        self.assertGreater(status_after_sell["net_pnl"], 1900.0)
        self.assertGreater(status_after_sell["equity"], 31900.0)

    def test_process_orders_queue(self):
        import yaml

        order_file = self.test_orders / "buy_bdms.yaml"
        with open(order_file, "w", encoding="utf-8") as f:
            yaml.dump(
                {
                    "action": "buy",
                    "symbol": "BDMS.BK",
                    "shares": 200,
                    "entry_price": 28.5,
                    "stop_price": 26.0,
                    "target_price": 32.0,
                    "thesis": "Queue execution test",
                },
                f,
            )

        results = jf.process_orders_queue()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "executed")

        status = jf.get_jules_status()
        self.assertEqual(status["open_count"], 1)
        self.assertEqual(status["open_positions"][0]["symbol"], "BDMS.BK")


if __name__ == "__main__":
    unittest.main()
