#!/usr/bin/env python3
"""
US Dividend Screener — high-yield + uptrend candidates via TradingView.

Filters:
  - Dividend yield ≥ 3%
  - Market cap ≥ 1B USD
  - P/E 4-25 (avoid bubbles and loss-makers)
  - Price > SMA200 (long-term uptrend confirms not a value trap)

Scoring (0-100 composite):
  40% yield · 20% valuation · 20% trend health · 20% pullback opportunity

Usage:
    python3 screen_us_dividends.py --output-dir reports/ --min-yield 3
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
    min_turnover: float = MIN_AVG_TURNOVER_USD,
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
    if 12 <= min_yield:
        yield_score = 0.0
    else:
        yield_score = ((capped_yield - min_yield) / (12 - min_yield)) * 100
    yield_score = max(0, min(100, yield_score))

    # Valuation score (P/E 8-15 sweet spot; lower = better but extreme low is suspicious)
    if 8 <= pe <= 15:
        val_score = 100
    elif pe < 8:
        val_score = 70 + (pe - 4) * 7.5
    else:
        val_score = max(0, 100 - (pe - 15) * 10)

    # Trend score (positive 1Y + above SMA200)
    sma200_premium = ((price - sma200) / sma200) * 100
    trend_score = min(50, max(0, py)) + min(50, max(0, sma200_premium * 2))

    # Pullback opportunity (RSI 35-55 = best entry; >65 = extended)
    if 35 <= rsi <= 55:
        pullback_score = 100
    elif rsi < 35:
        pullback_score = max(0, 100 - (35 - rsi) * 5)
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


def to_markdown(rows: list[dict], universe_size: int, ts: str, min_yield: float) -> str:
    lines = [
        "# US Dividend Screener",
        f"**Generated:** {ts}  |  **Universe:** {universe_size} stocks  |  **Source:** TradingView",
        "",
        "## Methodology",
        "",
        f"Hard filters: Yield ≥ {min_yield}% · MCap ≥ $1B · P/E 4-25 · Price > SMA200",
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
            f"| {i} | **{r['symbol']}** | {r['sector']} | ${r['price']:.2f} | "
            f"{r['dividend_yield']:.2f}% | {r['pe_ratio']:.1f} | {r['perf_y']:+.1f}% | "
            f"{r['rsi']:.1f} | **{r['score']:.1f}** | **{r['grade']}** |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="US dividend stock screener (TV)")
    parser.add_argument("--output-dir", default="reports/", help="Output directory")
    parser.add_argument("--min-yield", type=float, default=3.0, help="Min dividend yield %%")
    parser.add_argument("--min-mcap", type=float, default=1_000_000_000, help="Min market cap (USD)")
    parser.add_argument("--min-turnover", type=float, default=MIN_AVG_TURNOVER_USD, help="Min avg turnover (USD)")
    parser.add_argument("--top", type=int, default=30, help="Max candidates in output")
    args = parser.parse_args()

    if not tv_available():
        print("ERROR: tradingview-screener not installed.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("US Dividend Stock Screener (TradingView)")
    print("=" * 60)
    print("Fetching US stocks from TradingView...", end=" ", flush=True)
    stocks = get_us_stocks(limit=4000)
    print(f"OK ({len(stocks)} stocks)")

    candidates = []
    for s in stocks:
        ok, score, metrics = score_stock(s, args.min_yield, args.min_mcap, args.min_turnover)
        if ok:
            c = s.copy()
            c["score"] = score
            c["grade"] = grade(score)
            c["scoring_details"] = metrics
            candidates.append(c)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = candidates[:args.top]

    print(f"\nScreener Results:")
    print(f"  Passed filters: {len(candidates)} / {len(stocks)} stocks")
    print(f"  Selecting top: {len(top_candidates)}")

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.join(args.output_dir, f"us_dividends_{ts}")

    payload = {
        "generated": ts,
        "market": "US",
        "universe_size": len(stocks),
        "min_yield": args.min_yield,
        "min_mcap": args.min_mcap,
        "min_turnover": args.min_turnover,
        "candidates": [
            {
                "symbol": c["symbol"],
                "name": c["name"],
                "sector": c["sector"],
                "price": c["price"],
                "dividend_yield": c["dividend_yield"],
                "pe_ratio": c["pe_ratio"],
                "perf_y": c["perf_y"],
                "rsi": c["rsi"],
                "score": c["score"],
                "grade": c["grade"],
                "scoring_details": c["scoring_details"],
            }
            for c in top_candidates
        ],
        "metadata": {"market": "US", "source": "tradingview"},
    }

    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(clean_for_json(payload), f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(top_candidates, len(stocks), ts, args.min_yield))

    print(f"\nReports:")
    print(f"  {base}.json")
    print(f"  {base}.md")


if __name__ == "__main__":
    main()
