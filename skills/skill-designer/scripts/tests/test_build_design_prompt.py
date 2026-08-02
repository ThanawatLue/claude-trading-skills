"""Tests for build_design_prompt.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest
from build_design_prompt import (
    REFERENCES_DIR,
    build_prompt,
    list_existing_skills,
    load_references,
    main,
)


def _make_idea(title: str = "test-skill", description: str = "A test skill") -> dict:
    return {"title": title, "description": "A test skill", "category": "testing"}


def test_build_prompt_uses_skill_name():
    """Prompt uses the --skill-name value for directory and frontmatter name."""
    refs = load_references(REFERENCES_DIR)
    prompt = build_prompt(_make_idea(), "my-custom-name", refs, [])

    assert "skills/my-custom-name/" in prompt
    assert "`my-custom-name`" in prompt
    assert "name:` field MUST be exactly `my-custom-name`" in prompt


def test_build_prompt_includes_refs():
    """All three reference file contents are embedded in the prompt."""
    refs = load_references(REFERENCES_DIR)

    # All 3 references should be loaded
    assert len(refs) == 3
    assert "skill-structure-guide.md" in refs
    assert "quality-checklist.md" in refs
    assert "skill-template.md" in refs

    prompt = build_prompt(_make_idea(), "test-skill", refs, [])

    # Each reference content should appear in the prompt
    assert "--- BEGIN skill-structure-guide.md ---" in prompt
    assert "--- BEGIN quality-checklist.md ---" in prompt
    assert "--- BEGIN skill-template.md ---" in prompt


def test_build_prompt_frontmatter_name_matches():
    """Prompt instructs Claude to set name: matching the skill_name."""
    refs = load_references(REFERENCES_DIR)
    prompt = build_prompt(_make_idea(), "exact-name-here", refs, ["existing-a", "existing-b"])

    # Should instruct the frontmatter name to match
    assert "exact-name-here" in prompt
    # Should list existing skills for deduplication
    assert "existing-a" in prompt
    assert "existing-b" in prompt


def test_list_existing_skills_empty_dir(tmp_path: Path):
    """list_existing_skills returns empty if skills dir doesn't exist."""
    assert list_existing_skills(tmp_path) == []


def test_list_existing_skills_no_skill_files(tmp_path: Path):
    """list_existing_skills ignores directories without SKILL.md."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "not-a-skill").mkdir()
    (skills_dir / "another-dir").mkdir()
    (skills_dir / "skill-with-no-md").mkdir()
    (skills_dir / "skill-with-md-file").mkdir()
    (skills_dir / "skill-with-md-file" / "SKILL.md").write_text("content")

    assert list_existing_skills(tmp_path) == ["skill-with-md-file"]


def test_list_existing_skills_with_skills(tmp_path: Path):
    """list_existing_skills correctly lists existing skills."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "skill-a").mkdir()
    (skills_dir / "skill-a" / "SKILL.md").write_text("content")
    (skills_dir / "skill-b").mkdir()
    (skills_dir / "skill-b" / "SKILL.md").write_text("content")
    (skills_dir / "skill-c").mkdir()
    (skills_dir / "skill-c" / "SKILL.md").write_text("content")

    assert list_existing_skills(tmp_path) == ["skill-a", "skill-b", "skill-c"]


