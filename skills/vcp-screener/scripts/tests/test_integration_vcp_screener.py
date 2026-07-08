import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from screen_vcp import main

# Mock data for S&P 500 constituents
MOCK_SP500_CONSTITUENTS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "subSector": "Consumer Electronics",
    },
    {"symbol": "MSFT", "name": "Microsoft Corp.", "sector": "Technology", "subSector": "Software"},
    {
        "symbol": "GOOG",
        "name": "Alphabet Inc. (Class C)",
        "sector": "Technology",
        "subSector": "Internet Services",
    },
    {
        "symbol": "AMZN",
        "name": "Amazon.com Inc.",
        "sector": "Consumer Discretionary",
        "subSector": "Internet Retail",
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corp.",
        "sector": "Technology",
        "subSector": "Semiconductors",
    },
    {
        "symbol": "TSLA",
        "name": "Tesla Inc.",
        "sector": "Consumer Discretionary",
        "subSector": "Automobiles",
    },
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials", "subSector": "Banks"},
]

# Mock data for quotes
MOCK_QUOTES = {
    "AAPL": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 170.0,
        "yearHigh": 180.0,
        "yearLow": 120.0,
        "avgVolume": 100_000_000,
        "marketCap": 2_800_000_000_000,
        "sector": "Technology",
    },
    "MSFT": {
        "symbol": "MSFT",
        "name": "Microsoft Corp.",
        "price": 400.0,
        "yearHigh": 420.0,
        "yearLow": 280.0,
        "avgVolume": 50_000_000,
        "marketCap": 3_000_000_000_000,
        "sector": "Technology",
    },
    "GOOG": {
        "symbol": "GOOG",
        "name": "Alphabet Inc. (Class C)",
        "price": 150.0,
        "yearHigh": 160.0,
        "yearLow": 100.0,
        "avgVolume": 30_000_000,
        "marketCap": 1_900_000_000_000,
        "sector": "Technology",
    },
    "AMZN": {
        "symbol": "AMZN",
        "name": "Amazon.com Inc.",
        "price": 180.0,
        "yearHigh": 190.0,
        "yearLow": 130.0,
        "avgVolume": 70_000_000,
        "marketCap": 1_800_000_000_000,
        "sector": "Consumer Discretionary",
    },
    "NVDA": {
        "symbol": "NVDA",
        "name": "NVIDIA Corp.",
        "price": 900.0,
        "yearHigh": 950.0,
        "yearLow": 400.0,
        "avgVolume": 80_000_000,
        "marketCap": 2_200_000_000_000,
        "sector": "Technology",
    },
    "TSLA": {
        "symbol": "TSLA",
        "name": "Tesla Inc.",
        "price": 175.0,
        "yearHigh": 200.0,
        "yearLow": 150.0,
        "avgVolume": 60_000_000,
        "marketCap": 600_000_000_000,
        "sector": "Consumer Discretionary",
    },
    "JPM": {
        "symbol": "JPM",
        "name": "JPMorgan Chase & Co.",
        "price": 190.0,
        "yearHigh": 200.0,
        "yearLow": 140.0,
        "avgVolume": 20_000_000,
        "marketCap": 500_000_000_000,
        "sector": "Financials",
    },
}

# Mock data for historical prices (simplified for testing)
# A more realistic mock would generate actual OHLCV data.
# For now, ensure enough bars for SMA calculations (e.g., >200 days)
MOCK_HISTORICAL_PRICES = {
    "AAPL": {
        "symbol": "AAPL",
        "historical": [
            {
                "date": f"2023-01-{i:02d}",
                "open": 100 + i,
                "high": 102 + i,
                "low": 98 + i,
                "close": 101 + i,
                "volume": 100_000_000,
            }
            for i in range(1, 251)
        ],
    },
    "MSFT": {
        "symbol": "MSFT",
        "historical": [
            {
                "date": f"2023-01-{i:02d}",
                "open": 200 + i,
                "high": 202 + i,
                "low": 198 + i,
                "close": 201 + i,
                "volume": 50_000_000,
            }
            for i in range(1, 251)
        ],
    },
    "GOOG": {
        "symbol": "GOOG",
        "historical": [
            {
                "date": f"2023-01-{i:02d}",
                "open": 100 + i,
                "high": 102 + i,
                "low": 98 + i,
                "close": 101 + i,
                "volume": 30_000_000,
            }
            for i in range(1, 251)
        ],
    },
    "AMZN": {
        "symbol": "AMZN",
        "historical": [
            {
                "date": f"2023-01-{i:02d}",
                "open": 180 + i,
                "high": 182 + i,
                "low": 178 + i,
                "close": 181 + i,
                "volume": 70_000_000,
            }
            for i in range(1, 251)
        ],
    },
    "NVDA": {
        "symbol": "NVDA",
        "historical": [
            {
                "date": f"2023-01-{i:02d}",
                "open": 500 + i,
                "high": 505 + i,
                "low": 495 + i,
                "close": 502 + i,
                "volume": 80_000_000,
            }
            for i in range(1, 251)
        ],
    },
    "SPY": {
        "symbol": "SPY",
        "historical": [
            {
                "date": f"2023-01-{i:02d}",
                "open": 400 + i,
                "high": 402 + i,
                "low": 398 + i,
                "close": 401 + i,
                "volume": 120_000_000,
            }
            for i in range(1, 251)
        ],
    },
}


