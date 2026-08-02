"""Contract tests for the Gemini/local-only skill improvement loop."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from subprocess import CompletedProcess

import pytest


@pytest.fixture(scope="module")
def loop_module():
    script_path = Path(__file__).resolve().parents[1] / "run_skill_improvement_loop.py"
    spec = importlib.util.spec_from_file_location("run_skill_improvement_loop", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load run_skill_improvement_loop.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_skill(project_root: Path, name: str = "test-skill") -> None:
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test\n---\n# {name}\n",
        encoding="utf-8",
    )


def _report(score: int = 70, improvements: list[str] | None = None) -> dict:
    return {
        "auto_review": {"score": score},
        "final_review": {
            "score": score,
            "findings": [],
            "improvement_items": improvements if improvements is not None else ["fix X"],
        },
    }


def test_lock_lifecycle_and_running_pid(loop_module, tmp_path: Path, monkeypatch):
    assert loop_module.acquire_lock(tmp_path) is True
    lock_path = tmp_path / loop_module.LOCK_FILE
    assert lock_path.read_text(encoding="utf-8").strip() == str(os.getpid())

    assert loop_module.acquire_lock(tmp_path) is False
    loop_module.release_lock(tmp_path)
    assert not lock_path.exists()

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("999999999", encoding="utf-8")
    monkeypatch.setattr(loop_module, "pid_is_alive", lambda pid: False)
    assert loop_module.acquire_lock(tmp_path) is True
    loop_module.release_lock(tmp_path)


def test_load_save_state_is_utf8_and_bounded(loop_module, tmp_path: Path):
    state = {"last_skill_index": 2, "history": [{"i": i} for i in range(100)]}
    loop_module.save_state(tmp_path, state)
    loaded = loop_module.load_state(tmp_path)
    assert loaded["last_skill_index"] == 2
    assert len(loaded["history"]) == loop_module.HISTORY_LIMIT

    state_path = tmp_path / loop_module.STATE_FILE
    state_path.write_text("{not json", encoding="utf-8")
    assert loop_module.load_state(tmp_path) == {"last_skill_index": -1, "history": []}


def test_discover_and_pick_round_robin(loop_module, tmp_path: Path):
    _make_skill(tmp_path, "alpha")
    _make_skill(tmp_path, "beta")
    _make_skill(tmp_path, loop_module.SELF_SKILL_NAME)
    (tmp_path / "skills" / "not-a-skill").mkdir(parents=True)

    skills = loop_module.discover_skills(tmp_path)
    assert skills == ["alpha", "beta"]
    state = {"last_skill_index": -1, "history": []}
    assert [loop_module.pick_next_skill(skills, state) for _ in range(3)] == [
        "alpha",
        "beta",
        "alpha",
    ]
    assert loop_module.pick_next_skill([], state) is None


def test_run_llm_review_normalizes_gemini_dict_list_and_finding(
    loop_module, tmp_path: Path, monkeypatch
):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Review this skill", encoding="utf-8")
    calls: list[dict] = []
    responses = iter(
        [
            json.dumps({"score": 78, "summary": "ok", "findings": []}),
            json.dumps([{"severity": "high", "message": "add tests"}]),
            json.dumps({"severity": "low", "message": "tighten docs"}),
        ]
    )

    def fake_call(prompt_text, **kwargs):
        calls.append({"prompt": prompt_text, **kwargs})
        return next(responses)

    monkeypatch.setattr(loop_module.gemini_adapter, "call_gemini", fake_call)

    first = loop_module.run_llm_review(tmp_path, "test-skill", str(prompt))
    second = loop_module.run_llm_review(tmp_path, "test-skill", str(prompt))
    third = loop_module.run_llm_review(tmp_path, "test-skill", str(prompt))

    assert first["score"] == 78
    assert second["score"] == 85 and len(second["findings"]) == 1
    assert third["score"] == 85 and third["findings"][0]["severity"] == "low"
    assert all(call["response_mime_type"] == "application/json" for call in calls)


def test_run_llm_review_handles_missing_prompt_and_empty_response(
    loop_module, tmp_path: Path, monkeypatch
):
    assert loop_module.run_llm_review(tmp_path, "test-skill", "missing.txt") is None
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Review", encoding="utf-8")
    monkeypatch.setattr(loop_module.gemini_adapter, "call_gemini", lambda *a, **k: None)
    assert loop_module.run_llm_review(tmp_path, "test-skill", str(prompt)) is None


def test_run_auto_score_reads_latest_utf8_report(loop_module, tmp_path: Path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    report = _report(82)
    (reports / "skill_review_test-skill_2026.json").write_text(
        json.dumps(report, ensure_ascii=False), encoding="utf-8"
    )
    command_log: list[list[str]] = []

    monkeypatch.setattr(loop_module, "_build_reviewer_cmd", lambda root: ["python", "reviewer.py"])
    monkeypatch.setattr(
        loop_module.subprocess,
        "run",
        lambda cmd, **kwargs: command_log.append(list(cmd)) or CompletedProcess(cmd, 0, "ok", ""),
    )

    result = loop_module.run_auto_score(tmp_path, "test-skill", skip_tests=False)
    assert result["auto_review"]["score"] == 82
    assert command_log and "--skill" in command_log[0]
    assert "--skip-tests" not in command_log[0]


def test_run_auto_score_returns_none_on_reviewer_failure(loop_module, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(loop_module, "_build_reviewer_cmd", lambda root: ["python", "reviewer.py"])
    monkeypatch.setattr(
        loop_module.subprocess,
        "run",
        lambda cmd, **kwargs: CompletedProcess(cmd, 2, "", "failed"),
    )
    assert loop_module.run_auto_score(tmp_path, "test-skill") is None


def test_apply_improvement_is_dry_run_and_noop_safe(loop_module, tmp_path: Path, monkeypatch):
    agent_calls = []
    monkeypatch.setattr(
        loop_module.gemini_adapter,
        "run_gemini_agent",
        lambda *args, **kwargs: agent_calls.append(args) or True,
    )
    assert loop_module.apply_improvement(tmp_path, "test-skill", _report(), dry_run=True) is None
    assert (
        loop_module.apply_improvement(
            tmp_path, "test-skill", _report(improvements=[]), dry_run=False
        )
        is None
    )
    assert agent_calls == []


def test_apply_improvement_uses_gemini_and_auto_score_gate(
    loop_module, tmp_path: Path, monkeypatch
):
    agent_prompts: list[str] = []
    monkeypatch.setattr(
        loop_module.gemini_adapter,
        "run_gemini_agent",
        lambda prompt, **kwargs: agent_prompts.append(prompt) or True,
    )
    monkeypatch.setattr(loop_module, "run_auto_score", lambda *args, **kwargs: _report(85, []))
    monkeypatch.setattr(loop_module.shutil, "which", lambda name: None)

    result = loop_module.apply_improvement(tmp_path, "test-skill", _report(70), dry_run=False)
    assert result["auto_review"]["score"] == 85
    assert "test-skill" in agent_prompts[0]
    assert "git" not in agent_prompts[0].lower()


def test_apply_improvement_rejects_non_improving_score(loop_module, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(loop_module.gemini_adapter, "run_gemini_agent", lambda *a, **k: True)
    monkeypatch.setattr(loop_module, "run_auto_score", lambda *args, **kwargs: _report(70, []))
    monkeypatch.setattr(loop_module.shutil, "which", lambda name: None)
    assert loop_module.apply_improvement(tmp_path, "test-skill", _report(70)) is None


def test_write_summary_and_rotate_logs(loop_module, tmp_path: Path):
    report = _report(75, [])
    report["final_review"]["findings"] = [{"severity": "high"}, {"severity": "low"}]
    loop_module.write_daily_summary(tmp_path, "test-skill", report, improved=False)
    loop_module.write_daily_summary(tmp_path, "other-skill", report, improved=True)
    summary = next((tmp_path / loop_module.SUMMARY_DIR).glob("*_summary.md"))
    content = summary.read_text(encoding="utf-8")
    assert "test-skill" in content and "other-skill" in content
    assert "High findings: 1" in content

    log_dir = tmp_path / loop_module.LOG_DIR
    log_dir.mkdir(parents=True)
    old_log = log_dir / "old.log"
    old_log.write_text("old", encoding="utf-8")
    old_time = time.time() - (loop_module.LOG_RETENTION_DAYS + 1) * 86400
    os.utime(old_log, (old_time, old_time))
    new_log = log_dir / "new.log"
    new_log.write_text("new", encoding="utf-8")
    loop_module.rotate_logs(tmp_path)
    assert not old_log.exists() and new_log.exists()


def test_run_dry_run_records_not_improved_and_releases_lock(
    loop_module, tmp_path: Path, monkeypatch
):
    _make_skill(tmp_path)
    report = _report(70)
    saved_states: list[dict] = []
    apply_calls: list[bool] = []

    monkeypatch.setattr(loop_module, "run_auto_score", lambda *a, **k: report)
    monkeypatch.setattr(
        loop_module,
        "apply_improvement",
        lambda *a, **k: apply_calls.append(k["dry_run"]) or None,
    )
    monkeypatch.setattr(
        loop_module, "save_state", lambda root, state: saved_states.append(state.copy())
    )

    assert loop_module.run(tmp_path, dry_run=True) == 0
    assert apply_calls == [True]
    assert saved_states[-1]["history"][-1]["improved"] is False
    assert not (tmp_path / loop_module.LOCK_FILE).exists()


def test_run_skips_improvement_at_threshold(loop_module, tmp_path: Path, monkeypatch):
    _make_skill(tmp_path)
    monkeypatch.setattr(loop_module, "run_auto_score", lambda *a, **k: _report(95))
    apply_calls: list[object] = []
    monkeypatch.setattr(loop_module, "apply_improvement", lambda *a, **k: apply_calls.append(1))
    assert loop_module.run(tmp_path, dry_run=True) == 0
    assert apply_calls == []
