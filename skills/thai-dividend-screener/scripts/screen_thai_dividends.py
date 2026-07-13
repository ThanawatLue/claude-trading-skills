#!/usr/bin/env python3
"""
Thai Dividend Screener — high-yield + uptrend SET candidates via TradingView.

Filters:
  - Dividend yield ≥ 3%
  - Market cap ≥ 5B THB
  - P/E 4-25 (avoid bubbles and loss-makers)
  - Price > SMA200 (long-term uptrend confirms not a value trap)

Scoring (0-100 composite):
  40% yield · 20% valuation · 20% trend health · 20% pullback opportunity

Usage:
    python3 screen_thai_dividends.py --output-dir reports/ --min-yield 3
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from scripts.lib.tv_client import (
    get_thai_stocks,
    filter_common_stocks,
    clean_for_json,
    is_available as tv_available,
)

MIN_AVG_TURNOVER_THB = 10_000_000


def _safe(v) -> float:
    try:
        n = float(v) if v is not None else 0.0
        return 0.0 if n != n else n
    except (TypeError, ValueError):
        return 0.0


def score_stock(
    s: dict,
    min_yield: float,
    min_mcap: float,
    min_turnover: float = MIN_AVG_TURNOVER_THB,
) -> tuple[bool, float, dict]:
    yield_ = _safe(s.get("dividend_yield"))
    mcap = _safe(s.get("marketCap"))
    avg_turnover = _safe(s.get("avg_turnover"))
    pe = _safe(s.get("pe_ratio"))
    price = _safe(s.get("price"))
    if avg_turnover <= 0:
        avg_turnover = price * _safe(s.get("avgVolume"))
    sma200 = _safe(s.get("sma200"))
    rsi = _safe(s.get("rsi"))
    py = _safe(s.get("perf_y"))

    # Hard filters
    if yield_ < min_yield:
        return False, 0.0, {}
    if mcap < min_mcap:
        return False, 0.0, {}
    if avg_turnover < min_turnover:
        return False, 0.0, {}
    if not (4 <= pe <= 25):
        return False, 0.0, {}
    if price <= 0 or sma200 <= 0 or price < sma200:
        return False, 0.0, {}

    # Yield score (capped to penalize "yield trap" — anything > 12% suspicious)
    capped_yield = min(yield_, 12)
    # Linear ramp from min_yield (e.g., 3%) to 12% yield
    if 12 <= min_yield: # Guard against invalid min_yield which would cause division by zero or negative range
        yield_score = 0.0 # No score if min_yield is too high
    else:
        yield_score = ((capped_yield - min_yield) / (12 - min_yield)) * 100
    yield_score = max(0, min(100, yield_score))

    # Valuation score (P/E 8-15 sweet spot; lower = better but extreme low is suspicious)
    if 8 <= pe <= 15:
        val_score = 100
    elif pe < 8:
        val_score = 70 + (pe - 4) * 7.5  # P/E 4 → 70, P/E 8 → 100
    else:
        val_score = max(0, 100 - (pe - 15) * 10)  # P/E 15 → 100, P/E 25 → 0

    # Trend score (positive 1Y + above SMA200)
    sma200_premium = ((price - sma200) / sma200) * 100
    trend_score = min(50, max(0, py)) + min(50, max(0, sma200_premium * 2))

    # Pullback opportunity (RSI 35-55 = best entry; >65 = extended)
    if 35 <= rsi <= 55:
        pullback_score = 100
    elif rsi < 35:
        pullback_score = max(0, 100 - (35 - rsi) * 5)  # too oversold = caution
    elif rsi <= 65:
        pullback_score = 100 - (rsi - 55) * 5
    else:
        pullback_score = max(0, 50 - (rsi - 65) * 3)

    composite = round(
        yield_score * 0.40
        + val_score * 0.20
        + trend_score * 0.20
        + pullback_score * 0.20,
        2,
    )

    metrics = {
        "yield_score": round(yield_score, 1),
        "valuation_score": round(val_score, 1),
        "trend_score": round(trend_score, 1),
        "pullback_score": round(pullback_score, 1),
        "sma200_premium_pct": round(sma200_premium, 2),
        "avg_turnover": round(avg_turnover, 2),
    }
    return True, composite, metrics


def grade(score: float) -> str:
    if score >= 75:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 45:
        return "Fair"
    return "Avoid"


def to_markdown(rows: list[dict], universe_size: int, ts: str) -> str:
    lines = [
        "# Thai Dividend Screener",
        f"**Generated:** {ts}  |  **Universe:** {universe_size} stocks  |  **Source:** TradingView",
        "",
        "## Methodology",
        "",
        "Hard filters: Yield ≥ 3% · MCap ≥ 5B THB · P/E 4-25 · Price > SMA200",
        "",
        "Score = 40% Yield · 20% Valuation · 20% Trend · 20% Pullback",
        "",
        f"## Results — {len(rows)} candidates",
        "",
        "| Rank | Symbol | Sector | Price | Yield | P/E | 1Y% | RSI | Score | Grade |",
        "|------|--------|--------|-------|-------|-----|-----|-----|-------|-------|",
    ]
    for i, r in enumerate(rows[:50], 1):
        lines.append(
            f"| {i} | {r['symbol']} | {r['sector'][:20]} | {r['price']:.2f} | "
            f"{r['dividend_yield']:.2f}% | {r['pe_ratio']:.1f} | "
            f"{r.get('perf_y') or 0:+.1f}% | {r.get('rsi') or 0:.0f} | "
            f"{r['score']:.1f} | {r['grade']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(description="Thai dividend screener (TV-only)")
    parser.add_argument("--output-dir", default="reports/")
    parser.add_argument("--min-yield", type=float, default=3.0,
                        help="Min dividend yield pct (default: 3.0)")
    parser.add_argument("--min-mcap", type=float, default=5e9,
                        help="Min market cap THB (default: 5B)")
    parser.add_argument(
        "--min-turnover",
        type=float,
        default=MIN_AVG_TURNOVER_THB,
        help="Minimum average traded value in THB (default: 10M)",
    )
    parser.add_argument("--top", type=int, default=30, help="Top N to keep (default: 30)")
    args = parser.parse_args()

    if not tv_available():
        print("ERROR: tradingview-screener not installed.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Thai Dividend Screener")
    print("=" * 60)
    print(f"Filters: yield ≥ {args.min_yield}% · mcap ≥ {args.min_mcap/1e9:.1f}B THB · P/E 4-25 · above SMA200")
    print("Fetching SET universe...", end=" ", flush=True)
    stocks = filter_common_stocks(get_thai_stocks(limit=1500))
    print(f"OK ({len(stocks)} stocks)")

    print("Scoring...", end=" ", flush=True)
    results = []
    for s in stocks:
        ok, score, metrics = score_stock(s, args.min_yield, args.min_mcap, args.min_turnover)
        if not ok:
            continue
        results.append({
            "symbol": s["symbol"],
            "name": s.get("name", s["symbol"]),
            "sector": s.get("sector", "Unknown"),
            "price": _safe(s.get("price")),
            "marketCap": _safe(s.get("marketCap")),
            "avg_turnover": _safe(s.get("avg_turnover")),
            "liquidity_score": _safe(s.get("liquidity_score")),
            "dividend_yield": _safe(s.get("dividend_yield")),
            "pe_ratio": _safe(s.get("pe_ratio")),
            "rsi": _safe(s.get("rsi")),
            "sma50": _safe(s.get("sma50")),
            "sma200": _safe(s.get("sma200")),
            "perf_1m": _safe(s.get("perf_1m")),
            "perf_y": _safe(s.get("perf_y")),
            "score": score,
            "grade": grade(score),
            "score_breakdown": metrics,
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[: args.top]
    print(f"OK ({len(results)} candidates)")

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.join(args.output_dir, f"thai_dividends_{ts}")

    payload = {
        "generated": ts,
        "market": "TH",
        "universe_size": len(stocks),
        "filters": {
            "min_yield_pct": args.min_yield,
            "min_market_cap": args.min_mcap,
            "min_avg_turnover": args.min_turnover,
            "pe_range": [4, 25],
            "trend_filter": "price > SMA200",
        },
        "candidates": results,
        "metadata": {"market": "TH", "source": "tradingview"},
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(clean_for_json(payload), f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(results, len(stocks), ts))

    print(f"\nTop 5:")
    for r in results[:5]:
        print(f"  {r['symbol']:12s} yield={r['dividend_yield']:5.2f}% PE={r['pe_ratio']:5.1f} score={r['score']:.1f} ({r['grade']})")
    print(f"\nReports:")
    print(f"  {base}.json")
    print(f"  {base}.md")


if __name__ == "__main__":
    main()
