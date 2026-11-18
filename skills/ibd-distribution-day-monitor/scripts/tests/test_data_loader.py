"""Tests for data_loader (FMP wrapper + audit flags)."""

from unittest.mock import MagicMock

from data_loader import normalize_history, validate_history_quality


def _row(date, close, volume=1_000_000, high=None, low=None, open_=None):
    return {
        "date": date,
        "open": open_ if open_ is not None else close,
        "high": high if high is not None else close + 0.5,
        "low": low if low is not None else close - 0.5,
        "close": close,
        "volume": volume,
    }


class TestNormalizeHistory:
    def test_dict_with_historical_key(self):
        payload = {
            "symbol": "QQQ",
            "historical": [
                _row("2026-04-30", 500.0),
                _row("2026-04-29", 499.0),
            ],
        }
        rows = normalize_history(payload)
        assert len(rows) == 2
        assert rows[0]["date"] == "2026-04-30"

    def test_list_passthrough(self):
        payload = [_row("2026-04-30", 500.0), _row("2026-04-29", 499.0)]
        rows = normalize_history(payload)
        assert len(rows) == 2

    def test_none_returns_empty(self):
        assert normalize_history(None) == []


class TestValidateHistoryQuality:
    def test_no_issues_when_clean(self):
        history = [_row("2026-04-30", 500.0), _row("2026-04-29", 499.0)]
        flags, skipped = validate_history_quality(history)
        assert flags == []
        assert skipped == []

    def test_volume_zero_flagged_as_skipped(self):
        history = [
            _row("2026-04-30", 500.0, volume=0),
            _row("2026-04-29", 499.0),
        ]
        flags, skipped = validate_history_quality(history)
        assert any(s["reason"] == "invalid_volume" for s in skipped)

    def test_close_missing_flagged_as_skipped(self):
        history = [
            {"date": "2026-04-30", "close": None, "volume": 1_000_000},
            _row("2026-04-29", 499.0),
        ]
        flags, skipped = validate_history_quality(history)
        assert any(s["reason"] == "missing_close" for s in skipped)

    def test_close_zero_flagged_as_skipped(self):
        history = [
            _row("2026-04-30", 0.0),
            _row("2026-04-29", 499.0),
        ]
        flags, skipped = validate_history_quality(history)
        assert any(s["reason"] == "invalid_close" for s in skipped)


class TestFetchOHLCVMocked:
    """Higher-level FMP wrapper covered with a mocked client.

    Real network calls are out of scope for unit tests.
    """

    def test_fetch_uses_provided_client(self):
        from data_loader import fetch_ohlcv

        mock_client = MagicMock()
        mock_client.get_historical_prices.return_value = {
            "symbol": "QQQ",
            "historical": [
                _row("2026-04-30", 500.0),
                _row("2026-04-29", 499.0),
            ],
        }

        history, audit = fetch_ohlcv(mock_client, "QQQ", days=2)
        assert len(history) == 2
        assert history[0]["date"] == "2026-04-30"
        assert audit["data_source"] == "fmp"
        assert audit["audit_flags"] == []
        mock_client.get_historical_prices.assert_called_once_with("QQQ", days=2)

    def test_fetch_returns_audit_flag_when_no_data(self):
        from data_loader import fetch_ohlcv

        mock_client = MagicMock()
        mock_client.get_historical_prices.return_value = None
        history, audit = fetch_ohlcv(mock_client, "QQQ", days=80)
        assert history == []
        assert "no_data_returned" in audit["audit_flags"]


def test_ibd_monitor_falls_back_to_yf_when_fmp_returns_none(tmp_path, monkeypatch):
    """ibd_monitor must fall back to YFClient when FMP canary or symbol returns None (e.g. HTTP 403)."""
    import json
    from unittest.mock import patch

    import ibd_monitor

    monkeypatch.setenv("FMP_API_KEY", "test_key")

    mock_fmp = MagicMock()
    mock_fmp.rate_limit_reached = False
    mock_fmp.get_historical_prices.return_value = None  # Simulates 403 legacy endpoint failure

    dates = [f"2026-09-{(i % 28) + 1:02d}" for i in range(60)]
    mock_yf = MagicMock()
    mock_yf.get_historical_prices.return_value = {
        "historical": [_row(d, 500.0 + idx * 0.1) for idx, d in enumerate(reversed(dates))]
    }

    with (
        patch.object(ibd_monitor, "build_fmp_client", return_value=mock_fmp),
        patch.object(ibd_monitor, "build_yf_client", return_value=mock_yf),
    ):
        rc = ibd_monitor.main(["--symbols", "THD", "--market", "TH", "--output-dir", str(tmp_path)])

    assert rc == 0
    reports = list(tmp_path.glob("ibd_distribution_day_monitor_*.json"))
    assert len(reports) == 1
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["audit"]["data_source"] == "yfinance"
    assert payload["metadata"]["market"] == "TH"
