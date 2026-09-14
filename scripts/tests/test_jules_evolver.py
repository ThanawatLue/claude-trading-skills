#!/usr/bin/env python3
"""Unit tests for Jules Autonomous Self-Improvement & Trade Evolution Engine."""

import json
import sys
import unittest
import uuid
from pathlib import Path

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

import scripts.jules_evolver as je


class TestJulesEvolver(unittest.TestCase):
    def setUp(self):
        self.test_id = uuid.uuid4().hex[:8]
        self.test_dir = PROJECT_ROOT / "state" / f"test_evolver_{self.test_id}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.test_dir / "test_market.db"
        self.memory_dir = self.test_dir / "jules_memory"
        self.reports_dir = self.test_dir / "reports"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.orig_paper_db = paper_trade.DB_PATH
        paper_trade.DB_PATH = self.db_path

    def tearDown(self):
        paper_trade.DB_PATH = self.orig_paper_db
        # Clean up files
        for p in self.test_dir.glob("**/*"):
            if p.is_file():
                try:
                    p.unlink()
                except Exception:
                    pass
        try:
            import shutil

            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_load_dna_defaults(self):
        dna = je.load_dna(memory_dir=self.memory_dir)
        self.assertEqual(dna["generation"], 1)
        self.assertEqual(dna["total_analyzed_trades"], 0)
        self.assertGreaterEqual(len(dna["rules"]), 4)
        self.assertIn("strengths", dna)

    def test_get_pre_trade_briefing(self):
        brief = je.get_pre_trade_briefing(market="TH", memory_dir=self.memory_dir)
        self.assertIn("JULES AI FUND: PRE-TRADE BRAIN BRIEFING", brief)
        self.assertIn("GEN 1", brief)
        self.assertIn("฿30,000.00", brief)
        self.assertIn("CORE TRADING DNA & EVOLVED RULES", brief)

    def test_evolve_memory_with_trades(self):
        # Open 2 trades for jules
        t1 = paper_trade.open_position(
            symbol="BDMS.BK",
            market="TH",
            shares=1000,
            entry=28.0,
            stop=26.32,
            target=31.7,
            portfolio="jules",
            notes="Strong medical tourism catalyst",
        )
        t2 = paper_trade.open_position(
            symbol="CPALL.BK",
            market="TH",
            shares=500,
            entry=60.0,
            stop=56.4,
            target=67.92,
            portfolio="jules",
            notes="Convenience retail recovery",
        )

        # Close t1 with a win
        paper_trade.close_position(
            trade_id=t1["id"], exit_price=31.7, status="closed_target", notes="Hit full 2.2R target"
        )

        # Close t2 with a loss
        paper_trade.close_position(
            trade_id=t2["id"], exit_price=56.0, status="closed_stop", notes="Hit stop loss"
        )

        # Run evolution
        res = je.evolve_memory(
            market="TH", memory_dir=self.memory_dir, reports_dir=self.reports_dir
        )
        self.assertEqual(res["status"], "evolved")
        self.assertEqual(res["total_trades"], 2)
        self.assertEqual(res["generation"], 2)

        # Verify DNA file was saved
        dna_file = self.memory_dir / "trader_dna.json"
        self.assertTrue(dna_file.exists())
        with open(dna_file, encoding="utf-8") as f:
            saved_dna = json.load(f)
        self.assertEqual(saved_dna["generation"], 2)
        self.assertEqual(saved_dna["total_analyzed_trades"], 2)
        self.assertEqual(saved_dna["win_rate"], 0.5)

        # Verify Postmortem files were generated
        p1 = self.reports_dir / f"postmortem_trade_{t1['id']}_BDMS.BK.md"
        p2 = self.reports_dir / f"postmortem_trade_{t2['id']}_CPALL.BK.md"
        self.assertTrue(p1.exists())
        self.assertTrue(p2.exists())
        p1_content = p1.read_text(encoding="utf-8")
        self.assertIn("BDMS.BK", p1_content)
        self.assertIn("WIN", p1_content)
        self.assertIn("medical tourism", p1_content.lower())


if __name__ == "__main__":
    unittest.main()
