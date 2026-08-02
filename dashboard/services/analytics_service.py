"""Deterministic analytics for signal outcomes.

The dashboard uses this module as a read-only analysis boundary.  It accepts
joined SQLite rows (or plain mappings) and never changes signals, paper
positions, or execution settings.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from statistics import median
from typing import Any


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _pick(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def _payload(row: Mapping[str, Any]) -> dict[str, Any]:
    value = row.get("payload_json")
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _nested(row: Mapping[str, Any], *paths: tuple[str, ...]) -> Any:
    payload = _payload(row)
    for path in paths:
        current: Any = payload
        for part in path:
            if not isinstance(current, Mapping):
                current = None
                break
            current = current.get(part)
        if current is not None and current != "":
            return current
    return None


def _record_r(row: Mapping[str, Any]) -> float | None:
    explicit = _number(_pick(row, "theoretical_r", "r_multiple", "realized_r", "r"))
    if explicit is not None:
        return explicit
    return_pct = _number(_pick(row, "return_pct", "return"))
    entry = _number(_pick(row, "entry_price", "entry_close", "entry"))
    stop = _number(_pick(row, "stop_price", "stop"))
    if return_pct is None or entry is None or stop is None or entry <= stop:
        return None
    # Signal-ledger return_pct is stored as a decimal (0.04 == 4%), while
    # callers may provide a percentage. Convert the price move back to R.
    move = return_pct if abs(return_pct) > 1 else return_pct * entry
    return move / (entry - stop)


def _record_return_pct(row: Mapping[str, Any]) -> float | None:
    value = _number(_pick(row, "return_pct", "return"))
    if value is None:
        return None
    return value / 100 if abs(value) > 1 else value


def _record_regime(row: Mapping[str, Any]) -> str:
    value = _pick(row, "regime", "market_regime", "regime_label")
    if value is None:
        value = _nested(
            row,
            ("regime",),
            ("market_regime",),
            ("decision_trace", "features", "market_regime"),
            ("decision_trace", "features", "regime"),
            ("context", "regime"),
        )
    text = str(value).strip() if value is not None else ""
    return text or "unknown"


def _record_probability(row: Mapping[str, Any]) -> float | None:
    value = _pick(
        row,
        "predicted_probability",
        "win_probability",
        "probability",
        "confidence",
    )
    if value is None:
        value = _nested(
            row,
            ("predicted_probability",),
            ("win_probability",),
            ("confidence",),
            ("decision_trace", "features", "confidence"),
        )
    probability = _number(value)
    if probability is None:
        return None
    if probability > 1 and probability <= 100:
        probability /= 100
    return probability if 0 <= probability <= 1 else None


def wilson_interval(wins: int, sample_size: int, z: float = 1.96) -> list[float | None]:
    """Return a stable 95% Wilson interval for a binomial win rate."""
    if sample_size <= 0:
        return [None, None]
    p = wins / sample_size
    denominator = 1 + z * z / sample_size
    centre = (p + z * z / (2 * sample_size)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * sample_size)) / sample_size) / denominator
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def _max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    cumulative = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        cumulative += value
        peak = max(peak, cumulative)
        drawdown = min(drawdown, cumulative - peak)
    return round(drawdown, 4)


def summarize_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize R outcomes, risk excursions, and drawdown for a record set."""
    rows = list(records)
    rs = [value for row in rows if (value := _record_r(row)) is not None]
    outcome_values = []
    for row in rows:
        value = _record_r(row)
        if value is None:
            value = _record_return_pct(row)
        if value is not None:
            outcome_values.append(value)
    wins = sum(1 for value in outcome_values if value > 0)
    losses = sum(1 for value in outcome_values if value <= 0)
    win_rate = wins / len(outcome_values) if outcome_values else None
    positive = [value for value in rs if value > 0]
    negative = [value for value in rs if value <= 0]
    mae = [value for row in rows if (value := _number(row.get("mae_pct"))) is not None]
    mfe = [value for row in rows if (value := _number(row.get("mfe_pct"))) is not None]
    returns = [value for row in rows if (value := _record_return_pct(row)) is not None]
    rs_for_drawdown = []
    for row in sorted(
        rows, key=lambda item: str(item.get("evaluation_date") or item.get("signal_date") or "")
    ):
        value = _record_r(row)
        if value is not None:
            rs_for_drawdown.append(value)
    gross_profit = sum(positive)
    gross_loss = abs(sum(negative))

    return {
        "sample_size": len(outcome_values),
        "r_sample_size": len(rs),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "win_rate_ci": wilson_interval(wins, len(outcome_values)),
        "avg_win_r": round(sum(positive) / len(positive), 4) if positive else None,
        "avg_loss_r": round(sum(negative) / len(negative), 4) if negative else None,
        "avg_loss_abs_r": round(gross_loss / len(negative), 4) if negative else None,
        "expectancy_r": round(sum(rs) / len(rs), 4) if rs else None,
        "profit_factor": round(gross_profit / gross_loss, 4)
        if gross_loss
        else (None if not gross_profit else None),
        "median_r": round(median(rs), 4) if rs else None,
        "avg_return_pct": round(sum(returns) / len(returns), 4) if returns else None,
        "median_return_pct": round(median(returns), 4) if returns else None,
        "max_drawdown_r": _max_drawdown(rs_for_drawdown),
        "mae_mfe_sample": min(len(mae), len(mfe)) if mae and mfe else max(len(mae), len(mfe)),
        "avg_mae_pct": round(sum(mae) / len(mae), 4) if mae else None,
        "worst_mae_pct": round(min(mae), 4) if mae else None,
        "avg_mfe_pct": round(sum(mfe) / len(mfe), 4) if mfe else None,
        "best_mfe_pct": round(max(mfe), 4) if mfe else None,
    }


