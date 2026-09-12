"""Historical Replay & Exit Engine Simulation.

Replays historical signals through daily price bars to compare:
- Scenario A: Baseline Old Config (Static Target, No MFE Ratchet, 15-day calendar hold)
- Scenario B: New Institutional Config (Multi-tier MFE Ratchet + Velocity Decay Stall Exit)
- Scenario C: Variations / Parameter Tuning (Different ratchet tiers and stall thresholds)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / "state" / "vm_market_cache.db" if (BASE_DIR / "state" / "vm_market_cache.db").exists() else BASE_DIR / "state" / "market_cache.db"

# SET Tick rounding
def round_to_set_tick(price: float, direction: str = "down") -> float:
    if price < 2.0:
        tick = 0.01
    elif price < 5.0:
        tick = 0.02
    elif price < 10.0:
        tick = 0.05
    elif price < 25.0:
        tick = 0.10
    elif price < 100.0:
        tick = 0.25
    elif price < 200.0:
        tick = 0.50
    elif price < 400.0:
        tick = 1.00
    else:
        tick = 2.00

    import math
    if direction == "up":
        return round(math.ceil(price / tick) * tick, 2)
    elif direction == "down":
        return round(math.floor(price / tick) * tick, 2)
    return round(round(price / tick) * tick, 2)


@dataclass
class ExitConfig:
    name: str
    target_r: float = 2.0
    use_ratchet: bool = True
    ratchet_tiers: list[list[float]] = field(default_factory=lambda: [[0.8, -0.3], [1.2, 0.15], [1.8, 0.8]])
    use_velocity_stall: bool = True
    velocity_stall_days: int = 3
    velocity_min_mfe_r: float = 0.30
    max_hold_days: int = 15
    time_stop_min_r: float = -0.5
    commission_bps: float = 21.692  # InnovestX rate


@dataclass
class TradeResult:
    signal_id: str
    symbol: str
    source: str
    entry_date: str
    exit_date: str
    days_held: int
    entry_price: float
    exit_price: float
    initial_risk: float
    realized_r: float
    realized_pnl: float
    peak_mfe_r: float
    peak_mae_r: float
    exit_reason: str


def run_replay(
    db_path: Path,
    config: ExitConfig,
    min_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    min_scores = min_scores or {
        "thai-swing-dip": 80.0,
        "thai-swing-momentum": 75.0,
        "vcp-screener": 70.0,
    }
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Fetch signals
    signals = conn.execute(
        """SELECT * FROM signal_ledger 
           WHERE market='TH' AND entry_price IS NOT NULL AND entry_price > 0
           ORDER BY signal_date ASC, raw_score DESC"""
    ).fetchall()

    # Pre-cache price bars: symbol -> list of dicts sorted by date
    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    bar_rows = conn.execute(
        "SELECT symbol, date, open, high, low, close, volume FROM price_bar ORDER BY symbol, date ASC"
    ).fetchall()
    conn.close()

    for b in bar_rows:
        if b["open"] is not None and b["high"] is not None and b["low"] is not None and b["close"] is not None:
            bars_by_symbol.setdefault(b["symbol"], []).append(dict(b))

    results: list[TradeResult] = []
    # To prevent multiple overlapping trades in same symbol on same day
    active_symbols: dict[str, str] = {}  # symbol -> exit_date

    for sig in signals:
        src = sig["source_skill"]
        score = sig["raw_score"] or 0.0
        req_score = min_scores.get(src, 75.0)
        if score < req_score:
            continue

        sym = sig["symbol"]
        sig_date = sig["signal_date"]
        entry = float(sig["entry_price"])
        stop = float(sig["stop_price"]) if sig["stop_price"] else entry * 0.95
        risk = entry - stop
        if risk <= 0:
            risk = entry * 0.05
            stop = entry - risk

        # Account sizing: 30,000 THB account, 1% risk = 300 THB risk per trade
        risk_thb = 300.0
        shares = int(risk_thb / risk)
        shares = max(100, (shares // 100) * 100)  # board lot 100
        # Cap position size to 20% of account = 6,000 THB
        if shares * entry > 6000.0:
            shares = max(100, int(6000.0 / entry // 100) * 100)
        initial_risk_thb = shares * risk

        target = entry + (risk * config.target_r)

        bars = bars_by_symbol.get(sym, [])
        # Find bars after signal_date
        sub_bars = [b for b in bars if b["date"] >= sig_date]
        if len(sub_bars) < 2:
            continue

        # If already holding this symbol from earlier signal, skip
        if sym in active_symbols and active_symbols[sym] >= sub_bars[1]["date"]:
            continue

        # Trade entered at Open of the next bar after signal
        entry_bar = sub_bars[1]
        actual_entry = float(entry_bar["open"]) if entry_bar["open"] else entry
        actual_stop = actual_entry - risk
        actual_target = actual_entry + (risk * config.target_r)

        stop_price = actual_stop
        peak_high = actual_entry
        trough_low = actual_entry

        trade_bars = sub_bars[1:]
        closed = False
        exit_bar = trade_bars[-1]
        exit_price = float(exit_bar["close"])
        exit_reason = "end_of_data"

        for d_idx, b in enumerate(trade_bars):
            days_held = d_idx
            o = float(b["open"])
            h = float(b["high"])
            l = float(b["low"])
            c = float(b["close"])

            peak_high = max(peak_high, h)
            trough_low = min(trough_low, l)
            mfe_gain = peak_high - actual_entry
            mfe_r = mfe_gain / risk if risk > 0 else 0.0

            # 1. Evaluate MFE Ratchet Stop
            if config.use_ratchet and config.ratchet_tiers:
                for trigger_r, lock_r in config.ratchet_tiers:
                    if mfe_r >= trigger_r:
                        cand_stop = actual_entry + (risk * lock_r)
                        if cand_stop > stop_price:
                            stop_price = cand_stop

            # 2. Check Intraday Stop Hit
            if l <= stop_price:
                # Execution at stop (or open if gap down)
                exit_price = min(o, stop_price)
                exit_reason = "closed_ratchet" if (stop_price > actual_stop + 1e-4) else "closed_stop"
                exit_bar = b
                closed = True
                break

            # 3. Check Intraday Target Hit
            if h >= actual_target:
                exit_price = max(o, actual_target)
                exit_reason = "closed_target"
                exit_bar = b
                closed = True
                break

            # 4. Check Velocity / Momentum Decay Stall
            curr_r = (c - actual_entry) / risk if risk > 0 else 0.0
            stall_limit = config.velocity_stall_days if "momentum" in src else (config.velocity_stall_days + 1)
            if config.use_velocity_stall and days_held >= stall_limit and mfe_r < config.velocity_min_mfe_r and curr_r <= 0.0:
                exit_price = c
                exit_reason = "closed_stalled"
                exit_bar = b
                closed = True
                break

            # 5. Check Time Stop
            if days_held >= config.max_hold_days and curr_r < config.time_stop_min_r:
                exit_price = c
                exit_reason = "closed_time"
                exit_bar = b
                closed = True
                break

        # Calculate PnL & R
        gross_pnl = (exit_price - actual_entry) * shares
        entry_cost = actual_entry * shares * (config.commission_bps / 10000.0)
        exit_cost = exit_price * shares * (config.commission_bps / 10000.0)
        net_pnl = gross_pnl - entry_cost - exit_cost
        realized_r = net_pnl / initial_risk_thb if initial_risk_thb > 0 else 0.0

        peak_mfe_r = (peak_high - actual_entry) / risk if risk > 0 else 0.0
        peak_mae_r = (actual_entry - trough_low) / risk if risk > 0 else 0.0

        days_count = (trade_bars.index(exit_bar) if exit_bar in trade_bars else len(trade_bars) - 1)

        active_symbols[sym] = exit_bar["date"]
        results.append(
            TradeResult(
                signal_id=sig["signal_id"],
                symbol=sym,
                source=src,
                entry_date=entry_bar["date"],
                exit_date=exit_bar["date"],
                days_held=days_count,
                entry_price=actual_entry,
                exit_price=exit_price,
                initial_risk=initial_risk_thb,
                realized_r=realized_r,
                realized_pnl=net_pnl,
                peak_mfe_r=peak_mfe_r,
                peak_mae_r=peak_mae_r,
                exit_reason=exit_reason,
            )
        )

    # Compute Summary Stats
    total = len(results)
    if total == 0:
        return {"config": config.name, "total_trades": 0}

    wins = [r for r in results if r.realized_r > 0]
    losses = [r for r in results if r.realized_r <= 0]
    win_rate = len(wins) / total * 100.0
    net_r = sum(r.realized_r for r in results)
    net_pnl = sum(r.realized_pnl for r in results)
    avg_win_r = (sum(r.realized_r for r in wins) / len(wins)) if wins else 0.0
    avg_loss_r = (sum(r.realized_r for r in losses) / len(losses)) if losses else 0.0

    # Profit Factor
    sum_win_thb = sum(r.realized_pnl for r in wins)
    sum_loss_thb = abs(sum(r.realized_pnl for r in losses)) if losses else 1.0
    profit_factor = (sum_win_thb / sum_loss_thb) if sum_loss_thb > 0 else 999.0

    # Capture Efficiency
    win_mfe_sum = sum(r.peak_mfe_r for r in wins)
    win_r_sum = sum(r.realized_r for r in wins)
    capture_eff = (win_r_sum / win_mfe_sum * 100.0) if win_mfe_sum > 0 else 0.0

    # Exit reason counts
    by_reason: dict[str, int] = {}
    for r in results:
        by_reason[r.exit_reason] = by_reason.get(r.exit_reason, 0) + 1

    return {
        "name": config.name,
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(win_rate, 1),
        "net_realized_r": round(net_r, 2),
        "net_pnl_thb": round(net_pnl, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_win_r": round(avg_win_r, 2),
        "avg_loss_r": round(avg_loss_r, 2),
        "capture_efficiency_pct": round(capture_eff, 1),
        "avg_days_held": round(sum(r.days_held for r in results) / total, 1),
        "by_exit_reason": by_reason,
    }


def main():
    db = DEFAULT_DB
    print(f"Replaying historical signals from {db}...")
    
    # 1. Baseline: Old configuration (No ratchet, no velocity stall, static 2R, 15d time stop)
    old_cfg = ExitConfig(
        name="Baseline (Old System: Static 2R, No Ratchet, No Stall Exit)",
        target_r=2.0,
        use_ratchet=False,
        use_velocity_stall=False,
        max_hold_days=15,
        time_stop_min_r=-0.5,
    )
    
    # 2. New Config: Institutional Multi-Tier MFE Ratchet + Velocity Stall
    new_cfg = ExitConfig(
        name="New System (MFE Ratchet + Velocity Stall Exit + Target 2R)",
        target_r=2.0,
        use_ratchet=True,
        ratchet_tiers=[[0.8, -0.3], [1.2, 0.15], [1.8, 0.8]],
        use_velocity_stall=True,
        velocity_stall_days=3,
        velocity_min_mfe_r=0.30,
        max_hold_days=10,
        time_stop_min_r=-0.5,
    )

    # 3. Dynamic Swing Config (Adaptive 1.5R target with quick profit locking)
    adaptive_cfg = ExitConfig(
        name="Adaptive Fast Swing (Target 1.5R + Tight Ratchet + 3d Stall)",
        target_r=1.5,
        use_ratchet=True,
        ratchet_tiers=[[0.7, -0.2], [1.0, 0.20], [1.4, 0.70]],
        use_velocity_stall=True,
        velocity_stall_days=3,
        velocity_min_mfe_r=0.25,
        max_hold_days=8,
        time_stop_min_r=-0.3,
    )

    scenarios = [old_cfg, new_cfg, adaptive_cfg]
    summary = []
    for cfg in scenarios:
        res = run_replay(db, cfg)
        summary.append(res)

    print("\n" + "=" * 80)
    print("      HISTORICAL REPLAY & BACKTEST COMPARISON (Thai Market July-Sept 2026)")
    print("=" * 80)
    for s in summary:
        print(f"\nConfiguration: {s['name']}")
        print(f"  Trades Executed   : {s['total_trades']} ({s['wins']}W / {s['losses']}L)")
        print(f"  Win Rate          : {s['win_rate_pct']}%")
        print(f"  Net Realized R    : {s['net_realized_r']:+.2f}R")
        print(f"  Net PnL (THB)     : {s['net_pnl_thb']:+,.2f} THB")
        print(f"  Profit Factor     : {s['profit_factor']}")
        print(f"  Avg Win / Avg Loss: +{s['avg_win_r']}R / {s['avg_loss_r']}R")
        print(f"  Capture Efficiency: {s['capture_efficiency_pct']}%")
        print(f"  Avg Holding Period: {s['avg_days_held']} days")
        print(f"  Exit Distribution : {s['by_exit_reason']}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
