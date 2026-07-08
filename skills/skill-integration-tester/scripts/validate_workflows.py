#!/usr/bin/env python3
"""Validate multi-skill workflows defined in GEMINI.md.

Parses workflow definitions, checks skill existence, validates inter-skill
data contracts (JSON schema compatibility), verifies file naming conventions,
and reports broken handoffs.  Supports dry-run mode with synthetic fixtures.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _generate_display_map(skills_dir: Path) -> dict[str, str]:
    """Dynamically generate the display name to directory name mapping."""
    display_map: dict[str, str] = {}
    for skill_path in skills_dir.iterdir():
        if skill_path.is_dir() and not skill_path.name.startswith("_"): # Exclude _meta_ skills
            skill_md = skill_path / "SKILL.md"
            if skill_md.is_file():
                fm_name = parse_frontmatter_name(skill_md)
                if fm_name:
                    display_map[fm_name.lower()] = skill_path.name
    # Add meta skills explicitly as they don't have SKILL.md
    display_map["screener skills"] = "_meta_screener_skills"
    display_map["analysis skills"] = "_meta_analysis_skills"
    display_map["monitor breakout entries with stop-loss"] = "_meta_monitor"
    display_map["manage market-neutral positions"] = "_meta_manage"
    display_map["monitor z-score signals and spread convergence"] = "_meta_monitor_zscore"
    display_map["feed review findings back to kanchi-dividend-sop before any additional buys"] = "_meta_feedback"
    return display_map

# ── Skill output contracts ───────────────────────────────────────────

_SKILL_CONTRACTS: dict[str, dict[str, Any]] = {}  # Will be loaded dynamically

def _load_skill_contracts(project_root: Path) -> dict[str, Any]:
    """Load skill contracts from a JSON file."""
    contracts_path = project_root / "skills" / "skill-integration-tester" / "references" / "workflow_contracts" / "skill_contracts.json"
    try:
        with contracts_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Skill contracts file not found at {contracts_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in skill contracts file at {contracts_path}", file=sys.stderr)
        sys.exit(1)


# ── Handoff contracts (producer → consumer) ──────────────────────────

_HANDOFF_CONTRACTS: dict[tuple[str, str], dict[str, Any]] = {}  # Will be loaded dynamically

def _load_handoff_contracts(project_root: Path) -> dict[tuple[str, str], Any]:
    """Load handoff contracts from a JSON file, converting string keys to tuples."""
    contracts_path = project_root / "skills" / "skill-integration-tester" / "references" / "workflow_contracts" / "handoff_contracts.json"
    try:
        with contracts_path.open("r", encoding="utf-8") as f:
            raw_contracts = json.load(f)
            # Convert string keys like "producer_consumer" to tuple keys (producer, consumer)
            return {
                tuple(k.split("_", 1)): v for k, v in raw_contracts.items()
            }
    except FileNotFoundError:
        print(f"Error: Handoff contracts file not found at {contracts_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in handoff contracts file at {contracts_path}", file=sys.stderr)
        sys.exit(1)


# ── Core functions ───────────────────────────────────────────────────


def resolve_skill_name(display_name: str) -> str:
    """Convert a display name to a skill directory name."""
    normalized = display_name.strip().lower()
    if normalized in _DISPLAY_MAP:
        return _DISPLAY_MAP[normalized]
    # Algorithmic fallback: lowercase, replace whitespace with hyphens
    return re.sub(r"\s+", "-", normalized)


def parse_workflows(text: str) -> dict[str, list[dict[str, str]]]:
    """Parse multi-skill workflow definitions from GEMINI.md content.

    Returns dict mapping workflow name to list of steps, each step
    being {"skill_display": ..., "action": ...}.
    """
    workflows: dict[str, list[dict[str, str]]] = {}

    workflow_pattern = re.compile(r"\*\*(.+?):\*\*\s*\n((?:\s*\d+\.\s+.+\n?)+)", re.MULTILINE)
    step_pattern = re.compile(r"\d+\.\s+(.+?)\s*\u2192\s*(.+?)(?:\s*\n|$)")

    for wf_match in workflow_pattern.finditer(text):
        name = wf_match.group(1).strip()
        steps_text = wf_match.group(2)
        steps: list[dict[str, str]] = []
        for step_match in step_pattern.finditer(steps_text):
            raw_skill = step_match.group(1).strip()
            # Strip parenthetical notes like (Mode B), (--ohlcv)
            skill_display = re.sub(r"\s*\(.*?\)\s*$", "", raw_skill).strip()
            action = step_match.group(2).strip()
            steps.append({"skill_display": skill_display, "action": action})
        if steps:
            workflows[name] = steps

    return workflows


def parse_frontmatter_name(skill_md_path: Path) -> str | None:
    """Extract the name field from SKILL.md YAML frontmatter."""
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    for line in match.group(1).split("\n"):
        m = re.match(r"^name:\s*(.+)", line)
        if m:
            return m.group(1).strip()
    return None


def check_skill_exists(skill_name: str, skills_dir: Path) -> bool:
    """Check if a skill directory with SKILL.md exists."""
    return (skills_dir / skill_name / "SKILL.md").is_file()


def check_naming_conventions(skill_name: str, skills_dir: Path) -> list[str]:
    """Check file naming conventions for a skill. Returns violations."""
    violations: list[str] = []
    skill_dir = skills_dir / skill_name

    if not skill_dir.is_dir():
        return [f"{skill_name}: Skill directory not found"]

    # SKILL.md must exist
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        violations.append(f"{skill_name}: Missing SKILL.md")
    else:
        # Frontmatter name must match directory name
        fm_name = parse_frontmatter_name(skill_md)
        if fm_name and fm_name != skill_name:
            violations.append(f"{skill_name}: SKILL.md name '{fm_name}' does not match directory")

    # Script filenames must be snake_case
    scripts_dir_path = skill_dir / "scripts"
    if scripts_dir_path.is_dir():
        for py_file in scripts_dir_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            if not re.match(r"^[a-z][a-z0-9_]*\.py$", py_file.name):
                violations.append(f"{skill_name}: Script '{py_file.name}' not in snake_case")

    # Directory name must be lowercase-hyphenated
    if not re.match(r"^[a-z][a-z0-9-]*$", skill_name):
        violations.append(f"{skill_name}: Directory name not in lowercase-hyphen format")

    return violations


def validate_handoff(producer: str, consumer: str, skills_dir: Path) -> dict[str, Any]:
    """Validate data contract between two consecutive workflow steps."""
    result: dict[str, Any] = {
        "producer": producer,
        "consumer": consumer,
        "status": "unknown",
        "details": [],
    }

    if not check_skill_exists(producer, skills_dir):
        result["status"] = "broken"
        result["details"].append(f"Producer skill not found: {producer}")
        return result

    if not check_skill_exists(consumer, skills_dir):
        result["status"] = "broken"
        result["details"].append(f"Consumer skill not found: {consumer}")
        return result

    pair = (producer, consumer)
    if pair in _HANDOFF_CONTRACTS:
        contract = _HANDOFF_CONTRACTS[pair]
        producer_contract = _SKILL_CONTRACTS.get(producer, {})
        producer_fields = set(producer_contract.get("output_fields", []))
        required = set(contract.get("required_fields", []))

        missing = required - producer_fields
        if missing:
            result["status"] = "broken"
            result["details"].append(
                f"Missing required fields in {producer} output: {sorted(missing)}"
            )
        else:
            result["status"] = "valid"
            result["details"].append(f"Contract valid: {contract['description']}")
    else:
        result["status"] = "no_contract"
        result["details"].append(f"No handoff contract defined for {producer} \u2192 {consumer}")

    return result


def validate_workflow(
    name: str,
    steps: list[dict[str, str]],
    skills_dir: Path,
) -> dict[str, Any]:
    """Validate a complete workflow end-to-end."""
    result: dict[str, Any] = {
        "workflow": name,
        "step_count": len(steps),
        "steps": [],
        "handoffs": [],
        "naming_violations": [],
        "status": "valid",
    }

    for i, step in enumerate(steps):
        skill_name = resolve_skill_name(step["skill_display"])
        # Skip meta-steps (manual actions, not real skills)
        is_meta = skill_name.startswith("_meta_")
        exists = is_meta or check_skill_exists(skill_name, skills_dir)

        step_result = {
        "index": i + 1,
        "skill_display": step["skill_display"],
        "skill_name": skill_name,
        "action": step["action"],
        "exists": exists,
        "is_meta": is_meta,
        "has_contract": skill_name in _SKILL_CONTRACTS,
        }
        result["steps"].append(step_result)

        if not exists:
            result["status"] = "broken"

        # Naming conventions (skip meta-steps)
        if not is_meta:
            violations = check_naming_conventions(skill_name, skills_dir)
            result["naming_violations"].extend(violations)

        # Handoff with previous step
        if i > 0:
            prev_skill = resolve_skill_name(steps[i - 1]["skill_display"])
            if not prev_skill.startswith("_meta_") and not is_meta:
                handoff = validate_handoff(prev_skill, skill_name, skills_dir)
                result["handoffs"].append(handoff)
                if handoff["status"] == "broken":
                    result["status"] = "broken"

    if result["naming_violations"] and result["status"] == "valid":
        result["status"] = "warning"

    return result


def create_dry_run_fixtures(
    workflows: dict[str, list[dict[str, str]]],
    output_dir: Path,
) -> list[str]:
    """Create synthetic fixture files for dry-run mode."""
    created: list[str] = []
    fixtures_dir = output_dir / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    seen: set = set()
    for _wf_name, steps in workflows.items():
        for step in steps:
            skill_name = resolve_skill_name(step["skill_display"])
            if skill_name in seen or skill_name not in _SKILL_CONTRACTS:
                continue
            seen.add(skill_name)

            contract = _SKILL_CONTRACTS[skill_name]
            fields = contract.get("output_fields", [])
            fixture: dict[str, Any] = {
                "_fixture": True,
                "_skill": skill_name,
                "schema_version": "1.0",
            }
            for field in fields:
                fixture[field] = f"<synthetic_{field}>"

            fixture_path = fixtures_dir / f"{skill_name}_fixture.json"
            fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
            created.append(str(fixture_path))

    return created


def generate_report(
    results: list[dict[str, Any]],
    dry_run: bool,
    fixtures: list[str],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Generate JSON and Markdown reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")

    total = len(results)
    valid = sum(1 for r in results if r["status"] == "valid")
    broken = sum(1 for r in results if r["status"] == "broken")
    warnings = sum(1 for r in results if r["status"] == "warning")

    report_data: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "summary": {
            "total_workflows": total,
            "valid": valid,
            "broken": broken,
            "warnings": warnings,
        },
        "workflows": results,
    }
    if dry_run:
        report_data["fixtures_created"] = fixtures

    json_path = output_dir / f"integration_test_{ts}.json"
    json_path.write_text(
        json.dumps(report_data, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    # ── Markdown report ──
    lines = [
        "# Skill Integration Test Report",
        "",
        f"**Generated:** {report_data['generated_at']}",
        f"**Mode:** {'Dry-run' if dry_run else 'Live'}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total Workflows | {total} |",
        f"| Valid | {valid} |",
        f"| Broken | {broken} |",
        f"| Warnings | {warnings} |",
        "",
    ]

    for r in results:
        status_label = {
            "valid": "PASS",
            "broken": "FAIL",
            "warning": "WARN",
        }.get(r["status"], "?")
        lines.append(f"## [{status_label}] {r['workflow']}")
        lines.append("")
        lines.append(f"Steps: {r['step_count']}")
        lines.append("")

        for step in r["steps"]:
            exists_mark = "ok" if step["exists"] else "MISSING"
            contract_mark = "ok" if step["has_contract"] else "none"
            meta_note = " (meta)" if step.get("is_meta") else ""
            lines.append(
                f"  {step['index']}. **{step['skill_display']}** "
                f"(`{step['skill_name']}`){meta_note} "
                f"\u2014 exists: {exists_mark}, contract: {contract_mark}"
            )

        if r["handoffs"]:
            lines.append("")
            lines.append("### Handoffs")
            lines.append("")
            for h in r["handoffs"]:
                h_label = {
                    "valid": "PASS",
                    "broken": "FAIL",
                    "no_contract": "N/A",
                }.get(h["status"], "?")
                lines.append(f"- [{h_label}] {h['producer']} \u2192 {h['consumer']}")
                for d in h["details"]:
                    lines.append(f"  - {d}")

        if r["naming_violations"]:
            lines.append("")
            lines.append("### Naming Violations")
            lines.append("")
            for v in r["naming_violations"]:
                lines.append(f"- {v}")

        lines.append("")

    md_path = output_dir / f"integration_test_{ts}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return json_path, md_path


# ── CLI entry point ──────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("Validate multi-skill workflows defined in GEMINI.md"),
    )
    parser.add_argument(
        "--gemini-md",
        type=str,
        default=None,
        help="Path to GEMINI.md (default: auto-detect from project root)",
    )
    parser.add_argument(
        "--skills-dir",
        type=str,
        default=None,
        help=("Path to skills/ directory (default: auto-detect from project root)"),
    )
    parser.add_argument(
        "--workflow",
        type=str,
        default=None,
        help="Validate a specific workflow by name substring (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create synthetic fixtures and validate without real data",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports/)",
    )

    args = parser.parse_args(argv)

    # Resolve project root (script is at skills/<name>/scripts/<file>.py)
    project_root = Path(__file__).resolve().parents[3]

    gemini_md_path = Path(args.gemini_md) if args.gemini_md else project_root / "GEMINI.md"
    skills_dir = Path(args.skills_dir) if args.skills_dir else project_root / "skills"
    output_dir = Path(args.output_dir)

    global _DISPLAY_MAP
    _DISPLAY_MAP = _generate_display_map(skills_dir)

    global _SKILL_CONTRACTS
    _SKILL_CONTRACTS = _load_skill_contracts(project_root)

    global _HANDOFF_CONTRACTS
    _HANDOFF_CONTRACTS = _load_handoff_contracts(project_root)

    if not gemini_md_path.is_file():
        print(
            f"Error: GEMINI.md not found at {gemini_md_path}",
            file=sys.stderr,
        )
        return 1

    if not skills_dir.is_dir():
        print(
            f"Error: skills directory not found at {skills_dir}",
            file=sys.stderr,
        )
        return 1
    # The `resolve_skill_name` function uses `_DISPLAY_MAP`, so we need to ensure
    # it's initialized before `resolve_skill_name` is called.

    # Parse workflows
    content = gemini_md_path.read_text(encoding="utf-8")
    workflows = parse_workflows(content)

    if not workflows:
        print("Warning: No workflows found in GEMINI.md", file=sys.stderr)
        return 0

    # Filter to specific workflow if requested
    if args.workflow:
        matching = {k: v for k, v in workflows.items() if args.workflow.lower() in k.lower()}
        if not matching:
            available = ", ".join(workflows.keys())
            print(
                f"Error: No workflow matching '{args.workflow}' found. Available: {available}",
                file=sys.stderr,
            )
            return 1
        workflows = matching

    # Dry-run fixtures
    fixtures: list[str] = []
    if args.dry_run:
        fixtures = create_dry_run_fixtures(workflows, output_dir)
        print(
            f"Dry-run: created {len(fixtures)} fixture files",
            file=sys.stderr,
        )

    # Validate each workflow
    results: list[dict[str, Any]] = []
    for wf_name, steps in workflows.items():
        result = validate_workflow(wf_name, steps, skills_dir)
        results.append(result)

    # Generate reports
    json_path, md_path = generate_report(results, args.dry_run, fixtures, output_dir)

    # Print summary
    total = len(results)
    broken = sum(1 for r in results if r["status"] == "broken")
    valid = sum(1 for r in results if r["status"] == "valid")

    print("\nIntegration Test Results:")
    print(f"  Workflows tested: {total}")
    print(f"  Valid: {valid}")
    print(f"  Broken: {broken}")
    print(f"  Reports: {json_path}, {md_path}")

    return 1 if broken > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
