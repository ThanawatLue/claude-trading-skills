from trading_core.jobs import JobRunStore


def test_job_lifecycle_is_durable(tmp_path) -> None:
    store = JobRunStore(tmp_path / "db.sqlite")
    run_id = store.start("daily_signal_pipeline", market="th", metadata={"mode": "paper"})
    running = store.latest("daily_signal_pipeline", "TH")
    assert running is not None
    assert running["run_id"] == run_id
    assert running["status"] == "running"
    assert running["metadata"] == {"mode": "paper"}

    store.heartbeat(run_id)
    store.finish(run_id, metadata={"opened": 0})
    completed = store.latest("daily_signal_pipeline", "TH")
    assert completed["status"] == "success"
    assert completed["finished_at"] is not None
    assert completed["metadata"] == {"opened": 0}


def test_failed_job_keeps_error(tmp_path) -> None:
    store = JobRunStore(tmp_path / "db.sqlite")
    run_id = store.start("job")
    store.fail(run_id, "network unavailable")
    result = store.latest("job")
    assert result["status"] == "failed"
    assert result["error"] == "network unavailable"
