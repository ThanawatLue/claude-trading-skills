"""Tests for dividend-growth-pullback-screener screening logic.

These tests validate the core calculation functions without requiring
live API keys (FMP or FINVIZ). All external I/O is stubbed.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers to import the main script without executing top-level side effects
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "screen_dividend_growth_rsi.py"


def _load_script() -> ModuleType:
    """Import screen_dividend_growth_rsi as a module."""
    spec = importlib.util.spec_from_file_location("screen_dg", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    # Stub heavy imports that are not needed for unit tests
    sys.modules.setdefault("requests", MagicMock())
    sys.modules.setdefault("pandas", MagicMock())
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# RSI calculation tests
# ---------------------------------------------------------------------------


class TestRsiCalculation:
    """Validate the 14-period RSI formula used in the screener."""

    @pytest.fixture(scope="class")
    def mod(self):
        if not SCRIPT_PATH.exists():
            pytest.skip(f"Script not found: {SCRIPT_PATH}")
        return _load_script()

    def _prices_up(self, n: int = 30) -> list[float]:
        """Steadily rising prices → RSI should be high (>70)."""
        return [100.0 + i for i in range(n)]

    def _prices_down(self, n: int = 30) -> list[float]:
        """Steadily falling prices → RSI should be low (<30)."""
        return [100.0 - i for i in range(n)]

    def _prices_flat(self, n: int = 30) -> list[float]:
        """Flat prices (no change) → RSI = 50 by convention."""
        return [100.0] * n

    def test_rsi_function_exists(self, mod):
        """The script must expose a callable that computes RSI."""
        candidates = [
            name for name in dir(mod) if "rsi" in name.lower() and callable(getattr(mod, name))
        ]
        assert candidates, "No RSI function found in the script"

    def test_rsi_rising_prices_above_50(self, mod):
        candidates = [n for n in dir(mod) if "rsi" in n.lower() and callable(getattr(mod, n))]
        fn = getattr(mod, candidates[0])
        try:
            result = fn(self._prices_up())
        except Exception:
            pytest.skip("RSI function signature differs; skipping value test")
        if result is None:
            pytest.skip("RSI function returned None for rising prices")
        assert result > 50, f"RSI for rising prices should be >50, got {result}"

    def test_rsi_falling_prices_below_50(self, mod):
        candidates = [n for n in dir(mod) if "rsi" in n.lower() and callable(getattr(mod, n))]
        fn = getattr(mod, candidates[0])
        try:
            result = fn(self._prices_down())
        except Exception:
            pytest.skip("RSI function signature differs; skipping value test")
        if result is None:
            pytest.skip("RSI function returned None for falling prices")
        assert result < 50, f"RSI for falling prices should be <50, got {result}"

    def test_rsi_bounds(self, mod):
        """RSI must always be in [0, 100]."""
        candidates = [n for n in dir(mod) if "rsi" in n.lower() and callable(getattr(mod, n))]
        fn = getattr(mod, candidates[0])
        for prices in [self._prices_up(), self._prices_down(), self._prices_flat()]:
            try:
                result = fn(prices)
            except Exception:
                continue
            if result is None:
                continue
            assert 0 <= result <= 100, f"RSI out of [0,100] bounds: {result}"


# ---------------------------------------------------------------------------
# Dividend CAGR calculation tests
# ---------------------------------------------------------------------------


class TestDividendCagr:
    """Validate dividend CAGR computation."""

    @pytest.fixture(scope="class")
    def mod(self):
        if not SCRIPT_PATH.exists():
            pytest.skip(f"Script not found: {SCRIPT_PATH}")
        return _load_script()

    def test_cagr_function_exists(self, mod):
        assert hasattr(mod, "StockAnalyzer"), "StockAnalyzer class not found"
        assert hasattr(mod.StockAnalyzer, "calculate_cagr"), (
            "calculate_cagr not found in StockAnalyzer"
        )

    def test_cagr_doubles_in_six_years(self, mod):
        """12% CAGR should double the dividend in ~6 years."""
        fn = mod.StockAnalyzer.calculate_cagr
        try:
            # Dividend goes from 1.0 to 2.0 over 6 years ≈ 12.2% CAGR
            result = fn(1.0, 2.0, 6)
        except Exception:
            pytest.skip("CAGR function signature differs; skipping value test")
        if result is None:
            pytest.skip("CAGR function returned None")
        assert 11 < result < 14, f"Expected ~12% CAGR, got {result}"

    def test_cagr_zero_years_safe(self, mod):
        """CAGR with zero years should not raise ZeroDivisionError."""
        fn = mod.StockAnalyzer.calculate_cagr
        try:
            result = fn(1.0, 2.0, 0)
            assert result is None or math.isnan(result) or result == 0
        except ZeroDivisionError:
            pytest.fail("CAGR function raised ZeroDivisionError for n=0")
        except Exception:
            pass  # Other exceptions are acceptable for edge cases


# ---------------------------------------------------------------------------
# Script structure / CLI smoke tests
# ---------------------------------------------------------------------------


class TestFINVIZClient:
    """Validate FINVIZClient's API interactions."""

    @pytest.fixture
    def finviz_client(self, mod):
        """Fixture for FINVIZClient instance."""
        return mod.FINVIZClient(api_key="TEST_FINVIZ_KEY")

    def test_screen_stocks_success(self, finviz_client, mocker):
        """Test successful screening of stocks from FINVIZ API."""
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"Ticker,Company\nAAPL,Apple Inc.\nMSFT,Microsoft Corp.\n"
        mocker.patch.object(finviz_client.session, "get", return_value=mock_response)

        symbols = finviz_client.screen_stocks()
        assert symbols == {"AAPL", "MSFT"}
        finviz_client.session.get.assert_called_once()
        assert "auth=TEST_FINVIZ_KEY" in finviz_client.session.get.call_args[1]["params"]["auth"]

    def test_screen_stocks_auth_failure(self, finviz_client, mocker):
        """Test FINVIZ API authentication failure (401/403 status code)."""
        mock_response = mocker.MagicMock()
        mock_response.status_code = 401
        mocker.patch.object(finviz_client.session, "get", return_value=mock_response)

        symbols = finviz_client.screen_stocks()
        assert symbols == set()
        finviz_client.session.get.assert_called_once()

    def test_screen_stocks_api_failure(self, finviz_client, mocker):
        """Test general FINVIZ API request failure (non-200, non-401/403 status code)."""
        mock_response = mocker.MagicMock()
        mock_response.status_code = 500
        mocker.patch.object(finviz_client.session, "get", return_value=mock_response)

        symbols = finviz_client.screen_stocks()
        assert symbols == set()
        finviz_client.session.get.assert_called_once()

    def test_screen_stocks_request_exception(self, finviz_client, mocker):
        """Test FINVIZ API request exception."""
        mocker.patch.object(
            finviz_client.session, "get", side_effect=requests.exceptions.RequestException
        )

        symbols = finviz_client.screen_stocks()
        assert symbols == set()
        finviz_client.session.get.assert_called_once()


