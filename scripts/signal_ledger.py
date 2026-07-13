"""Signal ledger and outcome tracking.

This module stores every generated trade signal in the shared market cache DB
and computes forward outcomes from cached daily OHLCV bars. It is intentionally
local-only: no broker execution and no network fetches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"
DEFAULT_THESES_DIR = PROJECT_ROOT / "state" / "theses"
DEFAULT_HORIZONS = (5, 20, 60)
SOURCE_ALIASES = {
    "vcp": "vcp-screener",
    "vcp_screener": "vcp-screener",
    "vcp-screener": "vcp-screener",
    "canslim": "canslim-screener",
    "canslim_screener": "canslim-screener",
    "canslim-screener": "canslim-screener",
    "thai_swing_dip": "thai-swing-dip",
    "thai-swing-dip": "thai-swing-dip",
    "thai_swing_momentum": "thai-swing-momentum",
    "thai-swing-momentum": "thai-swing-momentum",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS signal_ledger (
    signal_id    TEXT PRIMARY KEY,
    symbol       TEXT NOT NULL,
    market       TEXT,
    source_skill TEXT NOT NULL,
    signal_date  TEXT NOT NULL,
    direction    TEXT NOT NULL DEFAULT 'LONG',
    raw_score    REAL,
    entry_price  REAL,
    stop_price   REAL,
    target_price REAL,
    status       TEXT NOT NULL DEFAULT 'OPEN',
    thesis_id    TEXT,
    origin_file  TEXT,
    payload_json TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_signal_source ON signal_ledger(source_skill);
CREATE INDEX IF NOT EXISTS idx_signal_symbol_date ON signal_ledger(symbol, signal_date);
CREATE INDEX IF NOT EXISTS idx_signal_status ON signal_ledger(status);

CREATE TABLE IF NOT EXISTS signal_outcome (
    signal_id     TEXT NOT NULL,
    horizon_days  INTEGER NOT NULL,
    evaluation_date TEXT,
    entry_close   REAL,
    close_price   REAL,
    high_price    REAL,
    low_price     REAL,
    return_pct    REAL,
    mae_pct       REAL,
    mfe_pct       REAL,
    hit_stop      INTEGER NOT NULL DEFAULT 0,
    hit_target    INTEGER NOT NULL DEFAULT 0,
    theoretical_r REAL,
    is_complete   INTEGER NOT NULL DEFAULT 0,
    updated_at    TEXT NOT NULL,
    PRIMARY KEY (signal_id, horizon_days),
    FOREIGN KEY (signal_id) REFERENCES signal_ledger(signal_id)
);
CREATE INDEX IF NOT EXISTS idx_outcome_complete ON signal_outcome(is_complete);

CREATE TABLE IF NOT EXISTS signal_paper_link (
    signal_id      TEXT PRIMARY KEY,
    paper_trade_id INTEGER NOT NULL,
    opened_at      TEXT NOT NULL,
    mode           TEXT NOT NULL DEFAULT 'auto',
    FOREIGN KEY (signal_id) REFERENCES signal_ledger(signal_id)
);
"""


@dataclass(frozen=True)
class SignalRecord:
    signal_id: str
    symbol: str
    source_skill: str
    signal_date: str
    market: str | None = None
    direction: str = "LONG"
    raw_score: float | None = None
    entry_price: float | None = None
    stop_price: float | None = None
    target_price: float | None = None
    status: str = "OPEN"
    thesis_id: str | None = None
    origin_file: str | None = None
    payload: dict[str, Any] | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=60.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def infer_market(symbol: str) -> str:
    return "TH" if symbol.upper().endswith(".BK") else "US"


def normalize_source(source: str | None) -> str:
    value = (source or "unknown").strip().lower().replace(" ", "-")
    return SOURCE_ALIASES.get(value, value)


