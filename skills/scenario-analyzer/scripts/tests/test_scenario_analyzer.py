import re
from pathlib import Path

import pytest

# Assuming the test runs from the project root or similar context
# Adjust this if the test execution environment is different
SKILL_DIR = Path("skills/scenario-analyzer")
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"

@pytest.fixture
def skill_md_content():
    """Fixture to read the content of SKILL.md."""
    return SKILL_MD.read_text(encoding="utf-8")

def test_skill_md_exists():
    """Verify that SKILL.md exists."""
    assert SKILL_MD.exists(), f"SKILL.md not found at {SKILL_MD}"

def test_reference_files_exist():
    """Verify that all referenced markdown files exist."""
    expected_references = [
        REFERENCES_DIR / "headline_event_patterns.md",
        REFERENCES_DIR / "sector_sensitivity_matrix.md",
        REFERENCES_DIR / "scenario_playbooks.md",
    ]
    for ref_file in expected_references:
        assert ref_file.exists(), f"Reference file not found: {ref_file}"

def test_frontmatter_presence_and_name(skill_md_content):
    """Verify that SKILL.md has proper frontmatter with a name matching the directory."""
    match = re.search(r"^---\s*\nname:\s*(.+?)\n", skill_md_content, re.MULTILINE)
    assert match, "Frontmatter with 'name' not found or malformed."
    name_in_frontmatter = match.group(1).strip()
    assert name_in_frontmatter == SKILL_DIR.name, (
        f"Frontmatter name '{name_in_frontmatter}' does not match skill directory name "
        f"'{SKILL_DIR.name}'."
    )

def test_frontmatter_description_present(skill_md_content):
    """Verify that SKILL.md has a 'description' in its frontmatter."""
    match = re.search(r"^---\s*\nname:.*?\ndescription:\s*([^\n]+|\|[\s\S]+?)\n---", skill_md_content, re.MULTILINE)
    assert match, "Frontmatter 'description' not found or malformed."
    description_content = match.group(1).strip()
    assert len(description_content) > 10, "Description content is too short or empty."

@pytest.mark.parametrize("section_heading", [
    "When to Use This Skill",
    "Prerequisites",
    "Architecture",
    "Workflow",
    "Output",
    "Resources",
    "Important Notes",
    "Quality Checklist",
])
def test_key_sections_exist(skill_md_content, section_heading):
    """Verify that key sections are present in SKILL.md."""
    pattern = re.compile(r"^##\s*" + re.escape(section_heading), re.MULTILINE)
    assert pattern.search(skill_md_content), f"Section '## {section_heading}' not found in SKILL.md."

def test_relative_paths_for_references(skill_md_content):
    """Verify that reference paths in SKILL.md use relative paths."""
    ref_section_match = re.search(r"### (?:Reference Loading|リファレンス読み込み|Step 1\.3).*?```(.*?)```", skill_md_content, re.MULTILINE | re.DOTALL)
    assert ref_section_match, "Reference loading section not found."
    code_block = ref_section_match.group(1)

    assert "skills/scenario-analyzer/" not in code_block
    assert not re.search(r"^\s*(/|\w:/)", code_block, re.MULTILINE), "Absolute path found in reference code block."

    resources_section_match = re.search(r"## Resources.*?### References(.*?)### Agents", skill_md_content, re.MULTILINE | re.DOTALL)
    assert resources_section_match, "Resources section (References subsection) not found."
    resources_content = resources_section_match.group(1)

    reference_path_pattern = re.compile(r"`(references/[^`]+?)`")
    found_relative_paths = reference_path_pattern.findall(resources_content)

    assert len(found_relative_paths) == 3, f"Expected 3 relative reference paths, found {len(found_relative_paths)}."
    for path in found_relative_paths:
        assert path.startswith("references/"), f"Reference path '{path}' does not start with 'references/'."
        assert not path.startswith("/") and not path.startswith("skills/"), f"Reference path '{path}' is not purely relative."


def test_sub_agent_prompt_structure(skill_md_content):
    """Verify that prompt structures for sub-agents are present."""
    scenario_analyst_prompt_pattern = re.compile(
        r"#### Step 2\.1: (?:scenario-analyst Invocation|scenario-analyst 呼び出し).*?```.*?prompt:\s*\|(.*?)```",
        re.MULTILINE | re.DOTALL
    )
    match_analyst = scenario_analyst_prompt_pattern.search(skill_md_content)
    assert match_analyst, "Prompt for scenario-analyst sub-agent not found."
    prompt_analyst_content = match_analyst.group(1)
    assert re.search(r"## (Target Headline|対象ヘッドライン)", prompt_analyst_content)
    assert re.search(r"## (Event Type|イベントタイプ)", prompt_analyst_content)
    assert re.search(r"## (Reference Information|リファレンス情報)", prompt_analyst_content)
    assert re.search(r"## (Analysis Requirements|分析要件)", prompt_analyst_content)

    strategy_reviewer_prompt_pattern = re.compile(
        r"#### Step 2\.2: (?:strategy-reviewer Invocation|strategy-reviewer 呼び出し).*?```.*?prompt:\s*\|(.*?)```",
        re.MULTILINE | re.DOTALL
    )
    match_reviewer = strategy_reviewer_prompt_pattern.search(skill_md_content)
    assert match_reviewer, "Prompt for strategy-reviewer sub-agent not found."
    prompt_reviewer_content = match_reviewer.group(1)
    assert re.search(r"## (Target Headline|対象ヘッドライン)", prompt_reviewer_content)
    assert re.search(r"## (Analysis Results|分析結果)", prompt_reviewer_content)
    assert re.search(r"## (Review Requirements|レビュー要件)", prompt_reviewer_content)

def test_report_output_naming_and_location(skill_md_content):
    """Verify that the report output naming and location conventions are specified."""
    output_section_match = re.search(r"## Output(.*?)(?:##|\Z)", skill_md_content, re.MULTILINE | re.DOTALL)
    assert output_section_match, "Output section not found."
    output_content = output_section_match.group(1)

    assert "`reports/scenario_analysis_<topic>_YYYYMMDD.md`" in output_content, (
        "Report naming convention missing or incorrect in Output section."
    )

    assert re.search(
        r"Step 3\..*?`reports/scenario_analysis_<topic>_YYYYMMDD\.md`",
        skill_md_content,
        re.MULTILINE | re.DOTALL
    ), "Report saving path and naming convention missing or incorrect in Step 3."

    important_notes_section_match = re.search(
        r"## Important Notes.*?### (?:Output Location|出力先).*?---",
        skill_md_content,
        re.MULTILINE | re.DOTALL
    )
    assert important_notes_section_match, "Important Notes -> Output Location section not found."
    important_notes_content = important_notes_section_match.group(0)

    assert "reports/" in important_notes_content
    assert "reports/scenario_analysis_<topic>_YYYYMMDD.md" in important_notes_content
