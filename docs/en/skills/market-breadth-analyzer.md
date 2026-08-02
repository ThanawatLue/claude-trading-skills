---
layout: default
title: "Market Breadth Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 38
lang_peer: /ja/skills/market-breadth-analyzer/
permalink: /en/skills/market-breadth-analyzer/
---

# Market Breadth Analyzer
{: .no_toc }

Quantifies market breadth health using data-driven 6-component scoring. Supports US (S&P 500) and Thai (SET50) markets. Use when user asks about market breadth, participation, or general market health assessment in either market.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/market-breadth-analyzer.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/market-breadth-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Market Breadth Analyzer Skill

---

## 2. When to Use

- User asks "Is the market rally broad-based?" or "How healthy is market breadth?"
- User wants to assess market participation rate
- User asks about advance-decline indicators or breadth thrust
- User wants to know if the market is narrowing (fewer stocks participating)
- User asks about equity exposure levels based on breadth conditions

---

## 3. Prerequisites

- **Python 3.8+** with `requests` library (for fetching CSV data)
- **Internet access** to reach GitHub Pages URLs
- **No API keys required** - uses freely available public CSV data

---

## 4. Quick Start

```bash
# Analyze US Market (Default)
python3 skills/market-breadth-analyzer/scripts/market_breadth_analyzer.py --market US

# Analyze Thai Market (SET50)
python3 skills/market-breadth-analyzer/scripts/market_breadth_analyzer.py --market TH
```

---

## 5. Workflow

### Phase 1: Execute Python Script

Execute the analysis script for the desired market:

```bash
# Analyze US Market (Default)
python3 skills/market-breadth-analyzer/scripts/market_breadth_analyzer.py --market US

# Analyze Thai Market (SET50)
python3 skills/market-breadth-analyzer/scripts/market_breadth_analyzer.py --market TH
```

**Key Actions:**
1. Fetch latest market data (US uses GitHub CSV; TH performs live calculation on SET50 constituents)
2. Validate data freshness
3. Calculate all 6 component scores
4. Generate composite score with zone classification
5. Compute trend (improving/deteriorating/stable)
6. Save JSON and Markdown reports to `reports/`

### Phase 2: Present Results

Present the generated Markdown report to the user, ensuring the output is beautifully formatted using GitHub-flavored Markdown. Use bolding for key terms, use color indicators or emojis (e.g., 🟢 Strong, 🔴 Critical) for health zones, and explicitly state the recommended equity exposure.

Highlight:
- Composite score and health zone
- Strongest and weakest components
- Recommended equity exposure level (Actionable Advice - clearly state if the user should increase or decrease risk)
- Key breadth levels to watch

---

---

## 6. Resources

**References:**

- `skills/market-breadth-analyzer/references/breadth_analysis_methodology.md`

**Scripts:**

- `skills/market-breadth-analyzer/scripts/config_loader.py`
- `skills/market-breadth-analyzer/scripts/csv_client.py`
- `skills/market-breadth-analyzer/scripts/history_tracker.py`
- `skills/market-breadth-analyzer/scripts/market_breadth_analyzer.py`
- `skills/market-breadth-analyzer/scripts/report_generator.py`
- `skills/market-breadth-analyzer/scripts/scorer.py`
