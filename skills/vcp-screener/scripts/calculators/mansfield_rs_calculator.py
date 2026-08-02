#!/usr/bin/env python3
"""
Mansfield Relative Strength Calculator — Smoothed RS Line

Calculates the Mansfield Relative Strength, a smoothed version of the
RS line that compares a stock's price performance to a benchmark index.

Unlike raw RS (which is noisy), Mansfield RS uses a 52-week simple moving
average of the RS ratio to provide a cleaner trend signal.

Formula:
    RS Ratio = Stock Price / Index Price
    RS Ratio SMA52 = 52-week SMA of RS Ratio
    Mansfield RS = ((RS Ratio / RS Ratio SMA52) - 1) * 100

Interpretation:
    Mansfield RS > 0: Stock is outperforming the index
    Mansfield RS < 0: Stock is underperforming the index
    Mansfield RS rising: Relative strength is improving
    Mansfield RS falling: Relative strength is weakening
    Zero-line crossover (up): Bullish transition
    Zero-line crossover (down): Bearish transition

Scoring:
- 100: RS > +20 AND rising (strong market leader)
-  90: RS > +10 AND rising
-  80: RS > +5 AND rising
-  70: RS > 0 AND rising (outperforming and improving)
-  60: RS > 0 but flat/falling (outperforming but losing momentum)
-  50: RS near zero (±2%, matching index)
-  40: RS < 0 but rising (underperforming but improving)
-  30: RS < 0 AND falling (underperforming and weakening)
-  20: RS < -10 (significant laggard)
-   0: RS < -20 (severe underperformance)
"""

from typing import Optional


def calculate_mansfield_rs(
    stock_prices: list[dict],
    index_prices: list[dict],
) -> dict:
    """
    Calculate Mansfield Relative Strength vs a benchmark index.

    Args:
        stock_prices: Daily OHLCV for stock (most recent first), need 260+ days
        index_prices: Daily OHLCV for index (most recent first), need 260+ days

    Returns:
        Dict with score (0-100), rs_line_value, rs_line_direction, detail, error
    """
    min_days = 60  # Minimum for a usable (but degraded) calculation

    if not stock_prices or len(stock_prices) < min_days:
        return _empty_result("Insufficient stock price data (need 60+ days)")

    if not index_prices or len(index_prices) < min_days:
        return _empty_result("Insufficient index price data (need 60+ days)")

    # Extract closes (most recent first)
    stock_closes = [float(d.get("close") or d.get("adjClose") or 0) for d in stock_prices]
    index_closes = [float(d.get("close") or d.get("adjClose") or 0) for d in index_prices]

    # Ensure same length
    n = min(len(stock_closes), len(index_closes))
    stock_closes = stock_closes[:n]
    index_closes = index_closes[:n]

    # Calculate RS ratio series (stock/index)
    rs_ratios = []
    for i in range(n):
        if index_closes[i] > 0:
            rs_ratios.append(stock_closes[i] / index_closes[i])
        else:
            rs_ratios.append(None)

    # Filter None values at the beginning
    valid_ratios = [r for r in rs_ratios if r is not None]
    if len(valid_ratios) < min_days:
        return _empty_result("Insufficient valid RS ratio data")

    # Calculate SMA of RS ratio (use available data, up to 252 days)
    sma_period = min(252, len(valid_ratios))
    rs_ratio_current = valid_ratios[0]
    rs_ratio_sma = sum(valid_ratios[:sma_period]) / sma_period

    # Mansfield RS value
    if rs_ratio_sma <= 0:
        return _empty_result("Invalid RS ratio SMA (zero or negative)")

    mansfield_rs = ((rs_ratio_current / rs_ratio_sma) - 1) * 100

    # Calculate direction (compare current RS ratio to 20 days ago)
    rs_direction = "flat"
    rs_momentum = 0.0
    if len(valid_ratios) >= 20:
        rs_ratio_20d_ago_sma = sum(valid_ratios[20:min(20 + sma_period, len(valid_ratios))]) / min(sma_period, len(valid_ratios) - 20)
        if rs_ratio_20d_ago_sma > 0:
            mansfield_rs_20d_ago = ((valid_ratios[20] / rs_ratio_20d_ago_sma) - 1) * 100
            rs_momentum = mansfield_rs - mansfield_rs_20d_ago
            if rs_momentum > 1.0:
                rs_direction = "rising"
            elif rs_momentum < -1.0:
                rs_direction = "falling"
            else:
                rs_direction = "flat"

    # Detect zero-line crossover
    rs_zero_cross = None
    if len(valid_ratios) >= 5:
        # Check if we crossed zero in the last 5 days
        for i in range(1, min(5, len(valid_ratios))):
            ratio_sma_i = sum(valid_ratios[i:min(i + sma_period, len(valid_ratios))]) / min(sma_period, len(valid_ratios) - i)
            if ratio_sma_i > 0:
                prev_mrs = ((valid_ratios[i] / ratio_sma_i) - 1) * 100
                if mansfield_rs >= 0 and prev_mrs < 0:
                    rs_zero_cross = "bullish_crossover"
                    break
                elif mansfield_rs < 0 and prev_mrs >= 0:
                    rs_zero_cross = "bearish_crossover"
                    break

    # Score
    is_rising = rs_direction == "rising"
    is_falling = rs_direction == "falling"

    if mansfield_rs >= 20 and is_rising:
        score = 100
    elif mansfield_rs >= 10 and is_rising:
        score = 90
    elif mansfield_rs >= 5 and is_rising:
        score = 80
    elif mansfield_rs >= 0 and is_rising:
        score = 70
    elif mansfield_rs >= 0 and not is_rising:
        score = 60
    elif abs(mansfield_rs) < 2:
        score = 50
    elif mansfield_rs < 0 and is_rising:
        score = 40
    elif mansfield_rs < -10:
        score = 20
    elif mansfield_rs < -20:
        score = 0
    elif mansfield_rs < 0 and is_falling:
        score = 30
    else:
        score = 50

    # Detail string
    direction_symbol = "↑" if is_rising else ("↓" if is_falling else "→")
    detail = (
        f"Mansfield RS: {mansfield_rs:+.1f}% {direction_symbol} "
        f"({'outperforming' if mansfield_rs >= 0 else 'underperforming'} index, "
        f"momentum {rs_momentum:+.1f}%)"
    )

    if rs_zero_cross:
        cross_label = "Bullish zero-line crossover ↑" if rs_zero_cross == "bullish_crossover" else "Bearish zero-line crossover ↓"
        detail += f" | {cross_label}"

    return {
        "score": score,
        "mansfield_rs": round(mansfield_rs, 2),
        "rs_line_direction": rs_direction,
        "rs_momentum": round(rs_momentum, 2),
        "rs_zero_cross": rs_zero_cross,
        "rs_ratio_current": round(rs_ratio_current, 6),
        "rs_ratio_sma": round(rs_ratio_sma, 6),
        "sma_period_used": sma_period,
        "detail": detail,
        "error": None,
    }


def _empty_result(error: str) -> dict:
    """Return a zero-score result for error paths."""
    return {
        "score": 0,
        "mansfield_rs": None,
        "rs_line_direction": None,
        "rs_momentum": None,
        "rs_zero_cross": None,
        "rs_ratio_current": None,
        "rs_ratio_sma": None,
        "sma_period_used": None,
        "detail": error,
        "error": error,
    }
