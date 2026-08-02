"""Dashboard persistence boundary backed by the shared SQLite policy."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from trading_core.sqlite import apply_migrations, connect_sqlite

ANALYSIS_RUN_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_run (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    market  TEXT    NOT NULL,
    run_at  TEXT    NOT NULL,
    data    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_run_market_at ON analysis_run(market, run_at DESC);
"""


def connect_dashboard_db(db_path: str | Path) -> sqlite3.Connection:
    """Open the dashboard DB with shared connection settings and migrations."""

    conn = connect_sqlite(db_path, timeout=60.0, check_same_thread=False)
    apply_migrations(conn, "dashboard", {1: ANALYSIS_RUN_SCHEMA})
    return conn