@pytest.fixture
def mock_yf_client():
    """Fixture to mock YFClient methods."""
    with patch("screen_vcp.YFClient") as MockClient:
        instance = MockClient.return_value
        instance.get_sp500_constituents.return_value = MOCK_SP500_CONSTITUENTS
        instance.get_batch_quotes.side_effect = lambda symbols: {
            s: MOCK_QUOTES.get(s) for s in symbols
        }
        instance.get_historical_prices.side_effect = (
            lambda symbol, days: MOCK_HISTORICAL_PRICES.get(symbol)
        )
        instance.get_api_stats.return_value = {
            "api_calls_made": 5,
            "cache_entries": 10,
            "rate_limit_reached": False,
        }
        yield instance


@pytest.fixture
def mock_fmp_client():
    """Fixture to mock FMPClient methods."""
    with patch("screen_vcp.FMPClient") as MockClient:
        instance = MockClient.return_value
        instance.get_sp500_constituents.return_value = MOCK_SP500_CONSTITUENTS
        instance.get_batch_quotes.side_effect = lambda symbols: {
            s: MOCK_QUOTES.get(s)
            for s in (symbols.split(",") if isinstance(symbols, str) else symbols)
        }
        instance.get_historical_prices.side_effect = (
            lambda symbol, days: MOCK_HISTORICAL_PRICES.get(symbol)
        )
        instance.get_api_stats.return_value = {
            "api_calls_made": 5,
            "cache_entries": 10,
            "rate_limit_reached": False,
        }
        yield instance


@pytest.fixture
def mock_reports():
    """Fixture to mock report generation functions."""
    with (
        patch("screen_vcp.generate_json_report") as mock_json_report,
        patch("screen_vcp.generate_markdown_report") as mock_md_report,
        patch("screen_vcp.os.makedirs"),
        patch("screen_vcp.os.path.join", side_effect=lambda *args: "/".join(args)),
    ):
        yield mock_json_report, mock_md_report


@pytest.fixture(autouse=True)
def mock_get_recent_expectancy():
    """Fixture to mock get_recent_expectancy to avoid DB access."""
    with patch("screen_vcp.get_recent_expectancy") as mock_expectancy:
        mock_expectancy.return_value = (0.5, 10)  # Simulate a positive expectancy
        yield mock_expectancy


