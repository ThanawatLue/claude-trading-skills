"""Explainable, data-driven paper-entry decisions.

The engine deliberately keeps feature extraction and scoring pure.  Auto-paper
passes a signal snapshot plus the symbol/source history and stores the returned
trace with the paper trade so a later outcome can be traced back to the exact
decision that opened it.
"""

from __future__ import annotations

import math
from typing import Any


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _first(mapping: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _number(mapping.get(key))
        if value is not None:
            return value
    return None


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 4)


def _normalise_range(value: float | None, low: float, high: float) -> float | None:
    if value is None:
        return None
    if high == low:
        return 0.5
    return _clip((value - low) / (high - low))


def extract_features(payload: dict[str, Any] | None) -> dict[str, float | None]:
    """Extract comparable features from screener payload variants."""
    raw = payload or {}
    plan = raw.get("plan") if isinstance(raw.get("plan"), dict) else {}
    price = _first(raw, "price", "current_price", "close", "entry_price")
    if price is None:
        price = _first(plan, "entry")
    sma20 = _first(raw, "sma20", "sma_20")
    sma50 = _first(raw, "sma50", "sma_50")
    sma200 = _first(raw, "sma200", "sma_200")
    volume = _first(raw, "volume")
    avg_volume = _first(raw, "avg_volume", "avgVolume", "average_volume")
    entry = _first(plan, "entry") or _first(raw, "entry_price", "entry") or price
    stop = _first(plan, "stop") or _first(raw, "stop_price", "stop")
    target = _first(plan, "target") or _first(raw, "target_price", "target")

    volume_ratio = volume / avg_volume if volume and avg_volume and avg_volume > 0 else None
    sma50_distance_pct = (price / sma50 - 1) * 100 if price and sma50 else None
    sma20_gap_pct = (price / sma20 - 1) * 100 if price and sma20 else None
    sma200_distance_pct = (price / sma200 - 1) * 100 if price and sma200 else None
    plan_risk_pct = (entry - stop) / entry * 100 if entry and stop and entry > stop else None
    plan_reward_pct = (target - entry) / entry * 100 if entry and target and target > entry else None
    plan_reward_r = (
        (target - entry) / (entry - stop)
        if entry and stop and target and entry > stop and target > entry
        else None
    )

    # These scores describe evidence of a bounce, rather than merely the
    # screener's score. Negative short-term performance is explicitly treated
    # as weak confirmation for a dip-buy entry.
    perf_1m = _first(raw, "perf_1m", "performance_1m")
    perf_3m = _first(raw, "perf_3m", "performance_3m")
    reversal_score = _normalise_range(perf_1m, -5.0, 5.0)
    support_score = _normalise_range(sma50_distance_pct, 0.5, 5.0)
    pullback_score = (
        _clip(1 - abs(sma20_gap_pct + 2.0) / 5.0) if sma20_gap_pct is not None else None
    )
    trend_score = None
    if perf_3m is not None and sma50_distance_pct is not None:
        trend_score = _clip(
            0.5 * _normalise_range(perf_3m, 0.0, 30.0)
            + 0.5 * _normalise_range(sma50_distance_pct, 0.0, 5.0)
        )
    components = [x for x in (reversal_score, support_score, pullback_score, trend_score) if x is not None]
    confirmation_score = sum(components) / len(components) if components else None

    return {
        "price": price,
        "rsi": _first(raw, "rsi"),
        "rsi_weekly": _first(raw, "rsi_weekly", "weekly_rsi"),
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "perf_1m": perf_1m,
        "perf_3m": perf_3m,
        "volume": volume,
        "avg_volume": avg_volume,
        "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
        "sma50_distance_pct": round(sma50_distance_pct, 4) if sma50_distance_pct is not None else None,
        "sma20_gap_pct": round(sma20_gap_pct, 4) if sma20_gap_pct is not None else None,
        "sma200_distance_pct": round(sma200_distance_pct, 4) if sma200_distance_pct is not None else None,
        "plan_risk_pct": round(plan_risk_pct, 4) if plan_risk_pct is not None else None,
        "plan_reward_pct": round(plan_reward_pct, 4) if plan_reward_pct is not None else None,
        "plan_reward_r": round(plan_reward_r, 4) if plan_reward_r is not None else None,
        "reversal_score": reversal_score,
        "support_score": support_score,
        "pullback_score": pullback_score,
        "trend_score": trend_score,
        "confirmation_score": round(confirmation_score, 4) if confirmation_score is not None else None,
    }


