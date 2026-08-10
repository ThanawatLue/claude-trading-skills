"""Tests for Dual-Check pattern stats + ranking upgrades."""

from __future__ import annotations

from datetime import date, timedelta

from dashboard.services.dual_check_service import rank_candidates
from dashboard.services.pattern_stats import compute_confluence, compute_day_bias


def _bars(n: int = 80, *, weekday: int | None = None, bullish: bool = True) -> list[dict]:
    """Synthetic daily bars ending on a target weekday."""
    # Find a recent date matching weekday (Mon=0)
    end = date(2026, 8, 10)  # Monday
    if weekday is not None:
        while end.weekday() != weekday:
            end -= timedelta(days=1)
    out = []
    price = 100.0
    for i in range(n):
        d = end - timedelta(days=(n - 1 - i))
        # skip weekends roughly by still emitting weekdays only
        if d.weekday() >= 5:
            continue
        open_px = price
        close_px = price * (1.01 if bullish else 0.99)
        high = max(open_px, close_px) * 1.01
        low = min(open_px, close_px) * 0.99
        out.append(
            {
                "date": d.isoformat(),
                "open": open_px,
                "high": high,
                "low": low,
                "close": close_px,
                "volume": 1_000_000,
            }
        )
        price = close_px
    return out


def _vcp_row(
    symbol: str,
    *,
    score: float = 75.0,
    state: str = "Pre-breakout",
    distance: float = -1.0,
    rs: float = 85.0,
    stage2: bool = True,
) -> dict:
    return {
        "symbol": symbol,
        "composite_score": score,
        "execution_state": state,
        "distance_from_pivot_pct": distance,
        "relative_strength": {"rs_percentile": rs},
        "pivot_proximity": {"distance_from_pivot_pct": distance, "pivot_price": 100.0},
        "trend_template": {"passed": stage2, "score": 90 if stage2 else 40},
    }


def test_day_bias_overnight_vs_intraday_metrics() -> None:
    bars = _bars(120, weekday=0, bullish=True)
    overnight = compute_day_bias(bars, hold_style="overnight")
    intraday = compute_day_bias(bars, hold_style="intraday")
    assert overnight is not None and overnight["metric"] == "close_to_close"
    assert intraday is not None and intraday["metric"] == "open_to_close"
    assert overnight["count"] >= 5
    assert overnight["passes_threshold"] is True


def test_confluence_bullish_on_uptrend_bars() -> None:
    bars = _bars(220, weekday=0, bullish=True)
    conf = compute_confluence(bars)
    assert conf is not None
    assert conf["net_score"] >= 1
    assert conf["passes_threshold"] is True


def test_rank_applies_pattern_gates_when_bars_present() -> None:
    bars = _bars(220, weekday=0, bullish=True)
    snap = {
        "market": "US",
        "exposure": {"recommendation": "NEW_ENTRY_ALLOWED"},
        "vcp": {"results": [_vcp_row("AAPL")]},
    }
    out = rank_candidates(
        snap,
        hold_style="overnight",
        earnings_lookup=lambda _s: {
            "symbol": "AAPL",
            "date": "2026-09-01",
            "days_to_earnings": 20,
            "verified": True,
        },
        bars_lookup=lambda _s: bars,
        require_verified_earnings=False,
    )
    assert out["passed"]
    assert out["passed"][0]["gates"]["confluence"]["status"] == "pass"
    assert out["passed"][0]["gates"]["day_bias"]["status"] == "pass"
    assert out["passed"][0]["gates"]["stage2"]["status"] == "pass"
    assert "confluence" not in out["gates_unavailable"]


def test_rank_rejects_weak_confluence() -> None:
    bars = _bars(220, weekday=0, bullish=False)
    snap = {
        "market": "US",
        "exposure": {"recommendation": "NEW_ENTRY_ALLOWED"},
        "vcp": {"results": [_vcp_row("WEAK")]},
    }
    out = rank_candidates(
        snap,
        hold_style="intraday",
        bars_lookup=lambda _s: bars,
        require_verified_earnings=False,
    )
    # Bearish bars should fail confluence and/or day bias
    assert out["passed"] == []
    reasons = out["rejected"][0]["reject_reasons"]
    assert "confluence_weak" in reasons or "day_bias_weak" in reasons


def test_thai_swing_not_included_for_us_market() -> None:
    snap = {
        "market": "US",
        "exposure": {"recommendation": "NEW_ENTRY_ALLOWED"},
        "vcp": {"results": []},
        "thai_swing": {
            "dip_buy": [
                {
                    "symbol": "KBANK.BK",
                    "score": 90,
                    "price": 140,
                    "sma50": 135,
                    "plan": {"entry": 139},
                }
            ],
            "momentum": [],
        },
    }
    out = rank_candidates(snap, hold_style="intraday", require_verified_earnings=False)
    assert out["summary"]["evaluated"] == 0
    assert out["summary"]["sources"]["thai_swing"] == 0


def test_thai_swing_included_and_th_requires_verified_earnings() -> None:
    snap = {
        "market": "TH",
        "exposure": {"recommendation": "NEW_ENTRY_ALLOWED"},
        "vcp": {"results": []},
        "thai_swing": {
            "dip_buy": [
                {
                    "symbol": "KBANK.BK",
                    "score": 82,
                    "price": 140,
                    "sma50": 135,
                    "plan": {"entry": 139},
                }
            ],
            "momentum": [],
        },
    }
    # Unverified earnings → reject overnight on TH
    out = rank_candidates(
        snap,
        hold_style="overnight",
        earnings_lookup=lambda _s: {
            "symbol": "KBANK.BK",
            "date": None,
            "days_to_earnings": None,
            "verified": False,
        },
        bars_lookup=lambda _s: None,
        require_verified_earnings=True,
    )
    assert out["summary"]["sources"]["thai_swing"] == 1
    assert out["passed"] == []
    assert "earnings_unverified" in out["rejected"][0]["reject_reasons"]

    # Intraday skips earnings verification
    out2 = rank_candidates(
        snap,
        hold_style="intraday",
        earnings_lookup=lambda _s: None,
        bars_lookup=lambda _s: None,
        require_verified_earnings=True,
    )
    assert out2["passed"]
    assert out2["passed"][0]["source"].startswith("thai_swing")


def test_stage2_failure_rejects() -> None:
    snap = {
        "market": "US",
        "exposure": {"recommendation": "NEW_ENTRY_ALLOWED"},
        "vcp": {"results": [_vcp_row("BAD", stage2=False)]},
    }
    out = rank_candidates(snap, hold_style="intraday", require_verified_earnings=False)
    assert out["passed"] == []
    assert "stage2_failed" in out["rejected"][0]["reject_reasons"]
