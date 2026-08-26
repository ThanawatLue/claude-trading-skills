"""Tests for paper ↔ trader-memory bridge and setup invalidation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts import auto_paper, paper_memory_bridge, signal_ledger


def test_sync_open_skips_without_thesis(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        signal_ledger.register_signal(
            conn,
            signal_ledger.SignalRecord(
                signal_id="sig_1",
                symbol="AAPL",
                market="US",
                source_skill="vcp-screener",
                signal_date="2026-07-01",
                raw_score=80,
                entry_price=100,
                stop_price=95,
                target_price=110,
            ),
        )
        result = paper_memory_bridge.sync_open(
            conn,
            signal_id="sig_1",
            entry_price=100,
            entry_date="2026-07-01",
            shares=10,
            state_dir=tmp_path / "theses",
        )
    assert result["skipped"] is True
    assert result["reason"] == "no_thesis_id"


def test_auto_paper_attaches_memory_payload_on_open(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        signal_ledger.register_signal(
            conn,
            signal_ledger.SignalRecord(
                signal_id="sig_mem",
                symbol="AAPL",
                market="US",
                source_skill="vcp-screener",
                signal_date="2026-07-01",
                raw_score=80,
                entry_price=100,
                stop_price=95,
                target_price=110,
                thesis_id="th_demo",
            ),
        )
        opened = []

        def fake_open(**kwargs):
            opened.append(kwargs)
            return {"id": 9}

        with patch("scripts.paper_memory_bridge.sync_open", return_value={"ok": True}) as sync:
            result = auto_paper.run_auto_paper(
                conn,
                auto_paper.AutoPaperConfig(
                    market="US",
                    as_of=date(2026, 7, 1),
                    dry_run=False,
                    require_dual_check=False,
                    require_regime_gate=False,
                ),
                open_fn=fake_open,
            )
    assert result["opened"] == 1
    assert result["opened_links"][0]["memory"] == {"ok": True}
    sync.assert_called_once()
    assert opened[0]["symbol"] == "AAPL"


def test_invalidate_damaged_setup(tmp_path: Path, monkeypatch) -> None:
    import sys

    paper_dir = Path("skills/paper-trade-simulator/scripts").resolve()
    sys.path.insert(0, str(paper_dir))
    import paper_trade
    import update_marks

    monkeypatch.setattr(paper_trade, "DB_PATH", tmp_path / "paper.sqlite")
    # Force update_marks to use the same DB helper after path patch.
    monkeypatch.setattr(update_marks, "_db", paper_trade._db)

    with paper_trade._db() as conn:
        conn.executescript(signal_ledger.SCHEMA)
        signal_ledger.register_signal(
            conn,
            signal_ledger.SignalRecord(
                signal_id="sig_bad",
                symbol="AAPL",
                market="US",
                source_skill="vcp-screener",
                signal_date="2026-07-01",
                raw_score=80,
                entry_price=100,
                stop_price=95,
                target_price=110,
                payload={"execution_state": "Damaged"},
            ),
        )
        trade = paper_trade.open_position(
            symbol="AAPL",
            market="US",
            shares=10,
            entry=100,
            stop=95,
            target=110,
            source="vcp-screener",
        )
        auto_paper.link_signal_to_paper(conn, "sig_bad", int(trade["id"]))
        row = conn.execute("SELECT * FROM paper_trade WHERE id=?", (trade["id"],)).fetchone()

    result = update_marks.update_one(row, 99.0)
    assert result["action"] == "auto_closed_invalidated"
    assert result["state"] == "Damaged"
