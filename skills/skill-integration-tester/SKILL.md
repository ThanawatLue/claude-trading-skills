---
name: skill-integration-tester
description: Validate multi-skill workflows defined in GEMINI.md by checking skill existence, inter-skill data contracts (JSON schema compatibility), file naming conventions, and handoff integrity. Use when adding new workflows, modifying skill outputs, or verifying pipeline health before release.
requires_api_key: false
---

# Skill Integration Tester

## Overview

Validate multi-skill workflows defined in GEMINI.md (Daily Market Monitoring,
Weekly Strategy Review, Earnings Momentum Trading, etc.) by executing each step
in sequence. Check inter-skill data contracts for JSON schema compatibility
between output of step N and input of step N+1, verify file naming conventions,
and report broken handoffs. Supports dry-run mode with synthetic fixtures.

## When to Use

- After adding or modifying a multi-skill workflow in GEMINI.md
- After changing a skill's output format (JSON schema, file naming)
- Before releasing new skills to verify pipeline compatibility
- When debugging broken handoffs between consecutive workflow steps
- As a CI pre-check for pull requests touching skill scripts

## Prerequisites

- Python 3.9+
- No API keys required
- No third-party Python packages required (uses only standard library)

## Workflow

### Step 1: Run Integration Validation

Execute the validation script against the project's GEMINI.md:

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --output-dir reports/
```

This parses all `**Workflow Name:**` blocks from the Multi-Skill Workflows
section, resolves each step's display name to a skill directory, and validates
existence, contracts, and naming.

### Step 2: Validate a Specific Workflow

Target a single workflow by name substring:

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --workflow "Earnings Momentum" \
  --output-dir reports/
```

### Step 3: Dry-Run with Synthetic Fixtures

Create synthetic fixture JSON files for each skill's expected output and
validate contract compatibility without real data:

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --dry-run \
  --output-dir reports/
```

Fixture files are written to `reports/fixtures/` with `_fixture` flag set.

### Step 4: Review Results

Open the generated Markdown report for a human-readable summary, or parse
the JSON report for programmatic consumption. Each workflow shows:
- Step-by-step skill existence checks
- Handoff contract validation (PASS / FAIL / N/A)
- File naming convention violations
- Overall workflow status (valid / broken / warning)

### Step 5: Fix Broken Handoffs

For each `FAIL` handoff, verify that:
1. The producer skill's output contains all required fields
2. The consumer skill's input parameter accepts the producer's output format
3. File naming patterns are consistent between producer output and consumer input

## Output Format

### JSON Report

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-03-01T12:00:00+00:00",
  "dry_run": false,
  "summary": {
    "total_workflows": 8,
    "valid": 6,
    "broken": 1,
    "warnings": 1
  },
  "workflows": [
    {
      "workflow": "Daily Market Monitoring",
      "step_count": 4,
      "status": "valid",
      "steps": [
        {
          "index": 1,
          "skill_display": "Economic Calendar Fetcher",
          "skill_name": "economic-calendar-fetcher",
          "action": "Fetch upcoming economic events",
          "exists": true,
          "is_meta": false,
          "has_contract": true
        }
      ],
      "handoffs": [
        {
          "producer": "economic-calendar-fetcher",
          "consumer": "market-news-analyst",
          "status": "valid",
          "details": [
            "Contract valid: Market News Analyst reads economic events."
          ]
        }
      ],
      "naming_violations": []
    }
  ]
}
```

### Markdown Report

Structured report with per-workflow sections showing step validation,
handoff status, and naming violations.

Reports are saved to `reports/` with filenames
`integration_test_YYYY-MM-DD_HHMMSS.{json,md}`.

## Resources

- `scripts/validate_workflows.py` -- Main validation script
- `references/workflow_contracts/skill_contracts.json` -- Defines expected output fields for each skill.
- `references/workflow_contracts/handoff_contracts.json` -- Defines required input fields for consumer skills from producer skills.

## Adding New Contracts

New skill contracts (defining a skill's output fields) should be added to
`references/workflow_contracts/skill_contracts.json`. Each entry is a key-value
pair where the key is the skill's directory name and the value is an object
describing its output, specifically an `output_fields` array.

Example `skill_contracts.json` entry:
```json
{
  "my-new-skill": {
    "output_fields": ["data_point_1", "data_point_2"],
    "description": "Description of what my-new-skill outputs"
  }
}
```

New handoff contracts (defining the required input fields for a consumer skill
from a producer skill) should be added to
`references/workflow_contracts/handoff_contracts.json`. Each entry's key is
a string formatted as `"producer-skill-name_consumer-skill-name"`, and its
value is an object containing a `required_fields` array.

Example `handoff_contracts.json` entry:
```json
{
  "producer-skill_consumer-skill": {
    "required_fields": ["data_point_1"],
    "description": "Consumer skill requires data_point_1 from producer"
  }
}
```

## Key Principles

1. No API keys required -- all validation is local and offline
2. Non-destructive -- reads SKILL.md and GEMINI.md only, never modifies skills
3. Deterministic -- same inputs always produce same validation results
