"""Unit tests for pattern_stats.py, dual_check_service trade plans, and /api/patterns."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from dashboard.services.dual_check_service import evaluate_candidate
from dashboard.services.pattern_stats import (
    _atr,
    _calculate_rsi_series,
    _ema,
    compute_confluence,
    compute_day_bias,
)


def _generate_bars(n: int = 100, *, base_price: float = 100.0, trend: float = 0.005) -> list[dict]:
    start_date = date(2026, 1, 5)
    bars = []
    p = base_price
    for i in range(n):
        d = start_date + timedelta(days=i)
        open_px = p
        close_px = p * (1.0 + trend)
        high_px = max(open_px, close_px) * 1.01
        low_px = min(open_px, close_px) * 0.99
        vol = 1_000_000.0 + (i * 1000)
        bars.append(
            {
                "date": d.isoformat(),
                "open": round(open_px, 2),
                "high": round(high_px, 2),
                "low": round(low_px, 2),
                "close": round(close_px, 2),
                "volume": vol,
            }
        )
        p = close_px
    return bars


def test_calculate_rsi_series_standard() -> None:
    closes = [100.0 + (i % 5) for i in range(30)]
    rsi_series = _calculate_rsi_series(closes, period=14)
    assert len(rsi_series) == 30
    assert rsi_series[0] is None
    assert rsi_series[13] is None
    assert rsi_series[14] is not None
    assert 0.0 <= rsi_series[14] <= 100.0


def test_ema_and_atr_helpers() -> None:
    bars = _generate_bars(30, base_price=50.0, trend=0.01)
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]

    ema10 = _ema(closes, 25, 10)
    assert ema10 is not None
    assert 50.0 < ema10 < 80.0

    atr14 = _atr(highs, lows, closes, 25, 14)
    assert atr14 is not None
    assert atr14 > 0.0


def test_confluence_extension_detection() -> None:
    # Build bars with a huge run-up on the last bar to trigger EMA10 extension >= 2.5 ATR
    bars = _generate_bars(60, base_price=100.0, trend=0.001)
    # Give the last bar an extreme spike
    last = bars[-1]
    last["open"] = 150.0
    last["close"] = 160.0
    last["high"] = 162.0
    last["low"] = 149.0

    conf = compute_confluence(bars)
    assert conf is not None
    assert conf["extension_ema10_atr"] is not None
    assert conf["extension_ema10_atr"] >= 2.5
    assert conf["is_extended"] is True
    assert conf["flags"]["is_extended"] is True


def test_day_bias_median_return() -> None:
    bars = _generate_bars(80, base_price=100.0, trend=0.005)
    bias = compute_day_bias(bars, hold_style="overnight")
    assert bias is not None
    assert "median_return" in bias
    if not bias.get("insufficient_samples"):
        assert isinstance(bias["median_return"], float)


def test_swing_pivot_rsi_bull_divergence() -> None:
    # Construct bars with a swing low pivot at idx - 10, then lower price today with higher RSI
    bars = _generate_bars(60, base_price=100.0, trend=-0.005)
    # At idx - 10, create a swing low pivot (lowest among +/- 2 bars)
    pivot_idx = 48
    bars[pivot_idx]["low"] = 70.0
    bars[pivot_idx]["close"] = 71.0
    for offset in (-2, -1, 1, 2):
        bars[pivot_idx + offset]["low"] = 75.0
        bars[pivot_idx + offset]["close"] = 76.0

    # Today (last bar) lower price than swing low pivot
    bars[-1]["close"] = 69.0
    bars[-1]["low"] = 68.0

    conf = compute_confluence(bars)
    assert conf is not None
    assert "rsi_bull_div" in conf["flags"]
    assert "rsi_bear_div" in conf["flags"]


def test_evaluate_candidate_synthesizes_trade_plan() -> None:
    row = {
        "symbol": "PTT.BK",
        "price": 34.50,
        "composite_score": 88.0,
        "execution_state": "Breakout",
        "distance_from_pivot_pct": 0.5,
        "rs_percentile": 85.0,
        "source": "thai_swing_momentum",
    }
    cand = evaluate_candidate(
        row,
        regime_allowed=True,
        hold_style="intraday",
        canslim_by_symbol={},
        earnings_lookup=None,
    )
    assert cand["plan"] is not None
    assert cand["plan"]["entry"] == 34.50
    assert cand["plan"]["stop_loss"] < 34.50
    assert cand["plan"]["take_profit"] > 34.50
    assert cand["plan"]["risk_pct"] > 0
    assert cand["price"] == 34.50


def test_api_patterns_endpoint(tmp_path, monkeypatch) -> None:
    from dashboard.app import app

    test_client = app.test_client()

    db_dir = tmp_path / "state"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "market_cache.db"

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE price_bar (
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
        )
        """
    )
    # Insert 30 bars with repeated 3-red drops followed by strong green bounce
    p = 100.0
    for i in range(30):
        step = i % 4
        if step < 3:
            # red bar
            o = p
            c = p - 1.0
        else:
            # green bounce bar
            o = p
            c = p + 2.0
        conn.execute(
            "INSERT INTO price_bar VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "CPALL.BK",
                f"2026-01-{(i % 28) + 1:02d}",
                o,
                max(o, c) + 0.5,
                min(o, c) - 0.5,
                c,
                100000.0,
            ),
        )
        p = c
    conn.commit()
    conn.close()

    monkeypatch.setattr("dashboard.app.BASE_DIR", str(tmp_path))

    res = test_client.get("/api/patterns?market=TH")
    assert res.status_code == 200
    data = res.get_json()
    assert "Oversold" in data
    assert "Overbought" in data
    assert data["market"] == "TH"
