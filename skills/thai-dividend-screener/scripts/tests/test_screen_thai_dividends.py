"""Tests for thai-dividend-screener — filters, scoring, grading."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from screen_thai_dividends import score_stock, grade, main, to_markdown  # noqa: E402


def _stock(
    yield_=5,
    mcap=10e9,
    pe=10,
    price=10,
    sma200=9,
    rsi=45,
    py=15,
    avg_turnover=20_000_000,
    avg_volume=200000
):
    return {
        "symbol": "TEST.BK",
        "name": "Test Stock",
        "sector": "Financials", # Added sector and name for the integration test
        "dividend_yield": yield_,
        "marketCap": mcap,
        "pe_ratio": pe,
        "price": price,
        "sma200": sma200,
        "rsi": rsi,
        "perf_y": py,
        "avg_turnover": avg_turnover,
        "avgVolume": avg_volume,
    }


def test_passing_stock_returns_high_score():
    """Healthy candidate: 5% yield, P/E 10, RSI 45, above SMA200, +15% 1Y."""
    ok, score, _ = score_stock(_stock(), min_yield=3, min_mcap=5e9)
    assert ok is True
    assert score >= 50


def test_filter_yield_below_minimum():
    """Yield < min_yield → rejected."""
    ok, score, _ = score_stock(_stock(yield_=2), min_yield=3, min_mcap=5e9)
    assert ok is False
    assert score == 0


def test_filter_market_cap_too_small():
    """Mcap < 5B → rejected."""
    ok, _, _ = score_stock(_stock(mcap=1e9), min_yield=3, min_mcap=5e9)
    assert ok is False


def test_filter_turnover_too_small():
    """Low turnover Thai dividend stocks are rejected to avoid illiquid traps."""
    ok, _, _ = score_stock(
        _stock(avg_turnover=2_000_000),
        min_yield=3,
        min_mcap=5e9,
        min_turnover=10_000_000,
    )
    assert ok is False


def test_filter_pe_out_of_range():
    """P/E < 4 or > 25 → rejected (avoid loss-makers and bubbles)."""
    ok, _, _ = score_stock(_stock(pe=2), min_yield=3, min_mcap=5e9)
    assert ok is False
    ok, _, _ = score_stock(_stock(pe=30), min_yield=3, min_mcap=5e9)
    assert ok is False


def test_filter_price_below_sma200():
    """Stage 4 stocks (below SMA200) rejected — avoid value traps."""
    ok, _, _ = score_stock(_stock(price=8, sma200=10), min_yield=3, min_mcap=5e9)
    assert ok is False


def test_yield_score_linear_ramp_and_capping():
    """Yield score should follow linear ramp from 3% (0 score) to 12% (100 score) and cap."""
    # Test lower bound (3% yield should be 0 score)
    _, _, m_min = score_stock(_stock(yield_=3.0), min_yield=3, min_mcap=5e9)
    assert m_min["yield_score"] == 0

    # Test mid-point (7.5% yield should be 50 score, assuming min_yield=3)
    _, _, m_mid = score_stock(_stock(yield_=7.5), min_yield=3, min_mcap=5e9)
    assert m_mid["yield_score"] == 50

    # Test upper bound (12% yield should be 100 score)
    _, _, m_max = score_stock(_stock(yield_=12.0), min_yield=3, min_mcap=5e9)
    assert m_max["yield_score"] == 100

    # Test yield above 12% should still be 100
    _, _, m_super = score_stock(_stock(yield_=20), min_yield=3, min_mcap=5e9)
    assert m_super["yield_score"] == 100


def test_valuation_score_bands():
    """Valuation score should reward P/E 8-15, penalize outside."""
    # P/E 10 (sweet spot) should be 100
    _, _, m_pe_sweet = score_stock(_stock(pe=10), min_yield=3, min_mcap=5e9)
    assert m_pe_sweet["valuation_score"] == 100

    # P/E 8 (lower bound sweet spot) should be 100
    _, _, m_pe_8 = score_stock(_stock(pe=8), min_yield=3, min_mcap=5e9)
    assert m_pe_8["valuation_score"] == 100

    # P/E 15 (upper bound sweet spot) should be 100
    _, _, m_pe_15 = score_stock(_stock(pe=15), min_yield=3, min_mcap=5e9)
    assert m_pe_15["valuation_score"] == 100

    # P/E 4 (lower bound of acceptance) should be 70
    _, _, m_pe_4 = score_stock(_stock(pe=4), min_yield=3, min_mcap=5e9)
    assert m_pe_4["valuation_score"] == 70

    # P/E 25 (upper bound of acceptance) should be 0
    _, _, m_pe_25 = score_stock(_stock(pe=25), min_yield=3, min_mcap=5e9)
    assert m_pe_25["valuation_score"] == 0

    # P/E below 4 should be rejected by hard filter, but if it passed (e.g. min_yield=1)
    # it would get less than 70 (or 0 for P/E=3)
    _, _, m_pe_3 = score_stock(_stock(pe=3), min_yield=1, min_mcap=5e9)
    assert m_pe_3["valuation_score"] < 70

    # P/E above 25 should be rejected by hard filter, but if it passed (e.g. min_yield=1)
    # it would get less than 0 (or 0 for P/E=26)
    _, _, m_pe_26 = score_stock(_stock(pe=26), min_yield=1, min_mcap=5e9)
    assert m_pe_26["valuation_score"] < 0


def test_rsi_pullback_sweet_spot():
    """RSI 35-55 = best entry → 100. RSI 70 = much lower."""
    _, _, m_good = score_stock(_stock(rsi=45), min_yield=3, min_mcap=5e9)
    _, _, m_extended = score_stock(_stock(rsi=72), min_yield=3, min_mcap=5e9)
    assert m_good["pullback_score"] > m_extended["pullback_score"]
    assert m_good["pullback_score"] == 100


def test_trend_score_components():
    """Trend score should combine 1Y performance and SMA200 premium."""
    # Only 1Y performance (SMA200 premium 0)
    _, _, m_py_only = score_stock(_stock(py=25, price=10, sma200=10), min_yield=3, min_mcap=5e9)
    # py=25, capped at 50. Trend score is 25
    assert m_py_only["trend_score"] == 25.0

    # Only SMA200 premium (1Y performance 0)
    # sma200_premium = ((11-10)/10)*100 = 10%
    # sma200_premium * 2 = 20, capped at 50. Trend score is 20
    _, _, m_sma_only = score_stock(_stock(py=0, price=11, sma200=10), min_yield=3, min_mcap=5e9)
    assert m_sma_only["trend_score"] == 20.0

    # Both components contribute
    # py=25 -> 25
    # sma200_premium = ((11-10)/10)*100 = 10% -> 20
    # Total = 25 + 20 = 45
    _, _, m_both = score_stock(_stock(py=25, price=11, sma200=10), min_yield=3, min_mcap=5e9)
    assert m_both["trend_score"] == 45.0


def test_grading_bands():
    assert grade(80) == "Excellent"
    assert grade(75) == "Excellent"  # boundary
    assert grade(70) == "Good"
    assert grade(60) == "Good"  # boundary
    assert grade(55) == "Fair"
    assert grade(45) == "Fair"  # boundary
    assert grade(30) == "Avoid"


def test_pullback_score_bands():
    """Pullback score should reward RSI 35-55, penalize outside."""
    # RSI 45 (sweet spot) should be 100
    _, _, m_rsi_sweet = score_stock(_stock(rsi=45), min_yield=3, min_mcap=5e9)
    assert m_rsi_sweet["pullback_score"] == 100

    # RSI 35 (lower bound sweet spot) should be 100
    _, _, m_rsi_35 = score_stock(_stock(rsi=35), min_yield=3, min_mcap=5e9)
    assert m_rsi_35["pullback_score"] == 100

    # RSI 55 (upper bound sweet spot) should be 100
    _, _, m_rsi_55 = score_stock(_stock(rsi=55), min_yield=3, min_mcap=5e9)
    assert m_rsi_55["pullback_score"] == 100

    # RSI 30 (slightly oversold) should be 75 (100 - (35-30)*5)
    _, _, m_rsi_30 = score_stock(_stock(rsi=30), min_yield=3, min_mcap=5e9)
    assert m_rsi_30["pullback_score"] == 75

    # RSI 65 (slightly extended) should be 50 (100 - (65-55)*5)
    _, _, m_rsi_65 = score_stock(_stock(rsi=65), min_yield=3, min_mcap=5e9)
    assert m_rsi_65["pullback_score"] == 50

    # RSI 70 (extended) should be 35 (50 - (70-65)*3)
    _, _, m_rsi_70 = score_stock(_stock(rsi=70), min_yield=3, min_mcap=5e9)
    assert m_rsi_70["pullback_score"] == 35

    # RSI 20 (very oversold) should be 0 (capped at 0)
    _, _, m_rsi_20 = score_stock(_stock(rsi=20), min_yield=3, min_mcap=5e9)
    assert m_rsi_20["pullback_score"] == 0


def test_handles_none_values_gracefully():
    """Missing fields should not crash; use _safe()."""
    bad = {
        "symbol": "X.BK",
        "dividend_yield": None,
        "marketCap": None,
        "pe_ratio": None,
        "price": None,
        "sma200": None,
        "rsi": None,
        "perf_y": None,
    }
    ok, _, _ = score_stock(bad, min_yield=3, min_mcap=5e9)
    assert ok is False  # filters reject it gracefully


def test_avg_turnover_fallback():
    """Test that avg_turnover is correctly calculated when missing or zero."""
    # Case 1: avg_turnover is None
    stock_none_turnover = _stock(
        avg_turnover=None,
        price=100.0,
        avg_volume=100_000, # This will make calculated avg_turnover 10,000,000
        yield_=5.0,
        mcap=10e9,
        pe=10,
        sma200=95,
        py=15
    )
    ok, score, metrics = score_stock(stock_none_turnover, min_yield=3, min_mcap=5e9, min_turnover=10_000_000)
    assert ok is True
    assert metrics["avg_turnover"] == 10_000_000.0 # Expecting price * avg_volume

    # Case 2: avg_turnover is 0
    stock_zero_turnover = _stock(
        avg_turnover=0,
        price=100.0,
        avg_volume=100_000, # This will make calculated avg_turnover 10,000,000
        yield_=5.0,
        mcap=10e9,
        pe=10,
        sma200=95,
        py=15
    )
    ok, score, metrics = score_stock(stock_zero_turnover, min_yield=3, min_mcap=5e9, min_turnover=10_000_000)
    assert ok is True
    assert metrics["avg_turnover"] == 10_000_000.0 # Expecting price * avg_volume

    # Case 3: avg_turnover is 0 and calculated is less than min_turnover (should be filtered out)
    stock_filtered_turnover = _stock(
        avg_turnover=0,
        price=50.0, # makes calculated avg_turnover 5,000,000
        avg_volume=100_000,
        yield_=5.0,
        mcap=10e9,
        pe=10,
        sma200=45,
        py=15
    )
    ok, _, _ = score_stock(stock_filtered_turnover, min_yield=3, min_mcap=5e9, min_turnover=10_000_000)
    assert ok is False


def test_grading_boundaries():
    """Test that grades are correctly assigned at composite score boundaries."""
    # Test for Excellent (composite >= 75)
    _, composite_75, _ = score_stock(_stock(yield_=6.375, pe=10, py=50, price=12.5, sma200=10, rsi=45), min_yield=3, min_mcap=5e9)
    assert composite_75 == 75.0
    assert grade(composite_75) == "Excellent"

    # Stock to yield a composite score of 74.99 (should be "Good")
    _, composite_74_99, _ = score_stock(_stock(yield_=6.37275, pe=10, py=50, price=12.5, sma200=10, rsi=45), min_yield=3, min_mcap=5e9)
    assert composite_74_99 == 74.99
    assert grade(composite_74_99) == "Good"

    # Test for Good (composite >= 60)
    _, composite_60, _ = score_stock(_stock(yield_=3.0, pe=10, py=50, price=12.5, sma200=10, rsi=45), min_yield=3, min_mcap=5e9)
    assert composite_60 == 60.0
    assert grade(composite_60) == "Good"

    # Stock to yield a composite score of 59.99 (should be "Fair")
    _, composite_59_99, _ = score_stock(_stock(yield_=3.0, pe=10, py=50, price=12.5, sma200=10, rsi=55.01), min_yield=3, min_mcap=5e9)
    assert composite_59_99 == 59.99
    assert grade(composite_59_99) == "Fair"

    # Test for Fair (composite >= 45)
    _, composite_45, _ = score_stock(_stock(yield_=8.0625, pe=19.375, py=28.125, price=11.40625, sma200=10, rsi=63.75), min_yield=3, min_mcap=5e9)
    assert composite_45 == 45.0
    assert grade(composite_45) == "Fair"

    # Stock to yield a composite score of 44.99 (should be "Avoid")
    _, composite_44_99, _ = score_stock(_stock(yield_=8.061375, pe=19.375, py=28.125, price=11.40625, sma200=10, rsi=63.75), min_yield=3, min_mcap=5e9)
    assert composite_44_99 == 44.99
    assert grade(composite_44_99) == "Avoid"

    # Test for Avoid (composite < 45)
    _, composite_0, _ = score_stock(_stock(yield_=3.0, pe=4, py=0, price=8, sma200=10, rsi=20), min_yield=3, min_mcap=5e9)
    assert composite_0 == 14.0
    assert grade(composite_0) == "Avoid"


# Mock for get_thai_stocks and filter_common_stocks
MOCK_STOCKS = [
    {
        "symbol": "STOCK1",
        "name": "Stock One",
        "sector": "Industrials",
        "price": 100.0,
        "marketCap": 10e9,
        "avg_turnover": 20_000_000,
        "dividend_yield": 5.0,
        "pe_ratio": 12.0,
        "rsi": 45,
        "sma50": 90,
        "sma200": 95,
        "perf_1m": 2.0,
        "perf_y": 15.0,
        "avgVolume": 200000,
    },
    {
        "symbol": "STOCK2",
        "name": "Stock Two",
        "sector": "Financials",
        "price": 50.0,
        "marketCap": 6e9,
        "avg_turnover": 15_000_000,
        "dividend_yield": 6.0,
        "pe_ratio": 10.0,
        "rsi": 50,
        "sma50": 48,
        "sma200": 45,
        "perf_1m": 3.0,
        "perf_y": 20.0,
        "avgVolume": 300000,
    },
    {
        "symbol": "STOCK3", # This stock will be filtered out by yield < min_yield
        "name": "Stock Three",
        "sector": "Utilities",
        "price": 200.0,
        "marketCap": 15e9,
        "avg_turnover": 25_000_000,
        "dividend_yield": 2.0, # Less than default 3.0
        "pe_ratio": 18.0,
        "rsi": 40,
        "sma50": 190,
        "sma200": 180,
        "perf_1m": 1.0,
        "perf_y": 10.0,
        "avgVolume": 150000,
    },
]


@patch('sys.stdout', new_callable=MagicMock)
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('screen_thai_dividends.datetime')
@patch('screen_thai_dividends.is_available', return_value=True)
@patch('screen_thai_dividends.get_thai_stocks', return_value=MOCK_STOCKS)
@patch('screen_thai_dividends.filter_common_stocks', side_effect=lambda x: x) # Simply return what's passed
@patch('argparse.ArgumentParser')
def test_main_function_integration(
    mock_arg_parser,
    mock_filter_common_stocks,
    mock_get_thai_stocks,
    mock_tv_available,
    mock_datetime,
    mock_json_dump,
    mock_open_file,
    mock_makedirs,
    mock_stdout,
):
    # Setup mock for argparse
    mock_args = MagicMock()
    mock_args.output_dir = "test_reports/"
    mock_args.min_yield = 3.0
    mock_args.min_mcap = 5e9
    mock_args.min_turnover = 10_000_000
    mock_args.top = 2
    mock_arg_parser.return_value.parse_args.return_value = mock_args

    # Setup mock for datetime to ensure predictable timestamp
    mock_datetime.now.return_value.strftime.return_value = "2026-06-16_123456"

    # Call main
    main()

    # Assertions
    mock_tv_available.assert_called_once()
    mock_get_thai_stocks.assert_called_once_with(limit=1500)
    mock_filter_common_stocks.assert_called_once_with(MOCK_STOCKS)
    mock_makedirs.assert_called_once_with("test_reports/", exist_ok=True)

    # Check JSON file writing
    json_filepath = os.path.join("test_reports/", "thai_dividends_2026-06-16_123456.json")
    md_filepath = os.path.join("test_reports/", "thai_dividends_2026-06-16_123456.md")

    # Assert correct calls to open for both JSON and MD files
    mock_open_file.assert_any_call(json_filepath, "w", encoding="utf-8")
    mock_open_file.assert_any_call(md_filepath, "w", encoding="utf-8")

    # Re-run scoring for mock stocks to get actual scores given current logic
    s1_ok, s1_score, s1_metrics = score_stock(MOCK_STOCKS[0], 3.0, 5e9, 10_000_000)
    s2_ok, s2_score, s2_metrics = score_stock(MOCK_STOCKS[1], 3.0, 5e9, 10_000_000)
    
    expected_candidates = []
    if s1_ok:
        expected_candidates.append({
            "symbol": MOCK_STOCKS[0]["symbol"],
            "name": MOCK_STOCKS[0]["name"],
            "sector": MOCK_STOCKS[0]["sector"],
            "price": MOCK_STOCKS[0]["price"],
            "marketCap": MOCK_STOCKS[0]["marketCap"],
            "avg_turnover": MOCK_STOCKS[0]["avg_turnover"],
            "liquidity_score": MOCK_STOCKS[0].get("liquidity_score"), 
            "dividend_yield": MOCK_STOCKS[0]["dividend_yield"],
            "pe_ratio": MOCK_STOCKS[0]["pe_ratio"],
            "rsi": MOCK_STOCKS[0]["rsi"],
            "sma50": MOCK_STOCKS[0]["sma50"],
            "sma200": MOCK_STOCKS[0]["sma200"],
            "perf_1m": MOCK_STOCKS[0]["perf_1m"],
            "perf_y": MOCK_STOCKS[0]["perf_y"],
            "score": s1_score,
            "grade": grade(s1_score),
            "score_breakdown": s1_metrics,
        })
    if s2_ok:
        expected_candidates.append({
            "symbol": MOCK_STOCKS[1]["symbol"],
            "name": MOCK_STOCKS[1]["name"],
            "sector": MOCK_STOCKS[1]["sector"],
            "price": MOCK_STOCKS[1]["price"],
            "marketCap": MOCK_STOCKS[1]["marketCap"],
            "avg_turnover": MOCK_STOCKS[1]["avg_turnover"],
            "liquidity_score": MOCK_STOCKS[1].get("liquidity_score"),
            "dividend_yield": MOCK_STOCKS[1]["dividend_yield"],
            "pe_ratio": MOCK_STOCKS[1]["pe_ratio"],
            "rsi": MOCK_STOCKS[1]["rsi"],
            "sma50": MOCK_STOCKS[1]["sma50"],
            "sma200": MOCK_STOCKS[1]["sma200"],
            "perf_1m": MOCK_STOCKS[1]["perf_1m"],
            "perf_y": MOCK_STOCKS[1]["perf_y"],
            "score": s2_score,
            "grade": grade(s2_score),
            "score_breakdown": s2_metrics,
        })

    expected_candidates.sort(key=lambda r: r["score"], reverse=True)
    expected_candidates = expected_candidates[:mock_args.top]

    mock_json_dump.assert_called_once()
    args_json, kwargs_json = mock_json_dump.call_args
    dumped_payload = args_json[0]
    assert dumped_payload["generated"] == "2026-06-16_123456"
    assert len(dumped_payload["candidates"]) == 2 # Only two candidates pass filters
    assert dumped_payload["candidates"][0]["symbol"] == expected_candidates[0]["symbol"] # Check sorting
    assert dumped_payload["candidates"][1]["symbol"] == expected_candidates[1]["symbol"]

    # Check markdown file writing
    mock_open_file.return_value.write.assert_called_with(unittest.mock.ANY) # Check any string written
    # More specific assertion on markdown content could be added if needed,
    # but that would duplicate to_markdown's internal logic.

    # Check console output
    mock_stdout.write.assert_called()
    output_calls = [call.args[0] for call in mock_stdout.write.call_args_list]
    output_str = "".join(output_calls)

    assert "Thai Dividend Screener" in output_str
    assert "Fetching SET universe... OK (3 stocks)" in output_str
    assert "Scoring... OK (2 candidates)" in output_str # Only 2 candidates pass filters
    assert "Reports:" in output_str
    assert "STOCK2" in output_str # Check top candidates are printed
    assert "STOCK1" in output_str
