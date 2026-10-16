import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests
from screen_dividend_stocks import FINVIZClient, FMPClient, RSICalculator, StockAnalyzer


def test_rsi_calculator():
    prices = [10.0 + i * 0.5 for i in range(20)]  # ascending prices
    rsi = RSICalculator.calculate_rsi(prices, period=14)
    assert rsi is not None
    assert rsi > 90.0

    prices_flat = [10.0] * 20
    rsi_flat = RSICalculator.calculate_rsi(prices_flat, period=14)
    assert rsi_flat is not None
    assert rsi_flat == 100.0


def test_is_reit():
    assert StockAnalyzer.is_reit({"sector": "Real Estate"}) is True
    assert StockAnalyzer.is_reit({"industry": "REIT - Residential"}) is True
    assert StockAnalyzer.is_reit({"sector": "Technology", "industry": "Software"}) is False


def test_calculate_ffo():
    cash_flows = [
        {"netIncome": 100, "depreciationAndAmortization": 50},
        {"netIncome": 80, "depreciationAndAmortization": 40},
    ]
    ffo = StockAnalyzer.calculate_ffo(cash_flows)
    assert ffo == 150

    assert StockAnalyzer.calculate_ffo([]) is None


def test_calculate_ffo_payout_ratio():
    cash_flows = [
        {"netIncome": 100, "depreciationAndAmortization": 50, "dividendsPaid": -90},
    ]
    ratio = StockAnalyzer.calculate_ffo_payout_ratio(cash_flows)
    assert ratio == 60.0


def test_calculate_cagr():
    cagr = StockAnalyzer.calculate_cagr(100.0, 133.1, 3)
    assert pytest.approx(cagr, 1e-4) == 10.0

    assert StockAnalyzer.calculate_cagr(100, 0, 3) is None


def test_check_positive_trend():
    assert StockAnalyzer.check_positive_trend([10, 12, 11, 15]) is True
    assert StockAnalyzer.check_positive_trend([10, 9, 8, 12]) is False
    assert StockAnalyzer.check_positive_trend([10, 15]) is False


def test_analyze_dividend_growth():
    div_hist = {
        "historical": [
            {"date": "2022-01-01", "dividend": 1.0},
            {"date": "2023-01-01", "dividend": 1.1},
            {"date": "2024-01-01", "dividend": 1.21},
            {"date": "2025-01-01", "dividend": 1.331},
        ]
    }
    cagr, consistent, latest = StockAnalyzer.analyze_dividend_growth(div_hist)
    assert pytest.approx(cagr, 1e-4) == 10.0
    assert consistent is True
    assert latest == 1.331


def test_analyze_revenue_growth():
    income_stmts = [{"revenue": 133.1}, {"revenue": 121.0}, {"revenue": 110.0}, {"revenue": 100.0}]
    trend, cagr = StockAnalyzer.analyze_revenue_growth(income_stmts)
    assert trend is True
    assert pytest.approx(cagr, 1e-4) == 10.0


def test_analyze_revenue_trend():
    # Positive trend
    income_stmts = [{"revenue": 150}, {"revenue": 140}, {"revenue": 130}, {"revenue": 100}]
    res = StockAnalyzer.analyze_revenue_trend(income_stmts)
    assert res["is_uptrend"] is True
    assert res["years_of_growth"] == 3
    assert pytest.approx(res["cagr"], 1e-4) == 14.47  # CAGR from 100 to 150 over 3 years

    # Negative trend
    income_stmts_neg = [{"revenue": 100}, {"revenue": 130}, {"revenue": 140}, {"revenue": 150}]
    res_neg = StockAnalyzer.analyze_revenue_trend(income_stmts_neg)
    assert res_neg["is_uptrend"] is False

    # Insufficient data
    res_insufficient = StockAnalyzer.analyze_revenue_trend([{"revenue": 100}])
    assert res_insufficient["is_uptrend"] is False
    assert res_insufficient["years_of_growth"] == 0
    assert res_insufficient["cagr"] is None


def test_analyze_earnings_trend():
    # Positive trend
    income_stmts = [{"netIncome": 150}, {"netIncome": 140}, {"netIncome": 130}, {"netIncome": 100}]
    res = StockAnalyzer.analyze_earnings_trend(income_stmts)
    assert res["is_uptrend"] is True
    assert res["years_of_growth"] == 3
    assert pytest.approx(res["cagr"], 1e-4) == 14.47

    # Negative trend (with positive earnings)
    income_stmts_neg = [
        {"netIncome": 100},
        {"netIncome": 130},
        {"netIncome": 140},
        {"netIncome": 150},
    ]
    res_neg = StockAnalyzer.analyze_earnings_trend(income_stmts_neg)
    assert res_neg["is_uptrend"] is False

    # Negative earnings
    income_stmts_neg_earning = [
        {"netIncome": 100},
        {"netIncome": -10},
        {"netIncome": 140},
        {"netIncome": 150},
    ]
    res_neg_earning = StockAnalyzer.analyze_earnings_trend(income_stmts_neg_earning)
    assert res_neg_earning["is_uptrend"] is False
    assert res_neg_earning["years_of_growth"] == 0
    assert res_neg_earning["cagr"] is None


def test_analyze_dividend_sustainability_reit():
    cash_flows = [
        {
            "netIncome": 100,
            "depreciationAndAmortization": 50,
            "dividendsPaid": -90,
            "operatingCashFlow": 120,
            "capitalExpenditure": -20,
        }
    ]
    res = StockAnalyzer.analyze_dividend_sustainability(
        income_statements=[], cash_flows=cash_flows, is_reit=True
    )
    assert res["sustainable"] is True
    assert res["payout_ratio"] == 60.0
    assert res["fcf_payout_ratio"] == 90.0


