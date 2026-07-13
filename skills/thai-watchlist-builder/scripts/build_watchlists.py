#!/usr/bin/env python3
# CRITICAL NOTICE FOR SELF-IMPROVEMENT AGENTS:
# This script is executed directly as a standalone subprocess by the dashboard (using python build_watchlists.py).
# It runs as __main__ and has no known parent package.
# Therefore, you MUST NOT use relative imports (e.g., from . import x, from .constants import y).
# Keep this file completely self-contained. Any constants or helpers must be defined directly in this file
# or loaded via absolute imports.

"""
Thai Watchlist Builder — 4 auto-curated buckets from the SET universe.

Buckets:
  GROWTH       — Stage 2 leaders (above SMA50/200 + 3M perf > 10%)
  VALUE        — P/E 5-15, yield ≥ 3%, uptrend intact
  MOMENTUM     — RSI 60-78, vol > 1.5x avg, near 52w high
  MEAN_REVERSION — RSI 28-40 pullback to SMA50 within larger uptrend

Each bucket gets its own composite score, sorted internally.

Output: thai_watchlists_<timestamp>.json + .md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from tv_client import (
    get_thai_stocks,
    filter_common_stocks,
    clean_for_json,
    is_available as tv_available,
)

MIN_AVG_TURNOVER_THB = 20_000_000

GROWTH_MIN_PRICE = 3
GROWTH_MIN_SMA50 = 0
GROWTH_MIN_SMA200 = 0
GROWTH_MIN_PERF_3M = 10
GROWTH_MIN_PERF_1M = 0
GROWTH_RSI_MIN = 50
GROWTH_RSI_MAX = 75
GROWTH_MIN_MARKET_CAP = 5_000_000_000

VALUE_MIN_PRICE = 3
VALUE_MIN_SMA200 = 0
VALUE_MIN_PE_RATIO = 5
VALUE_MAX_PE_RATIO = 15
VALUE_MIN_DIVIDEND_YIELD = 3
VALUE_MIN_PERF_Y = 0
VALUE_MIN_MARKET_CAP = 5_000_000_000

MOMENTUM_MIN_PRICE = 3
MOMENTUM_MIN_HIGH52 = 0
MOMENTUM_RSI_MIN = 60
MOMENTUM_RSI_MAX = 78
MOMENTUM_MIN_PERF_1M = 5
MOMENTUM_MIN_AVG_VOLUME = 1
MOMENTUM_VOLUME_RATIO = 1.5
MOMENTUM_MAX_DIST_FROM_HIGH52 = 0.08

MEAN_REVERSION_MIN_PRICE = 3
MEAN_REVERSION_MIN_SMA50 = 0
MEAN_REVERSION_MIN_SMA200 = 0
MEAN_REVERSION_RSI_MIN = 28
MEAN_REVERSION_RSI_MAX = 40
MEAN_REVERSION_MIN_PERF_Y = 0
MEAN_REVERSION_MAX_SMA50_DIST = 0.08



# ---------------------------------------------------------------------------
# Bucket filters and scorers
# ---------------------------------------------------------------------------

def _safe_num(v):
    """Coerce None/NaN to 0 for arithmetic."""
    try:
        n = float(v) if v is not None else 0.0
        return 0.0 if n != n else n  # NaN check
    except (TypeError, ValueError):
        return 0.0


def has_liquidity(s: dict, min_avg_turnover: float = MIN_AVG_TURNOVER_THB) -> bool:
    """Return True when average traded value is high enough for Thai swing use."""
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

    if price < 3 or sma50 <= 0 or sma200 <= 0:
        return False, 0.0
    if price < sma50 or price < sma200:
        return False, 0.0
    if p3m < 10:
        return False, 0.0
    if p1m <= 0:
        return False, 0.0
    if not (50 <= rsi <= 75):
        return False, 0.0
    if mcap < 5_000_000_000:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0

    # Score: momentum + healthy RSI
    score = min(100, p3m * 1.5) * 0.4 + min(100, p1m * 4) * 0.3 + (100 - abs(rsi - 62) * 4) * 0.3
    return True, round(max(0, score), 2)


def in_value(s: dict) -> tuple[bool, float]:
    price = _safe_num(s.get("price"))
    sma200 = _safe_num(s.get("sma200"))
    pe = _safe_num(s.get("pe_ratio"))
    yield_ = _safe_num(s.get("dividend_yield"))
    py = _safe_num(s.get("perf_y"))
    mcap = _safe_num(s.get("marketCap"))

    if price < 3 or sma200 <= 0 or price < sma200:
        return False, 0.0
    if not (5 <= pe <= 15):
        return False, 0.0
    if yield_ < 3:
        return False, 0.0
    if py <= 0:
        return False, 0.0
    if mcap < 5_000_000_000:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0

    # Score: cheaper + higher yield + steady uptrend
    pe_score = (15 - pe) * 6  # P/E=5 → 60, P/E=15 → 0
    yield_score = min(100, yield_ * 8)
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

    if price < 3 or high52 <= 0:
        return False, 0.0
    if not (60 <= rsi <= 78):
        return False, 0.0
    if p1m < 5:
        return False, 0.0
    if avg_vol < 1 or vol / avg_vol < 1.5:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0
    if (high52 - price) / high52 > 0.08:
        return False, 0.0

    # Score: nearest to high + high RSI in sweet spot + volume
    proximity = (1 - (high52 - price) / high52) * 100
    vol_score = min(100, (vol / avg_vol - 1.5) * 50)
    rsi_score = 100 - abs(rsi - 67) * 5
    score = proximity * 0.4 + vol_score * 0.3 + max(0, rsi_score) * 0.3
    return True, round(max(0, score), 2)


def in_mean_reversion(s: dict) -> tuple[bool, float]:
    price = _safe_num(s.get("price"))
    sma50 = _safe_num(s.get("sma50"))
    sma200 = _safe_num(s.get("sma200"))
    rsi = _safe_num(s.get("rsi"))
    py = _safe_num(s.get("perf_y"))

    if price < 3 or sma50 <= 0 or sma200 <= 0:
        return False, 0.0
    if price < sma200:
        return False, 0.0
    if not (28 <= rsi <= 40):
        return False, 0.0
    if py <= 0:
        return False, 0.0
    if not has_liquidity(s):
        return False, 0.0
    sma50_dist = abs(price - sma50) / sma50
    if sma50_dist > 0.08:
        return False, 0.0

    # Score: deeper oversold (within band) + closer to SMA50 + steady uptrend
    rsi_score = (40 - rsi) * 7  # RSI=28 → 84, RSI=40 → 0
    sma_score = (1 - sma50_dist / 0.08) * 100
    trend_score = min(100, py * 2)
    score = rsi_score * 0.4 + sma_score * 0.3 + trend_score * 0.3
    return True, round(max(0, score), 2)


_BUCKETS = [
    ("growth", in_growth),
    ("value", in_value),
    ("momentum", in_momentum),
    ("mean_reversion", in_mean_reversion),
]


def _to_row(s: dict, score: float) -> dict:
    return {
        "symbol": s["symbol"],
        "name": s.get("name", s["symbol"]),
        "sector": s.get("sector", "Unknown"),
        "price": s.get("price"),
        "marketCap": s.get("marketCap"),
        "avg_turnover": s.get("avg_turnover"),
        "liquidity_score": s.get("liquidity_score"),
        "rsi": s.get("rsi"),
        "sma50": s.get("sma50"),
        "sma200": s.get("sma200"),
        "perf_1m": s.get("perf_1m"),
        "perf_3m": s.get("perf_3m"),
        "perf_y": s.get("perf_y"),
        "dividend_yield": s.get("dividend_yield"),
        "pe_ratio": s.get("pe_ratio"),
        "score": score,
    }


def build_watchlists(stocks: list[dict], top_n: int = 30) -> dict:
    buckets: dict = {}
    for name, predicate in _BUCKETS:
        matches = []
        for s in stocks:
            ok, score = predicate(s)
            if ok:
                matches.append(_to_row(s, score))
        matches.sort(key=lambda r: r["score"], reverse=True)
        buckets[name] = matches[:top_n]
    return buckets


def to_markdown(buckets: dict, universe_size: int, ts: str, top_n: int) -> str:
    lines = [
        "# Thai Watchlist Builder",
        f"**Generated:** {ts}  |  **Universe:** {universe_size} SET stocks  |  **Source:** TradingView",
        "",
        "## Summary",
        "",
        "| Bucket | Candidates | Avg Score |",
        "|--------|------------|-----------|",
    ]
    for name in ["growth", "value", "momentum", "mean_reversion"]:
        b = buckets.get(name, [])
        avg = round(sum(r["score"] for r in b) / len(b), 1) if b else 0
        lines.append(f"| **{name.upper()}** | {len(b)} | {avg} |")
    lines.append("")

    titles = {
        "growth": "GROWTH - Stage 2 Leaders",
        "value": "VALUE - Cheap with Fundamentals",
        "momentum": "MOMENTUM - Hot Stocks",
        "mean_reversion": "MEAN-REVERSION - Oversold Bounces",
    }

    for name, title in titles.items():
        b = buckets.get(name, [])
        lines += [f"## {title}", ""]
        if not b:
            lines += ["_No candidates passed the filters._", ""]
            continue
        lines += [
            "| Rank | Symbol | Sector | Price | RSI | 1M% | 3M% | Score |",
            "|------|--------|--------|-------|-----|-----|-----|-------|",
        ]
        for i, r in enumerate(b[: min(top_n, 15)], 1):
            lines.append(
                f"| {i} | {r['symbol']} | {r['sector'][:25]} | "
                f"{r['price']:.2f} | {r.get('rsi') or 0:.0f} | "
                f"{r.get('perf_1m') or 0:+.1f}% | {r.get('perf_3m') or 0:+.1f}% | "
                f"{r['score']:.1f} |"
            )
        lines.append("")

    return "\n".join(lines)


def main():


    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(description="Build 4 Thai watchlist buckets via TV")
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument("--top", type=int, default=30, help="Top N per bucket (default: 30)")
    parser.add_argument(
        "--min-turnover",
        type=float,
        default=MIN_AVG_TURNOVER_THB,
        help="Minimum average traded value in THB (default: 20M)",
    )
    args = parser.parse_args()

    if not tv_available():
        print("ERROR: tradingview-screener not installed.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Thai Watchlist Builder")
    print("=" * 60)
    print("Fetching SET universe...", end=" ", flush=True)
    stocks = filter_common_stocks(get_thai_stocks(limit=1500))
    stocks = [s for s in stocks if has_liquidity(s, args.min_turnover)]
    print(f"OK ({len(stocks)} stocks)")

    print("Building buckets...", end=" ", flush=True)
    buckets = build_watchlists(stocks, top_n=args.top)
    counts = {k: len(v) for k, v in buckets.items()}
    print("OK")

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.join(args.output_dir, f"thai_watchlists_{ts}")

    payload = {
        "generated": ts,
        "market": "TH",
        "universe_size": len(stocks),
        "top_per_bucket": args.top,
        "min_avg_turnover": args.min_turnover,
        "counts": counts,
        "criteria": {
            "growth": f"Above SMA50/200 · perf_3m≥{GROWTH_MIN_PERF_3M}% · perf_1m>{GROWTH_MIN_PERF_1M} · RSI {GROWTH_RSI_MIN}-{GROWTH_RSI_MAX} · mcap≥{GROWTH_MIN_MARKET_CAP/1_000_000_000}B THB · price≥{GROWTH_MIN_PRICE}฿",
            "value":  f"Above SMA200 · P/E {VALUE_MIN_PE_RATIO}-{VALUE_MAX_PE_RATIO} · yield≥{VALUE_MIN_DIVIDEND_YIELD}% · perf_y>{VALUE_MIN_PERF_Y} · mcap≥{VALUE_MIN_MARKET_CAP/1_000_000_000}B THB · price≥{VALUE_MIN_PRICE}฿",
            "momentum": f"RSI {MOMENTUM_RSI_MIN}-{MOMENTUM_RSI_MAX} · perf_1m≥{MOMENTUM_MIN_PERF_1M}% · vol≥{MOMENTUM_VOLUME_RATIO}×avg · within {MOMENTUM_MAX_DIST_FROM_HIGH52*100}% of 52w high · price≥{MOMENTUM_MIN_PRICE}฿",
            "mean_reversion": f"Above SMA200 · RSI {MEAN_REVERSION_RSI_MIN}-{MEAN_REVERSION_RSI_MAX} · perf_y>{MEAN_REVERSION_MIN_PERF_Y} · within {MEAN_REVERSION_MAX_SMA50_DIST*100}% of SMA50 · price≥{MEAN_REVERSION_MIN_PRICE}฿",
        },
        "buckets": buckets,
        "metadata": {"market": "TH", "source": "tradingview"},
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(clean_for_json(payload), f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(buckets, len(stocks), ts, args.top))

    print(f"\nBucket counts:")
    for k, n in counts.items():
        print(f"  {k.upper():16s} → {n} candidates")
    print(f"\nReports:")
    print(f"  {base}.json")
    print(f"  {base}.md")


if __name__ == "__main__":
    main()