def test_list_existing_skills_limit(tmp_path: Path):
    """list_existing_skills respects the limit."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    for i in range(25):  # Create more than MAX_EXISTING_SKILLS
        skill_name = f"skill-{i:02d}"
        (skills_dir / skill_name).mkdir()
        (skills_dir / skill_name / "SKILL.md").write_text("content")

    # MAX_EXISTING_SKILLS is 20 in build_design_prompt.py
    expected_skills = [f"skill-{i:02d}" for i in range(20)]
    assert list_existing_skills(tmp_path) == expected_skills


@pytest.fixture
def mock_references_dir(tmp_path):
    """Fixture to create dummy reference files."""
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()
    (refs_dir / "skill-structure-guide.md").write_text("structure content")
    (refs_dir / "quality-checklist.md").write_text("quality content")
    (refs_dir / "skill-template.md").write_text("template content")
    return refs_dir


@mock.patch("build_design_prompt.REFERENCES_DIR")
def test_main_missing_idea_json(mock_references_dir, capsys, tmp_path):
    """Test main function with a missing idea JSON file."""
    mock_references_dir.resolve.return_value = (
        tmp_path / "references"
    )  # Point to our temporary directory
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "skill-structure-guide.md").write_text("structure content")
    (tmp_path / "references" / "quality-checklist.md").write_text("quality content")
    (tmp_path / "references" / "skill-template.md").write_text("template content")

    with mock.patch.object(
        sys,
        "argv",
        [
            "build_design_prompt.py",
            "--idea-json",
            "non_existent.json",
            "--skill-name",
            "test-skill",
        ],
    ):
        exit_code = main()
        assert exit_code == 1
    outerr = capsys.readouterr()
    assert "Error: idea JSON not found" in outerr.err


@mock.patch("build_design_prompt.REFERENCES_DIR")
def test_main_malformed_idea_json(mock_references_dir, capsys, tmp_path):
    """Test main function with a malformed idea JSON file."""
    idea_file = tmp_path / "malformed.json"
    idea_file.write_text("{'title': 'invalid json',}")  # Malformed JSON

    mock_references_dir.resolve.return_value = (
        tmp_path / "references"
    )  # Point to our temporary directory
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "skill-structure-guide.md").write_text("structure content")
    (tmp_path / "references" / "quality-checklist.md").write_text("quality content")
    (tmp_path / "references" / "skill-template.md").write_text("template content")

    with mock.patch.object(
        sys,
        "argv",
        ["build_design_prompt.py", "--idea-json", str(idea_file), "--skill-name", "test-skill"],
    ):
        exit_code = main()
        assert exit_code == 1
    outerr = capsys.readouterr()
    assert "Error: idea JSON is malformed or empty" in outerr.err


@mock.patch("build_design_prompt.REFERENCES_DIR")
def test_main_missing_skill_name(mock_references_dir, capsys, tmp_path):
    """Test main function with a missing skill-name argument."""
    idea_file = tmp_path / "idea.json"
    idea_file.write_text(json.dumps(_make_idea()))

    mock_references_dir.resolve.return_value = (
        tmp_path / "references"
    )  # Point to our temporary directory
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "skill-structure-guide.md").write_text("structure content")
    (tmp_path / "references" / "quality-checklist.md").write_text("quality content")
    (tmp_path / "references" / "skill-template.md").write_text("template content")

    with mock.patch.object(sys, "argv", ["build_design_prompt.py", "--idea-json", str(idea_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 2  # argparse exits with 2 for missing required args
    outerr = capsys.readouterr()
    assert "the following arguments are required: --skill-name" in outerr.err


@mock.patch("build_design_prompt.REFERENCES_DIR")
@mock.patch(
    "build_design_prompt.load_references", return_value={}
)  # Mock load_references to return empty dict
def test_main_missing_reference_files(mock_references_dir, mock_load_references, capsys, tmp_path):
    """Test main function when reference files are missing."""
    idea_file = tmp_path / "idea.json"
    idea_file.write_text(json.dumps(_make_idea()))

    mock_references_dir.resolve.return_value = (
        tmp_path / "references"
    )  # Point to our temporary directory
    (tmp_path / "references").mkdir()
    # Don't create reference files

    with mock.patch.object(
        sys,
        "argv",
        ["build_design_prompt.py", "--idea-json", str(idea_file), "--skill-name", "test-skill"],
    ):
        exit_code = main()
        assert exit_code == 1
    outerr = capsys.readouterr()
    assert "Error: reference files missing" in outerr.err


@mock.patch("build_design_prompt.load_references")
@mock.patch("builtins.print")  # Mock builtins.print
def test_main_success(mock_print, mock_load_references, capsys, tmp_path):
    """Test successful execution of main function."""
    idea_file = tmp_path / "idea.json"
    idea_file.write_text(
        json.dumps(_make_idea(title="My New Skill", description="A skill for testing."))
    )

    skill_name = "my-new-skill"

    (tmp_path / "references").mkdir()
    # No need to write content to disk, as load_references is mocked
    mock_load_references.return_value = {
        "skill-structure-guide.md": "mock structure content",
        "quality-checklist.md": "mock quality content",
        "skill-template.md": "mock template content",
    }

    # Create a dummy skills directory for list_existing_skills
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "existing-skill").mkdir()
    (skills_dir / "existing-skill" / "SKILL.md").write_text("content")

    with mock.patch.object(
        sys,
        "argv",
        [
            "build_design_prompt.py",
            "--idea-json",
            str(idea_file),
            "--skill-name",
            skill_name,
            "--project-root",
            str(tmp_path),
        ],
    ):
        exit_code = main()
        assert exit_code == 0

    # Assert that print was called with the correct prompt
    mock_print.assert_called_once()
    printed_prompt = mock_print.call_args[0][0]  # Get the first argument of the first call

    expected_idea = _make_idea(title="My New Skill", description="A skill for testing.")
    expected_skill_name = "my-new-skill"
    expected_refs = {
        "skill-structure-guide.md": "mock structure content",
        "quality-checklist.md": "mock quality content",
        "skill-template.md": "mock template content",
    }
    expected_existing = ["existing-skill"]  # From the dummy skills_dir

    # Reconstruct the expected prompt using the same logic as build_prompt
    expected_existing_list = (
        "\n".join(f"- {s}" for s in expected_existing) if expected_existing else "- (none)"
    )
    expected_ref_sections = ""
    for name, content in expected_refs.items():
        expected_ref_sections += f"\n\n--- BEGIN {name} ---\n{content}\n--- END {name} ---"

    expected_prompt = f"""Design and create a complete Claude skill named '{expected_skill_name}'.

## Idea Specification

- **Title**: {expected_idea.get("title", "unnamed")}
- **Description**: {expected_idea.get("description", "")}
- **Category**: {expected_idea.get("category", "general")}

## Requirements

1. Create the skill directory at `skills/{expected_skill_name}/`
2. The YAML frontmatter `name:` field MUST be exactly `{expected_skill_name}`
3. Follow the structure guide, quality checklist, and template below
4. Create all required files:
   - `skills/{expected_skill_name}/SKILL.md` (with YAML frontmatter)
   - At least one file in `skills/{expected_skill_name}/references/`
   - At least one script in `skills/{expected_skill_name}/scripts/` (unless this is a knowledge-only skill)
   - Test directory `skills/{expected_skill_name}/scripts/tests/` with conftest.py and at least 3 tests
5. Scripts must use `--output-dir reports/` as default output location
6. Do NOT duplicate functionality of existing skills listed below
7. Use imperative verb forms in SKILL.md workflow steps
8. All scripts must use relative paths (no hardcoded absolute paths)

## Existing Skills (do not duplicate)

{expected_existing_list}

## Reference Documents
{expected_ref_sections}

## Instructions

Create all the files for the skill now. Start with SKILL.md, then references, then scripts, then tests.
Ensure the skill scores well on all 5 quality categories (metadata, workflow, execution safety, artifacts, tests).
"""
    assert printed_prompt == expected_prompt
