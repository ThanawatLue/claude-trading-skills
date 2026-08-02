from dashboard.db import connect_dashboard_db


def test_dashboard_db_uses_shared_schema_migrations(tmp_path) -> None:
    with connect_dashboard_db(tmp_path / "db.sqlite") as conn:
        conn.execute("INSERT INTO analysis_run(market, run_at, data) VALUES ('US', 'now', '{}')")
        assert conn.execute("SELECT COUNT(*) FROM analysis_run").fetchone()[0] == 1
        assert (
            conn.execute(
                "SELECT version FROM _trading_core_schema_migrations WHERE namespace='dashboard'"
            ).fetchone()[0]
            == 1
        )
