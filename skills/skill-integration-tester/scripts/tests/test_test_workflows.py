"""Tests for validate_workflows.py — Skill Integration Tester."""

import json
from pathlib import Path

from validate_workflows import (
    _HANDOFF_CONTRACTS,
    _SKILL_CONTRACTS,
    check_naming_conventions,
    check_skill_exists,
    create_dry_run_fixtures,
    generate_report,
    parse_frontmatter_name,
    parse_workflows,
    resolve_skill_name,
    validate_handoff,
    validate_workflow,
)

# ── Sample GEMINI.md content for testing ─────────────────────────────

SAMPLE_GEMINI_MD = """\
## Multi-Skill Workflows

Skills are designed to be combined for comprehensive analysis:

**Daily Market Monitoring:**
1. Economic Calendar Fetcher \u2192 Check today's events
2. Earnings Calendar \u2192 Identify reporting companies
3. Market News Analyst \u2192 Review overnight developments

**Earnings Momentum Trading:**
1. Earnings Trade Analyzer \u2192 Score recent earnings reactions
2. PEAD Screener (Mode B) \u2192 Feed analyzer output and screen
3. Technical Analyst \u2192 Confirm weekly chart setups
"""


# ── parse_workflows ──────────────────────────────────────────────────


class TestParseWorkflows:
    def test_finds_named_workflows(self):
        workflows = parse_workflows(SAMPLE_GEMINI_MD)
        assert "Daily Market Monitoring" in workflows
        assert "Earnings Momentum Trading" in workflows

    def test_extracts_correct_step_count(self):
        workflows = parse_workflows(SAMPLE_GEMINI_MD)
        assert len(workflows["Daily Market Monitoring"]) == 3
        assert len(workflows["Earnings Momentum Trading"]) == 3

    def test_extracts_skill_display_and_action(self):
        workflows = parse_workflows(SAMPLE_GEMINI_MD)
        step = workflows["Daily Market Monitoring"][0]
        assert step["skill_display"] == "Economic Calendar Fetcher"
        assert step["action"] == "Check today's events"

    def test_strips_parenthetical_from_skill_name(self):
        workflows = parse_workflows(SAMPLE_GEMINI_MD)
        step = workflows["Earnings Momentum Trading"][1]
        assert step["skill_display"] == "PEAD Screener"

    def test_returns_empty_for_no_workflows(self):
        assert parse_workflows("No workflows here") == {}


# ── resolve_skill_name ───────────────────────────────────────────────


class TestResolveSkillName:
    def test_known_mapping(self):
        assert resolve_skill_name("Economic Calendar Fetcher") == "economic-calendar-fetcher"

    def test_case_insensitive(self):
        assert resolve_skill_name("SECTOR ANALYST") == "sector-analyst"

    def test_unknown_name_algorithmic_fallback(self):
        assert resolve_skill_name("My Custom Skill") == "my-custom-skill"


# ── _generate_display_map ────────────────────────────────────────────


