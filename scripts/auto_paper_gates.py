"""Shared gates for auto-paper: Dual-Check, regime sizing, kill switch.

Keeps suggestion quality (dashboard Dual-Check) aligned with auto open decisions.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from dashboard.services.dual_check_service import evaluate_candidate

BarsLookup = Callable[[str], Sequence[Mapping[str, Any]] | None]
EarningsLookup = Callable[[str], Mapping[str, Any] | None]

DEFAULT_REGIME_POLICY: dict[str, dict[str, Any]] = {
    "NEW_ENTRY_ALLOWED": {"allow_open": True, "risk_scale": 1.0},
    "REDUCE_ONLY": {"allow_open": True, "risk_scale": 0.5},
    "CASH_PRIORITY": {"allow_open": False, "risk_scale": 0.0},
}


def is_kill_switch_active(
    *,
    enabled: bool = True,
    kill_switch: bool = False,
) -> bool:
    """Return True when automation must not open new paper positions."""
    return bool(kill_switch) or not bool(enabled)


def resolve_regime_policy(
    recommendation: str | None,
    policy: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve allow_open / risk_scale for an exposure recommendation."""
    table = {**DEFAULT_REGIME_POLICY, **(dict(policy) if policy else {})}
    key = str(recommendation or "").strip().upper()
    if not key:
        return {
            "recommendation": None,
            "allow_open": False,
            "risk_scale": 0.0,
            "reason": "regime_missing",
        }
    row = table.get(key)
    if row is None:
        return {
            "recommendation": key,
            "allow_open": False,
            "risk_scale": 0.0,
            "reason": "regime_unknown",
        }
    return {
        "recommendation": key,
        "allow_open": bool(row.get("allow_open", False)),
        "risk_scale": float(row.get("risk_scale", 0.0)),
        "reason": None if row.get("allow_open", False) else f"regime_{key.lower()}",
    }


def map_signal_to_dual_row(
    symbol: str,
    raw_score: float | None,
    source_skill: str | None,
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize a ledger payload into Dual-Check candidate shape."""
    payload = dict(payload or {})
    raw = payload.get("raw_provenance")
    if isinstance(raw, Mapping):
        # Thesis ingest wraps screener fields under raw_provenance.
        merged = {**raw, **payload}
    else:
        merged = payload

    row = dict(merged)
    row["symbol"] = symbol
    if raw_score is not None and row.get("composite_score") is None:
        row["composite_score"] = raw_score

    source = str(row.get("_dual_source") or row.get("source") or source_skill or "")
    if source.startswith("thai-swing") or source.startswith("thai_swing"):
        bucket = "momentum" if "momentum" in source else "dip"
        row.setdefault("_dual_source", f"thai_swing_{bucket}")
        row.setdefault("source", row["_dual_source"])
        if not row.get("execution_state"):
            row["execution_state"] = "Breakout" if bucket == "momentum" else "Pre-breakout"
    elif "vcp" in source.lower():
        row.setdefault("_dual_source", "vcp")
        row.setdefault("source", "vcp")

    return row


def bars_lookup_from_conn(conn: sqlite3.Connection) -> BarsLookup:
    """Build a Dual-Check bars lookup from the shared market cache DB."""

    def lookup(symbol: str) -> list[dict[str, Any]] | None:
        candidates = [symbol, symbol.replace(".BK", ""), f"{symbol}.BK"]
        seen: set[str] = set()
        for key in candidates:
            key = key.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            try:
                rows = conn.execute(
                    """SELECT date, open, high, low, close, volume
                       FROM price_bar
                       WHERE symbol = ?
                       ORDER BY date ASC""",
                    (key,),
                ).fetchall()
            except sqlite3.OperationalError:
                return None
            if rows:
                return [dict(r) for r in rows]
        return None

    return lookup


def evaluate_signal_dual_check(
    *,
    symbol: str,
    raw_score: float | None,
    source_skill: str | None,
    payload: Mapping[str, Any] | None,
    regime_allowed: bool,
    hold_style: str = "overnight",
    bars_lookup: BarsLookup | None = None,
    earnings_lookup: EarningsLookup | None = None,
    require_verified_earnings: bool = False,
    canslim_by_symbol: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run Dual-Check hard gates for one ledger signal."""
    row = map_signal_to_dual_row(symbol, raw_score, source_skill, payload)
    result = evaluate_candidate(
        row,
        regime_allowed=regime_allowed,
        hold_style="intraday" if hold_style == "intraday" else "overnight",
        canslim_by_symbol=canslim_by_symbol or {},
        earnings_lookup=earnings_lookup,
        bars_lookup=bars_lookup,
        require_verified_earnings=require_verified_earnings,
        defer_earnings=False,
    )
    return result


def load_regime_recommendation(
    reports_dir: str | Path,
    market: str | None = None,
) -> str | None:
    """Load latest exposure_posture_*.json recommendation if present."""
    root = Path(reports_dir)
    if not root.exists():
        return None
    files = sorted(root.glob("exposure_posture_*.json"), key=lambda p: p.stat().st_mtime)
    if market:
        market_u = market.upper()
        market_files = [
            p
            for p in files
            if market_u in p.name.upper() or _json_market(p) in {market_u, market_u[:2]}
        ]
        if market_files:
            files = market_files
    if not files:
        return None
    try:
        data = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    rec = data.get("recommendation")
    return str(rec) if rec else None


def _json_market(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if isinstance(data, dict):
        return str(data.get("market") or "").upper()
    return ""
