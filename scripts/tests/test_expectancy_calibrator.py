"""Tests for expectancy calibration helpers."""

from __future__ import annotations

import sqlite3

from scripts import expectancy_calibrator


def test_calibrate_tightens_negative_expectancy_with_enough_samples() -> None:
    stats = {"vcp-screener": {"closed_trades": 25, "expectancy_r": -0.2}}
    rows = expectancy_calibrator.calibrate_source_rules(
        source_stats=stats,
        source_rules={"vcp-screener": {"min_score": 70}},
        default_min_score=70,
        min_closed=20,
    )
    assert len(rows) == 1
    assert rows[0].action == "tighten"
    assert rows[0].suggested_min_score == 75


def test_calibrate_holds_when_sample_too_small() -> None:
    stats = {"vcp-screener": {"closed_trades": 5, "expectancy_r": -1.0}}
    rows = expectancy_calibrator.calibrate_source_rules(
        source_stats=stats,
        source_rules={},
        default_min_score=70,
        min_closed=20,
    )
    assert rows[0].action == "hold"
    assert rows[0].suggested_min_score == 70


def test_apply_calibration_only_tightens_by_default() -> None:
    calibrations = expectancy_calibrator.calibrate_source_rules(
        source_stats={
            "a": {"closed_trades": 30, "expectancy_r": -0.1},
            "b": {"closed_trades": 30, "expectancy_r": 0.8},
        },
        source_rules={"a": {"min_score": 70}, "b": {"min_score": 70}},
    )
    applied = expectancy_calibrator.apply_calibration_to_source_rules(
        {"a": {"min_score": 70}, "b": {"min_score": 70}},
        calibrations,
    )
    assert applied["a"]["min_score"] == 75
    assert applied["b"]["min_score"] == 70


def test_paper_expectancy_by_source_reads_closed_trades(tmp_path) -> None:
    db = tmp_path / "db.sqlite"
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            """CREATE TABLE paper_trade (
                id INTEGER PRIMARY KEY,
                source TEXT,
                market TEXT,
                status TEXT,
                realized_r REAL
            )"""
        )
        conn.executemany(
            "INSERT INTO paper_trade (source, market, status, realized_r) VALUES (?,?,?,?)",
            [
                ("vcp-screener", "US", "closed_target", 1.5),
                ("vcp-screener", "US", "closed_stop", -1.0),
                ("vcp-screener", "US", "open", None),
            ],
        )
        stats = expectancy_calibrator.paper_expectancy_by_source(conn, market="US")
    assert stats["vcp-screener"]["closed_trades"] == 2
    assert stats["vcp-screener"]["expectancy_r"] == 0.25
