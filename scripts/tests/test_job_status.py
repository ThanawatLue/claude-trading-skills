from scripts.job_status import get_job_status
from trading_core.jobs import JobRunStore


def test_missing_job_is_explicitly_stale(tmp_path) -> None:
    result = get_job_status(tmp_path / "db.sqlite", market="TH")
    assert result["status"] == "never_run"
    assert result["stale"] is True


def test_successful_job_is_not_stale_with_large_window(tmp_path) -> None:
    db_path = tmp_path / "db.sqlite"
    run_id = JobRunStore(db_path).start("daily_signal_pipeline", market="TH")
    JobRunStore(db_path).finish(run_id)
    result = get_job_status(db_path, market="TH", stale_after_minutes=180)
    assert result["status"] == "success"
    assert result["stale"] is False
