"""Comprehensive Historical Backtest & Simulation Engine.

Simulates real-world execution of Jules AI Fund and Scout across historical price bars
from SQLite cache (March 2025 - September 2026).

Compares 4 configurations:
1. Baseline Naive (Static 2.0R target, -1.0R stop, 15d time stop, No Intelligence filters)
2. Exit Safeguards Only (Two-Tier Scale-out + BE Ratchet + Velocity Stall, No Intelligence filters)
3. Intelligence Filters Only (RS Filter + Overhead Supply Gate + SOE Gate, Baseline Exit)
4. Jules Full Champion (Gen 3 Trader DNA + Market Intelligence Gates + Dynamic Exits)

Accounts for:
- Zero look-ahead bias (Signal Day t close -> Entry Day t+1 open)
- Conservative slippage (1 tick on entry and stop fills)
- Realistic brokerage fees (InnovestX 21.692 bps for TH; SEC/FINRA $0.005/sh for US)
- Strict board lots (100 shares for TH, whole shares for US)
- Max 4 concurrent positions portfolio model with cash tracking
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.market_intelligence_filter import (
    STATE_OWNED_ADR_SYMBOLS,
    check_overhead_supply,
    check_state_owned_adr,
)

DEFAULT_DB = (
    BASE_DIR / "state" / "market_cache.db"
    if (BASE_DIR / "state" / "market_cache.db").exists()
    else BASE_DIR / "state" / "vm_market_cache.db"
)


def get_set_tick(price: float) -> float:
    """Return minimum price variation (tick size) for Thai stocks."""
    if price < 2.0:
        return 0.01
    elif price < 5.0:
        return 0.02
    elif price < 10.0:
        return 0.05
    elif price < 25.0:
        return 0.10
    elif price < 100.0:
        return 0.25
    elif price < 200.0:
        return 0.50
    elif price < 400.0:
        return 1.00
    return 2.00


def round_tick(price: float, market: str, direction: str = "nearest") -> float:
    """Round price to valid exchange tick."""
    if market == "TH":
        tick = get_set_tick(price)
    else:
        tick = 0.01

    if direction == "up":
        return round(math.ceil(price / tick) * tick, 2)
    elif direction == "down":
        return round(math.floor(price / tick) * tick, 2)
    return round(round(price / tick) * tick, 2)


@dataclass
class BacktestConfig:
    name: str
    use_intelligence_filters: bool = False
    use_two_tier_scale_out: bool = False
    target_1_r: float = 1.5
    target_2_r: float = 2.5
    baseline_target_r: float = 2.0
    use_velocity_stall: bool = False
    stall_days: int = 4
    stall_min_mfe: float = 0.30
    use_early_fakeout: bool = False
    use_be_ratchet: bool = False
    use_market_posture_gate: bool = False
    min_stop_floor_pct: float = 4.5
    max_stop_pct: float = 6.5
    max_hold_days: int = 15


@dataclass
class TradeRecord:
    symbol: str
    market: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    shares: int
    initial_risk: float
    net_pnl: float
    realized_r: float
    exit_reason: str
    hold_days: int
    t1_hit: bool = False


@dataclass
class SimulationResult:
    config_name: str
    market: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_pnl: float
    net_return_pct: float
    net_r: float
    profit_factor: float
    max_drawdown_pct: float
    avg_hold_days: float
    avg_win: float
    avg_loss: float
    exit_reasons: dict[str, int] = field(default_factory=dict)
    disqualified_count: int = 0


def load_price_history(
    db_path: Path, market: str
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Load daily OHLCV bars from SQLite."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    if market == "TH":
        symbol_filter = "symbol LIKE '%.BK' OR symbol='^SET.BK'"
        benchmark_sym = "^SET.BK"
    else:
        symbol_filter = "symbol NOT LIKE '%.BK' OR symbol='SPY'"
        benchmark_sym = "SPY"

    rows = conn.execute(
        f"""SELECT symbol, date, open, high, low, close, volume
           FROM price_bar
           WHERE ({symbol_filter})
             AND open > 0 AND high > 0 AND low > 0 AND close > 0
           ORDER BY symbol, date ASC"""
    ).fetchall()
    conn.close()

    bars_by_symbol: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        bars_by_symbol.setdefault(r["symbol"], []).append(dict(r))

    benchmark_bars = bars_by_symbol.get(benchmark_sym, [])
    return bars_by_symbol, benchmark_bars


def compute_indicators(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute SMA20, SMA50, SMA200, RSI14, ATR14, and 20d Volume SMA."""
    n = len(bars)
    closes = [float(b["close"]) for b in bars]
    highs = [float(b["high"]) for b in bars]
    lows = [float(b["low"]) for b in bars]
    volumes = [float(b["volume"]) for b in bars]

    out = []
    # True range for ATR
    tr_list = []
    for i in range(n):
        if i == 0:
            tr = highs[0] - lows[0]
        else:
            tr = max(
                highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])
            )
        tr_list.append(tr)

    for i in range(n):
        b = dict(bars[i])
        # SMAs
        b["sma20"] = sum(closes[max(0, i - 19) : i + 1]) / len(closes[max(0, i - 19) : i + 1])
        b["sma50"] = (
            sum(closes[max(0, i - 49) : i + 1]) / len(closes[max(0, i - 49) : i + 1])
            if i >= 10
            else b["sma20"]
        )
        b["sma200"] = (
            sum(closes[max(0, i - 199) : i + 1]) / len(closes[max(0, i - 199) : i + 1])
            if i >= 50
            else None
        )
        # Previous 5-bar SMA200 for slope
        if i >= 55 and b["sma200"] is not None:
            prev_sma200 = sum(closes[max(0, i - 204) : i - 4]) / len(
                closes[max(0, i - 204) : i - 4]
            )
            b["sma200_slope"] = (b["sma200"] - prev_sma200) / prev_sma200
        else:
            b["sma200_slope"] = 0.0

        # Volume SMA20
        b["vol_sma20"] = sum(volumes[max(0, i - 19) : i + 1]) / len(volumes[max(0, i - 19) : i + 1])

        # ATR14
        atr_window = tr_list[max(0, i - 13) : i + 1]
        b["atr14"] = sum(atr_window) / len(atr_window)
        b["atr_pct"] = (b["atr14"] / closes[i]) * 100.0 if closes[i] > 0 else 3.0

        # RSI14 (Simple Wilder)
        if i >= 14:
            gains = []
            losses = []
            for j in range(i - 13, i + 1):
                diff = closes[j] - closes[j - 1]
                if diff > 0:
                    gains.append(diff)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(diff))
            avg_gain = sum(gains) / 14.0
            avg_loss = sum(losses) / 14.0
            if avg_loss == 0:
                b["rsi14"] = 100.0
            else:
                rs = avg_gain / avg_loss
                b["rsi14"] = 100.0 - (100.0 / (1.0 + rs))
        else:
            b["rsi14"] = 50.0

        out.append(b)

    return out


