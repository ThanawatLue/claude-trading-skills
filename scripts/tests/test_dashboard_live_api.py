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


def test_run_stream_disables_proxy_buffering() -> None:
    with dashboard_app.app.test_request_context("/api/run/stream?market=TH"):
        response = dashboard_app.api_run_stream()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-cache, no-transform"
    assert response.headers["X-Accel-Buffering"] == "no"
