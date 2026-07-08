"""Auto-paper qualifying ledger signals.

This script opens simulated paper positions only. It never submits broker orders.
Signals must be recent, have an entry price, pass a score threshold, and not
already have an open paper position or prior signal-paper link.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import signal_ledger

PAPER_SCRIPT_DIR = PROJECT_ROOT / "skills" / "paper-trade-simulator" / "scripts"
if str(PAPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PAPER_SCRIPT_DIR))

from paper_trade import open_position  # noqa: E402


@dataclass(frozen=True)
class AutoPaperConfig:
    market: str | None = None
    min_score: float = 70.0
    max_age_days: int = 10
    max_new_positions: int = 3
    max_open_positions: int | None = None
    high_score_override_min: float | None = None
    max_open_positions_with_override: int | None = None
    shares: int = 100
    derive_missing_risk: bool = True
    default_stop_pct: float = 8.0
    target_r: float = 2.0
    source_rules: dict[str, dict[str, float]] = field(default_factory=dict)
    as_of: date | None = None
    dry_run: bool = True


def _as_of(config: AutoPaperConfig) -> date:
    return config.as_of or date.today()


def _open_symbols(conn: sqlite3.Connection, market: str | None = None) -> set[str]:
    where = "WHERE status = 'open'"
    params: list[Any] = []
    if market:
        where += " AND market = ?"
        params.append(market.upper())
    try:
        rows = conn.execute(f"SELECT symbol FROM paper_trade {where}", params).fetchall()
    except sqlite3.OperationalError:
        return set()
    return {r["symbol"].upper() for r in rows}


def _linked_signals(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT signal_id FROM signal_paper_link").fetchall()
    return {r["signal_id"] for r in rows}


def _open_capacity_for_score(config: AutoPaperConfig, score: float | None) -> int | None:
    base_capacity = config.max_open_positions
    if (
        config.high_score_override_min is not None
        and config.max_open_positions_with_override is not None
        and score is not None
        and float(score) >= float(config.high_score_override_min)
    ):
        if base_capacity is None:
            return config.max_open_positions_with_override
        return max(base_capacity, config.max_open_positions_with_override)
    return base_capacity


def _derive_prices(
    signal: sqlite3.Row, config: AutoPaperConfig
) -> tuple[float, float, float] | None:
    entry = signal["entry_price"]
    if entry is None or entry <= 0:
        return None
    stop = signal["stop_price"]
    target = signal["target_price"]
    if (stop is None or target is None) and config.derive_missing_risk:
        risk = entry * (config.default_stop_pct / 100.0)
        stop = entry - risk
        target = entry + (risk * config.target_r)
    if stop is None or target is None:
        return None
    source_rule = config.source_rules.get(signal["source_skill"], {})
    stop_pct_cap = source_rule.get("stop_pct_cap")
    if stop_pct_cap is not None:
        max_risk = entry * (float(stop_pct_cap) / 100.0)
        if entry - stop > max_risk:
            stop = entry - max_risk
    effective_target_r = float(source_rule.get("target_r", config.target_r))
    risk = entry - stop
    capped_target = entry + (risk * effective_target_r)
    if capped_target < target:
        target = capped_target
    if not (0 < stop < entry < target):
        return None
    return float(entry), float(stop), float(target)


def eligible_signals(conn: sqlite3.Connection, config: AutoPaperConfig) -> list[dict[str, Any]]:
    open_symbols = _open_symbols(conn, config.market)

    cutoff = _as_of(config) - timedelta(days=config.max_age_days)
    where = ["raw_score >= ?", "signal_date >= ?"]
    params: list[Any] = [config.min_score, cutoff.isoformat()]
    if config.market:
        where.append("market = ?")
        params.append(config.market.upper())

    rows = conn.execute(
        f"""SELECT *
            FROM signal_ledger
            WHERE {" AND ".join(where)}
            ORDER BY raw_score DESC, signal_date DESC""",
        params,
    ).fetchall()
    reserved_symbols = set(open_symbols)
    linked = _linked_signals(conn)

    out = []
    for row in rows:
        symbol = row["symbol"].upper()
        score = row["raw_score"]
        capacity = _open_capacity_for_score(config, score)
        if row["signal_id"] in linked:
            continue
        if symbol in reserved_symbols:
            continue
        if capacity is not None and len(reserved_symbols) >= capacity:
            continue
        prices = _derive_prices(row, config)
        if prices is None:
            continue
        entry, stop, target = prices
        out.append(
            {
                "signal_id": row["signal_id"],
                "symbol": row["symbol"],
                "market": row["market"],
                "source_skill": row["source_skill"],
                "raw_score": row["raw_score"],
                "signal_date": row["signal_date"],
                "entry": round(entry, 4),
                "stop": round(stop, 4),
                "target": round(target, 4),
                "shares": config.shares,
            }
        )
        reserved_symbols.add(symbol)
    return out[: config.max_new_positions]


def _candidate_from_row(
    row: sqlite3.Row, config: AutoPaperConfig, prices: tuple[float, float, float]
) -> dict[str, Any]:
    entry, stop, target = prices
    return {
        "signal_id": row["signal_id"],
        "symbol": row["symbol"],
        "market": row["market"],
        "source_skill": row["source_skill"],
        "raw_score": row["raw_score"],
        "signal_date": row["signal_date"],
        "entry": round(entry, 4),
        "stop": round(stop, 4),
        "target": round(target, 4),
        "shares": config.shares,
    }


def explain_candidates(
    conn: sqlite3.Connection,
    config: AutoPaperConfig,
    limit: int = 20,
) -> dict[str, Any]:
    """Explain which ledger signals pass or fail the auto-paper gate.

    This is read-only and intentionally mirrors `eligible_signals` so the
    dashboard can show why promising signals were skipped without opening paper
    positions.
    """
    cutoff = _as_of(config) - timedelta(days=config.max_age_days)
    where = []
    params: list[Any] = []
    if config.market:
        where.append("market = ?")
        params.append(config.market.upper())
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"""SELECT *
            FROM signal_ledger
            {where_sql}
            ORDER BY raw_score DESC, signal_date DESC
            LIMIT ?""",
        [*params, max(limit, config.max_new_positions * 3)],
    ).fetchall()
    open_symbols = _open_symbols(conn, config.market)
    selected_symbols: set[str] = set()
    linked = _linked_signals(conn)

    passed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in rows:
        reasons = []
        symbol = row["symbol"].upper()
        score = row["raw_score"]
        signal_date = date.fromisoformat(row["signal_date"])
        age_days = (_as_of(config) - signal_date).days
        if score is None or float(score) < config.min_score:
            reasons.append(
                f"score {score if score is not None else 'missing'} < {config.min_score:g}"
            )
        if signal_date < cutoff:
            reasons.append(f"age {age_days}d > {config.max_age_days}d")
        if row["signal_id"] in linked:
            reasons.append("already linked to paper")
        if symbol in open_symbols:
            reasons.append("symbol already open")
        if symbol in selected_symbols:
            reasons.append("symbol already selected this run")
        capacity = _open_capacity_for_score(config, score)
        if capacity is not None and len(open_symbols) + len(selected_symbols) >= capacity:
            reasons.append(f"open capacity {capacity} reached")
        prices = _derive_prices(row, config)
        if prices is None:
            reasons.append("missing or invalid entry/stop/target")

        base = {
            "signal_id": row["signal_id"],
            "symbol": row["symbol"],
            "market": row["market"],
            "source_skill": row["source_skill"],
            "raw_score": score,
            "signal_date": row["signal_date"],
            "age_days": age_days,
        }
        if reasons:
            skipped.append({**base, "reasons": reasons})
            continue
        passed.append(_candidate_from_row(row, config, prices))
        selected_symbols.add(symbol)

    selected = passed[: config.max_new_positions]
    overflow = passed[config.max_new_positions :]
    for row in overflow:
        skipped.append(
            {
                **{
                    k: row.get(k)
                    for k in (
                        "signal_id",
                        "symbol",
                        "market",
                        "source_skill",
                        "raw_score",
                        "signal_date",
                    )
                },
                "reasons": [f"ranked below max_new_positions={config.max_new_positions}"],
            }
        )

    return {
        "selected": selected,
        "skipped": skipped[:limit],
        "passed_before_position_limit": len(passed),
        "cutoff_date": cutoff.isoformat(),
    }


def link_signal_to_paper(
    conn: sqlite3.Connection, signal_id: str, paper_trade_id: int, mode: str = "auto"
) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO signal_paper_link
           (signal_id, paper_trade_id, opened_at, mode)
           VALUES (?,?,?,?)""",
        (
            signal_id,
            paper_trade_id,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            mode,
        ),
    )
    conn.commit()


