import pytest
from pathlib import Path
import re

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
    match = re.search(r"^---\s*
name:\s*(.+?)
", skill_md_content, re.MULTILINE)
    assert match, "Frontmatter with 'name' not found or malformed."
    name_in_frontmatter = match.group(1).strip()
    assert name_in_frontmatter == SKILL_DIR.name, (
        f"Frontmatter name '{name_in_frontmatter}' does not match skill directory name "
        f"'{SKILL_DIR.name}'."
    )

def test_frontmatter_description_present(skill_md_content):
    """Verify that SKILL.md has a 'description' in its frontmatter."""
    match = re.search(r"^---\s*
name:.*?
description:\s*(.+?)
", skill_md_content, re.MULTILINE | re.DOTALL)
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
    # Using re.escape to handle special characters in headings if any,
    # and ensuring it matches an H2 heading.
    pattern = re.compile(r"^##\s*" + re.escape(section_heading), re.MULTILINE)
    assert pattern.search(skill_md_content), f"Section '## {section_heading}' not found in SKILL.md."

def test_relative_paths_for_references(skill_md_content):
    """Verify that reference paths in SKILL.md use relative paths."""
    # This regex looks for `references/` within markdown code blocks or inline code
    # to specifically target the way references are shown in SKILL.md.
    # It explicitly excludes paths starting with 'skills/' or absolute paths.
    
    # Check "リファレンス読み込み" section
    ref_section_match = re.search(r"### リファレンス読み込み.*?```(.*?)```", skill_md_content, re.MULTILINE | re.DOTALL)
    assert ref_section_match, "Reference loading section not found."
    code_block = ref_section_match.group(1)
    
    # Ensure no 'skills/scenario-analyzer' or similar absolute paths in the code block
    assert "skills/scenario-analyzer/" not in code_block
    assert not re.search(r"^\s*(/|\w:/)", code_block, re.MULTILINE), "Absolute path found in reference code block."
    
    # Check "Resources" section
    resources_section_match = re.search(r"## Resources.*?### References(.*?)### Agents", skill_md_content, re.MULTILINE | re.DOTALL)
    assert resources_section_match, "Resources section (References subsection) not found."
    resources_content = resources_section_match.group(1)

    # Look for paths in the format `- `references/filename.md``
    # This pattern specifically targets markdown list items with backticks containing `references/`
    reference_path_pattern = re.compile(r"`(references/[^`]+?)`")
    found_relative_paths = reference_path_pattern.findall(resources_content)
    
    # Expecting 3 reference files as per SKILL.md
    assert len(found_relative_paths) == 3, f"Expected 3 relative reference paths, found {len(found_relative_paths)}."
    for path in found_relative_paths:
        assert path.startswith("references/"), f"Reference path '{path}' does not start with 'references/'."
        # Also ensure that it's not an absolute path or full project path
        assert not path.startswith("/") and not path.startswith("skills/"), f"Reference path '{path}' is not purely relative."


def test_sub_agent_prompt_structure(skill_md_content):
    """Verify that prompt structures for sub-agents are present."""
    # Test scenario-analyst prompt
    scenario_analyst_prompt_pattern = re.compile(
        r"#### Step 2\.1: scenario-analyst 呼び出し.*?```.*?prompt:\s*\|(.*?)```",
        re.MULTILINE | re.DOTALL
    )
    match_analyst = scenario_analyst_prompt_pattern.search(skill_md_content)
    assert match_analyst, "Prompt for scenario-analyst sub-agent not found."
    prompt_analyst_content = match_analyst.group(1)
    assert "## 対象ヘッドライン" in prompt_analyst_content
    assert "## イベントタイプ" in prompt_analyst_content
    assert "## リファレンス情報" in prompt_analyst_content
    assert "## 分析要件" in prompt_analyst_content

    # Test strategy-reviewer prompt
    strategy_reviewer_prompt_pattern = re.compile(
        r"#### Step 2\.2: strategy-reviewer 呼び出し.*?```.*?prompt:\s*\|(.*?)```",
        re.MULTILINE | re.DOTALL
    )
    match_reviewer = strategy_reviewer_prompt_pattern.search(skill_md_content)
    assert match_reviewer, "Prompt for strategy-reviewer sub-agent not found."
    prompt_reviewer_content = match_reviewer.group(1)
    assert "## 対象ヘッドライン" in prompt_reviewer_content
    assert "## 分析結果" in prompt_reviewer_content
    assert "## レビュー要件" in prompt_reviewer_content

def test_report_output_naming_and_location(skill_md_content):
    """Verify that the report output naming and location conventions are specified."""
    # Check "Output" section for table entry
    output_section_match = re.search(r"## Output.*?(```|
)(.*?)(```|
)", skill_md_content, re.MULTILINE | re.DOTALL)
    assert output_section_match, "Output section with table not found."
    output_table = output_section_match.group(2) # Capture content between fences or newlines

    assert "`reports/scenario_analysis_<topic>_YYYYMMDD.md`" in output_table, (
        "Report naming convention missing or incorrect in Output section table."
    )

    # Check "Step 3.2: レポート生成" for saving path
    report_gen_section_match = re.search(
        r"#### Step 3\.2: レポート生成.*?保存先:\s*`reports/scenario_analysis_<topic>_YYYYMMDD.md`",
        skill_md_content,
        re.MULTILINE | re.DOTALL
    )
    assert report_gen_section_match, (
        "Report saving path and naming convention missing or incorrect in 'レポート生成' section."
    )

    # Check "Important Notes" -> "出力先（重要）" section
    important_notes_section_match = re.search(
        r"## Important Notes.*?### 出力先（重要）(.*?)---",
        skill_md_content,
        re.MULTILINE | re.DOTALL
    )
    assert important_notes_section_match, "Important Notes -> 出力先（重要） section not found."
    important_notes_content = important_notes_section_match.group(1)

    assert "必ず `reports/` ディレクトリ配下に保存すること" in important_notes_content
    assert "プロジェクトルートに直接保存してはならない" in important_notes_content
    assert "reports/scenario_analysis_<topic>_YYYYMMDD.md" in important_notes_content
