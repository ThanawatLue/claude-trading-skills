"""Durable job-run records for cron, dashboard, and local CLI execution."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .clock import isoformat_seconds
from .sqlite import apply_migrations, connect_sqlite

JOB_SCHEMA = """
CREATE TABLE IF NOT EXISTS job_run (
    run_id       TEXT PRIMARY KEY,
    job_name     TEXT NOT NULL,
    market       TEXT,
    status       TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    heartbeat_at TEXT NOT NULL,
    finished_at  TEXT,
    error        TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_job_run_name_started
    ON job_run(job_name, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_run_status
    ON job_run(status, heartbeat_at);
"""


class JobRunStore:
    """Persist job lifecycle state without coupling callers to SQL."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self):
        conn = connect_sqlite(self.db_path)
        apply_migrations(conn, "job_run", {1: JOB_SCHEMA})
        return conn

    def start(
        self,
        job_name: str,
        *,
        market: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        run_id = f"{job_name}-{uuid.uuid4().hex[:12]}"
        now = isoformat_seconds()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO job_run(
                    run_id, job_name, market, status, started_at, heartbeat_at, metadata_json
                ) VALUES (?, ?, ?, 'running', ?, ?, ?)""",
                (
                    run_id,
                    job_name,
                    market.upper() if market else None,
                    now,
                    now,
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )
        return run_id

    def heartbeat(self, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE job_run SET heartbeat_at=? WHERE run_id=? AND status='running'",
                (isoformat_seconds(), run_id),
            )

    def finish(self, run_id: str, *, metadata: dict[str, Any] | None = None) -> None:
        self._complete(run_id, "success", metadata=metadata)

    def fail(self, run_id: str, error: str) -> None:
        self._complete(run_id, "failed", error=error)

    def _complete(
        self,
        run_id: str,
        status: str,
        *,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = isoformat_seconds()
        with self._connect() as conn:
            conn.execute(
                """UPDATE job_run
                   SET status=?, heartbeat_at=?, finished_at=?, error=?, metadata_json=?
                   WHERE run_id=?""",
                (status, now, now, error, json.dumps(metadata or {}, sort_keys=True), run_id),
            )

    def latest(self, job_name: str, market: str | None = None) -> dict[str, Any] | None:
        clauses = ["job_name = ?"]
        params: list[Any] = [job_name]
        if market:
            clauses.append("market = ?")
            params.append(market.upper())
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT * FROM job_run WHERE {' AND '.join(clauses)} "
                "ORDER BY started_at DESC LIMIT 1",
                params,
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        try:
            result["metadata"] = json.loads(result.pop("metadata_json") or "{}")
        except json.JSONDecodeError:
            result["metadata"] = {}
        return result
