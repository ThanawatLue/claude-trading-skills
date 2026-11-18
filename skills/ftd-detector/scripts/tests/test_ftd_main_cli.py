"""Tests for ftd_detector.py CLI fallback to YFClient and --market support."""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import ftd_detector


def _make_hist(n: int = 80, base: float = 500.0):
    return [
        {
            "date": f"2026-09-{(i % 28) + 1:02d}",
            "open": base + i * 0.2,
            "high": base + i * 0.2 + 1.0,
            "low": base + i * 0.2 - 1.0,
            "close": base + i * 0.2,
            "volume": 10_000_000,
        }
        for i in range(n)
    ]


def test_ftd_falls_back_to_yf_without_api_key(tmp_path, monkeypatch):
    """ftd_detector must work cleanly via YFClient when FMP_API_KEY is absent."""
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ftd_detector.py", "--output-dir", str(tmp_path)],
    )

    mock_yf = MagicMock()
    mock_yf.get_historical_prices.return_value = {"historical": _make_hist()}
    mock_yf.get_quote.return_value = [{"price": 520.0}]
    mock_yf.get_api_stats.return_value = {"api_calls_made": 0, "cache_entries": 2}

    with patch("ftd_detector.YFClient", return_value=mock_yf):
        ftd_detector.main()

    reports = list(tmp_path.glob("ftd_detector_*.json"))
    assert len(reports) == 1
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["metadata"]["market"] == "US"
    mock_yf.get_historical_prices.assert_called()


def test_ftd_supports_th_market_with_thd_proxy(tmp_path, monkeypatch):
    """--market TH analyzes THD proxy and tags metadata.market = TH."""
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ftd_detector.py", "--market", "TH", "--output-dir", str(tmp_path)],
    )

    mock_yf = MagicMock()
    mock_yf.get_historical_prices.return_value = {"historical": _make_hist(base=65.0)}
    mock_yf.get_quote.return_value = [{"price": 67.5}]
    mock_yf.get_api_stats.return_value = {"api_calls_made": 0, "cache_entries": 1}

    with patch("ftd_detector.YFClient", return_value=mock_yf):
        ftd_detector.main()

    reports = list(tmp_path.glob("ftd_detector_*.json"))
    assert len(reports) == 1
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["metadata"]["market"] == "TH"
    mock_yf.get_historical_prices.assert_any_call("THD", days=80)
