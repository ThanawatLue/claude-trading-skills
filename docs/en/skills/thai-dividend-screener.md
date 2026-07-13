---
layout: default
title: "Thai Dividend Screener"
grand_parent: English
parent: Skill Guides
nav_order: 59
lang_peer: /ja/skills/thai-dividend-screener/
permalink: /en/skills/thai-dividend-screener/
---

# Thai Dividend Screener
{: .no_toc }

Screen Thai SET stocks for high-quality dividend income opportunities. Uses TradingView Screener (no API key required) to filter for yield, valuation, and trend health. Replaces the US-only value-dividend-screener and dividend-growth-pullback-screener (which require paid FMP API) for Thai-market traders.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/thai-dividend-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Thai Dividend Screener

---

## 2. When to Use

- Build / rebalance a Thai dividend portfolio (income focus).
- Find pullback entries on SETHD-style dividend payers.
- Avoid "value traps" — stocks with high yield but deteriorating trends.

---

## 3. Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.
- Uses `tv_client.py` from `skills/vcp-screener/scripts/` (auto-added to PYTHONPATH).

---

## 4. Quick Start

1. Execute `scripts/screen_thai_dividends.py --output-dir reports/`.
2. Fetch full SET universe via TradingView Screener.
3. Apply hard filters and compute composite score.
4. Output ranked JSON + markdown report.

---

## 5. Workflow

1. Execute `scripts/screen_thai_dividends.py --output-dir reports/`.
2. Fetch full SET universe via TradingView Screener.
3. Apply hard filters and compute composite score.
4. Output ranked JSON + markdown report.

---

## 6. Resources

**References:**

- `skills/thai-dividend-screener/references/methodology.md`

**Scripts:**

- `skills/thai-dividend-screener/scripts/screen_thai_dividends.py`
