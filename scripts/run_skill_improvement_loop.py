#!/usr/bin/env python3
"""Skill self-improvement loop orchestrator.

Picks the next skill (round-robin), scores it with run_dual_axis_review.py,
and uses Gemini to apply targeted improvements directly on disk.
No git commits or PRs — all changes stay local.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to sys.path to import gemini_adapter
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))
import gemini_adapter

logger = logging.getLogger("skill_improvement")

REVIEWER_SCRIPT = "skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py"
SELF_SKILL_NAME = "dual-axis-skill-reviewer"
STATE_FILE = "logs/.skill_improvement_state.json"
LOCK_FILE = "logs/.skill_improvement.lock"
LOG_DIR = "logs"
SUMMARY_DIR = "reports/skill-improvement-log"
SCORE_THRESHOLD = 90
HISTORY_LIMIT = 60
LOG_RETENTION_DAYS = 30
GEMINI_TIMEOUT = 300       # renamed from CLAUDE_TIMEOUT
IMPROVEMENT_TIMEOUT = 600


# ── Lock ──


def acquire_lock(project_root: Path) -> bool:
    """Acquire a PID-based lock file. Returns True if acquired."""
    lock_path = project_root / LOCK_FILE
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if lock_path.exists():
        try:
            old_pid = int(lock_path.read_text().strip())
            os.kill(old_pid, 0)
            logger.info("Another instance (PID %d) is running. Exiting.", old_pid)
            return False
        except (ValueError, OSError):
            logger.info("Stale lock found, removing.")
            lock_path.unlink(missing_ok=True)

    lock_path.write_text(str(os.getpid()))
    return True


def release_lock(project_root: Path) -> None:
    lock_path = project_root / LOCK_FILE
    lock_path.unlink(missing_ok=True)


# ── State management ──


def load_state(project_root: Path) -> dict:
    state_path = project_root / STATE_FILE
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt state file, starting fresh.")
    return {"last_skill_index": -1, "history": []}


def save_state(project_root: Path, state: dict) -> None:
    state_path = project_root / STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state["history"] = state["history"][-HISTORY_LIMIT:]
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── Skill selection ──


def discover_skills(project_root: Path) -> list[str]:
    """Return sorted skill names, excluding the reviewer itself."""
    skills_dir = project_root / "skills"
    if not skills_dir.is_dir():
        return []
    names = []
    for child in sorted(skills_dir.iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists() and child.name != SELF_SKILL_NAME:
            names.append(child.name)
    return names


def pick_next_skill(skills: list[str], state: dict) -> str | None:
    if not skills:
        return None
    idx = (state.get("last_skill_index", -1) + 1) % len(skills)
    state["last_skill_index"] = idx
    return skills[idx]


# ── Scoring ──


def _build_reviewer_cmd(project_root: Path) -> list[str]:
    """Return command prefix for invoking the reviewer script."""
    # Use sys.executable directly if on Windows or inside a virtualenv to bypass
    # uv's package sync locks (which fail if another process like the dashboard holds locks).
    if os.name == "nt" or sys.prefix != sys.base_prefix:
        return [sys.executable, str(project_root / REVIEWER_SCRIPT)]
    if shutil.which("uv"):
        return ["uv", "run", "--extra", "dev", "python", str(project_root / REVIEWER_SCRIPT)]
    return [sys.executable, str(project_root / REVIEWER_SCRIPT)]



def run_auto_score(
    project_root: Path,
    skill_name: str,
    emit_prompt: bool = False,
    skip_tests: bool = True,
    llm_review_json: str | None = None,
) -> dict | None:
    """Run the auto reviewer and return its JSON report."""
    script = str(project_root / REVIEWER_SCRIPT)
    extra_args: list[str] = [
        "--project-root",
        str(project_root),
        "--skill",
        skill_name,
        "--output-dir",
        "reports",
    ]
    if skip_tests:
        extra_args.append("--skip-tests")
    if llm_review_json:
        extra_args.extend(["--llm-review-json", llm_review_json])
    if emit_prompt:
        extra_args.append("--emit-llm-prompt")

    cmd = [*_build_reviewer_cmd(project_root), *extra_args]

    result = subprocess.run(
        cmd, cwd=project_root, capture_output=True, text=True, check=False, timeout=120
    )

    # Fallback: if uv failed, retry with sys.executable
    if result.returncode != 0 and cmd[0] == "uv":
        logger.warning("uv run failed for %s; falling back to %s.", skill_name, sys.executable)
        cmd = [sys.executable, script, *extra_args]
        result = subprocess.run(
            cmd, cwd=project_root, capture_output=True, text=True, check=False, timeout=120
        )

    if result.returncode != 0:
        logger.error("Auto score failed for %s: %s", skill_name, result.stderr.strip())
        return None

    report_files = sorted(
        (project_root / "reports").glob(f"skill_review_{skill_name}_*.json"), reverse=True
    )
    if not report_files:
        logger.error("No report JSON found for %s.", skill_name)
        return None

    return json.loads(report_files[0].read_text(encoding="utf-8"))


def run_llm_review(project_root: Path, skill_name: str, prompt_file: str) -> dict | None:
    """Invoke Gemini for LLM review. Returns parsed JSON or None."""
    prompt_path = Path(prompt_file)
    if not prompt_path.is_absolute():
        prompt_path = project_root / prompt_path
    if not prompt_path.exists():
        logger.error("LLM prompt file not found: %s", prompt_file)
        return None

    prompt_text = prompt_path.read_text(encoding="utf-8")
    
    # JSON Schema instructions are already part of the prompt in some skills,
    # but we force JSON mode in gemini_adapter.
    response_text = gemini_adapter.call_gemini(
        prompt_text,
        model_name=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        response_mime_type="application/json"
    )
    
    if not response_text:
        logger.error("Gemini returned empty response for LLM review.")
        return None

    try:
        parsed = gemini_adapter.extract_json_from_text(response_text)
        if parsed is None:
            logger.error("Failed to extract JSON from response text: %s", response_text)
            return None
            
        if isinstance(parsed, dict):
            # If the model returned a single finding directly instead of wrapped in findings list
            if "severity" in parsed and "message" in parsed and "score" not in parsed:
                parsed = {
                    "score": 85,
                    "summary": parsed.get("message", "One finding identified."),
                    "findings": [parsed]
                }
            
            # Ensure required keys exist and have proper types
            if "score" not in parsed or not isinstance(parsed["score"], (int, float)):
                parsed["score"] = 85
            if "findings" not in parsed or not isinstance(parsed["findings"], list):
                parsed["findings"] = []
            return parsed
        elif isinstance(parsed, list):
            # If it returned a list of findings directly
            return {
                "score": 85,
                "summary": f"{len(parsed)} findings identified.",
                "findings": parsed
            }
        logger.error("Unexpected JSON type parsed: %s", type(parsed))
        return None
    except Exception as parse_ex:
        logger.error("Exception parsing LLM review JSON: %s. Raw text: %s", parse_ex, response_text)
        return None


def _extract_json_from_claude(output: str, required_keys: list[str]) -> dict | None:
    """Extract JSON from claude CLI --output-format json envelope.

    Unwraps the envelope (result or content[].text), then scans for
    the first JSON object containing any of the required_keys.
    """
    # claude --output-format json wraps response; try to extract inner JSON
    try:
        wrapper = json.loads(output)
        text = ""
        if isinstance(wrapper, dict):
            text = wrapper.get("result", "") or ""
            if not text:
                content = wrapper.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text += block.get("text", "")
        if not text:
            text = output
    except json.JSONDecodeError:
        text = output

    # Find JSON block using raw_decode (handles nested objects and braces in strings)
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        pos = text.find("{", idx)
        if pos == -1:
            break
        try:
            obj, end_idx = decoder.raw_decode(text, pos)
            if isinstance(obj, dict) and any(k in obj for k in required_keys):
                return obj
            idx = pos + 1
        except json.JSONDecodeError:
            idx = pos + 1
    return None


# ── Improvement ──


def apply_improvement(
    project_root: Path,
    skill_name: str,
    report: dict,
    dry_run: bool = False,
) -> dict | None:
    """Apply targeted improvements to a skill directly on disk using Gemini.

    Returns the post-improvement report dict on success, or None on failure/dry-run.
    No git operations — all changes are written locally.
    """
    if dry_run:
        logger.info(
            "[dry-run] Would improve skill '%s' (score=%d).",
            skill_name,
            report["final_review"]["score"],
        )
        return None

    pre_score = report["auto_review"]["score"]

    improvements = report["final_review"].get("improvement_items", [])
    if not improvements:
        logger.warning(
            "No improvement_items for '%s' (score=%d); skipping to avoid unguided changes.",
            skill_name,
            pre_score,
        )
        return None

    prompt = (
        f"Improve the skill '{skill_name}' in skills/{skill_name}/ based on these findings:\n\n"
        + "\n".join(f"- {item}" for item in improvements[:10])
        + "\n\nMake minimal, targeted edits to address the findings. Do not change unrelated code.\n\n"
        + "CRITICAL IMPORT RULES:\n"
        + "1. Do NOT use package-relative imports (e.g., `from . import ...`, `from .constants import ...`) in any python scripts that are designed to be run directly as entry points or standalone scripts (e.g., files in `scripts/` directory executed by the dashboard or command line). Direct scripts run as `__main__` and have no parent package, so relative imports will fail with `ImportError: attempted relative import with no known parent package`.\n"
        + "2. Keep entry points self-contained. If you need constants or helper functions, define them directly in the same file or use absolute imports after appending paths to `sys.path` if absolutely necessary."
    )

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    success = gemini_adapter.run_gemini_agent(prompt, model_name=model_name, max_turns=30)
    if not success:
        logger.error("Gemini improvement agent failed.")
        return None

    # Quality gate: re-score after improvement
    re_report = run_auto_score(project_root, skill_name, skip_tests=False)
    if not re_report:
        logger.error("Re-scoring failed after improvement.")
        return None

    re_score = re_report.get("auto_review", {}).get("score", 0)
    if re_score <= pre_score:
        logger.warning(
            "Re-score (%d) not better than pre-score (%d). Files left on disk for manual inspection.",
            re_score,
            pre_score,
        )
        return None

    # Auto-fix lint issues
    if shutil.which("ruff"):
        subprocess.run(
            ["ruff", "check", "--fix", f"skills/{skill_name}/"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["ruff", "format", f"skills/{skill_name}/"],
            cwd=project_root,
            capture_output=True,
            check=False,
        )

    logger.info("Successfully improved skill '%s' (score %d -> %d)!", skill_name, pre_score, re_score)
    return re_report


# ── Summary ──


def write_daily_summary(project_root: Path, skill_name: str, report: dict, improved: bool) -> None:
    summary_dir = project_root / SUMMARY_DIR
    summary_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    summary_path = summary_dir / f"{today}_summary.md"

    entry = (
        f"\n## {skill_name}\n"
        f"- Score: {report['final_review']['score']}/100\n"
        f"- Improved: {'Yes' if improved else 'No'}\n"
        f"- High findings: {sum(1 for f in report['final_review'].get('findings', []) if f.get('severity') == 'high')}\n"
    )

    if summary_path.exists():
        existing = summary_path.read_text(encoding="utf-8")
        summary_path.write_text(existing + entry, encoding="utf-8")
    else:
        header = f"# Skill Improvement Summary - {today}\n"
        summary_path.write_text(header + entry, encoding="utf-8")


def rotate_logs(project_root: Path) -> None:
    """Remove log files older than LOG_RETENTION_DAYS."""
    log_dir = project_root / LOG_DIR
    if not log_dir.is_dir():
        return
    cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    for f in log_dir.iterdir():
        if f.is_file() and f.suffix == ".log":
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    logger.info("Rotated old log: %s", f.name)
            except OSError:
                pass


# ── Main ──


def parse_args():
    parser = argparse.ArgumentParser(
        description="Skill self-improvement loop — scores one skill per run and improves it locally"
    )
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--dry-run", action="store_true", help="Score only; skip improvement"
    )
    return parser.parse_args()


def run(project_root: Path, dry_run: bool = False) -> int:
    """Core orchestration logic, separated from CLI for testability."""
    log_dir = project_root / LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "skill_improvement.log"),
        ],
    )

    if not acquire_lock(project_root):
        return 0

    try:
        # Discover and pick skill
        skills = discover_skills(project_root)
        if not skills:
            logger.error("No skills found.")
            return 1

        state = load_state(project_root)
        skill_name = pick_next_skill(skills, state)
        if not skill_name:
            logger.error("No skill to review.")
            return 1

        logger.info("Selected skill: %s", skill_name)

        # Auto scoring
        report = run_auto_score(project_root, skill_name, emit_prompt=True)
        if not report:
            logger.error("Auto scoring failed.")
            return 1

        auto_score = report.get("auto_review", {}).get("score", 0)
        logger.info("Auto score for %s: %d/100", skill_name, auto_score)

        # LLM review (optional)
        llm_prompt_file = report.get("llm_prompt_file")
        if llm_prompt_file and not dry_run:
            llm_result = run_llm_review(project_root, skill_name, llm_prompt_file)
            if llm_result:
                llm_json_path = project_root / "reports" / f"llm_review_{skill_name}.json"
                llm_json_path.write_text(json.dumps(llm_result, indent=2), encoding="utf-8")
                logger.info("LLM review score: %d", llm_result.get("score", 0))
                merged_report = run_auto_score(
                    project_root,
                    skill_name,
                    llm_review_json=str(llm_json_path),
                )
                if merged_report:
                    report = merged_report

        final_score = report.get("auto_review", {}).get("score", auto_score)
        logger.info("Auto-based score for %s: %d/100", skill_name, final_score)

        # Improvement
        improved = False
        if final_score < SCORE_THRESHOLD:
            logger.info(
                "Auto score %d below %d; attempting improvement.", final_score, SCORE_THRESHOLD
            )
            improvement_result = apply_improvement(
                project_root, skill_name, report, dry_run=dry_run
            )
            if isinstance(improvement_result, dict):
                report = improvement_result
                final_score = report.get("auto_review", {}).get("score", final_score)
                improved = True
        else:
            logger.info(
                "Auto score meets threshold (%d >= %d); no improvement needed.",
                final_score,
                SCORE_THRESHOLD,
            )

        # Summary + state
        write_daily_summary(project_root, skill_name, report, improved)
        state["history"].append(
            {
                "skill": skill_name,
                "score": final_score,
                "improved": improved,
                "timestamp": datetime.now().isoformat(),
            }
        )
        save_state(project_root, state)
        rotate_logs(project_root)
        return 0

    finally:
        release_lock(project_root)


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    return run(project_root, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
