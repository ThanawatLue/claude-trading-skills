from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import yaml

from scripts import signal_ledger


def _insert_bars(conn: sqlite3.Connection, symbol: str, closes: list[float]) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS price_bar (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, date)
        )"""
    )
    rows = []
    for i, close in enumerate(closes, start=1):
        rows.append(
            (
                symbol,
                f"2026-01-{i:02d}",
                close,
                close + 1,
                close - 1,
                close,
                1000,
                "2026-01-01T00:00:00",
            )
        )
    conn.executemany(
        """INSERT INTO price_bar
           (symbol, date, open, high, low, close, volume, fetched_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()


def test_ingest_theses_registers_deduplicated_signals(tmp_path: Path) -> None:
    db_path = tmp_path / "market_cache.db"
    theses_dir = tmp_path / "theses"
    theses_dir.mkdir()
    thesis = {
        "thesis_id": "th_abc",
        "ticker": "AAPL",
        "created_at": "2026-01-01T09:00:00+00:00",
        "thesis_type": "pivot_breakout",
        "status": "IDEA",
        "entry": {"target_price": None},
        "exit": {"stop_loss": 95.0, "take_profit": 115.0},
        "origin": {
            "skill": "vcp-screener",
            "output_file": "reports/vcp.json",
            "screening_score": 82.5,
            "screening_grade": "Strong VCP",
            "raw_provenance": {"symbol": "AAPL", "price": 100.0},
        },
    }
    (theses_dir / "th_aapl.yaml").write_text(yaml.safe_dump(thesis), encoding="utf-8")

    with signal_ledger.connect(db_path) as conn:
        first = signal_ledger.ingest_theses(conn, theses_dir)
        second = signal_ledger.ingest_theses(conn, theses_dir)
        rows = conn.execute("SELECT * FROM signal_ledger").fetchall()

    assert first == {"total": 1, "inserted": 1, "updated": 0, "skipped": 0}
    assert second == {"total": 1, "inserted": 0, "updated": 1, "skipped": 0}
    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["entry_price"] == 100.0
    assert rows[0]["stop_price"] == 95.0
    assert rows[0]["target_price"] == 115.0


def test_ingest_signal_files_accepts_canonical_json_and_aliases(tmp_path: Path) -> None:
    db_path = tmp_path / "market_cache.db"
    signal_file = tmp_path / "signals.json"
    signal_file.write_text(
        json.dumps(
            {
                "signals": [
                    {
                        "symbol": "AAPL",
                        "source": "vcp",
                        "signal_date": "2026-07-01",
                        "raw_score": 81.5,
                        "entry_price": 100,
                        "stop_price": 95,
                        "target_price": 110,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with signal_ledger.connect(db_path) as conn:
        result = signal_ledger.ingest_signal_files(conn, [signal_file])
        row = conn.execute("SELECT * FROM signal_ledger").fetchone()

    assert result == {"files": 1, "total": 1, "inserted": 1, "updated": 0, "skipped": 0}
    assert row["source_skill"] == "vcp-screener"
    assert row["symbol"] == "AAPL"
    assert row["raw_score"] == 81.5


def test_signals_from_thai_swing_report_uses_plan_risk(tmp_path: Path) -> None:
    report = tmp_path / "thai_swing_2026-07-01.json"
    report.write_text(
        json.dumps(
            {
                "generated": "2026-07-01T17:00:00",
                "metadata": {"market": "TH"},
                "dip_buy": [
                    {
                        "symbol": "AH.BK",
                        "score": 79.3,
                        "price": 13.9,
                        "plan": {"entry": 13.9, "stop": 13.59, "target": 14.52},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    signals = signal_ledger.signals_from_file(report)

    assert len(signals) == 1
    assert signals[0].source_skill == "thai-swing-dip"
    assert signals[0].market == "TH"
    assert signals[0].entry_price == 13.9
    assert signals[0].stop_price == 13.59
    assert signals[0].target_price == 14.52


def test_update_outcomes_from_cached_bars(tmp_path: Path) -> None:
    db_path = tmp_path / "market_cache.db"
    with signal_ledger.connect(db_path) as conn:
        signal = signal_ledger.SignalRecord(
            signal_id="sig_test",
            symbol="AAPL",
            source_skill="vcp-screener",
            signal_date="2026-01-01",
            market="US",
            entry_price=100.0,
            stop_price=96.0,
            target_price=106.0,
        )
        signal_ledger.register_signal(conn, signal)
        _insert_bars(conn, "AAPL", [100, 101, 103, 105, 107, 104, 108])

        result = signal_ledger.update_outcomes(conn, horizons=(5,), market="US")
        row = conn.execute(
            "SELECT * FROM signal_outcome WHERE signal_id = ? AND horizon_days = 5",
            ("sig_test",),
        ).fetchone()

    assert result == {"signals": 1, "outcomes_updated": 1, "complete_outcomes": 1}
    assert row["evaluation_date"] == "2026-01-06"
    assert row["close_price"] == 104.0
    assert row["return_pct"] == 0.04
    assert row["hit_target"] == 1
    assert row["hit_stop"] == 0
    assert row["theoretical_r"] == 1.0


def test_outcome_summary_groups_by_source_and_horizon(tmp_path: Path) -> None:
    db_path = tmp_path / "market_cache.db"
    with signal_ledger.connect(db_path) as conn:
        signal_ledger.register_signal(
            conn,
            signal_ledger.SignalRecord(
                signal_id="sig_a",
                symbol="AAPL",
                source_skill="vcp-screener",
                signal_date="2026-01-01",
                market="US",
                entry_price=100,
                stop_price=95,
            ),
        )
        _insert_bars(conn, "AAPL", [100, 101, 102, 103, 104, 105, 106])
        signal_ledger.update_outcomes(conn, horizons=(5,), market="US")

        summary = signal_ledger.outcome_summary(conn, market="US")
        counts = signal_ledger.get_signal_counts(conn, market="US")
        metrics = signal_ledger.source_metrics(conn, market="US")

    assert counts["total"] == 1
    assert counts["completed_signals"] == 1
    assert counts["by_source"] == {"vcp-screener": 1}
    assert summary["by_source"]["vcp-screener"]["5"]["outcomes"] == 1
    assert summary["by_source"]["vcp-screener"]["5"]["win_rate"] == 1.0
    assert metrics["vcp-screener"]["signals"] == 1
    assert metrics["vcp-screener"]["complete_signals"] == 1
    assert metrics["vcp-screener"]["complete_outcomes"] == 1
    assert metrics["vcp-screener"]["horizons"]["5"]["avg_return_pct"] == 0.05
