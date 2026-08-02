import pytest

from scripts.lib import tv_client


def test_row_to_stock_maps_us_ticker_and_usd_liquidity():
    row = {
        "ticker": "NASDAQ:AAPL",
        "name": "Apple Inc.",
        "close": 100,
        "volume": 1_000,
        "average_volume_10d_calc": 2_000,
        "market_cap_basic": 3_000_000_000,
        "RSI": 55,
    }

    stock = tv_client._row_to_stock(row, "US")

    assert stock["symbol"] == "AAPL"
    assert stock["board"] == "NASDAQ"
    assert stock["avg_turnover"] == 200_000
    assert stock["liquidity_score"] == 4.0


def test_tv_market_helpers_reject_unknown_market():
    with pytest.raises(ValueError, match="market must be TH or US"):
        tv_client.get_tv_stocks("JP")

    with pytest.raises(ValueError, match="market must be TH or US"):
        tv_client.get_tv_breadth("JP")


def test_tv_breadth_uses_us_universe_for_lowercase_market(monkeypatch):
    stocks = [
        {
            "price": 10,
            "sma50": 9,
            "sma200": 8,
            "change_pct": 1,
            "yearHigh": 10,
            "yearLow": 5,
            "rsi": 55,
            "perf_1m": 2,
            "perf_3m": 5,
            "sector": "Technology",
        }
    ] * 3
    monkeypatch.setattr(tv_client, "get_us_stocks", lambda **_: stocks)

    result = tv_client.get_tv_breadth("us", min_price=5, limit=3)

    assert result["total_stocks"] == 3
    assert result["pct_above_sma200"] == 100.0
