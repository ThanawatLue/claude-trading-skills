"""Market-scoped snapshot helpers for the trading dashboard.

Normalizes US/TH aliases, resolves Step-1 breadth fallbacks (classic → TV),
and computes freshness metadata for UI banners.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

UTC = timezone.utc

_MARKET_ALIASES = {
    "US": "US",
    "USA": "US",
    "TH": "TH",
    "THA": "TH",
}

_CRITICAL_SOURCES_US = ("step1_breadth", "exposure", "vcp", "ibd")
_CRITICAL_SOURCES_TH = ("step1_breadth", "exposure", "vcp")


def _critical_sources_for(market: str) -> tuple[str, ...]:
    return _CRITICAL_SOURCES_US if normalize_market(market) == "US" else _CRITICAL_SOURCES_TH


def normalize_market(value: str | None, default: str = "US") -> str:
    """Map USA/THA (and lowercase) onto canonical US/TH codes."""
    if value is None or str(value).strip() == "":
        return _MARKET_ALIASES.get(default.upper(), "US")
    key = str(value).strip().upper()
    if key in _MARKET_ALIASES:
        return _MARKET_ALIASES[key]
    return _MARKET_ALIASES.get(default.upper(), "US")


def has_usable_breadth(payload: dict[str, Any] | None) -> bool:
    """True when a breadth payload has a scorable composite."""
    if not isinstance(payload, dict):
        return False
    composite = payload.get("composite")
    if isinstance(composite, dict):
        for key in ("composite_score", "score"):
            if _finite_number(composite.get(key)) is not None:
                return True
        if composite.get("regime"):
            return True
    if _finite_number(payload.get("composite_score")) is not None:
        return True
    if payload.get("regime"):
        return True
    return False


def normalize_breadth_for_step1(
    payload: dict[str, Any] | None,
    *,
    source: str | None = None,
) -> dict[str, Any] | None:
    """Adapt classic/TV breadth shapes into the Step-1 UI contract."""
    if not has_usable_breadth(payload):
        return None
    assert isinstance(payload, dict)
    out = dict(payload)
    composite_in = payload.get("composite") if isinstance(payload.get("composite"), dict) else {}
    composite = dict(composite_in or {})
    score = (
        _finite_number(composite.get("composite_score"))
        or _finite_number(composite.get("score"))
        or _finite_number(payload.get("composite_score"))
    )
    if score is not None:
        composite["composite_score"] = score
        composite.setdefault("score", score)
    zone = composite.get("zone") or composite.get("regime") or payload.get("regime") or "Unknown"
    composite.setdefault("zone", zone)
    out["composite"] = composite

    meta = dict(payload.get("metadata") or {}) if isinstance(payload.get("metadata"), dict) else {}
    generated = meta.get("generated_at") or payload.get("generated_at") or payload.get("generated")
    if generated and not meta.get("generated_at"):
        meta["generated_at"] = str(generated).replace("_", "T", 1)
    if meta:
        out["metadata"] = meta
    if source:
        out["_step1_source"] = source
    return out


def resolve_step1_breadth(snapshot: dict[str, Any] | None, market: str) -> dict[str, Any] | None:
    """Pick classic breadth first, then market-local TV breadth."""
    market = normalize_market(market)
    snapshot = snapshot or {}
    classic = snapshot.get("breadth")
    if has_usable_breadth(classic if isinstance(classic, dict) else None):
        return normalize_breadth_for_step1(classic, source="breadth")

    fallback_key = "us_breadth_tv" if market == "US" else "thai_breadth"
    fallback = snapshot.get(fallback_key)
    if has_usable_breadth(fallback if isinstance(fallback, dict) else None):
        return normalize_breadth_for_step1(fallback, source=fallback_key)
    return None


def resolve_exposure_breadth_key(market: str) -> tuple[str, ...]:
    """Ordered snapshot keys to use as exposure --breadth input."""
    market = normalize_market(market)
    if market == "TH":
        return ("thai_breadth", "breadth")
    return ("breadth", "us_breadth_tv")


def resolve_exposure_breadth_path_keys(market: str) -> tuple[str, ...]:
    """Ordered filename globs (basename patterns) for exposure --breadth files."""
    market = normalize_market(market)
    if market == "TH":
        return ("thai_market_breadth_*.json", "market_breadth_20*-*.json")
    return ("market_breadth_20*-*.json", "us_market_breadth_tv_*.json")


def _finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).strip()
    if not text:
        return None
    # Support "YYYY-MM-DD_HH:MM:SS" TV style and space-separated legacy
    text = text.replace("_", "T", 1).replace(" ", "T", 1)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    elif len(text) == 19 and "T" in text:
        text = text + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        # date-only
        try:
            parsed = datetime.fromisoformat(text[:10]).replace(tzinfo=UTC)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def extract_generated_at(payload: dict[str, Any] | None) -> datetime | None:
    """Best-effort generation timestamp from common report shapes."""
    if not isinstance(payload, dict):
        return None
    candidates: list[Any] = [
        payload.get("generated_at"),
        payload.get("generated"),
        (payload.get("metadata") or {}).get("generated_at")
        if isinstance(payload.get("metadata"), dict)
        else None,
        (payload.get("market_distribution_state") or {}).get("generated_at")
        if isinstance(payload.get("market_distribution_state"), dict)
        else None,
        (payload.get("market_distribution_state") or {}).get("as_of")
        if isinstance(payload.get("market_distribution_state"), dict)
        else None,
    ]
    for value in candidates:
        parsed = _parse_timestamp(value)
        if parsed is not None:
            return parsed
    return None


def snapshot_freshness(
    snapshot: dict[str, Any] | None,
    market: str,
    *,
    now: datetime | None = None,
    stale_after_days: int = 3,
) -> dict[str, Any]:
    """Compute per-source age and stale flags for critical dashboard inputs."""
    market = normalize_market(market)
    snapshot = snapshot or {}
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    step1 = resolve_step1_breadth(snapshot, market)
    source_payloads = {
        "step1_breadth": step1,
        "exposure": snapshot.get("exposure")
        if isinstance(snapshot.get("exposure"), dict)
        else None,
        "vcp": snapshot.get("vcp") if isinstance(snapshot.get("vcp"), dict) else None,
        "ibd": snapshot.get("ibd") if isinstance(snapshot.get("ibd"), dict) else None,
    }

    sources: dict[str, Any] = {}
    stale_sources: list[str] = []
    for name in _critical_sources_for(market):
        payload = source_payloads.get(name)
        generated_at = extract_generated_at(payload)
        age_days: float | None = None
        stale = False
        missing = payload is None
        if generated_at is not None:
            age_days = max(0.0, (now - generated_at).total_seconds() / 86400.0)
            stale = age_days > float(stale_after_days)
        elif not missing and name == "ibd":
            # IBD without timestamp is treated conservatively as stale
            stale = True
        sources[name] = {
            "missing": missing,
            "generated_at": generated_at.isoformat().replace("+00:00", "Z")
            if generated_at
            else None,
            "age_days": round(age_days, 2) if age_days is not None else None,
            "stale": stale,
            "stale_after_days": stale_after_days,
        }
        if stale:
            stale_sources.append(name)

    return {
        "market": market,
        "as_of": now.isoformat().replace("+00:00", "Z"),
        "stale_after_days": stale_after_days,
        "sources": sources,
        "stale_sources": stale_sources,
        "any_critical_stale": bool(stale_sources),
    }


def annotate_snapshot(
    snapshot: dict[str, Any] | None,
    market: str,
    *,
    now: datetime | None = None,
    stale_after_days: int = 3,
) -> dict[str, Any]:
    """Return a shallow-copied snapshot with market, Step-1, and freshness fields."""
    market = normalize_market(market)
    out = dict(snapshot or {})
    out["market"] = market
    step1 = resolve_step1_breadth(out, market)
    out["_step1_breadth"] = step1
    out["_freshness"] = snapshot_freshness(out, market, now=now, stale_after_days=stale_after_days)
    return out
