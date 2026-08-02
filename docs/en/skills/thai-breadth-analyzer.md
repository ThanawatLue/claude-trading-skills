---
layout: default
title: "Thai Breadth Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 58
lang_peer: /ja/skills/thai-breadth-analyzer/
permalink: /en/skills/thai-breadth-analyzer/
---

# Thai Breadth Analyzer
{: .no_toc }

Compute fast market-breadth snapshot for the Thai SET market via TradingView Screener — % above SMA50/200, advance-decline, new highs/lows, RSI distribution, and a composite breadth score. Single API call covering the entire SET universe in ~5 seconds.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/thai-breadth-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Thai Breadth Analyzer

---

## 2. When to Use

- Daily morning routine to assess overall SET market health.
- Before entering new long positions to confirm broad participation.
- Detect regime shifts (e.g., from healthy uptrend to deteriorating breadth).

---

## 3. Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.
- Uses `tv_client.py` from `skills/vcp-screener/scripts/`. **WARNING**: This creates a tight dependency on the exact relative path of the `vcp-screener` skill. For standalone execution outside the agent's environment, ensure `skills/vcp-screener/scripts/` is explicitly added to your `PYTHONPATH` or that `vcp-screener` is installed as a separate package.

---

## 4. Quick Start

1. Execute `scripts/analyze_thai_breadth.py --output-dir reports/`.
2. Fetch the full SET universe (~900 stocks) via TradingView Screener in one call.
3. Compute breadth metrics:
   - % above SMA50 / SMA200 (Stage 2 confirmation)
   - Advance / decline / unchanged counts
   - New 52-week highs / lows (within 2% threshold)
   - RSI distribution (oversold / overbought / neutral)
   - Median RSI, 1M perf, 3M perf
4. Produce composite breadth score: 0-100 (higher = healthier).
5. Output JSON + markdown report.

---

## 5. Workflow

1. Execute `scripts/analyze_thai_breadth.py --output-dir reports/`.
2. Fetch the full SET universe (~900 stocks) via TradingView Screener in one call.
3. Compute breadth metrics:
   - % above SMA50 / SMA200 (Stage 2 confirmation)
   - Advance / decline / unchanged counts
   - New 52-week highs / lows (within 2% threshold)
   - RSI distribution (oversold / overbought / neutral)
   - Median RSI, 1M perf, 3M perf
4. Produce composite breadth score: 0-100 (higher = healthier).
5. Output JSON + markdown report.

---

## 6. Resources

**References:**

- `skills/thai-breadth-analyzer/references/methodology.md`

**Scripts:**

- `skills/thai-breadth-analyzer/scripts/analyze_thai_breadth.py`
