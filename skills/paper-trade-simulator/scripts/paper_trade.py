#!/usr/bin/env python3
"""Paper Trade Simulator — core CRUD + stats.

Subcommands:
    open      Open a new paper position
    close     Close an open position manually
    list      List positions (open/closed/all)
    stats     Show portfolio statistics
    journal   Add/update journal entry on a trade
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "state" / "market_cache.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_trade (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT    NOT NULL,
    market          TEXT    NOT NULL,
    side            TEXT    NOT NULL DEFAULT 'long',
    status          TEXT    NOT NULL,

    entry_price     REAL    NOT NULL,
    entry_at        TEXT    NOT NULL,
    shares          INTEGER NOT NULL,
    stop_price      REAL    NOT NULL,
    target_price    REAL    NOT NULL,
    initial_risk    REAL    NOT NULL,
    source          TEXT,
    source_score    REAL,
    notes_entry     TEXT,

    exit_price      REAL,
    exit_at         TEXT,
    realized_pnl    REAL,
    realized_r      REAL,
    gross_realized_pnl REAL,
    transaction_cost_bps REAL NOT NULL DEFAULT 0,
    entry_cost      REAL NOT NULL DEFAULT 0,
    exit_cost       REAL NOT NULL DEFAULT 0,

    last_price      REAL,
    last_updated    TEXT,
    unrealized_pnl  REAL,
    unrealized_r    REAL,
    mae             REAL,
    mfe             REAL,

    journal_emotion TEXT,
    journal_text    TEXT,

    days_held       INTEGER
);
CREATE INDEX IF NOT EXISTS idx_paper_status ON paper_trade(status);
CREATE INDEX IF NOT EXISTS idx_paper_symbol ON paper_trade(symbol);
"""

VALID_EMOTIONS = {"calm", "fearful", "greedy", "frustrated", "fomo", "confident", "uncertain"}
STATUS_OPEN = "open"
STATUS_CLOSED_STOP = "closed_stop"
STATUS_CLOSED_TARGET = "closed_target"
STATUS_CLOSED_TIME = "closed_time"
STATUS_CLOSED_MANUAL = "closed_manual"
CLOSED_STATUSES = (
    STATUS_CLOSED_STOP,
    STATUS_CLOSED_TARGET,
    STATUS_CLOSED_TIME,
    STATUS_CLOSED_MANUAL,
)
SOURCE_ALIASES = {
    "vcp": "vcp-screener",
    "vcp_screener": "vcp-screener",
    "canslim": "canslim-screener",
    "canslim_screener": "canslim-screener",
}


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(paper_trade)").fetchall()}
    migrations = {
        "gross_realized_pnl": "REAL",
        "transaction_cost_bps": "REAL NOT NULL DEFAULT 0",
        "entry_cost": "REAL NOT NULL DEFAULT 0",
        "exit_cost": "REAL NOT NULL DEFAULT 0",
    }
    for column, definition in migrations.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE paper_trade ADD COLUMN {column} {definition}")
    return conn


_trade_db = _db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def normalize_source(source: str | None) -> str:
    value = (source or "manual").strip().lower().replace(" ", "-")
    return SOURCE_ALIASES.get(value, value)


def check_discipline_warnings() -> dict[str, Any]:
    """Check recent trade history for discipline issues (low stop respect, FOMO streak)."""
    with _db() as conn:
        closed = conn.execute(
            """SELECT status, realized_r, journal_emotion FROM paper_trade
               WHERE status != 'open'
               ORDER BY exit_at DESC LIMIT 5"""
        ).fetchall()

    if not closed:
        return {"stop_respect_rate": None, "fomo_streak": False, "warnings": []}

    n_stop = sum(1 for r in closed if r["status"] == STATUS_CLOSED_STOP)
    n_manual_loss = sum(
        1 for r in closed if r["status"] == STATUS_CLOSED_MANUAL and (r["realized_r"] or 0) < 0
    )

    stop_respect = (n_stop / (n_stop + n_manual_loss)) if (n_stop + n_manual_loss) > 0 else None

    recent_emotions = [r["journal_emotion"] for r in closed if r["journal_emotion"] is not None]
    fomo_count = sum(1 for e in recent_emotions if e in ("fomo", "greedy", "frustrated"))
    fomo_streak = fomo_count >= 2

    warnings = []
    if stop_respect is not None and stop_respect < 0.8:
        warnings.append(
            f"Low Stop Respect Rate ({stop_respect:.0%}): You are overriding stops or taking large manual losses. Stick to your stop rules!"
        )
    if fomo_streak:
        warnings.append(
            "Emotional Risk: Recent trades show FOMO, greed, or frustration. Suggest waiting 24h or reducing position size by 50%."
        )

    return {
        "stop_respect_rate": stop_respect,
        "fomo_streak": fomo_streak,
        "recent_emotions": recent_emotions,
        "warnings": warnings,
    }


