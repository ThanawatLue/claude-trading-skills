#!/usr/bin/env python3
"""Unit tests for Jules Autonomous Scout & Daily Mission Generator."""

import sys
import unittest
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

import scripts.jules_scout as js


class TestJulesScout(unittest.TestCase):
    def test_calculate_sizing_and_levels(self):
        # Test cheap stock ฿19.20
        res1 = js.calculate_sizing_and_levels(19.20)
        self.assertEqual(res1["shares"] % 100, 0)
        self.assertGreaterEqual(res1["shares"], 100)
        self.assertLessEqual(res1["est_cost"], 8000.0)
        self.assertLess(res1["stop"], 19.20)
        self.assertGreater(res1["target"], 19.20)

        # Test higher price stock ฿63.00
        res2 = js.calculate_sizing_and_levels(63.00)
        self.assertEqual(res2["shares"], 100)
        self.assertEqual(res2["est_cost"], 6300.0)

    def test_generate_today_mission(self):
        mission = js.generate_today_mission(market="TH")
        self.assertIn("candidates", mission)
        self.assertIn("dna_generation", mission)
        self.assertIn("available_slots", mission)

        # Check mission files created
        self.assertTrue(js.MISSION_MD.exists())
        self.assertTrue(js.MISSION_JSON.exists())

        content = js.MISSION_MD.read_text(encoding="utf-8")
        self.assertIn("Jules AI Fund: Daily Mission", content)
        self.assertIn("Trader DNA Memory", content)
        self.assertIn("Order Templates", content)


if __name__ == "__main__":
    unittest.main()
