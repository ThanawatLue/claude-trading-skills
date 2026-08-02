import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "generate_us_heatmap.py"
spec = importlib.util.spec_from_file_location("generate_us_heatmap", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_compute_sector_stats_ranks_by_weighted_momentum():
    stocks = [
        {"symbol": f"TECH{i}", "name": "Tech", "sector": "Technology", "perf_1m": 10 + i, "perf_3m": 20, "perf_6m": 30, "perf_y": 40, "price": 100}
        for i in range(5)
    ] + [
        {"symbol": f"UTIL{i}", "name": "Utility", "sector": "Utilities", "perf_1m": -5, "perf_3m": -5, "perf_6m": -5, "perf_y": -5, "price": 50}
        for i in range(5)
    ]

    result = module.compute_sector_stats(stocks)

    assert result[0]["sector"] == "Technology"
    assert result[0]["rank"] == 1
    assert len(result[0]["top_stocks"]) == 3


def test_to_markdown_handles_missing_top_stock_price():
    sectors = [{
        "rank": 1,
        "sector": "Technology",
        "n_stocks": 5,
        "median_perf_1m": 1,
        "median_perf_3m": 2,
        "median_perf_6m": 3,
        "median_perf_y": 4,
        "momentum_score": 2,
        "top_stocks": [{"symbol": "AAPL", "name": "Apple", "perf_3m": 2, "price": None}],
    }]

    report = module.to_markdown(sectors, 5, "2026-07-20_120000")

    assert "$0.00" in report
