import sqlite3

from scripts.reset_paper_portfolio import reset_paper_portfolio


def test_reset_archives_trades_and_links(tmp_path):
    db_path = tmp_path / "market_cache.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE paper_trade (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE signal_paper_link (
                signal_id TEXT PRIMARY KEY,
                paper_trade_id INTEGER NOT NULL,
                opened_at TEXT NOT NULL,
                mode TEXT NOT NULL
            );
            INSERT INTO paper_trade (symbol, market, status)
            VALUES ('GULF', 'TH', 'closed_manual'), ('KCE', 'TH', 'open');
            INSERT INTO signal_paper_link (signal_id, paper_trade_id, opened_at, mode)
            VALUES ('sig-1', 1, '2026-07-13T01:00:00+00:00', 'manual');
            """
        )

    result = reset_paper_portfolio(
        db_path,
        reset_label="test-reset",
        now="2026-07-13T09:00:00+00:00",
    )

    assert result["archived_trades"] == 2
    assert result["archived_links"] == 1
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM paper_trade").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM signal_paper_link").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM paper_trade_archive").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM signal_paper_link_archive").fetchone()[0] == 1
        session = conn.execute(
            "SELECT started_at, reset_label FROM paper_session WHERE id=1"
        ).fetchone()
        assert tuple(session) == ("2026-07-13T09:00:00+00:00", "test-reset")
