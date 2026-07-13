---
layout: default
title: "Thai Watchlist Builder"
grand_parent: English
parent: Skill Guides
nav_order: 61
lang_peer: /ja/skills/thai-watchlist-builder/
permalink: /en/skills/thai-watchlist-builder/
---

# Thai Watchlist Builder
{: .no_toc }

Auto-build 4 curated watchlists from the Thai SET market (Growth, Value, Momentum, Mean-Reversion) using TradingView Screener filters. Reduces the ~900-stock SET universe to ~20-50 candidates per bucket — feed these to deeper screeners (VCP, CANSLIM) for focused analysis.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/thai-watchlist-builder){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Thai Watchlist Builder

---

## 2. When to Use

- Daily morning routine before running deep screeners.
- Reduce the universe from ~900 → ~30-50 per bucket for targeted analysis.
- Different traders pick different buckets (Growth, Value, Momentum, Mean-Reversion).

---

## 3. Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `pandas`, `requests`.

---

## 4. Quick Start

```bash
python3 skills/thai-watchlist-builder/scripts/build_watchlists.py --output-dir reports/ --top 30
```

---

## 5. Workflow

### Step 1: Execute the Watchlist Builder Script

To fetch the full SET universe and filter into the 4 buckets, run:

```bash
python3 skills/thai-watchlist-builder/scripts/build_watchlists.py --output-dir reports/ --top 30
```

Optional liquidity guardrail:

```bash
python3 skills/thai-watchlist-builder/scripts/build_watchlists.py \
  --output-dir reports/ --top 30 --min-turnover 20000000
```

`--min-turnover` is the minimum average traded value in THB. The default is 20M THB/day to reduce false positives where a Thai stock chart looks tradable but actual liquidity is too thin.

### Step 2: Review Output Reports

The script generates two reports in the specified `--output-dir` (default: `reports/`):
- `thai_watchlists_YYYY-MM-DD_HHMMSS.json` — Consumed by the Dashboard.
- `thai_watchlists_YYYY-MM-DD_HHMMSS.md` — Human-readable markdown report summarizing each bucket.

### Step 3: Analyze Methodology

JSON rows include `avg_turnover` and `liquidity_score`; the payload includes `min_avg_turnover` for later calibration.

Consult the methodology reference doc under `references/methodology.md` to understand the screening metrics, scoring formulas, and how to apply them.

---

## 6. Resources

**References:**

- `skills/thai-watchlist-builder/references/methodology.md`

**Scripts:**

- `skills/thai-watchlist-builder/scripts/build_watchlists.py`
- `skills/thai-watchlist-builder/scripts/tv_client.py`
