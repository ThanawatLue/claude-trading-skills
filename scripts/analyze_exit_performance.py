#!/usr/bin/env python3
"""Empirical Exit Performance Telemetry & Analytics.

Analyzes paper trading history to evaluate:
1. Distribution of exits (Target vs Ratchet vs Stop vs Velocity Stall vs Time vs Invalidation)
2. MFE Capture Efficiency (Realized R vs Peak MFE R)
3. Capital saved by Velocity Stall and Ratchet Stops
4. Empirical metrics for optimizing exit parameters per source technique
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / "state" / "market_cache.db"


def analyze_exits(
    db_path: Path = DEFAULT_DB,
    market: str | None = None,
) -> dict[str, Any]:
    """Inspect closed paper trades and generate exit telemetry."""
    if not db_path.exists():
        return {
            "ok": False,
            "error": f"database not found: {db_path}",
            "total_closed": 0,
        }

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trade'"
    ).fetchone()
    if not tbl:
        conn.close()
        return {
            "ok": False,
            "error": "paper_trade table does not exist in db",
            "total_closed": 0,
        }

    query = "SELECT * FROM paper_trade WHERE status != 'open'"
    params: list[Any] = []
    if market:
        query += " AND UPPER(market) = ?"
        params.append(market.upper())
    query += " ORDER BY id ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        return {
            "ok": True,
            "total_closed": 0,
            "message": "No closed trades found matching criteria",
            "market": market,
        }

    total_closed = len(rows)
    wins = [r for r in rows if (r["realized_r"] or 0) > 0]
    losses = [r for r in rows if (r["realized_r"] or 0) < 0]
    breakeven = [r for r in rows if (r["realized_r"] or 0) == 0]

    total_realized_r = sum((r["realized_r"] or 0) for r in rows)
    total_realized_pnl = sum((r["realized_pnl"] or 0) for r in rows)

    status_groups: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        st = r["status"] or "unknown"
        status_groups.setdefault(st, []).append(r)

    status_metrics: dict[str, dict[str, Any]] = {}
    total_saved_r_from_stalls = 0.0
    total_saved_r_from_ratchets = 0.0

    for st, group in sorted(status_groups.items()):
        cnt = len(group)
        g_wins = [r for r in group if (r["realized_r"] or 0) > 0]
        g_losses = [r for r in group if (r["realized_r"] or 0) < 0]
        g_r = sum((r["realized_r"] or 0) for r in group)
        g_pnl = sum((r["realized_pnl"] or 0) for r in group)
        g_days = [r["days_held"] for r in group if r["days_held"] is not None]

        mfe_r_list: list[float] = []
        mae_r_list: list[float] = []
        for r in group:
            entry = r["entry_price"]
            shares = r["shares"]
            initial_risk = float(r["initial_risk"] or 0)
            risk_per_share = (
                (initial_risk / shares)
                if (shares > 0 and initial_risk > 0)
                else abs(entry - float(r["stop_price"]))
            )
            if risk_per_share > 0:
                side = r["side"]
                mfe = r["mfe"] or entry
                mae = r["mae"] or entry
                m_gain = (mfe - entry) if side == "long" else (entry - mfe)
                m_loss = (entry - mae) if side == "long" else (mae - entry)
                mfe_r_list.append(round(m_gain / risk_per_share, 3))
                mae_r_list.append(round(m_loss / risk_per_share, 3))

        avg_mfe_r = (sum(mfe_r_list) / len(mfe_r_list)) if mfe_r_list else 0.0
        avg_mae_r = (sum(mae_r_list) / len(mae_r_list)) if mae_r_list else 0.0
        avg_r = g_r / cnt if cnt else 0.0

        if st in ("closed_stalled", "closed_time"):
            for r in group:
                realized = float(r["realized_r"] or 0)
                if realized > -1.0:
                    total_saved_r_from_stalls += 1.0 + realized
        elif st == "closed_ratchet":
            for r in group:
                realized = float(r["realized_r"] or 0)
                if realized > -1.0:
                    total_saved_r_from_ratchets += realized - (-1.0)

        status_metrics[st] = {
            "count": cnt,
            "pct_of_total": round((cnt / total_closed) * 100, 1),
            "wins": len(g_wins),
            "losses": len(g_losses),
            "sum_realized_r": round(g_r, 2),
            "avg_realized_r": round(avg_r, 2),
            "sum_pnl": round(g_pnl, 2),
            "avg_mfe_r": round(avg_mfe_r, 2),
            "avg_mae_r": round(avg_mae_r, 2),
            "avg_days_held": round(sum(g_days) / len(g_days), 1) if g_days else 0.0,
        }

    source_groups: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        src = r["source"] or "unknown"
        source_groups.setdefault(src, []).append(r)

    source_metrics: dict[str, dict[str, Any]] = {}
    for src, group in sorted(source_groups.items()):
        cnt = len(group)
        g_wins = [r for r in group if (r["realized_r"] or 0) > 0]
        g_r = sum((r["realized_r"] or 0) for r in group)
        g_pnl = sum((r["realized_pnl"] or 0) for r in group)
        win_r_sum = sum((r["realized_r"] or 0) for r in g_wins)

        win_mfe_sum = 0.0
        for r in g_wins:
            entry = r["entry_price"]
            shares = r["shares"]
            initial_risk = float(r["initial_risk"] or 0)
            risk_per_share = (
                (initial_risk / shares)
                if (shares > 0 and initial_risk > 0)
                else abs(entry - float(r["stop_price"]))
            )
            if risk_per_share > 0:
                side = r["side"]
                mfe = r["mfe"] or entry
                m_gain = (mfe - entry) if side == "long" else (entry - mfe)
                win_mfe_sum += m_gain / risk_per_share

        capture_eff = (win_r_sum / win_mfe_sum) if win_mfe_sum > 0 else 0.0

        source_metrics[src] = {
            "count": cnt,
            "wins": len(g_wins),
            "win_rate": round((len(g_wins) / cnt) * 100, 1) if cnt else 0.0,
            "sum_realized_r": round(g_r, 2),
            "sum_pnl": round(g_pnl, 2),
            "avg_r": round(g_r / cnt, 2) if cnt else 0.0,
            "capture_efficiency_pct": round(capture_eff * 100, 1),
        }

    total_win_r = sum((r["realized_r"] or 0) for r in wins)
    total_win_mfe = 0.0
    for r in wins:
        entry = r["entry_price"]
        shares = r["shares"]
        initial_risk = float(r["initial_risk"] or 0)
        risk_per_share = (
            (initial_risk / shares)
            if (shares > 0 and initial_risk > 0)
            else abs(entry - float(r["stop_price"]))
        )
        if risk_per_share > 0:
            side = r["side"]
            mfe = r["mfe"] or entry
            m_gain = (mfe - entry) if side == "long" else (entry - mfe)
            total_win_mfe += m_gain / risk_per_share

    global_capture_efficiency = (total_win_r / total_win_mfe) if total_win_mfe > 0 else 0.0

    return {
        "ok": True,
        "market": market or "ALL",
        "total_closed": total_closed,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(breakeven),
        "win_rate_pct": round((len(wins) / total_closed) * 100, 1) if total_closed else 0.0,
        "sum_realized_r": round(total_realized_r, 2),
        "sum_realized_pnl": round(total_realized_pnl, 2),
        "global_capture_efficiency_pct": round(global_capture_efficiency * 100, 1),
        "estimated_capital_saved_r": {
            "from_stalls": round(total_saved_r_from_stalls, 2),
            "from_ratchets": round(total_saved_r_from_ratchets, 2),
            "total": round(total_saved_r_from_stalls + total_saved_r_from_ratchets, 2),
        },
        "by_exit_status": status_metrics,
        "by_source": source_metrics,
    }


def print_report(data: dict[str, Any]) -> None:
    """Format and print the telemetry report."""
    if not data.get("ok"):
        print(f"Error: {data.get('error')}", file=sys.stderr)
        return

    total = data.get("total_closed", 0)
    if total == 0:
        print(data.get("message", "No trades to report"))
        return

    print("=" * 72)
    print(f"  EXIT PERFORMANCE & TELEMETRY REPORT (Market: {data.get('market')})")
    print("=" * 72)
    print(f"Total Closed Trades : {total}")
    print(
        f"Win / Loss / BE     : {data['wins']}W / {data['losses']}L / {data['breakeven']}BE (Win Rate: {data['win_rate_pct']}%)"
    )
    print(f"Net Realized R      : {data['sum_realized_r']:+.2f}R")
    print(f"Net Realized PnL    : {data['sum_realized_pnl']:+,.2f} THB")
    print(
        f"MFE Capture Effic.  : {data['global_capture_efficiency_pct']:.1f}% of peak profit banked"
    )

    saved = data.get("estimated_capital_saved_r", {})
    print(
        f"Risk Capital Saved  : {saved.get('total', 0.0):+.2f}R (Stalls: {saved.get('from_stalls', 0):+.2f}R, Ratchets: {saved.get('from_ratchets', 0):+.2f}R)"
    )
    print("-" * 72)

    print("\n[EXITS BY REASON / STATUS]")
    print(f"{'Status':<20} {'Count':>6} {'Pct':>7} {'Avg R':>8} {'Avg MFE':>9} {'Avg Days':>9}")
    print("-" * 64)
    for st, m in data.get("by_exit_status", {}).items():
        print(
            f"{st:<20} {m['count']:>6} {m['pct_of_total']:>6.1f}% {m['avg_realized_r']:>+7.2f}R {m['avg_mfe_r']:>+7.2f}R {m['avg_days_held']:>8.1f}d"
        )

    print("\n[PERFORMANCE BY SOURCE TECHNIQUE]")
    print(f"{'Source':<24} {'Count':>6} {'WinRate':>8} {'Net R':>8} {'CaptureEff':>11}")
    print("-" * 64)
    for src, m in data.get("by_source", {}).items():
        print(
            f"{src:<24} {m['count']:>6} {m['win_rate']:>7.1f}% {m['sum_realized_r']:>+7.2f}R {m['capture_efficiency_pct']:>9.1f}%"
        )
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze exit performance and telemetry.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to market_cache.db")
    parser.add_argument("--market", type=str, default="TH", help="Market filter (e.g. TH, US)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()
    market = None if args.market.upper() in ("ALL", "") else args.market
    data = analyze_exits(db_path=args.db, market=market)

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_report(data)
    return 0 if data.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
