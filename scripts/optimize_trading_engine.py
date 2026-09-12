"""Automated Strategy & Exit Engine Optimization Framework.

Performs systematic multi-dimensional grid search across historical data (July-Sept 2026)
to find the optimal combination of:
1. Source Strategy Selection & Score Filters
2. Minimum Risk Distance (to eliminate commission drag on small stops)
3. Profit Targets & Scale-Out (Partial TP)
4. MFE Ratchet & Breakeven Stops
5. Velocity Decay / Stall Exits
"""

from __future__ import annotations

import itertools
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path(r"d:\ex_work\tong_trading\state\vm_market_cache.db")


@dataclass
class SimStrategy:
    name: str
    allowed_sources: list[str]
    min_scores: dict[str, float]
    min_stop_pct: float = 3.0      # Minimum stop % to avoid fee drag
    max_stop_pct: float = 6.0      # Maximum stop % to keep positions meaningful
    use_scale_out: bool = True     # Sell 50% at T1, 50% at T2
    target_1_r: float = 1.0        # First target
    target_2_r: float = 2.0        # Final target
    use_breakeven: bool = True     # Move stop to BE (+0.05R) after T1 or MFE
    be_trigger_r: float = 1.0
    use_velocity_stall: bool = True
    stall_days: int = 4
    stall_min_mfe: float = 0.25
    max_hold_days: int = 12
    commission_bps: float = 21.692


