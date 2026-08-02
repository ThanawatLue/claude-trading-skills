import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "screen_us_dividends.py"
spec = importlib.util.spec_from_file_location("screen_us_dividends", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_score_stock_accepts_qualified_uptrend_dividend_stock():
    stock = {
        "dividend_yield": 4,
        "marketCap": 2_000_000_000,
        "avg_turnover": 10_000_000,
        "pe_ratio": 12,
        "price": 110,
        "sma200": 100,
        "rsi": 48,
        "perf_y": 15,
    }

    ok, score, metrics = module.score_stock(stock, min_yield=3, min_mcap=1_000_000_000)

    assert ok is True
    assert score > 0
    assert metrics["avg_turnover"] == 10_000_000


def test_score_stock_rejects_stock_below_sma200():
    stock = {
        "dividend_yield": 5,
        "marketCap": 2_000_000_000,
        "avg_turnover": 10_000_000,
        "pe_ratio": 12,
        "price": 90,
        "sma200": 100,
    }

    ok, score, metrics = module.score_stock(stock, min_yield=3, min_mcap=1_000_000_000)

    assert (ok, score, metrics) == (False, 0.0, {})
