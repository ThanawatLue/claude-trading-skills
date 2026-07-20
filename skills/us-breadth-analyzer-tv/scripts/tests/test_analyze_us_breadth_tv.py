import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "analyze_us_breadth_tv.py"
spec = importlib.util.spec_from_file_location("analyze_us_breadth_tv", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_composite_score_returns_expected_regime():
    score, regime = module.composite_score({
        "total_stocks": 100,
        "pct_above_sma50": 80,
        "pct_above_sma200": 75,
        "advancers": 70,
        "decliners": 20,
        "new_52w_highs": 20,
        "new_52w_lows": 2,
    })

    assert score >= 70
    assert regime == "Strong Bull"
