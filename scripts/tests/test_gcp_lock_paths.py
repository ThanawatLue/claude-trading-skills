from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_gcp_jobs_use_project_writable_lock_directory():
    cron_script = (ROOT / "scripts" / "setup_gcp_cron.sh").read_text(encoding="utf-8")
    pipeline_script = (ROOT / "scripts" / "run_gcp_daily_pipeline.sh").read_text(encoding="utf-8")

    assert 'LOCK_DIR="$PROJECT_ROOT/state/locks"' in cron_script
    assert 'flock -n /tmp/tong_trading_scan_' not in cron_script
    assert 'LOCK_DIR="$PROJECT_ROOT/state/locks"' in pipeline_script
    assert 'LOCK_FILE="/tmp/tong_trading_daily_pipeline_' not in pipeline_script
