from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from scripts import auto_paper, signal_ledger


def _register(
    conn: sqlite3.Connection,
    signal_id: str = "sig_a",
    symbol: str = "AAPL",
    score: float = 80,
    signal_date: str = "2026-07-01",
    entry: float = 100,
    stop: float | None = None,
    target: float | None = None,
    source: str = "vcp-screener",
) -> None:
    signal_ledger.register_signal(
        conn,
        signal_ledger.SignalRecord(
            signal_id=signal_id,
            symbol=symbol,
            market="US",
            source_skill=source,
            signal_date=signal_date,
            raw_score=score,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
        ),
    )


def test_eligible_signals_derives_missing_risk(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn)
        config = auto_paper.AutoPaperConfig(
            market="US", min_score=70, as_of=date(2026, 7, 1), dry_run=True
        )

        candidates = auto_paper.eligible_signals(conn, config)

    assert len(candidates) == 1
    assert candidates[0]["entry"] == 100
    assert candidates[0]["stop"] == 92
    assert candidates[0]["target"] == 116


def test_source_rules_cap_stop_and_target(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(
            conn,
            source="thai-swing-momentum",
            entry=100,
            stop=94,
            target=112,
        )
        config = auto_paper.AutoPaperConfig(
            market="US",
            min_score=70,
            as_of=date(2026, 7, 1),
            dry_run=True,
            source_rules={"thai-swing-momentum": {"target_r": 0.9, "stop_pct_cap": 4.0}},
        )

        candidates = auto_paper.eligible_signals(conn, config)

    assert len(candidates) == 1
    assert candidates[0]["stop"] == 96
    assert candidates[0]["target"] == 103.6


def test_run_auto_paper_dry_run_does_not_open(tmp_path: Path) -> None:
    calls = []

    def fake_open(**kwargs):
        calls.append(kwargs)
        return {"id": 123}

    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn)
        config = auto_paper.AutoPaperConfig(
            market="US", min_score=70, as_of=date(2026, 7, 1), dry_run=True
        )
        result = auto_paper.run_auto_paper(conn, config, open_fn=fake_open)
        links = conn.execute("SELECT * FROM signal_paper_link").fetchall()

    assert result["eligible"] == 1
    assert result["opened"] == 0
    assert calls == []
    assert links == []


def test_run_auto_paper_execute_links_signal(tmp_path: Path) -> None:
    calls = []

    def fake_open(**kwargs):
        calls.append(kwargs)
        return {"id": 123}

    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn)
        config = auto_paper.AutoPaperConfig(
            market="US", min_score=70, as_of=date(2026, 7, 1), dry_run=False
        )
        result = auto_paper.run_auto_paper(conn, config, open_fn=fake_open)
        second = auto_paper.run_auto_paper(conn, config, open_fn=fake_open)
        links = conn.execute("SELECT * FROM signal_paper_link").fetchall()

    assert result["opened"] == 1
    assert second["eligible"] == 0
    assert len(calls) == 1
    assert calls[0]["symbol"] == "AAPL"
    assert calls[0]["stop"] == 92
    assert len(links) == 1
    assert links[0]["paper_trade_id"] == 123


def test_eligible_signals_dedupes_same_symbol_within_batch(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(
            conn,
            signal_id="sig_a_new",
            symbol="AAPL",
            score=82,
            signal_date="2026-07-02",
        )
        _register(
            conn,
            signal_id="sig_a_old",
            symbol="AAPL",
            score=82,
            signal_date="2026-07-01",
        )
        _register(
            conn,
            signal_id="sig_m",
            symbol="MSFT",
            score=80,
            signal_date="2026-07-01",
        )
        config = auto_paper.AutoPaperConfig(
            market="US",
            min_score=70,
            max_new_positions=3,
            as_of=date(2026, 7, 2),
            dry_run=True,
        )

        candidates = auto_paper.eligible_signals(conn, config)
        diagnostics = auto_paper.explain_candidates(conn, config)

    assert [row["symbol"] for row in candidates] == ["AAPL", "MSFT"]
    skipped = {row["signal_id"]: row["reasons"] for row in diagnostics["skipped"]}
    assert "symbol already selected this run" in skipped["sig_a_old"]


def test_high_score_override_can_exceed_soft_open_cap(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        import sys

        sys.path.insert(0, str(auto_paper.PAPER_SCRIPT_DIR))
        try:
            import paper_trade

            conn.executescript(paper_trade.SCHEMA)
            conn.execute(
                """INSERT INTO paper_trade
                   (symbol, market, side, status, entry_price, entry_at, shares,
                    stop_price, target_price, initial_risk)
                   VALUES ('MSFT', 'US', 'long', 'open', 100, '2026-07-01T00:00:00+00:00',
                           1, 95, 110, 5)"""
            )
        finally:
            if str(auto_paper.PAPER_SCRIPT_DIR) in sys.path:
                sys.path.remove(str(auto_paper.PAPER_SCRIPT_DIR))
        _register(conn, signal_id="sig_high", symbol="AAPL", score=90, signal_date="2026-07-01")
        _register(conn, signal_id="sig_normal", symbol="NVDA", score=80, signal_date="2026-07-01")
        config = auto_paper.AutoPaperConfig(
            market="US",
            min_score=70,
            max_open_positions=1,
            high_score_override_min=85,
            max_open_positions_with_override=2,
            as_of=date(2026, 7, 1),
            dry_run=True,
        )

        candidates = auto_paper.eligible_signals(conn, config)

    assert [row["symbol"] for row in candidates] == ["AAPL"]


def test_stale_signal_is_not_eligible(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, signal_date="2026-05-25")
        config = auto_paper.AutoPaperConfig(
            market="US", min_score=70, max_age_days=10, as_of=date(2026, 7, 1)
        )

        candidates = auto_paper.eligible_signals(conn, config)

    assert candidates == []


def test_explain_candidates_reports_selected_and_skipped_reasons(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, signal_id="sig_top", symbol="AAPL", score=80, signal_date="2026-07-01")
        _register(conn, signal_id="sig_low", symbol="MSFT", score=60, signal_date="2026-07-01")
        _register(conn, signal_id="sig_old", symbol="NVDA", score=90, signal_date="2026-05-01")
        config = auto_paper.AutoPaperConfig(
            market="US",
            min_score=70,
            max_age_days=10,
            max_new_positions=1,
            as_of=date(2026, 7, 1),
        )

        diagnostics = auto_paper.explain_candidates(conn, config)

    assert [row["symbol"] for row in diagnostics["selected"]] == ["AAPL"]
    skipped = {row["symbol"]: row["reasons"] for row in diagnostics["skipped"]}
    assert any("score 60.0 < 70" in reason for reason in skipped["MSFT"])
    assert any("age" in reason for reason in skipped["NVDA"])
