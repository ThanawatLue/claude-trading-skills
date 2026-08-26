#!/usr/bin/env python3
"""Merge template automation defaults into state/automation_config.yaml.

Preserves operator overrides (execute, account_size, fee_model, etc.) while
adding new keys such as fingerprint_block and updated source/exit rules.
"""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = PROJECT_ROOT / "config" / "automation_config.template.yaml"
DEFAULT_STATE = PROJECT_ROOT / "state" / "automation_config.yaml"


def _deep_merge(base: dict, overrides: dict) -> dict:
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def sync_config(template_path: Path, state_path: Path, *, write: bool = True) -> dict:
    template = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
    if not isinstance(template, dict):
        raise ValueError(f"template must be a mapping: {template_path}")

    if state_path.exists():
        current = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        if not isinstance(current, dict):
            raise ValueError(f"state config must be a mapping: {state_path}")
        # Template provides defaults; existing state wins on conflicts.
        merged = _deep_merge(template, current)
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
    print(f"{action} {args.state} (keys={sorted(merged.keys())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
