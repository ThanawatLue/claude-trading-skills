"""Shared SQLite connection and migration primitives."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from .clock import isoformat_seconds

MIGRATION_TABLE: Final[str] = "_trading_core_schema_migrations"


def connect_sqlite(
    db_path: str | Path,
    *,
    timeout: float = 60.0,
    check_same_thread: bool = False,
) -> sqlite3.Connection:
    """Open a consistently configured SQLite connection."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=timeout, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def apply_migrations(
    conn: sqlite3.Connection,
    namespace: str,
    migrations: Mapping[int, str],
) -> int:
    """Apply ordered, idempotent migrations and return the current version."""

    if not namespace or not namespace.replace("_", "").isalnum():
        raise ValueError("namespace must contain only letters, numbers, and underscores")
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            namespace TEXT NOT NULL,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL,
            PRIMARY KEY(namespace, version)
        )"""
    )
    current_row = conn.execute(
        f"SELECT COALESCE(MAX(version), 0) FROM {MIGRATION_TABLE} WHERE namespace=?",
        (namespace,),
    ).fetchone()
    current = int(current_row[0]) if current_row else 0

    for version in sorted(migrations):
        if version <= current:
            continue
        if version <= 0:
            raise ValueError("migration versions must be positive integers")
        sql = migrations[version]
        with conn:
            conn.executescript(sql)
            conn.execute(
                f"INSERT INTO {MIGRATION_TABLE}(namespace, version, applied_at) VALUES (?, ?, ?)",
                (namespace, version, isoformat_seconds()),
            )
        current = version
    return current


def mark_migration(conn: sqlite3.Connection, namespace: str, version: int) -> None:
    """Record a compatibility migration that required runtime inspection."""

    if version <= 0:
        raise ValueError("migration versions must be positive integers")
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            namespace TEXT NOT NULL,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL,
            PRIMARY KEY(namespace, version)
        )"""
    )
    conn.execute(
        f"INSERT OR IGNORE INTO {MIGRATION_TABLE}(namespace, version, applied_at) VALUES (?, ?, ?)",
        (namespace, version, isoformat_seconds()),
    )
