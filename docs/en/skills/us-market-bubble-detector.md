---
layout: default
title: "US Market Bubble Detector"
grand_parent: English
parent: Skill Guides
nav_order: 66
lang_peer: /ja/skills/us-market-bubble-detector/
permalink: /en/skills/us-market-bubble-detector/
---

# US Market Bubble Detector
{: .no_toc }

Evaluates market bubble risk through quantitative data-driven analysis using the revised Minsky/Kindleberger framework v2.1. Prioritizes objective metrics (Put/Call, VIX, margin debt, breadth, IPO data) over subjective impressions. Features strict qualitative adjustment criteria with confirmation bias prevention. Supports practical investment decisions with mandatory data collection and mechanical scoring. Use when user asks about bubble risk, valuation concerns, or profit-taking timing.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/us-market-bubble-detector.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/us-market-bubble-detector){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# US Market Bubble Detection Skill (Revised v2.1)

---

## 2. When to Use

Use this skill when:
- User asks "Is the market in a bubble?" or "Are we in a bubble?"
- User seeks advice on profit-taking, new entry timing, or short-selling decisions
- User reports social phenomena (non-investors entering, media frenzy, IPO flood)
- User mentions narratives like "this time is different" or "revolutionary technology" becoming mainstream
- User consults about risk management for existing positions

---

---

## 3. Prerequisites

This skill requires a working Python environment with `uv` (a fast Python package installer and resolver) and access to the internet for data retrieval. Ensure the following are installed and configured:

- **Python 3.8+**: Ensure Python is installed and available in your PATH.
- **uv**: Install `uv` globally or in your project's virtual environment:
  ```bash
  pip install uv
  ```
- **Internet Access**: Required to fetch real-time market data from sources like CBOE DataShop, Yahoo Finance, FINRA, Renaissance Capital IPO, etc.

---

---

## 4. Quick Start

Invoke this skill by describing your analysis needs to Claude.

---

## 5. Workflow

See the skill's SKILL.md for the complete workflow.

---

## 6. Resources

**References:**

- `skills/us-market-bubble-detector/references/bubble_framework.md`
- `skills/us-market-bubble-detector/references/historical_cases.md`
- `skills/us-market-bubble-detector/references/implementation_guide.md`
- `skills/us-market-bubble-detector/references/quick_reference.md`

**Scripts:**

- `skills/us-market-bubble-detector/scripts/bubble_scorer.py`
