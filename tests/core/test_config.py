import pytest

from trading_core.config import (
    is_kill_switch_active,
    normalize_execution_config,
    resolve_execution_mode,
)


def test_legacy_execute_true_maps_to_paper_mode() -> None:
    assert resolve_execution_mode({"enabled": True, "execute": True}) == "paper"


def test_disabled_or_dry_run_is_explicit() -> None:
    normalized = normalize_execution_config({"enabled": True, "execute": False})
    assert normalized["execution_mode"] == "dry_run"
    assert normalized["real_money_enabled"] is False


def test_live_mode_is_blocked() -> None:
    with pytest.raises(ValueError, match="live execution is disabled"):
        resolve_execution_mode({"execution_mode": "live"})


def test_kill_switch_forces_dry_run_and_is_detectable() -> None:
    assert (
        resolve_execution_mode({"enabled": True, "execute": True, "kill_switch": True}) == "dry_run"
    )
    assert is_kill_switch_active({"kill_switch": True}) is True
    assert is_kill_switch_active({"enabled": False}) is True
    assert is_kill_switch_active({"enabled": True, "kill_switch": False}) is False
