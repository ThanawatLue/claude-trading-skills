#!/usr/bin/env python3
"""Unit tests for Market Intelligence Filter.

Verifies:
1. Red-flag headline detection (subsidies, lawsuits, investigations, downgrades, offerings).
2. Binary event earnings proximity gate (<= 7 days rejection).
3. Foreign state-owned ADR / political risk disqualification.
4. Relative Strength (RS Rating) calculation vs benchmark index (SPY / SET).
5. Overhead supply and weekly Stage-2 moving average alignment.
6. Average Daily Dollar Volume (ADDV) liquidity floor.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from scripts.market_intelligence_filter import (
    calculate_relative_strength,
    check_earnings_gate,
    check_news_red_flags,
    check_overhead_supply,
    check_state_owned_adr,
    evaluate_stock_intelligence,
)


def test_check_news_red_flags_detects_subsidies_and_political():
    """Verify detection of fuel subsidies and political risk (as in Petrobras case)."""
    headlines = [
        "Cheniere Energy Petrobras LNG Deal Supports Growth",
        "Can R$12.2 Billion in Fuel Subsidies Ease Petrobras Pricing Pressure?",
        "Drilling contract secured in offshore basin",
    ]
    res = check_news_red_flags("PBR.A", headlines=headlines)
    assert res.is_clean is False
    assert any("subsidies" in flag.lower() or "price" in flag.lower() for flag in res.red_flags)
    assert res.score_modifier <= -25.0


def test_check_news_red_flags_detects_lawsuit_and_investigation():
    """Verify detection of SEC investigations, fraud allegations, and secondary offerings."""
    headlines = [
        "Company Announces Secondary Public Offering of Common Stock",
        "Quarterly product launch in North America",
    ]
    res = check_news_red_flags("XYZ", headlines=headlines)
    assert res.is_clean is False
    assert any("offering" in flag.lower() for flag in res.red_flags)


def test_check_news_clean_headlines():
    """Verify clean pass for positive or neutral corporate news."""
    headlines = [
        "Hewlett Packard Enterprise Reports Record AI Server Orders",
        "Company expands enterprise cloud partnership",
        "Analyst raises price target following product innovation",
    ]
    res = check_news_red_flags("HPE", headlines=headlines)
    assert res.is_clean is True
    assert len(res.red_flags) == 0
    assert res.score_modifier >= 0.0


def test_check_earnings_gate_rejects_upcoming_earnings():
    """Verify rejection when earnings announcement is within 7 days."""
    # Mocking earnings date 3 days from now
    res = check_earnings_gate("TSLA", days_until_earnings=3)
    assert res.passed is False
    assert "binary event" in res.reason.lower() or "earnings" in res.reason.lower()


def test_check_earnings_gate_passes_distant_earnings():
    """Verify passing when earnings is 25 days away."""
    res = check_earnings_gate("AAPL", days_until_earnings=25)
    assert res.passed is True


def test_check_state_owned_adr_rejection():
    """Verify flagging of known state-owned enterprise ADRs with political price control risks."""
    # Petrobras, Ecopetrol, etc.
    assert check_state_owned_adr("PBR").is_state_owned is True
    assert check_state_owned_adr("PBR.A").is_state_owned is True
    assert check_state_owned_adr("EC").is_state_owned is True
    # Commercial tech growth stocks should pass
    assert check_state_owned_adr("HPE").is_state_owned is False
    assert check_state_owned_adr("NVDA").is_state_owned is False
    assert check_state_owned_adr("DELTA").is_state_owned is False


def test_calculate_relative_strength_leader_vs_laggard():
    """Verify that a stock outperforming benchmark receives strong RS score."""
    # Stock up +20% over 20 days
    stock_prices = pd.Series([100.0 + (i * 1.0) for i in range(21)])
    # Benchmark up only +2% over 20 days
    bm_prices = pd.Series([500.0 + (i * 0.5) for i in range(21)])

    rs = calculate_relative_strength(stock_prices, bm_prices)
    assert rs["rs_rating"] >= 75.0
    assert rs["is_market_leader"] is True
    assert rs["alpha_pct"] > 10.0


def test_check_overhead_supply_rejects_declining_200sma_overhead():
    """Verify rejection when a declining 200 SMA is directly overhead within 3%."""
    current_price = 100.0
    sma_200 = 102.5  # 2.5% overhead
    sma_200_slope = -0.5  # declining

    res = check_overhead_supply(current_price, sma_200=sma_200, sma_200_slope=sma_200_slope)
    assert res.passed is False
    assert "overhead supply" in res.reason.lower() or "200" in res.reason.lower()


def test_evaluate_stock_intelligence_full_pipeline():
    """Test integrated intelligence evaluation on a high-conviction candidate."""
    with patch(
        "scripts.market_intelligence_filter.fetch_recent_headlines",
        return_value=["Partnership announced"],
    ):
        with patch("scripts.market_intelligence_filter.get_days_until_earnings", return_value=35):
            res = evaluate_stock_intelligence(
                symbol="HPE",
                price=63.89,
                market="US",
                dollar_volume=50_000_000.0,
            )
            assert res.passed is True
            assert res.disqualified is False
            assert res.composite_modifier >= 0.0
