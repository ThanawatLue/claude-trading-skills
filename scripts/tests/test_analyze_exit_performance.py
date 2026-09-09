import sqlite3
from pathlib import Path

import pytest

from scripts.analyze_exit_performance import analyze_exits


def test_analyze_exits_empty_or_missing_db(tmp_path: Path):
    missing_db = tmp_path / "non_existent.db"
    res = analyze_exits(db_path=missing_db)
    assert res["ok"] is False
    assert "not found" in res["error"]


def test_analyze_exits_computes_telemetry_correctly(tmp_path: Path):
    db_path = tmp_path / "test_market_cache.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE paper_trade (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            market TEXT,
            side TEXT,
            status TEXT,
            entry_price REAL,
            entry_at TEXT,
            shares INTEGER,
            stop_price REAL,
            target_price REAL,
            initial_risk REAL,
            source TEXT,
            realized_pnl REAL,
            realized_r REAL,
            mae REAL,
            mfe REAL,
            days_held INTEGER
        )"""
    )
    # Trade 1: Target hit (Win: +2.0R, MFE: +2.2R)
    conn.execute(
        """INSERT INTO paper_trade VALUES (
            1, 'WIN.BK', 'TH', 'long', 'closed_target',
            100.0, '2026-07-01T09:00:00+00:00', 100, 90.0, 120.0, 1000.0,
            'thai-swing-momentum', 2000.0, 2.0, 98.0, 122.0, 4
        )"""
    )
    # Trade 2: Ratchet Stop (Win: +0.8R, MFE: +1.9R)
    conn.execute(
        """INSERT INTO paper_trade VALUES (
            2, 'RATCHET.BK', 'TH', 'long', 'closed_ratchet',
            100.0, '2026-07-01T09:00:00+00:00', 100, 90.0, 120.0, 1000.0,
            'thai-swing-momentum', 800.0, 0.8, 97.0, 119.0, 5
        )"""
    )
    # Trade 3: Velocity Stall (Small loss: -0.2R, MFE: +0.1R, saved 0.8R compared to -1.0R full stop)
    conn.execute(
        """INSERT INTO paper_trade VALUES (
            3, 'STALL.BK', 'TH', 'long', 'closed_stalled',
            100.0, '2026-07-01T09:00:00+00:00', 100, 90.0, 120.0, 1000.0,
            'thai-swing-dip', -200.0, -0.2, 97.5, 101.0, 3
        )"""
    )
    # Trade 4: Full Stop (Loss: -1.0R, MFE: 0.0R)
    conn.execute(
        """INSERT INTO paper_trade VALUES (
            4, 'LOSS.BK', 'TH', 'long', 'closed_stop',
            100.0, '2026-07-01T09:00:00+00:00', 100, 90.0, 120.0, 1000.0,
            'thai-swing-dip', -1000.0, -1.0, 89.5, 100.0, 2
        )"""
    )
    conn.commit()
    conn.close()

    res = analyze_exits(db_path=db_path, market="TH")
    assert res["ok"] is True
    assert res["total_closed"] == 4
    assert res["wins"] == 2
    assert res["losses"] == 2
    assert res["win_rate_pct"] == 50.0
    assert res["sum_realized_r"] == pytest.approx(1.6)
    assert res["sum_realized_pnl"] == pytest.approx(1600.0)

    # Check status groupings
    statuses = res["by_exit_status"]
    assert "closed_target" in statuses
    assert "closed_ratchet" in statuses
    assert "closed_stalled" in statuses
    assert "closed_stop" in statuses

    # Check capture efficiency
    assert res["global_capture_efficiency_pct"] > 0
    # Winning MFE = 2.2 + 1.9 = 4.1R, Winning Realized R = 2.0 + 0.8 = 2.8R -> 2.8 / 4.1 = ~68.3%
    assert res["global_capture_efficiency_pct"] == pytest.approx(68.3, abs=0.5)

    # Check savings
    saved = res["estimated_capital_saved_r"]
    assert saved["from_stalls"] == pytest.approx(0.8)
    assert saved["from_ratchets"] == pytest.approx(1.8)
    assert saved["total"] == pytest.approx(2.6)
