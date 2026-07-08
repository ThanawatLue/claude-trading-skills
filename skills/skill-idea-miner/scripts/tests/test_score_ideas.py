"""Tests for the skill idea scorer and deduplication script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


@pytest.fixture(scope="module")
def score_module():
    """Load score_ideas.py as a module via importlib."""
    script_path = Path(__file__).resolve().parents[1] / "score_ideas.py"
    spec = importlib.util.spec_from_file_location("score_ideas", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load score_ideas.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ── Jaccard similarity tests ──


def test_jaccard_identical(score_module):
    """Identical text returns 1.0."""
    assert score_module.jaccard_similarity("hello world", "hello world") == 1.0


def test_jaccard_partial(score_module):
    """Partially overlapping words return expected value."""
    # "hello world" -> {"hello", "world"}
    # "hello there" -> {"hello", "there"}
    # intersection = {"hello"}, union = {"hello", "world", "there"}
    # Jaccard = 1/3
    result = score_module.jaccard_similarity("hello world", "hello there")
    assert abs(result - 1.0 / 3.0) < 1e-9


def test_jaccard_disjoint(score_module):
    """No common words returns 0.0."""
    assert score_module.jaccard_similarity("alpha beta", "gamma delta") == 0.0


def test_jaccard_empty(score_module):
    """Empty string returns 0.0."""
    assert score_module.jaccard_similarity("", "hello") == 0.0
    assert score_module.jaccard_similarity("hello", "") == 0.0
    assert score_module.jaccard_similarity("", "") == 0.0


# ── list_existing_skills tests ──


def _make_skill(project_root: Path, name: str, description: str = "test") -> None:
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n# {name}\n",
        encoding="utf-8",
    )


def test_list_existing_skills(score_module, tmp_path: Path):
    """Create mock skills/*/SKILL.md and verify parsing."""
    _make_skill(tmp_path, "alpha-skill", "Alpha skill for testing")
    _make_skill(tmp_path, "beta-skill", "Beta skill for testing")

    results = score_module.list_existing_skills(tmp_path)

    assert len(results) == 2
    names = {r["name"] for r in results}
    assert "alpha-skill" in names
    assert "beta-skill" in names

    # Verify descriptions are parsed
    alpha = next(r for r in results if r["name"] == "alpha-skill")
    assert alpha["description"] == "Alpha skill for testing"


def test_list_existing_skills_skips_nested(score_module, tmp_path: Path):
    """Verify skills/**/SKILL.md nested entries are NOT returned."""
    _make_skill(tmp_path, "top-skill", "Top level skill")

    # Create a nested SKILL.md that should NOT be picked up
    nested_dir = tmp_path / "skills" / "top-skill" / "sub-component"
    nested_dir.mkdir(parents=True, exist_ok=True)
    (nested_dir / "SKILL.md").write_text(
        "---\nname: nested-skill\ndescription: Should not appear\n---\n",
        encoding="utf-8",
    )

    results = score_module.list_existing_skills(tmp_path)

    names = {r["name"] for r in results}
    assert "top-skill" in names
    assert "nested-skill" not in names
    assert len(results) == 1


def test_parse_yaml_frontmatter_valid(score_module):
    """Valid YAML frontmatter is parsed correctly."""
    content = "---\nname: Test Skill\ndescription: A test description\n---\n# Content"
    result = score_module._parse_yaml_frontmatter(content)
    assert result == {"name": "Test Skill", "description": "A test description"}


def test_parse_yaml_frontmatter_no_frontmatter(score_module):
    """Content without frontmatter returns None."""
    content = "# Just a markdown file"
    result = score_module._parse_yaml_frontmatter(content)
    assert result is None


def test_parse_yaml_frontmatter_malformed(score_module):
    """Malformed YAML frontmatter returns None."""
    content = "---\nname: Test Skill\ndescription: - this is bad\n---\n# Content"
    result = score_module._parse_yaml_frontmatter(content)
    assert result is None


# ── load_backlog tests ──


def test_load_backlog_existing_valid(score_module, tmp_path: Path):
    """Loads an existing valid backlog file."""
    backlog_path = tmp_path / "backlog.yaml"
    backlog_data = {
        "updated_at_utc": "2026-03-01T10:00:00Z",
        "ideas": [{"id": "idea_001", "title": "Test Idea"}],
    }
    backlog_path.write_text(yaml.safe_dump(backlog_data))

    result = score_module.load_backlog(backlog_path)
    assert result == backlog_data


def test_load_backlog_empty_file(score_module, tmp_path: Path):
    """Returns empty structure for an empty backlog file."""
    backlog_path = tmp_path / "backlog.yaml"
    backlog_path.write_text("")

    result = score_module.load_backlog(backlog_path)
    assert "ideas" in result
    assert result["ideas"] == []


def test_load_backlog_non_existent(score_module, tmp_path: Path):
    """Returns empty structure if backlog file does not exist."""
    backlog_path = tmp_path / "non_existent_backlog.yaml"
    result = score_module.load_backlog(backlog_path)
    assert "ideas" in result
    assert result["ideas"] == []


def test_load_backlog_malformed(score_module, tmp_path: Path, caplog):
    """Logs a warning and returns empty structure for a malformed backlog file."""
    backlog_path = tmp_path / "malformed_backlog.yaml"
    backlog_path.write_text("[\n}\n")

    with caplog.at_level(score_module.logging.WARNING):
        result = score_module.load_backlog(backlog_path)
    assert "Failed to load backlog" in caplog.text
    assert "ideas" in result
    assert result["ideas"] == []
