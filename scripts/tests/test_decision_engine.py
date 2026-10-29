from __future__ import annotations

from scripts.decision_engine import evaluate_signal, extract_features


def test_extract_features_reads_thai_swing_payload_aliases() -> None:
    features = extract_features(
        {
            "price": 3.02,
            "rsi": 47.8,
            "rsi_weekly": 65.9,
            "sma20": 3.11,
            "sma50": 2.93,
            "perf_1m": -4.4,
            "perf_3m": 56.5,
            "volume": 470_401,
            "avg_volume": 275_795.3,
            "plan": {"entry": 3.02, "stop": 2.95, "target": 3.16},
        }
    )

    assert features["volume_ratio"] > 1.7
    assert features["sma50_distance_pct"] > 3
    assert features["sma20_gap_pct"] < -2
    assert features["plan_reward_r"] == 2.0


def test_evaluate_signal_exposes_weak_reversal_as_a_decision_failure() -> None:
    trace = evaluate_signal(
        {
            "symbol": "KCC.BK",
            "market": "TH",
            "source_skill": "thai-swing-dip",
            "raw_score": 84.0,
            "payload": {
                "price": 3.02,
                "rsi": 47.8,
                "rsi_weekly": 65.9,
                "sma20": 3.11,
                "sma50": 2.93,
                "perf_1m": -4.4,
                "perf_3m": 56.5,
                "volume": 470_401,
                "avg_volume": 275_795.3,
                "plan": {"entry": 3.02, "stop": 2.95, "target": 3.16},
            },
            "entry": 3.02,
            "stop": 2.95,
            "target": 3.16,
            "transaction_cost_bps": 21.692,
            "history": {"closed_count": 0, "wins": 0, "losses": 0, "sum_realized_r": 0},
        }
    )

    assert trace["features"]["reversal_score"] < 0.6
    assert "reversal_not_confirmed" in trace["gates"]["failed"]
    assert trace["decision"] == "hold"


def test_evaluate_signal_accounts_for_history_and_round_trip_cost() -> None:
    trace = evaluate_signal(
        {
            "symbol": "KCC.BK",
            "market": "TH",
            "source_skill": "thai-swing-dip",
            "raw_score": 85.5,
            "payload": {},
            "entry": 3.0,
            "stop": 2.8,
            "target": 3.4,
            "transaction_cost_bps": 21.692,
            "history": {"closed_count": 2, "wins": 0, "losses": 2, "sum_realized_r": -2.3},
        }
    )

    assert trace["execution"]["round_trip_cost_r"] > 0
    assert trace["history"]["posterior_win_rate"] < 0.5
    assert trace["components"]["expected_net_r"] < trace["components"]["gross_reward_r"]


def test_evaluate_signal_calibrated_predicted_probability() -> None:
    # 0 trades history -> posterior_win_rate = 0.5
    # raw_score = 85.0 -> score_prior = 0.587
    # predicted_probability = 0.5 * 0.5 + 0.5 * 0.587 = 0.5435
    trace = evaluate_signal(
        {
            "symbol": "PTTGC.BK",
            "market": "TH",
            "source_skill": "thai-swing-dip",
            "raw_score": 85.0,
            "payload": {},
            "entry": 30.0,
            "stop": 28.5,
            "target": 33.0,
            "history": {"closed_count": 0, "wins": 0, "losses": 0, "sum_realized_r": 0},
        }
    )
    assert trace["predicted_probability"] == 0.5435
    assert trace["components"]["predicted_probability"] == 0.5435


def test_extract_features_dip_buy_reversal_score_bounce_floor() -> None:
    # Mild pullback (-1.5%) with strong support (+3% above SMA50) and good pullback gap (-2%)
    features_mild = extract_features(
        {
            "price": 10.0,
            "sma20": 10.2,  # gap -1.96% -> pullback_score high
            "sma50": 9.7,  # dist +3.09% -> support_score high
            "perf_1m": -1.5,
        }
    )
    # Reversal score elevated by bounce floor above raw -1.5% normalisation (0.35)
    assert features_mild["reversal_score"] is not None
    assert features_mild["reversal_score"] >= 0.60

    # Severe falling knife (-4.4%) does not get elevated
    features_knife = extract_features(
        {
            "price": 10.0,
            "sma20": 10.2,
            "sma50": 9.7,
            "perf_1m": -4.4,
        }
    )
    assert features_knife["reversal_score"] is not None
    assert features_knife["reversal_score"] < 0.20
