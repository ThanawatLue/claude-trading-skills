"""Tests for thai-sector-heatmap.

Pure unit tests — no TradingView network calls. We feed synthetic stock dicts
to compute_sector_stats() and verify the ranking and aggregation logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

from generate_heatmap import (  # noqa: E402
    compute_sector_stats,
    _median,
    _momentum_score,
    _emoji,
)


def _stock(symbol, sector, p1m=0, p3m=0, p6m=0, py=0, price=10):
    return {
        "symbol": symbol,
        "sector": sector,
        "price": price,
        "perf_1m": p1m,
        "perf_3m": p3m,
        "perf_6m": p6m,
        "perf_y": py,
    }


def test_groups_by_sector():
    stocks = [
        _stock("A.BK", "Tech", p1m=10),
        _stock("B.BK", "Tech", p1m=20),
        _stock("C.BK", "Tech", p1m=30),
        _stock("D.BK", "Energy", p1m=-5),
        _stock("E.BK", "Energy", p1m=-3),
        _stock("F.BK", "Energy", p1m=-1),
    ]
    out = compute_sector_stats(stocks)
    sectors = {s["sector"]: s for s in out}
    assert "Tech" in sectors and "Energy" in sectors
    assert sectors["Tech"]["n_stocks"] == 3
    assert sectors["Energy"]["n_stocks"] == 3


def test_median_calculation():
    stocks = [
        _stock("A.BK", "Tech", p1m=10),
        _stock("B.BK", "Tech", p1m=20),
        _stock("C.BK", "Tech", p1m=30),
    ]
    out = compute_sector_stats(stocks)
    assert out[0]["median_perf_1m"] == 20  # median of [10, 20, 30]


# New _median tests
def test_median_odd_elements():
    assert _median([1, 2, 3]) == 2.0

def test_median_even_elements():
    assert _median([1, 2, 3, 4]) == 2.5

def test_median_single_element():
    assert _median([5]) == 5.0

def test_median_empty_list():
    assert _median([]) == 0.0

def test_median_all_none():
    assert _median([None, None, None]) == 0.0

def test_median_mixed_none_and_numbers():
    assert _median([1, None, 2, None, 3]) == 2.0
    assert _median([None, 10, None, 20]) == 15.0


# New _momentum_score tests
def test_momentum_score_positive():
    assert _momentum_score(20, 15, 10, 5) == 16.55

def test_momentum_score_negative():
    assert _momentum_score(-10, -5, -2, -1) == -6.05

def test_momentum_score_mixed():
    assert _momentum_score(10, -5, 2, 0) == 2.85

def test_momentum_score_zero():
    assert _momentum_score(0, 0, 0, 0) == 0.0


# New _emoji tests
def test_emoji_hot():
    assert _emoji(10) == "🟢"
    assert _emoji(15) == "🟢"

def test_emoji_neutral():
    assert _emoji(0) == "🟡"
    assert _emoji(9.99) == "🟡"

def test_emoji_cold():
    assert _emoji(-1) == "🔴"
    assert _emoji(-10) == "🔴"


def test_ranks_by_momentum_score():
    stocks = [
        _stock("A.BK", "Hot", p1m=20, p3m=30, p6m=40),
        _stock("B.BK", "Hot", p1m=25, p3m=35, p6m=45),
        _stock("C.BK", "Hot", p1m=30, p3m=40, p6m=50),
        _stock("D.BK", "Cold", p1m=-10, p3m=-15, p6m=-20),
        _stock("E.BK", "Cold", p1m=-12, p3m=-18, p6m=-22),
        _stock("F.BK", "Cold", p1m=-15, p3m=-20, p6m=-25),
    ]
    out = compute_sector_stats(stocks)
    # Hot sector should rank 1 (positive scores), Cold sector last
    assert out[0]["sector"] == "Hot"
    assert out[0]["rank"] == 1
    assert out[-1]["sector"] == "Cold"
    assert out[0]["momentum_score"] > out[-1]["momentum_score"]


def test_drops_small_sectors():
    """Sectors with fewer than 3 stocks should be dropped (median unreliable)."""
    stocks = [
        _stock("A.BK", "Big", p1m=10),
        _stock("B.BK", "Big", p1m=20),
        _stock("C.BK", "Big", p1m=30),
        _stock("D.BK", "Tiny", p1m=99),  # only 1 stock → dropped
        _stock("E.BK", "Mini", p1m=50),
        _stock("F.BK", "Mini", p1m=60),  # only 2 stocks → dropped
    ]
    out = compute_sector_stats(stocks)
    names = {s["sector"] for s in out}
    assert "Big" in names
    assert "Tiny" not in names
    assert "Mini" not in names


def test_handles_unknown_sector():
    """Stocks with sector=None or 'Unknown' should be grouped or dropped gracefully."""
    stocks = [
        _stock("A.BK", "Tech", p1m=10),
        _stock("B.BK", "Tech", p1m=20),
        _stock("C.BK", "Tech", p1m=30),
        {"symbol": "X.BK", "sector": None, "price": 10, "perf_1m": 0, "perf_3m": 0, "perf_6m": 0, "perf_y": 0},
    ]
    # Should not crash
    out = compute_sector_stats(stocks)
    assert any(s["sector"] == "Tech" for s in out)


def test_top_stocks_field():
    stocks = [
        _stock("A.BK", "Tech", p3m=10),
        _stock("B.BK", "Tech", p3m=30),
        _stock("C.BK", "Tech", p3m=20),
        _stock("D.BK", "Tech", p3m=5),
        _stock("E.BK", "Tech", p3m=None), # Test case for None
        _stock("F.BK", "Tech", p3m=-5),
    ]
    out = compute_sector_stats(stocks)
    top = out[0]["top_stocks"]
    assert len(top) == 3 # Should still be 3 top stocks
    # B should be first (highest p3m)
    assert top[0]["symbol"] == "B.BK"
    assert top[1]["symbol"] == "C.BK"
    assert top[2]["symbol"] == "A.BK"