class TestVPCScreenerIntegration:
    @patch(
        "screen_vcp.argparse.ArgumentParser.parse_args",
        return_value=MagicMock(
            api_key=None,
            max_candidates=10,
            top=5,
            output_dir="reports/",
            universe=None,
            full_sp500=False,
            market="US",
            mode="all",
            max_above_pivot=3.0,
            max_risk=15.0,
            no_require_valid_vcp=False,
            min_atr_pct=1.0,
            ext_threshold=8.0,
            min_contractions=2,
            t1_depth_min=10.0,
            breakout_volume_ratio=1.5,
            trend_min_score=85.0,
            atr_multiplier=1.5,
            contraction_ratio=0.70,
            min_contraction_days=5,
            lookback_days=120,
            max_sma200_extension=50.0,
            wide_and_loose_threshold=15.0,
            strict=False,
        ),
    )
    def test_main_happy_path_yf(self, mock_args, mock_yf_client, mock_reports):
        """Test the main function with YFClient, happy path."""
        mock_json_report, mock_md_report = mock_reports
        main()

        # Verify client methods were called
        mock_yf_client.get_sp500_constituents.assert_called_once()
        mock_yf_client.get_batch_quotes.assert_called_once()
        assert mock_yf_client.get_historical_prices.call_count >= 1  # SPY + candidates

        # Verify reports were generated
        mock_json_report.assert_called_once()
        mock_md_report.assert_called_once()

        # Ensure results were passed to reports (check first arg, which is results list)
        results = mock_json_report.call_args[0][0]
        assert isinstance(results, list)
        assert len(results) <= mock_args.return_value.top  # Check top N results limit
        if results:
            assert all(isinstance(r, dict) for r in results)
            assert "composite_score" in results[0]

    @patch(
        "screen_vcp.argparse.ArgumentParser.parse_args",
        return_value=MagicMock(
            api_key="mock_fmp_key",  # pragma: allowlist secret
            max_candidates=10,
            top=5,
            output_dir="reports/",
            universe=None,
            full_sp500=False,
            market="US",
            mode="all",
            max_above_pivot=3.0,
            max_risk=15.0,
            no_require_valid_vcp=False,
            min_atr_pct=1.0,
            ext_threshold=8.0,
            min_contractions=2,
            t1_depth_min=10.0,
            breakout_volume_ratio=1.5,
            trend_min_score=85.0,
            atr_multiplier=1.5,
            contraction_ratio=0.70,
            min_contraction_days=5,
            lookback_days=120,  # This looks like a typo, should be lookback_days=120
            max_sma200_extension=50.0,
            wide_and_loose_threshold=15.0,
            strict=False,
        ),
    )
    def test_main_happy_path_fmp(self, mock_args, mock_fmp_client, mock_reports):
        """Test the main function with FMPClient, happy path."""
        mock_json_report, mock_md_report = mock_reports
        main()

        # Verify client methods were called
        mock_fmp_client.get_sp500_constituents.assert_called_once()
        mock_fmp_client.get_batch_quotes.assert_called_once()
        assert mock_fmp_client.get_historical_prices.call_count >= 1  # SPY + candidates

        # Verify reports were generated
        mock_json_report.assert_called_once()
        mock_md_report.assert_called_once()

    @patch(
        "screen_vcp.argparse.ArgumentParser.parse_args",
        return_value=MagicMock(
            api_key=None,
            max_candidates=10,
            top=5,
            output_dir="reports/",
            universe=None,
            full_sp500=False,
            market="US",
            mode="all",
            max_above_pivot=3.0,
            max_risk=15.0,
            no_require_valid_vcp=False,
            min_atr_pct=1.0,
            ext_threshold=8.0,
            min_contractions=2,
            t1_depth_min=10.0,
            breakout_volume_ratio=1.5,
            trend_min_score=85.0,
            atr_multiplier=1.5,
            contraction_ratio=0.70,
            min_contraction_days=5,
            lookback_days=120,
            max_sma200_extension=50.0,
            wide_and_loose_threshold=15.0,
            strict=False,
        ),
    )
    @patch("screen_vcp.YFClient.get_sp500_constituents", return_value=None)
    def test_main_no_constituents(self, mock_args, mock_get_constituents, mock_reports):
        """Test main function when no S&P 500 constituents are returned."""
        with pytest.raises(SystemExit):
            main()
        mock_get_constituents.assert_called_once()
        # No reports should be generated
        mock_reports[0].assert_not_called()
        mock_reports[1].assert_not_called()

    @patch(
        "screen_vcp.argparse.ArgumentParser.parse_args",
        return_value=MagicMock(
            api_key=None,
            max_candidates=10,
            top=5,
            output_dir="reports/",
            universe=["INVALID"],  # Provide an invalid symbol
            full_sp500=False,
            market="US",
            mode="all",
            max_above_pivot=3.0,
            max_risk=15.0,
            no_require_valid_vcp=False,
            min_atr_pct=1.0,
            ext_threshold=8.0,
            min_contractions=2,
            t1_depth_min=10.0,
            breakout_volume_ratio=1.5,
            trend_min_score=85.0,
            atr_multiplier=1.5,
            contraction_ratio=0.70,
            min_contraction_days=5,
            lookback_days=120,
            max_sma200_extension=50.0,
            wide_and_loose_threshold=15.0,
            strict=False,
        ),
    )
    @patch("screen_vcp.YFClient.get_batch_quotes", return_value={})  # No quotes for invalid symbol
    @patch("screen_vcp.YFClient")  # Mock the client instantiation
    def test_main_no_candidates_after_prefilter(
        self, mock_yf_client_class, mock_get_batch_quotes, mock_args, mock_reports
    ):
        """Test main function when no candidates pass the pre-filter."""
        mock_instance = mock_yf_client_class.return_value
        mock_instance.get_sp500_constituents.return_value = (
            MOCK_SP500_CONSTITUENTS  # Still need constituents to get to pre-filter
        )
        mock_instance.get_batch_quotes.return_value = {}  # No quotes will result in no pre-filtered stocks
        mock_instance.get_historical_prices.return_value = MOCK_HISTORICAL_PRICES.get(
            "SPY"
        )  # Still need SPY history
        mock_instance.get_api_stats.return_value = {
            "api_calls_made": 5,
            "cache_entries": 10,
            "rate_limit_reached": False,
        }

        main()

        # Reports should still be generated, but with an empty results list
        mock_reports[0].assert_called_once()
        mock_reports[1].assert_called_once()

        results_list = mock_reports[0].call_args[0][0]
        assert results_list == []
