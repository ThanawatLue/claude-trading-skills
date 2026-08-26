"""Tests for auto-paper Dual-Check / regime / kill-switch gates."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts import auto_paper, auto_paper_gates, signal_ledger


def _register(
    conn,
    *,
    signal_id: str = "sig_a",
    symbol: str = "AAPL",
    score: float = 80,
    signal_date: str = "2026-07-01",
    entry: float = 100,
    stop: float = 95,
    target: float = 110,
    source: str = "vcp-screener",
    payload: dict | None = None,
) -> None:
    signal_ledger.register_signal(
        conn,
        signal_ledger.SignalRecord(
            signal_id=signal_id,
            symbol=symbol,
            market=signal_ledger.infer_market(symbol),
            source_skill=source,
            signal_date=signal_date,
            raw_score=score,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            payload=payload,
        ),
    )


def _passing_vcp_payload() -> dict:
    return {
        "symbol": "AAPL",
        "composite_score": 80,
        "execution_state": "Pre-breakout",
        "distance_from_pivot_pct": -1.0,
        "relative_strength": {"rs_percentile": 88},
        "trend_template": {"passed": True, "score": 90},
        "source": "vcp",
        "_dual_source": "vcp",
    }


def test_kill_switch_blocks_all_opens(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, payload=_passing_vcp_payload())
        config = auto_paper.AutoPaperConfig(
            market="US",
            as_of=date(2026, 7, 1),
            kill_switch=True,
            require_dual_check=True,
            regime_recommendation="NEW_ENTRY_ALLOWED",
            require_regime_gate=True,
        )
        result = auto_paper.run_auto_paper(conn, config)

    assert result["eligible"] == 0
    assert result["kill_switch"] is True
    assert result["skipped_reason"] == "kill_switch_active"


def test_dual_check_rejects_extended_setup(tmp_path: Path) -> None:
    payload = _passing_vcp_payload()
    payload["execution_state"] = "Extended"
    payload["distance_from_pivot_pct"] = 8.0
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, payload=payload)
        config = auto_paper.AutoPaperConfig(
            market="US",
            as_of=date(2026, 7, 1),
            require_dual_check=True,
            dual_check_bars=False,
            require_verified_earnings=False,
            require_regime_gate=True,
            regime_recommendation="NEW_ENTRY_ALLOWED",
        )
        candidates = auto_paper.eligible_signals(conn, config)
        explained = auto_paper.explain_candidates(conn, config)

    assert candidates == []
    assert any(
        any(str(r).startswith("dual_check:") for r in row.get("reasons") or [])
        for row in explained["skipped"]
    )


def test_dual_check_passes_quality_setup(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, payload=_passing_vcp_payload())
        config = auto_paper.AutoPaperConfig(
            market="US",
            as_of=date(2026, 7, 1),
            require_dual_check=True,
            dual_check_bars=False,
            require_verified_earnings=False,
            require_regime_gate=True,
            regime_recommendation="NEW_ENTRY_ALLOWED",
        )
        candidates = auto_paper.eligible_signals(conn, config)

    assert len(candidates) == 1
    assert candidates[0]["dual_check"]["passed"] is True


def test_cash_priority_blocks_new_entries(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, payload=_passing_vcp_payload())
        config = auto_paper.AutoPaperConfig(
            market="US",
            as_of=date(2026, 7, 1),
            require_dual_check=False,
            require_regime_gate=True,
            regime_recommendation="CASH_PRIORITY",
        )
        candidates = auto_paper.eligible_signals(conn, config)

    assert candidates == []


def test_reduce_only_halves_risk_sized_shares(tmp_path: Path) -> None:
    with signal_ledger.connect(tmp_path / "db.sqlite") as conn:
        _register(conn, entry=10, stop=9, target=12, payload=_passing_vcp_payload())
        full = auto_paper.AutoPaperConfig(
            market="US",
            as_of=date(2026, 7, 1),
            account_size=100_000,
            risk_per_trade_pct=1.0,
            max_position_pct=20,
            board_lot_size=100,
            require_dual_check=False,
            require_regime_gate=True,
            regime_recommendation="NEW_ENTRY_ALLOWED",
        )
        reduced = auto_paper.AutoPaperConfig(
            market="US",
            as_of=date(2026, 7, 1),
            account_size=100_000,
            risk_per_trade_pct=1.0,
            max_position_pct=20,
            board_lot_size=100,
            require_dual_check=False,
            require_regime_gate=True,
            regime_recommendation="REDUCE_ONLY",
        )
        full_candidates = auto_paper.eligible_signals(conn, full)
        reduced_candidates = auto_paper.eligible_signals(conn, reduced)

    assert full_candidates[0]["shares"] == 1000
    assert reduced_candidates[0]["shares"] == 500
    assert reduced_candidates[0]["risk_scale"] == 0.5


def test_load_regime_recommendation_from_reports(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "exposure_posture_2026-07-01.json").write_text(
        '{"market": "US", "recommendation": "REDUCE_ONLY"}',
        encoding="utf-8",
    )
    assert auto_paper_gates.load_regime_recommendation(reports, "US") == "REDUCE_ONLY"


def test_resolve_regime_policy_defaults() -> None:
    assert auto_paper_gates.resolve_regime_policy(None)["allow_open"] is False
    assert auto_paper_gates.resolve_regime_policy("NEW_ENTRY_ALLOWED")["risk_scale"] == 1.0
    assert auto_paper_gates.resolve_regime_policy("CASH_PRIORITY")["allow_open"] is False
