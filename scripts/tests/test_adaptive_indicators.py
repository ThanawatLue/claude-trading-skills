#!/usr/bin/env python3
"""Unit tests for Adaptive Matrix and Specialized Dynamic Indicators."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import scripts.adaptive_indicators as ai


class TestAdaptiveIndicators(unittest.TestCase):
    def setUp(self):
        # Generate synthetic 60-day price bars
        dates = pd.date_range(end="2026-09-18", periods=60, freq="B")

        # 1. Benchmark (Steady sideways / mild decline)
        bench_close = [1600.0 - (i * 0.2) for i in range(60)]
        self.bench_df = pd.DataFrame({"Close": bench_close}, index=dates)

        # 2. Strong Outperforming Stock (Rising price, high up volume)
        stock_close = [10.0 + (i * 0.1) for i in range(60)]
        # Up days have 2,000,000 shares, down days have 500,000 shares
        stock_vol = [2000000 if i % 2 == 0 else 500000 for i in range(60)]
        self.strong_df = pd.DataFrame({"Close": stock_close, "Volume": stock_vol}, index=dates)

        # 3. Distribution Trap Stock (Rises initially, then heavy volume on down days)
        trap_close = [20.0 + (i * 0.05) if i < 40 else 22.0 - ((i - 40) * 0.15) for i in range(60)]
        # Massive volume on down days (5,000,000) and tiny volume on up days (300,000)
        trap_vol = [300000 if trap_close[i] >= trap_close[max(0, i - 1)] else 5000000 for i in range(60)]
        self.trap_df = pd.DataFrame({"Close": trap_close, "Volume": trap_vol}, index=dates)

    def test_thematic_cluster_mapping_and_detection(self):
        self.assertEqual(ai.get_cluster_for_symbol("PSL.BK"), "Marine Shipping")
        self.assertEqual(ai.get_cluster_for_symbol("rcl"), "Marine Shipping")
        self.assertEqual(ai.get_cluster_for_symbol("BDMS.BK"), "Healthcare & Hospitals")
        self.assertIsNone(ai.get_cluster_for_symbol("UNKNOWN.BK"))

        # Test cluster detection with 2 shipping gainers
        mock_universe = [
            {"symbol": "PSL.BK", "change": 7.92},
            {"symbol": "RCL.BK", "change": 6.40},
            {"symbol": "TTA.BK", "change": 5.71},
            {"symbol": "BDMS.BK", "change": 0.50},  # Single stock in healthcare
        ]
        res = ai.detect_thematic_clusters(mock_universe, min_cluster_gainers=2, min_gain_pct=1.5)
        active = res["active_clusters"]
        self.assertIn("Marine Shipping", active)
        self.assertEqual(active["Marine Shipping"]["gainer_count"], 3)
        self.assertNotIn("Healthcare & Hospitals", active)

    def test_recency_weighted_ud_ratio(self):
        strong_ud = ai.calculate_recency_weighted_ud_ratio(self.strong_df)
        self.assertGreater(strong_ud["ud_ratio"], 1.25)
        self.assertTrue(strong_ud["is_accumulation"])
        self.assertEqual(strong_ud["status"], "ACCUMULATION")

        trap_ud = ai.calculate_recency_weighted_ud_ratio(self.trap_df)
        self.assertLess(trap_ud["ud_ratio"], 0.85)
        self.assertFalse(trap_ud["is_accumulation"])
        self.assertEqual(trap_ud["status"], "DISTRIBUTION")

    def test_dynamic_risk_cap(self):
        # Volatile shipping stock: ฿10.80, ATR ฿0.44 (~4.1% ATR)
        cap_volatile = ai.calculate_dynamic_risk_cap(price=10.80, atr=0.44)
        # 0.44 / 10.80 * 100 * 1.8 ≈ 7.33%
        self.assertGreater(cap_volatile, 6.0)
        self.assertLessEqual(cap_volatile, 8.5)

        # Calm utility stock: ฿20.00, ATR ฿0.30 (~1.5% ATR)
        cap_calm = ai.calculate_dynamic_risk_cap(price=20.00, atr=0.30)
        # 0.30 / 20.00 * 100 * 1.8 ≈ 2.7% -> clipped to min_cap 3.5%
        self.assertEqual(cap_calm, 3.5)

    def test_mansfield_rs(self):
        rs_res = ai.calculate_mansfield_rs(self.strong_df, self.bench_df)
        self.assertTrue(rs_res["is_outperforming"])
        self.assertGreater(rs_res["rs_score"], 0.0)

    def test_evaluate_adaptive_candidate_traps(self):
        active_clusters = {
            "active_clusters": {
                "Marine Shipping": {"gainer_count": 2, "avg_gain": 7.16}
            }
        }

        # Case A: True Leader (PSL.BK)
        res_psl = ai.evaluate_adaptive_candidate(
            symbol="PSL.BK",
            price=10.80,
            traded_value_thb=177_000_000,
            high_52w=11.00,
            stock_df=self.strong_df,
            benchmark_df=self.bench_df,
            active_clusters=active_clusters,
            atr=0.44,
        )
        self.assertTrue(res_psl["eligible"])
        self.assertTrue(res_psl["in_active_cluster"])
        self.assertEqual(len(res_psl["rejection_reasons"]), 0)
        self.assertGreater(res_psl["adaptive_score"], 75.0)

        # Case B: Distribution Trap (ITC.BK) -> Must be rejected by U/D ratio
        res_itc = ai.evaluate_adaptive_candidate(
            symbol="ITC.BK",
            price=16.90,
            traded_value_thb=85_000_000,
            high_52w=18.00,
            stock_df=self.trap_df,
            benchmark_df=self.bench_df,
            active_clusters=active_clusters,
            atr=0.50,
        )
        self.assertFalse(res_itc["eligible"])
        self.assertTrue(any("Distribution Trap" in r for r in res_itc["rejection_reasons"]))

        # Case C: Low Liquidity Trap (WHAIR.BK) -> Must be rejected by ฿15M threshold
        res_whair = ai.evaluate_adaptive_candidate(
            symbol="WHAIR.BK",
            price=8.50,
            traded_value_thb=8_000_000,
            high_52w=9.00,
            stock_df=self.strong_df,
            benchmark_df=self.bench_df,
            active_clusters=active_clusters,
            atr=0.20,
        )
        self.assertFalse(res_whair["eligible"])
        self.assertTrue(any("Low Liquidity" in r for r in res_whair["rejection_reasons"]))

        # Case D: Deep Laggard Rebound Trap (MCOT.BK) -> Must be rejected by 52w distance > 15%
        res_mcot = ai.evaluate_adaptive_candidate(
            symbol="MCOT.BK",
            price=5.45,
            traded_value_thb=15_800_000,
            high_52w=7.50,  # 27.3% below high
            stock_df=self.strong_df,
            benchmark_df=self.bench_df,
            active_clusters=active_clusters,
            atr=0.30,
        )
        self.assertFalse(res_mcot["eligible"])
        self.assertTrue(any("Laggard / Rebound" in r for r in res_mcot["rejection_reasons"]))


if __name__ == "__main__":
    unittest.main()
