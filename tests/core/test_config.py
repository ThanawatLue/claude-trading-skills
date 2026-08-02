import pytest

from trading_core.config import normalize_execution_config, resolve_execution_mode


def test_legacy_execute_true_maps_to_paper_mode() -> None:
    assert resolve_execution_mode({"enabled": True, "execute": True}) == "paper"


def test_disabled_or_dry_run_is_explicit() -> None:
    normalized = normalize_execution_config({"enabled": True, "execute": False})
    assert normalized["execution_mode"] == "dry_run"
    assert normalized["real_money_enabled"] is False


def test_live_mode_is_blocked() -> None:
    with pytest.raises(ValueError, match="live execution is disabled"):
        resolve_execution_mode({"execution_mode": "live"})
