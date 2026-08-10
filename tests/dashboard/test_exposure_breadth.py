"""Tests for exposure breadth path resolution helpers."""

from __future__ import annotations

from dashboard.services.market_data import resolve_exposure_breadth_path_keys


def test_exposure_breadth_path_keys_th_prefers_thai_tv() -> None:
    assert resolve_exposure_breadth_path_keys("TH") == (
        "thai_market_breadth_*.json",
        "market_breadth_20*-*.json",
    )


def test_exposure_breadth_path_keys_us_prefers_classic_then_tv() -> None:
    assert resolve_exposure_breadth_path_keys("USA") == (
        "market_breadth_20*-*.json",
        "us_market_breadth_tv_*.json",
    )
