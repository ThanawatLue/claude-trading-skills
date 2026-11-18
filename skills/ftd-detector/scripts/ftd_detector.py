#!/usr/bin/env python3
"""
FTD Detector - Main Orchestrator

Detects Follow-Through Day (FTD) signals for market bottom confirmation
using William O'Neil's methodology with dual-index tracking.

Usage:
    python3 ftd_detector.py --api-key YOUR_KEY
    python3 ftd_detector.py  # uses FMP_API_KEY env var

Output:
    - JSON: ftd_detector_YYYY-MM-DD_HHMMSS.json
    - Markdown: ftd_detector_YYYY-MM-DD_HHMMSS.md
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Several skills historically expose a module named ``fmp_client``. Ensure
# this orchestrator never reuses a same-named module from another skill when
# multiple skill test suites run in one Python process.
_loaded_fmp = sys.modules.get("fmp_client")
if _loaded_fmp is not None:
    _loaded_path = getattr(_loaded_fmp, "__file__", None)
    if not _loaded_path or Path(_loaded_path).resolve() != SCRIPT_DIR / "fmp_client.py":
        del sys.modules["fmp_client"]

from fmp_client import FMPClient
from post_ftd_monitor import assess_post_ftd_health
from rally_tracker import get_market_state
from report_generator import generate_json_report, generate_markdown_report
from yf_client import YFClient


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="FTD Detector - Follow-Through Day Bottom Confirmation"
    )
    parser.add_argument(
        "--market",
        choices=["US", "TH"],
        default="US",
        help="Market context (US: S&P500/QQQ, TH: THD proxy)",
    )
    parser.add_argument(
        "--api-key", help="FMP API key (defaults to FMP_API_KEY environment variable)"
    )
    parser.add_argument(
        "--use-yf",
        action="store_true",
        help="Use Yahoo Finance directly instead of FMP API",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for reports (default: current directory)",
    )
    return parser.parse_args()


def _fetch_hist_with_fallback(client, symbol: str, days: int = 80):
    data = client.get_historical_prices(symbol, days=days)
    restricted = bool(
        getattr(client, "rate_limit_reached", False) or getattr(client, "auth_restricted", False)
    )
    if (not data or not data.get("historical")) and restricted:
        yf_client = YFClient()
        data = yf_client.get_historical_prices(symbol, days=days)
        return data, yf_client
    return data, None


def main():
    args = parse_arguments()
    market = getattr(args, "market", "US").upper()
    primary_sym = "THD" if market == "TH" else "^GSPC"
    secondary_sym = None if market == "TH" else "QQQ"

    print("=" * 70)
    print(f"FTD Detector ({market}) - Follow-Through Day Bottom Confirmation")
    print("O'Neil Rally Attempt + FTD State Machine")
    print("=" * 70)
    print()

    # Initialize FMP client with Yahoo Finance fallback
    if getattr(args, "use_yf", False):
        client = YFClient()
        print("Using Yahoo Finance client (--use-yf)")
        data_source = "Yahoo Finance"
    else:
        try:
            client = FMPClient(api_key=args.api_key)
            print("FMP API client initialized")
            data_source = "FMP API"
        except ValueError:
            client = YFClient()
            print("Using Yahoo Finance client (FMP API key not set)")
            data_source = "Yahoo Finance"

    # ========================================================================
    # Step 1: Fetch Market Data
    # ========================================================================
    print()
    print("Step 1: Fetching Market Data")
    print("-" * 70)

    # Primary index history
    print(f"  Fetching {primary_sym} history...", end=" ", flush=True)
    sp500_history_data, switched_yf = _fetch_hist_with_fallback(client, primary_sym, days=80)
    if switched_yf is not None:
        client = switched_yf
        data_source = "FMP API + Yahoo Finance fallback"
    sp500_history = sp500_history_data.get("historical", []) if sp500_history_data else []
    if sp500_history:
        print(f"OK ({len(sp500_history)} days)")
    else:
        print("FAILED")
        print(f"ERROR: Cannot proceed without {primary_sym} data", file=sys.stderr)
        sys.exit(1)

    # Secondary index history (NASDAQ/QQQ for US)
    qqq_history = []
    if secondary_sym:
        print(f"  Fetching {secondary_sym} history...", end=" ", flush=True)
        qqq_history_data, switched_yf2 = _fetch_hist_with_fallback(client, secondary_sym, days=80)
        if switched_yf2 is not None:
            client = switched_yf2
            data_source = "FMP API + Yahoo Finance fallback"
        qqq_history = qqq_history_data.get("historical", []) if qqq_history_data else []
        if qqq_history:
            print(f"OK ({len(qqq_history)} days)")
        else:
            print(f"WARN - {secondary_sym} data unavailable, using primary only")

    # Primary quote
    print(f"  Fetching {primary_sym} quote...", end=" ", flush=True)
    sp500_quote_list = client.get_quote(primary_sym)
    sp500_quote = sp500_quote_list[0] if sp500_quote_list else None
    if sp500_quote:
        print(f"OK (${sp500_quote.get('price', 0):.2f})")
    else:
        print("WARN - Using historical close as current price")

    # Secondary quote
    qqq_quote = None
    if secondary_sym:
        print(f"  Fetching {secondary_sym} quote...", end=" ", flush=True)
        qqq_quote_list = client.get_quote(secondary_sym)
        qqq_quote = qqq_quote_list[0] if qqq_quote_list else None
        if qqq_quote:
            print(f"OK (${qqq_quote.get('price', 0):.2f})")
        else:
            print("WARN - Using historical close as current price")

    print()

    # ========================================================================
    # Step 2: Run State Machine (Rally Tracker)
    # ========================================================================
    print("Step 2: Analyzing Market State")
    print("-" * 70)

    market_state = get_market_state(sp500_history, qqq_history)

    sp500_state = market_state["sp500"]["state"]
    nasdaq_state = market_state["nasdaq"]["state"]
    combined = market_state["combined_state"]

    print(f"  S&P 500 State: {sp500_state}")
    print(f"  NASDAQ State:  {nasdaq_state}")
    print(f"  Combined:      {combined}")

    # Print swing low info if found
    for label, idx_data in [("S&P 500", market_state["sp500"]), ("NASDAQ", market_state["nasdaq"])]:
        swing = idx_data.get("swing_low")
        if swing:
            print(
                f"  {label} Swing Low: {swing['swing_low_date']} "
                f"(${swing['swing_low_price']:.2f}, "
                f"{swing['decline_pct']:.1f}% decline)"
            )
        rally = idx_data.get("rally_attempt")
        if rally and rally.get("day1_date"):
            print(f"  {label} Rally Day 1: {rally['day1_date']} (Day {rally['current_day_count']})")

    print()

    # ========================================================================
    # Step 3: Post-FTD Health Assessment
    # ========================================================================
    print("Step 3: Post-FTD Health Assessment")
    print("-" * 70)

    # Convert to chronological for post-FTD analysis
    sp500_chrono = list(reversed(sp500_history))
    nasdaq_chrono = list(reversed(qqq_history)) if qqq_history else []

    market_state = assess_post_ftd_health(market_state, sp500_chrono, nasdaq_chrono)

    quality = market_state.get("quality_score", {})
    print(f"  Quality Score: {quality.get('total_score', 0)}/100")
    print(f"  Signal: {quality.get('signal', 'N/A')}")
    print(f"  Guidance: {quality.get('guidance', 'N/A')}")
    print(f"  Exposure Range: {quality.get('exposure_range', 'N/A')}")

    # Power trend
    pt = market_state.get("power_trend", {})
    if pt:
        print(
            f"  Power Trend: {'YES' if pt.get('power_trend') else 'No'} "
            f"({pt.get('conditions_met', 0)}/3 conditions)"
        )

    # Post-FTD distribution
    dist = market_state.get("post_ftd_distribution", {})
    if dist:
        print(
            f"  Post-FTD Distribution Days: {dist.get('distribution_count', 0)} "
            f"(monitored {dist.get('days_monitored', 0)} days)"
        )

    # Invalidation
    inv = market_state.get("ftd_invalidation", {})
    if inv and inv.get("invalidated"):
        print(
            f"  FTD INVALIDATED on {inv.get('invalidation_date')} "
            f"({inv.get('days_after_ftd')} days after FTD)"
        )

    print()

    # ========================================================================
    # Step 4: Generate Reports
    # ========================================================================
    print("Step 4: Generating Reports")
    print("-" * 70)

    analysis = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market": market,
            "data_source": data_source,
            "api_calls": client.get_api_stats(),
            "index_prices": {
                "sp500": sp500_quote.get("price", 0)
                if sp500_quote
                else (sp500_history[0].get("close", 0) if sp500_history else None),
                "qqq": qqq_quote.get("price", 0)
                if qqq_quote
                else (qqq_history[0].get("close", 0) if qqq_history else None),
            },
        },
        "market_state": {
            "combined_state": market_state["combined_state"],
            "dual_confirmation": market_state["dual_confirmation"],
            "ftd_index": market_state.get("ftd_index"),
        },
        "sp500": _serialize_index(market_state["sp500"]),
        "nasdaq": _serialize_index(market_state["nasdaq"]),
        "quality_score": quality,
        "post_ftd_distribution": market_state.get("post_ftd_distribution", {}),
        "ftd_invalidation": market_state.get("ftd_invalidation", {}),
        "power_trend": market_state.get("power_trend", {}),
    }

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    json_file = os.path.join(args.output_dir, f"ftd_detector_{market}_{timestamp}.json")
    md_file = os.path.join(args.output_dir, f"ftd_detector_{market}_{timestamp}.md")

    generate_json_report(analysis, json_file)
    generate_markdown_report(analysis, md_file)

    print()
    print("=" * 70)
    print("FTD Detection Complete")
    print("=" * 70)
    print(f"  Combined State: {market_state['combined_state']}")
    print(f"  Quality Score: {quality.get('total_score', 0)}/100 ({quality.get('signal', 'N/A')})")
    print(f"  JSON Report: {json_file}")
    print(f"  Markdown Report: {md_file}")
    print()

    stats = client.get_api_stats()
    print("API Usage:")
    print(f"  API calls made: {stats['api_calls_made']}")
    print(f"  Cache entries: {stats['cache_entries']}")
    print()


def _serialize_index(idx_data: dict) -> dict:
    """Serialize index analysis for JSON output, removing large rally_days lists."""
    result = {
        "state": idx_data.get("state"),
        "current_price": idx_data.get("current_price"),
        "lookback_high": idx_data.get("lookback_high"),
        "correction_depth_pct": idx_data.get("correction_depth_pct"),
    }

    swing = idx_data.get("swing_low")
    if swing:
        result["swing_low"] = {
            "date": swing.get("swing_low_date"),
            "price": swing.get("swing_low_price"),
            "decline_pct": swing.get("decline_pct"),
            "down_days": swing.get("down_days"),
            "recent_high_date": swing.get("recent_high_date"),
            "recent_high_price": swing.get("recent_high_price"),
        }

    rally = idx_data.get("rally_attempt")
    if rally:
        result["rally_attempt"] = {
            "day1_date": rally.get("day1_date"),
            "current_day_count": rally.get("current_day_count"),
            "invalidated": rally.get("invalidated"),
            "invalidation_reason": rally.get("invalidation_reason"),
        }

    ftd = idx_data.get("ftd")
    if ftd:
        result["ftd"] = {
            "ftd_detected": ftd.get("ftd_detected"),
            "ftd_date": ftd.get("ftd_date"),
            "ftd_day_number": ftd.get("ftd_day_number"),
            "ftd_low": ftd.get("ftd_low"),
            "gain_pct": ftd.get("gain_pct"),
            "gain_tier": ftd.get("gain_tier"),
            "volume_above_avg": ftd.get("volume_above_avg"),
        }

    return result


if __name__ == "__main__":
    main()
