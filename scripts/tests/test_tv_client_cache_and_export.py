from unittest import mock

import pytest

from scripts.lib import tv_client


@pytest.fixture(autouse=True)
def clean_cache():
    tv_client.clear_tv_cache()
    yield
    tv_client.clear_tv_cache()


def test_export_tradingview_watchlist_from_dicts():
    stocks = [
        {"symbol": "DELTA", "price": 100},
        {"symbol": "ADVANC", "price": 200},
        {"symbol": "SET:CPALL", "price": 50},
    ]
    res = tv_client.export_tradingview_watchlist(stocks)
    assert res == "SET:DELTA,SET:ADVANC,SET:CPALL"


def test_export_tradingview_watchlist_from_strings():
    symbols = ["PTT", "bbl", "SET:scb"]
    res = tv_client.export_tradingview_watchlist(symbols)
    assert res == "SET:PTT,SET:BBL,SET:SCB"


def test_export_tradingview_watchlist_custom_prefix():
    symbols = ["AAPL", "MSFT"]
    res = tv_client.export_tradingview_watchlist(symbols, prefix="NASDAQ:")
    assert res == "NASDAQ:AAPL,NASDAQ:MSFT"


def test_export_tradingview_watchlist_writes_file(tmp_path):
    out = tmp_path / "watchlist.txt"
    res = tv_client.export_tradingview_watchlist(["CPALL", "BDMS"], output_file=out)
    assert res == "SET:CPALL,SET:BDMS"
    assert out.is_file()
    assert out.read_text(encoding="utf-8").strip() == "SET:CPALL,SET:BDMS"


def test_tv_stocks_caching():
    sample_data = [{"symbol": "CPALL", "price": 60.0}]

    with mock.patch.object(tv_client, "_safe_query", return_value=sample_data) as mock_query:
        # First call fetches and saves to cache
        res1 = tv_client.get_tv_stocks("TH", limit=50, use_cache=True)
        assert res1 == sample_data
        assert mock_query.call_count == 1

        # Second call hits cache, does not query again
        res2 = tv_client.get_tv_stocks("TH", limit=50, use_cache=True)
        assert res2 == sample_data
        assert mock_query.call_count == 1

        # Call with use_cache=False bypasses cache
        res3 = tv_client.get_tv_stocks("TH", limit=50, use_cache=False)
        assert res3 == sample_data
        assert mock_query.call_count == 2
