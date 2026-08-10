"""OHLCV pattern stats for Dual-Check (day bias + confluence).

Ported from dashboard/static/js/app.js calculatePatternStats confluence /
day-of-week logic so ranked candidates can gate server-side.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any, Literal

HoldStyle = Literal["overnight", "intraday"]

DAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

# Dual-Check thresholds (AGENTS.md Dual-Check Analysis Protocol)
OVERNIGHT_MIN_WIN_RATE = 55.0
INTRADAY_MIN_WIN_RATE = 50.0
MIN_BIAS_SAMPLES = 5
CONFLUENCE_MIN_NET = 1.0


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _f(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def normalize_bars(bars: Sequence[Mapping[str, Any]] | None) -> list[dict[str, float | date]]:
    """Return chronological bars with open/high/low/close/volume and date."""
    if not bars:
        return []
    out: list[dict[str, float | date]] = []
    for row in bars:
        if not isinstance(row, Mapping):
            continue
        d = _as_date(row.get("date") or row.get("time") or row.get("Date"))
        o = _f(row.get("open") if "open" in row else row.get("Open"))
        h = _f(row.get("high") if "high" in row else row.get("High"))
        low = _f(row.get("low") if "low" in row else row.get("Low"))
        c = _f(row.get("close") if "close" in row else row.get("Close"))
        vol = _f(row.get("volume") if "volume" in row else row.get("value") or row.get("Volume"))
        if d is None or o is None or h is None or low is None or c is None:
            continue
        out.append(
            {
                "date": d,
                "open": o,
                "high": h,
                "low": low,
                "close": c,
                "volume": vol or 0.0,
            }
        )
    out.sort(key=lambda item: item["date"])  # type: ignore[arg-type, return-value]
    return out


def _sma(closes: Sequence[float], end_idx: int, window: int) -> float | None:
    if end_idx + 1 < window:
        return None
    chunk = closes[end_idx - window + 1 : end_idx + 1]
    if len(chunk) < window:
        return None
    return sum(chunk) / window


def compute_day_bias(
    bars: Sequence[Mapping[str, Any]] | None,
    *,
    hold_style: HoldStyle = "overnight",
    as_of_index: int | None = None,
) -> dict[str, Any] | None:
    """Day-of-week bias for the weekday of the reference bar.

    overnight: close-to-close (prev close → close)
    intraday: open-to-close ((close - open) / open)
    """
    series = normalize_bars(bars)
    if len(series) < 2:
        return None
    idx = len(series) - 1 if as_of_index is None else as_of_index
    if idx < 1 or idx >= len(series):
        return None

    target_weekday = series[idx]["date"].weekday()  # type: ignore[union-attr]
    wins = 0
    total = 0
    ret_sum = 0.0

    start = 1 if hold_style == "overnight" else 0
    for i in range(start, idx + 1):
        bar = series[i]
        if bar["date"].weekday() != target_weekday:  # type: ignore[union-attr]
            continue
        if hold_style == "intraday":
            open_px = float(bar["open"])
            if open_px <= 0:
                continue
            ret = (float(bar["close"]) - open_px) / open_px * 100.0
        else:
            prev = float(series[i - 1]["close"])
            if prev <= 0:
                continue
            ret = (float(bar["close"]) - prev) / prev * 100.0
        total += 1
        ret_sum += ret
        if ret > 0:
            wins += 1

    if total < MIN_BIAS_SAMPLES:
        return {
            "day": DAY_NAMES[target_weekday],
            "hold_style": hold_style,
            "win_rate": round(wins / total * 100.0, 1) if total else None,
            "avg_return": round(ret_sum / total, 2) if total else None,
            "count": total,
            "metric": "close_to_close" if hold_style == "overnight" else "open_to_close",
            "insufficient_samples": True,
        }

    win_rate = wins / total * 100.0
    avg_return = ret_sum / total
    return {
        "day": DAY_NAMES[target_weekday],
        "hold_style": hold_style,
        "win_rate": round(win_rate, 1),
        "avg_return": round(avg_return, 2),
        "count": total,
        "metric": "close_to_close" if hold_style == "overnight" else "open_to_close",
        "insufficient_samples": False,
        "passes_threshold": (
            win_rate > OVERNIGHT_MIN_WIN_RATE
            if hold_style == "overnight"
            else win_rate > INTRADAY_MIN_WIN_RATE
        )
        and avg_return > 0,
    }


def compute_confluence(
    bars: Sequence[Mapping[str, Any]] | None,
    *,
    as_of_index: int | None = None,
) -> dict[str, Any] | None:
    """Weighted bull/bear confluence matching the chart tooltip scorer."""
    series = normalize_bars(bars)
    if len(series) < 30:
        return None
    idx = len(series) - 1 if as_of_index is None else as_of_index
    if idx < 20 or idx >= len(series):
        return None

    closes = [float(b["close"]) for b in series]
    opens = [float(b["open"]) for b in series]
    highs = [float(b["high"]) for b in series]
    lows = [float(b["low"]) for b in series]
    volumes = [float(b["volume"]) for b in series]

    sma50 = _sma(closes, idx, 50)
    sma200 = _sma(closes, idx, 200)
    vol20 = _sma(volumes, idx, 20)
    high20 = max(highs[idx - 19 : idx]) if idx >= 20 else None
    range10 = None
    if idx >= 9:
        range10 = sum(highs[i] - lows[i] for i in range(idx - 9, idx + 1)) / 10.0

    # Gap streak
    gap_streak = 0
    gap_dir = 0
    for i in range(idx, 0, -1):
        gap = opens[i] - closes[i - 1]
        if gap == 0:
            break
        g_dir = 1 if gap > 0 else -1
        if gap_streak == 0:
            gap_dir = g_dir
            gap_streak = 1
        elif g_dir == gap_dir:
            gap_streak += 1
        else:
            break

    # Color streak
    color_streak = 0
    color_dir = 0
    for i in range(idx, -1, -1):
        if closes[i] > opens[i]:
            c_dir = 1
        elif closes[i] < opens[i]:
            c_dir = -1
        else:
            break
        if color_streak == 0:
            color_dir = c_dir
            color_streak = 1
        elif c_dir == color_dir:
            color_streak += 1
        else:
            break

    is_pullback = bool(sma50 is not None and lows[idx] <= sma50 and closes[idx] >= sma50 * 0.99)
    is_breakout = bool(high20 is not None and closes[idx] > high20)
    is_vol_spike = bool(vol20 and volumes[idx] >= vol20 * 2.0)
    is_vol_dry = bool(vol20 and volumes[idx] < vol20 * 0.5)

    body = abs(closes[idx] - opens[idx])
    lower_wick = min(closes[idx], opens[idx]) - lows[idx]
    is_hammer_shape = lower_wick >= body * 2 and lower_wick > 0
    near_sma50 = sma50 is not None and abs(lows[idx] - sma50) / sma50 <= 0.02
    near_sma200 = sma200 is not None and abs(lows[idx] - sma200) / sma200 <= 0.02
    after_down = (
        idx >= 4
        and closes[idx - 1] < closes[idx - 2]
        and closes[idx - 2] < closes[idx - 3]
        and closes[idx - 3] < closes[idx - 4]
    )
    is_hammer = bool(is_hammer_shape and (near_sma50 or near_sma200 or after_down))

    bar_range = highs[idx] - lows[idx]
    close_pos = (closes[idx] - lows[idx]) / bar_range if bar_range > 0 else 0.0
    is_strong_close = bool(
        close_pos >= 0.75 and closes[idx] > opens[idx] and vol20 and volumes[idx] > vol20
    )
    is_wide_bull = bool(range10 and bar_range >= range10 * 1.5 and closes[idx] > opens[idx])
    is_wide_bear = bool(range10 and bar_range >= range10 * 1.5 and closes[idx] < opens[idx])
    is_above_sma200 = bool(sma200 is not None and closes[idx] > sma200)

    # Weekly 10-SMA bias (last day of week closes)
    weekly_closes: list[float] = []
    for i in range(0, idx + 1):
        d = series[i]["date"]
        assert isinstance(d, date)
        next_d = series[i + 1]["date"] if i + 1 <= idx else None
        is_last = next_d is None or (
            isinstance(next_d, date) and (next_d.weekday() < d.weekday() or (next_d - d).days > 4)
        )
        if is_last:
            weekly_closes.append(closes[i])
    is_weekly_bull = False
    if len(weekly_closes) >= 10:
        sma10 = sum(weekly_closes[-10:]) / 10.0
        is_weekly_bull = weekly_closes[-1] > sma10

    # RSI(14) + simple divergence flags
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, idx + 1):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    rsi = None
    if len(gains) >= 14:
        avg_gain = sum(gains[:14]) / 14.0
        avg_loss = sum(losses[:14]) / 14.0
        for i in range(14, len(gains)):
            avg_gain = (avg_gain * 13 + gains[i]) / 14.0
            avg_loss = (avg_loss * 13 + losses[i]) / 14.0
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

    is_rsi_bull_div = False
    is_rsi_bear_div = False
    # Lightweight divergence proxy: RSI vs 10-day price extreme
    if rsi is not None and idx >= 20:
        window = closes[idx - 20 : idx + 1]
        if closes[idx] <= min(window) and rsi < 45:
            # price near window low while RSI not extremely oversold → soft bull
            is_rsi_bull_div = rsi > 30
        if closes[idx] >= max(window) and rsi > 55:
            is_rsi_bear_div = rsi < 70

    bull = 0.0
    bear = 0.0
    if gap_streak > 0 and gap_dir == 1:
        bull += 1
    if gap_streak > 0 and gap_dir == -1:
        bear += 1
    if color_streak > 0 and color_dir == 1:
        bull += 1
    if color_streak > 0 and color_dir == -1:
        bear += 1
    if is_pullback:
        bull += 1.5
    if is_breakout:
        bull += 2
    if is_vol_spike:
        if closes[idx] > opens[idx]:
            bull += 1.5
        elif closes[idx] < opens[idx]:
            bear += 1.5
    if is_vol_dry:
        bull += 1
    if is_hammer:
        bull += 1.5
    if is_strong_close:
        bull += 1
    if is_wide_bull:
        bull += 1
    if is_wide_bear:
        bear += 1
    if is_weekly_bull:
        bull += 1
    if is_rsi_bull_div:
        bull += 2
    if is_rsi_bear_div:
        bear += 2
    if is_above_sma200:
        bull += 1
    else:
        bear += 1

    net = bull - bear
    if net >= 5:
        label = "Strong Bullish"
    elif net >= 1:
        label = "Bullish"
    elif net <= -5:
        label = "Strong Bearish"
    elif net <= -1:
        label = "Bearish"
    else:
        label = "Neutral"

    return {
        "bull_weight": round(bull, 1),
        "bear_weight": round(bear, 1),
        "net_score": round(net, 1),
        "label": label,
        "passes_threshold": net >= CONFLUENCE_MIN_NET,
        "flags": {
            "gap_streak": gap_streak,
            "gap_dir": gap_dir,
            "color_streak": color_streak,
            "color_dir": color_dir,
            "pullback": is_pullback,
            "breakout": is_breakout,
            "volume_spike": is_vol_spike,
            "volume_dry_up": is_vol_dry,
            "hammer": is_hammer,
            "strong_close": is_strong_close,
            "wide_range_bull": is_wide_bull,
            "wide_range_bear": is_wide_bear,
            "weekly_bull": is_weekly_bull,
            "rsi": round(rsi, 1) if rsi is not None else None,
            "above_sma200": is_above_sma200,
        },
    }


def evaluate_day_bias_gate(bias: Mapping[str, Any] | None) -> tuple[str, str, str | None]:
    """Return (status, detail, reject_code|None)."""
    if not bias:
        return "unavailable", "No OHLCV bars for day bias", None
    if bias.get("insufficient_samples"):
        return (
            "unavailable",
            f"Insufficient same-weekday samples ({bias.get('count') or 0})",
            None,
        )
    win = bias.get("win_rate")
    avg = bias.get("avg_return")
    day = bias.get("day") or "?"
    metric = bias.get("metric") or ""
    detail = f"{day} {metric} win={win}% avg={avg}%"
    if bias.get("passes_threshold"):
        return "pass", detail, None
    hold = bias.get("hold_style") or "overnight"
    min_wr = OVERNIGHT_MIN_WIN_RATE if hold == "overnight" else INTRADAY_MIN_WIN_RATE
    return "fail", f"{detail} (need win>{min_wr}% and avg>0)", "day_bias_weak"


def evaluate_confluence_gate(conf: Mapping[str, Any] | None) -> tuple[str, str, str | None]:
    if not conf:
        return "unavailable", "No OHLCV bars for confluence", None
    detail = (
        f"{conf.get('label')} net={conf.get('net_score')} "
        f"({conf.get('bull_weight')}B-{conf.get('bear_weight')}S)"
    )
    if conf.get("passes_threshold"):
        return "pass", detail, None
    return "fail", f"{detail} (need net>={CONFLUENCE_MIN_NET})", "confluence_weak"