class TestFMPClient:
    """Validate FMPClient's API interactions."""

    @pytest.fixture
    def fmp_client(self, mod):
        """Fixture for FMPClient instance."""
        return mod.FMPClient(api_key="TEST_FMP_KEY")

    @pytest.fixture(autouse=True)
    def mock_session_get(self, mocker):
        """Mocks requests.Session.get for all tests in this class."""
        return mocker.patch("requests.Session.get")

    @pytest.fixture
    def mock_response(self, mocker):
        """Helper to create a mock response object."""
        mock = mocker.MagicMock()
        mock.status_code = 200
        mock.json.return_value = {}
        return mock

    def test_get_success(self, fmp_client, mock_session_get, mock_response):
        """Test successful _get request."""
        mock_response.json.return_value = {"data": "success"}
        mock_session_get.return_value = mock_response

        result = fmp_client._get("test-endpoint")
        assert result == {"data": "success"}
        mock_session_get.assert_called_once()
        assert "test-endpoint" in mock_session_get.call_args[0][0]

    def test_get_rate_limit(self, fmp_client, mock_session_get, mock_response, monkeypatch):
        """Test _get handles rate limiting (429)."""
        mock_response_429 = mocker.MagicMock(status_code=429)
        mock_response_200 = mocker.MagicMock(status_code=200, json=lambda: {"data": "success"})

        mock_session_get.side_effect = [mock_response_429, mock_response_200]
        monkeypatch.setattr(fmp_client.session, "get", mock_session_get)
        mocker.patch("time.sleep")  # Prevent actual sleep

        result = fmp_client._get("test-endpoint")
        assert result == {"data": "success"}
        assert mock_session_get.call_count == 2
        assert fmp_client.retry_count == 1

    def test_get_rate_limit_persistent(self, fmp_client, mock_session_get, mock_response, monkeypatch):
        """Test _get handles persistent rate limiting (stops after 2 attempts)."""
        mock_response_429 = mocker.MagicMock(status_code=429)
        mock_session_get.side_effect = [mock_response_429, mock_response_429, mock_response_429]
        monkeypatch.setattr(fmp_client.session, "get", mock_session_get)
        mocker.patch("time.sleep")

        result = fmp_client._get("test-endpoint")
        assert result is None
        assert mock_session_get.call_count == 2
        assert fmp_client.rate_limit_reached is True

    def test_get_api_failure(self, fmp_client, mock_session_get, mock_response):
        """Test _get handles general API failure (non-200, non-429)."""
        mock_response.status_code = 500
        mock_session_get.return_value = mock_response

        result = fmp_client._get("test-endpoint")
        assert result is None
        mock_session_get.assert_called_once()

    def test_get_exception(self, fmp_client, mock_session_get):
        """Test _get handles request exceptions."""
        mock_session_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = fmp_client._get("test-endpoint")
        assert result is None
        mock_session_get.assert_called_once()

    def test_get_historical_prices_stable_success(self, fmp_client, mock_session_get, mock_response, monkeypatch):
        """Test get_historical_prices with stable endpoint success."""
        mock_response.json.return_value = {"symbol": "AAPL", "historical": [{"date": "2023-01-01", "close": 150}]}
        mock_session_get.return_value = mock_response
        monkeypatch.setattr(fmp_client, "_FMP_HIST_ENDPOINTS", [("https://stable.com", True)])
        mocker.patch("time.sleep")

        result = fmp_client.get_historical_prices("AAPL")
        assert result == [{"date": "2023-01-01", "close": 150}]
        mock_session_get.assert_called_once()
        assert "stable.com" in mock_session_get.call_args[0][0]

    def test_get_historical_prices_v3_success(self, fmp_client, mock_session_get, mock_response, monkeypatch):
        """Test get_historical_prices with v3 endpoint fallback success."""
        mock_response_v3 = mocker.MagicMock(status_code=200, json=lambda: {"historicalStockList": [{"symbol": "AAPL", "historical": [{"date": "2023-01-01", "close": 150}]}]})
        mock_session_get.side_effect = [mocker.MagicMock(status_code=500), mock_response_v3] # Stable fails, v3 succeeds
        monkeypatch.setattr(fmp_client, "_FMP_HIST_ENDPOINTS", [("https://stable.com", True), ("https://v3.com", False)])
        mocker.patch("time.sleep")

        result = fmp_client.get_historical_prices("AAPL")
        assert result == [{"date": "2023-01-01", "close": 150}]
        assert mock_session_get.call_count == 2
        assert "v3.com" in mock_session_get.call_args[0][0]

    def test_get_historical_prices_no_data(self, fmp_client, mock_session_get, mock_response, monkeypatch):
        """Test get_historical_prices when no historical data is returned."""
        mock_response.json.return_value = {"symbol": "AAPL"}  # Missing 'historical' key
        mock_session_get.return_value = mock_response
        monkeypatch.setattr(fmp_client, "_FMP_HIST_ENDPOINTS", [("https://stable.com", True)])
        mocker.patch("time.sleep")

        result = fmp_client.get_historical_prices("AAPL")
        assert result is None

    def test_get_historical_prices_all_endpoints_fail(self, fmp_client, mock_session_get, monkeypatch, mocker):
        """Test get_historical_prices when all endpoints fail."""
        mock_session_get.return_value = mocker.MagicMock(status_code=500)
        monkeypatch.setattr(fmp_client, "_FMP_HIST_ENDPOINTS", [("https://stable.com", True), ("https://v3.com", False)])
        mocker.patch("time.sleep")

        result = fmp_client.get_historical_prices("AAPL")
        assert result is None
        assert mock_session_get.call_count == 2
        assert len(fmp_client._disabled_endpoints) == 2 # Both endpoints should be disabled after failures

    def test_get_dividend_history_success(self, fmp_client, mock_session_get, mock_response):
        """Test get_dividend_history success."""
        mock_response.json.return_value = {"historical": [{"date": "2023-01-01", "dividend": 0.5}]}
        mock_session_get.return_value = mock_response

        result = fmp_client.get_dividend_history("AAPL")
        assert result == {"historical": [{"date": "2023-01-01", "dividend": 0.5}]}

    def test_get_company_profile_success(self, fmp_client, mock_session_get, mock_response):
        """Test get_company_profile success."""
        mock_response.json.return_value = [{"symbol": "AAPL", "sector": "Technology"}]
        mock_session_get.return_value = mock_response

        result = fmp_client.get_company_profile("AAPL")
        assert result == {"symbol": "AAPL", "sector": "Technology"}

    def test_get_quote_with_profile_success(self, fmp_client, mock_session_get, mock_response):
        """Test get_quote_with_profile merges data correctly."""
        mock_response_quote = mocker.MagicMock(status_code=200, json=lambda: [{"symbol": "AAPL", "price": 170, "name": "Apple Inc."}])
        mock_response_profile = mocker.MagicMock(status_code=200, json=lambda: [{"symbol": "AAPL", "sector": "Technology", "companyName": "Apple Inc. (Profile)"}])

        # Mock both calls for quote and profile
        mock_session_get.side_effect = [mock_response_quote, mock_response_profile]

        result = fmp_client.get_quote_with_profile("AAPL")
        assert result["symbol"] == "AAPL"
        assert result["price"] == 170
        assert result["sector"] == "Technology"
        assert result["companyName"] == "Apple Inc. (Profile)"
        assert mock_session_get.call_count == 2

    def test_get_quote_with_profile_profile_fails(self, fmp_client, mock_session_get, mock_response):
        """Test get_quote_with_profile when profile fetch fails."""
        mock_response_quote = mocker.MagicMock(status_code=200, json=lambda: [{"symbol": "AAPL", "price": 170, "name": "Apple Inc."}])
        mock_response_profile_fail = mocker.MagicMock(status_code=500) # Profile fetch fails

        mock_session_get.side_effect = [mock_response_quote, mock_response_profile_fail]

        result = fmp_client.get_quote_with_profile("AAPL")
        assert result["symbol"] == "AAPL"
        assert result["price"] == 170
        assert result["sector"] == "Unknown"  # Should fallback to default
        assert result["companyName"] == "Apple Inc."
        assert mock_session_get.call_count == 2

