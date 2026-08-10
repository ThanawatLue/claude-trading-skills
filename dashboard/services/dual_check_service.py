"""Server-side Dual-Check ranking for dashboard candidates.

Hard gates use snapshot JSON + optional earnings lookup. Confluence and
day-bias remain unavailable until OHLCV pattern stats are ported server-side.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Literal

HoldStyle = Literal["overnight", "intraday"]
EarningsLookup = Callable[[str], Mapping[str, Any] | None]

TRADABLE_STATES = frozenset({"Pre-breakout", "Breakout"})
PIVOT_MIN_PCT = -2.0
PIVOT_MAX_PCT = 3.0
RS_MIN = 80.0
EARNINGS_MIN_DAYS = 7


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _gate(status: str, detail: str, code: str | None = None) -> dict[str, Any]:
    payload = {"status": status, "detail": detail}
    if code:
        payload["code"] = code
    return payload


def _pivot_distance(row: Mapping[str, Any]) -> float | None:
    direct = _number(row.get("distance_from_pivot_pct"))
    if direct is not None:
        return direct
    proximity = row.get("pivot_proximity")
    if isinstance(proximity, Mapping):
        return _number(proximity.get("distance_from_pivot_pct"))
    return None


def _rs_percentile(
    row: Mapping[str, Any], canslim_by_symbol: Mapping[str, Mapping[str, Any]]
) -> float | None:
    rs = row.get("relative_strength")
    if isinstance(rs, Mapping):
        for key in ("rs_percentile", "rs_rank_estimate", "rs_rank_percentile"):
            value = _number(rs.get(key))
            if value is not None:
                return value
    for key in ("rs_percentile", "rs_rank_estimate"):
        value = _number(row.get(key))
        if value is not None:
            return value

    symbol = str(row.get("symbol") or "")
    canslim = canslim_by_symbol.get(symbol) or canslim_by_symbol.get(symbol.replace(".BK", ""))
    if isinstance(canslim, Mapping):
        l_comp = canslim.get("l_component")
        if isinstance(l_comp, Mapping):
            for key in ("rs_rank_percentile", "rs_rank_estimate"):
                value = _number(l_comp.get(key))
                if value is not None:
                    return value
    return None


def _canslim_index(snapshot: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    canslim = snapshot.get("canslim")
    results = []
    if isinstance(canslim, Mapping):
        results = canslim.get("results") or []
    out: dict[str, Mapping[str, Any]] = {}
    if not isinstance(results, list):
        return out
    for row in results:
        if not isinstance(row, Mapping):
            continue
        symbol = str(row.get("symbol") or row.get("ticker") or "").strip()
        if not symbol:
            continue
        out[symbol] = row
        out[symbol.replace(".BK", "")] = row
    return out


def _unavailable_client_gates() -> dict[str, dict[str, Any]]:
    return {
        "confluence": _gate(
            "unavailable",
            "Confluence requires OHLCV pattern stats (client-side only in Phase B)",
        ),
        "day_bias": _gate(
            "unavailable",
            "Overnight/intraday day bias requires bar history (client-side only in Phase B)",
        ),
    }


def evaluate_candidate(
    row: Mapping[str, Any],
    *,
    regime_allowed: bool,
    hold_style: HoldStyle,
    canslim_by_symbol: Mapping[str, Mapping[str, Any]],
    earnings_lookup: EarningsLookup | None,
) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "").strip()
    score = _number(row.get("composite_score")) or 0.0
    state = str(row.get("execution_state") or row.get("consolidation_state") or "")
    distance = _pivot_distance(row)
    rs = _rs_percentile(row, canslim_by_symbol)

    gates: dict[str, dict[str, Any]] = {}
    reject_reasons: list[str] = []

    if regime_allowed:
        gates["regime"] = _gate("pass", "NEW_ENTRY_ALLOWED")
    else:
        gates["regime"] = _gate(
            "fail", "Regime does not allow new entries", "regime_not_new_entry_allowed"
        )
        reject_reasons.append("regime_not_new_entry_allowed")

    if state in TRADABLE_STATES:
        gates["setup_state"] = _gate("pass", state)
    else:
        gates["setup_state"] = _gate("fail", f"state={state or 'missing'}", "state_not_tradable")
        reject_reasons.append("state_not_tradable")

    if distance is not None and PIVOT_MIN_PCT <= distance <= PIVOT_MAX_PCT:
        gates["pivot"] = _gate("pass", f"{distance:.2f}% from pivot")
    else:
        detail = (
            "missing pivot distance" if distance is None else f"{distance:.2f}% outside [-2,+3]"
        )
        gates["pivot"] = _gate("fail", detail, "pivot_out_of_band")
        reject_reasons.append("pivot_out_of_band")

    if rs is not None and rs >= RS_MIN:
        gates["rs"] = _gate("pass", f"RS percentile {rs:.0f}")
    else:
        detail = "missing RS percentile" if rs is None else f"RS percentile {rs:.0f} < 80"
        gates["rs"] = _gate("fail", detail, "rs_below_80")
        reject_reasons.append("rs_below_80")

    earnings_info: Mapping[str, Any] | None = None
    if hold_style == "overnight":
        if earnings_lookup is not None and symbol:
            try:
                earnings_info = earnings_lookup(symbol)
            except Exception as exc:  # pragma: no cover - defensive
                gates["earnings"] = _gate(
                    "fail", f"earnings lookup error: {exc}", "earnings_lookup_error"
                )
                reject_reasons.append("earnings_lookup_error")
                earnings_info = None
        days = None
        if isinstance(earnings_info, Mapping):
            days = _number(earnings_info.get("days_to_earnings"))
        if "earnings" not in gates:
            if days is None or days > EARNINGS_MIN_DAYS:
                detail = "no upcoming earnings" if days is None else f"earnings in {int(days)} days"
                gates["earnings"] = _gate("pass", detail)
            else:
                gates["earnings"] = _gate(
                    "fail",
                    f"earnings in {int(days)} days",
                    "earnings_within_7_days",
                )
                reject_reasons.append("earnings_within_7_days")
    else:
        gates["earnings"] = _gate(
            "unavailable",
            "Earnings gate applies to overnight holds only",
        )

    gates.update(_unavailable_client_gates())

    passed = not reject_reasons
    return {
        "symbol": symbol,
        "composite_score": score,
        "execution_state": state,
        "distance_from_pivot_pct": distance,
        "rs_percentile": rs,
        "earnings": dict(earnings_info) if isinstance(earnings_info, Mapping) else None,
        "gates": gates,
        "passed": passed,
        "reject_reasons": reject_reasons,
        "source": "vcp",
    }


def rank_candidates(
    snapshot: Mapping[str, Any] | None,
    *,
    hold_style: HoldStyle = "overnight",
    earnings_lookup: EarningsLookup | None = None,
) -> dict[str, Any]:
    """Rank VCP candidates that pass Dual-Check hard gates."""
    snapshot = snapshot or {}
    if hold_style not in ("overnight", "intraday"):
        hold_style = "overnight"

    exposure = snapshot.get("exposure") if isinstance(snapshot.get("exposure"), Mapping) else {}
    recommendation = str((exposure or {}).get("recommendation") or "")
    regime_allowed = recommendation == "NEW_ENTRY_ALLOWED"

    vcp = snapshot.get("vcp") if isinstance(snapshot.get("vcp"), Mapping) else {}
    results = (vcp or {}).get("results") or []
    if not isinstance(results, list):
        results = []

    canslim_by_symbol = _canslim_index(snapshot)
    evaluated: list[dict[str, Any]] = []
    for row in results:
        if not isinstance(row, Mapping):
            continue
        evaluated.append(
            evaluate_candidate(
                row,
                regime_allowed=regime_allowed,
                hold_style=hold_style,
                canslim_by_symbol=canslim_by_symbol,
                earnings_lookup=earnings_lookup,
            )
        )

    evaluated.sort(key=lambda item: item.get("composite_score") or 0.0, reverse=True)
    passed = [item for item in evaluated if item.get("passed")]
    rejected = [item for item in evaluated if not item.get("passed")]

    return {
        "schema_version": 1,
        "hold_style": hold_style,
        "regime_allowed": regime_allowed,
        "recommendation": recommendation or None,
        "blocked_reason": None if regime_allowed else "regime_not_new_entry_allowed",
        "passed": passed,
        "rejected": rejected,
        "summary": {
            "evaluated": len(evaluated),
            "passed": len(passed),
            "rejected": len(rejected),
        },
        "gates_unavailable": ["confluence", "day_bias"],
    }
