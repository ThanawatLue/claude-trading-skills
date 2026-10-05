#!/usr/bin/env python3
"""Intraday Breakout & Volume Surge Scanner (ORB-30 / ORB-45).

Monitors market action 30–45 minutes after market open:
- Detects Opening Range Breakouts (ORB) where price decisively clears the initial session high.
- Confirms breakouts with Relative Volume surge (RVOL >= 1.5x) vs opening baseline.
- Anchors tight risk-reward stops to ORB midpoint / low to prevent whipsaws.
- Rejects over-extended entries (>4.5% above high) to avoid buying the top of intraday spikes.
- Exports actionable candidates to `state/jules_tasks/intraday_candidates.json` (TH)
  and `state/jules_us_tasks/intraday_candidates.json` (US).

Usage:
    python scripts/intraday_breakout_scanner.py scan --market TH
    python scripts/intraday_breakout_scanner.py scan --market US
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

import pandas as pd

from scripts.jules_trader import round_to_set_tick

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("intraday_breakout_scanner")

# Standard High-Liquidity Watchlists for Intraday Monitoring
DEFAULT_TH_UNIVERSE = [
    "DELTA",
    "PTT",
    "AOT",
    "CPALL",
    "ADVANC",
    "GULF",
    "PTTEP",
    "BDMS",
    "SCB",
    "KBANK",
    "BBL",
    "TRUE",
    "CPN",
    "MINT",
    "KTB",
    "CRC",
    "TOP",
    "SCC",
    "BGRIM",
    "BANPU",
    "HMPRO",
    "IVL",
    "GPSC",
    "WHA",
    "MTC",
    "SAWAD",
    "COM7",
    "ITC",
    "CBG",
    "TIDLOR",
]

DEFAULT_US_UNIVERSE = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "AVGO",
    "PLTR",
    "NFLX",
    "QCOM",
    "ARM",
    "SMCI",
    "MU",
    "PANW",
    "CRWD",
    "COIN",
    "UBER",
    "DIS",
]


def get_default_output_dir(market: str = "TH") -> Path:
    """Return default tasks directory for saving intraday candidates."""
    if market.upper() == "US":
        path = PROJECT_ROOT / "state" / "jules_us_tasks"
    else:
        path = PROJECT_ROOT / "state" / "jules_tasks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def compute_orb_levels(df: pd.DataFrame, orb_minutes: int = 30) -> dict[str, float] | None:
    """Compute Opening Range High, Low, Midpoint, and baseline volume from minute candles."""
    if df is None or len(df) < orb_minutes:
        return None

    orb_bars = df.iloc[:orb_minutes]
    high_col = "High" if "High" in orb_bars.columns else "high"
    low_col = "Low" if "Low" in orb_bars.columns else "low"
    vol_col = "Volume" if "Volume" in orb_bars.columns else "volume"

    if high_col not in orb_bars.columns or low_col not in orb_bars.columns:
        return None

    orb_high = float(orb_bars[high_col].max())
    orb_low = float(orb_bars[low_col].min())
    orb_mid = (orb_high + orb_low) / 2.0
    orb_vol = float(orb_bars[vol_col].sum()) if vol_col in orb_bars.columns else 0.0

    return {
        "orb_high": round(orb_high, 4),
        "orb_low": round(orb_low, 4),
        "orb_mid": round(orb_mid, 4),
        "orb_volume": orb_vol,
    }


def evaluate_intraday_candidate(
    symbol: str,
    bars: pd.DataFrame,
    avg_daily_volume: int = 200_000,
    orb_minutes: int = 30,
    market: str = "TH",
) -> dict[str, Any] | None:
    """Evaluate whether a stock exhibits a verified Opening Range Breakout with RVOL."""
    if bars is None or len(bars) <= orb_minutes:
        return None

    orb = compute_orb_levels(bars, orb_minutes=orb_minutes)
    if not orb or orb["orb_high"] <= 0:
        return None

    market_clean = market.upper()
    close_col = "Close" if "Close" in bars.columns else "close"
    vol_col = "Volume" if "Volume" in bars.columns else "volume"

    curr_bar = bars.iloc[-1]
    curr_price = float(curr_bar[close_col])

    # 1. Breakout Clearance Check: Must be above ORB High
    if curr_price <= orb["orb_high"]:
        return {"symbol": symbol, "is_breakout": False, "reason": "Inside or below ORB"}

    # 2. Over-extension Check: Reject if extended > 4.5% past ORB high
    pct_extended = ((curr_price - orb["orb_high"]) / orb["orb_high"]) * 100.0
    if pct_extended > 4.5:
        return {
            "symbol": symbol,
            "is_breakout": False,
            "reason": f"Over-extended (+{pct_extended:.1f}% above ORB high)",
        }

    # 3. Relative Volume (RVOL) Check
    recent_bars = bars.iloc[orb_minutes:]
    if vol_col in recent_bars.columns and orb["orb_volume"] > 0:
        recent_vol_rate = float(recent_bars[vol_col].mean())
        orb_vol_rate = orb["orb_volume"] / orb_minutes
        rvol = recent_vol_rate / orb_vol_rate if orb_vol_rate > 0 else 1.0
    else:
        rvol = 1.0

    if rvol < 1.5:
        return {
            "symbol": symbol,
            "is_breakout": False,
            "reason": f"Insufficient volume surge (RVOL {rvol:.2f}x < 1.5x)",
        }

    # 4. Stop and Target Calculation
    # Invalidation stop: ORB Midpoint (or ORB Low if midpoint is too tight)
    raw_stop = orb["orb_mid"]
    if market_clean == "US":
        stop_price = round(raw_stop, 2)
        # Ensure stop is at least 4.5% below entry to pass Jules risk sanity
        if (curr_price - stop_price) / curr_price < 0.045:
            stop_price = round(curr_price * 0.955, 2)
        target_price = round(curr_price + ((curr_price - stop_price) * 2.0), 2)
    else:
        stop_price = round_to_set_tick(raw_stop, "down")
        if (curr_price - stop_price) / curr_price < 0.045:
            stop_price = round_to_set_tick(curr_price * 0.955, "down")
        target_price = round_to_set_tick(curr_price + ((curr_price - stop_price) * 2.0), "down")

    # Score synthesis: 70 base + (RVOL * 5) + extension bonus
    score = min(95.0, 70.0 + (rvol * 5.0) + (pct_extended * 2.0))

    curr_sym = "$" if market_clean == "US" else "฿"
    highlights = (
        f"ORB-{orb_minutes} Breakout: +{pct_extended:.1f}% > High ({curr_sym}{orb['orb_high']:.2f}) "
        f"| RVOL: {rvol:.1f}x | Stop: {curr_sym}{stop_price:.2f}"
    )

    return {
        "symbol": symbol,
        "is_breakout": True,
        "current_price": curr_price,
        "price": curr_price,
        "stop": stop_price,
        "target": target_price,
        "orb_high": orb["orb_high"],
        "orb_low": orb["orb_low"],
        "orb_mid": orb["orb_mid"],
        "rvol": round(rvol, 2),
        "pct_extended": round(pct_extended, 2),
        "suggested_stop": stop_price,
        "suggested_target": target_price,
        "score": round(score, 1),
        "strategy": f"ORB_{orb_minutes}",
        "market": market_clean,
        "highlights": highlights,
    }


def scan_intraday_breakouts(
    symbols: list[str] | None = None,
    market: str = "TH",
    orb_minutes: int = 30,
    output_dir: Path | None = None,
    data_provider: Callable[[str], pd.DataFrame] | None = None,
) -> list[dict[str, Any]]:
    """Scan the universe for intraday opening range breakouts."""
    market_clean = market.upper()
    target_out_dir = output_dir or get_default_output_dir(market_clean)

    if symbols is None:
        symbols = DEFAULT_US_UNIVERSE if market_clean == "US" else DEFAULT_TH_UNIVERSE

    logger.info(
        "Scanning %d %s symbols for ORB-%d breakouts...", len(symbols), market_clean, orb_minutes
    )
    candidates: list[dict[str, Any]] = []

    for sym in symbols:
        try:
            if data_provider:
                bars = data_provider(sym)
            else:
                from scripts.lib.market_dal import MarketDAL

                dal = MarketDAL()
                bars = dal.get_minute_candles(sym, limit=120)

            if bars is None or bars.empty:
                continue

            result = evaluate_intraday_candidate(
                symbol=sym,
                bars=bars,
                orb_minutes=orb_minutes,
                market=market_clean,
            )
            if result and result.get("is_breakout"):
                candidates.append(result)
                logger.info(
                    "Found Breakout: %s (RVOL: %.1fx, Extended: +%.1f%%)",
                    sym,
                    result["rvol"],
                    result["pct_extended"],
                )
        except Exception as e:
            logger.debug("Error scanning %s: %s", sym, e)

    # Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Save to JSON
    out_payload = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "market": market_clean,
        "orb_minutes": orb_minutes,
        "count": len(candidates),
        "candidates": candidates,
    }
    out_file = target_out_dir / "intraday_candidates.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d intraday breakout candidates to %s", len(candidates), out_file)
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Intraday Breakout & Volume Surge Scanner")
    subparsers = parser.add_subparsers(dest="command")

    scan_p = subparsers.add_parser("scan", help="Scan universe for ORB breakouts")
    scan_p.add_argument("--market", choices=["TH", "US"], default="TH", help="Market to scan")
    scan_p.add_argument("--orb", type=int, default=30, help="Opening range minutes (30 or 45)")
    scan_p.add_argument("--limit", type=int, default=10, help="Max candidates to return")

    args = parser.parse_args()

    if args.command == "scan":
        results = scan_intraday_breakouts(market=args.market, orb_minutes=args.orb)
        print(f"\n=== Found {len(results)} {args.market} Intraday Breakouts ===")
        for r in results[: args.limit]:
            print(f"- {r['symbol']}: {r['highlights']} (Score: {r['score']})")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