def stable_signal_id(
    source: str, symbol: str, signal_date: str, thesis_id: str | None = None
) -> str:
    source = normalize_source(source)
    if thesis_id:
        base = thesis_id
    else:
        base = f"{source}|{symbol}|{signal_date}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    safe_source = source.lower().replace("_", "-")
    safe_symbol = symbol.lower().replace(".", "-")
    return f"sig_{safe_source}_{safe_symbol}_{signal_date.replace('-', '')}_{digest}"


def parse_signal_date(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).date().isoformat()
    text = str(value)
    return text[:10]


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_value(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def nested_get(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def register_signal(conn: sqlite3.Connection, signal: SignalRecord) -> bool:
    """Insert or update a signal. Returns True when a new row was created."""
    existing = conn.execute(
        "SELECT signal_id FROM signal_ledger WHERE signal_id = ?", (signal.signal_id,)
    ).fetchone()
    created_at = now_iso()
    updated_at = created_at
    conn.execute(
        """INSERT INTO signal_ledger (
            signal_id, symbol, market, source_skill, signal_date, direction,
            raw_score, entry_price, stop_price, target_price, status, thesis_id,
            origin_file, payload_json, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(signal_id) DO UPDATE SET
            symbol=excluded.symbol,
            market=excluded.market,
            source_skill=excluded.source_skill,
            signal_date=excluded.signal_date,
            direction=excluded.direction,
            raw_score=excluded.raw_score,
            entry_price=excluded.entry_price,
            stop_price=excluded.stop_price,
            target_price=excluded.target_price,
            status=excluded.status,
            thesis_id=excluded.thesis_id,
            origin_file=excluded.origin_file,
            payload_json=excluded.payload_json,
            updated_at=excluded.updated_at
        """,
        (
            signal.signal_id,
            signal.symbol.upper(),
            signal.market or infer_market(signal.symbol),
            normalize_source(signal.source_skill),
            signal.signal_date,
            signal.direction.upper(),
            signal.raw_score,
            signal.entry_price,
            signal.stop_price,
            signal.target_price,
            signal.status,
            signal.thesis_id,
            signal.origin_file,
            json.dumps(signal.payload or {}, ensure_ascii=False, sort_keys=True),
            created_at,
            updated_at,
        ),
    )
    conn.commit()
    return existing is None


def signal_from_thesis(thesis: dict[str, Any]) -> SignalRecord | None:
    ticker = thesis.get("ticker")
    origin = thesis.get("origin") or {}
    raw_source = origin.get("skill")
    if not ticker or not raw_source:
        return None
    source = normalize_source(raw_source)

    raw = origin.get("raw_provenance") or {}
    entry = thesis.get("entry") or {}
    exit_cfg = thesis.get("exit") or {}
    signal_date = parse_signal_date(thesis.get("created_at"))
    thesis_id = thesis.get("thesis_id")
    signal_id = stable_signal_id(source, ticker, signal_date, thesis_id)

    entry_price = (
        as_float(entry.get("target_price"))
        or as_float(entry.get("actual_price"))
        or as_float(raw.get("entry_price"))
        or as_float(raw.get("price"))
        or as_float(raw.get("close"))
    )
    stop_price = as_float(exit_cfg.get("stop_loss")) or as_float(raw.get("stop_loss"))
    target_price = (
        as_float(exit_cfg.get("take_profit"))
        or as_float(raw.get("target_price"))
        or as_float(raw.get("take_profit"))
    )

    payload = {
        "thesis_statement": thesis.get("thesis_statement"),
        "screening_grade": origin.get("screening_grade"),
        "raw_provenance": raw,
    }
    return SignalRecord(
        signal_id=signal_id,
        symbol=ticker,
        source_skill=source,
        signal_date=signal_date,
        market=infer_market(ticker),
        raw_score=as_float(origin.get("screening_score")),
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        thesis_id=thesis_id,
        origin_file=origin.get("output_file"),
        payload=payload,
    )


def _metadata_market(data: dict[str, Any]) -> str | None:
    metadata = data.get("metadata") or {}
    return (
        metadata.get("market")
        or nested_get(metadata, "screening_options.market")
        or nested_get(data, "screening_options.market")
    )


def _metadata_date(data: dict[str, Any]) -> str | None:
    metadata = data.get("metadata") or {}
    return parse_signal_date(
        data.get("generated_at")
        or data.get("generated")
        or metadata.get("generated_at")
        or metadata.get("generated")
        or metadata.get("run_at")
    )


def _source_from_filename(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("vcp_screener_"):
        return "vcp-screener"
    if name.startswith("canslim_screener_"):
        return "canslim-screener"
    if name.startswith("thai_swing_"):
        return "thai-swing"
    if name.startswith("pead_") or name.startswith("pead-screener"):
        return "pead-screener"
    return "unknown"


def signal_from_mapping(
    record: dict[str, Any],
    *,
    default_source: str,
    default_market: str | None,
    default_date: str,
    origin_file: str | None,
) -> SignalRecord | None:
    symbol = first_value(record.get("symbol"), record.get("ticker"))
    source = normalize_source(
        first_value(record.get("source_skill"), record.get("source"), default_source)
    )
    if not symbol or source == "unknown":
        return None

    plan = record.get("plan") if isinstance(record.get("plan"), dict) else {}
    signal_date = parse_signal_date(
        first_value(
            record.get("signal_date"), record.get("date"), record.get("created_at"), default_date
        )
    )
    signal_id = str(
        first_value(record.get("signal_id"), stable_signal_id(source, str(symbol), signal_date))
    )
    entry_price = as_float(
        first_value(
            record.get("entry_price"),
            record.get("entry"),
            plan.get("entry"),
            record.get("price"),
            record.get("current_price"),
            record.get("close"),
            nested_get(record, "vcp_pattern.pivot_price"),
        )
    )
    stop_price = as_float(
        first_value(
            record.get("stop_price"),
            record.get("stop"),
            record.get("stop_loss"),
            plan.get("stop"),
            nested_get(record, "pivot_proximity.stop_loss_price"),
        )
    )
    target_price = as_float(
        first_value(
            record.get("target_price"),
            record.get("target"),
            record.get("take_profit"),
            plan.get("target"),
        )
    )
    raw_score = as_float(
        first_value(record.get("raw_score"), record.get("score"), record.get("composite_score"))
    )
    return SignalRecord(
        signal_id=signal_id,
        symbol=str(symbol),
        market=str(
            first_value(record.get("market"), default_market, infer_market(str(symbol)))
        ).upper(),
        source_skill=source,
        signal_date=signal_date,
        direction=str(record.get("direction") or "LONG").upper(),
        raw_score=raw_score,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        origin_file=origin_file,
        payload=record,
    )


def signals_from_file(path: str | Path) -> list[SignalRecord]:
    file_path = Path(path)
    try:
        if file_path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        else:
            data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError):
        return []
    if not isinstance(data, dict):
        return []

    default_market = _metadata_market(data)
    default_date = _metadata_date(data)
    default_source = _source_from_filename(file_path)
    origin_file = str(file_path)

    items: list[tuple[dict[str, Any], str]] = []
    if isinstance(data.get("signals"), list):
        items.extend((item, default_source) for item in data["signals"] if isinstance(item, dict))
    elif isinstance(data.get("results"), list):
        items.extend((item, default_source) for item in data["results"] if isinstance(item, dict))
    else:
        source_by_key = {
            "dip_buy": "thai-swing-dip",
            "momentum": "thai-swing-momentum",
        }
        for key, source in source_by_key.items():
            if isinstance(data.get(key), list):
                items.extend((item, source) for item in data[key] if isinstance(item, dict))

    signals = []
    for item, source in items:
        signal = signal_from_mapping(
            item,
            default_source=source,
            default_market=default_market,
            default_date=default_date,
            origin_file=origin_file,
        )
        if signal is not None:
            signals.append(signal)
    return signals


def ingest_signal_files(conn: sqlite3.Connection, paths: list[str | Path]) -> dict[str, int]:
    files = 0
    total = 0
    inserted = 0
    updated = 0
    skipped = 0
    for path in paths:
        file_path = Path(path)
        signals = signals_from_file(file_path)
        if not signals:
            skipped += 1
            continue
        files += 1
        for signal in signals:
            total += 1
            is_new = register_signal(conn, signal)
            inserted += int(is_new)
            updated += int(not is_new)
    return {
        "files": files,
        "total": total,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
    }


def ingest_theses(
    conn: sqlite3.Connection, theses_dir: str | Path = DEFAULT_THESES_DIR
) -> dict[str, int]:
    total = 0
    inserted = 0
    updated = 0
    skipped = 0
    for path in sorted(Path(theses_dir).glob("th_*.yaml")):
        try:
            thesis = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            skipped += 1
            continue
        signal = signal_from_thesis(thesis)
        if signal is None:
            skipped += 1
            continue
        total += 1
        is_new = register_signal(conn, signal)
        inserted += int(is_new)
        updated += int(not is_new)
    return {"total": total, "inserted": inserted, "updated": updated, "skipped": skipped}


def get_signal_counts(conn: sqlite3.Connection, market: str | None = None) -> dict[str, Any]:
    where = ""
    params: list[Any] = []
    if market:
        where = " WHERE market = ?"
        params.append(market.upper())

    total = conn.execute(f"SELECT COUNT(*) AS n FROM signal_ledger{where}", params).fetchone()["n"]
    by_source = conn.execute(
        f"""SELECT source_skill, COUNT(*) AS signals
            FROM signal_ledger{where}
            GROUP BY source_skill
            ORDER BY signals DESC""",
        params,
    ).fetchall()
    completed = conn.execute(
        f"""SELECT COUNT(DISTINCT s.signal_id) AS n
            FROM signal_ledger s
            JOIN signal_outcome o ON o.signal_id = s.signal_id
            {"WHERE s.market = ? AND" if market else "WHERE"} o.is_complete = 1""",
        params,
    ).fetchone()["n"]
    return {
        "total": total,
        "completed_signals": completed,
        "by_source": {r["source_skill"]: r["signals"] for r in by_source},
    }


def _bars_for_signal(conn: sqlite3.Connection, symbol: str, signal_date: str) -> list[sqlite3.Row]:
    try:
        return conn.execute(
            """SELECT date, open, high, low, close, volume
               FROM price_bar
               WHERE symbol = ? AND date >= ? AND close IS NOT NULL
               ORDER BY date ASC""",
            (symbol.upper(), signal_date),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if "no such table: price_bar" in str(exc):
            return []
        raise


def _compute_long_outcome(
    signal: sqlite3.Row, bars: list[sqlite3.Row], horizon: int
) -> dict[str, Any]:
    if not bars:
        return {"is_complete": 0}

    entry_bar = bars[0]
    entry_price = signal["entry_price"] or entry_bar["close"]
    if not entry_price:
        return {"is_complete": 0}

    complete = len(bars) > horizon
    window = bars[1 : horizon + 1] if len(bars) > 1 else []
    if not window:
        return {"entry_close": entry_price, "is_complete": 0}

    eval_bar = window[-1]
    high_price = max(float(b["high"] if b["high"] is not None else b["close"]) for b in window)
    low_price = min(float(b["low"] if b["low"] is not None else b["close"]) for b in window)
    close_price = float(eval_bar["close"])
    return_pct = (close_price - entry_price) / entry_price
    mae_pct = (low_price - entry_price) / entry_price
    mfe_pct = (high_price - entry_price) / entry_price

    stop_price = signal["stop_price"]
    target_price = signal["target_price"]
    hit_stop = bool(stop_price is not None and low_price <= float(stop_price))
    hit_target = bool(target_price is not None and high_price >= float(target_price))
    theoretical_r = None
    if stop_price is not None and entry_price > float(stop_price):
        theoretical_r = (close_price - entry_price) / (entry_price - float(stop_price))

    return {
        "evaluation_date": eval_bar["date"],
        "entry_close": entry_price,
        "close_price": close_price,
        "high_price": high_price,
        "low_price": low_price,
        "return_pct": return_pct,
        "mae_pct": mae_pct,
        "mfe_pct": mfe_pct,
        "hit_stop": int(hit_stop),
        "hit_target": int(hit_target),
        "theoretical_r": theoretical_r,
        "is_complete": int(complete),
    }


def update_outcomes(
    conn: sqlite3.Connection,
    horizons: tuple[int, ...] = DEFAULT_HORIZONS,
    market: str | None = None,
) -> dict[str, int]:
    where = ""
    params: list[Any] = []
    if market:
        where = " WHERE market = ?"
        params.append(market.upper())
    signals = conn.execute(f"SELECT * FROM signal_ledger{where}", params).fetchall()
    updated = 0
    complete = 0
    now = now_iso()
    for signal in signals:
        bars = _bars_for_signal(conn, signal["symbol"], signal["signal_date"])
        for horizon in horizons:
            outcome = _compute_long_outcome(signal, bars, horizon)
            conn.execute(
                """INSERT INTO signal_outcome (
                    signal_id, horizon_days, evaluation_date, entry_close, close_price,
                    high_price, low_price, return_pct, mae_pct, mfe_pct, hit_stop,
                    hit_target, theoretical_r, is_complete, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(signal_id, horizon_days) DO UPDATE SET
                    evaluation_date=excluded.evaluation_date,
                    entry_close=excluded.entry_close,
                    close_price=excluded.close_price,
                    high_price=excluded.high_price,
                    low_price=excluded.low_price,
                    return_pct=excluded.return_pct,
                    mae_pct=excluded.mae_pct,
                    mfe_pct=excluded.mfe_pct,
                    hit_stop=excluded.hit_stop,
                    hit_target=excluded.hit_target,
                    theoretical_r=excluded.theoretical_r,
                    is_complete=excluded.is_complete,
                    updated_at=excluded.updated_at
                """,
                (
                    signal["signal_id"],
                    horizon,
                    outcome.get("evaluation_date"),
                    outcome.get("entry_close"),
                    outcome.get("close_price"),
                    outcome.get("high_price"),
                    outcome.get("low_price"),
                    outcome.get("return_pct"),
                    outcome.get("mae_pct"),
                    outcome.get("mfe_pct"),
                    int(outcome.get("hit_stop") or 0),
                    int(outcome.get("hit_target") or 0),
                    outcome.get("theoretical_r"),
                    int(outcome.get("is_complete") or 0),
                    now,
                ),
            )
            updated += 1
            complete += int(outcome.get("is_complete") or 0)
    conn.commit()
    return {"signals": len(signals), "outcomes_updated": updated, "complete_outcomes": complete}


def outcome_summary(conn: sqlite3.Connection, market: str | None = None) -> dict[str, Any]:
    market_clause = ""
    params: list[Any] = []
    if market:
        market_clause = "WHERE s.market = ?"
        params.append(market.upper())

    rows = conn.execute(
        f"""SELECT s.source_skill, o.horizon_days, COUNT(*) AS outcomes,
                   AVG(o.return_pct) AS avg_return_pct,
                   AVG(o.theoretical_r) AS avg_r,
                   AVG(CASE WHEN o.return_pct > 0 THEN 1.0 ELSE 0.0 END) AS win_rate,
                   SUM(o.hit_stop) AS hit_stop,
                   SUM(o.hit_target) AS hit_target
            FROM signal_ledger s
            JOIN signal_outcome o ON o.signal_id = s.signal_id
            {market_clause}
            {"AND" if market_clause else "WHERE"} o.is_complete = 1
            GROUP BY s.source_skill, o.horizon_days
            ORDER BY s.source_skill, o.horizon_days""",
        params,
    ).fetchall()
    by_source: dict[str, dict[str, Any]] = {}
    for row in rows:
        source = row["source_skill"]
        by_source.setdefault(source, {})[str(row["horizon_days"])] = {
            "outcomes": row["outcomes"],
            "avg_return_pct": row["avg_return_pct"],
            "avg_r": row["avg_r"],
            "win_rate": row["win_rate"],
            "hit_stop": row["hit_stop"],
            "hit_target": row["hit_target"],
        }
    return {"by_source": by_source}


def source_metrics(
    conn: sqlite3.Connection, market: str | None = None
) -> dict[str, dict[str, Any]]:
    market_filter = ""
    params: list[Any] = []
    if market:
        market_filter = "WHERE market = ?"
        params.append(market.upper())
    signal_rows = conn.execute(
        f"""SELECT source_skill, COUNT(*) AS signals
            FROM signal_ledger
            {market_filter}
            GROUP BY source_skill""",
        params,
    ).fetchall()

    outcome_filter = "WHERE o.is_complete = 1"
    outcome_params: list[Any] = []
    if market:
        outcome_filter = "WHERE s.market = ? AND o.is_complete = 1"
        outcome_params.append(market.upper())
    outcome_rows = conn.execute(
        f"""SELECT s.source_skill, o.horizon_days,
                   COUNT(*) AS outcomes,
                   AVG(o.return_pct) AS avg_return_pct,
                   AVG(o.theoretical_r) AS avg_r,
                   AVG(CASE WHEN o.return_pct > 0 THEN 1.0 ELSE 0.0 END) AS win_rate
            FROM signal_ledger s
            JOIN signal_outcome o ON o.signal_id = s.signal_id
            {outcome_filter}
            GROUP BY s.source_skill, o.horizon_days""",
        outcome_params,
    ).fetchall()
    complete_signal_rows = conn.execute(
        f"""SELECT s.source_skill, COUNT(DISTINCT s.signal_id) AS complete_signals
            FROM signal_ledger s
            JOIN signal_outcome o ON o.signal_id = s.signal_id
            {outcome_filter}
            GROUP BY s.source_skill""",
        outcome_params,
    ).fetchall()

    result: dict[str, dict[str, Any]] = {}
    for row in signal_rows:
        result[row["source_skill"]] = {
            "signals": row["signals"],
            "complete_signals": 0,
            "complete_outcomes": 0,
            "horizons": {},
        }
    for row in complete_signal_rows:
        source = row["source_skill"]
        result.setdefault(
            source, {"signals": 0, "complete_signals": 0, "complete_outcomes": 0, "horizons": {}}
        )
        result[source]["complete_signals"] = row["complete_signals"]
    for row in outcome_rows:
        source = row["source_skill"]
        result.setdefault(
            source, {"signals": 0, "complete_signals": 0, "complete_outcomes": 0, "horizons": {}}
        )
        result[source]["complete_outcomes"] += row["outcomes"]
        result[source]["horizons"][str(row["horizon_days"])] = {
            "outcomes": row["outcomes"],
            "avg_return_pct": row["avg_return_pct"],
            "avg_r": row["avg_r"],
            "win_rate": row["win_rate"],
        }
    return result


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Signal ledger maintenance")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    sub = parser.add_subparsers(dest="cmd", required=True)

    ingest = sub.add_parser("ingest-theses")
    ingest.add_argument("--theses-dir", default=str(DEFAULT_THESES_DIR))

    ingest_signals = sub.add_parser("ingest-signals")
    ingest_signals.add_argument("paths", nargs="+")

    update = sub.add_parser("update-outcomes")
    update.add_argument("--market", choices=["US", "TH"])
    update.add_argument("--horizons", default="5,20,60")

    summary = sub.add_parser("summary")
    summary.add_argument("--market", choices=["US", "TH"])

    args = parser.parse_args(argv)
    with connect(args.db_path) as conn:
        if args.cmd == "ingest-theses":
            result = ingest_theses(conn, args.theses_dir)
        elif args.cmd == "ingest-signals":
            result = ingest_signal_files(conn, args.paths)
        elif args.cmd == "update-outcomes":
            horizons = tuple(int(x.strip()) for x in args.horizons.split(",") if x.strip())
            result = update_outcomes(conn, horizons=horizons, market=args.market)
        else:
            result = {
                "signals": get_signal_counts(conn, market=args.market),
                "outcomes": outcome_summary(conn, market=args.market),
            }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