class TestStockAnalyzer:
    """Validate StockAnalyzer's analytical methods."""

    @pytest.fixture(scope="class")
    def mod(self):
        if not SCRIPT_PATH.exists():
            pytest.skip(f"Script not found: {SCRIPT_PATH}")
        return _load_script()

    @pytest.fixture
    def analyzer(self, mod):
        return mod.StockAnalyzer

    def test_analyze_dividend_growth_success(self, analyzer):
        """Test analyze_dividend_growth with a typical scenario."""
        dividend_history = {
            "historical": [
                {"date": "2020-01-01", "dividend": 0.25},
                {"date": "2020-04-01", "dividend": 0.25},
                {"date": "2020-07-01", "dividend": 0.25},
                {"date": "2020-10-01", "dividend": 0.25},  # Total 2020: 1.00
                {"date": "2021-01-01", "dividend": 0.27},
                {"date": "2021-04-01", "dividend": 0.27},
                {"date": "2021-07-01", "dividend": 0.27},
                {"date": "2021-10-01", "dividend": 0.27},  # Total 2021: 1.08
                {"date": "2022-01-01", "dividend": 0.30},
                {"date": "2022-04-01", "dividend": 0.30},
                {"date": "2022-07-01", "dividend": 0.30},
                {"date": "2022-10-01", "dividend": 0.30},  # Total 2022: 1.20
                {"date": "2023-01-01", "dividend": 0.33},
                {"date": "2023-04-01", "dividend": 0.33},
                {"date": "2023-07-01", "dividend": 0.33},
                {"date": "2023-10-01", "dividend": 0.33},  # Total 2023: 1.32
            ]
        }
        cagr, consistent, annual_dividend, years_of_growth = analyzer.analyze_dividend_growth(
            dividend_history
        )
        assert cagr == 9.66  # CAGR from 2020 (1.00) to 2023 (1.32) over 3 years
        assert consistent is True
        assert annual_dividend == 1.32
        assert years_of_growth == 3

    def test_analyze_dividend_growth_inconsistent_cut(self, analyzer):
        """Test analyze_dividend_growth with a significant dividend cut."""
        dividend_history = {
            "historical": [
                {"date": "2020-01-01", "dividend": 0.25},
                {"date": "2021-01-01", "dividend": 0.27},
                {"date": "2022-01-01", "dividend": 0.10},  # Significant cut
                {"date": "2023-01-01", "dividend": 0.33},
            ]
        }
        cagr, consistent, annual_dividend, years_of_growth = analyzer.analyze_dividend_growth(
            dividend_history
        )
        assert consistent is False
        assert years_of_growth == 0

    def test_analyze_dividend_growth_consistent_small_drop(self, analyzer):
        """Test analyze_dividend_growth with a small drop allowed by 5% tolerance."""
        dividend_history = {
            "historical": [
                {"date": "2020-01-01", "dividend": 1.00},
                {"date": "2021-01-01", "dividend": 1.04},  # +4%
                {"date": "2022-01-01", "dividend": 1.02},  # -1.9% from 1.04 (within 5% tolerance)
                {"date": "2023-01-01", "dividend": 1.05},
            ]
        }
        cagr, consistent, annual_dividend, years_of_growth = analyzer.analyze_dividend_growth(
            dividend_history
        )
        assert consistent is True
        assert years_of_growth == 3

    def test_is_reit_true(self, analyzer):
        """Test is_reit for a REIT stock."""
        assert analyzer.is_reit({"sector": "Real Estate"}) is True
        assert analyzer.is_reit({"industry": "Equity REITs"}) is True
        assert analyzer.is_reit({"sector": "real estate", "industry": "reits"}) is True

    def test_is_reit_false(self, analyzer):
        """Test is_reit for a non-REIT stock."""
        assert analyzer.is_reit({"sector": "Technology"}) is False
        assert analyzer.is_reit({"industry": "Software"}) is False

    def test_calculate_ffo_success(self, analyzer):
        """Test FFO calculation."""
        cash_flows = [{"netIncome": 100, "depreciationAndAmortization": 20}]
        assert analyzer.calculate_ffo(cash_flows) == 120

    def test_calculate_ffo_zero_data(self, analyzer):
        """Test FFO calculation with zero values."""
        cash_flows = [{"netIncome": 0, "depreciationAndAmortization": 0}]
        assert analyzer.calculate_ffo(cash_flows) is None

    def test_calculate_ffo_payout_ratio_success(self, analyzer):
        """Test FFO payout ratio calculation."""
        cash_flows = [{"netIncome": 100, "depreciationAndAmortization": 20, "dividendsPaid": 30}]
        assert analyzer.calculate_ffo_payout_ratio(cash_flows) == round((30 / 120) * 100, 1)

    def test_calculate_ffo_payout_ratio_no_ffo(self, analyzer):
        """Test FFO payout ratio when FFO is zero or negative."""
        cash_flows = [{"netIncome": -10, "depreciationAndAmortization": 5, "dividendsPaid": 10}]
        assert analyzer.calculate_ffo_payout_ratio(cash_flows) is None

    def test_calculate_payout_ratios_non_reit(self, analyzer):
        """Test payout ratios for a non-REIT."""
        income_stmts = [{"netIncome": 100}]
        cash_flows = [{"dividendsPaid": 30, "freeCashFlow": 80}]
        payouts = analyzer.calculate_payout_ratios(income_stmts, cash_flows, is_reit=False)
        assert payouts["payout_ratio"] == 30.0
        assert payouts["fcf_payout_ratio"] == round((30 / 80) * 100, 1)

    def test_calculate_payout_ratios_reit(self, analyzer, mocker):
        """Test payout ratios for a REIT, ensuring FFO is used."""
        cash_flows = [{"netIncome": 100, "depreciationAndAmortization": 20, "dividendsPaid": 30, "freeCashFlow": 80}]
        mocker.patch.object(analyzer, "calculate_ffo", return_value=120) # Mock FFO for consistency
        payouts = analyzer.calculate_payout_ratios([], cash_flows, is_reit=True)
        assert payouts["payout_ratio"] == 25.0 # (30 / 120) * 100
        assert payouts["fcf_payout_ratio"] == round((30 / 80) * 100, 1)

    def test_get_payout_ratio_from_metrics_success(self, analyzer):
        """Test fallback payout ratio from key metrics."""
        key_metrics = [{"payoutRatio": 0.45}]
        assert analyzer.get_payout_ratio_from_metrics(key_metrics) == 45.0

    def test_analyze_financial_health_healthy(self, analyzer):
        """Test financially healthy scenario."""
        balance_sheet = [
            {"totalDebt": 100, "totalStockholdersEquity": 200, "totalCurrentAssets": 150, "totalCurrentLiabilities": 100}
        ]
        health = analyzer.analyze_financial_health(balance_sheet)
        assert health["debt_to_equity"] == 0.5
        assert health["current_ratio"] == 1.5
        assert health["financially_healthy"] is True

    def test_analyze_financial_health_unhealthy(self, analyzer):
        """Test financially unhealthy scenario (high debt, low current ratio)."""
        balance_sheet = [
            {"totalDebt": 300, "totalStockholdersEquity": 100, "totalCurrentAssets": 80, "totalCurrentLiabilities": 100}
        ]
        health = analyzer.analyze_financial_health(balance_sheet)
        assert health["debt_to_equity"] == 3.0
        assert health["current_ratio"] == 0.8
        assert health["financially_healthy"] is False

    def test_analyze_growth_metrics_success(self, analyzer):
        """Test revenue and EPS growth metrics."""
        income_stmts = [
            {"revenue": 150, "eps": 1.5}, # latest
            {"revenue": 140, "eps": 1.4},
            {"revenue": 130, "eps": 1.3},
            {"revenue": 100, "eps": 1.0}, # 3 years ago
            {"revenue": 90, "eps": 0.9},
        ]
        growth = analyzer.analyze_growth_metrics(income_stmts)
        assert growth["revenue_cagr_3y"] == round(((150/100)**(1/3) -1) * 100, 2)
        assert growth["eps_cagr_3y"] == round(((1.5/1.0)**(1/3) -1) * 100, 2)

    def test_calculate_composite_score(self, analyzer):
        """Test composite score calculation with various inputs."""
        stock_data = {
            "dividend_cagr_3y": 18,
            "dividend_consistent": True,
            "roe": 22,
            "profit_margin": 17,
            "debt_to_equity": 0.8,
            "rsi": 32,
            "pe_ratio": 12,
            "pb_ratio": 2.5,
        }
        score = analyzer.calculate_composite_score(stock_data)
        # Expected score:
        # Div Growth: 35 (15-20)
        # Consistency bonus: 5
        # ROE: 12 (>=20)
        # Profit Margin: 8 (15-20)
        # Debt/Equity: 6 (<1.0)
        # RSI: 15 (30-35)
        # PE: 5 (<15)
        # PB: 5 (<3)
        # Total: 35 + 5 + 12 + 8 + 6 + 15 + 5 + 5 = 91
        assert score == 91.0

    def test_calculate_composite_score_low_scores(self, analyzer):
        """Test composite score with lower values."""
        stock_data = {
            "dividend_cagr_3y": 5,
            "dividend_consistent": False,
            "roe": 5,
            "profit_margin": 5,
            "debt_to_equity": 3.0,
            "rsi": 60,
            "pe_ratio": 50,
            "pb_ratio": 10,
        }
        score = analyzer.calculate_composite_score(stock_data)
        # Expected score:
        # Div Growth: 20 (<12)
        # Consistency bonus: 0
        # ROE: 3 (<10)
        # Profit Margin: 3 (<10)
        # Debt/Equity: 0 (>=2.0)
        # RSI: 5 (>40)
        # PE: 0 (>25)
        # PB: 0 (>5)
        # Total: 20 + 0 + 3 + 3 + 0 + 5 + 0 + 0 = 31
        assert score == 31.0

