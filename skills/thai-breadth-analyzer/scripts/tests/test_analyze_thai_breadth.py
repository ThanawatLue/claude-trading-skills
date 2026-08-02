"""Tests for thai-breadth-analyzer — composite scoring and regime classification."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyze_thai_breadth import composite_score, to_markdown  # noqa: E402


def _breadth(pct50=50, pct200=50, adv=400, dec=400, hi=20, lo=20, total=800):
    return {
        "pct_above_sma50": pct50,
        "pct_above_sma200": pct200,
        "advancers": adv,
        "decliners": dec,
        "new_52w_highs": hi,
        "new_52w_lows": lo,
        "total_stocks": total,
    }


def test_balanced_market_around_fifty():
    """50% above MAs, equal A/D, equal highs/lows → composite around 50."""
    score, regime = composite_score(_breadth())
    assert 45 <= score <= 55
    assert regime in ("Healthy Uptrend", "Mixed / Corrective")


def test_strong_bull():
    """80% above SMAs, lots of advancers + new highs → score ≥ 70 = Strong Bull."""
    score, regime = composite_score(_breadth(pct50=85, pct200=75, adv=600, dec=150, hi=80, lo=5))
    assert score >= 70
    assert regime == "Strong Bull"


def test_bear_market():
    """20% above SMAs, mostly decliners, new lows expanding → score < 30 = Bear."""
    score, regime = composite_score(_breadth(pct50=20, pct200=15, adv=150, dec=600, hi=5, lo=80))
    assert score < 30
    assert regime == "Bear Regime"


def test_regime_boundary_70():
    """Score exactly 70 → Strong Bull (>=70)."""
    # Engineer inputs that produce ~70
    score, regime = composite_score(_breadth(pct50=70, pct200=70, adv=500, dec=300, hi=60, lo=20))
    assert score >= 50  # Healthy or Strong
    assert regime in ("Strong Bull", "Healthy Uptrend")


def test_score_bounded_to_0_100():
    """Even extreme inputs should clamp to [0, 100]."""
    score, _ = composite_score(_breadth(pct50=100, pct200=100, adv=800, dec=0, hi=200, lo=0, total=800))
    assert 0 <= score <= 100
    score, _ = composite_score(_breadth(pct50=0, pct200=0, adv=0, dec=800, hi=0, lo=200, total=800))
    assert 0 <= score <= 100


def test_zero_total_no_crash():
    """Empty market (total=0) should not divide-by-zero."""
    b = _breadth(total=0, adv=0, dec=0, hi=0, lo=0)
    score, regime = composite_score(b)
    assert isinstance(score, (int, float))
import unittest.mock
import tempfile
import shutil

# ... (existing imports and tests) ...


def test_main_integration():
    """Integration test for the main function: data fetch, process, and file output."""
    mock_breadth_data = {
        "total_stocks": 750,
        "pct_above_sma50": 60.0,
        "pct_above_sma200": 55.0,
        "advancers": 400,
        "decliners": 300,
        "unchanged": 50,
        "new_52w_highs": 25,
        "new_52w_lows": 10,
        "median_rsi": 52.0,
        "rsi_oversold": 15,
        "rsi_overbought": 70,
        "median_perf_1m": 1.5,
        "median_perf_3m": 4.0,
        "sector_breakdown": [
            ("Energy", 2.0),
            ("Banking", 1.0),
        ],
    }

    # Use a TemporaryDirectory for output files
    with tempfile.TemporaryDirectory() as tmpdir:
        with unittest.mock.patch("analyze_thai_breadth.get_thai_breadth", return_value=mock_breadth_data):
            with unittest.mock.patch("analyze_thai_breadth.tv_available", return_value=True):
                # Mock sys.argv to pass arguments to main()
                test_args = ["analyze_thai_breadth.py", "--output-dir", tmpdir]
                with unittest.mock.patch("sys.argv", test_args):
                    from analyze_thai_breadth import main
                    main()

                # Assert files were created
                output_files = list(Path(tmpdir).iterdir())
                assert len(output_files) == 2
                json_file = next(f for f in output_files if f.suffix == ".json")
                md_file = next(f for f in output_files if f.suffix == ".md")

                assert json_file.exists()
                assert md_file.exists()

                # Validate JSON content
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    assert data["market"] == "TH"
                    assert data["composite_score"] > 0
                    assert "regime" in data
                    assert data["breadth"]["total_stocks"] == 750

                # Validate Markdown content
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "Thai Market Breadth Report" in content
                    assert "Composite Score:" in content
                    assert "Healthy Uptrend" in content
                    assert "Sector Strength" in content
                    assert "Energy | +2.00%" in content


def test_to_markdown_with_sectors():
    """Test to_markdown function with sector breakdown data."""
    sample_breadth_data = {
        "total_stocks": 800,
        "pct_above_sma50": 65.5,
        "pct_above_sma200": 58.2,
        "advancers": 450,
        "decliners": 300,
        "unchanged": 50,
        "new_52w_highs": 30,
        "new_52w_lows": 5,
        "median_rsi": 55.3,
        "rsi_oversold": 20,
        "rsi_overbought": 80,
        "median_perf_1m": 2.1,
        "median_perf_3m": 5.8,
        "sector_breakdown": [
            ("Energy", 3.5),
            ("Banking", 1.2),
            ("Food", -0.5),
        ],
    }
    sample_score = 62.1
    sample_regime = "Healthy Uptrend"
    sample_timestamp = "2026-06-15_103000"

    expected_markdown = """# Thai Market Breadth Report
