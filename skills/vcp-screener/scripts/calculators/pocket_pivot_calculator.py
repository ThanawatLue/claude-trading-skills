#!/usr/bin/env python3
"""
Pocket Pivot Calculator - Gil Morales / Chris Kacher Entry Signal

Detects "Pocket Pivot" buy signals within a VCP base structure.
A Pocket Pivot identifies institutional buying before a traditional breakout.

Definition (Gil Morales):
A Pocket Pivot occurs when:
1. Today's up-volume exceeds the LARGEST down-volume day in the prior 10 sessions
2. The stock closes up on the day
3. The stock is trading above its 50-day SMA (or rising 10-day SMA)
4. The stock is building a constructive base pattern

This is a "stealth" institutional buying signal — big money accumulating
before the obvious breakout over pivot. It allows earlier entry with
tighter stop losses.

Scoring:
- 100: Pocket Pivot confirmed + volume surge 2x+ max down-volume + above 50 SMA
-  85: Pocket Pivot confirmed + volume surge 1.5x max down-volume
-  70: Pocket Pivot confirmed (basic criteria met)
-  50: Near Pocket Pivot (volume close but not exceeding max down-volume)
-  30: Up day with above-average volume but not a true Pocket Pivot
-   0: No Pocket Pivot signal
"""

from typing import Optional


def calculate_pocket_pivot(
    historical_prices: list[dict],
    sma50: Optional[float] = None,
) -> dict:
    """
    Detect Pocket Pivot buy signal in recent price/volume data.

    Args:
        historical_prices: Daily OHLCV data (most recent first), need 15+ days
        sma50: Pre-calculated 50-day SMA. If None, calculated internally.

    Returns:
        Dict with score (0-100), is_pocket_pivot, volume details, error
    """
    if not historical_prices or len(historical_prices) < 15:
        return {
            "score": 0,
            "is_pocket_pivot": False,
            "volume_surge_ratio": None,
            "detail": "Insufficient data (need 15+ days)",
            "error": "Insufficient data",
        }

    closes = [float(d.get("close") or d.get("adjClose") or 0) for d in historical_prices]
    volumes = [d.get("volume", 0) for d in historical_prices]

    # Today's data (index 0 = most recent)
    today_close = closes[0]
    today_volume = volumes[0]
    yesterday_close = closes[1] if len(closes) > 1 else 0

    # Check if today is an up day
    is_up_day = today_close > yesterday_close
    if not is_up_day:
        return {
            "score": 0,
            "is_pocket_pivot": False,
            "volume_surge_ratio": None,
            "detail": "Not an up day",
            "error": None,
        }

    # Find the maximum down-volume in the prior 10 sessions (indices 1-10)
    max_down_volume = 0
    down_days_count = 0
    for i in range(1, min(11, len(closes))):
        if i + 1 < len(closes) and closes[i] < closes[i + 1]:
            # This was a down day
            max_down_volume = max(max_down_volume, volumes[i])
            down_days_count += 1

    if max_down_volume <= 0:
        # No down days in last 10 sessions — unusual, score as neutral
        return {
            "score": 30,
            "is_pocket_pivot": False,
            "volume_surge_ratio": None,
            "detail": "No down-volume days found in prior 10 sessions",
            "error": None,
        }

    # Calculate volume surge ratio
    volume_surge_ratio = today_volume / max_down_volume

    # Check if above 50-day SMA
    if sma50 is None and len(closes) >= 50:
        sma50 = sum(closes[:50]) / 50
    above_sma50 = today_close > sma50 if sma50 else False

    # Check if above rising 10-day SMA (alternative to 50-day)
    sma10 = sum(closes[:10]) / 10 if len(closes) >= 10 else None
    sma10_5d_ago = sum(closes[5:15]) / 10 if len(closes) >= 15 else None
    sma10_rising = (sma10 > sma10_5d_ago) if (sma10 and sma10_5d_ago) else False

    # Determine Pocket Pivot
    is_pocket_pivot = volume_surge_ratio >= 1.0 and (above_sma50 or sma10_rising)

    # Score
    if is_pocket_pivot and volume_surge_ratio >= 2.0 and above_sma50:
        score = 100
        detail = (
            f"Strong Pocket Pivot: volume {today_volume:,.0f} is "
            f"{volume_surge_ratio:.1f}x max down-volume {max_down_volume:,.0f}, "
            f"above 50-SMA"
        )
    elif is_pocket_pivot and volume_surge_ratio >= 1.5:
        score = 85
        detail = (
            f"Pocket Pivot confirmed: volume {today_volume:,.0f} is "
            f"{volume_surge_ratio:.1f}x max down-volume {max_down_volume:,.0f}"
        )
    elif is_pocket_pivot:
        score = 70
        detail = (
            f"Pocket Pivot: volume {today_volume:,.0f} exceeds "
            f"max down-volume {max_down_volume:,.0f}"
        )
    elif volume_surge_ratio >= 0.85:
        score = 50
        detail = (
            f"Near Pocket Pivot: volume {today_volume:,.0f} is "
            f"{volume_surge_ratio:.1f}x max down-volume (needs 1.0x+)"
        )
    elif is_up_day and today_volume > sum(volumes[:50]) / 50 if len(volumes) >= 50 else False:
        score = 30
        detail = "Up day with above-average volume, but not a Pocket Pivot"
    else:
        score = 0
        detail = "No Pocket Pivot signal"

    return {
        "score": score,
        "is_pocket_pivot": is_pocket_pivot,
        "volume_surge_ratio": round(volume_surge_ratio, 2),
        "max_down_volume_10d": int(max_down_volume),
        "today_volume": int(today_volume),
        "above_sma50": above_sma50,
        "sma10_rising": sma10_rising,
        "down_days_in_lookback": down_days_count,
        "detail": detail,
        "error": None,
    }
