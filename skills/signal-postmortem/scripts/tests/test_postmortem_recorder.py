import json
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch, MagicMock
import pytest
from postmortem_recorder import (
    calculate_return,
    classify_outcome,
    create_postmortem_record,
    fetch_price_data,
    process_signal,
    list_ready_signals,
    get_macro_regime, # New import
    get_fmp_api_key # New import
)
from postmortem_recorder import main as recorder_main # For main function testing
import requests
import sys


class TestCalculateReturn:
    """Tests for calculate_return function."""

    def test_positive_return(self):
        """Test positive return calculation."""
        result = calculate_return(100.0, 110.0)
        assert result == pytest.approx(0.10, rel=1e-6)

    def test_negative_return(self):
        """Test negative return calculation."""
        result = calculate_return(100.0, 95.0)
        assert result == pytest.approx(-0.05, rel=1e-6)

    def test_zero_entry_price(self):
        """Test handling of zero entry price."""
        result = calculate_return(0.0, 100.0)
        assert result == 0.0

    def test_no_change(self):
        """Test flat return."""
        result = calculate_return(100.0, 100.0)
        assert result == 0.0


class TestClassifyOutcome:
    """Tests for classify_outcome function."""

    def test_true_positive_long(self):
        """Test TRUE_POSITIVE classification for LONG signal with positive return."""
        result = classify_outcome(
            predicted_direction="LONG",
            return_pct=0.05,
            regime_at_signal="RISK_ON",
            regime_at_exit="RISK_ON",
        )
        assert result == "TRUE_POSITIVE"

    def test_true_positive_short(self):
        """Test TRUE_POSITIVE classification for SHORT signal with negative return."""
        result = classify_outcome(
            predicted_direction="SHORT",
            return_pct=-0.03,
            regime_at_signal="RISK_OFF",
            regime_at_exit="RISK_OFF",
        )
        assert result == "TRUE_POSITIVE"

    def test_false_positive_long(self):
        """Test FALSE_POSITIVE classification for LONG signal with negative return."""
        result = classify_outcome(
            predicted_direction="LONG",
            return_pct=-0.015,
            regime_at_signal="RISK_ON",
            regime_at_exit="RISK_ON",
        )
        assert result == "FALSE_POSITIVE"

    def test_false_positive_severe(self):
        """Test FALSE_POSITIVE_SEVERE classification for large loss."""
        result = classify_outcome(
            predicted_direction="LONG",
            return_pct=-0.05,
            regime_at_signal="RISK_ON",
            regime_at_exit="RISK_ON",
        )
        assert result == "FALSE_POSITIVE_SEVERE"

    def test_neutral_flat_return(self):
        """Test NEUTRAL classification for flat return."""
        result = classify_outcome(
            predicted_direction="LONG",
            return_pct=0.002,
            regime_at_signal="RISK_ON",
            regime_at_exit="RISK_ON",
        )
        assert result == "NEUTRAL"

    def test_regime_mismatch(self):
        """Test REGIME_MISMATCH classification when regime changed."""
        result = classify_outcome(
            predicted_direction="LONG",
            return_pct=-0.03,
            regime_at_signal="RISK_ON",
            regime_at_exit="RISK_OFF",
        )
        assert result == "REGIME_MISMATCH"

    def test_regime_change_but_small_loss(self):
        """Test that small loss with regime change is not REGIME_MISMATCH."""
        result = classify_outcome(
            predicted_direction="LONG",
            return_pct=-0.01,
            regime_at_signal="RISK_ON",
            regime_at_exit="RISK_OFF",
        )
        # Should be FALSE_POSITIVE since loss is < 2%
        assert result == "FALSE_POSITIVE"


