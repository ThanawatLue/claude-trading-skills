---
name: edge-concept-synthesizer
description: Abstract detector tickets and hints into reusable edge concepts with thesis, invalidation signals, and strategy playbooks before strategy design/export.
---

# Edge Concept Synthesizer

## Overview

Create an abstraction layer between detection and strategy implementation.
This skill clusters ticket evidence, summarizes recurring conditions, and outputs `edge_concepts.yaml` with explicit thesis and invalidation logic.

## When to Use

- You have many raw tickets and need mechanism-level structure.
- You want to avoid direct ticket-to-strategy overfitting.
- You need concept-level review before strategy drafting.

## Prerequisites

- Python 3.9+
- `PyYAML`
- Ticket YAML directory from detector output (`tickets/exportable`, `tickets/research_only`)
- Optional `hints.yaml`

## Output

- `edge_concepts.yaml` containing:
  - concept clusters
  - support statistics
  - abstract thesis
  - invalidation signals
  - export readiness flag

## Workflow

1. Collect ticket YAML files from auto-detection output.
2. Optionally provide `hints.yaml` for context matching.
3. Run `scripts/synthesize_edge_concepts.py`.
4. Deduplicate concepts: merge same-hypothesis concepts with overlapping conditions (containment > threshold).
5. Review concepts and promote only high-support concepts into strategy drafting.

## Quick Commands

```bash
python3 skills/edge-concept-synthesizer/scripts/synthesize_edge_concepts.py \
  --tickets-dir data/edge-auto/tickets \
  --hints data/edge-hints/hints.yaml \
  --output reports/edge-concepts/edge_concepts.yaml \
  --min-ticket-support 2

# With hint promotion and synthetic cap
python3 skills/edge-concept-synthesizer/scripts/synthesize_edge_concepts.py \
  --tickets-dir data/edge-auto/tickets \
  --hints data/edge-hints/hints.yaml \
  --output reports/edge-concepts/edge_concepts.yaml \
  --promote-hints \
  --max-synthetic-ratio 1.5

# With custom dedup threshold (or disable dedup)
python3 skills/edge-concept-synthesizer/scripts/synthesize_edge_concepts.py \
  --tickets-dir data/edge-auto/tickets \
  --output reports/edge-concepts/edge_concepts.yaml \
  --overlap-threshold 0.6

python3 skills/edge-concept-synthesizer/scripts/synthesize_edge_concepts.py \
  --tickets-dir data/edge-auto/tickets \
  --output reports/edge-concepts/edge_concepts.yaml \
  --no-dedup
```

## Troubleshooting

- **Missing Directories**: The `--tickets-dir` must exist before running. If the directory is missing, the script will log an error and exit with code 1. The output path's parent directories will be created automatically if they do not exist.
- **Unexpected Concept Merges**: Concepts with conditional overlap above 75% are merged by default. If you see too many distinct concepts merged, raise `--overlap-threshold` (e.g. `0.90`) or disable deduplication entirely with `--no-dedup`.
- **Synthetic Ticket Cap**: When `--max-synthetic-ratio` is set, synthetic tickets created from hints might be capped relative to real tickets. Adjust or omit the ratio flag if you want to include all hints.

## Resources

- `skills/edge-concept-synthesizer/scripts/synthesize_edge_concepts.py`
- `references/concept_schema.md`
