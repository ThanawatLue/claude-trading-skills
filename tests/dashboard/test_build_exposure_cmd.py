"""Tests that TH exposure commands do not attach US-only inputs."""

from __future__ import annotations

from unittest.mock import patch

import dashboard.app as dash_app


def test_build_exposure_cmd_th_omits_uptrend_and_top_risk(tmp_path) -> None:
    breadth = tmp_path / "thai_market_breadth_x.json"
    breadth.write_text("{}", encoding="utf-8")
    with patch.object(dash_app, "latest_file_any", return_value=str(tmp_path / "uptrend.json")):
        cmd = dash_app.build_exposure_cmd(str(breadth), "THA")
    assert "--market" in cmd and "TH" in cmd
    assert "--breadth" in cmd and str(breadth) in cmd
    assert "--uptrend" not in cmd
    assert "--top-risk" not in cmd


def test_build_exposure_cmd_us_includes_uptrend_when_present(tmp_path) -> None:
    breadth = tmp_path / "market_breadth_x.json"
    breadth.write_text("{}", encoding="utf-8")
    uptrend = tmp_path / "uptrend_analysis_x.json"
    top = tmp_path / "market_top_x.json"

    def fake_latest(pattern: str):
        if "uptrend_analysis" in pattern:
            return str(uptrend)
        if "market_top" in pattern:
            return str(top)
        return None

    with patch.object(dash_app, "latest_file_any", side_effect=fake_latest):
        cmd = dash_app.build_exposure_cmd(str(breadth), "USA")
    assert "US" in cmd
    assert "--uptrend" in cmd and str(uptrend) in cmd
    assert "--top-risk" in cmd and str(top) in cmd
