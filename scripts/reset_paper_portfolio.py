#!/usr/bin/env python3
"""Archive and reset the shared paper-trading portfolio.

The reset intentionally leaves market data, signal history, and analysis runs
untouched. Only paper trades and their paper-entry links are moved out of the
active portfolio, so the next paper trade starts a clean measurement window.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARCHIVE_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_trade_archive (
    archive_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    archived_at  TEXT NOT NULL,
    reset_label  TEXT NOT NULL,
    trade_id     INTEGER NOT NULL,
    trade_json   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS signal_paper_link_archive (
    archive_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    archived_at  TEXT NOT NULL,
    reset_label  TEXT NOT NULL,
    signal_id    TEXT NOT NULL,
    link_json    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paper_session (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    session_id   TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    reset_label  TEXT NOT NULL
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def reset_paper_portfolio(
    db_path: str | Path,
    reset_label: str | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Archive active paper rows and reset the active portfolio to zero rows."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    archived_at = now or _now_iso()
    label = reset_label or f"paper-reset-{archived_at[:10]}"
    session_id = f"paper-{archived_at.replace(':', '').replace('+00:00', 'z')}"

    with sqlite3.connect(str(path), timeout=60.0) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(ARCHIVE_SCHEMA)

        trade_rows = conn.execute("SELECT * FROM paper_trade ORDER BY id").fetchall()
        link_rows = conn.execute(
            "SELECT * FROM signal_paper_link ORDER BY opened_at"
        ).fetchall()

        with conn:
            for row in trade_rows:
                payload = json.dumps(dict(row), ensure_ascii=False, default=str)
                conn.execute(
                    """INSERT INTO paper_trade_archive
                       (archived_at, reset_label, trade_id, trade_json)
                       VALUES (?, ?, ?, ?)""",
                    (archived_at, label, int(row["id"]), payload),
                )
            for row in link_rows:
                payload = json.dumps(dict(row), ensure_ascii=False, default=str)
                conn.execute(
                    """INSERT INTO signal_paper_link_archive
                       (archived_at, reset_label, signal_id, link_json)
                       VALUES (?, ?, ?, ?)""",
                    (archived_at, label, row["signal_id"], payload),
                )

            # Remove links first because signal_paper_link references paper IDs.
            conn.execute("DELETE FROM signal_paper_link")
            conn.execute("DELETE FROM paper_trade")
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'paper_trade'")
            conn.execute(
                """INSERT INTO paper_session (id, session_id, started_at, reset_label)
                   VALUES (1, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     session_id=excluded.session_id,
                     started_at=excluded.started_at,
                     reset_label=excluded.reset_label""",
                (session_id, archived_at, label),
            )

    return {
        "ok": True,
        "db_path": str(path),
        "reset_label": label,
        "session_id": session_id,
        "started_at": archived_at,
        "archived_trades": len(trade_rows),
        "archived_links": len(link_rows),
        "active_trades": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--archive-label")
    args = parser.parse_args()
    print(json.dumps(reset_paper_portfolio(args.db_path, args.archive_label), ensure_ascii=False))


if __name__ == "__main__":
    main()
