"""Bridge auto-paper opens/closes into trader-memory-core theses.

Best-effort and non-fatal: missing thesis_id or invalid transitions are skipped
with a structured result so the paper loop never fails on memory sync.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_SCRIPTS = PROJECT_ROOT / "skills" / "trader-memory-core" / "scripts"
if str(MEMORY_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MEMORY_SCRIPTS))

DEFAULT_STATE_DIR = PROJECT_ROOT / "state" / "theses"

PAPER_STATUS_TO_EXIT = {
    "closed_stop": "stop_hit",
    "closed_target": "target_hit",
    "closed_time": "time_stop",
    "closed_manual": "manual",
    "closed_invalidated": "invalidated",
}


def _thesis_store():
    import thesis_store  # type: ignore

    return thesis_store


def thesis_id_for_signal(conn: sqlite3.Connection, signal_id: str) -> str | None:
    try:
        row = conn.execute(
            "SELECT thesis_id FROM signal_ledger WHERE signal_id = ?",
            (signal_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row:
        return None
    value = row["thesis_id"] if isinstance(row, sqlite3.Row) else row[0]
    return str(value) if value else None


def signal_id_for_paper(conn: sqlite3.Connection, paper_trade_id: int) -> str | None:
    try:
        row = conn.execute(
            "SELECT signal_id FROM signal_paper_link WHERE paper_trade_id = ?",
            (paper_trade_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row:
        return None
    value = row["signal_id"] if isinstance(row, sqlite3.Row) else row[0]
    return str(value) if value else None


def sync_open(
    conn: sqlite3.Connection,
    *,
    signal_id: str,
    entry_price: float,
    entry_date: str,
    shares: int | None = None,
    state_dir: str | Path = DEFAULT_STATE_DIR,
) -> dict[str, Any]:
    """Promote linked thesis to ACTIVE when a paper position opens."""
    thesis_id = thesis_id_for_signal(conn, signal_id)
    if not thesis_id:
        return {"ok": False, "skipped": True, "reason": "no_thesis_id", "signal_id": signal_id}

    store = _thesis_store()
    root = Path(state_dir)
    try:
        thesis = store.get(root, thesis_id)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "ok": False,
            "skipped": True,
            "reason": f"thesis_load_error:{exc}",
            "thesis_id": thesis_id,
        }

    status = thesis.get("status")
    try:
        if status == "IDEA":
            store.transition(root, thesis_id, "ENTRY_READY", "auto-paper open")
            status = "ENTRY_READY"
        if status == "ENTRY_READY":
            store.open_position(
                root,
                thesis_id,
                actual_price=float(entry_price),
                actual_date=str(entry_date)[:10],
                reason="auto-paper open",
                shares=shares,
            )
            return {"ok": True, "thesis_id": thesis_id, "status": "ACTIVE"}
        if status == "ACTIVE":
            return {"ok": True, "skipped": True, "reason": "already_active", "thesis_id": thesis_id}
        return {
            "ok": False,
            "skipped": True,
            "reason": f"unsupported_status:{status}",
            "thesis_id": thesis_id,
        }
    except Exception as exc:
        return {
            "ok": False,
            "skipped": True,
            "reason": f"sync_open_error:{exc}",
            "thesis_id": thesis_id,
        }


def sync_close(
    conn: sqlite3.Connection,
    *,
    paper_trade_id: int,
    exit_price: float,
    exit_date: str,
    paper_status: str,
    state_dir: str | Path = DEFAULT_STATE_DIR,
) -> dict[str, Any]:
    """Close linked ACTIVE thesis when a paper position closes."""
    signal_id = signal_id_for_paper(conn, paper_trade_id)
    if not signal_id:
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_signal_link",
            "paper_trade_id": paper_trade_id,
        }
    thesis_id = thesis_id_for_signal(conn, signal_id)
    if not thesis_id:
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_thesis_id",
            "signal_id": signal_id,
        }

    exit_reason = PAPER_STATUS_TO_EXIT.get(paper_status, "manual")
    store = _thesis_store()
    root = Path(state_dir)
    try:
        thesis = store.get(root, thesis_id)
        if thesis.get("status") != "ACTIVE":
            return {
                "ok": True,
                "skipped": True,
                "reason": f"thesis_not_active:{thesis.get('status')}",
                "thesis_id": thesis_id,
            }
        store.close(
            root,
            thesis_id,
            exit_reason=exit_reason,
            actual_price=float(exit_price),
            actual_date=str(exit_date)[:10],
        )
        return {
            "ok": True,
            "thesis_id": thesis_id,
            "exit_reason": exit_reason,
            "status": "CLOSED",
        }
    except Exception as exc:
        return {
            "ok": False,
            "skipped": True,
            "reason": f"sync_close_error:{exc}",
            "thesis_id": thesis_id,
        }
