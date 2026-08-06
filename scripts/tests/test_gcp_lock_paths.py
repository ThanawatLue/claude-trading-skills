from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gcp_jobs_use_project_writable_lock_directory():
    cron_script = (ROOT / "scripts" / "setup_gcp_cron.sh").read_text(encoding="utf-8")
    pipeline_script = (ROOT / "scripts" / "run_gcp_daily_pipeline.sh").read_text(encoding="utf-8")

    assert 'LOCK_DIR="$PROJECT_ROOT/state/locks"' in cron_script
    assert "flock -n /tmp/tong_trading_scan_" not in cron_script
    assert 'LOCK_DIR="$PROJECT_ROOT/state/locks"' in pipeline_script
    assert 'LOCK_FILE="/tmp/tong_trading_daily_pipeline_' not in pipeline_script
    # The VM runs cron in UTC and this cron implementation does not reliably
    # apply CRON_TZ, so the intended Bangkok schedule is encoded explicitly.
    assert "CRON_TZ=UTC" in cron_script
    assert 'CRON_TH_HOURLY="0 3-10 * * 1-5' in cron_script
    assert 'CRON_TH_MARKS="30 3-10 * * 1-5' in cron_script
    assert 'CRON_US_SCAN="30 13 * * 1-5' in cron_script
    assert 'CRON_US_PIPE="0 14 * * 1-5' in cron_script
    assert 'CRON_US_MARKS="30 14 * * 1-5' in cron_script
    assert 'CRON_TH_HOURLY="0 10-17 * * 1-5' not in cron_script
    assert "CRON_TH_MORN=" not in cron_script
    assert "CRON_TH_PIPE_MORN=" not in cron_script
    assert 'sudo systemctl enable --now "$service"' in cron_script
    assert 'sudo systemctl is-active --quiet "$service"' in cron_script

    deploy_workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    assert "sudo -n crontab -u github-actions -l" in deploy_workflow
    assert 'sudo -n crontab -u github-actions "$LEGACY_CLEAN"' in deploy_workflow
