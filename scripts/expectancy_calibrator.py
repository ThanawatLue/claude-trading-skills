"""Advisory expectancy calibration for auto-paper source score gates.

Uses closed paper trades (and optionally ledger horizons) to suggest
min_score adjustments. Never auto-writes config unless explicitly applied
with a sample-size gate — calibration is advisory by default.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MIN_CLOSED_TRADES = 20
NEGATIVE_EXPECTANCY = 0.0
STRONG_EXPECTANCY = 0.4
SCORE_BUMP_ON_NEGATIVE = 5.0
SCORE_CUT_ON_STRONG = 2.0
SCORE_FLOOR = 60.0
SCORE_CEILING = 90.0


@dataclass(frozen=True)
class SourceCalibration:
    source: str
    closed_trades: int
    expectancy_r: float | None
    current_min_score: float
    suggested_min_score: float
    action: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "closed_trades": self.closed_trades,
            "expectancy_r": self.expectancy_r,
            "current_min_score": self.current_min_score,
            "suggested_min_score": self.suggested_min_score,
            "action": self.action,
            "reason": self.reason,
        }


def _expectancy_from_rows(rows: list[sqlite3.Row]) -> tuple[int, float | None]:
    closed = [r for r in rows if r["realized_r"] is not None]
    if not closed:
        return 0, None
    values = [float(r["realized_r"]) for r in closed]
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v <= 0]
    win_rate = len(wins) / len(values)
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    expectancy = win_rate * avg_win + (1.0 - win_rate) * avg_loss
    return len(values), round(expectancy, 4)


def paper_expectancy_by_source(
    conn: sqlite3.Connection, market: str | None = None
) -> dict[str, dict[str, Any]]:
    """Compute expectancy_r per paper source from closed trades."""
    where = "WHERE status != 'open' AND realized_r IS NOT NULL"
    params: list[Any] = []
    if market:
        where += " AND market = ?"
        params.append(market.upper())
    try:
        rows = conn.execute(
            f"""SELECT source, realized_r FROM paper_trade {where}""",
            params,
        ).fetchall()
    except sqlite3.OperationalError:
        return {}

    by_source: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        source = (row["source"] or "unknown").strip() or "unknown"
        by_source.setdefault(source, []).append(row)

    out: dict[str, dict[str, Any]] = {}
    for source, source_rows in by_source.items():
        n, exp = _expectancy_from_rows(source_rows)
        out[source] = {"closed_trades": n, "expectancy_r": exp}
    return out


def calibrate_source_rules(
    *,
    source_stats: Mapping[str, Mapping[str, Any]],
    source_rules: Mapping[str, Mapping[str, Any]] | None,
    default_min_score: float = 70.0,
    min_closed: int = MIN_CLOSED_TRADES,
) -> list[SourceCalibration]:
    """Return advisory min_score suggestions per source."""
    rules = source_rules or {}
    results: list[SourceCalibration] = []
    for source, stats in sorted(source_stats.items()):
        closed = int(stats.get("closed_trades") or 0)
        exp = stats.get("expectancy_r")
        current = float(rules.get(source, {}).get("min_score", default_min_score))
        if closed < min_closed:
            results.append(
                SourceCalibration(
                    source=source,
                    closed_trades=closed,
                    expectancy_r=float(exp) if exp is not None else None,
                    current_min_score=current,
                    suggested_min_score=current,
                    action="hold",
                    reason=f"sample {closed} < min_closed {min_closed}",
                )
            )
            continue
        if exp is None:
            results.append(
                SourceCalibration(
                    source=source,
                    closed_trades=closed,
                    expectancy_r=None,
                    current_min_score=current,
                    suggested_min_score=current,
                    action="hold",
                    reason="expectancy unavailable",
                )
            )
            continue
        exp_f = float(exp)
        if exp_f < NEGATIVE_EXPECTANCY:
            suggested = min(SCORE_CEILING, current + SCORE_BUMP_ON_NEGATIVE)
            action = "tighten" if suggested > current else "hold"
            reason = f"negative expectancy {exp_f:.3f}R"
        elif exp_f >= STRONG_EXPECTANCY:
            suggested = max(SCORE_FLOOR, current - SCORE_CUT_ON_STRONG)
            action = "ease" if suggested < current else "hold"
            reason = f"strong expectancy {exp_f:.3f}R"
        else:
            suggested = current
            action = "hold"
            reason = f"expectancy {exp_f:.3f}R within band"
        results.append(
            SourceCalibration(
                source=source,
                closed_trades=closed,
                expectancy_r=exp_f,
                current_min_score=current,
                suggested_min_score=suggested,
                action=action,
                reason=reason,
            )
        )
    return results


def apply_calibration_to_source_rules(
    source_rules: dict[str, dict[str, Any]],
    calibrations: list[SourceCalibration],
    *,
    apply_actions: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return a copy of source_rules with suggested min_score applied."""
    apply_actions = apply_actions or {"tighten"}
    updated = {k: dict(v) for k, v in source_rules.items()}
    for row in calibrations:
        if row.action not in apply_actions:
            continue
        if row.suggested_min_score == row.current_min_score:
            continue
        bucket = updated.setdefault(row.source, {})
        bucket["min_score"] = row.suggested_min_score
    return updated


def run_calibration(
    conn: sqlite3.Connection,
    *,
    market: str | None = None,
    source_rules: Mapping[str, Mapping[str, Any]] | None = None,
    default_min_score: float = 70.0,
    min_closed: int = MIN_CLOSED_TRADES,
    apply: bool = False,
) -> dict[str, Any]:
    stats = paper_expectancy_by_source(conn, market=market)
    calibrations = calibrate_source_rules(
        source_stats=stats,
        source_rules=source_rules,
        default_min_score=default_min_score,
        min_closed=min_closed,
    )
    applied_rules = None
    if apply:
        applied_rules = apply_calibration_to_source_rules(dict(source_rules or {}), calibrations)
    return {
        "market": market,
        "min_closed": min_closed,
        "apply": apply,
        "sources": [c.as_dict() for c in calibrations],
        "applied_source_rules": applied_rules,
    }


def write_calibration_report(result: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
