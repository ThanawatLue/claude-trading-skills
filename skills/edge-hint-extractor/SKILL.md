---
name: edge-hint-extractor
description: Extract edge hints from daily market observations and news reactions, with optional LLM ideation, and output canonical hints.yaml for downstream concept synthesis and auto detection.
---

# Edge Hint Extractor

## Overview

Convert raw observation signals (`market_summary`, `anomalies`, `news reactions`) into structured edge hints.
This skill is the first stage in the split workflow: `observe -> abstract -> design -> pipeline`.

## When to Use

- You want to turn daily market observations into reusable hint objects.
- You want LLM-generated ideas constrained by current anomalies/news context.
- You need a clean `hints.yaml` input for concept synthesis or auto detection.

## Prerequisites

- Python 3.9+
- `PyYAML`
- Optional inputs from detector run:
  - `market_summary.json`
  - `anomalies.json`
  - `news_reactions.csv` or `news_reactions.json`

## Output

- `hints.yaml` containing:
  - `hints` list
  - generation metadata
  - rule/LLM hint counts

## Workflow

1. Gather observation files (`market_summary`, `anomalies`, optional news reactions).
2. Run `scripts/build_hints.py` to generate deterministic hints.
3. Optionally augment hints with LLM ideas via one of two methods:
   - a. `--llm-ideas-cmd` — pipe data to an external LLM CLI (subprocess).
   - b. `--llm-ideas-file PATH` — load pre-written hints from a YAML file (for Claude Code workflows where Claude generates hints itself).
4. Pass `hints.yaml` into concept synthesis or auto detection.

Note: `--llm-ideas-cmd` and `--llm-ideas-file` are mutually exclusive.

## Hint Extraction Logic

The `build_hints.py` script extracts hints based on predefined patterns. It currently looks for:
- **IP addresses:** Both IPv4 (e.g., `192.168.1.1`) and IPv6 (e.g., `2001:0db8:85a3:0000:0000:8a2e:0370:7334`).
- **Specific device IDs:** Patterns like `DEV-XXXX` where `XXXX` are alphanumeric characters.
- **Port numbers:** Numerical values typically found in network contexts (e.g., `80`, `443`, `8080`).
- **Other keywords:** Context-specific terms identified through regular expressions.

The extraction logic uses predefined patterns within the script and is not currently configurable via external files or environment variables. Future versions may introduce configuration options.

## Quick Commands

Rule-based only (default output to `reports/edge_hint_extractor/hints.yaml`):

```bash
python3 skills/edge-hint-extractor/scripts/build_hints.py \
  --market-summary /tmp/edge-auto/market_summary.json \
  --anomalies /tmp/edge-auto/anomalies.json \
  --news-reactions /tmp/news_reactions.csv \
  --as-of 2026-02-20 \
  --output-dir reports/
```

Rule + LLM augmentation (external CLI):

```bash
python3 skills/edge-hint-extractor/scripts/build_hints.py \
  --market-summary /tmp/edge-auto/market_summary.json \
  --anomalies /tmp/edge-auto/anomalies.json \
  --llm-ideas-cmd "python3 /path/to/llm_ideas_cli.py" \
  --output-dir reports/
```

Rule + LLM augmentation (pre-written file, for Claude Code):

```bash
python3 skills/edge-hint-extractor/scripts/build_hints.py \
  --market-summary /tmp/edge-auto/market_summary.json \
  --anomalies /tmp/edge-auto/anomalies.json \
  --llm-ideas-file /tmp/llm_hints.yaml \
  --output-dir reports/
```

## Troubleshooting

This section covers common issues and their resolutions when using the Edge Hint Extractor.

### Input file not found

**Issue:** The script reports that an input file (e.g., `market_summary.json`, `anomalies.json`, `news_reactions.csv`) does not exist.
**Resolution:**
1.  **Verify Path:** Double-check the file path provided in the command-line arguments. Ensure there are no typos.
2.  **Check Existence:** Confirm that the file actually exists at the specified location.
3.  **Absolute vs. Relative Paths:** If using relative paths, ensure you are running the script from the correct working directory. Consider using absolute paths for clarity.

### Permission denied for output

**Issue:** The script fails to write the output `hints.yaml` file due to a permission error.
**Resolution:**
1.  **Check Directory Permissions:** Ensure the user running the script has write permissions to the `--output-dir` specified.
2.  **Change Output Directory:** Try writing to a different directory where you have known write access (e.g., `/tmp/`).

### No hints extracted

**Issue:** The `hints.yaml` file is generated, but the `hints` list is empty, even when input files contain data.
**Resolution:**
1.  **Review Input Content:** Examine the content of your input files (`market_summary.json`, `anomalies.json`, `news_reactions.csv`). The script extracts hints based on specific patterns (IP addresses, device IDs, port numbers, keywords). If your input does not contain these patterns, no hints will be extracted.
2.  **Understand Extraction Logic:** Refer to the "Hint Extraction Logic" section above to understand what patterns the script looks for.
3.  **Check for Malformed Input:** Ensure your input JSON/CSV files are well-formed and can be parsed correctly. Errors during parsing might lead to no hints being processed.

### Unexpected output or script crash

**Issue:** The script crashes or produces unexpected output.
**Resolution:**
1.  **Check Logs:** Look for error messages in the console output or any generated log files (if logging is configured). The script uses Python's `logging` module, so check `stderr` for detailed error messages.
2.  **Input File Integrity:** Verify the integrity and format of all input files. Corrupted or malformed files can cause parsing errors.
3.  **Python Environment:** Ensure all prerequisites (Python 3.9+, `PyYAML`) are correctly installed and your Python environment is set up properly.

## Resources

- `skills/edge-hint-extractor/scripts/build_hints.py`
- `references/hints_schema.md`
