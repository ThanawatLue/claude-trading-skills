"""Expanded Parameter Sweep for Historical Exit Engine Replay.

Tests multiple variations to discover the mathematically and statistically optimal
exit rules for Thai equity swing trading.
"""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "state" / "vm_market_cache.db" if (BASE_DIR / "state" / "vm_market_cache.db").exists() else BASE_DIR / "state" / "market_cache.db"


@dataclass
class ReplayConfig:
    name: str
    target_r: float = 2.0
    use_scale_out: bool = False  # 50% take profit at target_1, 50% trail/target_2
    scale_out_r: float = 1.0
    use_ratchet: bool = True
    ratchet_tiers: list[list[float]] = field(default_factory=list)
    use_velocity_stall: bool = True
    velocity_stall_days: int = 4
    velocity_min_mfe_r: float = 0.30
    max_hold_days: int = 15
    time_stop_min_r: float = -0.5
    min_score_dip: float = 80.0
    min_score_momo: float = 75.0
    commission_bps: float = 21.692


def run_sweep(db_path: Path, configs: list[ReplayConfig]):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    signals = conn.execute(
        """SELECT * FROM signal_ledger 
           WHERE market='TH' AND entry_price IS NOT NULL AND entry_price > 0
           ORDER BY signal_date ASC, raw_score DESC"""
    ).fetchall()

    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    bar_rows = conn.execute(
        "SELECT symbol, date, open, high, low, close, volume FROM price_bar ORDER BY symbol, date ASC"
    ).fetchall()
    conn.close()

    for b in bar_rows:
        if b["open"] is not None and b["high"] is not None and b["low"] is not None and b["close"] is not None:
            bars_by_symbol.setdefault(b["symbol"], []).append(dict(b))

    print(f"Loaded {len(signals)} signals, {len(bar_rows)} price bars across {len(bars_by_symbol)} symbols.\n")

    results_table = []

    for cfg in configs:
        active_symbols: dict[str, str] = {}
        trade_records = []

        for sig in signals:
            src = sig["source_skill"]
            score = sig["raw_score"] or 0.0
            
            # Filter score
            if "dip" in src and score < cfg.min_score_dip:
                continue
            if "momentum" in src and score < cfg.min_score_momo:
                continue
            if "vcp" in src and score < 70.0:
                continue

            sym = sig["symbol"]
            sig_date = sig["signal_date"]
            entry = float(sig["entry_price"])
            stop = float(sig["stop_price"]) if sig["stop_price"] else entry * 0.95
            risk = entry - stop
            if risk <= 0:
                risk = entry * 0.05
                stop = entry - risk

            # 30,000 THB account, 300 THB risk (1%)
            risk_thb = 300.0
            shares = int(risk_thb / risk)
            shares = max(100, (shares // 100) * 100)
            if shares * entry > 6000.0:
                shares = max(100, int(6000.0 / entry // 100) * 100)
            initial_risk_thb = shares * risk

            bars = bars_by_symbol.get(sym, [])
            sub_bars = [b for b in bars if b["date"] >= sig_date]
            if len(sub_bars) < 2:
                continue

            if sym in active_symbols and active_symbols[sym] >= sub_bars[1]["date"]:
                continue

            entry_bar = sub_bars[1]
            actual_entry = float(entry_bar["open"]) if entry_bar["open"] else entry
            actual_stop = actual_entry - risk
            target_1 = actual_entry + (risk * cfg.scale_out_r) if cfg.use_scale_out else actual_entry + (risk * cfg.target_r)
            target_final = actual_entry + (risk * cfg.target_r)

            stop_price = actual_stop
            peak_high = actual_entry
            trade_bars = sub_bars[1:]
            
            scaled_out = False
            scale_out_price = 0.0
            scale_out_pnl = 0.0

            exit_price = float(trade_bars[-1]["close"])
            exit_reason = "end_of_data"
            exit_bar = trade_bars[-1]

            for d_idx, b in enumerate(trade_bars):
                o, h, l, c = float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])
                peak_high = max(peak_high, h)
                mfe_r = (peak_high - actual_entry) / risk if risk > 0 else 0.0

                # 1. Evaluate Ratchet Tiers
                if cfg.use_ratchet and cfg.ratchet_tiers:
                    for trigger_r, lock_r in cfg.ratchet_tiers:
                        if mfe_r >= trigger_r:
                            cand = actual_entry + (risk * lock_r)
                            if cand > stop_price:
                                stop_price = cand

                # 2. Scale-out Check (Partial TP 50%)
                if cfg.use_scale_out and not scaled_out and h >= target_1:
                    scaled_out = True
                    scale_out_price = max(o, target_1)
                    # When scaling out 50%, move stop to Breakeven (+0.1R to cover fees)
                    stop_price = max(stop_price, actual_entry + (risk * 0.1))

                # 3. Stop check
                if l <= stop_price:
                    exit_price = min(o, stop_price)
                    exit_reason = "closed_ratchet" if (stop_price > actual_stop + 1e-4) else "closed_stop"
                    exit_bar = b
                    break

                # 4. Final Target check
                if h >= target_final:
                    exit_price = max(o, target_final)
                    exit_reason = "closed_target"
                    exit_bar = b
                    break

                # 5. Velocity Stall check
                curr_r = (c - actual_entry) / risk if risk > 0 else 0.0
                stall_limit = cfg.velocity_stall_days if "momentum" in src else (cfg.velocity_stall_days + 1)
                if cfg.use_velocity_stall and d_idx >= stall_limit and mfe_r < cfg.velocity_min_mfe_r and curr_r <= 0.0:
                    exit_price = c
                    exit_reason = "closed_stalled"
                    exit_bar = b
                    break

                # 6. Time Stop check
                if d_idx >= cfg.max_hold_days and curr_r < cfg.time_stop_min_r:
                    exit_price = c
                    exit_reason = "closed_time"
                    exit_bar = b
                    break

            # Calculate combined PnL
            fee_rate = cfg.commission_bps / 10000.0
            if cfg.use_scale_out and scaled_out:
                half_shares = shares // 2
                rem_shares = shares - half_shares
                pnl_1 = (scale_out_price - actual_entry) * half_shares - (actual_entry * half_shares * fee_rate) - (scale_out_price * half_shares * fee_rate)
                pnl_2 = (exit_price - actual_entry) * rem_shares - (actual_entry * rem_shares * fee_rate) - (exit_price * rem_shares * fee_rate)
                net_pnl = pnl_1 + pnl_2
            else:
                gross = (exit_price - actual_entry) * shares
                cost = (actual_entry * shares * fee_rate) + (exit_price * shares * fee_rate)
                net_pnl = gross - cost

            realized_r = net_pnl / initial_risk_thb if initial_risk_thb > 0 else 0.0
            active_symbols[sym] = exit_bar["date"]

            trade_records.append({
                "realized_r": realized_r,
                "realized_pnl": net_pnl,
                "exit_reason": exit_reason,
                "days": trade_bars.index(exit_bar) if exit_bar in trade_bars else len(trade_bars) - 1,
            })

        # Calculate metrics
        total = len(trade_records)
        wins = [t for t in trade_records if t["realized_r"] > 0]
        losses = [t for t in trade_records if t["realized_r"] <= 0]
        win_rate = (len(wins) / total * 100.0) if total else 0.0
        net_r = sum(t["realized_r"] for t in trade_records)
        net_pnl = sum(t["realized_pnl"] for t in trade_records)
        sum_win_thb = sum(t["realized_pnl"] for t in wins)
        sum_loss_thb = abs(sum(t["realized_pnl"] for t in losses)) if losses else 1.0
        profit_factor = (sum_win_thb / sum_loss_thb) if sum_loss_thb > 0 else 999.0
        avg_days = sum(t["days"] for t in trade_records) / total if total else 0.0

        results_table.append({
            "name": cfg.name,
            "trades": total,
            "wins": len(wins),
            "win_rate": round(win_rate, 1),
            "net_r": round(net_r, 2),
            "net_pnl": round(net_pnl, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_days": round(avg_days, 1),
        })

    print(f"{'Configuration':<52} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6} {'AvgDays':>7}")
    print("-" * 105)
    for r in results_table:
        print(f"{r['name']:<52} {r['trades']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['profit_factor']:>6.2f} {r['avg_days']:>6.1f}d")


if __name__ == "__main__":
    configs = [
        ReplayConfig(
            name="1. Baseline Old (No Ratchet, Target 2.0R, 15d)",
            target_r=2.0,
            use_ratchet=False,
            use_velocity_stall=False,
            max_hold_days=15,
        ),
        ReplayConfig(
            name="2. Tight Ratchet (0.8R->-0.3R, 1.2R->0.15R, 3d Stall)",
            target_r=2.0,
            use_ratchet=True,
            ratchet_tiers=[[0.8, -0.3], [1.2, 0.15], [1.8, 0.8]],
            use_velocity_stall=True,
            velocity_stall_days=3,
        ),
        ReplayConfig(
            name="3. Wide Ratchet (1.2R->0.1R Breakeven, 1.8R->0.8R)",
            target_r=2.0,
            use_ratchet=True,
            ratchet_tiers=[[1.2, 0.10], [1.8, 0.80]],
            use_velocity_stall=True,
            velocity_stall_days=4,
        ),
        ReplayConfig(
            name="4. Pure Breakeven Ratchet (1.0R->0.05R BE only)",
            target_r=1.8,
            use_ratchet=True,
            ratchet_tiers=[[1.0, 0.05]],
            use_velocity_stall=False,
            max_hold_days=10,
        ),
        ReplayConfig(
            name="5. 50% Scale-Out at 1.0R + 50% at 2.0R (Minervini Scale)",
            target_r=2.0,
            use_scale_out=True,
            scale_out_r=1.0,
            use_ratchet=False,
            use_velocity_stall=True,
            velocity_stall_days=4,
        ),
        ReplayConfig(
            name="6. High Quality Filter (Dip>=85, Momo>=80) + BE Ratchet",
            target_r=1.8,
            use_ratchet=True,
            ratchet_tiers=[[1.1, 0.10]],
            use_velocity_stall=True,
            velocity_stall_days=4,
            min_score_dip=85.0,
            min_score_momo=80.0,
        ),
        ReplayConfig(
            name="7. High Quality + 50% Scale-Out (1.0R) + 50% (2.0R)",
            target_r=2.0,
            use_scale_out=True,
            scale_out_r=1.0,
            use_ratchet=False,
            use_velocity_stall=True,
            velocity_stall_days=4,
            min_score_dip=85.0,
            min_score_momo=80.0,
        ),
    ]

    run_sweep(DB_PATH, configs)
