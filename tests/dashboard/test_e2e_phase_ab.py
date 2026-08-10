"""E2E acceptance checks for Dashboard Accuracy Refactor Phase A+B."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture()
def dash_env(tmp_path, monkeypatch):
    """Isolate dashboard I/O onto a temp tree and disable HF sync side effects."""
    import dashboard.app as dash_app
    import dashboard.hf_sync as hf_sync

    reports = tmp_path / "reports"
    root = tmp_path / "root"
    state = tmp_path / "state"
    reports.mkdir()
    root.mkdir()
    state.mkdir()

    monkeypatch.setattr(dash_app, "REPORTS_DIR", str(reports))
    monkeypatch.setattr(dash_app, "ROOT_DIR", str(root))
    monkeypatch.setattr(dash_app, "DB_PATH", str(state / "market_cache.db"))
    monkeypatch.setattr(dash_app, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(hf_sync, "download_db", lambda: None)
    monkeypatch.setattr(hf_sync, "upload_db", lambda: None)

    # Fresh sqlite schema for this temp DB
    from dashboard.db import connect_dashboard_db

    with connect_dashboard_db(state / "market_cache.db"):
        pass

    def write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    fresh = (datetime.now(UTC) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale = (datetime.now(UTC) - timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # US: classic breadth missing; TV breadth present
    write_json(
        reports / "us_market_breadth_tv_2026-08-10_120000.json",
        {
            "market": "US",
            "generated": "2026-08-10_12:00:00",
            "composite": {"score": 59.99, "regime": "Healthy Uptrend"},
            "metadata": {"market": "US", "generated_at": fresh},
        },
    )
    write_json(
        reports / "vcp_screener_2026-08-10_120000.json",
        {
            "metadata": {"market": "US", "generated_at": fresh},
            "results": [
                {
                    "symbol": "AAPL",
                    "composite_score": 78.0,
                    "execution_state": "Pre-breakout",
                    "distance_from_pivot_pct": -1.2,
                    "relative_strength": {"rs_percentile": 88},
                },
                {
                    "symbol": "LAGGY",
                    "composite_score": 90.0,
                    "execution_state": "Pre-breakout",
                    "distance_from_pivot_pct": -0.5,
                    "relative_strength": {"rs_percentile": 40},
                },
                {
                    "symbol": "EXTND",
                    "composite_score": 85.0,
                    "execution_state": "Overextended",
                    "distance_from_pivot_pct": 6.0,
                    "relative_strength": {"rs_percentile": 92},
                },
            ],
        },
    )
    write_json(
        reports / "exposure_posture_2026-08-10_120000.json",
        {
            "metadata": {"market": "US", "generated_at": fresh},
            "generated_at": fresh,
            "recommendation": "NEW_ENTRY_ALLOWED",
            "exposure_ceiling_pct": 70,
        },
    )
    write_json(
        reports / "ibd_distribution_day_monitor_2026-06-30.json",
        {
            "market_distribution_state": {
                "as_of": "2026-06-30",
                "generated_at": stale,
            },
            "portfolio_action": {"recommended_action": "HOLD"},
            "audit": {},
            "rule_evaluation": {},
        },
    )

    # TH: classic breadth + thai TV + exposure without US bleed fixture needs
    write_json(
        root / "market_breadth_2026-08-10_110000.json",
        {
            "metadata": {"market": "TH", "generated_at": fresh},
            "composite": {"composite_score": 64.5, "zone": "Healthy"},
            "components": {},
        },
    )
    write_json(
        reports / "thai_market_breadth_2026-08-10_110000.json",
        {
            "market": "TH",
            "generated": "2026-08-10_11:00:00",
            "composite_score": 58.0,
            "regime": "Neutral",
            "metadata": {"market": "TH", "generated_at": fresh},
        },
    )
    write_json(
        reports / "vcp_screener_th_2026-08-10_110000.json",
        {
            "metadata": {"market": "TH", "generated_at": fresh},
            "results": [
                {
                    "symbol": "KBANK.BK",
                    "composite_score": 72.0,
                    "execution_state": "Breakout",
                    "distance_from_pivot_pct": 1.5,
                    "relative_strength": {"rs_percentile": 81},
                }
            ],
        },
    )
    write_json(
        reports / "exposure_posture_th_2026-08-10_110000.json",
        {
            "metadata": {"market": "TH", "generated_at": fresh},
            "generated_at": fresh,
            "recommendation": "NEW_ENTRY_ALLOWED",
            "exposure_ceiling_pct": 67,
        },
    )

    # Avoid live earnings lookups during ranked-candidates E2E
    monkeypatch.setattr(
        dash_app,
        "_lookup_earnings",
        lambda symbol: {"symbol": symbol, "date": None, "days_to_earnings": None},
    )

    client = dash_app.app.test_client()
    return {
        "client": client,
        "app": dash_app,
        "reports": reports,
        "root": root,
        "fresh": fresh,
        "stale": stale,
    }


def test_e2e_health_advertises_ranked_candidates(dash_env) -> None:
    res = dash_env["client"].get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["features"]["ranked_candidates"] is True
    assert body["features"]["step1_breadth_fallback"] is True


def test_e2e_us_step1_falls_back_to_tv_breadth(dash_env) -> None:
    res = dash_env["client"].get("/api/data?market=USA")
    assert res.status_code == 200
    body = res.get_json()
    assert body["market"] == "US"
    assert body["breadth"] is None
    step1 = body["_step1_breadth"]
    assert step1 is not None
    assert step1["_step1_source"] == "us_breadth_tv"
    assert step1["composite"]["composite_score"] == pytest.approx(59.99)
    assert body["_freshness"]["sources"]["ibd"]["stale"] is True


def test_e2e_tha_alias_and_th_step1_classic(dash_env) -> None:
    res = dash_env["client"].get("/api/data?market=THA")
    assert res.status_code == 200
    body = res.get_json()
    assert body["market"] == "TH"
    assert body["_step1_breadth"]["_step1_source"] == "breadth"
    assert body["_step1_breadth"]["composite"]["composite_score"] == pytest.approx(64.5)


def test_e2e_ranked_candidates_filters_dual_check_gates(dash_env) -> None:
    res = dash_env["client"].get(
        "/api/ranked-candidates?market=US&hold_style=overnight&include_rejected=1"
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["market"] == "US"
    assert body["regime_allowed"] is True
    passed_symbols = [c["symbol"] for c in body["passed"]]
    assert passed_symbols == ["AAPL"]
    rejected = {c["symbol"]: c["reject_reasons"] for c in body["rejected"]}
    assert "rs_below_80" in rejected["LAGGY"]
    assert "state_not_tradable" in rejected["EXTND"]
    assert "confluence" in body["gates_unavailable"]
    assert "day_bias" in body["gates_unavailable"]


def test_e2e_th_ranked_candidates_pass(dash_env) -> None:
    res = dash_env["client"].get("/api/ranked-candidates?market=TH&hold_style=intraday")
    assert res.status_code == 200
    body = res.get_json()
    assert [c["symbol"] for c in body["passed"]] == ["KBANK.BK"]
    assert body["passed"][0]["gates"]["earnings"]["status"] == "unavailable"


def test_e2e_th_exposure_cmd_has_no_us_uptrend(dash_env, tmp_path) -> None:
    app = dash_env["app"]
    # Plant a fake US uptrend that would previously bleed into TH
    uptrend = dash_env["reports"] / "uptrend_analysis_2026-08-10.json"
    uptrend.write_text(json.dumps({"metadata": {"market": "US"}}), encoding="utf-8")
    thai_tv = str(dash_env["reports"] / "thai_market_breadth_2026-08-10_110000.json")
    cmd = app.build_exposure_cmd(thai_tv, "TH")
    assert "--uptrend" not in cmd
    assert "--top-risk" not in cmd
    assert "TH" in cmd


def test_e2e_index_includes_dual_check_markup(dash_env) -> None:
    res = dash_env["client"].get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "dualCheckSection" in html
    assert "freshnessBanner" in html
    assert "thBreadthProxyCard" in html
    assert "ranked-candidates" in html or "Dual-Check" in html