def test_analyze_dividend_sustainability_non_reit():
    income_statements = [{"netIncome": 100}]
    cash_flows = [{"dividendsPaid": -70, "operatingCashFlow": 120, "capitalExpenditure": -20}]
    res = StockAnalyzer.analyze_dividend_sustainability(
        income_statements=income_statements, cash_flows=cash_flows, is_reit=False
    )
    assert res["sustainable"] is True
    assert res["payout_ratio"] == 70.0
    assert res["fcf_payout_ratio"] == 70.0


def test_analyze_financial_health():
    balance_sheets = [
        {
            "totalDebt": 50,
            "totalStockholdersEquity": 100,
            "totalCurrentAssets": 150,
            "totalCurrentLiabilities": 100,
        }
    ]
    res = StockAnalyzer.analyze_financial_health(balance_sheets)
    assert res["healthy"] is True
    assert res["debt_to_equity"] == 0.5
    assert res["current_ratio"] == 1.5


def test_calculate_stability_score():
    stability = {"is_stable": True, "is_growing": True, "years_of_growth": 3}
    score = StockAnalyzer.calculate_stability_score(stability)
    assert score == 100.0


def test_calculate_quality_score():
    key_metrics = [{"roe": 0.20}]
    income_statements = [{"revenue": 1000, "netIncome": 150}]
    res = StockAnalyzer.calculate_quality_score(key_metrics, income_statements)
    assert res["quality_score"] == 100.0
    assert res["roe"] == 0.20
    assert res["profit_margin"] == 15.0