def run_auto_paper(
    conn: sqlite3.Connection,
    config: AutoPaperConfig,
    open_fn: Callable[..., dict[str, Any]] = open_position,
) -> dict[str, Any]:
    candidates = eligible_signals(conn, config)
    opened = []
    for candidate in candidates:
        if config.dry_run:
            continue
        row = open_fn(
            symbol=candidate["symbol"],
            market=candidate["market"],
            shares=int(candidate["shares"]),
            entry=float(candidate["entry"]),
            stop=float(candidate["stop"]),
            target=float(candidate["target"]),
            side="long",
            source=candidate["source_skill"],
            source_score=candidate["raw_score"],
            notes=(
                "AUTO-PAPER from signal ledger "
                f"{candidate['signal_id']} | signal_date={candidate['signal_date']}"
            ),
            emotion="calm",
        )
        link_signal_to_paper(conn, candidate["signal_id"], int(row["id"]))
        opened.append({"signal_id": candidate["signal_id"], "paper_trade_id": row["id"]})

    return {
        "dry_run": config.dry_run,
        "eligible": len(candidates),
        "opened": len(opened),
        "candidates": candidates,
        "opened_links": opened,
        "config": {
            "market": config.market,
            "min_score": config.min_score,
            "max_age_days": config.max_age_days,
            "max_new_positions": config.max_new_positions,
            "max_open_positions": config.max_open_positions,
            "high_score_override_min": config.high_score_override_min,
            "max_open_positions_with_override": config.max_open_positions_with_override,
            "shares": config.shares,
            "derive_missing_risk": config.derive_missing_risk,
            "default_stop_pct": config.default_stop_pct,
            "target_r": config.target_r,
            "source_rules": config.source_rules,
            "as_of": _as_of(config).isoformat(),
        },
    }


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auto-open paper trades from signal ledger")
    parser.add_argument("--db-path", default=str(signal_ledger.DEFAULT_DB_PATH))
    parser.add_argument("--market", choices=["US", "TH"])
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--max-age-days", type=int, default=10)
    parser.add_argument("--max-new-positions", type=int, default=3)
    parser.add_argument("--max-open-positions", type=int)
    parser.add_argument("--high-score-override-min", type=float)
    parser.add_argument("--max-open-positions-with-override", type=int)
    parser.add_argument("--shares", type=int, default=100)
    parser.add_argument("--default-stop-pct", type=float, default=8.0)
    parser.add_argument("--target-r", type=float, default=2.0)
    parser.add_argument("--as-of")
    parser.add_argument("--execute", action="store_true", help="Actually open paper positions")
    parser.add_argument(
        "--require-explicit-risk",
        action="store_true",
        help="Skip signals missing stop/target instead of deriving default risk.",
    )
    args = parser.parse_args(argv)

    config = AutoPaperConfig(
        market=args.market,
        min_score=args.min_score,
        max_age_days=args.max_age_days,
        max_new_positions=args.max_new_positions,
        max_open_positions=args.max_open_positions,
        high_score_override_min=args.high_score_override_min,
        max_open_positions_with_override=args.max_open_positions_with_override,
        shares=args.shares,
        derive_missing_risk=not args.require_explicit_risk,
        default_stop_pct=args.default_stop_pct,
        target_r=args.target_r,
        as_of=date.fromisoformat(args.as_of) if args.as_of else None,
        dry_run=not args.execute,
    )
    with signal_ledger.connect(args.db_path) as conn:
        result = run_auto_paper(conn, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
