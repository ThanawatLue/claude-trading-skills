"""Safe normalization of automation configuration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

VALID_EXECUTION_MODES = frozenset({"dry_run", "paper", "live"})


def resolve_execution_mode(config: dict[str, Any]) -> str:
    """Resolve explicit execution mode while preserving legacy config behavior.

    ``execute: true`` historically meant paper execution, never broker orders.
    The explicit mode makes that boundary visible in reports and logs.
    """

    explicit = config.get("execution_mode")
    if explicit is not None:
        mode = str(explicit).strip().lower()
        if mode not in VALID_EXECUTION_MODES:
            raise ValueError(f"unsupported execution_mode: {explicit!r}")
        if mode == "live":
            raise ValueError("live execution is disabled in this repository")
        return mode

    enabled = bool(config.get("enabled", True))
    execute = bool(config.get("execute", False))
    if not enabled or not execute or bool(config.get("kill_switch", False)):
        return "dry_run"
    return "paper"


def is_kill_switch_active(config: dict[str, Any]) -> bool:
    """Return True when automation must not open new positions."""

    return bool(config.get("kill_switch", False)) or not bool(config.get("enabled", True))


def normalize_execution_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with an explicit safe execution mode."""

    normalized = deepcopy(config)
    mode = resolve_execution_mode(normalized)
    normalized["execution_mode"] = mode
    normalized["real_money_enabled"] = False
    normalized["kill_switch"] = bool(normalized.get("kill_switch", False))
    paper = normalized.get("auto_paper")
    if isinstance(paper, dict):
        paper["execution_mode"] = mode
        paper["execute"] = mode == "paper"
        paper["kill_switch"] = bool(paper.get("kill_switch", normalized["kill_switch"]))
    return normalized
