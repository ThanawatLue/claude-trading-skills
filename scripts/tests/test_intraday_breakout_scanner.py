#!/usr/bin/env python3
"""Unit tests for Intraday Breakout & Volume Surge Scanner.

Verifies:
1. Accurate Opening Range (ORB-30/45) high and low extraction from intraday candles.
2. Relative Volume (RVOL) calculation.
3. Positive breakout detection (price > ORB high with RVOL >= 1.5x).
4. Rejection of non-breakouts (inside range) and low-volume moves.
5. Protection against over-extended chasing (>4.5% above ORB high).
6. File output generation to `intraday_candidates.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.intraday_breakout_scanner import (
    compute_orb_levels,
    evaluate_intraday_candidate,
    scan_intraday_breakouts,
)


@pytest.fixture
def sample_minute_bars() -> pd.DataFrame:
    """Generate 45 1-minute bars representing an opening range followed by a breakout."""
    # 09:30 to 10:15 (45 minutes)
    timestamps = pd.date_range("2026-09-28 09:30:00", periods=50, freq="1min")
    records = []
    for i, ts in enumerate(timestamps):
        if i < 30:
            # Range: Low 100.0, High 102.0, avg vol 1,000
            records.append(
                {
                    "Datetime": ts,
                    "Open": 100.5,
                    "High": 102.0 if i == 10 else 101.5,
                    "Low": 100.0 if i == 5 else 100.2,
                    "Close": 101.0,
                    "Volume": 1000,
                }
            )
        elif i < 45:
            # Still in range 100.5 - 102.0
            records.append(
                {
                    "Datetime": ts,
                    "Open": 101.0,
                    "High": 102.0,
                    "Low": 100.8,
                    "Close": 101.8,
                    "Volume": 1200,
                }
            )
        else:
            # Breakout bar: price pushes to 103.0 with volume surge 3,500
            records.append(
                {
                    "Datetime": ts,
                    "Open": 102.0,
                    "High": 103.0,
                    "Low": 101.9,
                    "Close": 102.8,
                    "Volume": 3500,
                }
            )
    df = pd.DataFrame(records).set_index("Datetime")
    return df


def test_compute_orb_levels(sample_minute_bars: pd.DataFrame):
    """Test extraction of ORB high, low, midpoint, and baseline volume."""
    orb = compute_orb_levels(sample_minute_bars, orb_minutes=30)
    assert orb is not None
    assert orb["orb_high"] == 102.0
    assert orb["orb_low"] == 100.0
    assert orb["orb_mid"] == 101.0
    assert orb["orb_volume"] == 30 * 1000  # 30,000


def test_evaluate_intraday_breakout_success(sample_minute_bars: pd.DataFrame):
    """Test successful breakout detection with strong RVOL."""
    # Current bar is the breakout bar: close=102.8, volume surge
    res = evaluate_intraday_candidate(
        symbol="PTT",
        bars=sample_minute_bars,
        avg_daily_volume=500_000,
        orb_minutes=30,
        market="TH",
    )

    assert res is not None
    assert res["is_breakout"] is True
    assert res["orb_high"] == 102.0
    assert res["current_price"] == 102.8
    assert res["rvol"] >= 1.5
    # Enforces the 4.5% stop width floor (102.8 * 0.955 -> 98.0 tick)
    assert res["suggested_stop"] <= 101.0
    assert (res["current_price"] - res["suggested_stop"]) / res["current_price"] >= 0.045
    assert res["suggested_target"] > 102.8
    assert res["score"] >= 75.0


def test_evaluate_intraday_rejection_inside_range():
    """Test that a stock remaining inside its opening range is rejected."""
    timestamps = pd.date_range("2026-09-28 09:30:00", periods=40, freq="1min")
    records = []
    for ts in timestamps:
        records.append(
            {
                "Datetime": ts,
                "Open": 50.0,
                "High": 51.0,
                "Low": 49.5,
                "Close": 50.2,  # Inside range
                "Volume": 1000,
            }
        )
    df = pd.DataFrame(records).set_index("Datetime")

    res = evaluate_intraday_candidate(
        "AOT", df, avg_daily_volume=200_000, orb_minutes=30, market="TH"
    )
    assert res is None or res["is_breakout"] is False


def test_evaluate_intraday_rejection_low_volume(sample_minute_bars: pd.DataFrame):
    """Test that breakout above high without RVOL confirmation is rejected."""
    # Set breakout volume very low
    df = sample_minute_bars.copy()
    df.loc[df.index >= df.index[45], "Volume"] = 200

    res = evaluate_intraday_candidate(
        "CPALL", df, avg_daily_volume=5_000_000, orb_minutes=30, market="TH"
    )
    # Low volume should fail RVOL filter
    assert res is None or res["is_breakout"] is False


def test_evaluate_intraday_rejection_overextended(sample_minute_bars: pd.DataFrame):
    """Test that stocks extended > 4.5% above ORB high are rejected to prevent chasing tops."""
    df = sample_minute_bars.copy()
    # High was 102.0. Set price to 108.0 (+5.8% extended)
    df.loc[df.index[-1], "Close"] = 108.0
    df.loc[df.index[-1], "High"] = 108.5

    res = evaluate_intraday_candidate(
        "DELTA", df, avg_daily_volume=500_000, orb_minutes=30, market="TH"
    )
    assert res is None or res["is_breakout"] is False


def test_scan_intraday_breakouts_exports_json(tmp_path: Path, sample_minute_bars: pd.DataFrame):
    """Test scanning a list of symbols and writing actionable JSON candidates."""
    mock_universe = ["PTT", "ADVANC"]

    def mock_data_provider(sym: str):
        return sample_minute_bars

    candidates = scan_intraday_breakouts(
        symbols=mock_universe,
        market="TH",
        output_dir=tmp_path,
        data_provider=mock_data_provider,
    )

    assert len(candidates) >= 1
    out_file = tmp_path / "intraday_candidates.json"
    assert out_file.exists()

    with open(out_file, encoding="utf-8") as f:
        saved_data = json.load(f)
        assert "candidates" in saved_data
        assert len(saved_data["candidates"]) >= 1
        assert saved_data["candidates"][0]["symbol"] in mock_universe
