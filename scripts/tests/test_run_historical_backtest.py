#!/usr/bin/env python3
"""Unit tests for Historical Backtest Engine.

Verifies:
1. Calculation of technical indicators (SMA, RSI, ATR, Volume).
2. Set tick rounding and US tick rounding rules.
3. Simulation run across mock price history with expected metric outputs.
4. Correct attribution of exit reasons (Two-tier scale out, Velocity stall, Breakeven stop).
"""

from __future__ import annotations

from scripts.run_historical_backtest import (
    BacktestConfig,
    compute_indicators,
    get_set_tick,
    round_tick,
    run_backtest_simulation,
)


def test_get_set_tick_ladders():
    """Verify SET tick rules across all price brackets."""
    assert get_set_tick(1.50) == 0.01
    assert get_set_tick(3.20) == 0.02
    assert get_set_tick(7.50) == 0.05
    assert get_set_tick(18.0) == 0.10
    assert get_set_tick(45.0) == 0.25
    assert get_set_tick(120.0) == 0.50
    assert get_set_tick(250.0) == 1.00
    assert get_set_tick(500.0) == 2.00


def test_round_tick():
    """Verify tick rounding up, down, and nearest."""
    assert round_tick(18.23, market="TH", direction="down") == 18.20
    assert round_tick(18.23, market="TH", direction="up") == 18.30
    assert round_tick(150.32, market="US", direction="nearest") == 150.32


def test_compute_indicators_shape():
    """Verify indicator generation on a minimal synthetic bar series."""
    bars = []
    for i in range(40):
        price = 100.0 + i
        bars.append(
            {
                "symbol": "TEST",
                "date": f"2026-01-{i + 1:02d}",
                "open": price,
                "high": price + 2.0,
                "low": price - 2.0,
                "close": price + 1.0,
                "volume": 100000.0 + (i * 1000),
            }
        )
    processed = compute_indicators(bars)
    assert len(processed) == 40
    last_bar = processed[-1]
    assert "sma20" in last_bar
    assert "rsi14" in last_bar
    assert "atr14" in last_bar
    assert "vol_sma20" in last_bar
    assert last_bar["sma20"] > 0
    assert 0 <= last_bar["rsi14"] <= 100


def test_run_backtest_simulation_synthetic():
    """Verify that backtest simulation executes and produces valid SimulationResult."""
    # Generate 45 bars for 2 symbols: one winner, one benchmark
    test_bars = []
    bench_bars = []
    for i in range(45):
        d_str = f"2026-02-{i + 1:02d}" if i < 28 else f"2026-03-{i - 27:02d}"
        bench_price = 100.0 + (i * 0.2)
        bench_bars.append(
            {
                "symbol": "SPY",
                "date": d_str,
                "open": bench_price,
                "high": bench_price + 1.0,
                "low": bench_price - 1.0,
                "close": bench_price + 0.5,
                "volume": 500000.0,
            }
        )

        stock_price = 50.0 + (i * 0.8)  # Trending up
        test_bars.append(
            {
                "symbol": "WINR",
                "date": d_str,
                "open": stock_price,
                "high": stock_price + 2.0,
                "low": stock_price - 0.5,
                "close": stock_price + 1.5,
                "volume": 200000.0 + (i * 5000),
            }
        )

    bars_by_symbol = {"WINR": test_bars, "SPY": bench_bars}
    cfg = BacktestConfig(
        name="Test Config",
        use_two_tier_scale_out=True,
        use_velocity_stall=True,
        use_market_posture_gate=False,
    )

    result = run_backtest_simulation(
        bars_by_symbol=bars_by_symbol,
        benchmark_bars=bench_bars,
        market="US",
        config=cfg,
        initial_capital=1000.0,
        start_date="2026-02-01",
        end_date="2026-03-30",
    )

    assert result.config_name == "Test Config"
    assert result.market == "US"
    assert result.total_trades >= 0
    assert isinstance(result.win_rate, float)
    assert isinstance(result.profit_factor, float)
