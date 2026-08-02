import sqlite3

from trading_core.sqlite import apply_migrations, connect_sqlite


def test_connection_has_safe_pragmas(tmp_path) -> None:
    with connect_sqlite(tmp_path / "db.sqlite") as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_migrations_are_idempotent_and_ordered(tmp_path) -> None:
    with connect_sqlite(tmp_path / "db.sqlite") as conn:
        migrations = {
            1: "CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL);",
            2: "CREATE INDEX idx_sample_value ON sample(value);",
        }
        assert apply_migrations(conn, "sample", migrations) == 2
        assert apply_migrations(conn, "sample", migrations) == 2
        assert (
            conn.execute("SELECT COUNT(*) FROM _trading_core_schema_migrations").fetchone()[0] == 2
        )


def test_connection_returns_sqlite_rows(tmp_path) -> None:
    with connect_sqlite(tmp_path / "db.sqlite") as conn:
        conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO sample(value) VALUES ('ok')")
        row = conn.execute("SELECT value FROM sample").fetchone()
        assert isinstance(row, sqlite3.Row)
        assert row["value"] == "ok"
