"""Inspect durable scheduler evidence for local and production runbooks."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from trading_core.clock import parse_iso, utc_now
from trading_core.jobs import JobRunStore

DEFAULT_DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"


def get_job_status(
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    job_name: str = "daily_signal_pipeline",
    market: str | None = None,
    stale_after_minutes: int = 180,
) -> dict:
    """Return the latest job record plus an explicit freshness assessment."""

    if stale_after_minutes <= 0:
        raise ValueError("stale_after_minutes must be > 0")
    latest = JobRunStore(db_path).latest(job_name, market)
    if latest is None:
        return {
            "job_name": job_name,
            "market": market.upper() if market else None,
            "status": "never_run",
            "stale": True,
        }

    heartbeat = latest.get("heartbeat_at") or latest.get("finished_at")
    stale = True
    if heartbeat:
        try:
            stale = utc_now() - parse_iso(heartbeat) > timedelta(minutes=stale_after_minutes)
        except ValueError:
            stale = True
    latest["stale"] = stale
    latest["freshness_threshold_minutes"] = stale_after_minutes
    return latest


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show latest durable trading job status")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--job", default="daily_signal_pipeline")
    parser.add_argument("--market", choices=["US", "TH"])
    parser.add_argument("--stale-after-minutes", type=int, default=180)
    args = parser.parse_args(argv)
    result = get_job_status(
        args.db_path,
        job_name=args.job,
        market=args.market,
        stale_after_minutes=args.stale_after_minutes,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" and not result["stale"] else 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
