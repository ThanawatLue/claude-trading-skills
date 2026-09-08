#!/usr/bin/env python3
"""
Thai Market Daily Routine Pipeline Runner.

Runs the complete end-of-day Thai market analysis pipeline sequentially:
  1. thai-breadth-analyzer: Assess SET market breadth (% > SMA50/200, AD ratio)
  2. thai-sector-heatmap: Rank 3M/1M sector momentum to identify leading sectors
  3. thai-watchlist-builder: Segment universe into Growth, Momentum, Value, Mean-Reversion
  4. vcp-screener (screen_thai_swing.py): Screen swing setups (3-5 day breakout/pullback)
  5. thai-dividend-screener: Screen dividend yield & payout safety
  6. paper-trade-simulator (update_marks.py): Update mark-to-market prices & trade status

Usage:
  python scripts/run_thai_market_daily.py [--output-dir reports/] [--skip-dividends] [--skip-paper]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Resolve project root
_REPO_ROOT = Path(__file__).resolve().parents[1]


def run_step(step_num: int, name: str, script_path: Path, args: list[str]) -> bool:
    """Execute a single pipeline step via subprocess."""
    print("\n" + "=" * 65)
    print(f"[{step_num}/6] Running: {name}")
    print("=" * 65)

    cmd = [sys.executable, str(script_path)] + args
    start_t = time.time()
    res = subprocess.run(cmd, cwd=str(_REPO_ROOT))
    elapsed = time.time() - start_t

    if res.returncode == 0:
        print(f"\n[OK] Step {step_num} finished in {elapsed:.1f}s")
        return True
    else:
        print(f"\n[FAIL] Step {step_num} failed with return code {res.returncode}", file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run complete Thai market daily analysis pipeline")
    parser.add_argument("--output-dir", default="reports", help="Output directory for reports (default: reports/)")
    parser.add_argument("--skip-dividends", action="store_true", help="Skip dividend screener")
    parser.add_argument("--skip-paper", action="store_true", help="Skip paper trade simulator marks update")

    args = parser.parse_args(argv)
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print("*" * 65)
    print("       THAI MARKET DAILY ROUTINE PIPELINE (SET / MAI)")
    print("*" * 65)
    print(f"Output Directory: {output_dir}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    steps = [
        (
            1,
            "Market Breadth Analyzer",
            _REPO_ROOT / "skills" / "thai-breadth-analyzer" / "scripts" / "analyze_thai_breadth.py",
            ["--output-dir", output_dir],
            True,
        ),
        (
            2,
            "Sector Rotation Heatmap",
            _REPO_ROOT / "skills" / "thai-sector-heatmap" / "scripts" / "generate_heatmap.py",
            ["--output-dir", output_dir],
            True,
        ),
        (
            3,
            "Multi-Strategy Watchlist Builder",
            _REPO_ROOT / "skills" / "thai-watchlist-builder" / "scripts" / "build_watchlists.py",
            ["--output-dir", output_dir],
            True,
        ),
        (
            4,
            "Thai Swing Trade Screener (3-5 day setups)",
            _REPO_ROOT / "skills" / "vcp-screener" / "scripts" / "screen_thai_swing.py",
            ["--output-dir", output_dir],
            True,
        ),
        (
            5,
            "Dividend Growth & High-Yield Screener",
            _REPO_ROOT / "skills" / "thai-dividend-screener" / "scripts" / "screen_thai_dividends.py",
            ["--output-dir", output_dir],
            not args.skip_dividends,
        ),
        (
            6,
            "Paper Trade Simulator (Mark-to-market update)",
            _REPO_ROOT / "skills" / "paper-trade-simulator" / "scripts" / "update_marks.py",
            [],
            not args.skip_paper,
        ),
    ]

    total_start = time.time()
    failures = 0

    for step_num, name, script_file, script_args, should_run in steps:
        if not should_run:
            print(f"\n[SKIP] Step {step_num}: {name} skipped by user flag.")
            continue

        if not script_file.is_file():
            print(f"\n[ERROR] Script not found: {script_file}", file=sys.stderr)
            failures += 1
            continue

        success = run_step(step_num, name, script_file, script_args)
        if not success:
            failures += 1

    total_elapsed = time.time() - total_start
    print("\n" + "*" * 65)
    print("                    PIPELINE SUMMARY")
    print("*" * 65)
    print(f"Total Elapsed Time: {total_elapsed:.1f}s")
    print(f"Status: {'SUCCESS' if failures == 0 else f'FAILED ({failures} steps failed)'}")
    print(f"Reports available in: {output_dir}")

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
