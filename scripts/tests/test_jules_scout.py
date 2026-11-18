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
        self.assertIn("Jules AI Fund (TH): Daily Mission", content)
        self.assertIn("Trader DNA Memory", content)
        self.assertIn("Order Templates", content)

    def test_get_latest_intraday_candidates(self):
        import json

        tasks_dir, _, _, _ = js.get_mission_paths("TH")
        intraday_file = tasks_dir / "intraday_candidates.json"
        mock_data = {
            "candidates": [
                {
                    "symbol": "INTRADAY_TEST",
                    "price": 25.0,
                    "score": 88.0,
                    "highlights": "ORB Breakout",
                    "suggested_stop": 23.8,
                    "suggested_target": 27.5,
                }
            ]
        }
        intraday_file.write_text(json.dumps(mock_data), encoding="utf-8")
        try:
            cands = js.get_latest_intraday_candidates("TH")
            self.assertEqual(len(cands), 1)
            self.assertEqual(cands[0]["symbol"], "INTRADAY_TEST")
            self.assertEqual(cands[0]["score"], 88.0)
            self.assertEqual(cands[0]["source"], "Intraday ORB Scanner")
        finally:
            if intraday_file.exists():
                intraday_file.unlink()

    def test_canslim_candidates_filtered_strictly_by_market(self):
        import json
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp)
            th_f = reports / "canslim_screener_2026-11-17_100000.json"
            us_f = reports / "canslim_screener_2026-11-17_133000.json"
            th_f.write_text(
                json.dumps(
                    {
                        "metadata": {"screening_options": {"market": "TH"}},
                        "results": [
                            {
                                "symbol": "TIDLOR.BK",
                                "company_name": "Tidlor",
                                "sector": "Finance",
                                "price": 19.2,
                                "composite_score": 68.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            us_f.write_text(
                json.dumps(
                    {
                        "metadata": {"screening_options": {"market": "US"}},
                        "results": [
                            {
                                "symbol": "APH",
                                "company_name": "Amphenol",
                                "sector": "Electronic Technology",
                                "price": 78.2,
                                "composite_score": 72.0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(js, "REPORTS_DIR", reports):
                th_cands = js.get_latest_canslim_candidates(market="TH")
                self.assertEqual([c["symbol"] for c in th_cands], ["TIDLOR.BK"])

    def test_thai_swing_preserves_dip_buy_when_momentum_has_12_stocks(self):
        import json
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp)
            swing_f = reports / "thai_swing_2026-11-17_100000.json"
            momentum = [
                {
                    "symbol": f"MOM{i}.BK",
                    "name": f"Mom{i}",
                    "sector": "Finance",
                    "strategy": "MOMENTUM",
                    "price": 10.0,
                    "score": 80.0 - i,
                }
                for i in range(12)
            ]
            dip_buy = [
                {
                    "symbol": "PLANB.BK",
                    "name": "Plan B",
                    "sector": "Commercial Services",
                    "strategy": "DIP_BUY",
                    "price": 7.5,
                    "score": 87.7,
                }
            ]
            swing_f.write_text(
                json.dumps({"momentum": momentum, "dip_buy": dip_buy}),
                encoding="utf-8",
            )
            with patch.object(js, "REPORTS_DIR", reports):
                cands = js.get_latest_thai_swing_candidates()
                syms = [c["symbol"] for c in cands]
                self.assertIn("PLANB.BK", syms)


if __name__ == "__main__":
    unittest.main()
