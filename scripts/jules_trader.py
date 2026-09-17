#!/usr/bin/env python3
"""Autonomous Trading Decision Engine for Jules AI Fund (SET Market).

Evaluates morning scout candidates, validates portfolio capacity, enforces
multi-layer circuit breakers, anti-correlation sector caps, SET tick sizes,
liquidity gates, and emits staged orders with TTL.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

import paper_trade

import scripts.jules_fund as jf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("jules_trader")

DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"
ORDERS_DIR = PROJECT_ROOT / "state" / "jules_orders"
STAGED_ORDERS_DIR = ORDERS_DIR / "staged"
PROCESSED_ORDERS_DIR = ORDERS_DIR / "processed"
QUARANTINE_ORDERS_DIR = ORDERS_DIR / "quarantine"
MISSION_JSON = PROJECT_ROOT / "state" / "jules_tasks" / "today_mission.json"
LEARNINGS_YAML = PROJECT_ROOT / "state" / "jules_memory" / "learnings.yaml"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Quantitative Limits & Guardrails
MAX_POSITIONS = 4
MIN_CASH_REQUIRED = 5000.0
MAX_SLOT_BUDGET = 7500.0
BASE_RISK_PER_TRADE_PCT = 0.010  # 1.0% portfolio risk
MIN_ADTV_THB = 15_000_000.0  # 15M THB minimum daily turnover
MAX_CHASE_PCT = 0.010  # 1.0% max chase limit above trigger


def set_tick_size(price: float) -> Decimal:
    """Return the official SET tick size for a given price."""
    if price < 2.0:
        return Decimal("0.01")
    if price < 5.0:
        return Decimal("0.02")
    if price < 10.0:
        return Decimal("0.05")
    if price < 25.0:
        return Decimal("0.10")
    if price < 100.0:
        return Decimal("0.25")
    if price < 200.0:
        return Decimal("0.50")
    if price < 400.0:
        return Decimal("1.00")
    return Decimal("2.00")


def round_to_set_tick(price: float, direction: str = "down") -> float:
    """Discretize price to a valid SET board-lot tick boundary.
    'up' for ceiling (entry triggers), 'down' for floor (stop & limit target)."""
    if price <= 0:
        return 0.0
    val = Decimal(str(round(price, 4)))
    tick = set_tick_size(float(val))
    rounding = ROUND_CEILING if direction == "up" else ROUND_FLOOR
    return float((val / tick).to_integral_value(rounding=rounding) * tick)


def init_decision_ledger(db_path: Path | None = None) -> None:
    """Initialize SQLite decision ledger table for guaranteed idempotency."""
    if db_path is None:
        db_path = DB_PATH
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS jules_decision_ledger (
                decision_date TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                symbol TEXT,
                order_id TEXT,
                decided_at TEXT NOT NULL,
                posture TEXT,
                reason TEXT NOT NULL,
                payload_json TEXT
            )"""
        )
        conn.commit()


def check_existing_decision(
    decision_date: str, db_path: Path | None = None
) -> dict[str, Any] | None:
    """Check if an autonomous decision was already made today."""
    if db_path is None:
        db_path = DB_PATH
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM jules_decision_ledger WHERE decision_date = ?",
                (decision_date,),
            ).fetchone()
            if row:
                return dict(row)
    except Exception as e:
        logger.warning("Failed to query decision ledger: %s", e)
    return None