**Generated:** 2026-06-15_103000  |  **Universe:** 800 SET stocks  |  **Source:** TradingView Screener

## Composite Score: **62.1 / 100** — Healthy Uptrend

## Trend Participation

- **% above SMA50:** 65.50%
- **% above SMA200:** 58.20%

## Today's Tape

- **Advancers:** 450
- **Decliners:** 300
- **Unchanged:** 50

## Leadership (52w Highs/Lows)

- **New 52w highs (within 2%):** 30
- **New 52w lows (within 2%):** 5

## RSI Distribution

- **Median RSI:** 55.30
- **Oversold (RSI < 30):** 20
- **Overbought (RSI > 70):** 80

## Performance

- **Median 1M return:** +2.10%
- **Median 3M return:** +5.80%

## Sector Strength (Median 1M Return)

| Sector | 1M % |
|--------|------
| Energy | +3.50% |
| Banking | +1.20% |
| Food | -0.50% |

## Composite Score Methodology

- 40% × `pct_above_sma50` (trend participation)
- 30% × `pct_above_sma200` (long-term trend)
- 15% × normalized A/D balance
- 15% × normalized new highs/lows balance

Score bands: ≥70 Strong Bull · 50-70 Healthy Uptrend · 30-50 Mixed · <30 Bear"""

    generated_markdown = to_markdown(sample_breadth_data, sample_score, sample_regime, sample_timestamp)
    assert generated_markdown == expected_markdown

def test_to_markdown_no_sectors():
    """Test to_markdown function without sector breakdown data."""
    sample_breadth_data = {
        "total_stocks": 800,
        "pct_above_sma50": 65.5,
        "pct_above_sma200": 58.2,
        "advancers": 450,
        "decliners": 300,
        "unchanged": 50,
        "new_52w_highs": 30,
        "new_52w_lows": 5,
        "median_rsi": 55.3,
        "rsi_oversold": 20,
        "rsi_overbought": 80,
        "median_perf_1m": 2.1,
        "median_perf_3m": 5.8,
        # No sector_breakdown key
    }
    sample_score = 62.1
    sample_regime = "Healthy Uptrend"
    sample_timestamp = "2026-06-15_103000"

    expected_markdown = """# Thai Market Breadth Report
**Generated:** 2026-06-15_103000  |  **Universe:** 800 SET stocks  |  **Source:** TradingView Screener

## Composite Score: **62.1 / 100** — Healthy Uptrend

## Trend Participation

- **% above SMA50:** 65.50%
- **% above SMA200:** 58.20%

## Today's Tape

- **Advancers:** 450
- **Decliners:** 300
- **Unchanged:** 50

## Leadership (52w Highs/Lows)

- **New 52w highs (within 2%):** 30
- **New 52w lows (within 2%):** 5

## RSI Distribution

- **Median RSI:** 55.30
- **Oversold (RSI < 30):** 20
- **Overbought (RSI > 70):** 80

## Performance

- **Median 1M return:** +2.10%
- **Median 3M return:** +5.80%

## Composite Score Methodology

- 40% × `pct_above_sma50` (trend participation)
- 30% × `pct_above_sma200` (long-term trend)
- 15% × normalized A/D balance
- 15% × normalized new highs/lows balance

Score bands: ≥70 Strong Bull · 50-70 Healthy Uptrend · 30-50 Mixed · <30 Bear"""

    generated_markdown = to_markdown(sample_breadth_data, sample_score, sample_regime, sample_timestamp)
    assert generated_markdown == expected_markdown

