from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCRIPT_DIR = _REPO_ROOT / "skills" / "vcp-screener" / "scripts"
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from screen_thai_swing import (
    build_plan,
    get_set_tick_size,
    get_tick_spread_pct,
    score_dip_buy,
)


def test_get_set_tick_size_brackets():
    assert get_set_tick_size(1.50) == 0.01
    assert get_set_tick_size(2.00) == 0.02
    assert get_set_tick_size(4.98) == 0.02
    assert get_set_tick_size(5.00) == 0.05
    assert get_set_tick_size(9.90) == 0.05
    assert get_set_tick_size(10.00) == 0.10
    assert get_set_tick_size(24.50) == 0.10
    assert get_set_tick_size(25.00) == 0.25
    assert get_set_tick_size(99.50) == 0.25
    assert get_set_tick_size(100.00) == 0.50
    assert get_set_tick_size(200.00) == 1.00
    assert get_set_tick_size(450.00) == 2.00


def test_get_tick_spread_pct_identifies_spread_traps():
    # Boundary traps (first tick of the bracket) have ~0.99% - 1.0% single tick spread
    assert get_tick_spread_pct(2.02) > 0.80
    assert get_tick_spread_pct(5.05) > 0.80
    assert get_tick_spread_pct(10.10) > 0.80
    assert get_tick_spread_pct(25.25) > 0.80

    # Well inside the bracket has much lower single tick spread
    assert get_tick_spread_pct(4.50) < 0.60
    assert get_tick_spread_pct(9.00) < 0.60
    assert get_tick_spread_pct(20.00) < 0.60
    assert get_tick_spread_pct(60.00) < 0.50


def test_build_plan_incorporates_set_tick_minimum():
    # If recent low is very close to entry (e.g. entry=5.05, recent_low=5.00),
    # normal 0.99 * recent_low gives 4.95 (only 0.10 = 2 ticks away).
    # The updated build_plan ensures at least 3 ticks (0.15) distance for Thai stocks.
    plan = build_plan(price=5.05, strategy="DIP_BUY", atr=0.08, recent_low=5.00)
    stop = plan["stop"]
    assert stop <= round(5.05 - (0.05 * 3.0), 2)  # At least 3 ticks of 0.05
    assert plan["risk_pct"] >= 3.0


def test_score_dip_buy_rejects_severe_spread_traps():
    # A stock with identical technicals but at 2.02 (0.99% single tick spread)
    # should be penalized or filtered vs a stock at 4.50 (0.44% single tick spread)
    candidate_trap = {
        "price": 2.02,
        "rsi": 44,
        "rsi_weekly": 48,
        "sma20": 2.10,
        "sma50": 1.95,
        "sma200": 1.80,
        "volume": 1_000_000,
        "avgVolume": 1_000_000,
    }
    candidate_good = {
        "price": 4.50,
        "rsi": 44,
        "rsi_weekly": 48,
        "sma20": 4.65,
        "sma50": 4.30,
        "sma200": 4.00,
        "volume": 1_000_000,
        "avgVolume": 1_000_000,
    }
    score_trap = score_dip_buy(candidate_trap)
    score_good = score_dip_buy(candidate_good)
    assert score_good > score_trap
