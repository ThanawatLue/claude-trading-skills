from unittest import mock

from scripts import run_thai_market_daily


def test_main_runs_all_steps_mocked(tmp_path):
    with mock.patch("scripts.run_thai_market_daily.subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0)

        ret = run_thai_market_daily.main(["--output-dir", str(tmp_path)])
        assert ret == 0
        # All 6 steps executed
        assert mock_run.call_count == 6


def test_main_handles_skip_flags(tmp_path):
    with mock.patch("scripts.run_thai_market_daily.subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0)

        ret = run_thai_market_daily.main(
            ["--output-dir", str(tmp_path), "--skip-dividends", "--skip-paper"]
        )
        assert ret == 0
        # 4 steps executed (6 - 2)
        assert mock_run.call_count == 4


def test_main_reports_failure_on_subprocess_error(tmp_path):
    with mock.patch("scripts.run_thai_market_daily.subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=1)

        ret = run_thai_market_daily.main(["--output-dir", str(tmp_path)])
        assert ret == 1
