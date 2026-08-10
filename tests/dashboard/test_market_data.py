"""Tests for dashboard market_data helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from dashboard.services.market_data import (
    annotate_snapshot,
    has_usable_breadth,
    normalize_market,
    resolve_exposure_breadth_key,
    resolve_step1_breadth,
    snapshot_freshness,
)


def test_normalize_market_aliases() -> None:
    assert normalize_market("us") == "US"
    assert normalize_market("USA") == "US"
    assert normalize_market("THA") == "TH"
    assert normalize_market("th") == "TH"
    assert normalize_market(None) == "US"
    assert normalize_market("") == "US"


def test_resolve_step1_breadth_us_falls_back_to_tv() -> None:
    tv = {"composite": {"score": 60}, "generated": "2026-08-10_04:00:00", "market": "US"}
    snapshot = {"breadth": None, "us_breadth_tv": tv, "thai_breadth": {"composite_score": 1}}
    resolved = resolve_step1_breadth(snapshot, "US")
    assert resolved is not None
    assert resolved["_step1_source"] == "us_breadth_tv"
    assert resolved["composite"]["composite_score"] == 60
    assert resolved["metadata"]["generated_at"].startswith("2026-08-10")


def test_resolve_step1_breadth_th_prefers_classic_then_tv() -> None:
    classic = {
        "composite": {"composite_score": 64.5},
        "metadata": {"generated_at": "2026-08-10T04:00:00Z"},
    }
    tv = {"composite_score": 55, "generated": "2026-08-09_10:00:00"}
    preferred = resolve_step1_breadth({"breadth": classic, "thai_breadth": tv}, "TH")
    assert preferred is not None
    assert preferred["_step1_source"] == "breadth"
    assert preferred["composite"]["composite_score"] == 64.5
    resolved = resolve_step1_breadth({"breadth": None, "thai_breadth": tv}, "TH")
    assert resolved is not None
    assert resolved["_step1_source"] == "thai_breadth"
    assert resolved["composite"]["composite_score"] == 55


def test_has_usable_breadth() -> None:
    assert has_usable_breadth({"composite": {"composite_score": 64.5}})
    assert has_usable_breadth({"composite": {"score": 59.9}})
    assert has_usable_breadth({"composite_score": 50})
    assert not has_usable_breadth(None)
    assert not has_usable_breadth({})


def test_snapshot_freshness_marks_stale_sources() -> None:
    now = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    fresh_at = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    stale_at = (now - timedelta(days=40)).isoformat().replace("+00:00", "Z")
    snapshot = {
        "breadth": {"metadata": {"generated_at": fresh_at}, "composite": {"composite_score": 60}},
        "ibd": {"market_distribution_state": {"as_of": "2026-06-30", "generated_at": stale_at}},
        "vcp": {"metadata": {"generated_at": fresh_at}},
        "exposure": {"generated_at": fresh_at, "recommendation": "NEW_ENTRY_ALLOWED"},
    }
    freshness = snapshot_freshness(snapshot, "US", now=now, stale_after_days=3)
    assert freshness["sources"]["step1_breadth"]["stale"] is False
    assert freshness["sources"]["ibd"]["stale"] is True
    assert freshness["any_critical_stale"] is True
    assert "ibd" in freshness["stale_sources"]


def test_annotate_snapshot_attaches_step1_and_freshness() -> None:
    tv = {
        "composite": {"score": 59.99, "regime": "Healthy Uptrend"},
        "generated": "2026-08-10_04:00:00",
        "market": "US",
    }
    snapshot = {"breadth": None, "us_breadth_tv": tv, "ibd": None, "vcp": None, "exposure": None}
    out = annotate_snapshot(snapshot, "USA")
    assert out["market"] == "US"
    assert out["_step1_breadth"]["_step1_source"] == "us_breadth_tv"
    assert "_freshness" in out
    assert has_usable_breadth(out["_step1_breadth"])


def test_resolve_exposure_breadth_key() -> None:
    assert resolve_exposure_breadth_key("TH") == ("thai_breadth", "breadth")
    assert resolve_exposure_breadth_key("US") == ("breadth", "us_breadth_tv")
