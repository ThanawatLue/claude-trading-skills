from dashboard import app as dashboard_app


def test_live_snapshot_prefers_fresh_report_values() -> None:
    stored = {
        "market": "TH",
        "vcp": {"metadata": {"generated_at": "old"}, "results": ["old"]},
        "legacy_only": {"value": 1},
    }
    fresh = {
        "vcp": {"metadata": {"generated_at": "new"}, "results": ["new"]},
        "legacy_only": None,
    }

    merged = dashboard_app._merge_live_snapshot(stored, fresh)

    assert merged["vcp"]["metadata"]["generated_at"] == "new"
    assert merged["vcp"]["results"] == ["new"]
    assert merged["legacy_only"] == {"value": 1}


def test_api_data_returns_standard_json_for_non_finite_values(monkeypatch) -> None:
    monkeypatch.setattr(
        dashboard_app,
        "db_load_run",
        lambda market, at=None: {"market": market, "stored": float("nan")},
    )
    monkeypatch.setattr(
        dashboard_app,
        "_collect_snapshot",
        lambda market: {"fresh": {"value": float("inf")}},
    )

    response = dashboard_app.app.test_client().get("/api/data?market=TH")

    assert response.status_code == 200
    body = response.get_json()
    assert body["market"] == "TH"
    assert body["stored"] is None
    assert body["fresh"] == {"value": None}
    assert "_step1_breadth" in body
    assert "_freshness" in body
    assert body["_freshness"]["market"] == "TH"
    assert b"NaN" not in response.data
    assert b"Infinity" not in response.data


def test_paper_list_normalizes_status_and_rejects_invalid(monkeypatch) -> None:
    calls = []

    def fake_list(status, market):
        calls.append((status, market))
        return [{"status": status, "market": market}]

    monkeypatch.setattr(dashboard_app, "paper_list", fake_list)
    client = dashboard_app.app.test_client()

    response = client.get("/api/paper/list?status=OPEN&market=th")
    assert response.status_code == 200
    assert calls == [("open", "th")]

    invalid = client.get("/api/paper/list?status=active")
    assert invalid.status_code == 400


def test_paper_fingerprint_endpoint_returns_profiles(monkeypatch) -> None:
    monkeypatch.setattr(
        dashboard_app,
        "paper_fingerprints",
        lambda market: {"market": market, "profiles": [{"symbol": "ABC.BK"}]},
    )

    response = dashboard_app.app.test_client().get("/api/paper/fingerprint?market=TH")

    assert response.status_code == 200
    assert response.get_json() == {"market": "TH", "profiles": [{"symbol": "ABC.BK"}]}


