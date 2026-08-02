from dashboard.services.analytics_service import (
    build_decision_analytics,
    calibration_summary,
    summarize_records,
    wilson_interval,
)


def test_summarize_records_reports_expectancy_drawdown_and_mae_mfe() -> None:
    rows = [
        {"theoretical_r": 2.0, "mae_pct": -0.03, "mfe_pct": 0.08, "evaluation_date": "2026-01-01"},
        {"theoretical_r": -1.0, "mae_pct": -0.07, "mfe_pct": 0.02, "evaluation_date": "2026-01-02"},
        {"theoretical_r": 1.0, "mae_pct": -0.02, "mfe_pct": 0.04, "evaluation_date": "2026-01-03"},
    ]

    result = summarize_records(rows)

    assert result["sample_size"] == 3
    assert result["win_rate"] == 0.6667
    assert result["expectancy_r"] == 0.6667
    assert result["profit_factor"] == 3.0
    assert result["max_drawdown_r"] == -1.0
    assert result["avg_mae_pct"] == -0.04
    assert result["best_mfe_pct"] == 0.08


def test_build_decision_analytics_groups_horizons_score_regime_and_calibration() -> None:
    rows = [
        {
            "horizon_days": 5,
            "is_complete": 1,
            "theoretical_r": 1,
            "raw_score": 82,
            "regime": "bull",
            "predicted_probability": 0.7,
        },
        {
            "horizon_days": 5,
            "is_complete": 1,
            "theoretical_r": -1,
            "raw_score": 68,
            "regime": "bear",
            "predicted_probability": 0.4,
        },
        {
            "horizon_days": 20,
            "is_complete": 1,
            "theoretical_r": 2,
            "raw_score": 91,
            "regime": "bull",
            "predicted_probability": 0.9,
        },
        {
            "horizon_days": 5,
            "is_complete": 0,
            "theoretical_r": 3,
            "raw_score": 95,
            "regime": "bull",
            "predicted_probability": 0.9,
        },
    ]

    result = build_decision_analytics(rows)

    assert result["status"] == "ok"
    assert result["primary_horizon_days"] == 5
    assert result["overall"]["sample_size"] == 2
    assert {item["label"] for item in result["score_buckets"]} == {"60-69", "80-89"}
    assert {item["label"] for item in result["regimes"]} == {"bear", "bull"}
    assert result["calibration"]["available"] is True
    assert result["by_horizon"]["20"]["sample_size"] == 1


def test_calibration_summary_is_explicitly_unavailable_without_probabilities() -> None:
    result = calibration_summary([{"theoretical_r": 1}, {"theoretical_r": -1}])

    assert result == {
        "available": False,
        "sample_size": 0,
        "brier_score": None,
        "ece": None,
        "bins": [],
    }


def test_wilson_interval_handles_empty_and_small_samples() -> None:
    assert wilson_interval(0, 0) == [None, None]
    low, high = wilson_interval(1, 1)
    assert 0 <= low < high <= 1