class TestCreatePostmortemRecord:
    """Tests for create_postmortem_record function."""

    def test_basic_postmortem_creation(self):
        """Test basic postmortem record creation."""
        signal = {
            "signal_id": "sig_aapl_20260310_abc",
            "ticker": "AAPL",
            "signal_date": "2026-03-10",
            "predicted_direction": "LONG",
            "source_skill": "vcp-screener",
            "entry_price": 170.0,
            "regime": "RISK_ON",
        }

        realized_returns = {"5d": 0.032, "20d": 0.058}

        result = create_postmortem_record(
            signal=signal,
            realized_returns=realized_returns,
            exit_price=175.44,
            exit_date="2026-03-15",
        )

        assert result["schema_version"] == "1.0"
        assert result["postmortem_id"] == "pm_sig_aapl_20260310_abc"
        assert result["signal_id"] == "sig_aapl_20260310_abc"
        assert result["ticker"] == "AAPL"
        assert result["signal_date"] == "2026-03-10"
        assert result["source_skill"] == "vcp-screener"
        assert result["predicted_direction"] == "LONG"
        assert result["entry_price"] == 170.0
        assert result["realized_returns"]["5d"] == 0.032
        assert result["exit_price"] == 175.44
        assert result["exit_date"] == "2026-03-15"
        assert result["holding_days"] == 5
        assert result["outcome_category"] == "TRUE_POSITIVE"
        assert result["regime_at_signal"] == "RISK_ON"
        assert "recorded_at" in result

    def test_postmortem_with_false_positive(self):
        """Test postmortem record with false positive outcome."""
        signal = {
            "signal_id": "sig_nvda_20260305_xyz",
            "ticker": "NVDA",
            "signal_date": "2026-03-05",
            "predicted_direction": "LONG",
            "source_skill": "canslim-screener",
            "entry_price": 900.0,
            "regime": "RISK_ON",
        }

        realized_returns = {"5d": -0.033}

        result = create_postmortem_record(
            signal=signal,
            realized_returns=realized_returns,
            exit_price=870.3,
            exit_date="2026-03-10",
        )

        assert result["outcome_category"] == "FALSE_POSITIVE_SEVERE"
        assert result["holding_days"] == 5

    def test_postmortem_missing_dates(self):
        """Test postmortem with missing dates."""
        signal = {
            "signal_id": "sig_test_abc",
            "ticker": "TEST",
            "signal_date": "",
            "predicted_direction": "LONG",
            "source_skill": "test",
            "entry_price": 100.0,
        }

        result = create_postmortem_record(
            signal=signal, realized_returns={}, exit_price=105.0, exit_date=""
        )

        assert result["holding_days"] == 0
        assert result["outcome_category"] == "NEUTRAL"  # No returns data


class TestIntegration:
    """Integration tests for postmortem recording flow."""

    def test_full_postmortem_flow(self, tmp_path):
        """Test complete postmortem recording to file."""

        signal = {
            "signal_id": "sig_msft_20260301_test",
            "ticker": "MSFT",
            "signal_date": "2026-03-01",
            "predicted_direction": "LONG",
            "source_skill": "earnings-trade-analyzer",
            "entry_price": 420.0,
            "regime": "RISK_ON",
        }

        realized_returns = {"5d": 0.024, "20d": 0.045}

        postmortem = create_postmortem_record(
            signal=signal,
            realized_returns=realized_returns,
            exit_price=430.08,
            exit_date="2026-03-06",
        )

        # Write to file
        output_file = tmp_path / "pm_sig_msft_20260301_test.json"
        with open(output_file, "w") as f:
            json.dump(postmortem, f, indent=2)

        # Read back and verify
        with open(output_file) as f:
            loaded = json.load(f)

        assert loaded["ticker"] == "MSFT"
        assert loaded["outcome_category"] == "TRUE_POSITIVE"
        assert loaded["realized_returns"]["5d"] == 0.024