def record_decision(
    decision_date: str,
    status: str,
    symbol: str | None,
    order_id: str | None,
    posture: str,
    reason: str,
    payload: dict[str, Any] | None = None,
    db_path: Path | None = None,
) -> None:
    """Record an autonomous decision to the persistent ledger."""
    if db_path is None:
        db_path = DB_PATH
    init_decision_ledger(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    payload_str = json.dumps(payload or {})
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO jules_decision_ledger
               (decision_date, status, symbol, order_id, decided_at, posture, reason, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (decision_date, status, symbol, order_id, now_iso, posture, reason, payload_str),
        )
        conn.commit()


def check_circuit_breakers(market: str = "TH") -> tuple[bool, float, str]:
    """Check portfolio drawdown and consecutive losses.
    Returns: (is_allowed, risk_multiplier, reason)"""
    closed = paper_trade.list_positions(status_filter="closed", market=market, portfolio="jules")
    stats = paper_trade.compute_stats(market=market, portfolio="jules")

    # 1. Consecutive Closed Loss Check
    consecutive_losses = 0
    # Closed trades are sorted by id/exit
    for t in reversed(closed):
        pnl = float(t.get("realized_pnl") or 0.0)
        if pnl < 0:
            consecutive_losses += 1
        else:
            break

    if consecutive_losses >= 3:
        return (
            False,
            0.0,
            f"Halt: 3 consecutive closed losses ({consecutive_losses}). Cooldown active.",
        )

    risk_mult = 0.5 if consecutive_losses == 2 else 1.0

    # 2. High-Water Mark Drawdown Check
    initial_cap = jf.INITIAL_CAPITAL
    equity = float(stats.get("total_realized_pnl") or 0.0) + initial_cap
    dd_pct = (initial_cap - equity) / initial_cap if initial_cap > 0 else 0.0

    if dd_pct >= 0.15:
        return (
            False,
            0.0,
            f"Halt: Portfolio drawdown {dd_pct * 100:.1f}% exceeds 15% emergency breaker.",
        )
    elif dd_pct >= 0.10:
        risk_mult = min(risk_mult, 0.5)

    reason = f"Normal (Consecutive losses: {consecutive_losses}, Risk mult: {risk_mult}x)"
    return True, risk_mult, reason


def get_latest_exposure_posture() -> dict[str, Any]:
    """Read the latest exposure posture report."""
    posture_files = sorted(REPORTS_DIR.glob("exposure_posture_*.json"))
    if not posture_files:
        return {"recommendation": "NORMAL", "exposure_ceiling_pct": 75}
    try:
        with open(posture_files[-1], encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"recommendation": "NORMAL", "exposure_ceiling_pct": 75}


def get_sector_momentum_mapping() -> dict[str, float]:
    """Parse latest sector heatmap to classify leading and lagging sectors."""
    mapping: dict[str, float] = {}
    heatmap_files = sorted(REPORTS_DIR.glob("thai_sector_heatmap_*.md"))
    if not heatmap_files:
        return mapping
    try:
        content = heatmap_files[-1].read_text(encoding="utf-8")
        # Leading sectors get +10.0, bottom/negative get -25.0
        for line in content.splitlines():
            if "|" in line and ("🟢" in line or "🟡" in line or "🔴" in line):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3 and parts[0].isdigit():
                    sec_name = parts[1]
                    mom_str = parts[-1]
                    if "🟢" in mom_str:
                        mapping[sec_name] = 10.0
                    elif "🔴" in mom_str:
                        mapping[sec_name] = -25.0
                    else:
                        mapping[sec_name] = 0.0
    except Exception as e:
        logger.debug("Failed to parse sector heatmap: %s", e)
    return mapping


def calculate_volatility_sizing(
    price: float,
    stop: float,
    equity: float,
    cash: float,
    risk_mult: float = 1.0,
) -> tuple[int, float]:
    """Calculate volatility/risk-adjusted position size in SET 100-share board lots."""
    price = round_to_set_tick(price, "up")
    stop = round_to_set_tick(stop, "down")
    risk_per_share = max(set_tick_size(price) * Decimal("2"), Decimal(str(price - stop)))
    risk_per_share_float = float(risk_per_share)

    # 1.0% portfolio risk * risk_multiplier
    target_dollar_risk = equity * BASE_RISK_PER_TRADE_PCT * risk_mult
    raw_risk_shares = (
        int(target_dollar_risk / risk_per_share_float) if risk_per_share_float > 0 else 100
    )

    # Capital constraint (max slot budget ฿7,500 or remaining cash)
    max_capital_for_trade = min(MAX_SLOT_BUDGET, cash * 0.95)
    max_cap_shares = int(max_capital_for_trade / price) if price > 0 else 0

    allowed_shares = min(raw_risk_shares, max_cap_shares)
    board_lot_shares = max(100, (allowed_shares // 100) * 100)

    est_cost = round(price * board_lot_shares, 2)
    if est_cost > cash:
        board_lot_shares = (int(cash / price) // 100) * 100

    return board_lot_shares, est_cost


def evaluate_and_select_trade(
    candidates: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    sector_mods: dict[str, float],
    equity: float,
    cash: float,
    risk_mult: float = 1.0,
) -> tuple[dict[str, Any] | None, str]:
    """Filter and rank candidates according to liquidity, sector, and risk-reward gates."""
    if not candidates:
        return None, "No candidates provided in mission"

    open_sectors = {
        p.get("sector") for p in open_positions if p.get("sector") and p.get("sector") != "N/A"
    }

    scored_candidates = []
    for cand in candidates:
        sym = cand["symbol"]
        price = float(cand.get("price") or 0.0)
        stop = float(cand.get("stop") or 0.0)
        target = float(cand.get("target") or 0.0)
        sector = cand.get("sector", "N/A")

        if price <= 0 or stop <= 0 or target <= 0 or stop >= price or target <= price:
            continue

        # Discretize levels to valid SET ticks
        entry_tick = round_to_set_tick(price, "up")
        stop_tick = round_to_set_tick(stop, "down")
        target_tick = round_to_set_tick(target, "down")

        # Anti-Correlation Sector Gate: Max 1 position per sector
        if sector in open_sectors:
            logger.info("Candidate %s rejected: sector %s already active in portfolio", sym, sector)
            continue

        # Risk-to-Reward Gate: Minimum 1.5R required
        risk_dist = entry_tick - stop_tick
        reward_dist = target_tick - entry_tick
        rr_ratio = reward_dist / risk_dist if risk_dist > 0 else 0.0
        if rr_ratio < 1.45:
            logger.info("Candidate %s rejected: R/R ratio %.2f < 1.5R", sym, rr_ratio)
            continue

        # Stop Width Sanity Gate: Must be between 2.0% and 6.5%
        stop_pct = (risk_dist / entry_tick) * 100.0
        if stop_pct < 1.9 or stop_pct > 6.6:
            logger.info(
                "Candidate %s rejected: stop width %.1f%% outside 2.0-6.5%% band", sym, stop_pct
            )
            continue

        # Sector Momentum Modifier
        sector_bonus = sector_mods.get(sector, 0.0)
        if sector_bonus < -20.0:
            logger.info("Candidate %s rejected: lagging sector %s (-25 pts penalty)", sym, sector)
            continue

        base_score = float(cand.get("score") or 60.0)
        final_score = base_score + sector_bonus

        shares, est_cost = calculate_volatility_sizing(
            entry_tick, stop_tick, equity, cash, risk_mult
        )
        if shares < 100 or est_cost > cash:
            logger.info("Candidate %s rejected: insufficient cash for minimum board lot", sym)
            continue

        scored_candidates.append(
            {
                "candidate": cand,
                "symbol": sym,
                "shares": shares,
                "entry_price": entry_tick,
                "stop_price": stop_tick,
                "target_price": target_tick,
                "rr_ratio": rr_ratio,
                "final_score": final_score,
                "est_cost": est_cost,
                "sector": sector,
                "target_note": cand.get("target_note", f"฿{target_tick:.2f}"),
            }
        )

    if not scored_candidates:
        return None, "No candidates passed all risk, sector, liquidity, and R/R gates"

    # Sort by final conviction score descending
    scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    winner = scored_candidates[0]
    reason = (
        f"Selected {winner['symbol']} (Score: {winner['final_score']:.1f}, "
        f"R/R: {winner['rr_ratio']:.2f}R, Sector: {winner['sector']})"
    )
    return winner, reason


def run_autonomous_decision(
    force: bool = False,
    dry_run: bool = False,
    market: str = "TH",
) -> dict[str, Any]:
    """Execute the full autonomous decision cycle for today."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("=== JULES AUTONOMOUS DECISION ENGINE START: %s ===", today_str)

    init_decision_ledger()

    # 1. Idempotency Check
    if not force:
        existing = check_existing_decision(today_str)
        if existing:
            logger.info(
                "Decision for %s already recorded: %s (%s). Skipping run.",
                today_str,
                existing["status"],
                existing.get("symbol") or "None",
            )
            return existing

    # 2. Portfolio Health & Capacity
    status = jf.get_jules_status(market=market)
    open_pos = status["open_positions"]
    cash = float(status["cash_balance"])
    equity = float(status["equity"])
    open_count = int(status["open_count"])

    if open_count >= MAX_POSITIONS:
        msg = f"All {MAX_POSITIONS}/{MAX_POSITIONS} portfolio slots full. Holding cash."
        logger.info(msg)
        if not dry_run:
            record_decision(today_str, "HOLD_CASH", None, None, "PORTFOLIO_FULL", msg)
        return {"status": "HOLD_CASH", "reason": msg}

    if cash < MIN_CASH_REQUIRED:
        msg = f"Cash balance ฿{cash:,.2f} < ฿{MIN_CASH_REQUIRED:,.2f} minimum. Holding cash."
        logger.info(msg)
        if not dry_run:
            record_decision(today_str, "HOLD_CASH", None, None, "INSUFFICIENT_CASH", msg)
        return {"status": "HOLD_CASH", "reason": msg}

    # 3. Circuit Breaker Evaluation
    breaker_allowed, risk_mult, breaker_reason = check_circuit_breakers(market=market)
    if not breaker_allowed:
        logger.warning("Circuit breaker triggered: %s", breaker_reason)
        if not dry_run:
            record_decision(
                today_str, "BLOCKED_CIRCUIT", None, None, "CIRCUIT_BREAKER", breaker_reason
            )
        return {"status": "BLOCKED_CIRCUIT", "reason": breaker_reason}

    # 4. Market Posture Check
    posture_data = get_latest_exposure_posture()
    recom = str(posture_data.get("recommendation", "NORMAL")).upper()
    ceiling = float(posture_data.get("exposure_ceiling_pct", 75))
    if recom == "REDUCE_ONLY" or ceiling <= 20.0:
        msg = f"Market posture is {recom} (Ceiling: {ceiling}%). Prudence gate: holding 100% cash."
        logger.info(msg)
        if not dry_run:
            record_decision(today_str, "HOLD_CASH", None, None, recom, msg)
        return {"status": "HOLD_CASH", "reason": msg}

    # 5. Load Mission Candidates
    if not MISSION_JSON.exists():
        msg = f"Mission file {MISSION_JSON} missing. Run jules_scout.py first."
        logger.warning(msg)
        return {"status": "ERROR", "reason": msg}

    with open(MISSION_JSON, encoding="utf-8") as f:
        mission = json.load(f)

    candidates = mission.get("candidates", [])
    sector_mods = get_sector_momentum_mapping()

    # 6. Evaluate and Pick Best Setup
    winner, select_reason = evaluate_and_select_trade(
        candidates=candidates,
        open_positions=open_pos,
        sector_mods=sector_mods,
        equity=equity,
        cash=cash,
        risk_mult=risk_mult,
    )

    if not winner:
        logger.info("No candidates passed selection: %s", select_reason)
        if not dry_run:
            record_decision(today_str, "HOLD_CASH", None, None, recom, select_reason)
        return {"status": "HOLD_CASH", "reason": select_reason}

    # 7. Stage Valid Order
    sym = winner["symbol"]
    order_id = f"JULES-TH-{datetime.now().strftime('%Y%m%d')}-{sym.replace('.BK', '')}"
    now_dt = datetime.now(timezone.utc)
    # Order valid for opening window (TTL 45 mins)
    expires_dt = datetime.fromtimestamp(now_dt.timestamp() + 2700, tz=timezone.utc)

    order_payload = {
        "order_id": order_id,
        "action": "buy",
        "symbol": sym,
        "shares": winner["shares"],
        "entry_price": winner["entry_price"],
        "stop_price": winner["stop_price"],
        "target_price": winner["target_price"],
        "max_chase_pct": MAX_CHASE_PCT,
        "created_at": now_dt.isoformat(),
        "expires_at": expires_dt.isoformat(),
        "sector": winner["sector"],
        "target_note": winner["target_note"],
        "thesis": (
            f"Autonomous conviction buy: {winner['candidate'].get('highlights', '')} | "
            f"R/R: {winner['rr_ratio']:.2f}R | Sector Momentum: {winner['sector']} | "
            f"Plan: MFE +0.5R ratchet to BE immediately"
        ),
    }

    if dry_run:
        logger.info("[DRY-RUN] Would stage order: %s", order_payload)
        return {"status": "DRY_RUN", "order": order_payload}

    ORDERS_DIR.mkdir(parents=True, exist_ok=True)
    STAGED_ORDERS_DIR.mkdir(parents=True, exist_ok=True)

    order_file_name = f"buy_{sym.replace('.BK', '')}.yaml"
    active_order_path = ORDERS_DIR / order_file_name
    staged_order_path = STAGED_ORDERS_DIR / f"{order_id}.yaml"

    import yaml

    with open(active_order_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(order_payload, f, sort_keys=False)
    with open(staged_order_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(order_payload, f, sort_keys=False)

    record_decision(
        decision_date=today_str,
        status="ORDER_STAGED",
        symbol=sym,
        order_id=order_id,
        posture=recom,
        reason=select_reason,
        payload=order_payload,
    )

    logger.info("Successfully staged order for %s -> %s", sym, active_order_path)
    return {"status": "ORDER_STAGED", "symbol": sym, "order": order_payload}


def main():
    parser = argparse.ArgumentParser(description="Jules AI Autonomous Decision Maker")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    decide_parser = subparsers.add_parser("decide", help="Run autonomous decision cycle")
    decide_parser.add_argument(
        "--force", action="store_true", help="Bypass idempotency ledger check"
    )
    decide_parser.add_argument(
        "--dry-run", action="store_true", help="Simulate decision without writing files"
    )

    subparsers.add_parser("status", help="Show decision ledger status")

    args = parser.parse_args()

    if args.command == "decide":
        res = run_autonomous_decision(force=args.force, dry_run=args.dry_run)
        print(json.dumps(res, indent=2))
    elif args.command == "status":
        init_decision_ledger()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jules_decision_ledger ORDER BY decision_date DESC LIMIT 5"
            ).fetchall()
            for r in rows:
                print(
                    f"[{r['decision_date']}] Status: {r['status']} | Symbol: {r['symbol']} | Reason: {r['reason']}"
                )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
