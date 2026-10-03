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
ORDERS_DIR_TH = PROJECT_ROOT / "state" / "jules_orders"
ORDERS_DIR_US = PROJECT_ROOT / "state" / "jules_us_orders"
MISSION_JSON_TH = PROJECT_ROOT / "state" / "jules_tasks" / "today_mission.json"
MISSION_JSON_US = PROJECT_ROOT / "state" / "jules_us_tasks" / "today_mission.json"

# Backwards compatibility defaults
ORDERS_DIR = ORDERS_DIR_TH
STAGED_ORDERS_DIR = ORDERS_DIR / "staged"
PROCESSED_ORDERS_DIR = ORDERS_DIR / "processed"
QUARANTINE_ORDERS_DIR = ORDERS_DIR / "quarantine"
MISSION_JSON = MISSION_JSON_TH
LEARNINGS_YAML = PROJECT_ROOT / "state" / "jules_memory" / "learnings.yaml"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Quantitative Limits & Guardrails
MAX_POSITIONS = 4
BASE_RISK_PER_TRADE_PCT = 0.010  # 1.0% portfolio risk

# TH Limits
MIN_CASH_REQUIRED_TH = 5000.0
MAX_SLOT_BUDGET_TH = 7500.0

# US Limits ($1,000 Starting Fund)
MIN_CASH_REQUIRED_US = 50.0  # $50.0 USD minimum cash
MAX_SLOT_BUDGET_US = 250.0  # $250.0 USD max slot (1000 / 4)

# Backward-compat aliases
MIN_CASH_REQUIRED = MIN_CASH_REQUIRED_TH
MAX_SLOT_BUDGET = MAX_SLOT_BUDGET_TH

MIN_ADTV_THB = 15_000_000.0  # 15M THB minimum daily turnover
MAX_CHASE_PCT = 0.010  # 1.0% max chase limit above trigger


def get_trader_paths(market: str = "TH") -> tuple[Path, Path, Path, Path, Path]:
    market_clean = market.upper()
    if market_clean == "US":
        orders_dir = ORDERS_DIR_US
        mission_json = MISSION_JSON_US
    else:
        orders_dir = ORDERS_DIR_TH
        mission_json = MISSION_JSON_TH
    staged = orders_dir / "staged"
    processed = orders_dir / "processed"
    quarantine = orders_dir / "quarantine"
    return orders_dir, staged, processed, quarantine, mission_json


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


def calculate_order_expiry(now_dt: datetime, market: str = "TH") -> datetime:
    """Calculate order expiration TTL.

    Ensures pre-market staged orders remain valid through the market opening execution
    window rather than expiring prematurely before the opening bell.
    - TH: Valid at least through 11:00 ICT (04:00 UTC) or now + 45m.
    - US: Valid at least through 10:30 ET (15:00 UTC) or now + 45m.
    """
    default_expiry = datetime.fromtimestamp(now_dt.timestamp() + 2700, tz=timezone.utc)
    m = market.upper()
    if m == "TH":
        today_open_cutoff = now_dt.replace(hour=4, minute=0, second=0, microsecond=0)
        if now_dt < today_open_cutoff:
            return max(default_expiry, today_open_cutoff)
    elif m == "US":
        today_open_cutoff = now_dt.replace(hour=15, minute=0, second=0, microsecond=0)
        if now_dt < today_open_cutoff:
            return max(default_expiry, today_open_cutoff)
    return default_expiry


