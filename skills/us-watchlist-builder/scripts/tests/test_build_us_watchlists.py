import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "build_us_watchlists.py"
spec = importlib.util.spec_from_file_location("build_us_watchlists", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_serialize_candidate_keeps_dashboard_metrics_and_metadata():
    source = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 200,
        "sector": "Technology",
        "rsi": 62,
        "perf_1m": 4.5,
        "perf_3m": 12.0,
        "perf_y": 18.0,
        "avg_turnover": 10_000_000,
        "score": 88.5,
    }

    result = module.serialize_candidate(source)

    assert result["rsi"] == 62
    assert result["perf_1m"] == 4.5
    assert result["perf_3m"] == 12.0
    assert result["perf_y"] == 18.0
    assert result["avg_turnover"] == 10_000_000
    assert result["score"] == 88.5


def test_watchlist_criteria_are_available_for_dashboard():
    assert "growth" in module.WATCHLIST_CRITERIA
    assert "mean_reversion" in module.WATCHLIST_CRITERIA