# ── Core actions ────────────────────────────────────────────────────────────


def open_position(
    symbol: str,
    market: str,
    shares: int,
    entry: float,
    stop: float,
    target: float,
    side: str = "long",
    source: str | None = None,
    source_score: float | None = None,
    notes: str | None = None,
    emotion: str | None = None,
    transaction_cost_bps: float = 0.0,
) -> dict[str, Any]:
    """Open a new paper position. Returns the created row."""
    if shares <= 0:
        raise ValueError("shares must be > 0")
    if entry <= 0 or stop <= 0 or target <= 0:
        raise ValueError("entry/stop/target must be > 0")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be >= 0")
    if side == "long":
        if stop >= entry:
            raise ValueError("for long, stop must be < entry")
        if target <= entry:
            raise ValueError("for long, target must be > entry")
        initial_risk = abs(entry - stop) * shares
    else:  # short
        if stop <= entry:
            raise ValueError("for short, stop must be > entry")
        if target >= entry:
            raise ValueError("for short, target must be < entry")
        initial_risk = abs(entry - stop) * shares

    if emotion and emotion not in VALID_EMOTIONS:
        raise ValueError(f"emotion must be one of {sorted(VALID_EMOTIONS)}")

    warnings = []
    try:
        warnings = check_discipline_warnings()["warnings"]
    except Exception as e:
        logger.exception("Error checking discipline warnings from DB")
        warnings = [f"An error occurred while checking discipline warnings: {e}"]

    now = _now_iso()
    entry_cost = entry * shares * transaction_cost_bps / 10_000
    with _trade_db() as conn:
        cur = conn.execute(
            """INSERT INTO paper_trade
               (symbol, market, side, status, entry_price, entry_at, shares,
                stop_price, target_price, initial_risk, source, source_score,
                 notes_entry, transaction_cost_bps, entry_cost, exit_cost, last_price, last_updated, unrealized_pnl, unrealized_r,
                mae, mfe, journal_emotion, days_held)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                symbol.upper(),
                market.upper(),
                side,
                STATUS_OPEN,
                entry,
                now,
                shares,
                stop,
                target,
                initial_risk,
                normalize_source(source) if source else None,
                source_score,
                notes,
                transaction_cost_bps,
                entry_cost,
                0.0,
                entry,
                now,
                0.0,
                0.0,
                entry,
                entry,
                emotion,
                0,
            ),
        )
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM paper_trade WHERE id=?", (new_id,)).fetchone()
        row_dict = _row_to_dict(row)
        row_dict["discipline_warnings"] = warnings
    return row_dict


def close_position(
    trade_id: int,
    exit_price: float,
    status: str = STATUS_CLOSED_MANUAL,
    emotion: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Close an open position with the given exit price."""
    if exit_price <= 0:
        raise ValueError("exit_price must be > 0")
    if status not in CLOSED_STATUSES:
        raise ValueError(f"status must be one of {CLOSED_STATUSES}")
    if emotion and emotion not in VALID_EMOTIONS:
        raise ValueError(f"emotion must be one of {sorted(VALID_EMOTIONS)}")

    with _db() as conn:
        row = conn.execute("SELECT * FROM paper_trade WHERE id=?", (trade_id,)).fetchone()
        if row is None:
            raise ValueError(f"trade id {trade_id} not found")
        if row["status"] != STATUS_OPEN:
            raise ValueError(f"trade {trade_id} is already closed (status={row['status']})")

        side = row["side"]
        entry = row["entry_price"]
        shares = row["shares"]
        initial_risk_per_share = (
            (entry - row["stop_price"]) if side == "long" else (row["stop_price"] - entry)
        )

        if side == "long":
            gross_pnl = (exit_price - entry) * shares
        else:
            gross_pnl = (entry - exit_price) * shares
        entry_cost = row["entry_cost"] or 0.0
        exit_cost = exit_price * shares * (row["transaction_cost_bps"] or 0.0) / 10_000
        pnl = gross_pnl - entry_cost - exit_cost

        realized_r = pnl / (initial_risk_per_share * shares) if initial_risk_per_share > 0 else 0
        now = _now_iso()
        days_held = (
            datetime.fromisoformat(now).replace(tzinfo=None)
            - datetime.fromisoformat(row["entry_at"]).replace(tzinfo=None)
        ).days

        # Update MAE/MFE for the exit price too
        new_mae = (
            min(row["mae"] or exit_price, exit_price)
            if side == "long"
            else max(row["mae"] or exit_price, exit_price)
        )
        new_mfe = (
            max(row["mfe"] or exit_price, exit_price)
            if side == "long"
            else min(row["mfe"] or exit_price, exit_price)
        )

        # Merge notes
        merged_notes = row["journal_text"]
        if notes:
            merged_notes = (
                merged_notes + "\n---\n" if merged_notes else ""
            ) + f"[EXIT {now}] {notes}"

        conn.execute(
            """UPDATE paper_trade
               SET status=?, exit_price=?, exit_at=?,
                    realized_pnl=?, realized_r=?, gross_realized_pnl=?, exit_cost=?, last_price=?, last_updated=?,
                   unrealized_pnl=0, unrealized_r=0, mae=?, mfe=?,
                   journal_emotion=COALESCE(?, journal_emotion),
                   journal_text=?, days_held=?
               WHERE id=?""",
            (
                status,
                exit_price,
                now,
                pnl,
                realized_r,
                gross_pnl,
                exit_cost,
                exit_price,
                now,
                new_mae,
                new_mfe,
                emotion,
                merged_notes,
                days_held,
                trade_id,
            ),
        )
        out = conn.execute("SELECT * FROM paper_trade WHERE id=?", (trade_id,)).fetchone()
    return _row_to_dict(out)


def list_positions(status_filter: str = "all", market: str | None = None) -> list[dict[str, Any]]:
    """List positions filtered by status and optionally market."""
    where = []
    params: list[Any] = []
    if status_filter == "open":
        where.append("status = ?")
        params.append(STATUS_OPEN)
    elif status_filter == "closed":
        where.append("status != ?")
        params.append(STATUS_OPEN)
    if market:
        where.append("market = ?")
        params.append(market.upper())
    sql = "SELECT * FROM paper_trade"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"
    with _db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def add_journal(trade_id: int, text: str, emotion: str | None = None) -> dict[str, Any]:
    """Append a journal entry to an existing trade (open or closed)."""
    if emotion and emotion not in VALID_EMOTIONS:
        raise ValueError(f"emotion must be one of {sorted(VALID_EMOTIONS)}")
    now = _now_iso()
    with _db() as conn:
        row = conn.execute("SELECT * FROM paper_trade WHERE id=?", (trade_id,)).fetchone()
        if row is None:
            raise ValueError(f"trade id {trade_id} not found")
        merged = row["journal_text"]
        entry = f"[{now}] {text}"
        merged = (merged + "\n---\n" if merged else "") + entry
        conn.execute(
            "UPDATE paper_trade SET journal_text=?, journal_emotion=COALESCE(?, journal_emotion) WHERE id=?",
            (merged, emotion, trade_id),
        )
        out = conn.execute("SELECT * FROM paper_trade WHERE id=?", (trade_id,)).fetchone()
    return _row_to_dict(out)


# ── Stats ───────────────────────────────────────────────────────────────────


def _score_bucket(score: float | None) -> str:
    """Return a coarse bucket for screener score calibration."""
    if score is None:
        return "unknown"
    if score >= 85:
        return "85+"
    if score >= 70:
        return "70-84"
    if score >= 50:
        return "50-69"
    return "<50"


def _group_stats(rows: list[sqlite3.Row]) -> dict[str, Any]:
    """Aggregate paper-trade performance for one source or score bucket."""
    open_pos = [r for r in rows if r["status"] == STATUS_OPEN]
    closed = [r for r in rows if r["status"] != STATUS_OPEN]
    wins = [r for r in closed if (r["realized_r"] or 0) > 0]
    losses = [r for r in closed if (r["realized_r"] or 0) < 0]
    scored = [r for r in rows if r["source_score"] is not None]

    win_rate = (len(wins) / len(closed)) if closed else 0
    avg_win_r = (sum(r["realized_r"] for r in wins) / len(wins)) if wins else 0
    avg_loss_r = (sum(r["realized_r"] for r in losses) / len(losses)) if losses else 0
    expectancy = win_rate * avg_win_r + (1 - win_rate) * avg_loss_r if closed else 0
    avg_realized_r = (sum((r["realized_r"] or 0) for r in closed) / len(closed)) if closed else 0
    avg_score = (sum(r["source_score"] for r in scored) / len(scored)) if scored else None

    return {
        "total_trades": len(rows),
        "open_positions": len(open_pos),
        "closed_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 3),
        "avg_realized_r": round(avg_realized_r, 3),
        "expectancy_r": round(expectancy, 3),
        "avg_source_score": round(avg_score, 2) if avg_score is not None else None,
    }


def _aggregate_by(rows: list[sqlite3.Row], key_fn) -> dict[str, Any]:
    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(key_fn(row), []).append(row)
    return {key: _group_stats(group) for key, group in sorted(groups.items())}


def compute_stats(market: str | None = None) -> dict[str, Any]:
    """Aggregate performance and discipline metrics."""
    where = ""
    params: list[Any] = []
    if market:
        where = " WHERE market = ?"
        params.append(market.upper())

    with _db() as conn:
        rows = conn.execute(f"SELECT * FROM paper_trade{where}", params).fetchall()

    open_pos = [r for r in rows if r["status"] == STATUS_OPEN]
    closed = [r for r in rows if r["status"] != STATUS_OPEN]
    wins = [r for r in closed if (r["realized_r"] or 0) > 0]
    losses = [r for r in closed if (r["realized_r"] or 0) < 0]

    total_realized_r = sum((r["realized_r"] or 0) for r in closed)
    total_realized_pnl = sum((r["realized_pnl"] or 0) for r in closed)
    total_gross_realized_pnl = sum((r["gross_realized_pnl"] or r["realized_pnl"] or 0) for r in closed)
    total_closed_cost = sum((r["entry_cost"] or 0) + (r["exit_cost"] or 0) for r in closed)
    total_open_entry_cost = sum((r["entry_cost"] or 0) for r in open_pos)
    total_unrealized_pnl = sum((r["unrealized_pnl"] or 0) for r in open_pos)

    avg_win_r = (sum(r["realized_r"] for r in wins) / len(wins)) if wins else 0
    avg_loss_r = (sum(r["realized_r"] for r in losses) / len(losses)) if losses else 0
    win_rate = (len(wins) / len(closed)) if closed else 0
    expectancy = win_rate * avg_win_r + (1 - win_rate) * avg_loss_r if closed else 0

    n_stop = sum(1 for r in closed if r["status"] == STATUS_CLOSED_STOP)
    n_target = sum(1 for r in closed if r["status"] == STATUS_CLOSED_TARGET)
    n_manual_loss = sum(
        1 for r in closed if r["status"] == STATUS_CLOSED_MANUAL and (r["realized_r"] or 0) < 0
    )
    n_manual_win = sum(
        1 for r in closed if r["status"] == STATUS_CLOSED_MANUAL and (r["realized_r"] or 0) > 0
    )
    stop_respect = (n_stop / (n_stop + n_manual_loss)) if (n_stop + n_manual_loss) else None

    # Patience score: did you let winners run? (counts trades where MFE-R > realized_r + 0.5R)
    # i.e. trades where you could've made +0.5R more if you held to MFE → you cut too early.
    early_cuts = 0
    eligible = 0
    for r in closed:
        if (r["realized_r"] or 0) <= 0:
            continue  # only count winners
        mfe = r["mfe"] or r["entry_price"]
        entry = r["entry_price"]
        stop = r["stop_price"]
        risk_per_share = abs(entry - stop)
        if risk_per_share <= 0:
            continue
        side = r["side"]
        mfe_r = (mfe - entry) / risk_per_share if side == "long" else (entry - mfe) / risk_per_share
        if mfe_r > 0.5:  # had meaningful favorable move
            eligible += 1
            if mfe_r - (r["realized_r"] or 0) > 0.5:
                early_cuts += 1
    patience_score = (
        (1 - early_cuts / eligible) if eligible else None
    )  # 1.0 = perfect, 0 = always cut early

    # Discipline: avg days held
    avg_days_winners = (sum(r["days_held"] or 0 for r in wins) / len(wins)) if wins else 0
    avg_days_losers = (sum(r["days_held"] or 0 for r in losses) / len(losses)) if losses else 0

    return {
        "total_trades": len(rows),
        "open_positions": len(open_pos),
        "closed_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(closed) - len(wins) - len(losses),
        "win_rate": round(win_rate, 3),
        "avg_win_r": round(avg_win_r, 2),
        "avg_loss_r": round(avg_loss_r, 2),
        "expectancy_r": round(expectancy, 3),
        "total_realized_r": round(total_realized_r, 2),
        "total_realized_pnl": round(total_realized_pnl, 2),
        "total_gross_realized_pnl": round(total_gross_realized_pnl, 2),
        "total_closed_cost": round(total_closed_cost, 2),
        "total_open_entry_cost": round(total_open_entry_cost, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "discipline": {
            "stop_respect_rate": round(stop_respect, 3) if stop_respect is not None else None,
            "patience_score": round(patience_score, 3) if patience_score is not None else None,
            "n_closed_by_stop": n_stop,
            "n_closed_by_target": n_target,
            "n_closed_manual_loss": n_manual_loss,
            "n_closed_manual_win": n_manual_win,
            "n_early_cuts": early_cuts,
            "n_eligible_for_patience": eligible,
            "avg_days_held_winners": round(avg_days_winners, 1),
            "avg_days_held_losers": round(avg_days_losers, 1),
        },
        "by_source": _aggregate_by(rows, lambda r: normalize_source(r["source"])),
        "by_score_bucket": _aggregate_by(rows, lambda r: _score_bucket(r["source_score"])),
        "as_of": _now_iso(),
    }


# ── CLI ─────────────────────────────────────────────────────────────────────


def _print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("open")
    o.add_argument("--symbol", required=True)
    o.add_argument("--market", required=True, choices=["TH", "US"])
    o.add_argument("--shares", type=int, required=True)
    o.add_argument("--entry", type=float, required=True)
    o.add_argument("--stop", type=float, required=True)
    o.add_argument("--target", type=float, required=True)
    o.add_argument("--side", default="long", choices=["long", "short"])
    o.add_argument("--source")
    o.add_argument("--source-score", type=float)
    o.add_argument("--notes")
    o.add_argument("--emotion", choices=sorted(VALID_EMOTIONS))

    c = sub.add_parser("close")
    c.add_argument("--id", type=int, required=True)
    c.add_argument("--exit-price", type=float, required=True)
    c.add_argument("--status", default=STATUS_CLOSED_MANUAL, choices=list(CLOSED_STATUSES))
    c.add_argument("--emotion", choices=sorted(VALID_EMOTIONS))
    c.add_argument("--notes")

    lst = sub.add_parser("list")
    lst.add_argument("--status", default="all", choices=["open", "closed", "all"])
    lst.add_argument("--market", choices=["TH", "US"])

    st = sub.add_parser("stats")
    st.add_argument("--market", choices=["TH", "US"])

    j = sub.add_parser("journal")
    j.add_argument("--id", type=int, required=True)
    j.add_argument("--text", required=True)
    j.add_argument("--emotion", choices=sorted(VALID_EMOTIONS))

    args = p.parse_args()

    if args.cmd == "open":
        out = open_position(
            args.symbol,
            args.market,
            args.shares,
            args.entry,
            args.stop,
            args.target,
            args.side,
            args.source,
            args.source_score,
            args.notes,
            args.emotion,
        )
        _print_json(out)
    elif args.cmd == "close":
        out = close_position(args.id, args.exit_price, args.status, args.emotion, args.notes)
        _print_json(out)
    elif args.cmd == "list":
        out = list_positions(args.status, args.market)
        _print_json(out)
    elif args.cmd == "stats":
        out = compute_stats(args.market)
        _print_json(out)
    elif args.cmd == "journal":
        out = add_journal(args.id, args.text, args.emotion)
        _print_json(out)


if __name__ == "__main__":
    main()
