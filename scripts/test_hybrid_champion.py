"""Test the Unified Hybrid Champion:
1. Dynamic ATR clamp: stop = min(6.5%, max(5.0%, 1.5 * ATR14))
2. Early Fakeout exit (Day 1-2 vol collapse & red)
3. Velocity Stall (Day 4)
4. Target 2.0R vs 2.2R
5. Source-specific RS filter (Momentum filtered, Dip preserved)
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(r"d:\ex_work\tong_trading\state\vm_market_cache.db")

def load_data():
    conn = sqlite3.connect(str(DB_PATH))
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

    set_bars = bars_by_symbol.get("^SET.BK", [])
    set_ret_by_date = {}
    for i in range(20, len(set_bars)):
        p_now = float(set_bars[i]["close"])
        p_past = float(set_bars[i - 20]["close"])
        set_ret_by_date[set_bars[i]["date"]] = (p_now - p_past) / p_past * 100.0

    return signals, bars_by_symbol, atr_by_symbol, set_ret_by_date

def sim_hybrid(target_r, use_fakeout, use_momo_rs, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date):
    active_symbols = {}
    trades = []
    risk_budget = 300.0
    max_pos_val = 6000.0
    fee_rate = 21.692 / 10000.0
    sources = ["thai-swing-momentum", "thai-swing-dip", "vcp-screener"]
    min_scores = {"thai-swing-momentum": 78.0, "thai-swing-dip": 80.0, "vcp-screener": 70.0}

    for sig in signals:
        src = sig["source_skill"]
        if src not in sources:
            continue
        score = float(sig["raw_score"] or 0.0)
        if score < min_scores.get(src, 75.0):
            continue

        sym = sig["symbol"]
        sig_date = sig["signal_date"]
        entry = float(sig["entry_price"])

        bars = bars_by_symbol.get(sym, [])
        sub_bars = [b for b in bars if b["date"] >= sig_date]
        if len(sub_bars) < 2:
            continue

        if sym in active_symbols and active_symbols[sym] >= sub_bars[1]["date"]:
            continue

        entry_bar = sub_bars[1]
        actual_entry = float(entry_bar["open"]) if entry_bar["open"] else entry

        # Momentum RS filter (only apply to momentum/vcp, not dip)
        if use_momo_rs and src in ("thai-swing-momentum", "vcp-screener"):
            sym_full_bars = bars_by_symbol.get(sym, [])
            bar_idx = next((i for i, b in enumerate(sym_full_bars) if b["date"] == entry_bar["date"]), -1)
            if bar_idx >= 20:
                stock_ret = (float(sym_full_bars[bar_idx]["close"]) - float(sym_full_bars[bar_idx - 20]["close"])) / float(sym_full_bars[bar_idx - 20]["close"]) * 100.0
                set_ret = set_ret_by_date.get(entry_bar["date"], 0.0)
                if (stock_ret - set_ret) < -2.0:
                    continue

        # Dynamic ATR Stop Clamp
        sym_full_bars = bars_by_symbol.get(sym, [])
        bar_idx = next((i for i, b in enumerate(sym_full_bars) if b["date"] == entry_bar["date"]), -1)
        atr_pct = atr_by_symbol.get(sym, [])[bar_idx] if (bar_idx >= 0 and bar_idx < len(atr_by_symbol.get(sym, []))) else None
        if atr_pct is not None and atr_pct > 0:
            effective_stop_pct = max(5.0, 1.5 * atr_pct)
            effective_stop_pct = min(6.5, effective_stop_pct)
        else:
            effective_stop_pct = 5.0

        risk_dist = actual_entry * (effective_stop_pct / 100.0)
        actual_stop = actual_entry - risk_dist
        risk = actual_entry - actual_stop
        if risk <= 0:
            continue

        t_price = actual_entry + (risk * target_r)

        shares = int(risk_budget / risk)
        shares = max(100, (shares // 100) * 100)
        if shares * actual_entry > max_pos_val:
            shares = max(100, int(max_pos_val / actual_entry // 100) * 100)
        initial_risk_thb = shares * risk

        trade_bars = sub_bars[1:]
        stop_price = actual_stop
        peak_high = actual_entry
        exit_bar = trade_bars[-1]
        exit_price = float(exit_bar["close"])
        exit_reason = "end_of_data"
        entry_vol = float(entry_bar["volume"]) if entry_bar.get("volume") else 1.0

        for d_idx, b in enumerate(trade_bars):
            o, h, low_val, c = float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])
            v = float(b["volume"]) if b.get("volume") else 0.0
            peak_high = max(peak_high, h)
            mfe_r = (peak_high - actual_entry) / risk
            curr_r = (c - actual_entry) / risk

            if low_val <= stop_price:
                exit_price = min(o, stop_price)
                exit_reason = "stop"
                exit_bar = b
                break

            if h >= t_price:
                exit_price = max(o, t_price)
                exit_reason = "target"
                exit_bar = b
                break

            # Early Fakeout / Volume Collapse (Day 1 or 2)
            if use_fakeout and d_idx in (0, 1):
                if entry_vol > 0 and (v / entry_vol) < 0.40 and curr_r < 0.0 and mfe_r < 0.20:
                    exit_price = c
                    exit_reason = "early_fakeout"
                    exit_bar = b
                    break

            # Velocity Stall at 4 days
            if d_idx >= 4 and mfe_r < 0.30 and curr_r <= 0.0:
                exit_price = c
                exit_reason = "stalled"
                exit_bar = b
                break

            if d_idx >= 10 and curr_r < -0.5:
                exit_price = c
                exit_reason = "time"
                exit_bar = b
                break

        gross = (exit_price - actual_entry) * shares
        costs = (actual_entry * shares * fee_rate) + (exit_price * shares * fee_rate)
        net_pnl = gross - costs
        realized_r = net_pnl / initial_risk_thb if initial_risk_thb > 0 else 0.0
        active_symbols[sym] = exit_bar["date"]

        trades.append({
            "realized_r": realized_r,
            "net_pnl": net_pnl,
            "reason": exit_reason,
        })

    wins = [t for t in trades if t["realized_r"] > 0]
    losses = [t for t in trades if t["realized_r"] <= 0]
    win_rate = len(wins) / len(trades) * 100.0 if trades else 0
    net_r = sum(t["realized_r"] for t in trades)
    net_pnl = sum(t["net_pnl"] for t in trades)
    sum_win = sum(t["net_pnl"] for t in wins)
    sum_loss = abs(sum(t["net_pnl"] for t in losses)) if losses else 1.0
    pf = sum_win / sum_loss if sum_loss > 0 else 99.0
    reasons = {}
    for t in trades:
        reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1

    return {
        "trades": len(trades),
        "win_rate": win_rate,
        "net_r": net_r,
        "net_pnl": net_pnl,
        "pf": pf,
        "reasons": reasons,
    }

def main():
    signals, bars_by_symbol, atr_by_symbol, set_ret_by_date = load_data()
    print("=" * 110)
    print("                    UNIFIED HYBRID SUITE: EMPIRICAL PERFORMANCE")
    print("=" * 110)
    print(f"{'Configuration':<55} {'Trades':>6} {'WinRate':>8} {'Net R':>8} {'Net PnL (THB)':>14} {'PF':>6} {'Exit Reasons'}")
    print("-" * 110)

    configs = [
        (2.0, False, False, "DynATR 1.5x (Floor 5%) | Target 2.0R | Stall 4d"),
        (2.0, True, False, "DynATR + Early Fakeout Vol<40% | Target 2.0R"),
        (2.0, True, True, "DynATR + Early Fakeout + Momo RS Filter | Target 2.0R"),
        (2.2, False, False, "DynATR 1.5x (Floor 5%) | Target 2.2R | Stall 4d"),
        (2.2, True, False, "DynATR + Early Fakeout Vol<40% | Target 2.2R"),
        (2.2, True, True, "DynATR + Early Fakeout + Momo RS Filter | Target 2.2R"),
    ]

    for t_r, use_fake, use_rs, lbl in configs:
        r = sim_hybrid(t_r, use_fake, use_rs, signals, bars_by_symbol, atr_by_symbol, set_ret_by_date)
        reasons_str = ", ".join(f"{k}:{v}" for k, v in r["reasons"].items())
        print(f"{lbl:<55} {r['trades']:>6} {r['win_rate']:>7.1f}% {r['net_r']:>+7.2f}R {r['net_pnl']:>+13,.2f} {r['pf']:>6.2f}  {reasons_str}")

if __name__ == "__main__":
    main()
