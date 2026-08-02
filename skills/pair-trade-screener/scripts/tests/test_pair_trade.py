from unittest.mock import MagicMock, patch

import analyze_spread
import find_pairs
import numpy as np
import pandas as pd
import pytest


def test_calculate_correlation():
    dates = pd.date_range(start="2025-01-01", periods=100)
    series_a = pd.Series(np.linspace(10, 20, 100) + np.random.normal(0, 0.1, 100), index=dates)
    series_b = pd.Series(np.linspace(20, 40, 100) + np.random.normal(0, 0.1, 100), index=dates)

    corr = find_pairs.calculate_correlation(series_a, series_b)
    assert corr is not None
    assert corr > 0.90

    # Low correlation
    series_c = pd.Series(np.random.normal(0, 1, 100), index=dates)
    corr_low = find_pairs.calculate_correlation(series_a, series_c)
    assert corr_low is not None
    assert abs(corr_low) < 0.3


def test_calculate_beta():
    dates = pd.date_range(start="2025-01-01", periods=100)
    series_b = pd.Series(np.linspace(10, 20, 100), index=dates)
    series_a = pd.Series(2 * series_b + 5, index=dates)

    res = find_pairs.calculate_beta(series_a, series_b)
    assert pytest.approx(res["beta"], 1e-5) == 2.0
    assert pytest.approx(res["intercept"], 1e-5) == 5.0
    assert pytest.approx(res["r_squared"], 1e-5) == 1.0


def test_test_cointegration():
    dates = pd.date_range(start="2025-01-01", periods=200)
    np.random.seed(42)
    spread = pd.Series(np.random.normal(0, 1, 200), index=dates)
    prices_b = pd.Series(np.cumsum(np.random.normal(0, 1, 200)) + 50, index=dates)
    prices_a = prices_b + spread

    res = find_pairs.test_cointegration(prices_a, prices_b, 1.0)
    assert res is not None
    assert res["is_cointegrated"] == True
    assert res["p_value"] < 0.05

    res2 = analyze_spread.test_cointegration(spread)
    assert res2 is not None
    assert res2["is_cointegrated"] == True


def test_calculate_half_life():
    dates = pd.date_range(start="2025-01-01", periods=200)
    np.random.seed(42)
    spread_vals = [0.0]
    for i in range(1, 200):
        spread_vals.append(0.5 * spread_vals[-1] + np.random.normal(0, 0.1))
    spread = pd.Series(spread_vals, index=dates)

    hl = find_pairs.calculate_half_life(spread)
    assert hl is not None
    assert pytest.approx(hl, abs=0.5) == 1.0


def test_calculate_current_zscore():
    dates = pd.date_range(start="2025-01-01", periods=100)
    spread = pd.Series(np.zeros(100), index=dates)
    spread.iloc[-90:] = np.random.normal(0, 1, 90)
    spread.iloc[-90:] = (spread.iloc[-90:] - spread.iloc[-90:].mean()) / spread.iloc[-90:].std()
    spread.iloc[-1] = 2.0

    z = find_pairs.calculate_current_zscore(spread, window=90)
    assert pytest.approx(z, abs=0.2) == 2.0


def test_generate_ascii_chart():
    dates = pd.date_range(start="2025-01-01", periods=100)
    zscore = pd.Series(np.sin(np.linspace(0, 10, 100)) * 2, index=dates)
    chart = analyze_spread.generate_ascii_chart(zscore)
    assert "Z-Score History" in chart
    assert "Time" in chart


@patch("requests.get")
def test_fetch_sector_stocks(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "symbol": "AAPL",
            "companyName": "Apple",
            "marketCap": 3000000000000,
            "sector": "Technology",
            "isActivelyTrading": True,
        },
        {
            "symbol": "MSFT",
            "companyName": "Microsoft",
            "marketCap": 3000000000000,
            "sector": "Technology",
            "isActivelyTrading": True,
        },
    ]
    mock_get.return_value = mock_resp

    stocks = find_pairs.fetch_sector_stocks("Technology", "dummy_key")
    assert len(stocks) == 2
    assert stocks[0]["symbol"] == "AAPL"


@patch("requests.get")
def test_fetch_historical_prices(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "symbol": "AAPL",
        "historical": [
            {"date": "2025-01-01", "adjClose": 150.0},
            {"date": "2025-01-02", "adjClose": 151.0},
            {"date": "2025-01-03", "adjClose": 152.0},
        ],
    }
    mock_get.return_value = mock_resp

    prices = find_pairs.fetch_historical_prices("AAPL", "dummy_key")
    assert prices is not None
    assert len(prices) == 3
    # The prices will be reversed (chronological order)
    # The inputs were index 0 (2025-01-01: 150) -> index 2 (2025-01-03: 152).
    # Reversing changes the order so latest (index 0) becomes first, which is 152.0.
    assert prices.iloc[0] == 152.0
    assert prices.index[0] == pd.to_datetime("2025-01-03")