class TestGenerateDisplayMap:
    def test_generates_correct_map_for_standard_skills(self, tmp_path):
        from validate_workflows import _generate_display_map

        # Create dummy skill directories
        skill_a_dir = tmp_path / "skill-a"
        skill_a_dir.mkdir()
        (skill_a_dir / "SKILL.md").write_text("---\nname: Skill A\n---\n")

        skill_b_dir = tmp_path / "skill-b"
        skill_b_dir.mkdir()
        (skill_b_dir / "SKILL.md").write_text("---\nname: Skill B\n---\n")

        display_map = _generate_display_map(tmp_path)
        assert display_map["skill a"] == "skill-a"
        assert display_map["skill b"] == "skill-b"

    def test_excludes_meta_skills_from_dynamic_generation(self, tmp_path):
        from validate_workflows import _generate_display_map

        # Create a directory that starts with '_' but has a SKILL.md
        meta_skill_dir = tmp_path / "_meta_example"
        meta_skill_dir.mkdir()
        (meta_skill_dir / "SKILL.md").write_text("---\nname: Meta Example\n---\n")

        # Create a regular skill
        regular_skill_dir = tmp_path / "regular-skill"
        regular_skill_dir.mkdir()
        (regular_skill_dir / "SKILL.md").write_text("---\nname: Regular Skill\n---\n")

        display_map = _generate_display_map(tmp_path)
        # Should not find the _meta_example from dynamic generation
        assert "meta example" not in display_map
        assert "regular skill" in display_map
        # Explicit meta skills should still be in the map (hardcoded in _generate_display_map)
        assert "screener skills" in display_map

    def test_handles_missing_skill_md_gracefully(self, tmp_path):
        from validate_workflows import _generate_display_map

        # Create skill directory without SKILL.md
        skill_c_dir = tmp_path / "skill-c"
        skill_c_dir.mkdir()

        display_map = _generate_display_map(tmp_path)
        assert "skill c" not in display_map
        # Ensure hardcoded meta skills are still present
        assert "screener skills" in display_map

    def test_handles_skill_md_without_frontmatter_name(self, tmp_path):
        from validate_workflows import _generate_display_map

        # Create skill with SKILL.md but no name in frontmatter
        skill_d_dir = tmp_path / "skill-d"
        skill_d_dir.mkdir()
        (skill_d_dir / "SKILL.md").write_text("No frontmatter here")

        display_map = _generate_display_map(tmp_path)
        assert "skill d" not in display_map
        # Ensure hardcoded meta skills are still present
        assert "screener skills" in display_map


# ── _load_skill_contracts ────────────────────────────────────────────


