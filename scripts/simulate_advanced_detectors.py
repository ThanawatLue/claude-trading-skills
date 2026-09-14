"""Advanced Strategy & Exit Engine Optimization Framework.

Performs systematic multi-dimensional grid search across historical data (July-Sept 2026)
to evaluate:
1. Dynamic ATR Risk Clamping: stop = max(fee_floor, k * ATR14) vs static clamp
2. Early Fakeout & Volume Collapse Detector: exiting dead breakouts on Day 1-2
3. Sector Relative Strength Alignment: filtering or prioritizing leading sectors
4. Native Scale-Out Engine: 50% TP1, 50% TP2 + Breakeven stop vs Single-Exit
"""

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DB_PATH = Path(r"d:\ex_work\tong_trading\state\vm_market_cache.db")


@dataclass
class AdvancedStrategy:
    name: str
    allowed_sources: list[str] = field(default_factory=lambda: ["thai-swing-momentum", "thai-swing-dip", "vcp-screener"])
    min_scores: dict[str, float] = field(default_factory=lambda: {"thai-swing-momentum": 78.0, "thai-swing-dip": 80.0, "vcp-screener": 70.0})

    # ATR Stop Sizing
    use_dynamic_atr: bool = False
    atr_multiplier: float = 1.5     # Stop = max(fee_floor_pct, k * ATR_pct)
    fee_floor_pct: float = 4.0      # Minimum stop % to avoid fee drag
    static_min_stop_pct: float = 5.0
    max_stop_pct: float = 6.5

    # Exit Architecture
    architecture: str = "single"    # 'single' or 'scale_out'
    target_1_r: float = 2.0        # Target 1 (or sole target if single)
    target_2_r: float = 2.5        # Target 2 (only if scale_out)

    # Early Fakeout / Volume Collapse
    use_early_fakeout: bool = False
    fakeout_vol_ratio: float = 0.40 # If Day 1/2 volume < 0.40x Day 0
    fakeout_max_mfe: float = 0.20   # And MFE < 0.20R

    # Velocity Stall Exit
    use_velocity_stall: bool = True
    stall_days: int = 4
    stall_min_mfe: float = 0.30

    # Sector RS Filter
    use_sector_filter: bool = False
    min_sector_relative_return: float = 0.0 # Sector 20d return - SET 20d return >= 0

    max_hold_days: int = 10
    time_stop_min_r: float = -0.5
    account_size: float = 30000.0
    risk_pct: float = 1.0          # 1% risk = 300 THB
    max_pos_pct: float = 20.0      # 20% max pos = 6,000 THB
    commission_bps: float = 21.692 # InnovestX 21.692 bps per side


