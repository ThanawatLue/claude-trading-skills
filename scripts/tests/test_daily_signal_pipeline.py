from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest
import yaml

from scripts import run_daily_signal_pipeline as pipeline


def _write_thesis(theses_dir: Path, created_at: str = "2026-07-01T09:00:00+00:00") -> None:
    theses_dir.mkdir(parents=True, exist_ok=True)
    thesis = {
        "thesis_id": "th_aapl_vcp_20260701",
        "ticker": "AAPL",
        "created_at": created_at,
        "thesis_type": "pivot_breakout",
        "status": "IDEA",
        "entry": {"target_price": 100.0},
        "exit": {"stop_loss": 95.0, "take_profit": 110.0},
        "origin": {
            "skill": "vcp-screener",
            "output_file": "reports/vcp.json",
            "screening_score": 82.5,
            "screening_grade": "Strong VCP",
            "raw_provenance": {"price": 100.0},
        },
    }
    (theses_dir / "th_aapl.yaml").write_text(yaml.safe_dump(thesis), encoding="utf-8")


def _insert_bars(conn: sqlite3.Connection, symbol: str) -> None:
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
    for i, close in enumerate([100, 101, 102, 103, 104, 105, 106], start=1):
        rows.append(
            (
                symbol,
                f"2026-07-{i:02d}",
                close,
                close + 1,
                close - 1,
                close,
                1000,
                "2026-07-01T00:00:00",
            )
        )
    conn.executemany(
        """INSERT INTO price_bar
           (symbol, date, open, high, low, close, volume, fetched_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()


def _base_config(tmp_path: Path) -> dict:
    return pipeline._deep_merge(
        pipeline.DEFAULT_CONFIG,
        {
            "market": "US",
            "db_path": str(tmp_path / "market_cache.db"),
            "theses_dir": str(tmp_path / "theses"),
            "signal_files": {"enabled": False},
            "output_dir": str(tmp_path / "reports"),
            "horizons": [5],
            "analysis": {"enabled": False},
            "auto_paper": {"enabled": True, "execute": False, "min_score": 70},
        },
    )


def test_load_config_merges_nested_values(tmp_path: Path) -> None:
    cfg_path = tmp_path / "automation_config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "market": "US",
                "auto_paper": {"min_score": 75, "execute": True},
            }
        ),
        encoding="utf-8",
    )

    config = pipeline.load_config(cfg_path)

    assert config["market"] == "US"
    assert config["auto_paper"]["min_score"] == 75
    assert config["auto_paper"]["execute"] is True
    assert config["auto_paper"]["max_age_days"] == 10


def test_default_paper_profile_is_aggressive_30k_experiment() -> None:
    config = pipeline.load_config()
    paper = config["auto_paper"]

    assert config["market"] == "TH"
    assert paper["execute"] is True
    assert paper["account_size"] == 30_000
    assert paper["risk_per_trade_pct"] == 1
    assert paper["max_position_pct"] == 20
    assert paper["max_portfolio_heat_pct"] == 3
    assert paper["max_new_positions"] == 4
    assert paper["max_open_positions"] == 4
    assert paper["max_open_positions_with_override"] == 4
    auto_config = pipeline._build_auto_config(config)
    assert auto_config.transaction_cost_bps == pytest.approx(21.692)
    assert auto_config.fee_model["broker"] == "innovestx"


def test_run_pipeline_dry_run_ingests_and_updates_without_opening(tmp_path: Path) -> None:
    _write_thesis(tmp_path / "theses")
    config = _base_config(tmp_path)
    calls = []

    def fake_open(**kwargs):
        calls.append(kwargs)
        return {"id": 123}

    with sqlite3.connect(config["db_path"]) as conn:
        _insert_bars(conn, "AAPL")

    result = pipeline.run_pipeline(
        config,
        analysis_runner=lambda _: {"enabled": False, "ok": True, "status": "skipped"},
        open_fn=fake_open,
        as_of=date(2026, 7, 1),
    )

    assert result["ingest"]["theses"]["inserted"] == 1
    assert result["ingest"]["signals"]["total"] == 0
    assert result["outcomes"]["complete_outcomes"] == 1
    assert result["auto_paper"]["eligible"] == 1
    assert result["auto_paper"]["opened"] == 0
    assert result["auto_paper"]["dry_run"] is True
    assert calls == []
    assert Path(result["reports"]["json"]).exists()
    assert Path(result["reports"]["markdown"]).exists()


def test_run_pipeline_execute_opens_and_links_signal(tmp_path: Path) -> None:
    _write_thesis(tmp_path / "theses")
    config = _base_config(tmp_path)
    config["auto_paper"]["execute"] = True
    opened = []

    def fake_open(**kwargs):
        opened.append(kwargs)
        return {"id": 456}

    result = pipeline.run_pipeline(
        config,
        analysis_runner=lambda _: {"enabled": False, "ok": True, "status": "skipped"},
        open_fn=fake_open,
        as_of=date(2026, 7, 1),
        write_output=False,
    )

    assert result["auto_paper"]["dry_run"] is False
    assert result["auto_paper"]["opened"] == 1
    assert opened[0]["symbol"] == "AAPL"

    with sqlite3.connect(config["db_path"]) as conn:
        links = conn.execute("SELECT signal_id, paper_trade_id FROM signal_paper_link").fetchall()

    assert len(links) == 1
    assert links[0][1] == 456


def test_run_pipeline_ingests_signal_file_patterns(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports-src"
    reports_dir.mkdir()
    signal_path = reports_dir / "thai_swing_2026-07-01.json"
    signal_path.write_text(
        json.dumps(
            {
                "generated": "2026-07-01T17:00:00",
                "metadata": {"market": "TH"},
                "momentum": [
                    {
                        "symbol": "SAT.BK",
                        "score": 70.8,
                        "price": 15.8,
                        "plan": {"entry": 15.8, "stop": 15.56, "target": 16.27},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    config = pipeline._deep_merge(
        _base_config(tmp_path),
        {
            "market": "TH",
            "signal_files": {
                "enabled": True,
                "patterns": [str(reports_dir / "thai_swing_*.json")],
                "max_files_per_pattern": 3,
            },
        },
    )

    result = pipeline.run_pipeline(
        config,
        analysis_runner=lambda _: {"enabled": False, "ok": True, "status": "skipped"},
        as_of=date(2026, 7, 1),
        write_output=False,
    )

    assert result["ingest"]["signals"]["inserted"] == 1
    # A pipeline run outside the live Thai session must ingest the signal but
    # must not create an optimistic after-hours paper entry.
    assert result["auto_paper"]["eligible"] == 0
