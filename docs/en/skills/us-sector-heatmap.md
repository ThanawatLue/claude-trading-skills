---
layout: default
title: "US Sector Heatmap"
grand_parent: English
parent: Skill Guides
nav_order: 69
lang_peer: /ja/skills/us-sector-heatmap/
permalink: /en/skills/us-sector-heatmap/
---

# US Sector Heatmap
{: .no_toc }

Generate a sector-rotation heatmap for the US market using TradingView Screener data. Computes median 1M/3M/6M/YTD returns per sector, ranks them by momentum, and outputs a markdown + JSON report.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/us-sector-heatmap){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# US Sector Heatmap

---

## 2. Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.

---

## 3. Quick Start

Invoke this skill by describing your analysis needs to Claude.

---

## 4. Workflow

See the skill's SKILL.md for the complete workflow.

---

## 5. Resources

**Scripts:**

- `skills/us-sector-heatmap/scripts/generate_us_heatmap.py`
