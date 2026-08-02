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
    assert response.get_json() == {
        "market": "TH",
        "stored": None,
        "fresh": {"value": None},
    }
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