def load_dataset(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    signals = [dict(r) for r in conn.execute(
        """SELECT signal_id, symbol, market, source_skill, signal_date, 
                  raw_score, entry_price, stop_price, target_price
           FROM signal_ledger 
           WHERE market='TH' AND entry_price IS NOT NULL AND entry_price > 0
           ORDER BY signal_date ASC, raw_score DESC"""
    ).fetchall()]

    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    bar_rows = conn.execute(
        "SELECT symbol, date, open, high, low, close, volume FROM price_bar ORDER BY symbol, date ASC"
    ).fetchall()
    conn.close()

    for b in bar_rows:
        if b["open"] is not None and b["high"] is not None and b["low"] is not None and b["close"] is not None:
            bars_by_symbol.setdefault(b["symbol"], []).append(dict(b))

    return signals, bars_by_symbol


def simulate(strategy: SimStrategy, signals: list[dict], bars_by_symbol: dict) -> dict[str, Any]:
    active_symbols: dict[str, str] = {}
    trades = []
    account_cash = 30000.0
    risk_budget_thb = 300.0  # 1% risk
    max_pos_thb = 6000.0     # 20% max per position
    fee_rate = strategy.commission_bps / 10000.0

    for sig in signals:
        src = sig["source_skill"]
        if src not in strategy.allowed_sources:
            continue

        score = float(sig["raw_score"] or 0.0)
        req_score = strategy.min_scores.get(src, 75.0)
        if score < req_score:
            continue

        sym = sig["symbol"]
        sig_date = sig["signal_date"]
        entry = float(sig["entry_price"])
        raw_stop = float(sig["stop_price"]) if sig["stop_price"] else entry * 0.95
        
        # Risk clamp
        raw_risk_pct = (entry - raw_stop) / entry * 100.0
        if raw_risk_pct < strategy.min_stop_pct:
            # Expand stop to min_stop_pct to avoid fee drag
            stop = entry * (1.0 - strategy.min_stop_pct / 100.0)
        elif raw_risk_pct > strategy.max_stop_pct:
            stop = entry * (1.0 - strategy.max_stop_pct / 100.0)
        else:
            stop = raw_stop

        risk = entry - stop
        if risk <= 0:
            continue

        bars = bars_by_symbol.get(sym, [])
        sub_bars = [b for b in bars if b["date"] >= sig_date]
        if len(sub_bars) < 2:
            continue

        # Prevent concurrent duplicate position
        if sym in active_symbols and active_symbols[sym] >= sub_bars[1]["date"]:
            continue

        entry_bar = sub_bars[1]
        actual_entry = float(entry_bar["open"]) if entry_bar["open"] else entry
        actual_stop = actual_entry - risk
        t1_price = actual_entry + (risk * strategy.target_1_r)
        t2_price = actual_entry + (risk * strategy.target_2_r)

        # Position sizing in board lots (100 shares)
        shares = int(risk_budget_thb / risk)
        shares = max(100, (shares // 100) * 100)
        if shares * actual_entry > max_pos_thb:
            shares = max(100, int(max_pos_thb / actual_entry // 100) * 100)
        initial_risk_thb = shares * risk

        trade_bars = sub_bars[1:]
        stop_price = actual_stop
        peak_high = actual_entry
        scaled_out = False
        scale_pnl = 0.0
        scale_price = 0.0

        exit_bar = trade_bars[-1]
        exit_price = float(exit_bar["close"])
        exit_reason = "end_of_data"

        for d_idx, b in enumerate(trade_bars):
            o, h, l, c = float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])
            peak_high = max(peak_high, h)
            mfe_r = (peak_high - actual_entry) / risk

            # Breakeven trigger
            if strategy.use_breakeven and mfe_r >= strategy.be_trigger_r:
                # Lift stop to Breakeven (+0.05R to cover fees)
                stop_price = max(stop_price, actual_entry + (risk * 0.05))

            # Scale-out at Target 1 (50% position)
            if strategy.use_scale_out and not scaled_out and h >= t1_price:
                scaled_out = True
                scale_price = max(o, t1_price)
                half_shares = shares // 2
                scale_pnl = (scale_price - actual_entry) * half_shares - (actual_entry * half_shares * fee_rate) - (scale_price * half_shares * fee_rate)
                # After scale out, guarantee remaining half stop is at Breakeven
                stop_price = max(stop_price, actual_entry + (risk * 0.05))

            # Stop hit
            if l <= stop_price:
                exit_price = min(o, stop_price)
                exit_reason = "ratchet_be" if stop_price > actual_stop + 1e-4 else "stop"
                exit_bar = b
                break

            # Target 2 hit (remaining or full)
            if h >= t2_price:
                exit_price = max(o, t2_price)
                exit_reason = "target"
                exit_bar = b
                break

            # Velocity Stall (dead trade)
            curr_r = (c - actual_entry) / risk
            if strategy.use_velocity_stall and d_idx >= strategy.stall_days and mfe_r < strategy.stall_min_mfe and curr_r <= 0.0:
                exit_price = c
                exit_reason = "stalled"
                exit_bar = b
                break

            # Max hold time stop
            if d_idx >= strategy.max_hold_days and curr_r < -0.3:
                exit_price = c
                exit_reason = "time"
                exit_bar = b
                break

        # Calculate Net PnL
        if strategy.use_scale_out and scaled_out:
            rem_shares = shares - (shares // 2)
            rem_pnl = (exit_price - actual_entry) * rem_shares - (actual_entry * rem_shares * fee_rate) - (exit_price * rem_shares * fee_rate)
            net_pnl = scale_pnl + rem_pnl
        else:
            gross = (exit_price - actual_entry) * shares
            costs = (actual_entry * shares * fee_rate) + (exit_price * shares * fee_rate)
            net_pnl = gross - costs

        realized_r = net_pnl / initial_risk_thb if initial_risk_thb > 0 else 0.0
        active_symbols[sym] = exit_bar["date"]

        trades.append({
            "realized_r": realized_r,
            "net_pnl": net_pnl,
            "reason": exit_reason,
            "days": trade_bars.index(exit_bar) if exit_bar in trade_bars else len(trade_bars) - 1,
        })

    total = len(trades)
    if total == 0:
        return {"name": strategy.name, "total": 0, "net_r": -999, "net_pnl": -999, "win_rate": 0, "pf": 0}

    wins = [t for t in trades if t["realized_r"] > 0]
    losses = [t for t in trades if t["realized_r"] <= 0]
    win_rate = len(wins) / total * 100.0
    net_r = sum(t["realized_r"] for t in trades)
    net_pnl = sum(t["net_pnl"] for t in trades)

    sum_win_thb = sum(t["net_pnl"] for t in wins)
    sum_loss_thb = abs(sum(t["net_pnl"] for t in losses)) if losses else 1.0
    pf = (sum_win_thb / sum_loss_thb) if sum_loss_thb > 0 else 99.0
    avg_days = sum(t["days"] for t in trades) / total

    # Exit reason distribution
    reasons = {}
    for t in trades:
        reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1

    return {
        "name": strategy.name,
        "total": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "net_r": round(net_r, 2),
        "net_pnl": round(net_pnl, 2),
        "pf": round(pf, 2),
        "avg_days": round(avg_days, 1),
        "reasons": reasons,
    }


def main():
    print(f"Loading data from {DB_PATH}...")
    signals, bars = load_dataset(DB_PATH)

    # ── Exploration Grid ──
    # 1. Test Source Combinations
    source_sets = [
        ("All Sources", ["thai-swing-momentum", "thai-swing-dip", "vcp-screener"]),
        ("Momentum Only", ["thai-swing-momentum"]),
        ("Momentum + VCP", ["thai-swing-momentum", "vcp-screener"]),
        ("Momentum + High-Score Dip (Dip>=85)", ["thai-swing-momentum", "thai-swing-dip"]),
    ]

    # 2. Test Minimum Stop Pct (eliminating fee drag: 2.0% vs 3.0% vs 4.0%)
    min_stops = [2.5, 3.5, 4.5]

    # 3. Test Scale-Out Targets (T1 / T2)
    targets = [
        (1.0, 2.0),
        (1.2, 2.0),
        (1.2, 2.5),
        (1.5, 2.5),
        (1.0, 1.8),
    ]

    # 4. Test Velocity Stall Days (3d vs 4d vs 5d vs None)
    stalls = [
        (True, 3, 0.25),
        (True, 4, 0.30),
        (True, 5, 0.35),
        (False, 0, 0.0),
    ]

    print("Running multi-dimensional optimization grid...")
    all_results = []

    for (s_label, sources), min_stop, (t1, t2), (use_stall, stall_d, stall_mfe) in itertools.product(
        source_sets, min_stops, targets, stalls
    ):
        min_scores = {
            "thai-swing-momentum": 78.0,
            "thai-swing-dip": 85.0 if "High-Score" in s_label else 80.0,
            "vcp-screener": 70.0,
        }
        cfg_name = f"{s_label} | Stop>={min_stop}% | T1:{t1}R T2:{t2}R | Stall:{stall_d}d" if use_stall else f"{s_label} | Stop>={min_stop}% | T1:{t1}R T2:{t2}R | NoStall"
        strat = SimStrategy(
            name=cfg_name,
            allowed_sources=sources,
            min_scores=min_scores,
            min_stop_pct=min_stop,
            target_1_r=t1,
            target_2_r=t2,
            be_trigger_r=t1,
            use_velocity_stall=use_stall,
            stall_days=stall_d,
            stall_min_mfe=stall_mfe,
        )
        res = simulate(strat, signals, bars)
        if res["total"] >= 10:  # Must have statistical sample
            all_results.append(res)

    # Sort by Net Realized R descending, then Profit Factor
    all_results.sort(key=lambda x: (x["net_r"], x["pf"]), reverse=True)

    print("\n" + "=" * 110)
    print("                      TOP 15 BEST PERFORMING CONFIGURATIONS ACROSS ALL TESTS")
    print("=" * 110)
    print(f"{'Rank':<5} {'Configuration':<60} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6}")
    print("-" * 110)

    for idx, r in enumerate(all_results[:15], 1):
        print(f"{idx:<5} {r['name']:<60} {r['total']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}")

    print("\n" + "=" * 110)
    print("                      TOP 5 CONFIGURATIONS FOR 'MOMENTUM ONLY'")
    print("=" * 110)
    momo_results = [r for r in all_results if "Momentum Only" in r["name"]]
    for idx, r in enumerate(momo_results[:5], 1):
        print(f"{idx:<5} {r['name']:<60} {r['total']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}")

    print("\n" + "=" * 110)


if __name__ == "__main__":
    main()