def load_dataset(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    raw_signals = conn.execute(
        """SELECT signal_id, symbol, market, source_skill, signal_date,
                  raw_score, entry_price, stop_price, target_price, payload_json
           FROM signal_ledger
           WHERE market='TH' AND entry_price IS NOT NULL AND entry_price > 0
           ORDER BY signal_date ASC, raw_score DESC"""
    ).fetchall()

    signals = []
    for r in raw_signals:
        item = dict(r)
        sector = ""
        if item.get("payload_json"):
            try:
                p = json.loads(item["payload_json"])
                sector = p.get("sector") or ""
            except Exception:
                pass
        item["sector"] = sector
        signals.append(item)

    bar_rows = conn.execute(
        "SELECT symbol, date, open, high, low, close, volume FROM price_bar ORDER BY symbol, date ASC"
    ).fetchall()
    conn.close()

    bars_by_symbol = {}
    for b in bar_rows:
        if b["open"] is not None and b["high"] is not None and b["low"] is not None and b["close"] is not None:
            bars_by_symbol.setdefault(b["symbol"], []).append(dict(b))

    # Precalculate ATR(14) for each bar in each symbol
    atr_by_symbol = {}
    for sym, bars in bars_by_symbol.items():
        atr_list = [None] * len(bars)
        tr_list = []
        for i in range(len(bars)):
            h = float(bars[i]["high"])
            low_val = float(bars[i]["low"])
            if i == 0:
                tr = h - low_val
            else:
                prev_c = float(bars[i - 1]["close"])
                tr = max(h - low_val, abs(h - prev_c), abs(low_val - prev_c))
            tr_list.append(tr)
            if len(tr_list) >= 14:
                atr = sum(tr_list[-14:]) / 14.0
                atr_pct = (atr / float(bars[i]["close"])) * 100.0
                atr_list[i] = atr_pct
        atr_by_symbol[sym] = atr_list

    # Precalculate Sector 20-day returns vs SET
    # 1. Index 20d return by date
    set_bars = bars_by_symbol.get("^SET.BK", [])
    set_ret_by_date = {}
    for i in range(20, len(set_bars)):
        p_now = float(set_bars[i]["close"])
        p_past = float(set_bars[i - 20]["close"])
        set_ret_by_date[set_bars[i]["date"]] = (p_now - p_past) / p_past * 100.0

    return signals, bars_by_symbol, atr_by_symbol, set_ret_by_date


def simulate(strat: AdvancedStrategy, signals: list[dict], bars_by_symbol: dict, atr_by_symbol: dict, set_ret_by_date: dict) -> dict[str, Any]:
    active_symbols: dict[str, str] = {}
    trades = []
    risk_budget = strat.account_size * (strat.risk_pct / 100.0)
    max_pos_val = strat.account_size * (strat.max_pos_pct / 100.0)
    fee_rate = strat.commission_bps / 10000.0

    for sig in signals:
        src = sig["source_skill"]
        if src not in strat.allowed_sources:
            continue

        score = float(sig["raw_score"] or 0.0)
        req_score = strat.min_scores.get(src, 75.0)
        if score < req_score:
            continue

        sym = sig["symbol"]
        sig_date = sig["signal_date"]
        entry = float(sig["entry_price"])
        raw_stop = float(sig["stop_price"]) if sig["stop_price"] else entry * 0.95

        bars = bars_by_symbol.get(sym, [])
        sub_bars = [b for b in bars if b["date"] >= sig_date]
        if len(sub_bars) < 2:
            continue

        # Prevent concurrent duplicate position
        if sym in active_symbols and active_symbols[sym] >= sub_bars[1]["date"]:
            continue

        entry_bar = sub_bars[1]
        actual_entry = float(entry_bar["open"]) if entry_bar["open"] else entry

        # Sector RS filter
        if strat.use_sector_filter and sig.get("sector"):
            # If stock 20d return < SET 20d return, filter out
            # Look up past 20 bars
            sym_full_bars = bars_by_symbol.get(sym, [])
            bar_idx = next((i for i, b in enumerate(sym_full_bars) if b["date"] == entry_bar["date"]), -1)
            if bar_idx >= 20:
                stock_ret = (float(sym_full_bars[bar_idx]["close"]) - float(sym_full_bars[bar_idx - 20]["close"])) / float(sym_full_bars[bar_idx - 20]["close"]) * 100.0
                set_ret = set_ret_by_date.get(entry_bar["date"], 0.0)
                if (stock_ret - set_ret) < strat.min_sector_relative_return:
                    continue

        # Stop loss calculation
        if strat.use_dynamic_atr:
            # Lookup ATR(14)
            sym_full_bars = bars_by_symbol.get(sym, [])
            bar_idx = next((i for i, b in enumerate(sym_full_bars) if b["date"] == entry_bar["date"]), -1)
            atr_pct = atr_by_symbol.get(sym, [])[bar_idx] if (bar_idx >= 0 and bar_idx < len(atr_by_symbol.get(sym, []))) else None
            if atr_pct is not None and atr_pct > 0:
                effective_stop_pct = max(strat.fee_floor_pct, strat.atr_multiplier * atr_pct)
                effective_stop_pct = min(strat.max_stop_pct, effective_stop_pct)
            else:
                effective_stop_pct = strat.fee_floor_pct
            risk_dist = actual_entry * (effective_stop_pct / 100.0)
            actual_stop = actual_entry - risk_dist
        else:
            raw_risk_pct = (entry - raw_stop) / entry * 100.0
            if raw_risk_pct < strat.static_min_stop_pct:
                risk_dist = actual_entry * (strat.static_min_stop_pct / 100.0)
            elif raw_risk_pct > strat.max_stop_pct:
                risk_dist = actual_entry * (strat.max_stop_pct / 100.0)
            else:
                risk_dist = (actual_entry - (actual_entry * (raw_stop / entry)))
            actual_stop = actual_entry - risk_dist

        risk = actual_entry - actual_stop
        if risk <= 0:
            continue

        # Position sizing (SET board lot = 100 shares)
        shares = int(risk_budget / risk)
        shares = max(100, (shares // 100) * 100)
        if shares * actual_entry > max_pos_val:
            shares = max(100, int(max_pos_val / actual_entry // 100) * 100)
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

        t1_price = actual_entry + (risk * strat.target_1_r)
        t2_price = actual_entry + (risk * strat.target_2_r)

        entry_vol = float(entry_bar["volume"]) if entry_bar.get("volume") else 1.0

        for d_idx, b in enumerate(trade_bars):
            o, h, low_val, c = float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])
            v = float(b["volume"]) if b.get("volume") else 0.0
            peak_high = max(peak_high, h)
            mfe_r = (peak_high - actual_entry) / risk
            curr_r = (c - actual_entry) / risk

            if strat.architecture == "scale_out":
                # Partial scale-out at T1
                if not scaled_out and h >= t1_price:
                    scaled_out = True
                    scale_price = max(o, t1_price)
                    half_shares = shares // 2
                    scale_pnl = (scale_price - actual_entry) * half_shares - (actual_entry * half_shares * fee_rate) - (scale_price * half_shares * fee_rate)
                    # Move remaining stop to Breakeven (+0.05R)
                    stop_price = max(stop_price, actual_entry + (risk * 0.05))

                # Stop hit
                if low_val <= stop_price:
                    exit_price = min(o, stop_price)
                    exit_reason = "ratchet_be" if stop_price > actual_stop + 1e-4 else "stop"
                    exit_bar = b
                    break

                # T2 hit
                if h >= t2_price:
                    exit_price = max(o, t2_price)
                    exit_reason = "target"
                    exit_bar = b
                    break
            else:
                # Single-Exit
                if low_val <= stop_price:
                    exit_price = min(o, stop_price)
                    exit_reason = "stop"
                    exit_bar = b
                    break

                if h >= t1_price:
                    exit_price = max(o, t1_price)
                    exit_reason = "target"
                    exit_bar = b
                    break

            # Early Fakeout / Volume Collapse check (Day 1 or 2)
            if strat.use_early_fakeout and d_idx in (0, 1):
                # If volume collapses to < fakeout_vol_ratio and price is in red and peak mfe is negligible
                if entry_vol > 0 and (v / entry_vol) < strat.fakeout_vol_ratio and curr_r < 0.0 and mfe_r < strat.fakeout_max_mfe:
                    exit_price = c
                    exit_reason = "early_fakeout"
                    exit_bar = b
                    break

            # Velocity Stall
            if strat.use_velocity_stall and d_idx >= strat.stall_days and mfe_r < strat.stall_min_mfe and curr_r <= 0.0:
                exit_price = c
                exit_reason = "stalled"
                exit_bar = b
                break

            # Max hold time stop
            if d_idx >= strat.max_hold_days and curr_r < strat.time_stop_min_r:
                exit_price = c
                exit_reason = "time"
                exit_bar = b
                break

        # Calculate Net PnL
        if strat.architecture == "scale_out" and scaled_out:
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
            "fees": (actual_entry * shares * fee_rate) + (exit_price * shares * fee_rate),
        })

    total = len(trades)
    if total == 0:
        return {"name": strat.name, "total": 0, "net_r": -999, "net_pnl": -999, "win_rate": 0, "pf": 0}

    wins = [t for t in trades if t["realized_r"] > 0]
    losses = [t for t in trades if t["realized_r"] <= 0]
    win_rate = len(wins) / total * 100.0
    net_r = sum(t["realized_r"] for t in trades)
    net_pnl = sum(t["net_pnl"] for t in trades)

    sum_win_thb = sum(t["net_pnl"] for t in wins)
    sum_loss_thb = abs(sum(t["net_pnl"] for t in losses)) if losses else 1.0
    pf = (sum_win_thb / sum_loss_thb) if sum_loss_thb > 0 else 99.0
    total_fees = sum(t["fees"] for t in trades)

    reasons = {}
    for t in trades:
        reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1

    return {
        "name": strat.name,
        "total": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "net_r": round(net_r, 2),
        "net_pnl": round(net_pnl, 2),
        "pf": round(pf, 2),
        "fees": round(total_fees, 2),
        "reasons": reasons,
        "trades": trades,
    }


def main():
    print(f"Loading data from {DB_PATH}...")
    signals, bars_by_symbol, atr_by_symbol, set_ret_by_date = load_dataset(DB_PATH)

    print("\n" + "=" * 115)
    print("                    GRID 1: DYNAMIC ATR STOP CLAMPING VS STATIC 5.0%")
    print("=" * 115)
    atr_results = []
    # Test Dynamic ATR parameters:
    for k in [1.2, 1.5, 1.8, 2.0]:
        for fee_floor in [3.5, 4.0, 4.5, 5.0]:
            name = f"Dynamic ATR | k={k}x | Floor={fee_floor}% | Target:2.0R | Stall:4d"
            strat = AdvancedStrategy(
                name=name,
                use_dynamic_atr=True,
                atr_multiplier=k,
                fee_floor_pct=fee_floor,
                target_1_r=2.0,
                use_velocity_stall=True,
                stall_days=4,
            )
            r = simulate(strat, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date)
            if r["total"] >= 10:
                atr_results.append(r)

    # Add Static 5.0% reference
    strat_static = AdvancedStrategy(
        name="Static Baseline | Stop>=5.0% | Target:2.0R | Stall:4d",
        use_dynamic_atr=False,
        static_min_stop_pct=5.0,
        target_1_r=2.0,
        use_velocity_stall=True,
        stall_days=4,
    )
    atr_results.append(simulate(strat_static, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date))

    atr_results.sort(key=lambda x: (x["net_pnl"], x["net_r"]), reverse=True)
    print(f"{'Rank':<5} {'Configuration':<62} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6}")
    print("-" * 115)
    for idx, r in enumerate(atr_results[:10], 1):
        print(f"{idx:<5} {r['name']:<62} {r['total']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}")

    print("\n" + "=" * 115)
    print("                    GRID 2: EARLY FAKEOUT / VOLUME COLLAPSE DETECTOR")
    print("=" * 115)
    fakeout_results = []
    best_atr = atr_results[0]
    print(f"Using top ATR model from Grid 1: {best_atr['name']}")
    for vol_ratio in [0.30, 0.40, 0.50, 0.60, 99.0]: # 99 = no fakeout check
        for max_mfe in [0.15, 0.25, 0.35]:
            f_label = f"Vol<{int(vol_ratio*100)}% & MFE<{max_mfe}R" if vol_ratio < 90 else "NoEarlyFakeout"
            name = f"Dynamic ATR | {f_label} | Stall:4d"
            strat = AdvancedStrategy(
                name=name,
                use_dynamic_atr=True,
                atr_multiplier=1.8,
                fee_floor_pct=4.5,
                target_1_r=2.0,
                use_early_fakeout=(vol_ratio < 90),
                fakeout_vol_ratio=vol_ratio,
                fakeout_max_mfe=max_mfe,
                use_velocity_stall=True,
                stall_days=4,
            )
            r = simulate(strat, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date)
            if r["total"] >= 10:
                fakeout_results.append(r)

    fakeout_results.sort(key=lambda x: (x["net_pnl"], x["net_r"]), reverse=True)
    print(f"{'Rank':<5} {'Configuration':<62} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6}")
    print("-" * 115)
    for idx, r in enumerate(fakeout_results[:8], 1):
        print(f"{idx:<5} {r['name']:<62} {r['total']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}")

    print("\n" + "=" * 115)
    print("                    GRID 3: SECTOR RS ALIGNMENT FILTER")
    print("=" * 115)
    sec_results = []
    for min_rel_ret in [-5.0, 0.0, 2.0, 5.0, 999.0]:
        s_label = f"Stock 20d >= SET + {min_rel_ret}%" if min_rel_ret < 900 else "NoSectorFilter"
        name = f"Dynamic ATR | {s_label}"
        strat = AdvancedStrategy(
            name=name,
            use_dynamic_atr=True,
            atr_multiplier=1.8,
            fee_floor_pct=4.5,
            target_1_r=2.0,
            use_sector_filter=(min_rel_ret < 900),
            min_sector_relative_return=min_rel_ret,
            use_velocity_stall=True,
            stall_days=4,
        )
        r = simulate(strat, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date)
        if r["total"] >= 5:
            sec_results.append(r)

    sec_results.sort(key=lambda x: (x["net_pnl"], x["net_r"]), reverse=True)
    print(f"{'Rank':<5} {'Configuration':<62} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6}")
    print("-" * 115)
    for idx, r in enumerate(sec_results, 1):
        print(f"{idx:<5} {r['name']:<62} {r['total']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}")

    print("\n" + "=" * 115)
    print("                    GRID 4: SCALE-OUT (50% T1, 50% T2) VS SINGLE-EXIT")
    print("=" * 115)
    scale_results = []
    for (t1, t2) in [(1.2, 2.0), (1.2, 2.5), (1.4, 2.2), (1.5, 2.5), (1.5, 3.0)]:
        name = f"Scale-Out | 50%@{t1}R + 50%@{t2}R | DynATR k=1.8 Flr=4.5%"
        strat = AdvancedStrategy(
            name=name,
            architecture="scale_out",
            use_dynamic_atr=True,
            atr_multiplier=1.8,
            fee_floor_pct=4.5,
            target_1_r=t1,
            target_2_r=t2,
            use_velocity_stall=True,
            stall_days=4,
        )
        r = simulate(strat, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date)
        if r["total"] >= 10:
            scale_results.append(r)

    scale_results.sort(key=lambda x: (x["net_pnl"], x["net_r"]), reverse=True)
    print(f"{'Rank':<5} {'Configuration':<62} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6}")
    print("-" * 115)
    for idx, r in enumerate(scale_results, 1):
        print(f"{idx:<5} {r['name']:<62} {r['total']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}")


if __name__ == "__main__":
    main()
