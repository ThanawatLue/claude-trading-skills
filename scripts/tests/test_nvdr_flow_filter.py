#!/usr/bin/env python3
"""Unit tests for NVDR Flow Divergence Filter.

Verifies:
1. SQLite nvdr_flow table creation and record upserting.
2. Bull trap divergence detection (price surging while NVDR net dumps).
3. Institutional accumulation detection (heavy net NVDR buying).
4. Neutral flow and graceful handling of missing/insufficient data.
5. 5-day rolling aggregation of institutional net value.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.nvdr_flow_filter import (
    analyze_nvdr_divergence,
    get_nvdr_flow,
    init_nvdr_table,
    upsert_nvdr_flow,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database for testing."""
    db_file = tmp_path / "test_market_cache.db"
    init_nvdr_table(db_file)
    return db_file


def test_init_and_upsert_nvdr_flow(temp_db: Path):
    """Test table creation and upserting of daily NVDR records."""
    records = [
        {
            "symbol": "DELTA",
            "date": "2026-09-25",
            "buy_vol": 1_000_000,
            "sell_vol": 500_000,
            "net_vol": 500_000,
            "buy_val": 100_000_000.0,
            "sell_val": 50_000_000.0,
            "net_val": 50_000_000.0,
            "nvdr_ratio": 25.5,
        },
        {
            "symbol": "DELTA",
            "date": "2026-09-26",
            "buy_vol": 2_000_000,
            "sell_vol": 1_000_000,
            "net_vol": 1_000_000,
            "buy_val": 200_000_000.0,
            "sell_val": 100_000_000.0,
            "net_val": 100_000_000.0,
            "nvdr_ratio": 30.0,
        },
    ]

    inserted = upsert_nvdr_flow(records, db_path=temp_db)
    assert inserted == 2

    # Fetch records back
    flow = get_nvdr_flow("DELTA", days=5, db_path=temp_db)
    assert len(flow) == 2
    # Verify sorted descending by date
    assert flow[0]["date"] == "2026-09-26"
    assert flow[0]["net_val"] == 100_000_000.0


def test_bull_trap_divergence_detected(temp_db: Path):
    """Test flagging of bull trap divergence when stock rallies but NVDR dumps."""
    records = [
        {
            "symbol": "KBANK",
            "date": "2026-09-26",
            "buy_vol": 500_000,
            "sell_vol": 2_000_000,
            "net_vol": -1_500_000,
            "buy_val": 75_000_000.0,
            "sell_val": 300_000_000.0,
            "net_val": -225_000_000.0,  # Heavy dump: -225M THB
            "nvdr_ratio": 35.0,
        },
        {
            "symbol": "KBANK",
            "date": "2026-09-25",
            "buy_vol": 1_000_000,
            "sell_vol": 1_500_000,
            "net_vol": -500_000,
            "buy_val": 150_000_000.0,
            "sell_val": 225_000_000.0,
            "net_val": -75_000_000.0,
            "nvdr_ratio": 28.0,
        },
    ]
    upsert_nvdr_flow(records, db_path=temp_db)

    # Stock is surging +3.5%
    result = analyze_nvdr_divergence(
        symbol="KBANK",
        current_price=150.0,
        price_change_pct=3.5,
        db_path=temp_db,
    )

    assert result.status == "DIVERGENCE_BULL_TRAP"
    assert result.is_bull_trap is True
    assert result.score_modifier <= -20.0
    assert result.net_val_1d == -225_000_000.0
    assert result.net_val_5d == -300_000_000.0
    assert "Bull trap" in result.details


def test_institutional_accumulation_detected(temp_db: Path):
    """Test rewarding accumulation when stock has strong NVDR net buying."""
    records = [
        {
            "symbol": "PTT",
            "date": "2026-09-26",
            "buy_vol": 5_000_000,
            "sell_vol": 1_000_000,
            "net_vol": 4_000_000,
            "buy_val": 175_000_000.0,
            "sell_val": 35_000_000.0,
            "net_val": 140_000_000.0,  # Strong net buy: +140M THB
            "nvdr_ratio": 32.0,
        }
    ]
    upsert_nvdr_flow(records, db_path=temp_db)

    result = analyze_nvdr_divergence(
        symbol="PTT",
        current_price=35.0,
        price_change_pct=1.5,
        db_path=temp_db,
    )

    assert result.status == "ACCUMULATION"
    assert result.is_bull_trap is False
    assert result.score_modifier == 15.0
    assert result.net_val_1d == 140_000_000.0
    assert "accumulation" in result.details.lower()


def test_neutral_flow(temp_db: Path):
    """Test neutral status when NVDR net flow is minor and balanced."""
    records = [
        {
            "symbol": "CPALL",
            "date": "2026-09-26",
            "buy_vol": 100_000,
            "sell_vol": 90_000,
            "net_vol": 10_000,
            "buy_val": 6_500_000.0,
            "sell_val": 5_850_000.0,
            "net_val": 650_000.0,  # Small net buy < 10M THB
            "nvdr_ratio": 12.0,
        }
    ]
    upsert_nvdr_flow(records, db_path=temp_db)

    result = analyze_nvdr_divergence(
        symbol="CPALL",
        current_price=65.0,
        price_change_pct=0.5,
        db_path=temp_db,
    )

    assert result.status == "NEUTRAL"
    assert result.is_bull_trap is False
    assert result.score_modifier == 0.0


def test_no_data_fallback(temp_db: Path):
    """Test graceful handling when no NVDR data exists for the symbol."""
    result = analyze_nvdr_divergence(
        symbol="UNKNOWN_STOCK",
        current_price=10.0,
        price_change_pct=2.0,
        db_path=temp_db,
    )

    assert result.status == "NO_DATA"
    assert result.is_bull_trap is False
    assert result.score_modifier == 0.0
    assert "No NVDR data" in result.details