class TestLoadSkillContracts:
    def test_loads_valid_json(self, tmp_path):
        from validate_workflows import _load_skill_contracts

        # Create dummy contracts file
        contracts_dir = tmp_path / "skills" / "skill-integration-tester" / "references" / "workflow_contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        (contracts_dir / "skill_contracts.json").write_text(
            json.dumps({"skill-a": {"output_fields": ["field1"]}})
        )

        project_root = tmp_path
        contracts = _load_skill_contracts(project_root)
        assert "skill-a" in contracts
        assert contracts["skill-a"]["output_fields"] == ["field1"]

    def test_handles_missing_file(self, tmp_path, mocker):
        from validate_workflows import _load_skill_contracts

        project_root = tmp_path
        # Mock sys.exit to prevent actual exit during test
        mock_sys_exit = mocker.patch("sys.exit")
        # Ensure contracts directory does not exist to simulate FileNotFoundError
        # Or, ensure the specific file is not there
        (project_root / "skills" / "skill-integration-tester" / "references" / "workflow_contracts").mkdir(parents=True, exist_ok=True)
        
        _load_skill_contracts(project_root)
        mock_sys_exit.assert_called_once_with(1)

    def test_handles_malformed_json(self, tmp_path, mocker):
        from validate_workflows import _load_skill_contracts

        # Create malformed JSON contracts file
        contracts_dir = tmp_path / "skills" / "skill-integration-tester" / "references" / "workflow_contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        (contracts_dir / "skill_contracts.json").write_text("this is not json {")

        project_root = tmp_path
        mock_sys_exit = mocker.patch("sys.exit")
        _load_skill_contracts(project_root)
        mock_sys_exit.assert_called_once_with(1)


# ── _load_handoff_contracts ──────────────────────────────────────────


class TestLoadHandoffContracts:
    def test_loads_valid_json_and_converts_keys(self, tmp_path):
        from validate_workflows import _load_handoff_contracts

        # Create dummy contracts file
        contracts_dir = tmp_path / "skills" / "skill-integration-tester" / "references" / "workflow_contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        (contracts_dir / "handoff_contracts.json").write_text(
            json.dumps({"skill-a_skill-b": {"description": "A to B"}})
        )

        project_root = tmp_path
        contracts = _load_handoff_contracts(project_root)
        assert ("skill-a", "skill-b") in contracts
        assert contracts[("skill-a", "skill-b")]["description"] == "A to B"

    def test_handles_missing_file(self, tmp_path, mocker):
        from validate_workflows import _load_handoff_contracts

        project_root = tmp_path
        mock_sys_exit = mocker.patch("sys.exit")
        # Ensure contracts directory does not exist to simulate FileNotFoundError
        (project_root / "skills" / "skill-integration-tester" / "references" / "workflow_contracts").mkdir(parents=True, exist_ok=True)

        _load_handoff_contracts(project_root)
        mock_sys_exit.assert_called_once_with(1)

    def test_handles_malformed_json(self, tmp_path, mocker):
        from validate_workflows import _load_handoff_contracts

        # Create malformed JSON contracts file
        contracts_dir = tmp_path / "skills" / "skill-integration-tester" / "references" / "workflow_contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        (contracts_dir / "handoff_contracts.json").write_text("this is not json [")

        project_root = tmp_path
        mock_sys_exit = mocker.patch("sys.exit")
        _load_handoff_contracts(project_root)
        mock_sys_exit.assert_called_once_with(1)


# ── check_skill_exists ──────────────────────────────────────────────


class TestCheckSkillExists:
    def test_exists_when_skill_md_present(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        assert check_skill_exists("my-skill", tmp_path)

    def test_not_exists_when_missing(self, tmp_path):
        assert not check_skill_exists("nonexistent", tmp_path)


# ── parse_frontmatter_name ──────────────────────────────────────────


class TestParseFrontmatterName:
    def test_extracts_name(self, tmp_path):
        md = tmp_path / "SKILL.md"
        md.write_text("---\nname: foo-bar\ndescription: X\n---\nBody")
        assert parse_frontmatter_name(md) == "foo-bar"

    def test_returns_none_for_no_frontmatter(self, tmp_path):
        md = tmp_path / "SKILL.md"
        md.write_text("No frontmatter here")
        assert parse_frontmatter_name(md) is None

    def test_returns_none_for_missing_file(self, tmp_path):
        assert parse_frontmatter_name(tmp_path / "missing.md") is None


# ── check_naming_conventions ─────────────────────────────────────────


class TestCheckNamingConventions:
    def test_valid_skill_no_violations(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "run_check.py").write_text("")
        assert check_naming_conventions("my-skill", tmp_path) == []

    def test_detects_non_snake_case_script(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "RunAnalysis.py").write_text("")
        violations = check_naming_conventions("my-skill", tmp_path)
        assert any("snake_case" in v for v in violations)

    def test_detects_name_mismatch(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: wrong-name\n---\n")
        violations = check_naming_conventions("my-skill", tmp_path)
        assert any("does not match" in v for v in violations)


# ── validate_handoff ─────────────────────────────────────────────────


class TestValidateHandoff:
    def _make_skill(self, skills_dir, name):
        d = skills_dir / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n")

    def test_known_valid_contract(self, tmp_path):
        self._make_skill(tmp_path, "earnings-trade-analyzer")
        self._make_skill(tmp_path, "pead-screener")
        result = validate_handoff("earnings-trade-analyzer", "pead-screener", tmp_path)
        assert result["status"] == "valid"

    def test_missing_producer_is_broken(self, tmp_path):
        self._make_skill(tmp_path, "pead-screener")
        result = validate_handoff("nonexistent", "pead-screener", tmp_path)
        assert result["status"] == "broken"

    def test_unknown_pair_is_no_contract(self, tmp_path):
        self._make_skill(tmp_path, "skill-a")
        self._make_skill(tmp_path, "skill-b")
        result = validate_handoff("skill-a", "skill-b", tmp_path)
        assert result["status"] == "no_contract"


# ── validate_workflow ────────────────────────────────────────────────


class TestValidateWorkflow:
    def test_all_steps_exist(self, tmp_path):
        for name in ("skill-a", "skill-b"):
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
        steps = [
            {"skill_display": "skill-a", "action": "do A"},
            {"skill_display": "skill-b", "action": "do B"},
        ]
        result = validate_workflow("Test", steps, tmp_path)
        assert result["status"] != "broken"

    def test_missing_step_marks_broken(self, tmp_path):
        d = tmp_path / "skill-a"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: skill-a\n---\n")
        steps = [
            {"skill_display": "skill-a", "action": "do A"},
            {"skill_display": "nonexistent", "action": "do B"},
        ]
        result = validate_workflow("Test", steps, tmp_path)
        assert result["status"] == "broken"


# ── generate_report ──────────────────────────────────────────────────


class TestGenerateReport:
    def _make_result(self, status="valid"):
        return {
            "workflow": "Test",
            "step_count": 1,
            "steps": [
                {
                    "index": 1,
                    "skill_display": "A",
                    "skill_name": "a",
                    "action": "do",
                    "exists": True,
                    "is_meta": False,
                    "has_contract": False,
                }
            ],
            "handoffs": [],
            "naming_violations": [],
            "status": status,
        }

    def test_creates_json_and_md_files(self, tmp_path):
        json_p, md_p = generate_report([self._make_result()], False, [], tmp_path)
        assert json_p.is_file()
        assert md_p.is_file()

    def test_json_report_schema(self, tmp_path):
        json_p, _ = generate_report([self._make_result()], False, [], tmp_path)
        data = json.loads(json_p.read_text())
        assert data["schema_version"] == "1.0"
        assert data["summary"]["total_workflows"] == 1
        assert data["summary"]["valid"] == 1
        assert data["summary"]["broken"] == 0

    def test_dry_run_includes_fixtures(self, tmp_path):
        json_p, _ = generate_report(
            [self._make_result()],
            True,
            ["/tmp/fixture.json"],
            tmp_path,
        )
        data = json.loads(json_p.read_text())
        assert data["dry_run"] is True
        assert "/tmp/fixture.json" in data["fixtures_created"]


# ── create_dry_run_fixtures ──────────────────────────────────────────


class TestCreateDryRunFixtures:
    def test_creates_fixture_files(self, tmp_path):
        workflows = {
            "Test": [
                {
                    "skill_display": "Earnings Calendar",
                    "action": "check",
                },
            ],
        }
        fixtures = create_dry_run_fixtures(workflows, tmp_path)
        assert len(fixtures) > 0
        data = json.loads(Path(fixtures[0]).read_text())
        assert data["_fixture"] is True
        assert data["_skill"] == "earnings-calendar"
        assert data["schema_version"] == "1.0"

    def test_skips_unknown_skills(self, tmp_path):
        workflows = {
            "Test": [
                {
                    "skill_display": "Unknown Skill XYZ",
                    "action": "do",
                },
            ],
        }
        fixtures = create_dry_run_fixtures(workflows, tmp_path)
        assert len(fixtures) == 0

    def test_deduplicates_across_workflows(self, tmp_path):
        workflows = {
            "WF1": [
                {
                    "skill_display": "Earnings Calendar",
                    "action": "a",
                },
            ],
            "WF2": [
                {
                    "skill_display": "Earnings Calendar",
                    "action": "b",
                },
            ],
        }
        fixtures = create_dry_run_fixtures(workflows, tmp_path)
        assert len(fixtures) == 1


        # ── Test Main Function ───────────────────────────────────────────────

        class TestMainFunction:
            def test_main_runs_successfully(self, tmp_path, mocker):
                # Create dummy GEMINI.md and skill directories for the test
                gemini_md_content = """\
        ## Multi-Skill Workflows

        **Daily Market Monitoring:**
        1. Economic Calendar Fetcher \u2192 Check today's events
        """
            (tmp_path / "GEMINI.md").write_text(gemini_md_content)

            economic_calendar_fetcher_dir = tmp_path / "skills" / "economic-calendar-fetcher"
            economic_calendar_fetcher_dir.mkdir(parents=True, exist_ok=True)
            (economic_calendar_fetcher_dir / "SKILL.md").write_text("---\nname: economic-calendar-fetcher\n---\n")

            # Mock sys.argv to pass command-line arguments
            mocker.patch("sys.argv", [
                "validate_workflows.py",
                "--gemini-md", str(tmp_path / "GEMINI.md"),
                "--skills-dir", str(tmp_path / "skills"),
                "--output-dir", str(tmp_path / "reports")
            ])

            # Mock sys.exit to prevent the test from exiting
            mock_sys_exit = mocker.patch("sys.exit")

            # Call the main function
            from validate_workflows import main
            main()

            # Assertions
            mock_sys_exit.assert_called_once_with(0)  # Expect successful execution
            assert (tmp_path / "reports").is_dir()
            # Verify reports are generated
            assert any(f.name.startswith("integration_test_") and f.suffix == ".json" for f in (tmp_path / "reports").iterdir())
            assert any(f.name.startswith("integration_test_") and f.suffix == ".md" for f in (tmp_path / "reports").iterdir())

        def test_main_exits_with_error_if_gemini_md_not_found(self, tmp_path, mocker):
            mocker.patch("sys.argv", [
                "validate_workflows.py",
                "--gemini-md", str(tmp_path / "non_existent_GEMINI.md"),
                "--skills-dir", str(tmp_path / "skills"),
                "--output-dir", str(tmp_path / "reports")
            ])
            mock_sys_exit = mocker.patch("sys.exit")

            from validate_workflows import main
            main()
            mock_sys_exit.assert_called_once_with(1)

        def test_main_exits_with_error_if_skills_dir_not_found(self, tmp_path, mocker):
            # Create dummy GEMINI.md for the test
            (tmp_path / "GEMINI.md").write_text("## Multi-Skill Workflows")

            mocker.patch("sys.argv", [
                "validate_workflows.py",
                "--gemini-md", str(tmp_path / "GEMINI.md"),
                "--skills-dir", str(tmp_path / "non_existent_skills"),
                "--output-dir", str(tmp_path / "reports")
            ])
            mock_sys_exit = mocker.patch("sys.exit")

            from validate_workflows import main
            main()
            mock_sys_exit.assert_called_once_with(1)

        # ── Contract data integrity ──────────────────────────────────────────


        class TestContractIntegrity:
            def test_all_handoff_producers_have_contracts(self):
                """Every producer in _HANDHOFF_CONTRACTS must exist in _SKILL_CONTRACTS."""
                # _SKILL_CONTRACTS and _HANDHOFF_CONTRACTS are global variables loaded in main.
                # For unit tests, we need to ensure they are available or mocked.
                # Since these tests run independently, we will assume a setup
                # where these are loaded or available from the `validate_workflows` module.
                # Or, we can load them manually for this specific test class.
                from validate_workflows import _HANDHOFF_CONTRACTS, _SKILL_CONTRACTS
                for (producer, _consumer), _contract in _HANDHOFF_CONTRACTS.items():
                    assert producer in _SKILL_CONTRACTS, (
                        f"Handoff producer '{producer}' missing from _SKILL_CONTRACTS"
                    )

        def test_handoff_required_fields_subset_of_output(self):
            """Required fields in handoff must be subset of producer output."""
            from validate_workflows import _HANDOFF_CONTRACTS, _SKILL_CONTRACTS
            for (producer, consumer), contract in _HANDOFF_CONTRACTS.items():
                producer_fields = set(_SKILL_CONTRACTS[producer]["output_fields"])
                required = set(contract["required_fields"])
                missing = required - producer_fields
                assert not missing, (
                    f"Handoff {producer}\u2192{consumer}: "
                    f"required fields {missing} not in producer output"
                )