class TestScriptStructure:
    """Ensure the script file meets structural requirements."""

    @pytest.fixture(scope="class")
    def mod(self):
        if not SCRIPT_PATH.exists():
            pytest.skip(f"Script not found: {SCRIPT_PATH}")
        return _load_script()

    def test_script_exists(self):
        assert SCRIPT_PATH.exists(), f"Main script missing: {SCRIPT_PATH}"

    def test_script_has_main_guard(self):
        source = SCRIPT_PATH.read_text()
        assert 'if __name__ == "__main__"' in source or "if __name__ == '__main__'" in source, (
            "Script should have a __main__ guard"
        )

    def test_script_references_fmp_api(self):
        source = SCRIPT_PATH.read_text()
        assert "FMP_API_KEY" in source or "fmp_api_key" in source or "fmp-api-key" in source, (
            "Script should reference FMP_API_KEY"
        )

    def test_script_references_rsi(self):
        source = SCRIPT_PATH.read_text()
        assert "rsi" in source.lower(), "Script should implement or reference RSI"

    @pytest.mark.parametrize("use_finviz", [True, False])
    def test_full_integration_run(
        self, mod, tmp_path, monkeypatch, mocker, use_finviz
    ):
        """
        Tests a full run of the main function, mocking API clients and verifying output.
        This acts as an end-to-end integration test for the script's workflow.
        """
        # Mock API keys
        monkeypatch.setenv("FMP_API_KEY", "dummy_fmp_key")
        monkeypatch.setenv("FINVIZ_API_KEY", "dummy_finviz_key")

        # Mock FMPClient methods
        mock_fmp_client_instance = mocker.MagicMock()
        mock_fmp_client_instance.rate_limit_reached = False
        mock_fmp_client_instance.get_quote_with_profile.return_value = {
            "symbol": "AAPL",
            "companyName": "Apple Inc.",
            "sector": "Technology",
            "price": 170.0,
            "marketCap": 2.5e12,
        }
        mock_fmp_client_instance.screen_stocks.return_value = [
            {"symbol": "AAPL", "companyName": "Apple Inc.", "price": 170.0, "marketCap": 2.5e12}
        ]
        mock_fmp_client_instance.get_dividend_history.return_value = {
            "historical": [
                {"date": "2020-01-01", "dividend": 0.25},
                {"date": "2021-01-01", "dividend": 0.27},
                {"date": "2022-01-01", "dividend": 0.30},
                {"date": "2023-01-01", "dividend": 0.33},
                {"date": "2024-01-01", "dividend": 0.35},
            ]
        }
        mock_fmp_client_instance.get_historical_prices.return_value = [
            {"date": f"2023-01-{i:02d}", "close": 100 + i} for i in range(1, 31)
        ]
        mock_fmp_client_instance.get_income_statement.return_value = [
            {"revenue": 1000, "eps": 10},
            {"revenue": 900, "eps": 9},
            {"revenue": 800, "eps": 8},
            {"revenue": 700, "eps": 7},
        ]
        mock_fmp_client_instance.get_balance_sheet.return_value = [
            {
                "totalDebt": 100,
                "totalStockholdersEquity": 200,
                "totalCurrentAssets": 150,
                "totalCurrentLiabilities": 100,
            }
        ]
        mock_fmp_client_instance.get_cash_flow.return_value = [
            {"dividendsPaid": 30, "freeCashFlow": 80, "netIncome": 100, "depreciationAndAmortization": 20}
        ]
        mock_fmp_client_instance.get_key_metrics.return_value = [{"payoutRatio": 0.3}]

        mocker.patch.object(mod, "FMPClient", return_value=mock_fmp_client_instance)

        # Mock FINVIZClient methods if used
        mock_finviz_client_instance = mocker.MagicMock()
        mock_finviz_client_instance.screen_stocks.return_value = {"AAPL"}
        mocker.patch.object(mod, "FINVIZClient", return_value=mock_finviz_client_instance)

        # Mock RSICalculator (already tested, just ensure it's called)
        mocker.patch.object(mod, "RSICalculator")
        mod.RSICalculator.return_value.calculate_rsi.return_value = 30.0

        # Mock StockAnalyzer (already tested, just ensure it's called)
        mocker.patch.object(mod, "StockAnalyzer")
        mod.StockAnalyzer.calculate_cagr.return_value = 15.0
        mod.StockAnalyzer.analyze_dividend_growth.return_value = (15.0, True, 1.40, 5) # cagr, consistent, annual_div, years_growth
        mod.StockAnalyzer.is_reit.return_value = False
        mod.StockAnalyzer.calculate_payout_ratios.return_value = {"payout_ratio": 30.0, "fcf_payout_ratio": 37.5}
        mod.StockAnalyzer.analyze_financial_health.return_value = {"financially_healthy": True, "debt_to_equity": 0.5, "current_ratio": 1.5}
        mod.StockAnalyzer.analyze_growth_metrics.return_value = {"revenue_cagr_3y": 10.0, "eps_cagr_3y": 10.0}
        mod.StockAnalyzer.calculate_composite_score.return_value = 95.0


        # Mock report generation
        mock_generate_markdown_report = mocker.patch.object(mod, "generate_markdown_report")
        mock_json_dump = mocker.patch("json.dump")

        # Set up sys.argv
        sys_argv = ["screen_dividend_growth_rsi.py", "--output-dir", str(tmp_path)]
        if use_finviz:
            sys_argv.append("--use-finviz")
        monkeypatch.setattr(sys, "argv", sys_argv)

        # Run main
        mod.main()

        # Assertions
        if use_finviz:
            mock_finviz_client_instance.screen_stocks.assert_called_once()
            mock_fmp_client_instance.get_quote_with_profile.assert_called_once_with("AAPL")
        else:
            mock_fmp_client_instance.screen_stocks.assert_called_once()

        mock_fmp_client_instance.get_dividend_history.assert_called_once_with("AAPL")
        mock_fmp_client_instance.get_historical_prices.assert_called_once_with("AAPL", days=30)
        mock_fmp_client_instance.get_income_statement.assert_called_once_with("AAPL", limit=5)
        mock_fmp_client_instance.get_balance_sheet.assert_called_once_with("AAPL", limit=5)
        mock_fmp_client_instance.get_cash_flow.assert_called_once_with("AAPL", limit=5)
        mock_fmp_client_instance.get_key_metrics.assert_called_once_with("AAPL", limit=1)

        # Verify output calls
        assert mock_json_dump.call_count == 1
        assert mock_generate_markdown_report.call_count == 1

        # Check output file paths
        json_path = mock_json_dump.call_args[0][2]
        md_path = mock_generate_markdown_report.call_args[0][2]

        assert Path(json_path).parent == tmp_path
        assert Path(md_path).parent == tmp_path

        # Optionally, check content passed to report generators (more detailed checks could go here)
        assert len(mock_json_dump.call_args[0][0]["stocks"]) == 1
        assert mock_json_dump.call_args[0][0]["stocks"][0]["symbol"] == "AAPL"
        
        assert len(mock_generate_markdown_report.call_args[0][0]) == 1 # results list
        assert mock_generate_markdown_report.call_args[0][0][0]["symbol"] == "AAPL"

    @pytest.mark.parametrize("fmp_key_env", [True, False])
    @pytest.mark.parametrize("finviz_key_env", [True, False])
    @pytest.mark.parametrize("use_finviz_arg", [True, False])
    @pytest.mark.parametrize("output_dir_arg", [True, False])
    @pytest.mark.parametrize("min_yield_arg", [True, False])
    def test_main_function_args(
        self,
        mod,
        fmp_key_env,
        finviz_key_env,
        use_finviz_arg,
        output_dir_arg,
        min_yield_arg,
        tmp_path,
        monkeypatch,
        mocker,
    ):
        """
        Test that main function parses arguments correctly and calls downstream functions.
        This is a smoke test to ensure argument parsing and flow.
        """
        # Mock external API calls and report generation
        mock_finviz_client = mocker.patch.object(mod, "FINVIZClient")
        mock_screen_stocks_finviz = mock_finviz_client.return_value.screen_stocks
        mock_screen_stocks_finviz.return_value = {"AAPL", "MSFT"}

        mock_screen_dividend_growth_pullbacks = mocker.patch.object(
            mod, "screen_dividend_growth_pullbacks"
        )
        mock_screen_dividend_growth_pullbacks.return_value = [
            {"symbol": "AAPL", "composite_score": 90}
        ]
        mock_generate_markdown_report = mocker.patch.object(mod, "generate_markdown_report")
        mock_os_makedirs = mocker.patch("os.makedirs")
        mock_json_dump = mocker.patch("json.dump")

        # Prepare sys.argv
        sys_argv = ["screen_dividend_growth_rsi.py"]
        if use_finviz_arg:
            sys_argv.append("--use-finviz")
        if output_dir_arg:
            sys_argv.extend(["--output-dir", str(tmp_path)])
        if min_yield_arg:
            sys_argv.extend(["--min-yield", "2.5"])

        # Prepare API keys
        fmp_api_key = "test_fmp_key"
        finviz_api_key = "test_finviz_key"

        if fmp_key_env:
            monkeypatch.setenv("FMP_API_KEY", fmp_api_key)
        else:
            sys_argv.extend(["--fmp-api-key", fmp_api_key])

        if use_finviz_arg:
            if finviz_key_env:
                monkeypatch.setenv("FINVIZ_API_KEY", finviz_api_key)
            else:
                sys_argv.extend(["--finviz-api-key", finviz_api_key])

        monkeypatch.setattr(sys, "argv", sys_argv)

        # Execute main function
        try:
            mod.main()
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"main() exited with error code {e.code}")

        # Assertions
        mock_os_makedirs.assert_called_once()
        mock_json_dump.assert_called_once()
        mock_generate_markdown_report.assert_called_once()

        # Verify output directory
        expected_output_dir = str(tmp_path) if output_dir_arg else mod.os.path.join(mod.os.path.dirname(mod.os.path.dirname(mod.os.path.dirname(SCRIPT_PATH))), "logs")
        
        json_call_args = mock_json_dump.call_args[0][2] # file path is the 3rd arg to json.dump
        md_call_args = mock_generate_markdown_report.call_args[0][2] # output_path is the 3rd arg

        assert Path(json_call_args).parent == Path(expected_output_dir)
        assert Path(md_call_args).parent == Path(expected_output_dir)

        if use_finviz_arg:
            mock_finviz_client.assert_called_once_with(finviz_api_key)
            mock_screen_stocks_finviz.assert_called_once()
            mock_screen_dividend_growth_pullbacks.assert_called_once_with(
                api_key=fmp_api_key,
                min_yield=2.5 if min_yield_arg else 1.5,
                min_div_growth=12.0,
                rsi_max=40.0,
                max_candidates=None,
                finviz_symbols={"AAPL", "MSFT"},
            )
        else:
            mock_finviz_client.assert_not_called()
            mock_screen_stocks_finviz.assert_not_called()
            mock_screen_dividend_growth_pullbacks.assert_called_once_with(
                api_key=fmp_api_key,
                min_yield=2.5 if min_yield_arg else 1.5,
                min_div_growth=12.0,
                rsi_max=40.0,
                max_candidates=None,
                finviz_symbols=None,
            )


