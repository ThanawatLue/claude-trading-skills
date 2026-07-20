#!/usr/bin/env python3
"""
US Watchlist Builder — 4 auto-curated buckets from the US market.

Buckets:
  GROWTH         — Stage 2 leaders (above SMA50/200 + 3M perf > 10%)
  VALUE          — P/E 5-15, yield ≥ 2.5%, uptrend intact
  MOMENTUM       — RSI 60-78, vol > 1.5x avg, near 52w high
  MEAN_REVERSION — RSI 28-40 pullback to SMA50 within larger uptrend

Each bucket gets its own composite score, sorted internally.

Output: us_watchlists_<timestamp>.json + .md

Usage:
    python3 build_us_watchlists.py --output-dir reports/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path for importing scripts.lib.tv_client
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.lib.tv_client import (
    get_us_stocks,
    clean_for_json,
    is_available as tv_available,
)

MIN_AVG_TURNOVER_USD = 2_000_000

GROWTH_MIN_PRICE = 5.0
GROWTH_MIN_SMA50 = 0
GROWTH_MIN_SMA200 = 0
GROWTH_MIN_PERF_3M = 10
GROWTH_MIN_PERF_1M = 0
GROWTH_RSI_MIN = 50
GROWTH_RSI_MAX = 75
GROWTH_MIN_MARKET_CAP = 1_000_000_000

VALUE_MIN_PRICE = 5.0
VALUE_MIN_SMA200 = 0
VALUE_MIN_PE_RATIO = 5
VALUE_MAX_PE_RATIO = 15
VALUE_MIN_DIVIDEND_YIELD = 2.5
VALUE_MIN_PERF_Y = 0
VALUE_MIN_MARKET_CAP = 1_000_000_000

MOMENTUM_MIN_PRICE = 5.0
MOMENTUM_MIN_HIGH52 = 0
MOMENTUM_RSI_MIN = 60
MOMENTUM_RSI_MAX = 78
MOMENTUM_MIN_PERF_1M = 5
MOMENTUM_MIN_AVG_VOLUME = 1
MOMENTUM_VOLUME_RATIO = 1.5
MOMENTUM_MAX_DIST_FROM_HIGH52 = 0.08

MEAN_REVERSION_MIN_PRICE = 5.0
MEAN_REVERSION_MIN_SMA50 = 0
MEAN_REVERSION_MIN_SMA200 = 0
MEAN_REVERSION_RSI_MIN = 28
MEAN_REVERSION_RSI_MAX = 40
MEAN_REVERSION_MIN_PERF_Y = 0
MEAN_REVERSION_MAX_SMA50_DIST = 0.08

WATCHLIST_CRITERIA = {
    "growth": "Price above SMA50/200, 3M return ≥ 10%, RSI 50-75, market cap ≥ $1B",
    "value": "P/E 5-15, dividend yield ≥ 2.5%, positive 1Y return, price above SMA200",
    "momentum": "RSI 60-78, 1M return ≥ 5%, volume ≥ 1.5x average, near 52-week high",
    "mean_reversion": "RSI 28-40, positive 1Y return, price above SMA200, near SMA50",
}


def _safe_num(v):
    """Coerce None/NaN to 0 for arithmetic."""
    try:
        n = float(v) if v is not None else 0.0
        return 0.0 if n != n else n
    except (TypeError, ValueError):
        return 0.0


def has_liquidity(s: dict, min_avg_turnover: float | None = None) -> bool:
    """Return True when average traded value in USD is high enough."""
    if min_avg_turnover is None:
        min_avg_turnover = MIN_AVG_TURNOVER_USD
    avg_turnover = _safe_num(s.get("avg_turnover"))
    if avg_turnover <= 0:
        avg_turnover = _safe_num(s.get("price")) * _safe_num(s.get("avgVolume"))
    return avg_turnover >= min_avg_turnover


def in_growth(s: dict) -> tuple[bool, float]:
    price = _safe_num(s.get("price"))
    sma50 = _safe_num(s.get("sma50"))
    sma200 = _safe_num(s.get("sma200"))
    p1m = _safe_num(s.get("perf_1m"))
    p3m = _safe_num(s.get("perf_3m"))
    rsi = _safe_num(s.get("rsi"))
    mcap = _safe_num(s.get("marketCap"))

    if price < GROWTH_MIN_PRICE or sma50 <= 0 or sma200 <= 0:
        return False, 0.0
    if price < sma50 or price < sma200:
        return False, 0.0
    if p3m < GROWTH_MIN_PERF_3M:
        return False, 0.0
    if p1m <= GROWTH_MIN_PERF_1M:
        return False, 0.0
    if not (GROWTH_RSI_MIN <= rsi <= GROWTH_RSI_MAX):
        return False, 0.0
    if mcap < GROWTH_MIN_MARKET_CAP:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0

    score = min(100, p3m * 1.5) * 0.4 + min(100, p1m * 4) * 0.3 + (100 - abs(rsi - 62) * 4) * 0.3
    return True, round(max(0, score), 2)


def in_value(s: dict) -> tuple[bool, float]:
    price = _safe_num(s.get("price"))
    sma200 = _safe_num(s.get("sma200"))
    pe = _safe_num(s.get("pe_ratio"))
    yield_ = _safe_num(s.get("dividend_yield"))
    py = _safe_num(s.get("perf_y"))
    mcap = _safe_num(s.get("marketCap"))

    if price < VALUE_MIN_PRICE or sma200 <= 0 or price < sma200:
        return False, 0.0
    if not (VALUE_MIN_PE_RATIO <= pe <= VALUE_MAX_PE_RATIO):
        return False, 0.0
    if yield_ < VALUE_MIN_DIVIDEND_YIELD:
        return False, 0.0
    if py <= VALUE_MIN_PERF_Y:
        return False, 0.0
    if mcap < VALUE_MIN_MARKET_CAP:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0

    pe_score = (VALUE_MAX_PE_RATIO - pe) * 10
    yield_score = min(100, yield_ * 10)
    trend_score = min(100, py * 2)
    score = pe_score * 0.4 + yield_score * 0.4 + trend_score * 0.2
    return True, round(max(0, score), 2)


def in_momentum(s: dict) -> tuple[bool, float]:
    price = _safe_num(s.get("price"))
    high52 = _safe_num(s.get("yearHigh"))
    avg_vol = _safe_num(s.get("avgVolume"))
    vol = _safe_num(s.get("volume"))
    rsi = _safe_num(s.get("rsi"))
    p1m = _safe_num(s.get("perf_1m"))

    if price < MOMENTUM_MIN_PRICE or high52 <= 0:
        return False, 0.0
    if not (MOMENTUM_RSI_MIN <= rsi <= MOMENTUM_RSI_MAX):
        return False, 0.0
    if p1m < MOMENTUM_MIN_PERF_1M:
        return False, 0.0
    if avg_vol < 1 or vol / avg_vol < MOMENTUM_VOLUME_RATIO:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0
    if (high52 - price) / high52 > MOMENTUM_MAX_DIST_FROM_HIGH52:
        return False, 0.0

    proximity = (1 - (high52 - price) / high52) * 100
    vol_score = min(100, (vol / avg_vol - 1.5) * 50)
    rsi_score = 100 - abs(rsi - 67) * 5
    score = proximity * 0.4 + vol_score * 0.3 + rsi_score * 0.3
    return True, round(max(0, score), 2)


def in_mean_reversion(s: dict) -> tuple[bool, float]:
    price = _safe_num(s.get("price"))
    sma50 = _safe_num(s.get("sma50"))
    sma200 = _safe_num(s.get("sma200"))
    rsi = _safe_num(s.get("rsi"))
    py = _safe_num(s.get("perf_y"))

    if price < MEAN_REVERSION_MIN_PRICE or sma50 <= 0 or sma200 <= 0:
        return False, 0.0
    if price < sma200:
        return False, 0.0
    if not (MEAN_REVERSION_RSI_MIN <= rsi <= MEAN_REVERSION_RSI_MAX):
        return False, 0.0
    if py <= MEAN_REVERSION_MIN_PERF_Y:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0

    dist_sma50 = (price - sma50) / sma50
    if abs(dist_sma50) > MEAN_REVERSION_MAX_SMA50_DIST:
        return False, 0.0

    rsi_score = (MEAN_REVERSION_RSI_MAX - rsi) * 8
    dist_score = (1 - abs(dist_sma50) / MEAN_REVERSION_MAX_SMA50_DIST) * 100
    trend_score = min(100, py * 2)
    score = rsi_score * 0.4 + dist_score * 0.4 + trend_score * 0.2
    return True, round(max(0, score), 2)


def serialize_candidate(s: dict) -> dict:
    """Keep the fields required by the dashboard and downstream consumers."""
    return {
        "symbol": s.get("symbol", ""),
        "name": s.get("name", ""),
        "price": s.get("price") or 0,
        "sector": s.get("sector") or "Unknown",
        "rsi": s.get("rsi"),
        "perf_1m": s.get("perf_1m"),
        "perf_3m": s.get("perf_3m"),
        "perf_y": s.get("perf_y"),
        "avg_turnover": s.get("avg_turnover"),
        "score": s.get("score", 0),
    }


def to_markdown(buckets: dict[str, list[dict]], min_turnover: float, ts: str) -> str:
    lines = [
        "# US Watchlist Report",
        f"**Generated:** {ts}  |  **Market:** US  |  **Liquidity Floor:** ${min_turnover:,.2f}",
        "",
    ]
    emojis = {"growth": "🚀 Growth", "value": "💰 Value", "momentum": "🔥 Momentum", "mean_reversion": "🔄 Mean-Reversion"}
    for k, name in emojis.items():
        list_ = buckets.get(k, [])
        lines += [f"## {name} ({len(list_)} candidates)", ""]
        if not list_:
            lines.append("No candidates found meeting the filters today.")
            lines.append("")
            continue
        lines += ["| Ticker | Company | Price | Sector | Score |", "|--------|---------|-------|--------|-------|"]
        for s in list_[:15]:
            lines.append(
                f"| **{s['symbol']}** | {s['name'][:24]} | ${s['price']:.2f} | "
                f"{s['sector']} | **{s['score']:.1f}** |"
            )
        lines.append("")
    return "\n".join(lines)


def main():
    global MIN_AVG_TURNOVER_USD
    parser = argparse.ArgumentParser(description="Build US watchlists via TradingView")
    parser.add_argument("--output-dir", default="reports/", help="Output directory")
    parser.add_argument("--top", type=int, default=30, help="Max candidates per bucket")
    parser.add_argument(
        "--min-turnover",
        type=float,
        default=MIN_AVG_TURNOVER_USD,
        help=f"Minimum average turnover in USD (default: {MIN_AVG_TURNOVER_USD})",
    )
    args = parser.parse_args()

    MIN_AVG_TURNOVER_USD = args.min_turnover

    if not tv_available():
        print("ERROR: tradingview-screener not installed.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("US Watchlist Builder (TradingView)")
    print("=" * 60)
    print("Fetching US stocks from TradingView...", end=" ", flush=True)
    stocks = get_us_stocks(limit=4000)
    print(f"OK ({len(stocks)} stocks)")

    buckets = {"growth": [], "value": [], "momentum": [], "mean_reversion": []}
    for s in stocks:
        # Growth
        ok, score = in_growth(s)
        if ok:
            c = s.copy()
            c["score"] = score
            buckets["growth"].append(c)

        # Value
        ok, score = in_value(s)
        if ok:
            c = s.copy()
            c["score"] = score
            buckets["value"].append(c)

        # Momentum
        ok, score = in_momentum(s)
        if ok:
            c = s.copy()
            c["score"] = score
            buckets["momentum"].append(c)

        # Mean-Reversion
        ok, score = in_mean_reversion(s)
        if ok:
            c = s.copy()
            c["score"] = score
            buckets["mean_reversion"].append(c)

    # Sort each bucket
    for k in buckets:
        buckets[k].sort(key=lambda x: x["score"], reverse=True)
        buckets[k] = buckets[k][:args.top]

    print(f"\nBucket Results (Top {args.top}):")
    print(f"  Growth:         {len(buckets['growth'])} stocks")
    print(f"  Value:          {len(buckets['value'])} stocks")
    print(f"  Momentum:       {len(buckets['momentum'])} stocks")
    print(f"  Mean-Reversion: {len(buckets['mean_reversion'])} stocks")

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.join(args.output_dir, f"us_watchlists_{ts}")

    payload = {
        "generated": ts,
        "market": "US",
        "universe_size": len(stocks),
        "min_avg_turnover": MIN_AVG_TURNOVER_USD,
        "top_per_bucket": args.top,
        "criteria": WATCHLIST_CRITERIA,
        "buckets": {
            k: [serialize_candidate(s) for s in v]
            for k, v in buckets.items()
        },
        "metadata": {"market": "US", "source": "tradingview"},
    }

    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(clean_for_json(payload), f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(buckets, MIN_AVG_TURNOVER_USD, ts))

    print(f"\nReports:")
    print(f"  {base}.json")
    print(f"  {base}.md")


if __name__ == "__main__":
    main()