def run_backtest_simulation(
    bars_by_symbol: dict[str, list[dict[str, Any]]],
    benchmark_bars: list[dict[str, Any]],
    market: str,
    config: BacktestConfig,
    initial_capital: float | None = None,
    max_concurrent: int = 4,
    risk_pct_per_trade: float = 1.0,
    start_date: str = "2025-06-01",
    end_date: str = "2026-09-25",
) -> SimulationResult:
    """Execute historical replay backtest."""
    if initial_capital is None:
        initial_capital = 30000.0 if "TH" in market else 1000.0
    # Precompute indicators for all symbols
    processed_bars: dict[str, list[dict[str, Any]]] = {}
    for sym, raw_bars in bars_by_symbol.items():
        if len(raw_bars) >= 30:
            processed_bars[sym] = compute_indicators(raw_bars)

    # Precompute benchmark return and posture by date
    bench_returns: dict[str, float] = {}
    bench_posture_by_date: dict[str, str] = {}
    if benchmark_bars:
        bench_processed = (
            compute_indicators(benchmark_bars) if len(benchmark_bars) >= 30 else benchmark_bars
        )
        bench_closes = [float(b["close"]) for b in benchmark_bars]
        bench_dates = [b["date"] for b in benchmark_bars]
        for i in range(20, len(bench_dates)):
            p_now = bench_closes[i]
            p_past = bench_closes[i - 20]
            bench_returns[bench_dates[i]] = ((p_now - p_past) / p_past) * 100.0

        for b in bench_processed:
            c = float(b["close"])
            s50 = float(b.get("sma50") or c)
            s20 = float(b.get("sma20") or c)
            # Posture is Healthy only if price >= SMA50 and SMA20 >= SMA50
            if c >= s50 and s20 >= s50 * 0.99:
                bench_posture_by_date[b["date"]] = "HEALTHY"
            else:
                bench_posture_by_date[b["date"]] = "REDUCE_ONLY"

    # Collect all unique trading dates sorted
    all_dates = sorted(
        list(
            {
                b["date"]
                for bars in processed_bars.values()
                for b in bars
                if start_date <= b["date"] <= end_date
            }
        )
    )

    fee_rate_th = 21.692 / 10000.0  # InnovestX cash balance fee
    fee_per_share_us = 0.005  # SEC + FINRA + clearing, min $1.00

    capital = initial_capital
    peak_capital = initial_capital
    max_drawdown_pct = 0.0

    # Active positions: symbol -> position dict
    active_positions: dict[str, dict[str, Any]] = {}
    completed_trades: list[TradeRecord] = []
    disqualified_candidates = 0

    for current_date in all_dates:
        # Step 1: Manage open positions first (Day bar updates)
        closed_symbols = []
        for sym, pos in active_positions.items():
            sym_bars = processed_bars.get(sym, [])
            # Find bar for today
            day_bar = next((b for b in sym_bars if b["date"] == current_date), None)
            if not day_bar:
                continue

            pos["hold_days"] += 1
            o, h, l_val, c = (
                float(day_bar["open"]),
                float(day_bar["high"]),
                float(day_bar["low"]),
                float(day_bar["close"]),
            )
            peak_high = max(pos["peak_high"], h)
            pos["peak_high"] = peak_high
            unit_risk = pos["unit_risk"]

            mfe_r = (peak_high - pos["entry_price"]) / unit_risk if unit_risk > 0 else 0.0
            curr_r = (c - pos["entry_price"]) / unit_risk if unit_risk > 0 else 0.0

            exit_triggered = False
            exit_price = c
            exit_reason = ""

            # Exit Check 1: Stop Loss
            if l_val <= pos["stop_price"]:
                # Broker resting stop filled at stop_price (with 1-tick slippage)
                slip = get_set_tick(pos["stop_price"]) if market == "TH" else 0.01
                exit_price = max(l_val, pos["stop_price"] - slip)
                exit_reason = "stop_loss" if not pos.get("t1_hit") else "breakeven_stop"
                exit_triggered = True

            # Exit Check 2: Profit Targets
            elif config.use_two_tier_scale_out:
                # Two-tier Scale Out
                # Tier 1: 50% at target_1_r (1.5R)
                if not pos.get("t1_hit") and h >= pos["t1_price"]:
                    t1_exit = max(o, pos["t1_price"])
                    scale_shares = pos["shares"] // 2
                    if scale_shares > 0 and pos["shares"] > 1:
                        # Realize 50% profit
                        gross = (t1_exit - pos["entry_price"]) * scale_shares
                        if market == "TH":
                            costs = (pos["entry_price"] * scale_shares * fee_rate_th) + (
                                t1_exit * scale_shares * fee_rate_th
                            )
                        else:
                            costs = max(1.0, scale_shares * fee_per_share_us * 2)
                        part_pnl = gross - costs
                        capital += (pos["entry_price"] * scale_shares) + part_pnl
                        pos["shares"] -= scale_shares
                        pos["t1_hit"] = True
                        pos["realized_pnl_t1"] = part_pnl
                        # Move stop to Breakeven (+0.05R buffer)
                        pos["stop_price"] = pos["entry_price"] + (unit_risk * 0.05)
                    else:
                        # Single share: protect capital without fractional sale
                        pos["t1_hit"] = True
                        pos["stop_price"] = pos["entry_price"] + (unit_risk * 0.05)

                # Tier 2: Runner to target_2_r (2.5R) with Ratchet
                if pos.get("t1_hit"):
                    # Trailing ratchet: at +2.0R MFE, lock +1.0R
                    if mfe_r >= 2.0:
                        pos["stop_price"] = max(
                            pos["stop_price"], pos["entry_price"] + (unit_risk * 1.0)
                        )

                    if h >= pos["t2_price"]:
                        exit_price = max(o, pos["t2_price"])
                        exit_reason = "target_t2_runner"
                        exit_triggered = True

            else:
                # Single Target Baseline
                if h >= pos["target_price"]:
                    exit_price = max(o, pos["target_price"])
                    exit_reason = "target_hit"
                    exit_triggered = True

            # Exit Check 2.5: Early Fakeout / Volume Collapse (Day 1 or 2)
            if not exit_triggered and config.use_early_fakeout and pos["hold_days"] in (1, 2):
                entry_vol = pos.get("entry_volume", 1.0)
                v = float(day_bar.get("volume") or 0.0)
                if entry_vol > 0 and (v / entry_vol) < 0.40 and curr_r < 0.0 and mfe_r < 0.20:
                    exit_price = c
                    exit_reason = "early_fakeout"
                    exit_triggered = True

            # Exit Check 3: Velocity Stall Exit (4 days if MFE < 0.3R)
            if not exit_triggered and config.use_velocity_stall:
                if (
                    pos["hold_days"] >= config.stall_days
                    and mfe_r < config.stall_min_mfe
                    and curr_r <= 0.0
                ):
                    exit_price = c
                    exit_reason = "velocity_stall"
                    exit_triggered = True

            # Exit Check 4: Maximum Time Stop
            if not exit_triggered and pos["hold_days"] >= config.max_hold_days:
                exit_price = c
                exit_reason = "time_stop"
                exit_triggered = True

            if exit_triggered:
                # Calculate Net PnL on remaining shares
                rem_shares = pos["shares"]
                gross = (exit_price - pos["entry_price"]) * rem_shares
                if market == "TH":
                    costs = (pos["entry_price"] * rem_shares * fee_rate_th) + (
                        exit_price * rem_shares * fee_rate_th
                    )
                else:
                    costs = max(1.0, rem_shares * fee_per_share_us * 2)

                final_pnl = gross - costs + pos.get("realized_pnl_t1", 0.0)
                tot_initial_risk = pos["orig_shares"] * unit_risk
                realized_r = final_pnl / tot_initial_risk if tot_initial_risk > 0 else 0.0

                capital += (pos["entry_price"] * rem_shares) + (gross - costs)
                peak_capital = max(peak_capital, capital)
                dd = ((peak_capital - capital) / peak_capital) * 100.0
                max_drawdown_pct = max(max_drawdown_pct, dd)

                completed_trades.append(
                    TradeRecord(
                        symbol=sym,
                        market=market,
                        entry_date=pos["entry_date"],
                        entry_price=pos["entry_price"],
                        exit_date=current_date,
                        exit_price=exit_price,
                        shares=pos["orig_shares"],
                        initial_risk=tot_initial_risk,
                        net_pnl=final_pnl,
                        realized_r=realized_r,
                        exit_reason=exit_reason,
                        hold_days=pos["hold_days"],
                        t1_hit=pos.get("t1_hit", False),
                    )
                )
                closed_symbols.append(sym)

        for sym in closed_symbols:
            del active_positions[sym]

        # Step 2: Scout New Signals for Tomorrow
        if len(active_positions) >= max_concurrent:
            continue

        if config.use_market_posture_gate:
            posture = bench_posture_by_date.get(current_date, "REDUCE_ONLY")
            if posture == "REDUCE_ONLY":
                continue

        available_slots = max_concurrent - len(active_positions)
        slot_budget = capital / max_concurrent
        candidates = []

        for sym, bars in processed_bars.items():
            if sym in active_positions or sym in ("^SET.BK", "SPY", "QQQ"):
                continue

            # Find bar index for current_date
            idx = next((i for i, b in enumerate(bars) if b["date"] == current_date), -1)
            if idx < 20 or idx >= len(bars) - 1:
                continue

            bar_t = bars[idx]
            close_t = float(bar_t["close"])
            sma20_t = float(bar_t["sma20"])
            sma50_t = float(bar_t["sma50"])
            vol_t = float(bar_t["volume"])
            vol_sma20_t = float(bar_t["vol_sma20"])
            rsi_t = float(bar_t["rsi14"])
            atr_pct = float(bar_t["atr_pct"])

            # Technical Scout Condition (Jules Swing Momentum):
            # Price > SMA20, SMA20 > SMA50, Volume breakout > 1.2x, RSI healthy (50-70)
            if not (
                close_t > sma20_t
                and sma20_t >= sma50_t * 0.98
                and vol_t >= vol_sma20_t * 1.15
                and 48.0 <= rsi_t <= 72.0
            ):
                continue

            # Apply Intelligence Gates if enabled
            if config.use_intelligence_filters:
                # Gate 1: State-Owned Enterprise ADR / Political Risk Gate
                clean_sym = sym.replace(".BK", "").replace("-", ".")
                if (
                    clean_sym in STATE_OWNED_ADR_SYMBOLS
                    or check_state_owned_adr(sym).is_state_owned
                ):
                    disqualified_candidates += 1
                    continue

                # Gate 2: Overhead Supply Gate (Declining 200 SMA directly overhead)
                overhead_res = check_overhead_supply(
                    close_t, bar_t.get("sma200"), bar_t.get("sma200_slope", 0.0)
                )
                if not overhead_res.passed:
                    disqualified_candidates += 1
                    continue

                # Gate 3: Relative Strength vs Benchmark
                # 20-day return of stock vs benchmark
                past_bar = bars[idx - 20]
                stock_20d_ret = (
                    (close_t - float(past_bar["close"])) / float(past_bar["close"])
                ) * 100.0
                bench_20d_ret = bench_returns.get(current_date, 0.0)
                relative_diff = stock_20d_ret - bench_20d_ret

                if relative_diff < -2.0:  # Underperforming benchmark
                    disqualified_candidates += 1
                    continue

                # Gate 4: Dollar Volume Liquidity Floor
                dollar_vol = close_t * vol_t
                if market == "TH" and dollar_vol < 15_000_000.0:  # ฿15M THB
                    disqualified_candidates += 1
                    continue
                elif market == "US" and dollar_vol < 10_000_000.0:  # $10M USD
                    disqualified_candidates += 1
                    continue

            # Candidate passed criteria!
            # Next day bar
            bar_next = bars[idx + 1]
            candidates.append(
                {
                    "symbol": sym,
                    "date_signal": current_date,
                    "date_entry": bar_next["date"],
                    "open_next": float(bar_next["open"]),
                    "atr_pct": atr_pct,
                    "rsi": rsi_t,
                    "vol_ratio": vol_t / max(1.0, vol_sma20_t),
                    "entry_volume": vol_t,
                }
            )

        # Sort candidates by volume surge & RSI momentum
        candidates.sort(key=lambda x: (x["vol_ratio"], x["rsi"]), reverse=True)

        # Stage Orders for Next Day Open
        for cand in candidates[:available_slots]:
            sym = cand["symbol"]
            next_open = cand["open_next"]
            atr_pct = cand["atr_pct"]

            # Dynamic ATR Stop Clamping
            stop_pct = max(config.min_stop_floor_pct, 1.5 * atr_pct)
            stop_pct = min(config.max_stop_pct, stop_pct)

            # Slip 1 tick on entry
            slip = get_set_tick(next_open) if market == "TH" else 0.01
            entry_price = next_open + slip
            stop_price = entry_price * (1.0 - stop_pct / 100.0)
            unit_risk = entry_price - stop_price
            if unit_risk <= 0:
                continue

            # Position Sizing
            risk_budget = capital * (risk_pct_per_trade / 100.0)
            target_shares = int(risk_budget / unit_risk)
            if market == "TH":
                shares = (target_shares // 100) * 100
                if shares * entry_price > slot_budget:
                    shares = int(slot_budget / entry_price // 100) * 100
                shares = max(100, shares)
            else:
                shares = min(target_shares, int(slot_budget / entry_price))
                shares = max(1, shares)

            pos_cost = shares * entry_price
            if pos_cost > capital:
                continue

            capital -= pos_cost

            # Targets
            t1_price = entry_price + (unit_risk * config.target_1_r)
            t2_price = entry_price + (unit_risk * config.target_2_r)
            base_target = entry_price + (unit_risk * config.baseline_target_r)

            active_positions[sym] = {
                "symbol": sym,
                "entry_date": cand["date_entry"],
                "entry_price": entry_price,
                "shares": shares,
                "orig_shares": shares,
                "stop_price": stop_price,
                "unit_risk": unit_risk,
                "t1_price": t1_price,
                "t2_price": t2_price,
                "target_price": base_target,
                "peak_high": entry_price,
                "hold_days": 0,
                "t1_hit": False,
                "realized_pnl_t1": 0.0,
                "entry_volume": cand.get("entry_volume", 1.0),
            }

    # Close any still-open positions at the last available close price
    for sym, pos in active_positions.items():
        sym_bars = processed_bars.get(sym, [])
        last_bar = sym_bars[-1]
        exit_price = float(last_bar["close"])
        rem_shares = pos["shares"]
        gross = (exit_price - pos["entry_price"]) * rem_shares
        if market == "TH":
            costs = (pos["entry_price"] * rem_shares * fee_rate_th) + (
                exit_price * rem_shares * fee_rate_th
            )
        else:
            costs = max(1.0, rem_shares * fee_per_share_us * 2)

        final_pnl = gross - costs + pos.get("realized_pnl_t1", 0.0)
        tot_initial_risk = pos["orig_shares"] * pos["unit_risk"]
        realized_r = final_pnl / tot_initial_risk if tot_initial_risk > 0 else 0.0

        capital += (pos["entry_price"] * rem_shares) + (gross - costs)
        completed_trades.append(
            TradeRecord(
                symbol=sym,
                market=market,
                entry_date=pos["entry_date"],
                entry_price=pos["entry_price"],
                exit_date=last_bar["date"],
                exit_price=exit_price,
                shares=pos["orig_shares"],
                initial_risk=tot_initial_risk,
                net_pnl=final_pnl,
                realized_r=realized_r,
                exit_reason="end_of_backtest",
                hold_days=pos["hold_days"],
                t1_hit=pos.get("t1_hit", False),
            )
        )

    # Compute Statistics
    wins = [t for t in completed_trades if t.net_pnl > 0]
    losses = [t for t in completed_trades if t.net_pnl <= 0]
    total_trades = len(completed_trades)
    win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

    net_pnl = sum(t.net_pnl for t in completed_trades)
    net_return_pct = (net_pnl / initial_capital) * 100.0
    net_r = sum(t.realized_r for t in completed_trades)

    gross_wins = sum(t.net_pnl for t in wins)
    gross_losses = abs(sum(t.net_pnl for t in losses))
    profit_factor = (
        (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 1.0)
    )

    avg_hold = (
        (sum(t.hold_days for t in completed_trades) / total_trades) if total_trades > 0 else 0.0
    )
    avg_win = (gross_wins / len(wins)) if wins else 0.0
    avg_loss = (gross_losses / len(losses)) if losses else 0.0

    reasons: dict[str, int] = {}
    for t in completed_trades:
        reasons[t.exit_reason] = reasons.get(t.exit_reason, 0) + 1

    return SimulationResult(
        config_name=config.name,
        market=market,
        total_trades=total_trades,
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=win_rate,
        net_pnl=net_pnl,
        net_return_pct=net_return_pct,
        net_r=net_r,
        profit_factor=profit_factor,
        max_drawdown_pct=max_drawdown_pct,
        avg_hold_days=avg_hold,
        avg_win=avg_win,
        avg_loss=avg_loss,
        exit_reasons=reasons,
        disqualified_count=disqualified_candidates,
    )


def print_comparison_table(results: list[SimulationResult], market: str, currency: str):
    """Format and print an institutional markdown comparison table."""
    print("\n" + "=" * 115)
    print(
        f"📊 HISTORICAL BACKTEST & SIMULATION AUDIT: {market} EQUITIES (March 2025 - September 2026)"
    )
    print("=" * 115)
    header = (
        f"{'Configuration':<42} {'Trades':>6} {'WinRate':>8} {'Net R':>8} "
        f"{'Net PnL (' + currency + ')':>16} {'Return':>8} {'PF':>6} {'MaxDD':>7} {'AvgDays':>7}"
    )
    print(header)
    print("-" * 115)

    for r in results:
        pnl_str = f"{r.net_pnl:>+14,.2f} {currency}"
        print(
            f"{r.config_name:<42} {r.total_trades:>6} {r.win_rate:>7.1f}% {r.net_r:>+7.2f}R "
            f"{pnl_str:>16} {r.net_return_pct:>+7.1f}% {r.profit_factor:>6.2f} "
            f"{r.max_drawdown_pct:>6.1f}% {r.avg_hold_days:>6.1f}d"
        )
    print("-" * 115)
    print("Detailed Exit Breakdown:")
    for r in results:
        reason_items = [f"{k}: {v}" for k, v in sorted(r.exit_reasons.items())]
        print(f"  • {r.config_name}: {', '.join(reason_items)}")
        if r.disqualified_count > 0:
            print(f"    (Disqualified Toxic Candidates: {r.disqualified_count})")
    print("=" * 115 + "\n")


def run_full_audit(market: str = "BOTH", db_path: Path = DEFAULT_DB):
    """Run full historical backtest across all 4 configurations."""
    configs = [
        BacktestConfig(
            name="1. Baseline Naive (Static 2.0R, No Gates)",
            use_intelligence_filters=False,
            use_two_tier_scale_out=False,
            use_velocity_stall=False,
            use_be_ratchet=False,
        ),
        BacktestConfig(
            name="2. Exit Safeguards Only (Scale-Out + Stall)",
            use_intelligence_filters=False,
            use_two_tier_scale_out=True,
            use_velocity_stall=True,
            use_be_ratchet=True,
        ),
        BacktestConfig(
            name="3. Market Intelligence Only (RS + SOE Gate)",
            use_intelligence_filters=True,
            use_two_tier_scale_out=False,
            use_velocity_stall=False,
            use_be_ratchet=False,
        ),
        BacktestConfig(
            name="4. Jules Champion (DNA Gen 3 + Intelligence)",
            use_intelligence_filters=True,
            use_two_tier_scale_out=True,
            use_velocity_stall=True,
            use_be_ratchet=True,
            use_market_posture_gate=False,
        ),
        BacktestConfig(
            name="5. Live Full System (Posture + Gates + DNA 3)",
            use_intelligence_filters=True,
            use_two_tier_scale_out=True,
            use_velocity_stall=True,
            use_be_ratchet=True,
            use_market_posture_gate=True,
        ),
        BacktestConfig(
            name="6. Live System + Early Fakeout Cut",
            use_intelligence_filters=True,
            use_two_tier_scale_out=True,
            use_velocity_stall=True,
            use_early_fakeout=True,
            use_be_ratchet=True,
            use_market_posture_gate=True,
        ),
    ]

    markets = ["TH", "US"] if market == "BOTH" else [market]

    for m in markets:
        currency = "THB" if m == "TH" else "USD"
        bars_by_symbol, bench_bars = load_price_history(db_path, m)
        print(
            f"Loaded {len(bars_by_symbol)} symbols and {len(bench_bars)} benchmark bars for {m} market."
        )

        market_results = []
        for cfg in configs:
            res = run_backtest_simulation(
                bars_by_symbol=bars_by_symbol,
                benchmark_bars=bench_bars,
                market=m,
                config=cfg,
            )
            market_results.append(res)

        print_comparison_table(market_results, m, currency)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run institutional historical backtest")
    parser.add_argument(
        "--market", choices=["TH", "US", "BOTH"], default="BOTH", help="Market to test"
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to SQLite database")
    args = parser.parse_args()

    run_full_audit(market=args.market, db_path=Path(args.db))