def init_decision_ledger(db_path: Path | None = None) -> None:
    """Initialize SQLite decision ledger table for guaranteed idempotency."""
    if db_path is None:
        db_path = DB_PATH
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS jules_decision_ledger (
                decision_date TEXT,
                market TEXT DEFAULT 'TH',
                status TEXT NOT NULL,
                symbol TEXT,
                order_id TEXT,
                decided_at TEXT NOT NULL,
                posture TEXT,
                reason TEXT NOT NULL,
                payload_json TEXT,
                PRIMARY KEY (decision_date, market)
            )"""
        )
        cursor = conn.execute("PRAGMA table_info(jules_decision_ledger)")
        cols = [r[1] for r in cursor.fetchall()]
        if "market" not in cols:
            conn.execute("ALTER TABLE jules_decision_ledger ADD COLUMN market TEXT DEFAULT 'TH'")
        conn.commit()


def check_existing_decision(
    decision_date: str, market: str = "TH", db_path: Path | None = None
) -> dict[str, Any] | None:
    """Check if an autonomous decision was already made today."""
    if db_path is None:
        db_path = DB_PATH
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("PRAGMA table_info(jules_decision_ledger)")
            cols = [r[1] for r in cursor.fetchall()]
            if "market" in cols:
                row = conn.execute(
                    "SELECT * FROM jules_decision_ledger WHERE decision_date = ? AND (market = ? OR (market IS NULL AND ? = 'TH'))",
                    (decision_date, market.upper(), market.upper()),
                ).fetchone()
            else:
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
    market: str = "TH",
    db_path: Path | None = None,
) -> None:
    """Record an autonomous decision to the persistent ledger."""
    if db_path is None:
        db_path = DB_PATH
    init_decision_ledger(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    payload_str = json.dumps(payload or {})
    market_clean = market.upper()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO jules_decision_ledger
               (decision_date, market, status, symbol, order_id, decided_at, posture, reason, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                decision_date,
                market_clean,
                status,
                symbol,
                order_id,
                now_iso,
                posture,
                reason,
                payload_str,
            ),
        )
        conn.commit()


def check_circuit_breakers(market: str = "TH") -> tuple[bool, float, str]:
    """Check portfolio drawdown and consecutive losses.
    Returns: (is_allowed, risk_multiplier, reason)"""
    market_clean = market.upper()
    closed = paper_trade.list_positions(
        status_filter="closed", market=market_clean, portfolio="jules"
    )
    stats = paper_trade.compute_stats(market=market_clean, portfolio="jules")

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
    initial_cap = jf.INITIAL_CAPITAL_US if market_clean == "US" else jf.INITIAL_CAPITAL
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


def get_latest_exposure_posture(market: str = "TH") -> dict[str, Any]:
    """Read the latest exposure posture report or calculate US breadth posture."""
    market_clean = market.upper()
    if market_clean == "US":
        try:
            import src.trading_view_client as tv_client

            breadth = tv_client.get_us_breadth(limit=1000)
            pct_50 = breadth.get("pct_above_sma50", 50.0)
            if pct_50 >= 45.0:
                return {
                    "recommendation": "NORMAL",
                    "exposure_ceiling_pct": 100.0,
                    "details": f"{pct_50:.1f}% > 50d SMA",
                }
            elif pct_50 >= 25.0:
                return {
                    "recommendation": "DEFENSIVE",
                    "exposure_ceiling_pct": 50.0,
                    "details": f"{pct_50:.1f}% > 50d SMA",
                }
            else:
                return {
                    "recommendation": "REDUCE_ONLY",
                    "exposure_ceiling_pct": 0.0,
                    "details": f"{pct_50:.1f}% > 50d SMA",
                }
        except Exception as e:
            logger.debug("Failed to fetch US breadth for posture: %s", e)
            return {"recommendation": "NORMAL", "exposure_ceiling_pct": 75.0}

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
    market: str = "TH",
) -> tuple[int, float]:
    """Calculate volatility/risk-adjusted position size."""
    market_clean = market.upper()
    if market_clean == "US":
        price = round(price, 2)
        stop = round(stop, 2)
        risk_per_share = max(0.01, round(price - stop, 2))
        target_dollar_risk = equity * BASE_RISK_PER_TRADE_PCT * risk_mult
        raw_risk_shares = int(target_dollar_risk / risk_per_share) if risk_per_share > 0 else 0

        max_capital_for_trade = min(MAX_SLOT_BUDGET_US, cash * 0.95)
        max_cap_shares = int(max_capital_for_trade / price) if price > 0 else 0

        allowed_shares = min(raw_risk_shares, max_cap_shares)
        if allowed_shares <= 0:
            return 0, 0.0
        shares = allowed_shares
        est_cost = round(price * shares, 2)
        if est_cost > cash and price > 0:
            shares = int(cash / price)
            est_cost = round(price * shares, 2)
        return shares, est_cost

    price = round_to_set_tick(price, "up")
    stop = round_to_set_tick(stop, "down")
    risk_per_share = max(set_tick_size(price) * Decimal("2"), Decimal(str(price - stop)))
    risk_per_share_float = float(risk_per_share)

    # 1.0% portfolio risk * risk_multiplier
    target_dollar_risk = equity * BASE_RISK_PER_TRADE_PCT * risk_mult
    raw_risk_shares = (
        int(target_dollar_risk / risk_per_share_float) if risk_per_share_float > 0 else 0
    )

    # Capital constraint (max slot budget ฿7,500 or remaining cash)
    max_capital_for_trade = min(MAX_SLOT_BUDGET_TH, cash * 0.95)
    max_cap_shares = int(max_capital_for_trade / price) if price > 0 else 0

    allowed_shares = min(raw_risk_shares, max_cap_shares)
    board_lot_shares = (allowed_shares // 100) * 100
    if board_lot_shares < 100:
        return 0, 0.0

    est_cost = round(price * board_lot_shares, 2)
    if est_cost > cash and price > 0:
        board_lot_shares = (int(cash / price) // 100) * 100
        est_cost = round(price * board_lot_shares, 2)

    return board_lot_shares, est_cost


def evaluate_and_select_trade(
    candidates: list[dict[str, Any]],
    open_positions: list[dict[str, Any]],
    sector_mods: dict[str, float],
    equity: float,
    cash: float,
    risk_mult: float = 1.0,
    market: str = "TH",
) -> tuple[dict[str, Any] | None, str]:
    """Filter and rank candidates according to liquidity, sector, and risk-reward gates."""
    if not candidates:
        return None, "No candidates provided in mission"

    market_clean = market.upper()
    curr_sym = "$" if market_clean == "US" else "฿"

    open_sectors = {
        p.get("sector") for p in open_positions if p.get("sector") and p.get("sector") != "N/A"
    }
    open_clusters = {p.get("cluster") for p in open_positions if p.get("cluster")}

    scored_candidates = []
    for cand in candidates:
        sym = cand["symbol"]
        price = float(cand.get("price") or 0.0)
        stop = float(cand.get("stop") or 0.0)
        target = float(cand.get("target") or 0.0)
        sector = cand.get("sector", "N/A")
        cluster = cand.get("cluster")

        if price <= 0 or stop <= 0 or target <= 0 or stop >= price or target <= price:
            continue

        if market_clean == "US":
            entry_tick = round(price, 2)
            stop_tick = round(stop, 2)
            target_tick = round(target, 2)
        else:
            # Discretize levels to valid SET ticks
            entry_tick = round_to_set_tick(price, "up")
            stop_tick = round_to_set_tick(stop, "down")
            target_tick = round_to_set_tick(target, "down")

        # Anti-Correlation Sector & Cluster Gate: Max 1 position per sector/cluster
        if cluster and cluster in open_clusters:
            logger.info(
                "Candidate %s rejected: cluster %s already active in portfolio", sym, cluster
            )
            continue
        if sector in open_sectors and sector not in ("N/A", "Unknown", "Volume Surge"):
            logger.info("Candidate %s rejected: sector %s already active in portfolio", sym, sector)
            continue

        # Stop Width Sanity Gate: Enforce minimum 4.5% stop width floor to eliminate noise whipouts
        raw_stop_pct = ((entry_tick - stop_tick) / entry_tick) * 100.0
        if raw_stop_pct < 4.5:
            # Clamp stop to 4.5% floor to prevent intraday noise whipouts & fee drag
            if market_clean == "US":
                stop_tick = round(entry_tick * 0.955, 2)
            else:
                stop_tick = round_to_set_tick(entry_tick * 0.955, "down")
            risk_dist = entry_tick - stop_tick
            stop_pct = (risk_dist / entry_tick) * 100.0
        else:
            risk_dist = entry_tick - stop_tick
            stop_pct = raw_stop_pct

        if stop_pct > 7.5:
            logger.info("Candidate %s rejected: stop width %.1f%% exceeds 7.5%% max", sym, stop_pct)
            continue

        # Two-Tier Target Calculation: T1 = 1.5R (50% scale-out), T2 = 2.5R (runner)
        if market_clean == "US":
            t1_price = round(entry_tick + (risk_dist * 1.5), 2)
            t2_price = round(entry_tick + (risk_dist * 2.5), 2)
        else:
            t1_price = round_to_set_tick(entry_tick + (risk_dist * 1.5), "down")
            t2_price = round_to_set_tick(entry_tick + (risk_dist * 2.5), "down")

        final_target = max(t2_price, target_tick)
        reward_dist = final_target - entry_tick
        rr_ratio = reward_dist / risk_dist if risk_dist > 0 else 0.0
        if rr_ratio < 1.45:
            logger.info("Candidate %s rejected: R/R ratio %.2f < 1.5R", sym, rr_ratio)
            continue

        # Sector Momentum Modifier (for TH)
        sector_bonus = sector_mods.get(sector, 0.0)
        if sector_bonus < -20.0:
            logger.info("Candidate %s rejected: lagging sector %s (-25 pts penalty)", sym, sector)
            continue

        # NVDR Institutional Flow Divergence Filter (for TH)
        nvdr_bonus = 0.0
        nvdr_status = "N/A"
        if market_clean == "TH":
            try:
                from scripts.nvdr_flow_filter import analyze_nvdr_divergence

                price_chg = float(cand.get("price_change_pct") or 1.0)
                nvdr_res = analyze_nvdr_divergence(
                    sym, current_price=entry_tick, price_change_pct=price_chg
                )
                nvdr_bonus = nvdr_res.score_modifier
                nvdr_status = nvdr_res.status
                if nvdr_res.is_bull_trap:
                    logger.info(
                        "Candidate %s rejected: NVDR bull trap divergence (%s)",
                        sym,
                        nvdr_res.details,
                    )
                    continue
            except Exception as e:
                logger.debug("NVDR filter check failed for %s: %s", sym, e)

        base_score = float(cand.get("score") or 60.0)
        final_score = base_score + sector_bonus + nvdr_bonus

        shares, est_cost = calculate_volatility_sizing(
            entry_tick, stop_tick, equity, cash, risk_mult, market=market_clean
        )
        min_shares = 1 if market_clean == "US" else 100
        if shares < min_shares or est_cost > cash:
            logger.info(
                "Candidate %s rejected: insufficient cash for sizing (%d shares, cost %s%.2f > %s%.2f)",
                sym,
                shares,
                curr_sym,
                est_cost,
                curr_sym,
                cash,
            )
            continue

        scored_candidates.append(
            {
                "candidate": cand,
                "symbol": sym,
                "shares": shares,
                "entry_price": entry_tick,
                "stop_price": stop_tick,
                "target_price": final_target,
                "t1_price": t1_price,
                "t2_price": t2_price,
                "rr_ratio": rr_ratio,
                "final_score": final_score,
                "nvdr_status": nvdr_status,
                "nvdr_bonus": nvdr_bonus,
                "est_cost": est_cost,
                "sector": sector,
                "cluster": cluster,
                "target_note": f"T1: {curr_sym}{t1_price:.2f} (1.5R) | T2: {curr_sym}{t2_price:.2f} (2.5R)",
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
    market_clean = market.upper()
    curr_sym = "$" if market_clean == "US" else "฿"
    min_cash_required = MIN_CASH_REQUIRED_US if market_clean == "US" else MIN_CASH_REQUIRED_TH

    orders_dir, staged_orders_dir, _, _, mission_json = get_trader_paths(market_clean)
    if market_clean == "TH":
        # Respect unittests patching jt.ORDERS_DIR, jt.STAGED_ORDERS_DIR, jt.MISSION_JSON
        orders_dir = ORDERS_DIR
        staged_orders_dir = STAGED_ORDERS_DIR
        mission_json = MISSION_JSON

    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("=== JULES AUTONOMOUS DECISION ENGINE (%s) START: %s ===", market_clean, today_str)

    init_decision_ledger()

    # 1. Idempotency Check
    if not force:
        existing = check_existing_decision(today_str, market=market_clean)
        if existing:
            logger.info(
                "Decision for %s (%s) already recorded: %s (%s). Skipping run.",
                today_str,
                market_clean,
                existing["status"],
                existing.get("symbol") or "None",
            )
            return existing

    # 2. Portfolio Health & Capacity
    status = jf.get_jules_status(market=market_clean)
    open_pos = status["open_positions"]
    cash = float(status["cash_balance"])
    equity = float(status["equity"])
    open_count = int(status["open_count"])

    if open_count >= MAX_POSITIONS:
        msg = f"All {MAX_POSITIONS}/{MAX_POSITIONS} portfolio slots full. Holding cash."
        logger.info(msg)
        if not dry_run:
            record_decision(
                today_str, "HOLD_CASH", None, None, "PORTFOLIO_FULL", msg, market=market_clean
            )
        return {"status": "HOLD_CASH", "reason": msg}

    if cash < min_cash_required:
        msg = f"Cash balance {curr_sym}{cash:,.2f} < {curr_sym}{min_cash_required:,.2f} minimum. Holding cash."
        logger.info(msg)
        if not dry_run:
            record_decision(
                today_str, "HOLD_CASH", None, None, "INSUFFICIENT_CASH", msg, market=market_clean
            )
        return {"status": "HOLD_CASH", "reason": msg}

    # 3. Circuit Breaker Evaluation
    breaker_allowed, risk_mult, breaker_reason = check_circuit_breakers(market=market_clean)
    if not breaker_allowed:
        logger.warning("Circuit breaker triggered: %s", breaker_reason)
        if not dry_run:
            record_decision(
                today_str,
                "BLOCKED_CIRCUIT",
                None,
                None,
                "CIRCUIT_BREAKER",
                breaker_reason,
                market=market_clean,
            )
        return {"status": "BLOCKED_CIRCUIT", "reason": breaker_reason}

    # 4. Market Posture Check
    posture_data = get_latest_exposure_posture(market=market_clean)
    recom = str(posture_data.get("recommendation", "NORMAL")).upper()
    ceiling = float(posture_data.get("exposure_ceiling_pct", 75))
    if recom == "REDUCE_ONLY" or ceiling <= 20.0:
        msg = f"Market posture is {recom} (Ceiling: {ceiling}%). Prudence gate: holding 100% cash."
        logger.info(msg)
        if not dry_run:
            record_decision(today_str, "HOLD_CASH", None, None, recom, msg, market=market_clean)
        return {"status": "HOLD_CASH", "reason": msg}

    # 5. Load Mission Candidates
    if not mission_json.exists():
        msg = f"Mission file {mission_json} missing. Run jules_scout.py first."
        logger.warning(msg)
        return {"status": "ERROR", "reason": msg}

    with open(mission_json, encoding="utf-8") as f:
        mission = json.load(f)

    candidates = mission.get("candidates", [])
    sector_mods = get_sector_momentum_mapping() if market_clean == "TH" else {}

    # 6. Evaluate and Pick Best Setup
    winner, select_reason = evaluate_and_select_trade(
        candidates=candidates,
        open_positions=open_pos,
        sector_mods=sector_mods,
        equity=equity,
        cash=cash,
        risk_mult=risk_mult,
        market=market_clean,
    )

    if not winner:
        logger.info("No candidates passed selection: %s", select_reason)
        if not dry_run:
            record_decision(
                today_str, "HOLD_CASH", None, None, recom, select_reason, market=market_clean
            )
        return {"status": "HOLD_CASH", "reason": select_reason}

    # 7. Stage Valid Order
    sym = winner["symbol"]
    order_id = f"JULES-{market_clean}-{datetime.now().strftime('%Y%m%d')}-{sym.replace('.BK', '')}"
    now_dt = datetime.now(timezone.utc)
    # Order valid for opening window (TTL aware of market open)
    expires_dt = calculate_order_expiry(now_dt, market=market_clean)

    order_payload = {
        "order_id": order_id,
        "action": "buy",
        "symbol": sym,
        "market": market_clean,
        "shares": winner["shares"],
        "entry_price": winner["entry_price"],
        "stop_price": winner["stop_price"],
        "target_price": winner["target_price"],
        "t1_price": winner.get("t1_price"),
        "t2_price": winner.get("t2_price"),
        "max_chase_pct": MAX_CHASE_PCT,
        "created_at": now_dt.isoformat(),
        "expires_at": expires_dt.isoformat(),
        "sector": winner["sector"],
        "cluster": winner.get("cluster"),
        "target_note": winner["target_note"],
        "thesis": (
            f"Autonomous conviction buy: {winner['candidate'].get('highlights', '')} | "
            f"R/R: {winner['rr_ratio']:.2f}R | Sector/Cluster: {winner.get('cluster') or winner['sector']} | "
            f"Plan: Scale-out 50% at T1 ({curr_sym}{winner.get('t1_price', 0):.2f}, 1.5R), shift stop to BE, trail runner to T2 ({curr_sym}{winner.get('t2_price', 0):.2f}, 2.5R)"
        ),
    }

    if dry_run:
        logger.info("[DRY-RUN] Would stage order: %s", order_payload)
        return {"status": "DRY_RUN", "order": order_payload}

    orders_dir.mkdir(parents=True, exist_ok=True)
    staged_orders_dir.mkdir(parents=True, exist_ok=True)

    order_file_name = f"buy_{sym.replace('.BK', '')}.yaml"
    active_order_path = orders_dir / order_file_name
    staged_order_path = staged_orders_dir / f"{order_id}.yaml"

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
        market=market_clean,
    )

    try:
        from scripts.notify_service import notify_order_staged

        notify_order_staged(order_payload)
    except Exception as notify_err:
        logger.debug("Notification dispatch skipped or failed: %s", notify_err)

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
    decide_parser.add_argument(
        "--market", choices=["TH", "US"], default="TH", help="Target equity market (TH or US)"
    )

    status_parser = subparsers.add_parser("status", help="Show decision ledger status")
    status_parser.add_argument(
        "--market", choices=["TH", "US"], default="TH", help="Target equity market (TH or US)"
    )

    args = parser.parse_args()

    if args.command == "decide":
        res = run_autonomous_decision(force=args.force, dry_run=args.dry_run, market=args.market)
        print(json.dumps(res, indent=2))
    elif args.command == "status":
        init_decision_ledger()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jules_decision_ledger WHERE market = ? ORDER BY decision_date DESC LIMIT 5",
                (args.market,),
            ).fetchall()
            for r in rows:
                print(
                    f"[{r['decision_date']} | {r['market']}] Status: {r['status']} | Symbol: {r['symbol']} | Reason: {r['reason']}"
                )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
