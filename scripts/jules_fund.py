#!/usr/bin/env python3
"""Jules AI Fund Portfolio Manager and Order Execution Engine.

Allows Jules AI to autonomously manage its virtual fund (30,000 THB starting capital),
screen candidate stocks, evaluate business models/catalysts, submit buy/sell orders,
and benchmark live against the Systematic Quant Champion.

Usage:
    python scripts/jules_fund.py status
    python scripts/jules_fund.py buy --symbol BDMS.BK --shares 1000 --thesis "Strong Q2 growth and private hospital demand"
    python scripts/jules_fund.py sell --symbol BDMS.BK --reason "Reached resistance, taking profit"
    python scripts/jules_fund.py scan
    python scripts/jules_fund.py process-orders
    python scripts/jules_fund.py arena
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import paper_trade

from trading_core.clock import isoformat_seconds

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jules_fund")

DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"
ORDERS_DIR = PROJECT_ROOT / "state" / "jules_orders"
PROCESSED_ORDERS_DIR = ORDERS_DIR / "processed"

INITIAL_CAPITAL = 30000.0  # THB
DEFAULT_FEE_BPS = 21.692  # InnovestX cash balance fee per side (0.21692%)
MAX_OPEN_POSITIONS = 4


def _normalize_symbol(symbol: str, market: str = "TH") -> str:
    sym = symbol.strip().upper()
    if market == "TH" and not sym.endswith(".BK"):
        sym = f"{sym}.BK"
    return sym


def _get_latest_price(symbol: str, market: str = "TH") -> float:
    """Fetch latest available price from local DB or yfinance fallback."""
    clean_sym = _normalize_symbol(symbol, market)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT close FROM price_bar WHERE symbol=? AND close IS NOT NULL ORDER BY date DESC LIMIT 1",
                (clean_sym,),
            ).fetchone()
            if row and row[0] and float(row[0]) > 0:
                return float(row[0])
    except Exception as e:
        logger.debug("Local price lookup failed for %s: %s", clean_sym, e)

    try:
        import yfinance as yf

        ticker = yf.Ticker(clean_sym)
        hist = ticker.history(period="5d")
        if not hist.empty and "Close" in hist.columns:
            return float(hist["Close"].iloc[-1])
    except Exception as e:
        logger.warning("yfinance lookup failed for %s: %s", clean_sym, e)

    raise ValueError(
        f"Could not determine current market price for {clean_sym}. Please specify --entry manually."
    )


def get_jules_status(market: str = "TH") -> dict[str, Any]:
    """Calculate exact portfolio metrics for Jules AI Fund."""
    open_pos = paper_trade.list_positions(status_filter="open", market=market, portfolio="jules")
    closed_pos = paper_trade.list_positions(
        status_filter="closed", market=market, portfolio="jules"
    )
    stats = paper_trade.compute_stats(market=market, portfolio="jules")

    realized_pnl = float(stats.get("total_realized_pnl") or 0.0)
    unrealized_pnl = float(stats.get("total_unrealized_pnl") or 0.0)
    total_open_cost = sum(
        float(r["entry_price"] * r["shares"] + (r.get("entry_cost") or 0)) for r in open_pos
    )
    cash_balance = INITIAL_CAPITAL - total_open_cost + realized_pnl
    equity = cash_balance + sum(
        float((r.get("last_price") or r["entry_price"]) * r["shares"]) for r in open_pos
    )
    net_pnl = realized_pnl + unrealized_pnl
    net_return_pct = (net_pnl / INITIAL_CAPITAL) * 100.0 if INITIAL_CAPITAL > 0 else 0.0

    return {
        "fund_name": "Jules AI Autonomous Fund",
        "market": market,
        "initial_capital": INITIAL_CAPITAL,
        "cash_balance": round(cash_balance, 2),
        "equity": round(equity, 2),
        "net_pnl": round(net_pnl, 2),
        "net_return_pct": round(net_return_pct, 2),
        "realized_pnl": round(realized_pnl, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "win_rate": round(float(stats.get("win_rate") or 0.0), 3),
        "open_count": len(open_pos),
        "closed_count": len(closed_pos),
        "open_positions": open_pos,
        "closed_trades": closed_pos,
        "as_of": isoformat_seconds(),
    }


def execute_buy(
    symbol: str,
    shares: int,
    market: str = "TH",
    entry: float | None = None,
    stop: float | None = None,
    target: float | None = None,
    thesis: str | None = None,
    fee_bps: float = DEFAULT_FEE_BPS,
) -> dict[str, Any]:
    """Execute a buy order for Jules AI Fund under fair competition rules."""
    sym = _normalize_symbol(symbol, market)
    if market == "TH" and shares % 100 != 0:
        raise ValueError(f"SET board lot violation: shares ({shares}) must be a multiple of 100.")

    if shares <= 0:
        raise ValueError("shares must be > 0")

    entry_price = float(entry) if entry else _get_latest_price(sym, market)
    if entry_price <= 0:
        raise ValueError(f"Invalid entry price: {entry_price}")

    if stop is None:
        stop_price = round(entry_price * 0.94, 2)
    else:
        stop_price = float(stop)

    if target is None:
        risk_per_share = entry_price - stop_price
        target_price = round(entry_price + (2.2 * risk_per_share), 2)
    else:
        target_price = float(target)

    if stop_price >= entry_price:
        raise ValueError(f"Stop price ({stop_price}) must be less than entry price ({entry_price})")
    if target_price <= entry_price:
        raise ValueError(
            f"Target price ({target_price}) must be greater than entry price ({entry_price})"
        )

    status = get_jules_status(market)
    if status["open_count"] >= MAX_OPEN_POSITIONS:
        raise ValueError(
            f"Risk limit reached: Jules fund already has {status['open_count']} open positions (max {MAX_OPEN_POSITIONS})."
        )

    for p in status["open_positions"]:
        if p["symbol"].upper() == sym.upper():
            raise ValueError(f"Already holding an active position in {sym}.")

    total_cost = (entry_price * shares) * (1.0 + fee_bps / 10000.0)
    if total_cost > status["cash_balance"]:
        raise ValueError(
            f"Insufficient cash: order requires {total_cost:.2f} THB, but available cash is {status['cash_balance']:.2f} THB."
        )

    decision_trace = {
        "fund": "jules_ai",
        "thesis": thesis or "Fundamental and catalyst momentum thesis",
        "timestamp": isoformat_seconds(),
        "fee_bps": fee_bps,
        "entry_rule": "jules_discretionary_entry",
    }

    trade = paper_trade.open_position(
        symbol=sym,
        market=market,
        shares=shares,
        entry=entry_price,
        stop=stop_price,
        target=target_price,
        side="long",
        source="jules_ai",
        source_score=85.0,
        notes=thesis,
        transaction_cost_bps=fee_bps,
        decision_trace=decision_trace,
        portfolio="jules",
    )
    logger.info(
        "Jules AI Fund OPENED: %s %d shares @ %.2f (Stop: %.2f, Target: %.2f)",
        sym,
        shares,
        entry_price,
        stop_price,
        target_price,
    )
    return trade


def execute_sell(
    symbol: str | None = None,
    trade_id: int | None = None,
    market: str = "TH",
    price: float | None = None,
    reason: str = "Jules take profit / risk exit",
) -> dict[str, Any]:
    """Close an active position for Jules AI Fund."""
    open_positions = paper_trade.list_positions(
        status_filter="open", market=market, portfolio="jules"
    )
    target_pos = None

    if trade_id:
        target_pos = next((p for p in open_positions if p["id"] == trade_id), None)
    elif symbol:
        sym = _normalize_symbol(symbol, market)
        target_pos = next((p for p in open_positions if p["symbol"].upper() == sym.upper()), None)

    if not target_pos:
        raise ValueError(
            f"No active position found in Jules fund for symbol={symbol} id={trade_id}"
        )

    exit_price = float(price) if price else _get_latest_price(target_pos["symbol"], market)
    tid = target_pos["id"]

    status = "closed_manual"
    if exit_price >= target_pos["target_price"]:
        status = "closed_target"
    elif exit_price <= target_pos["stop_price"]:
        status = "closed_stop"

    closed = paper_trade.close_position(
        trade_id=tid,
        exit_price=exit_price,
        status=status,
        notes=reason,
    )
    logger.info(
        "Jules AI Fund CLOSED: %s id=%d @ %.2f (Status: %s, Realized PnL: %.2f)",
        target_pos["symbol"],
        tid,
        exit_price,
        status,
        closed.get("realized_pnl", 0),
    )

    try:
        import scripts.jules_evolver as je

        je.evolve_memory(market=market)
    except Exception as e:
        logger.warning("Auto-evolution after trade close failed: %s", e)

    return closed


def process_orders_queue(market: str = "TH") -> list[dict[str, Any]]:
    """Scan and process pending order files submitted by Jules via GitHub."""
    ORDERS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_ORDERS_DIR.mkdir(parents=True, exist_ok=True)

    order_files = sorted(
        glob.glob(str(ORDERS_DIR / "*.yaml")) + glob.glob(str(ORDERS_DIR / "*.json"))
    )
    results = []

    for fpath in order_files:
        p = Path(fpath)
        if p.parent == PROCESSED_ORDERS_DIR:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                if p.suffix == ".json":
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)

            action = data.get("action", "buy").lower()
            symbol = data.get("symbol")
            if not symbol:
                raise ValueError("Order file missing 'symbol'")

            if action == "buy":
                res = execute_buy(
                    symbol=symbol,
                    shares=int(data.get("shares", 100)),
                    market=data.get("market", market),
                    entry=data.get("entry_price") or data.get("entry"),
                    stop=data.get("stop_price") or data.get("stop"),
                    target=data.get("target_price") or data.get("target"),
                    thesis=data.get("thesis") or data.get("notes"),
                )
            elif action == "sell":
                res = execute_sell(
                    symbol=symbol,
                    trade_id=data.get("trade_id") or data.get("id"),
                    market=data.get("market", market),
                    price=data.get("exit_price") or data.get("price"),
                    reason=data.get("reason") or data.get("notes") or "Order executed from queue",
                )
            else:
                raise ValueError(f"Unknown order action: {action}")

            results.append({"file": p.name, "status": "executed", "result": res})
            dest = PROCESSED_ORDERS_DIR / f"{p.stem}_{int(datetime.now().timestamp())}{p.suffix}"
            shutil.move(str(p), str(dest))
        except Exception as e:
            logger.error("Failed to process order file %s: %s", p.name, e)
            results.append({"file": p.name, "status": "error", "error": str(e)})

    return results


def get_scan_candidates(limit: int = 10, market: str = "TH") -> list[dict[str, Any]]:
    """Scan latest price bars and candidate metrics to assist Jules's fundamental screening."""
    candidates = []
    if not DB_PATH.exists():
        return candidates

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT symbol, date, open, high, low, close, volume
                   FROM price_bar
                   WHERE symbol LIKE '%.BK'
                   ORDER BY date DESC, volume DESC
                   LIMIT ?""",
                (limit * 3,),
            ).fetchall()

            seen = set()
            for r in rows:
                sym = r["symbol"]
                if sym in seen:
                    continue
                seen.add(sym)
                candidates.append(
                    {
                        "symbol": sym,
                        "date": r["date"],
                        "close": r["close"],
                        "volume": r["volume"],
                    }
                )
                if len(candidates) >= limit:
                    break
    except Exception as e:
        logger.error("Error fetching candidates: %s", e)

    return candidates


def main():
    parser = argparse.ArgumentParser(description="Jules AI Fund Portfolio Manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")

    b = sub.add_parser("buy")
    b.add_argument("--symbol", required=True, help="Stock ticker (e.g. BDMS.BK)")
    b.add_argument(
        "--shares",
        type=int,
        required=True,
        help="Number of shares (SET board lot = multiple of 100)",
    )
    b.add_argument("--entry", type=float, help="Entry price (auto-fetched if omitted)")
    b.add_argument("--stop", type=float, help="Stop loss price (auto 6 percent if omitted)")
    b.add_argument("--target", type=float, help="Take profit target price (auto 2.2R if omitted)")
    b.add_argument("--thesis", help="Investment thesis and catalyst justification")
    b.add_argument("--market", default="TH")

    s = sub.add_parser("sell")
    s.add_argument("--symbol", help="Stock ticker to sell")
    s.add_argument("--id", type=int, help="Trade ID to close")
    s.add_argument("--price", type=float, help="Exit price (auto-fetched if omitted)")
    s.add_argument("--reason", default="Jules take profit / risk exit", help="Reason for selling")
    s.add_argument("--market", default="TH")

    sc = sub.add_parser("scan")
    sc.add_argument("--limit", type=int, default=10)
    sc.add_argument("--market", default="TH")

    sub.add_parser("process-orders")
    sub.add_parser("arena")
    sub.add_parser("briefing")
    sub.add_parser("evolve")

    args = parser.parse_args()

    if args.cmd == "status":
        print(json.dumps(get_jules_status(), ensure_ascii=False, indent=2))
    elif args.cmd == "buy":
        out = execute_buy(
            symbol=args.symbol,
            shares=args.shares,
            market=args.market,
            entry=args.entry,
            stop=args.stop,
            target=args.target,
            thesis=args.thesis,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "sell":
        out = execute_sell(
            symbol=args.symbol,
            trade_id=args.id,
            market=args.market,
            price=args.price,
            reason=args.reason,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "scan":
        print(
            json.dumps(
                get_scan_candidates(limit=args.limit, market=args.market),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.cmd == "process-orders":
        out = process_orders_queue()
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "arena":
        q_stats = paper_trade.compute_stats(portfolio="quant")
        j_stats = paper_trade.compute_stats(portfolio="jules")
        print(json.dumps({"quant": q_stats, "jules": j_stats}, ensure_ascii=False, indent=2))
    elif args.cmd == "briefing":
        import scripts.jules_evolver as je

        print(je.get_pre_trade_briefing())
    elif args.cmd == "evolve":
        import scripts.jules_evolver as je

        print(json.dumps(je.evolve_memory(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
