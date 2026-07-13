---
layout: default
title: "US Stock Analysis"
grand_parent: English
parent: Skill Guides
nav_order: 67
lang_peer: /ja/skills/us-stock-analysis/
permalink: /en/skills/us-stock-analysis/
---

# US Stock Analysis
{: .no_toc }

Comprehensive US stock analysis including fundamental analysis (financial metrics, business quality, valuation), technical analysis (indicators, chart patterns, support/resistance), stock comparisons, and investment report generation. Use when user requests analysis of US stock tickers (e.g., "analyze AAPL", "compare TSLA vs NVDA", "give me a report on Microsoft"), evaluation of financial metrics, technical chart analysis, or investment recommendations for American stocks.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/us-stock-analysis.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/us-stock-analysis){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

Perform comprehensive analysis of US stocks covering fundamental analysis (financials, business quality, valuation), technical analysis (indicators, trends, patterns), peer comparisons, and generate detailed investment reports. Fetch real-time market data via web search tools and apply structured analytical frameworks.

---

## 2. When to Use

Use this skill when the user requests any form of analysis, information, or comparison related to US stocks. This includes:
-   **Fetching basic stock information:** Current prices, key metrics, recent news.
-   **Performing fundamental analysis:** Deep dive into financials, business quality, and valuation.
-   **Conducting technical analysis:** Chart patterns, indicators, and trend analysis.
-   **Generating comprehensive investment reports:** Combining fundamental and technical insights with recommendations.
-   **Comparing multiple US stocks:** Side-by-side analysis of peers.

This skill is suitable for queries such as "analyze AAPL", "compare TSLA vs NVDA", "give me a report on Microsoft", "is Amazon overvalued?", or "technical analysis of TSLA".

---

## 3. Prerequisites

This skill heavily relies on web search capabilities to fetch real-time and historical market data. Ensure the following tools are available and configured:

-   **`google_web_search`**: This tool is essential for querying financial news, company reports, stock metrics, and technical data from various online sources. It requires proper API key setup (if applicable) and access to function effectively.

Without the proper functioning of `google_web_search`, the skill will be unable to gather the necessary data for analysis.

---

## 4. Quick Start

The `us-stock-analysis` skill follows a systematic workflow to process user requests and generate comprehensive insights:

1.  **Parse User Query**: The skill first interprets the user's natural language request to identify the target stock tickers and the desired type of analysis (e.g., Basic Info, Fundamental, Technical, Comprehensive, Comparison).
2.  **Data Acquisition**: Using `google_web_search`, the skill fetches relevant market data, financial statements, key metrics, news, and technical indicators for the identified tickers from reliable sources. This step is critical for up-to-date and accurate analysis.
3.  **Perform Analysis**: Based on the identified analysis type, the skill applies the appropriate analytical frameworks and methodologies (e.g., fundamental ratios, technical patterns, valuation models) to the acquired data. It references internal knowledge bases (`references/fundamental-analysis.md`, `references/technical-analysis.md`, `references/financial-metrics.md`) for detailed guidance.
4.  **Synthesize and Report**: The analyzed data is then synthesized into a coherent and structured report, formatted according to specified guidelines and report templates (`references/report-template.md`). The output provides clear insights, and where applicable, recommendations or comparisons.
5.  **Error Handling**: Throughout the process, the skill is equipped to handle scenarios such as invalid tickers, missing data, or API failures, providing informative feedback or fallback mechanisms.

---

## 5. Workflow

The `us-stock-analysis` skill follows a systematic workflow to process user requests and generate comprehensive insights:

1.  **Parse User Query**: The skill first interprets the user's natural language request to identify the target stock tickers and the desired type of analysis (e.g., Basic Info, Fundamental, Technical, Comprehensive, Comparison).
2.  **Data Acquisition**: Using `google_web_search`, the skill fetches relevant market data, financial statements, key metrics, news, and technical indicators for the identified tickers from reliable sources. This step is critical for up-to-date and accurate analysis.
3.  **Perform Analysis**: Based on the identified analysis type, the skill applies the appropriate analytical frameworks and methodologies (e.g., fundamental ratios, technical patterns, valuation models) to the acquired data. It references internal knowledge bases (`references/fundamental-analysis.md`, `references/technical-analysis.md`, `references/financial-metrics.md`) for detailed guidance.
4.  **Synthesize and Report**: The analyzed data is then synthesized into a coherent and structured report, formatted according to specified guidelines and report templates (`references/report-template.md`). The output provides clear insights, and where applicable, recommendations or comparisons.
5.  **Error Handling**: Throughout the process, the skill is equipped to handle scenarios such as invalid tickers, missing data, or API failures, providing informative feedback or fallback mechanisms.

---

## 6. Resources

**References:**

- `skills/us-stock-analysis/references/financial-metrics.md`
- `skills/us-stock-analysis/references/fundamental-analysis.md`
- `skills/us-stock-analysis/references/report-template.md`
- `skills/us-stock-analysis/references/technical-analysis.md`

**Scripts:**

- `skills/us-stock-analysis/scripts/us_stock_analysis.py`
