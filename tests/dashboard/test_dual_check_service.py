"""Tests for Dual-Check ranked candidate service."""

from __future__ import annotations

from dashboard.services.dual_check_service import rank_candidates


def _vcp_row(
    symbol: str,
    *,
    score: float = 75.0,
    state: str = "Pre-breakout",
    distance: float = -1.0,
    rs: float = 85.0,
) -> dict:
    return {
        "symbol": symbol,
        "composite_score": score,
        "execution_state": state,
        "distance_from_pivot_pct": distance,
        "relative_strength": {"rs_percentile": rs},
        "pivot_proximity": {"distance_from_pivot_pct": distance, "pivot_price": 100.0},
    }


def _snapshot(rows: list[dict], recommendation: str = "NEW_ENTRY_ALLOWED") -> dict:
    return {
        "market": "US",
        "exposure": {"recommendation": recommendation, "exposure_ceiling_pct": 70},
        "vcp": {"results": rows},
        "canslim": {"results": []},
    }


def test_rank_candidates_passes_dual_check_gates() -> None:
    snap = _snapshot(
        [
            _vcp_row("AAPL", score=88, distance=-1.5, rs=90),
            _vcp_row("MSFT", score=80, distance=1.0, rs=82),
        ]
    )
    out = rank_candidates(snap, hold_style="overnight", earnings_lookup=lambda _s: None)
    assert out["regime_allowed"] is True
    assert [c["symbol"] for c in out["passed"]] == ["AAPL", "MSFT"]
    assert out["passed"][0]["gates"]["confluence"]["status"] == "unavailable"
    assert out["passed"][0]["gates"]["day_bias"]["status"] == "unavailable"


def test_rank_candidates_blocks_when_regime_not_allowed() -> None:
    snap = _snapshot([_vcp_row("AAPL")], recommendation="CASH_PRIORITY")
    out = rank_candidates(snap, hold_style="overnight")
    assert out["regime_allowed"] is False
    assert out["passed"] == []
    assert out["blocked_reason"] == "regime_not_new_entry_allowed"
    assert all(c["gates"]["regime"]["status"] == "fail" for c in out["rejected"])


def test_rank_candidates_rejects_state_pivot_rs() -> None:
    snap = _snapshot(
        [
            _vcp_row("LAG", state="Pre-breakout", distance=-1.0, rs=45, score=90),
            _vcp_row("EXT", state="Overextended", distance=4.0, rs=95, score=89),
            _vcp_row("FAR", state="Pre-breakout", distance=-5.0, rs=90, score=88),
            _vcp_row("OK", state="Breakout", distance=2.0, rs=81, score=70),
        ]
    )
    out = rank_candidates(snap, hold_style="intraday")
    assert [c["symbol"] for c in out["passed"]] == ["OK"]
    reasons = {c["symbol"]: c["reject_reasons"] for c in out["rejected"]}
    assert "rs_below_80" in reasons["LAG"]
    assert "state_not_tradable" in reasons["EXT"]
    assert "pivot_out_of_band" in reasons["FAR"]


def test_rank_candidates_overnight_rejects_near_earnings() -> None:
    snap = _snapshot([_vcp_row("EARN"), _vcp_row("SAFE", score=71)])

    def lookup(symbol: str):
        if symbol == "EARN":
            return {"symbol": symbol, "days_to_earnings": 3, "date": "2026-08-13"}
        return {"symbol": symbol, "days_to_earnings": 20, "date": "2026-09-01"}

    out = rank_candidates(snap, hold_style="overnight", earnings_lookup=lookup)
    assert [c["symbol"] for c in out["passed"]] == ["SAFE"]
    earn = next(c for c in out["rejected"] if c["symbol"] == "EARN")
    assert "earnings_within_7_days" in earn["reject_reasons"]


def test_rank_candidates_intraday_skips_earnings_gate() -> None:
    snap = _snapshot([_vcp_row("EARN")])
    out = rank_candidates(
        snap,
        hold_style="intraday",
        earnings_lookup=lambda _s: {"days_to_earnings": 1},
    )
    assert [c["symbol"] for c in out["passed"]] == ["EARN"]
    assert out["passed"][0]["gates"]["earnings"]["status"] == "unavailable"


def test_rank_candidates_merges_canslim_rs_fallback() -> None:
    row = _vcp_row("AAA", rs=10, score=72)
    row["relative_strength"] = {}
    snap = _snapshot([row])
    snap["canslim"] = {
        "results": [
            {
                "symbol": "AAA",
                "composite_score": 75,
                "l_component": {"rs_rank_percentile": 88},
                "threshold_check": {"recommendation": "buy"},
            }
        ]
    }
    out = rank_candidates(snap, hold_style="intraday")
    assert [c["symbol"] for c in out["passed"]] == ["AAA"]
    assert out["passed"][0]["rs_percentile"] == 88