class TestNewPostmortemRecorderFunctions:
    """Tests for newly added/improved functions in postmortem_recorder.py."""

    @pytest.fixture
    def mock_fmp_response(self, mocker):
        """Fixture to mock requests.get for FMP API."""
        def _mock_fmp(status_code, json_data):
            mock_resp = mocker.Mock()
            mock_resp.status_code = status_code
            mock_resp.json.return_value = json_data
            mocker.patch('requests.get', return_value=mock_resp)
        return _mock_fmp

    @pytest.fixture
    def setup_macro_regime_dir(self, tmp_path):
        """Setup a temporary directory for macro regime reports."""
        reports_dir = tmp_path / "reports"
        macro_regime_dir = reports_dir / "macro_regime"
        macro_regime_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir, macro_regime_dir

    def test_get_macro_regime_found(self, setup_macro_regime_dir):
        reports_dir, macro_regime_dir = setup_macro_regime_dir
        # Create some mock regime files
        (macro_regime_dir / "macro_regime_2023-01-01_100000.json").write_text(json.dumps({"regime": "RISK_ON"}))
        (macro_regime_dir / "macro_regime_2023-01-05_100000.json").write_text(json.dumps({"regime": "RISK_OFF"}))
        (macro_regime_dir / "macro_regime_2023-01-10_100000.json").write_text(json.dumps({"regime": "TRANSITIONAL"}))

        assert get_macro_regime("2023-01-06", reports_dir) == "RISK_OFF"
        assert get_macro_regime("2023-01-01", reports_dir) == "RISK_ON"
        assert get_macro_regime("2023-01-15", reports_dir) == "TRANSITIONAL"

    def test_get_macro_regime_no_files(self, tmp_path):
        reports_dir = tmp_path / "reports"
        assert get_macro_regime("2023-01-05", reports_dir) == "UNKNOWN"

    def test_get_macro_regime_invalid_json(self, setup_macro_regime_dir, capsys):
        reports_dir, macro_regime_dir = setup_macro_regime_dir
        (macro_regime_dir / "macro_regime_2023-01-01_100000.json").write_text("invalid json")
        assert get_macro_regime("2023-01-05", reports_dir) == "UNKNOWN"
        captured = capsys.readouterr()
        assert "Warning: Error reading macro regime file" in captured.err

    def test_get_macro_regime_future_files(self, setup_macro_regime_dir):
        reports_dir, macro_regime_dir = setup_macro_regime_dir
        (macro_regime_dir / "macro_regime_2023-01-10_100000.json").write_text(json.dumps({"regime": "RISK_ON"}))
        assert get_macro_regime("2023-01-05", reports_dir) == "UNKNOWN" # Should not pick up future file

    def test_fetch_price_data_stable_api_success(self, mock_fmp_response):
        mock_fmp_response(200, {"historical": [{"date": "2023-01-01", "close": 100.0}]})
        prices = fetch_price_data("AAPL", "2023-01-01", "2023-01-01", "fake_key")
        assert prices == {"2023-01-01": 100.0}

    def test_fetch_price_data_v3_api_success(self, mock_fmp_response):
        mock_fmp_response(200, {"historicalStockList": [{"symbol": "AAPL", "historical": [{"date": "2023-01-01", "close": 100.0}]}]})
        prices = fetch_price_data("AAPL", "2023-01-01", "2023-01-01", "fake_key")
        assert prices == {"2023-01-01": 100.0}

    def test_fetch_price_data_api_failure(self, mock_fmp_response, capsys):
        mock_fmp_response(404, {})
        prices = fetch_price_data("AAPL", "2023-01-01", "2023-01-01", "fake_key")
        assert prices == {}
        captured = capsys.readouterr()
        assert "Warning: Failed to fetch price data" in captured.err

    def test_fetch_price_data_no_requests_module(self, mocker):
        mocker.patch('postmortem_recorder.HAS_REQUESTS', False)
        prices = fetch_price_data("AAPL", "2023-01-01", "2023-01-01", "fake_key")
        assert prices == {}

    def test_process_signal_successful_recording(self, mocker, tmp_path):
        mocker.patch('postmortem_recorder.fetch_price_data', return_value={
            "2023-01-01": 100.0, "2023-01-06": 105.0, "2023-01-26": 110.0
        })
        mocker.patch('postmortem_recorder.get_macro_regime', return_value="RISK_ON")
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        signal = {
            "signal_id": "sig_test_20230101_001",
            "ticker": "TEST",
            "signal_date": "2023-01-01",
            "predicted_direction": "LONG",
            "source_skill": "test_skill",
            "entry_price": 0.0, # Will be fetched
            "regime": "RISK_ON"
        }
        postmortem = process_signal(signal, [5, 20], "fake_key", reports_dir=reports_dir)
        assert postmortem is not None
        assert postmortem["outcome_category"] == "TRUE_POSITIVE"
        assert postmortem["realized_returns"]["5d"] == pytest.approx(0.05)
        assert postmortem["realized_returns"]["20d"] == pytest.approx(0.10)
        assert postmortem["regime_at_exit"] == "RISK_ON"

    def test_process_signal_manual_exit(self, mocker, tmp_path):
        mocker.patch('postmortem_recorder.fetch_price_data', return_value={}) # No auto-fetch
        mocker.patch('postmortem_recorder.get_macro_regime', return_value="RISK_OFF")
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        signal = {
            "signal_id": "sig_test_20230101_002",
            "ticker": "TEST",
            "signal_date": "2023-01-01",
            "predicted_direction": "SHORT",
            "source_skill": "test_skill",
            "entry_price": 100.0,
            "regime": "RISK_ON"
        }
        postmortem = process_signal(
            signal, [5], api_key="fake_key", manual_exit_price=90.0, manual_exit_date="2023-01-05", reports_dir=reports_dir
        )
        assert postmortem is not None
        assert postmortem["outcome_category"] == "TRUE_POSITIVE"
        assert postmortem["exit_price"] == 90.0
        assert postmortem["exit_date"] == "2023-01-05"
        assert postmortem["regime_at_exit"] == "RISK_OFF"

    def test_process_signal_missing_data(self, mocker, capsys, tmp_path):
        mocker.patch('postmortem_recorder.fetch_price_data', return_value={
            "2023-01-01": 100.0 # Only entry price available
        })
        mocker.patch('postmortem_recorder.get_macro_regime', return_value="UNKNOWN")
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        signal = {
            "signal_id": "sig_test_20230101_003",
            "ticker": "TEST",
            "signal_date": "2023-01-01",
            "predicted_direction": "LONG",
            "source_skill": "test_skill",
            "entry_price": 0.0,
            "regime": "RISK_ON"
        }
        postmortem = process_signal(signal, [5, 20], "fake_key", reports_dir=reports_dir)
        assert postmortem is not None
        # Should default to entry price for exit if no data, leading to NEUTRAL if no returns
        assert postmortem["outcome_category"] == "NEUTRAL"
        captured = capsys.readouterr()
        # Expecting a warning about no price for 5d or 20d, but current implementation does not print it.
        # It just won't add the return.
        assert "5d" not in postmortem["realized_returns"]

    def test_process_signal_no_api_key_no_entry_price(self, capsys, tmp_path):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        signal = {
            "signal_id": "sig_test_20230101_004",
            "ticker": "TEST",
            "signal_date": "2023-01-01",
            "predicted_direction": "LONG",
            "source_skill": "test_skill",
            "entry_price": 0.0,
            "regime": "RISK_ON"
        }
        postmortem = process_signal(signal, [5], reports_dir=reports_dir) # No api_key
        assert postmortem is None
        captured = capsys.readouterr()
        assert "Warning: No entry price for TEST on 2023-01-01" in captured.err

    def test_list_ready_signals(self, tmp_path):
        signals_dir = tmp_path / "state" / "signals"
        signals_dir.mkdir(parents=True)

        # Create mock signal files
        (signals_dir / "signal_old.json").write_text(json.dumps({"signal_date": "2023-01-01", "signal_id": "old_sig"}))
        (signals_dir / "signal_recent.json").write_text(json.dumps({"signal_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"), "signal_id": "recent_sig"}))
        (signals_dir / "signal_invalid.json").write_text("invalid json")
        (signals_dir / "signal_empty.json").write_text(json.dumps({}))

        ready_signals = list_ready_signals(str(signals_dir), min_days=3)
        assert len(ready_signals) == 1
        assert ready_signals[0]["signal_id"] == "old_sig"

        # Test with no ready signals
        ready_signals_none = list_ready_signals(str(signals_dir), min_days=0)
        assert len(ready_signals_none) == 1 # "old_sig" is still old enough for min_days=0 too

    def test_list_ready_signals_empty_dir(self, tmp_path):
        signals_dir = tmp_path / "empty_signals"
        signals_dir.mkdir()
        ready_signals = list_ready_signals(str(signals_dir))
        assert len(ready_signals) == 0

    def test_list_ready_signals_non_existent_dir(self, tmp_path):
        signals_dir = tmp_path / "non_existent"
        ready_signals = list_ready_signals(str(signals_dir))
        assert len(ready_signals) == 0

    @patch('sys.exit')
    @patch('builtins.print')
    def test_main_list_ready(self, mock_print, mock_exit, mocker, tmp_path):
        signals_dir = tmp_path / "state" / "signals"
        signals_dir.mkdir(parents=True)
        (signals_dir / "signal_ready.json").write_text(json.dumps({"signal_date": "2023-01-01", "signal_id": "ready_sig"}))

        test_args = ["--list-ready", "--signals-dir", str(signals_dir), "--min-days", "0"]
        mocker.patch('sys.argv', ['postmortem_recorder.py'] + test_args)
        recorder_main()
        mock_print.assert_any_call("Found 1 signals ready for postmortem:")
        mock_print.assert_any_call("  ready_sig: N/A on 2023-01-01")
        mock_exit.assert_not_called()

    @patch('sys.exit')
    @patch('builtins.print')
    def test_main_manual_recording(self, mock_print, mock_exit, mocker, tmp_path):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "macro_regime" ).mkdir()
        (reports_dir / "macro_regime" / "macro_regime_2023-01-05_100000.json").write_text(json.dumps({"regime": "RISK_OFF"}))

        test_args = [
            "--signal-id", "sig_AAPL_20230101_XYZ",
            "--exit-price", "150.0",
            "--exit-date", "2023-01-05",
            "--output-dir", str(tmp_path),
            "--outcome-notes", "Test notes"
        ]
        mocker.patch('sys.argv', ['postmortem_recorder.py'] + test_args)
        recorder_main()

        output_file = tmp_path / "postmortems" / "pm_sig_AAPL_20230101_XYZ.json"
        assert output_file.exists()
        with open(output_file) as f:
            pm = json.load(f)
        assert pm["ticker"] == "AAPL"
        assert pm["signal_date"] == "2023-01-01"
        assert pm["exit_price"] == 150.0
        assert pm["exit_date"] == "2023-01-05"
        assert pm["outcome_notes"] == "Test notes"
        assert pm["regime_at_exit"] == "RISK_OFF"
        mock_print.assert_any_call(f"Saved postmortem: {output_file}")
        mock_print.assert_any_call("Outcome: NEUTRAL") # No returns in this minimal signal
        mock_exit.assert_not_called()

    @patch('sys.exit')
    @patch('builtins.print')
    def test_main_batch_processing(self, mock_print, mock_exit, mocker, tmp_path):
        signals_file = tmp_path / "signals.json"
        signals_file.write_text(json.dumps([
            {"signal_id": "sig_MSFT_20230101_A", "ticker": "MSFT", "signal_date": "2023-01-01", "predicted_direction": "LONG", "entry_price": 100.0, "regime": "RISK_ON"},
            {"signal_id": "sig_GOOG_20230102_B", "ticker": "GOOG", "signal_date": "2023-01-02", "predicted_direction": "SHORT", "entry_price": 200.0, "regime": "RISK_OFF"}
        ]))

        mocker.patch('postmortem_recorder.fetch_price_data', side_effect=[
            {"2023-01-01": 100.0, "2023-01-06": 105.0}, # For MSFT (5d)
            {"2023-01-02": 200.0, "2023-01-07": 190.0}  # For GOOG (5d)
        ])
        mocker.patch('postmortem_recorder.get_macro_regime', return_value="RISK_ON") # Simplistic for test

        test_args = [
            "--signals-file", str(signals_file),
            "--api-key", "fake_key",
            "--output-dir", str(tmp_path)
        ]
        mocker.patch('sys.argv', ['postmortem_recorder.py'] + test_args)
        recorder_main()

        msft_output = tmp_path / "postmortems" / "pm_sig_MSFT_20230101_A.json"
        goog_output = tmp_path / "postmortems" / "pm_sig_GOOG_20230102_B.json"
        assert msft_output.exists()
        assert goog_output.exists()

        with open(msft_output) as f:
            msft_pm = json.load(f)
        assert msft_pm["outcome_category"] == "TRUE_POSITIVE"
        assert msft_pm["realized_returns"]["5d"] == pytest.approx(0.05)

        with open(goog_output) as f:
            goog_pm = json.load(f)
        assert goog_pm["outcome_category"] == "TRUE_POSITIVE" # Short, price went down
        assert goog_pm["realized_returns"]["5d"] == pytest.approx(-0.05)

        mock_print.assert_any_call("Processed 2/2 signals")
        mock_exit.assert_not_called()

    @patch('sys.exit')
    @patch('builtins.print')
    def test_main_signal_id_parsing(self, mock_print, mock_exit, mocker, tmp_path):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "macro_regime" ).mkdir()
        (reports_dir / "macro_regime" / "macro_regime_2023-01-05_100000.json").write_text(json.dumps({"regime": "RISK_OFF"}))

        test_args = [
            "--signal-id", "sig_BRK.A_20230101_custom",
            "--exit-price", "1500.0",
            "--exit-date", "2023-01-05",
            "--output-dir", str(tmp_path)
        ]
        mocker.patch('sys.argv', ['postmortem_recorder.py'] + test_args)
        recorder_main()

        output_file = tmp_path / "postmortems" / "pm_sig_BRK.A_20230101_custom.json"
        assert output_file.exists()
        with open(output_file) as f:
            pm = json.load(f)
        assert pm["ticker"] == "BRK.A"
        assert pm["signal_date"] == "2023-01-01"
        mock_exit.assert_not_called()

    @patch('sys.exit')
    @patch('builtins.print')
    def test_main_signal_id_parsing_invalid_date_warns(self, mock_print, mock_exit, mocker, tmp_path):
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "macro_regime" ).mkdir()
        (reports_dir / "macro_regime" / "macro_regime_2023-01-05_100000.json").write_text(json.dumps({"regime": "RISK_OFF"}))

        test_args = [
            "--signal-id", "sig_BRK.A_20239999_custom", # Invalid date
            "--exit-price", "1500.0",
            "--exit-date", "2023-01-05",
            "--output-dir", str(tmp_path)
        ]
        mocker.patch('sys.argv', ['postmortem_recorder.py'] + test_args)
        recorder_main()

        output_file = tmp_path / "postmortems" / "pm_sig_BRK.A_20239999_custom.json"
        assert output_file.exists()
        with open(output_file) as f:
            pm = json.load(f)
        assert pm["ticker"] == "BRK.A"
        assert pm["signal_date"] == datetime.now().strftime("%Y-%m-%d") # Should be current date
        mock_print.assert_any_call(f"Warning: Could not parse date from signal_id: 20239999. Using current date.", file=sys.stderr)
        mock_exit.assert_not_called()