def evaluate_signal(context: dict[str, Any]) -> dict[str, Any]:
    """Return an explainable dynamic decision trace for one candidate."""
    entry = float(context["entry"])
    stop = float(context["stop"])
    target = float(context["target"])
    bps = float(context.get("transaction_cost_bps") or 0.0)
    features = extract_features(context.get("payload"))
    history = context.get("history") or {}
    closed_count = int(history.get("closed_count") or 0)
    wins = int(history.get("wins") or 0)
    losses = int(history.get("losses") or 0)
    sum_realized_r = float(history.get("sum_realized_r") or 0.0)

    # Bayesian shrinkage keeps a two-trade profile from becoming a permanent
    # blacklist while still lowering its expected value immediately.
    prior_n = 5.0
    posterior_win_rate = (wins + prior_n * 0.5) / (closed_count + prior_n)
    posterior_avg_r = sum_realized_r / (closed_count + prior_n)

    risk = entry - stop
    gross_reward_r = (target - entry) / risk if risk > 0 else 0.0
    round_trip_cost = (entry + target) * bps / 10_000
    round_trip_cost_r = round_trip_cost / risk if risk > 0 else 0.0
    net_reward_r = gross_reward_r - round_trip_cost_r
    expected_loss_r = (
        float(history["avg_loss_r"])
        if history.get("avg_loss_r") is not None and losses
        else -1.0
    )
    expected_net_r = posterior_win_rate * net_reward_r + (1 - posterior_win_rate) * expected_loss_r

    failed: list[str] = []
    confirmation = features.get("confirmation_score")
    if confirmation is not None and confirmation < float(context.get("min_confirmation_score", 0.6)):
        failed.append("reversal_not_confirmed")
    if expected_net_r < float(context.get("min_expected_net_r", 0.0)):
        failed.append("negative_expected_net_edge")
    if context.get("cooldown_active"):
        failed.append("symbol_cooldown_after_loss")

    raw_score = _number(context.get("raw_score")) or 0.0
    confirmation_adjustment = (confirmation - 0.5) * 20 if confirmation is not None else 0.0
    behavior_adjustment = posterior_avg_r * 10
    decision_score = raw_score + confirmation_adjustment + behavior_adjustment + expected_net_r * 5

    return {
        "version": "dynamic-v1",
        "decision": "hold" if failed else "open",
        "symbol": context.get("symbol"),
        "market": context.get("market"),
        "source_skill": context.get("source_skill"),
        "features": features,
        "history": {
            "closed_count": closed_count,
            "wins": wins,
            "losses": losses,
            "sum_realized_r": round(sum_realized_r, 4),
            "avg_loss_r": round(expected_loss_r, 4),
            "posterior_win_rate": round(posterior_win_rate, 4),
            "posterior_avg_r": round(posterior_avg_r, 4),
            "cooldown_active": bool(context.get("cooldown_active")),
        },
        "execution": {
            "entry": entry,
            "stop": stop,
            "target": target,
            "gross_reward_r": round(gross_reward_r, 4),
            "round_trip_cost_r": round(round_trip_cost_r, 4),
            "net_reward_r": round(net_reward_r, 4),
        },
        "components": {
            "raw_score": round(raw_score, 4),
            "confirmation_adjustment": round(confirmation_adjustment, 4),
            "behavior_adjustment": round(behavior_adjustment, 4),
            "gross_reward_r": round(gross_reward_r, 4),
            "expected_net_r": round(expected_net_r, 4),
            "decision_score": round(decision_score, 4),
        },
        "gates": {"failed": failed, "passed": not failed},
    }
