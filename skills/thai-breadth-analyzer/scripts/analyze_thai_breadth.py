#!/usr/bin/env python3
"""
Thai Market Breadth Analyzer — fast SET breadth snapshot via TradingView.

Replaces the slow yfinance-loop approach of the US market-breadth-analyzer
for the Thai market: single TV call → full universe → all metrics in ~5s.

Output schema mirrors `market_breadth_<date>.json` so the dashboard's
existing breadth UI can consume it (with metadata.market = "TH").

Usage:
    python3 analyze_thai_breadth.py --output-dir reports/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Import tv_client from the vcp-screener skill
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "vcp-screener" / "scripts"),
)
from tv_client import (  # noqa: E402
    get_thai_breadth,
    clean_for_json,
    is_available as tv_available,
)


# Composite breadth score weights (sum = 1.0)
_W_SMA50 = 0.40
_W_SMA200 = 0.30
_W_AD = 0.15
_W_NHL = 0.15


def composite_score(b: dict) -> tuple[float, str]:
    """Compute 0-100 breadth score from TV breadth dict and return (score, regime)."""
    total = max(b.get("total_stocks", 1), 1)

    # Normalize each component to 0-100
    p50 = b.get("pct_above_sma50", 0)
    p200 = b.get("pct_above_sma200", 0)
    advs = b.get("advancers", 0)
    decs = b.get("decliners", 0)
    ad_balance = ((advs - decs) / total) * 100 + 50  # range ~0-100
    ad_balance = max(0.0, min(100.0, ad_balance))  # Clamping to 0-100
    nh = b.get("new_52w_highs", 0)
    nl = b.get("new_52w_lows", 0)
    nhl_balance = ((nh - nl) / total) * 100 + 50
    nhl_balance = max(0.0, min(100.0, nhl_balance))  # Clamping to 0-100

    score = (
        p50 * _W_SMA50
        + p200 * _W_SMA200
        + ad_balance * _W_AD
        + nhl_balance * _W_NHL
    )
    score = round(max(0.0, min(100.0, score)), 2)

    if score >= 70:
        regime = "Strong Bull"
    elif score >= 50:
        regime = "Healthy Uptrend"
    elif score >= 30:
        regime = "Mixed / Corrective"
    else:
        regime = "Bear Regime"
    return score, regime


def to_markdown(b: dict, score: float, regime: str, ts: str) -> str:
    sectors = list(b.get("sector_breakdown", {}).items())
    lines = [
        "# Thai Market Breadth Report",
        f"**Generated:** {ts}  |  **Universe:** {b.get('total_stocks', 0)} SET stocks  |  **Source:** TradingView Screener",
        "",
        f"## Composite Score: **{score:.1f} / 100** — {regime}",
        "",
        "## Trend Participation",
        "",
        f"- **% above SMA50:** {b.get('pct_above_sma50', 0):.2f}%",
        f"- **% above SMA200:** {b.get('pct_above_sma200', 0):.2f}%",
        "",
        "## Today's Tape",
        "",
        f"- **Advancers:** {b.get('advancers', 0)}",
        f"- **Decliners:** {b.get('decliners', 0)}",
        f"- **Unchanged:** {b.get('unchanged', 0)}",
        "",
        "## Leadership (52w Highs/Lows)",
        "",
        f"- **New 52w highs (within 2%):** {b.get('new_52w_highs', 0)}",
        f"- **New 52w lows (within 2%):** {b.get('new_52w_lows', 0)}",
        "",
        "## RSI Distribution",
        "",
        f"- **Median RSI:** {b.get('median_rsi', 0):.2f}",
        f"- **Oversold (RSI < 30):** {b.get('rsi_oversold', 0)}",
        f"- **Overbought (RSI > 70):** {b.get('rsi_overbought', 0)}",
        "",
        "## Performance",
        "",
        f"- **Median 1M return:** {b.get('median_perf_1m', 0):+.2f}%",
        f"- **Median 3M return:** {b.get('median_perf_3m', 0):+.2f}%",
        "",
    ]

    if sectors:
        lines += ["## Sector Strength (Median 1M Return)", ""]
        lines += ["| Sector | 1M % |", "|--------|------|"]
        for sec, pct in sectors[:15]:
            lines.append(f"| {sec} | {pct:+.2f}% |")
        lines.append("")

    lines += [
        "## Composite Score Methodology",
        "",
        f"- {_W_SMA50:.0%} × `pct_above_sma50` (trend participation)",
        f"- {_W_SMA200:.0%} × `pct_above_sma200` (long-term trend)",
        f"- {_W_AD:.0%} × normalized A/D balance",
        f"- {_W_NHL:.0%} × normalized new highs/lows balance",
        "",
        "Score bands: ≥70 Strong Bull · 50-70 Healthy Uptrend · 30-50 Mixed · <30 Bear",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Thai SET market breadth analyzer (TV)")
    parser.add_argument("--output-dir", default="reports/", help="Output directory")
    parser.add_argument("--min-price", type=float, default=1.0,
                        help="Minimum price filter (default: 1.0 THB)")
    args = parser.parse_args()

    if not tv_available():
        print("ERROR: tradingview-screener not installed.", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Thai Market Breadth Analyzer")
    print("=" * 60)
    print("Fetching breadth snapshot from TradingView...", end=" ", flush=True)
    b = get_thai_breadth(min_price=args.min_price, limit=1500)
    print(f"OK ({b.get('total_stocks', 0)} stocks)")

    score, regime = composite_score(b)
    print(f"Composite Score: {score:.1f} ({regime})")
    print(f"  % above SMA50:  {b.get('pct_above_sma50', 0):.2f}%")
    print(f"  % above SMA200: {b.get('pct_above_sma200', 0):.2f}%")
    print(f"  A/D: {b.get('advancers', 0)}/{b.get('decliners', 0)}")
    print(f"  New highs / lows: {b.get('new_52w_highs', 0)} / {b.get('new_52w_lows', 0)}")

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = os.path.join(args.output_dir, f"thai_market_breadth_{ts}")

    payload = {
        "generated": ts,
        "market": "TH",
        "composite_score": score,
        "regime": regime,
        "composite": {  # mirror US breadth schema so dashboard can render it
            "score": score,
            "regime": regime,
            "components": {
                "pct_above_sma50": b.get("pct_above_sma50"),
                "pct_above_sma200": b.get("pct_above_sma200"),
                "advance_decline_balance": b.get("advancers", 0) - b.get("decliners", 0),
                "new_highs_lows_balance": b.get("new_52w_highs", 0) - b.get("new_52w_lows", 0),
            },
        },
        "breadth": b,
        "metadata": {"market": "TH", "source": "tradingview"},
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(clean_for_json(payload), f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(b, score, regime, ts))

    print(f"\nReports:")
    print(f"  {base}.json")
    print(f"  {base}.md")


if __name__ == "__main__":
    main()
