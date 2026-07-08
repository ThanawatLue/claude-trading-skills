---
layout: default
title: "Thai Sector Heatmap"
grand_parent: English
parent: Skill Guides
nav_order: 60
lang_peer: /ja/skills/thai-sector-heatmap/
permalink: /en/skills/thai-sector-heatmap/
---

# Thai Sector Heatmap
{: .no_toc }

Generate a sector-rotation heatmap for the Thai SET market using TradingView Screener data. Computes median 1M/3M/6M/YTD returns per sector, ranks them by momentum, and outputs a markdown + JSON report suitable for the trading dashboard.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/thai-sector-heatmap){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Thai Sector Heatmap

---

## 2. When to Use

- Daily morning routine to identify which SET sectors are leading vs lagging.
- Before running individual stock screeners (VCP, CANSLIM, Thai Swing) to focus on sectors with positive momentum.
- To detect sector rotation regime shifts (e.g., Energy weakening while Healthcare strengthens).

---

## 3. Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.
- The `tv_client` helper from `skills/vcp-screener/scripts/` must be on `PYTHONPATH` (auto-added by the script).

---

## 4. Quick Start

1. Execute `scripts/generate_heatmap.py --output-dir reports/`.
2. The script fetches the full SET universe (~900 stocks) via TradingView in a single API call.
3. Filter out DR certificates, warrants, and rights.
4. Group stocks by sector and compute median Perf.1M, Perf.3M, Perf.6M, and Perf.Y per sector.
5. Rank sectors by composite momentum score (weighted average of 1M/3M/6M).
6. Output both markdown report and JSON for dashboard consumption.

---

## 5. Workflow

1. Execute `scripts/generate_heatmap.py --output-dir reports/`.
2. The script fetches the full SET universe (~900 stocks) via TradingView in a single API call.
3. Filter out DR certificates, warrants, and rights.
4. Group stocks by sector and compute median Perf.1M, Perf.3M, Perf.6M, and Perf.Y per sector.
5. Rank sectors by composite momentum score (weighted average of 1M/3M/6M).
6. Output both markdown report and JSON for dashboard consumption.

---

## 6. Resources

**References:**

- `skills/thai-sector-heatmap/references/methodology.md`

**Scripts:**

- `skills/thai-sector-heatmap/scripts/generate_heatmap.py`
