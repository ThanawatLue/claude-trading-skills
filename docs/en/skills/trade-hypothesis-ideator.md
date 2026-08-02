---
layout: default
title: "Trade Hypothesis Ideator"
grand_parent: English
parent: Skill Guides
nav_order: 63
lang_peer: /ja/skills/trade-hypothesis-ideator/
permalink: /en/skills/trade-hypothesis-ideator/
---

# Trade Hypothesis Ideator
{: .no_toc }

Generate falsifiable trade strategy hypotheses from market data, trade logs, and journal snippets. Use when you have a structured input bundle and want ranked hypothesis cards with experiment designs, kill criteria, and optional strategy.yaml export compatible with edge-finder-candidate/v1.

{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/trade-hypothesis-ideator.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/trade-hypothesis-ideator){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Trade Hypothesis Ideator

---

## 2. When to Use

Use this skill when you have gathered market data, trade logs, or journal snippets and need to systematically generate and evaluate potential trading strategies. It is particularly useful for:
- **Generating new trade ideas:** When exploring new market opportunities or refining existing ones.
- **Validating intuitions:** To formalize vague trading hunches into testable hypotheses.
- **Pre-analysis of strategy concepts:** Before committing to full backtesting, quickly assess the viability and potential risks of a strategy.
- **Structured learning from trade journals:** Extracting patterns and generating hypotheses from your past trading performance.
- **Input:** Structured input bundles containing market context, trade details, and observational data.
- **Strategic Objective:** To accelerate the identification of promising trading strategies and enhance the decision-making process.

---

## 3. Prerequisites

- **Python Environment:** Python 3.9 or higher.
- **Poetry:** This project uses Poetry for dependency management. Ensure it is installed (`pip install poetry`).
- **Dependencies:** Install project dependencies using `poetry install`.
- **Environment Variables:**
    - `GEMINI_API_KEY`: Your Gemini API key for accessing language models.
    - `ANTHROPIC_API_KEY`: (Optional) Your Anthropic API key if using Anthropic models.
- **Input Bundle Format:** Input JSON bundles must conform to the schema defined in `schemas/input_bundle_schema.json`.
- **Configurable Guardrails:** The list of banned phrases used for guardrails can be found and customized in `config/banned_phrases.json`. Operators can modify this file to adjust the phrases that trigger warnings or rejections in hypothesis generation.

---

## 4. Quick Start

1. Receive input JSON bundle.
2. Run pass 1 normalization + evidence extraction.
3. Generate hypotheses with prompts:
   - `prompts/system_prompt.md`
   - `prompts/developer_prompt_template.md` (inject `{{evidence_summary}}`)
4. Critique hypotheses with `prompts/critique_prompt_template.md`.
5. Run pass 2 ranking + output formatting + guardrails.
6. Optionally export `pursue` hypotheses via Step H strategy exporter.

---

## 5. Workflow

1. Receive input JSON bundle.
2. Run pass 1 normalization + evidence extraction.
3. Generate hypotheses with prompts:
   - `prompts/system_prompt.md`
   - `prompts/developer_prompt_template.md` (inject `{{evidence_summary}}`)
4. Critique hypotheses with `prompts/critique_prompt_template.md`.
5. Run pass 2 ranking + output formatting + guardrails.
6. Optionally export `pursue` hypotheses via Step H strategy exporter.

---

## 6. Resources

**References:**

- `skills/trade-hypothesis-ideator/references/evidence_quality_guide.md`
- `skills/trade-hypothesis-ideator/references/hypothesis_types.md`

**Scripts:**

- `skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py`
