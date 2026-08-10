"""Server-side Dual-Check ranking for dashboard candidates.

Hard gates: regime, setup state, Stage-2 trend template, pivot band, RS,
earnings (overnight), confluence, and hold-style day bias when OHLCV bars
are available. Thai swing candidates are included alongside VCP.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

from dashboard.services.pattern_stats import (
    compute_confluence,
    compute_day_bias,
    evaluate_confluence_gate,
    evaluate_day_bias_gate,
)

HoldStyle = Literal["overnight", "intraday"]
EarningsLookup = Callable[[str], Mapping[str, Any] | None]
BarsLookup = Callable[[str], Sequence[Mapping[str, Any]] | None]

TRADABLE_STATES = frozenset({"Pre-breakout", "Breakout"})
PIVOT_MIN_PCT = -2.0
PIVOT_MAX_PCT = 3.0
RS_MIN = 80.0
EARNINGS_MIN_DAYS = 7
TREND_TEMPLATE_MIN = 85.0
THAI_SWING_MIN_SCORE = 70.0


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
    plan = row.get("plan")
    price = _number(row.get("price"))
    if isinstance(plan, Mapping) and price is not None and price > 0:
        entry = _number(plan.get("entry"))
        if entry is not None:
            return (price - entry) / entry * 100.0
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


def _trend_template_passed(row: Mapping[str, Any]) -> bool | None:
    tt = row.get("trend_template")
    if isinstance(tt, Mapping):
        if "passed" in tt:
            return bool(tt.get("passed"))
        score = _number(tt.get("score"))
        if score is not None:
            return score >= TREND_TEMPLATE_MIN
    # Explicit flag from screeners
    if "trend_template_passed" in row:
        return bool(row.get("trend_template_passed"))
    # Thai swing proxy: price above SMA50 (Stage-2-ish short-term)
    if row.get("source", "").startswith("thai_swing") or row.get("_dual_source", "").startswith(
        "thai_swing"
    ):
        price = _number(row.get("price"))
        sma50 = _number(row.get("sma50"))
        if price is not None and sma50 is not None and sma50 > 0:
            return price > sma50
        return None
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


def _normalize_thai_swing_rows(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    thai = snapshot.get("thai_swing")
    if not isinstance(thai, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    for bucket, state in (("dip_buy", "Pre-breakout"), ("momentum", "Breakout")):
        items = thai.get(bucket) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, Mapping):
                continue
            symbol = str(item.get("symbol") or "").strip()
            if not symbol:
                continue
            score = _number(item.get("score")) or 0.0
            row = dict(item)
            row["symbol"] = symbol
            row["composite_score"] = score
            row["execution_state"] = state
            row["_dual_source"] = f"thai_swing_{bucket}"
            row["source"] = f"thai_swing_{bucket}"
            rows.append(row)
    return rows


def _candidate_rows(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    market = str(snapshot.get("market") or "").upper()

    vcp = snapshot.get("vcp") if isinstance(snapshot.get("vcp"), Mapping) else {}
    results = (vcp or {}).get("results") or []
    if isinstance(results, list):
        for row in results:
            if not isinstance(row, Mapping):
                continue
            symbol = str(row.get("symbol") or "").strip()
            if not symbol or symbol in seen:
                continue
            item = dict(row)
            item.setdefault("source", "vcp")
            item["_dual_source"] = "vcp"
            rows.append(item)
            seen.add(symbol)

    # Thai swing candidates are TH-only (US snapshots may still contain the file).
    if market in {"TH", "THA"}:
        for row in _normalize_thai_swing_rows(snapshot):
            symbol = str(row.get("symbol") or "").strip()
            if not symbol or symbol in seen:
                continue
            # Only keep swing names that clear a minimum score before Dual-Check
            if (_number(row.get("composite_score")) or 0.0) < THAI_SWING_MIN_SCORE:
                continue
            rows.append(row)
            seen.add(symbol)
    return rows


def evaluate_candidate(
    row: Mapping[str, Any],
    *,
    regime_allowed: bool,
    hold_style: HoldStyle,
    canslim_by_symbol: Mapping[str, Mapping[str, Any]],
    earnings_lookup: EarningsLookup | None,
    bars_lookup: BarsLookup | None = None,
    require_verified_earnings: bool = False,
    defer_earnings: bool = False,
) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "").strip()
    score = _number(row.get("composite_score")) or 0.0
    state = str(row.get("execution_state") or row.get("consolidation_state") or "")
    distance = _pivot_distance(row)
    rs = _rs_percentile(row, canslim_by_symbol)
    source = str(row.get("_dual_source") or row.get("source") or "vcp")

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

    tt_passed = _trend_template_passed(row)
    if tt_passed is True:
        gates["stage2"] = _gate("pass", "Trend template / Stage-2 proxy passed")
    elif tt_passed is False:
        gates["stage2"] = _gate("fail", "Trend template / Stage-2 failed", "stage2_failed")
        reject_reasons.append("stage2_failed")
    else:
        # VCP funnel usually already Stage-2 filtered; missing field = unavailable (non-blocking)
        gates["stage2"] = _gate(
            "unavailable",
            "Trend template fields missing on candidate",
        )

    if distance is not None and PIVOT_MIN_PCT <= distance <= PIVOT_MAX_PCT:
        gates["pivot"] = _gate("pass", f"{distance:.2f}% from pivot/entry")
    else:
        detail = (
            "missing pivot distance" if distance is None else f"{distance:.2f}% outside [-2,+3]"
        )
        gates["pivot"] = _gate("fail", detail, "pivot_out_of_band")
        reject_reasons.append("pivot_out_of_band")

    if rs is not None and rs >= RS_MIN:
        gates["rs"] = _gate("pass", f"RS percentile {rs:.0f}")
    elif source.startswith("thai_swing") and rs is None:
        # Thai swing often lacks universe RS — do not hard-fail; require confluence instead
        gates["rs"] = _gate("unavailable", "RS percentile not provided for Thai swing")
    else:
        detail = "missing RS percentile" if rs is None else f"RS percentile {rs:.0f} < 80"
        gates["rs"] = _gate("fail", detail, "rs_below_80")
        reject_reasons.append("rs_below_80")

    earnings_info: Mapping[str, Any] | None = None
    if hold_style == "overnight":
        if defer_earnings:
            gates["earnings"] = _gate("pending", "Earnings check deferred until other gates pass")
        else:
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
            verified = False
            if isinstance(earnings_info, Mapping):
                days = _number(earnings_info.get("days_to_earnings"))
                verified = bool(earnings_info.get("verified")) or bool(earnings_info.get("date"))
            if "earnings" not in gates:
                if require_verified_earnings and not verified:
                    gates["earnings"] = _gate(
                        "fail",
                        "earnings date unverified for overnight hold",
                        "earnings_unverified",
                    )
                    reject_reasons.append("earnings_unverified")
                elif days is None or days > EARNINGS_MIN_DAYS:
                    detail = (
                        "no upcoming earnings" if days is None else f"earnings in {int(days)} days"
                    )
                    if not verified and days is None:
                        detail = "no upcoming earnings (unverified)"
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

    bars = None
    if bars_lookup is not None and symbol:
        try:
            bars = bars_lookup(symbol)
        except Exception:
            bars = None

    confluence = compute_confluence(bars) if bars is not None else None
    c_status, c_detail, c_code = evaluate_confluence_gate(confluence)
    gates["confluence"] = _gate(c_status, c_detail, c_code)
    if c_code:
        reject_reasons.append(c_code)

    bias = compute_day_bias(bars, hold_style=hold_style) if bars is not None else None
    b_status, b_detail, b_code = evaluate_day_bias_gate(bias)
    gates["day_bias"] = _gate(b_status, b_detail, b_code)
    if b_code:
        reject_reasons.append(b_code)

    passed = not reject_reasons
    return {
        "symbol": symbol,
        "composite_score": score,
        "execution_state": state,
        "distance_from_pivot_pct": distance,
        "rs_percentile": rs,
        "earnings": dict(earnings_info) if isinstance(earnings_info, Mapping) else None,
        "confluence": dict(confluence) if isinstance(confluence, Mapping) else None,
        "day_bias": dict(bias) if isinstance(bias, Mapping) else None,
        "gates": gates,
        "passed": passed,
        "reject_reasons": reject_reasons,
        "source": source,
    }


def rank_candidates(
    snapshot: Mapping[str, Any] | None,
    *,
    hold_style: HoldStyle = "overnight",
    earnings_lookup: EarningsLookup | None = None,
    bars_lookup: BarsLookup | None = None,
    require_verified_earnings: bool | None = None,
) -> dict[str, Any]:
    """Rank VCP + Thai swing candidates that pass Dual-Check hard gates."""
    snapshot = snapshot or {}
    if hold_style not in ("overnight", "intraday"):
        hold_style = "overnight"

    market = str(snapshot.get("market") or "").upper()
    if require_verified_earnings is None:
        require_verified_earnings = market in {"TH", "THA"}

    exposure = snapshot.get("exposure") if isinstance(snapshot.get("exposure"), Mapping) else {}
    recommendation = str((exposure or {}).get("recommendation") or "")
    regime_allowed = recommendation == "NEW_ENTRY_ALLOWED"

    canslim_by_symbol = _canslim_index(snapshot)
    rows = _candidate_rows(snapshot)
    # Overnight earnings lookups are expensive (yfinance/FMP). First pass every
    # candidate without network earnings; only look up symbols that clear the
    # remaining Dual-Check gates.
    defer_earnings = hold_style == "overnight" and earnings_lookup is not None
    evaluated: list[dict[str, Any]] = []
    for row in rows:
        evaluated.append(
            evaluate_candidate(
                row,
                regime_allowed=regime_allowed,
                hold_style=hold_style,
                canslim_by_symbol=canslim_by_symbol,
                earnings_lookup=None if defer_earnings else earnings_lookup,
                bars_lookup=bars_lookup,
                require_verified_earnings=require_verified_earnings,
                defer_earnings=defer_earnings,
            )
        )

    if defer_earnings:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        pending_idxs = [i for i, item in enumerate(evaluated) if not item.get("reject_reasons")]
        # Cap live earnings fan-out so ranked-candidates stays interactive.
        pending_idxs = pending_idxs[:12]

        def _fetch(symbol: str):
            try:
                return symbol, earnings_lookup(symbol) if earnings_lookup else None, None
            except Exception as exc:  # pragma: no cover - defensive
                return symbol, None, exc

        fetched: dict[str, tuple[Mapping[str, Any] | None, Exception | None]] = {}
        if pending_idxs and earnings_lookup is not None:
            with ThreadPoolExecutor(max_workers=min(6, len(pending_idxs))) as pool:
                futs = {
                    pool.submit(_fetch, str(evaluated[i].get("symbol") or "")): i
                    for i in pending_idxs
                }
                try:
                    for fut in as_completed(futs, timeout=45):
                        symbol, info, err = fut.result()
                        fetched[symbol] = (info, err)
                except TimeoutError:
                    # Mark unfinished symbols as timed out below via missing fetched entry.
                    pass

        checked = {str(evaluated[i].get("symbol") or "") for i in pending_idxs}
        for item in evaluated:
            symbol = str(item.get("symbol") or "")
            if item.get("reject_reasons"):
                item["gates"]["earnings"] = _gate(
                    "unavailable",
                    "Skipped earnings lookup; other Dual-Check gates already failed",
                )
                item["passed"] = False
                continue
            if symbol not in checked:
                item["gates"]["earnings"] = _gate(
                    "unavailable",
                    "Earnings lookup capped; open chart or refresh later",
                )
                item["reject_reasons"] = list(item.get("reject_reasons") or []) + [
                    "earnings_lookup_capped"
                ]
                item["passed"] = False
                continue
            info, err = fetched.get(symbol, (None, TimeoutError("earnings lookup timed out")))
            if err is not None and symbol not in fetched:
                item["gates"]["earnings"] = _gate(
                    "fail", "earnings lookup timed out", "earnings_lookup_error"
                )
                item["reject_reasons"] = list(item.get("reject_reasons") or []) + [
                    "earnings_lookup_error"
                ]
                item["passed"] = False
                continue
            if err is not None:
                item["gates"]["earnings"] = _gate(
                    "fail", f"earnings lookup error: {err}", "earnings_lookup_error"
                )
                item["reject_reasons"] = list(item.get("reject_reasons") or []) + [
                    "earnings_lookup_error"
                ]
                item["passed"] = False
                continue
            earnings_info = info
            days = None
            verified = False
            if isinstance(earnings_info, Mapping):
                item["earnings"] = dict(earnings_info)
                days = _number(earnings_info.get("days_to_earnings"))
                verified = bool(earnings_info.get("verified")) or bool(earnings_info.get("date"))
            if require_verified_earnings and not verified:
                item["gates"]["earnings"] = _gate(
                    "fail",
                    "earnings date unverified for overnight hold",
                    "earnings_unverified",
                )
                item["reject_reasons"] = list(item.get("reject_reasons") or []) + [
                    "earnings_unverified"
                ]
                item["passed"] = False
            elif days is None or days > EARNINGS_MIN_DAYS:
                detail = "no upcoming earnings" if days is None else f"earnings in {int(days)} days"
                if not verified and days is None:
                    detail = "no upcoming earnings (unverified)"
                item["gates"]["earnings"] = _gate("pass", detail)
                item["passed"] = not item.get("reject_reasons")
            else:
                item["gates"]["earnings"] = _gate(
                    "fail",
                    f"earnings in {int(days)} days",
                    "earnings_within_7_days",
                )
                item["reject_reasons"] = list(item.get("reject_reasons") or []) + [
                    "earnings_within_7_days"
                ]
                item["passed"] = False

    evaluated.sort(key=lambda item: item.get("composite_score") or 0.0, reverse=True)
    passed = [item for item in evaluated if item.get("passed")]
    rejected = [item for item in evaluated if not item.get("passed")]

    unavailable: set[str] = set()
    for item in evaluated:
        for name, gate in (item.get("gates") or {}).items():
            if isinstance(gate, Mapping) and gate.get("status") == "unavailable":
                unavailable.add(name)

    return {
        "schema_version": 2,
        "hold_style": hold_style,
        "regime_allowed": regime_allowed,
        "recommendation": recommendation or None,
        "blocked_reason": None if regime_allowed else "regime_not_new_entry_allowed",
        "require_verified_earnings": require_verified_earnings,
        "passed": passed,
        "rejected": rejected,
        "summary": {
            "evaluated": len(evaluated),
            "passed": len(passed),
            "rejected": len(rejected),
            "sources": {
                "vcp": sum(1 for c in evaluated if c.get("source") == "vcp"),
                "thai_swing": sum(
                    1 for c in evaluated if str(c.get("source") or "").startswith("thai_swing")
                ),
            },
        },
        "gates_unavailable": sorted(unavailable),
    }