def _bucket_label(score: float) -> str:
    for low, high in ((0, 60), (60, 70), (70, 80), (80, 90), (90, 101)):
        if low <= score < high:
            return f"{low}-{high - 1}"
    return "unknown"


def _group_stats(records: Iterable[Mapping[str, Any]], key_fn) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        groups[str(key_fn(row))].append(row)
    output = []
    for label in sorted(groups):
        output.append({"label": label, **summarize_records(groups[label])})
    return output


def calibration_summary(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate reliability bins only when a probability-like field exists."""
    points: list[tuple[float, int]] = []
    for row in records:
        probability = _record_probability(row)
        value = _record_r(row)
        if probability is not None and value is None:
            value = _record_return_pct(row)
        if probability is not None and value is not None:
            points.append((probability, int(value > 0)))
    if not points:
        return {"available": False, "sample_size": 0, "brier_score": None, "ece": None, "bins": []}

    bins = []
    total_error = 0.0
    brier = 0.0
    for low, high in zip((0.0, 0.2, 0.4, 0.6, 0.8), (0.2, 0.4, 0.6, 0.8, 1.01)):
        selected = [
            (probability, outcome) for probability, outcome in points if low <= probability < high
        ]
        if selected:
            avg_probability = sum(item[0] for item in selected) / len(selected)
            observed_rate = sum(item[1] for item in selected) / len(selected)
            total_error += abs(avg_probability - observed_rate) * len(selected)
            brier += sum((probability - outcome) ** 2 for probability, outcome in selected)
        else:
            avg_probability = None
            observed_rate = None
        bins.append(
            {
                "label": f"{int(low * 100)}-{min(100, int(high * 100))}%",
                "sample_size": len(selected),
                "predicted": round(avg_probability, 4) if avg_probability is not None else None,
                "observed": round(observed_rate, 4) if observed_rate is not None else None,
            }
        )
    return {
        "available": True,
        "sample_size": len(points),
        "brier_score": round(brier / len(points), 4),
        "ece": round(total_error / len(points), 4),
        "bins": bins,
    }


def build_decision_analytics(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build all decision-quality views from complete outcome rows."""
    rows = list(records)
    by_horizon: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        horizon = _number(row.get("horizon_days"))
        if horizon is not None and bool(row.get("is_complete", 1)):
            by_horizon[str(int(horizon))].append(row)

    horizon_stats = {
        horizon: summarize_records(items)
        for horizon, items in sorted(by_horizon.items(), key=lambda item: int(item[0]))
    }
    primary_horizon = "5" if "5" in horizon_stats else (next(iter(horizon_stats), None))
    primary_rows = by_horizon.get(primary_horizon, []) if primary_horizon else []
    notes = []
    if not primary_rows:
        notes.append("ยังไม่มี complete outcome ที่ใช้คำนวณ analytics ได้")
    if primary_rows and all(_record_regime(row) == "unknown" for row in primary_rows):
        notes.append("ยังไม่มี market regime ใน signal payload จึงแสดง regime bucket เป็น unknown")
    if primary_rows and not summarize_records(primary_rows).get("r_sample_size"):
        notes.append(
            "complete outcomes ยังไม่มี entry/stop risk ที่คำนวณ R ได้ จึงใช้ forward return สำหรับ win rate และยังไม่สรุป expectancy R"
        )
    if not calibration_summary(primary_rows).get("available"):
        notes.append(
            "ยังไม่มี predicted probability/confidence ที่ผูกกับ outcome จึงยังไม่แสดง calibration curve"
        )

    return {
        "status": "ok" if primary_rows else "insufficient_data",
        "primary_horizon_days": int(primary_horizon) if primary_horizon else None,
        "overall": summarize_records(primary_rows),
        "by_horizon": horizon_stats,
        "score_buckets": _group_stats(
            [row for row in primary_rows if _number(_pick(row, "raw_score", "score")) is not None],
            lambda row: _bucket_label(_number(_pick(row, "raw_score", "score")) or 0),
        ),
        "regimes": _group_stats(primary_rows, _record_regime),
        "calibration": calibration_summary(primary_rows),
        "notes": notes,
    }


__all__ = [
    "build_decision_analytics",
    "calibration_summary",
    "summarize_records",
    "wilson_interval",
]
