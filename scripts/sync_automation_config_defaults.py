#!/usr/bin/env python3
"""Merge template automation defaults into state/automation_config.yaml.

Preserves operator overrides (execute, account_size, fee_model, etc.) while
adding new keys such as fingerprint_block and updated source/exit rules.

Hardening keys under FORCE_TEMPLATE_PATHS always refresh from the template so
VM state cannot keep stale exit/fingerprint settings after deploy.
"""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = PROJECT_ROOT / "config" / "automation_config.template.yaml"
DEFAULT_STATE = PROJECT_ROOT / "state" / "automation_config.yaml"

# Dot-paths refreshed from template on every sync (state cannot pin stale values).
FORCE_TEMPLATE_PATHS = (
    "paper_exit_rules",
    "auto_paper.fingerprint_block",
    "auto_paper.fingerprint_min_closed",
    "auto_paper.fingerprint_min_win_rate",
    "auto_paper.fingerprint_max_avg_realized_r",
    "auto_paper.min_expected_net_r",
    "auto_paper.require_dual_check",
    "auto_paper.require_regime_gate",
    "auto_paper.source_rules.thai-swing-dip.min_score",
    "auto_paper.source_rules.thai-swing-dip.max_new_per_run",
    "auto_paper.source_rules.thai-swing-dip.max_open",
    "auto_paper.source_rules.thai-swing-dip.max_hold_days",
    "auto_paper.source_rules.thai-swing-dip.time_stop_min_r",
    "auto_paper.source_rules.thai-swing-dip.take_profit_r",
    "auto_paper.source_rules.thai-swing-dip.trail_after_r",
    "auto_paper.source_rules.thai-swing-dip.trail_stop_r",
    "auto_paper.source_rules.thai-swing-momentum.min_score",
    "auto_paper.source_rules.thai-swing-momentum.max_new_per_run",
    "auto_paper.source_rules.thai-swing-momentum.max_open",
    "auto_paper.source_rules.thai-swing-momentum.max_hold_days",
    "auto_paper.source_rules.thai-swing-momentum.time_stop_min_r",
)


def _deep_merge(base: dict, overrides: dict) -> dict:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _get_path(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur = data
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = deepcopy(value)


def _apply_forced_template_paths(
    merged: dict[str, Any], template: dict[str, Any]
) -> dict[str, Any]:
    out = deepcopy(merged)
    for path in FORCE_TEMPLATE_PATHS:
        value = _get_path(template, path)
        if value is None:
            continue
        _set_path(out, path, value)
    return out


def sync_config(template_path: Path, state_path: Path, *, write: bool = True) -> dict:
    template = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
    if not isinstance(template, dict):
        raise ValueError(f"template must be a mapping: {template_path}")

    if state_path.exists():
        current = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        if not isinstance(current, dict):
            raise ValueError(f"state config must be a mapping: {state_path}")
        # Template provides defaults; existing state wins on conflicts,
        # then forced paths refresh from template.
        merged = _apply_forced_template_paths(_deep_merge(template, current), template)
    else:
        merged = deepcopy(template)

    if write:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return merged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.template.exists():
        print(f"ERROR: template not found: {args.template}", file=sys.stderr)
        return 1

    merged = sync_config(args.template, args.state, write=not args.dry_run)
    action = "would write" if args.dry_run else "wrote"
    dip = ((merged.get("auto_paper") or {}).get("source_rules") or {}).get("thai-swing-dip") or {}
    print(
        f"{action} {args.state} "
        f"(dip max_hold_days={dip.get('max_hold_days')} "
        f"time_stop_min_r={dip.get('time_stop_min_r')} "
        f"min_score={dip.get('min_score')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