class TestFINVIZClient(unittest.TestCase):
    @patch("requests.Session")
    def test_screen_stocks_success(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = (
            b"Ticker,Company,Sector\nAAPL,Apple Inc,Technology\nMSFT,Microsoft Corp,Technology"
        )
        mock_session.return_value.get.return_value = mock_response

        client = FINVIZClient(api_key="test_key")
        symbols = client.screen_stocks()
        self.assertEqual(symbols, {"AAPL", "MSFT"})
        mock_session.return_value.get.assert_called_once()

    @patch("requests.Session")
    def test_screen_stocks_auth_failure(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.return_value.get.return_value = mock_response

        client = FINVIZClient(api_key="test_key")
        symbols = client.screen_stocks()
        self.assertEqual(symbols, set())
        mock_session.return_value.get.assert_called_once()

    @patch("requests.Session")
    def test_screen_stocks_http_error(self, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_session.return_value.get.return_value = mock_response

        client = FINVIZClient(api_key="test_key")
        symbols = client.screen_stocks()
        self.assertEqual(symbols, set())
        mock_session.return_value.get.assert_called_once()

    @patch("requests.Session")
    def test_screen_stocks_request_exception(self, mock_session):
        mock_session.return_value.get.side_effect = requests.exceptions.RequestException(
            "Test Exception"
        )

        client = FINVIZClient(api_key="test_key")
        symbols = client.screen_stocks()
        self.assertEqual(symbols, set())
        mock_session.return_value.get.assert_called_once()


class TestFMPClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_fmp_key"
        self.client = FMPClient(api_key=self.api_key)

    @patch("requests.Session")
    @patch("time.sleep", return_value=None)  # Mock time.sleep to speed up tests
    def test_get_success(self, mock_sleep, mock_session):
        self.client.session = mock_session.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_session.return_value.get.return_value = mock_response

        data = self.client._get("test-endpoint")
        self.assertEqual(data, {"test": "data"})
        mock_session.return_value.get.assert_called_once_with(
            f"{self.client.BASE_URL}/test-endpoint", params={}, timeout=30
        )

    @patch("requests.Session")
    @patch("time.sleep", return_value=None)
    def test_get_rate_limit_retry_success(self, mock_sleep, mock_session):
        self.client.session = mock_session.return_value
        # First call is 429, second call is 200
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"test": "data_retried"}

        mock_session.return_value.get.side_effect = [mock_response_429, mock_response_200]

        data = self.client._get("test-endpoint")
        self.assertEqual(data, {"test": "data_retried"})
        self.assertEqual(mock_session.return_value.get.call_count, 2)
        self.assertFalse(self.client.rate_limit_reached)

    @patch("requests.Session")
    @patch("time.sleep", return_value=None)
    def test_get_rate_limit_stops(self, mock_sleep, mock_session):
        self.client.session = mock_session.return_value
        # Two 429 responses, should set rate_limit_reached to True
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_session.return_value.get.side_effect = [mock_response_429, mock_response_429]

        data = self.client._get("test-endpoint")
        self.assertIsNone(data)
        self.assertTrue(self.client.rate_limit_reached)
        self.assertEqual(mock_session.return_value.get.call_count, 2)

    @patch("requests.Session")
    @patch("time.sleep", return_value=None)
    def test_get_http_error(self, mock_sleep, mock_session):
        self.client.session = mock_session.return_value
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_session.return_value.get.return_value = mock_response

        data = self.client._get("test-endpoint")
        self.assertIsNone(data)
        mock_session.return_value.get.assert_called_once()

    @patch("requests.Session")
    @patch("time.sleep", return_value=None)
    def test_get_request_exception(self, mock_sleep, mock_session):
        self.client.session = mock_session.return_value
        mock_session.return_value.get.side_effect = requests.exceptions.RequestException(
            "Test Exception"
        )

        data = self.client._get("test-endpoint")
        self.assertIsNone(data)
        mock_session.return_value.get.assert_called_once()

    @patch.object(FMPClient, "_get")
    def test_screen_stocks(self, mock_get):
        mock_get.return_value = [{"symbol": "TEST"}]
        stocks = self.client.screen_stocks(dividend_yield_min=3.0, pe_max=20, pb_max=2)
        self.assertEqual(stocks, [{"symbol": "TEST"}])
        mock_get.assert_called_once_with(
            "stock-screener",
            {
                "dividendYieldMoreThan": 3.0,
                "priceEarningRatioLowerThan": 20,
                "priceToBookRatioLowerThan": 2,
                "marketCapMoreThan": 2000000000,
                "exchange": "NASDAQ,NYSE",
                "limit": 1000,
            },
        )

    @patch.object(FMPClient, "_get")
    def test_get_income_statement(self, mock_get):
        mock_get.return_value = [{"date": "2023"}]
        income_statements = self.client.get_income_statement("AAPL")
        self.assertEqual(income_statements, [{"date": "2023"}])
        mock_get.assert_called_once_with("income-statement/AAPL", {"limit": 5})

    @patch.object(FMPClient, "_get")
    def test_get_company_profile(self, mock_get):
        mock_get.return_value = [{"companyName": "Apple Inc"}]
        profile = self.client.get_company_profile("AAPL")
        self.assertEqual(profile, {"companyName": "Apple Inc"})
        mock_get.assert_called_once_with("profile/AAPL")

    @patch("requests.Session")
    @patch("time.sleep", return_value=None)
    def test_get_historical_prices(self, mock_sleep, mock_session):
        self.client.session = mock_session.return_value
        # Mock for stable endpoint success
        mock_response_stable = MagicMock()
        mock_response_stable.status_code = 200
        mock_response_stable.json.return_value = {
            "historical": [{"date": "2023-01-01", "close": 150}]
        }

        # Mock for v3 fallback endpoint success
        mock_response_v3 = MagicMock()
        mock_response_v3.status_code = 200
        mock_response_v3.json.return_value = {
            "historicalStockList": [
                {"symbol": "AAPL", "historical": [{"date": "2023-01-01", "close": 150}]}
            ]
        }

        # Test stable endpoint first
        mock_session.return_value.get.side_effect = [mock_response_stable]
        prices = self.client.get_historical_prices("AAPL")
        self.assertEqual(prices, [{"date": "2023-01-01", "close": 150}])
        self.assertEqual(mock_session.return_value.get.call_count, 1)

        # Reset mocks for fallback test
        mock_session.return_value.get.reset_mock()
        self.client._endpoint_failures = {}  # Reset internal state
        self.client._disabled_endpoints = set()

        # Test fallback to v3
        mock_response_stable_fail = MagicMock()
        mock_response_stable_fail.status_code = 404
        mock_session.return_value.get.side_effect = [mock_response_stable_fail, mock_response_v3]

        prices_fallback = self.client.get_historical_prices("AAPL")
        self.assertEqual(prices_fallback, [{"date": "2023-01-01", "close": 150}])
        self.assertEqual(mock_session.return_value.get.call_count, 2)


@patch("time.sleep", return_value=None)  # Mocks all time.sleep calls
class TestScreenValueDividendStocks(unittest.TestCase):
    def setUp(self):
        self.fmp_api_key = "test_fmp_key"

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_screen_two_stage_success(self, MockFINVIZClient, MockFMPClient, mock_sleep):
        # Setup FINVIZ mock
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"AAPL", "MSFT"}

        # Setup FMP mock
        mock_fmp_instance = MockFMPClient.return_value

        income_statements = [
            {"date": "2023", "revenue": 400_000_000_000, "netIncome": 100_000_000_000, "eps": 6.0},
            {"date": "2022", "revenue": 380_000_000_000, "netIncome": 95_000_000_000, "eps": 5.5},
            {"date": "2021", "revenue": 360_000_000_000, "netIncome": 90_000_000_000, "eps": 5.0},
            {"date": "2020", "revenue": 340_000_000_000, "netIncome": 85_000_000_000, "eps": 4.5},
        ]
        balance_sheet = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -15_000_000_000,
                "netIncome": 100_000_000_000,
            },
        ]
        key_metrics = [{"roe": 0.20}]

        dividend_history_aapl = {
            "historical": [
                {"date": "2023-01-01", "dividend": 1.1},
                {"date": "2023-04-01", "dividend": 1.1},
                {"date": "2023-07-01", "dividend": 1.1},
                {"date": "2023-10-01", "dividend": 1.1},
                {"date": "2022-01-01", "dividend": 1.0},
                {"date": "2022-04-01", "dividend": 1.0},
                {"date": "2022-07-01", "dividend": 1.0},
                {"date": "2022-10-01", "dividend": 1.0},
                {"date": "2021-01-01", "dividend": 0.9},
                {"date": "2021-04-01", "dividend": 0.9},
                {"date": "2021-07-01", "dividend": 0.9},
                {"date": "2021-10-01", "dividend": 0.9},
                {"date": "2020-01-01", "dividend": 0.8},
                {"date": "2020-04-01", "dividend": 0.8},
                {"date": "2020-07-01", "dividend": 0.8},
                {"date": "2020-10-01", "dividend": 0.8},
            ]
        }
        dividend_history_msft = {
            "historical": [
                {"date": "2023-01-01", "dividend": 1.5},
                {"date": "2023-04-01", "dividend": 1.5},
                {"date": "2023-07-01", "dividend": 1.5},
                {"date": "2023-10-01", "dividend": 1.5},
                {"date": "2022-01-01", "dividend": 1.4},
                {"date": "2022-04-01", "dividend": 1.4},
                {"date": "2022-07-01", "dividend": 1.4},
                {"date": "2022-10-01", "dividend": 1.4},
                {"date": "2021-01-01", "dividend": 1.3},
                {"date": "2021-04-01", "dividend": 1.3},
                {"date": "2021-07-01", "dividend": 1.3},
                {"date": "2021-10-01", "dividend": 1.3},
                {"date": "2020-01-01", "dividend": 1.2},
                {"date": "2020-04-01", "dividend": 1.2},
                {"date": "2020-07-01", "dividend": 1.2},
                {"date": "2020-10-01", "dividend": 1.2},
            ]
        }
        prices_hist = [{"close": 100 + i} for i in range(30)]

        mock_fmp_instance._get.side_effect = [
            [{"symbol": "AAPL", "name": "Apple Inc", "price": 140.0, "marketCap": 2_500_000_000_000, "pe": 20, "priceToBook": 2}],
            [{"symbol": "MSFT", "name": "Microsoft Corp", "price": 200.0, "marketCap": 2_000_000_000_000, "pe": 20, "priceToBook": 2}],
        ]
        mock_fmp_instance.get_company_profile.side_effect = [
            {"companyName": "Apple Inc", "sector": "Technology", "industry": "Consumer Electronics"},
            {"companyName": "Microsoft Corp", "sector": "Technology", "industry": "Software"},
        ]
        mock_fmp_instance.get_income_statement.return_value = income_statements
        mock_fmp_instance.get_balance_sheet.return_value = balance_sheet
        mock_fmp_instance.get_cash_flow.return_value = cash_flow
        mock_fmp_instance.get_key_metrics.return_value = key_metrics
        mock_fmp_instance.get_dividend_history.side_effect = [dividend_history_aapl, dividend_history_msft]
        mock_fmp_instance.get_historical_prices.return_value = prices_hist

        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(
            self.fmp_api_key, top_n=2, finviz_symbols={"AAPL", "MSFT"}
        )

        self.assertEqual(len(results), 2)
        aapl_result = next(item for item in results if item["symbol"] == "AAPL")
        self.assertIsNotNone(aapl_result)
        self.assertAlmostEqual(aapl_result["dividend_yield"], (4.4 / 140.0) * 100, places=2)
        self.assertGreaterEqual(aapl_result["dividend_yield"], 3.0)
        self.assertTrue(aapl_result["revenue_uptrend"])
        self.assertTrue(aapl_result["earnings_uptrend"])
        self.assertTrue(aapl_result["dividend_sustainable"])
        self.assertTrue(aapl_result["financially_healthy"])
        self.assertGreater(aapl_result["composite_score"], 0)

        msft_result = next(item for item in results if item["symbol"] == "MSFT")
        self.assertIsNotNone(msft_result)
        self.assertAlmostEqual(msft_result["dividend_yield"], (6.0 / 200.0) * 100, places=2)
        self.assertGreaterEqual(msft_result["dividend_yield"], 3.0)
        self.assertTrue(msft_result["revenue_uptrend"])
        self.assertTrue(msft_result["earnings_uptrend"])
        self.assertTrue(msft_result["dividend_sustainable"])
        self.assertTrue(msft_result["financially_healthy"])
        self.assertGreater(msft_result["composite_score"], 0)

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_screen_dividend_yield_filter(self, MockFINVIZClient, MockFMPClient, mock_sleep):
        # Setup FINVIZ mock to return one symbol
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"AAPL"}

        # Define mock data for a stock that fails dividend yield
        income_statements_aapl = [
            {"date": "2023", "revenue": 400_000_000_000, "netIncome": 100_000_000_000, "eps": 6.0},
            {"date": "2022", "revenue": 380_000_000_000, "netIncome": 95_000_000_000, "eps": 5.5},
            {"date": "2021", "revenue": 360_000_000_000, "netIncome": 90_000_000_000, "eps": 5.0},
            {"date": "2020", "revenue": 340_000_000_000, "netIncome": 85_000_000_000, "eps": 4.5},
        ]
        balance_sheet_aapl = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow_aapl = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -10_000_000_000,
                "netIncome": 100_000_000_000,
            },  # Lower dividendsPaid
        ]
        key_metrics_aapl = [
            {"roe": 0.20},
        ]
        # Annual dividend for AAPL for 2023 would be 1.0 (assuming this is annual, not quarterly)
        # Price is 140. Yield = (1.0/140)*100 = 0.71% (should fail 3.0% minimum)
        dividend_history_aapl = {
            "historical": [
                {"date": "2023-01-01", "dividend": 1.05},
                {"date": "2022-01-01", "dividend": 1.0},
                {"date": "2021-01-01", "dividend": 0.95},
                {"date": "2020-01-01", "dividend": 0.90},
            ]
        }
        historical_prices_aapl = [{"close": 100 + i} for i in range(30)]  # For RSI

        mock_fmp_instance = MockFMPClient.return_value
        mock_fmp_instance._get.side_effect = [
            # For AAPL quote and profile
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": 140.0,
                    "marketCap": 2_500_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {
                    "companyName": "Apple Inc",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                }
            ],  # Profile
            # FMP detailed data for AAPL
            income_statements_aapl,
            balance_sheet_aapl,
            cash_flow_aapl,
            key_metrics_aapl,
            dividend_history_aapl,
            historical_prices_aapl,
        ]

        # --- Test execution ---
        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(self.fmp_api_key, top_n=1, finviz_symbols={"AAPL"})

        # --- Assertions ---
        self.assertEqual(len(results), 0)  # Should be filtered out

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_screen_fmp_rate_limit_during_detailed_analysis(
        self, MockFINVIZClient, MockFMPClient, mock_sleep
    ):
        # Setup FINVIZ mock to return two symbols
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"AAPL", "MSFT"}

        income_statements_aapl = [
            {"date": "2023", "revenue": 400_000_000_000, "netIncome": 100_000_000_000, "eps": 6.0},
            {"date": "2022", "revenue": 380_000_000_000, "netIncome": 95_000_000_000, "eps": 5.5},
            {"date": "2021", "revenue": 360_000_000_000, "netIncome": 90_000_000_000, "eps": 5.0},
            {"date": "2020", "revenue": 340_000_000_000, "netIncome": 85_000_000_000, "eps": 4.5},
        ]
        balance_sheet_aapl = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow_aapl = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -15_000_000_000,
                "netIncome": 100_000_000_000,
            },
        ]
        key_metrics_aapl = [
            {"roe": 0.20},
        ]
        dividend_history_aapl = {
            "historical": [
                {"date": "2023-01-01", "dividend": 1.1},
                {"date": "2023-04-01", "dividend": 1.1},
                {"date": "2023-07-01", "dividend": 1.1},
                {"date": "2023-10-01", "dividend": 1.1},
                {"date": "2022-01-01", "dividend": 1.0},
                {"date": "2022-04-01", "dividend": 1.0},
                {"date": "2022-07-01", "dividend": 1.0},
                {"date": "2022-10-01", "dividend": 1.0},
                {"date": "2021-01-01", "dividend": 0.9},
                {"date": "2021-04-01", "dividend": 0.9},
                {"date": "2021-07-01", "dividend": 0.9},
                {"date": "2021-10-01", "dividend": 0.9},
                {"date": "2020-01-01", "dividend": 0.8},
                {"date": "2020-04-01", "dividend": 0.8},
                {"date": "2020-07-01", "dividend": 0.8},
                {"date": "2020-10-01", "dividend": 0.8},
            ]
        }
        historical_prices_aapl = [
            {"close": 100 + i} for i in range(30)
        ]  # For RSI (low RSI for AAPL)

        mock_fmp_instance = MockFMPClient.return_value
        mock_fmp_instance._get.side_effect = [
            # For AAPL quote and profile
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": 140.0,
                    "marketCap": 2_500_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {
                    "companyName": "Apple Inc",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                }
            ],  # Profile
            # FMP detailed data for AAPL
            income_statements_aapl,
            balance_sheet_aapl,
            cash_flow_aapl,
            key_metrics_aapl,
            dividend_history_aapl,
            historical_prices_aapl,  # RSI for AAPL will be calculated here
            # For MSFT quote, and then rate limit hit
            [
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corp",
                    "price": 200.0,
                    "marketCap": 2_000_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {"companyName": "Microsoft Corp", "sector": "Technology", "industry": "Software"}
            ],  # Profile
            # Simulate rate limit hit during MSFT income statement fetch
            None,  # get_income_statement will return None due to rate_limit_reached flag
        ]

        # Manually set rate_limit_reached to True after MSFT quote/profile fetch
        def fmp_client_get_side_effect(*args, **kwargs):
            # After fetching MSFT profile, set rate_limit_reached to True for subsequent calls
            if args[0] == "profile/MSFT":
                mock_fmp_instance.rate_limit_reached = True
            return (
                MagicMock(status_code=200, json=lambda: args[0]).json()
                if "income-statement" not in args[0]
                else None
            )

        # Reset side_effect for _get to inject rate_limit_reached logic
        mock_fmp_instance._get.side_effect = [
            # For AAPL quote and profile
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": 140.0,
                    "marketCap": 2_500_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {
                    "companyName": "Apple Inc",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                }
            ],  # Profile
            # FMP detailed data for AAPL
            income_statements_aapl,
            balance_sheet_aapl,
            cash_flow_aapl,
            key_metrics_aapl,
            dividend_history_aapl,
            historical_prices_aapl,
            # For MSFT quote and profile
            [
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corp",
                    "price": 200.0,
                    "marketCap": 2_000_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {"companyName": "Microsoft Corp", "sector": "Technology", "industry": "Software"}
            ],  # Profile
            # Simulate rate limit hit for MSFT's income statement.
            # The get_income_statement will check rate_limit_reached internally and return [].
            # So, we don't need to return None directly from _get.
            # Instead, the mock_fmp_instance.rate_limit_reached will be set to True after profile call.
            # For the income statement call, we can return empty list or None.
            # Since the actual screen_value_dividend_stocks checks for client.rate_limit_reached,
            # we need to ensure that the flag is set after the MSFT profile is fetched.
            # So, we'll manually set it for the next call.
        ]

        # Use a mock for FMPClient.get_income_statement directly to simulate rate limit
        # After successful profile fetch for MSFT, subsequent calls should trigger rate limit.
        def mock_get_income_statement(symbol, limit):
            if symbol == "MSFT":
                mock_fmp_instance.rate_limit_reached = True  # Simulate rate limit being hit
                return []  # Return empty list, signaling failure for this stock
            return income_statements_aapl  # For AAPL

        mock_fmp_instance.get_income_statement.side_effect = mock_get_income_statement
        mock_fmp_instance.get_balance_sheet.return_value = balance_sheet_aapl
        mock_fmp_instance.get_cash_flow.return_value = cash_flow_aapl
        mock_fmp_instance.get_key_metrics.return_value = key_metrics_aapl
        mock_fmp_instance.get_dividend_history.return_value = dividend_history_aapl
        mock_fmp_instance.get_historical_prices.return_value = historical_prices_aapl
        mock_fmp_instance.get_company_profile.return_value = {
            "companyName": "Apple Inc",
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }
        mock_fmp_instance._get.side_effect = [
            # For AAPL quote and profile
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": 140.0,
                    "marketCap": 2_500_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {
                    "companyName": "Apple Inc",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                }
            ],  # Profile
            # For MSFT quote and profile
            [
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corp",
                    "price": 200.0,
                    "marketCap": 2_000_000_000_000,
                    "pe": 20,
                    "priceToBook": 2,
                }
            ],  # Quote
            [
                {"companyName": "Microsoft Corp", "sector": "Technology", "industry": "Software"}
            ],  # Profile
        ]

        # --- Test execution ---
        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(
            self.fmp_api_key, top_n=2, finviz_symbols={"AAPL", "MSFT"}
        )

        # --- Assertions ---
        self.assertEqual(len(results), 1)  # Only AAPL should be in results
        self.assertEqual(results[0]["symbol"], "AAPL")
        self.assertTrue(mock_fmp_instance.rate_limit_reached)  # Ensure rate limit flag was set

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_rsi_oversold_prioritization(self, MockFINVIZClient, MockFMPClient, mock_sleep):
        # Setup FINVIZ mock to return two symbols
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"AAPL", "MSFT"}

        income_statements_template = [
            {"date": "2023", "revenue": 400_000_000_000, "netIncome": 100_000_000_000, "eps": 6.0},
            {"date": "2022", "revenue": 380_000_000_000, "netIncome": 95_000_000_000, "eps": 5.5},
            {"date": "2021", "revenue": 360_000_000_000, "netIncome": 90_000_000_000, "eps": 5.0},
            {"date": "2020", "revenue": 340_000_000_000, "netIncome": 85_000_000_000, "eps": 4.5},
        ]
        balance_sheet_template = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow_template = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -15_000_000_000,
                "netIncome": 100_000_000_000,
            },
        ]
        key_metrics_template = [
            {"roe": 0.20},
        ]
        dividend_history_template = {
            "historical": [  # Yield > 3% with price 100
                {"date": "2023-01-01", "dividend": 0.8},
                {"date": "2023-04-01", "dividend": 0.8},
                {"date": "2023-07-01", "dividend": 0.8},
                {
                    "date": "2023-10-01",
                    "dividend": 0.8,
                },  # Total 3.2 annual. If price 100, yield 3.2%
                {"date": "2022-01-01", "dividend": 0.75},
                {"date": "2022-04-01", "dividend": 0.75},
                {"date": "2022-07-01", "dividend": 0.75},
                {"date": "2022-10-01", "dividend": 0.75},
                {"date": "2021-01-01", "dividend": 0.7},
                {"date": "2021-04-01", "dividend": 0.7},
                {"date": "2021-07-01", "dividend": 0.7},
                {"date": "2021-10-01", "dividend": 0.7},
                {"date": "2020-01-01", "dividend": 0.65},
                {"date": "2020-04-01", "dividend": 0.65},
                {"date": "2020-07-01", "dividend": 0.65},
                {"date": "2020-10-01", "dividend": 0.65},
            ]
        }
        # Prices for RSI calculation (historical prices are newest first in FMP)
        p_oversold = [100.0 - i * 1.5 for i in range(30)]  # price drops, RSI < 40
        p_normal = [100.0 + i * 1.5 for i in range(30)]    # price rises, RSI > 40
        prices_oversold = list(reversed(p_oversold))
        prices_normal = list(reversed(p_normal))

        mock_fmp_instance = MockFMPClient.return_value
        mock_fmp_instance._get.side_effect = [
            # AAPL quote
            [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "price": 100.0,
                    "marketCap": 2_500_000_000_000,
                    "pe": 15,
                    "priceToBook": 1.5,
                }
            ],
            # MSFT quote
            [
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corp",
                    "price": 100.0,
                    "marketCap": 2_000_000_000_000,
                    "pe": 18,
                    "priceToBook": 1.8,
                }
            ],
        ]
        mock_fmp_instance.get_company_profile.side_effect = [
            {"companyName": "Apple Inc", "sector": "Technology", "industry": "Consumer Electronics"},
            {"companyName": "Microsoft Corp", "sector": "Technology", "industry": "Software"},
        ]

        mock_fmp_instance.get_income_statement.return_value = income_statements_template
        mock_fmp_instance.get_balance_sheet.return_value = balance_sheet_template
        mock_fmp_instance.get_cash_flow.return_value = cash_flow_template
        mock_fmp_instance.get_key_metrics.return_value = key_metrics_template
        mock_fmp_instance.get_dividend_history.return_value = dividend_history_template

        mock_fmp_instance.get_historical_prices.side_effect = [
            [{"close": p} for p in prices_oversold],  # For AAPL (RSI < 40)
            [{"close": p} for p in prices_normal],  # For MSFT (RSI > 40)
        ]

        # --- Test execution ---
        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(
            self.fmp_api_key, top_n=1, finviz_symbols={"AAPL", "MSFT"}
        )

        # --- Assertions ---
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["symbol"], "AAPL")  # AAPL should be chosen due to RSI < 40
        self.assertLessEqual(results[0]["rsi"], 40)  # Ensure RSI is indeed low

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_rsi_no_oversold_returns_lowest_rsi(self, MockFINVIZClient, MockFMPClient, mock_sleep):
        # Setup FINVIZ mock to return two symbols
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"GOOG", "AMZN"}

        income_statements_template = [
            {"date": "2023", "revenue": 400_000_000_000, "netIncome": 100_000_000_000, "eps": 6.0},
            {"date": "2022", "revenue": 380_000_000_000, "netIncome": 95_000_000_000, "eps": 5.5},
            {"date": "2021", "revenue": 360_000_000_000, "netIncome": 90_000_000_000, "eps": 5.0},
            {"date": "2020", "revenue": 340_000_000_000, "netIncome": 85_000_000_000, "eps": 4.5},
        ]
        balance_sheet_template = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow_template = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -15_000_000_000,
                "netIncome": 100_000_000_000,
            },
        ]
        key_metrics_template = [
            {"roe": 0.20},
        ]
        dividend_history_template = {
            "historical": [  # Yield > 3% with price 100
                {"date": "2023-01-01", "dividend": 0.8},
                {"date": "2023-04-01", "dividend": 0.8},
                {"date": "2023-07-01", "dividend": 0.8},
                {
                    "date": "2023-10-01",
                    "dividend": 0.8,
                },  # Total 3.2 annual. If price 100, yield 3.2%
                {"date": "2022-01-01", "dividend": 0.75},
                {"date": "2022-04-01", "dividend": 0.75},
                {"date": "2022-07-01", "dividend": 0.75},
                {"date": "2022-10-01", "dividend": 0.75},
                {"date": "2021-01-01", "dividend": 0.7},
                {"date": "2021-04-01", "dividend": 0.7},
                {"date": "2021-07-01", "dividend": 0.7},
                {"date": "2021-10-01", "dividend": 0.7},
                {"date": "2020-01-01", "dividend": 0.65},
                {"date": "2020-04-01", "dividend": 0.65},
                {"date": "2020-07-01", "dividend": 0.65},
                {"date": "2020-10-01", "dividend": 0.65},
            ]
        }

        # Prices for RSI calculation (both > 40, but GOOG lower; historical prices are newest first in FMP)
        p_goog = [100.0]
        for i in range(29):
            p_goog.append(p_goog[-1] + (0.5 if i % 2 == 0 else -0.4))
        p_amzn = [100.0]
        for i in range(29):
            p_amzn.append(p_amzn[-1] + (2.0 if i % 4 != 0 else -0.5))
        prices_goog = list(reversed(p_goog))
        prices_amzn = list(reversed(p_amzn))

        mock_fmp_instance = MockFMPClient.return_value
        mock_fmp_instance._get.side_effect = [
            # GOOG quote
            [
                {
                    "symbol": "GOOG",
                    "name": "Alphabet Inc",
                    "price": 100.0,
                    "marketCap": 1_500_000_000_000,
                    "pe": 25,
                    "priceToBook": 5,
                }
            ],
            # AMZN quote
            [
                {
                    "symbol": "AMZN",
                    "name": "Amazon.com Inc",
                    "price": 100.0,
                    "marketCap": 1_000_000_000_000,
                    "pe": 30,
                    "priceToBook": 6,
                }
            ],
        ]
        mock_fmp_instance.get_company_profile.side_effect = [
            {
                "companyName": "Alphabet Inc",
                "sector": "Technology",
                "industry": "Internet Content & Information",
            },
            {
                "companyName": "Amazon.com Inc",
                "sector": "Technology",
                "industry": "Internet Retail",
            },
        ]

        mock_fmp_instance.get_income_statement.return_value = income_statements_template
        mock_fmp_instance.get_balance_sheet.return_value = balance_sheet_template
        mock_fmp_instance.get_cash_flow.return_value = cash_flow_template
        mock_fmp_instance.get_key_metrics.return_value = key_metrics_template
        mock_fmp_instance.get_dividend_history.return_value = dividend_history_template

        mock_fmp_instance.get_historical_prices.side_effect = [
            [{"close": p} for p in prices_goog],  # For GOOG
            [{"close": p} for p in prices_amzn],  # For AMZN
        ]

        # --- Test execution ---
        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(
            self.fmp_api_key, top_n=1, finviz_symbols={"GOOG", "AMZN"}
        )

        # --- Assertions ---
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["symbol"], "GOOG"
        )  # GOOG should be chosen due to lower RSI (even if both > 40)
        self.assertGreater(
            results[0]["rsi"], 40
        )  # Ensure RSI is indeed high, but lowest of the two

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_insufficient_income_statement_data_filter(
        self, MockFINVIZClient, MockFMPClient, mock_sleep
    ):
        # Setup FINVIZ mock to return one symbol
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"NO_DATA_STOCK"}

        # Define mock data for a stock with insufficient income statement data
        income_statements_insufficient = [
            {"date": "2023", "revenue": 100},
            {"date": "2022", "revenue": 90},
            {"date": "2021", "revenue": 80},  # Only 3 years, should be filtered
        ]
        balance_sheet_template = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow_template = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -15_000_000_000,
                "netIncome": 100_000_000_000,
            },
        ]
        key_metrics_template = [
            {"roe": 0.20},
        ]
        dividend_history_template = {
            "historical": [
                {"date": "2023-01-01", "dividend": 0.8},
                {"date": "2023-04-01", "dividend": 0.8},
                {"date": "2023-07-01", "dividend": 0.8},
                {
                    "date": "2023-10-01",
                    "dividend": 0.8,
                },  # Total 3.2 annual. If price 100, yield 3.2%
                {"date": "2022-01-01", "dividend": 0.75},
                {"date": "2022-04-01", "dividend": 0.75},
                {"date": "2022-07-01", "dividend": 0.75},
                {"date": "2022-10-01", "dividend": 0.75},
                {"date": "2021-01-01", "dividend": 0.7},
                {"date": "2021-04-01", "dividend": 0.7},
                {"date": "2021-07-01", "dividend": 0.7},
                {"date": "2021-10-01", "dividend": 0.7},
            ]
        }
        historical_prices_template = [{"close": 100 + i} for i in range(30)]

        mock_fmp_instance = MockFMPClient.return_value
        mock_fmp_instance._get.side_effect = [
            [
                {
                    "symbol": "NO_DATA_STOCK",
                    "name": "No Data Inc",
                    "price": 100.0,
                    "marketCap": 1_000_000_000_000,
                    "pe": 15,
                    "priceToBook": 1.5,
                }
            ],
            [{"companyName": "No Data Inc", "sector": "Other", "industry": "Misc"}],
        ]
        mock_fmp_instance.get_income_statement.return_value = income_statements_insufficient
        mock_fmp_instance.get_balance_sheet.return_value = balance_sheet_template
        mock_fmp_instance.get_cash_flow.return_value = cash_flow_template
        mock_fmp_instance.get_key_metrics.return_value = key_metrics_template
        mock_fmp_instance.get_dividend_history.return_value = dividend_history_template
        mock_fmp_instance.get_historical_prices.return_value = historical_prices_template

        # --- Test execution ---
        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(
            self.fmp_api_key, top_n=1, finviz_symbols={"NO_DATA_STOCK"}
        )

        # --- Assertions ---
        self.assertEqual(
            len(results), 0
        )  # Should be filtered out due to insufficient income statement data

    @patch("screen_dividend_stocks.FMPClient")
    @patch("screen_dividend_stocks.FINVIZClient")
    def test_insufficient_rsi_data_filter(self, MockFINVIZClient, MockFMPClient, mock_sleep):
        # Setup FINVIZ mock to return one symbol
        mock_finviz_instance = MockFINVIZClient.return_value
        mock_finviz_instance.screen_stocks.return_value = {"NO_RSI_DATA_STOCK"}

        # Define mock data for a stock with sufficient income statement data but insufficient historical prices
        income_statements_sufficient = [
            {"date": "2023", "revenue": 100},
            {"date": "2022", "revenue": 90},
            {"date": "2021", "revenue": 80},
            {"date": "2020", "revenue": 70},
        ]
        balance_sheet_template = [
            {
                "totalDebt": 100_000_000_000,
                "totalStockholdersEquity": 500_000_000_000,
                "totalCurrentAssets": 200_000_000_000,
                "totalCurrentLiabilities": 100_000_000_000,
            },
        ]
        cash_flow_template = [
            {
                "operatingCashFlow": 120_000_000_000,
                "capitalExpenditure": -20_000_000_000,
                "dividendsPaid": -15_000_000_000,
                "netIncome": 100_000_000_000,
            },
        ]
        key_metrics_template = [
            {"roe": 0.20},
        ]
        dividend_history_template = {
            "historical": [  # Yield > 3% with price 100
                {"date": "2023-01-01", "dividend": 0.8},
                {"date": "2023-04-01", "dividend": 0.8},
                {"date": "2023-07-01", "dividend": 0.8},
                {
                    "date": "2023-10-01",
                    "dividend": 0.8,
                },  # Total 3.2 annual. If price 100, yield 3.2%
                {"date": "2022-01-01", "dividend": 0.75},
                {"date": "2022-04-01", "dividend": 0.75},
                {"date": "2022-07-01", "dividend": 0.75},
                {"date": "2022-10-01", "dividend": 0.75},
                {"date": "2021-01-01", "dividend": 0.7},
                {"date": "2021-04-01", "dividend": 0.7},
                {"date": "2021-07-01", "dividend": 0.7},
                {"date": "2021-10-01", "dividend": 0.7},
                {"date": "2020-01-01", "dividend": 0.65},
                {"date": "2020-04-01", "dividend": 0.65},
                {"date": "2020-07-01", "dividend": 0.65},
                {"date": "2020-10-01", "dividend": 0.65},
            ]
        }
        # Only 19 days of historical prices, insufficient for RSI (needs 20+)
        historical_prices_insufficient = [{"close": 100 + i} for i in range(19)]

        mock_fmp_instance = MockFMPClient.return_value
        mock_fmp_instance._get.side_effect = [
            [
                {
                    "symbol": "NO_RSI_DATA_STOCK",
                    "name": "No RSI Data Inc",
                    "price": 100.0,
                    "marketCap": 1_000_000_000_000,
                    "pe": 15,
                    "priceToBook": 1.5,
                }
            ],
            [{"companyName": "No RSI Data Inc", "sector": "Other", "industry": "Misc"}],
        ]
        mock_fmp_instance.get_income_statement.return_value = income_statements_sufficient
        mock_fmp_instance.get_balance_sheet.return_value = balance_sheet_template
        mock_fmp_instance.get_cash_flow.return_value = cash_flow_template
        mock_fmp_instance.get_key_metrics.return_value = key_metrics_template
        mock_fmp_instance.get_dividend_history.return_value = dividend_history_template
        mock_fmp_instance.get_historical_prices.return_value = historical_prices_insufficient

        # --- Test execution ---
        from screen_dividend_stocks import screen_value_dividend_stocks

        results = screen_value_dividend_stocks(
            self.fmp_api_key, top_n=1, finviz_symbols={"NO_RSI_DATA_STOCK"}
        )

        # --- Assertions ---
        self.assertEqual(len(results), 0)  # Should be filtered out due to insufficient RSI data