def test_decision_analytics_endpoint_reads_complete_signal_outcomes(monkeypatch, tmp_path) -> None:
    from scripts import signal_ledger

    db_path = tmp_path / "analytics.db"
    with signal_ledger.connect(db_path) as conn:
        signal_ledger.register_signal(
            conn,
            signal_ledger.SignalRecord(
                signal_id="sig_analytics",
                symbol="AAPL",
                source_skill="vcp-screener",
                signal_date="2026-01-01",
                market="US",
                raw_score=84,
                entry_price=100,
                stop_price=95,
                payload={"regime": "bull", "predicted_probability": 0.7},
            ),
        )
        conn.execute(
            """INSERT INTO signal_outcome
               (signal_id, horizon_days, evaluation_date, entry_close, close_price,
                high_price, low_price, return_pct, mae_pct, mfe_pct, theoretical_r, is_complete, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "sig_analytics",
                5,
                "2026-01-08",
                100,
                110,
                112,
                97,
                0.10,
                -0.03,
                0.12,
                2.0,
                1,
                "2026-01-08T00:00:00",
            ),
        )
        conn.commit()

    monkeypatch.setattr(dashboard_app, "DB_PATH", str(db_path))
    response = dashboard_app.app.test_client().get("/api/decision-analytics?market=US")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["analytics"]["status"] == "ok"
    assert payload["analytics"]["overall"]["expectancy_r"] == 2.0
    assert payload["analytics"]["regimes"][0]["label"] == "bull"


def test_jobs_latest_reports_never_run_without_confusing_health(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(dashboard_app, "DB_PATH", str(tmp_path / "db.sqlite"))

    response = dashboard_app.app.test_client().get(
        "/api/jobs/latest?job=daily_signal_pipeline&market=TH"
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "job_name": "daily_signal_pipeline",
        "market": "TH",
        "status": "never_run",
    }


def test_run_stream_disables_proxy_buffering() -> None:
    with dashboard_app.app.test_request_context("/api/run/stream?market=TH"):
        response = dashboard_app.api_run_stream()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-cache, no-transform"
    assert response.headers["X-Accel-Buffering"] == "no"


def test_arena_overview_endpoint(monkeypatch) -> None:
    client = dashboard_app.app.test_client()
    response = client.get("/api/arena/overview?market=TH")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "quant" in data
    assert "jules" in data
    assert data["quant"]["initial_capital"] == 30000.0
    assert data["jules"]["initial_capital"] == 30000.0
    assert "leader" in data
    assert "dna" in data["jules"]
    assert data["jules"]["dna"]["generation"] >= 1
    assert len(data["jules"]["dna"]["rules"]) >= 1


def test_build_exposure_cmd_th_includes_local_regime_and_sector_without_uptrend(
    monkeypatch, tmp_path
) -> None:
    reports = tmp_path / "reports"
    root = tmp_path
    reports.mkdir()

    th_mb = reports / "thai_market_breadth_2026-11-18_080000.json"
    th_mb.write_text('{"metadata": {"market": "TH"}, "composite_score": 40}', encoding="utf-8")
    th_sec = reports / "thai_sector_heatmap_2026-11-18_080000.json"
    th_sec.write_text('{"metadata": {"market": "TH"}, "sectors": []}', encoding="utf-8")
    set50_mb = root / "market_breadth_2026-11-18_080000.json"
    set50_mb.write_text(
        '{"metadata": {"market": "TH"}, "composite": {"composite_score": 52}}', encoding="utf-8"
    )
    # Also create a US-only uptrend file that TH must NOT touch
    us_up = reports / "uptrend_analysis_2026-11-18_080000.json"
    us_up.write_text('{"uptrend_score": 80}', encoding="utf-8")

    monkeypatch.setattr(dashboard_app, "REPORTS_DIR", str(reports))
    monkeypatch.setattr(dashboard_app, "ROOT_DIR", str(root))

    cmd = dashboard_app.build_exposure_cmd(str(th_mb), "TH")
    assert "--uptrend" not in cmd
    assert "--top-risk" not in cmd
    assert "--sector" in cmd
    assert str(th_sec) == cmd[cmd.index("--sector") + 1]
    assert "--regime" in cmd
    assert str(set50_mb) == cmd[cmd.index("--regime") + 1]
    assert str(us_up) not in cmd


def test_build_exposure_cmd_us_includes_regime_ftd_and_sector(monkeypatch, tmp_path) -> None:
    reports = tmp_path / "reports"
    root = tmp_path
    reports.mkdir()

    us_mb = root / "market_breadth_2026-11-18_080000.json"
    us_mb.write_text(
        '{"metadata": {"market": "US"}, "composite": {"composite_score": 55}}', encoding="utf-8"
    )
    us_up = reports / "uptrend_analysis_2026-11-18_080000.json"
    us_up.write_text('{"uptrend_score": 45}', encoding="utf-8")
    reg = reports / "macro_regime_2026-11-18_080000.json"
    reg.write_text(
        '{"metadata": {"market": "US"}, "regime": {"current_regime": "broadening"}}',
        encoding="utf-8",
    )
    ftd = reports / "ftd_detector_US_2026-11-18_080000.json"
    ftd.write_text(
        '{"metadata": {"market": "US"}, "market_state": {"combined_state": "FTD_CONFIRMED"}}',
        encoding="utf-8",
    )
    ibd = reports / "ibd_distribution_day_monitor_US_2026-11-18_080000.json"
    ibd.write_text(
        '{"metadata": {"market": "US"}, "market_distribution_state": {"overall_risk_level": "CAUTION"}}',
        encoding="utf-8",
    )
    sec = reports / "sector_rotation_2026-11-18.json"
    sec.write_text('{"groups": {"score": 54}}', encoding="utf-8")

    monkeypatch.setattr(dashboard_app, "REPORTS_DIR", str(reports))
    monkeypatch.setattr(dashboard_app, "ROOT_DIR", str(root))

    cmd = dashboard_app.build_exposure_cmd(str(us_mb), "US")
    for flag, expected in [
        ("--uptrend", us_up),
        ("--regime", reg),
        ("--top-risk", ibd),
        ("--ftd", ftd),
        ("--sector", sec),
    ]:
        assert flag in cmd
        assert str(expected) == cmd[cmd.index(flag) + 1]


def test_cleanup_old_files_preserves_both_th_and_us_postures(monkeypatch, tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(dashboard_app, "REPORTS_DIR", str(reports))
    monkeypatch.setattr(dashboard_app, "ROOT_DIR", str(tmp_path))

    # One US posture and three newer TH postures
    us_file = reports / "exposure_posture_US_2026-11-17_134000.json"
    us_file.write_text('{"market": "US"}', encoding="utf-8")
    for hr in ("10", "11", "12"):
        f = reports / f"exposure_posture_TH_2026-11-18_{hr}0000.json"
        f.write_text('{"market": "TH"}', encoding="utf-8")

    dashboard_app.cleanup_old_files(keep_count=1)
    assert us_file.exists()
    th_remaining = list(reports.glob("exposure_posture_TH_*.json"))
    assert len(th_remaining) == 1
