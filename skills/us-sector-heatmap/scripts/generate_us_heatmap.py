#!/usr/bin/env python3
"""
US Sector Heatmap — daily sector-rotation snapshot for the US market.

Single-call data fetch from TradingView Screener (~4000 liquid stocks), grouped
by sector, with median 1M/3M/6M/Y returns and momentum ranking.

Output: us_sector_heatmap_<timestamp>.json + .md

Usage:
    python3 generate_us_heatmap.py --output-dir reports/
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

# Sector momentum composite weights (sum = 1.0)
_W_1M = 0.40
_W_3M = 0.35
_W_6M = 0.20
_W_Y = 0.05
MIN_STOCK_PRICE = 5.0
MIN_STOCK_VOLUME = 100000


def _median(values: list) -> float:
    vs = sorted(v for v in values if v is not None)
    if not vs:
        return 0.0
    m = len(vs) // 2
    return float(vs[m] if len(vs) % 2 else (vs[m - 1] + vs[m]) / 2)


def _momentum_score(p1m: float, p3m: float, p6m: float, py: float) -> float:
    return round(p1m * _W_1M + p3m * _W_3M + p6m * _W_6M + py * _W_Y, 2)


def _emoji(score: float) -> str:
    if score >= 10:
        return "🟢"
    if score >= 0:
        return "🟡"
    return "🔴"


def compute_sector_stats(stocks: list[dict], min_stocks_per_sector: int = 5) -> list[dict]:
    """Group stocks by sector and compute median performance metrics."""
    by_sector: dict[str, list[dict]] = {}
    for s in stocks:
        sec = s.get("sector") or "Unknown"
        if sec == "Unknown":
            continue
        by_sector.setdefault(sec, []).append(s)

    sectors = []
    for sec, group in by_sector.items():
        if len(group) < min_stocks_per_sector:
            continue
        p1m = _median([s.get("perf_1m") for s in group])
        p3m = _median([s.get("perf_3m") for s in group])
        p6m = _median([s.get("perf_6m") for s in group])
        py = _median([s.get("perf_y") for s in group])
        # Top 3 stocks within sector by 3-month performance
        top3 = sorted(
            group,
            key=lambda s: s.get("perf_3m") or -999,
            reverse=True,
        )[:3]
        sectors.append({
            "sector": sec,
            "n_stocks": len(group),
            "median_perf_1m": round(p1m, 2),
            "median_perf_3m": round(p3m, 2),
            "median_perf_6m": round(p6m, 2),
            "median_perf_y": round(py, 2),
            "momentum_score": _momentum_score(p1m, p3m, p6m, py),
            "top_stocks": [
                {
                    "symbol": s["symbol"],
                    "name": s.get("name", s["symbol"]),
                    "perf_3m": round(s.get("perf_3m") or 0, 2),
                    "price": s.get("price"),
                }
                for s in top3
            ],
        })

    # Rank by momentum score (descending)
    sectors.sort(key=lambda s: s["momentum_score"], reverse=True)
    for i, s in enumerate(sectors):
        s["rank"] = i + 1
    return sectors


def to_markdown(sectors: list[dict], universe_size: int, ts: str) -> str:
    lines = [
        "# US Sector Heatmap",
        f"**Generated:** {ts}  |  **Universe:** {universe_size} US stocks  |  **Market:** US",
        "",
        "## Sector Momentum Ranking",
        "",
        "| Rank | Sector | Stocks | 1M | 3M | 6M | 1Y | Momentum |",
        "|------|--------|--------|----|----|----|----|----------|",
    ]
    for s in sectors:
        e = _emoji(s["momentum_score"])
        lines.append(
            f"| {s['rank']} | {s['sector']} | {s['n_stocks']} | "
            f"{s['median_perf_1m']:+.1f}% | {s['median_perf_3m']:+.1f}% | "
            f"{s['median_perf_6m']:+.1f}% | {s['median_perf_y']:+.1f}% | "
            f"{e} {s['momentum_score']:+.1f} |"
        )

    # Top 5 sectors with top stocks
    lines += ["", "## Top 5 Sectors — Leading Stocks", ""]
    for s in sectors[:5]:
        lines.append(f"### {s['rank']}. {s['sector']}  ({_emoji(s['momentum_score'])} {s['momentum_score']:+.1f})")
        for ts_ in s["top_stocks"]:
            price = ts_.get("price") or 0
            lines.append(f"- **{ts_['symbol']}** {ts_['name']} — 3M: {ts_['perf_3m']:+.1f}% @ ${price:.2f}")
        lines.append("")

    # Bottom 3 sectors (avoid list)
    if len(sectors) > 5:
        lines += ["## Bottom 3 Sectors (Avoid / Short Candidates)", ""]
        for s in sectors[-3:]:
            lines.append(f"- {s['rank']}. **{s['sector']}** — Momentum {s['momentum_score']:+.1f}  (1M {s['median_perf_1m']:+.1f}%, 3M {s['median_perf_3m']:+.1f}%)")
        lines.append("")

    lines += [
        "## Methodology",
        "",
        "- **Data source:** TradingView Screener (no API key required)",
        "- **Universe:** US Common Stocks (ETFs and low-liquidity excluded)",
        f"- **Minimum stock price:** ${MIN_STOCK_PRICE:.2f} (stocks below this price are filtered out)",
        f"- **Minimum stock volume:** {MIN_STOCK_VOLUME:,} (avg 10d volume floor)",
        "- **Per-sector aggregation:** Median return (resistant to outliers)",
        f"- **Momentum score:** {_W_1M:.0%}×1M + {_W_3M:.0%}×3M + {_W_6M:.0%}×6M + {_W_Y:.0%}×1Y",
        "- **Color code:** 🟢 ≥ +10  |  🟡 0 to +10  |  🔴 < 0",
        f"- **Minimum stocks per sector:** 5 (sectors with fewer constituents excluded)",
    ]
    return "\n".join(lines)


def main():
    global _W_1M, _W_3M, _W_6M, _W_Y, MIN_STOCK_PRICE, MIN_STOCK_VOLUME

    parser = argparse.ArgumentParser(description="Generate US sector rotation heatmap")
    parser.add_argument("--output-dir", default="reports/", help="Output directory")
    parser.add_argument("--min-stocks", type=int, default=5,
                        help="Minimum stocks per sector to include (default: 5)")
    parser.add_argument("--limit", type=int, default=4000,
                        help="Max stocks to fetch from TradingView (default: 4000)")
    parser.add_argument(
        "--w-1m",
        type=float,
        default=_W_1M,
        help=f"Weight for 1-month performance in momentum score (default: {_W_1M})",
    )
    parser.add_argument(
        "--w-3m",
        type=float,
        default=_W_3M,
        help=f"Weight for 3-month performance in momentum score (default: {_W_3M})",
    )
    parser.add_argument(
        "--w-6m",
        type=float,
        default=_W_6M,
        help=f"Weight for 6-month performance in momentum score (default: {_W_6M})",
    )
    parser.add_argument(
        "--w-y",
        type=float,
        default=_W_Y,
        help=f"Weight for YTD performance in momentum score (default: {_W_Y})",
    )
    parser.add_argument(
        "--min-price",
        type=float,
        default=MIN_STOCK_PRICE,
        help=f"Minimum price filter (default: {MIN_STOCK_PRICE})",
    )
    parser.add_argument(
        "--min-volume",
        type=float,
        default=MIN_STOCK_VOLUME,
        help=f"Minimum 10d avg volume filter (default: {MIN_STOCK_VOLUME})",
    )
    args = parser.parse_args()

    _W_1M = args.w_1m
    _W_3M = args.w_3m
    _W_6M = args.w_6m
    _W_Y = args.w_y
    MIN_STOCK_PRICE = args.min_price
    MIN_STOCK_VOLUME = args.min_volume

    if not tv_available():
        print("ERROR: tradingview-screener not installed.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("US Sector Heatmap Generator")
    print("=" * 60)
    print("Fetching US stocks from TradingView...", end=" ", flush=True)
    stocks = get_us_stocks(limit=args.limit)
    print(f"OK ({len(stocks)} stocks)")

    # Filter out penny and low liquidity stocks
    filtered = [
        s for s in stocks
        if (s.get("price") or 0) >= MIN_STOCK_PRICE
        and (s.get("avgVolume") or 0) >= MIN_STOCK_VOLUME
    ]
    print(f"Applying filters (price >= ${MIN_STOCK_PRICE}, avg volume >= {MIN_STOCK_VOLUME:,}):")
    print(f"  Passed: {len(filtered)} / {len(stocks)} stocks")

    print("\nComputing sector aggregates...", end=" ", flush=True)
    sectors = compute_sector_stats(filtered, min_stocks_per_sector=args.min_stocks)
    print(f"OK ({len(sectors)} sectors)")

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.join(args.output_dir, f"us_sector_heatmap_{ts}")

    payload = {
        "generated": ts,
        "market": "US",
        "universe_size": len(filtered),
        "sectors": sectors,
        "metadata": {"market": "US", "source": "tradingview"},
    }

    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(clean_for_json(payload), f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(sectors, len(filtered), ts))

    print(f"\nReports:")
    print(f"  {base}.json")
    print(f"  {base}.md")


if __name__ == "__main__":
    main()
