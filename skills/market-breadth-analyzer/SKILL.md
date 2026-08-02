---
name: market-breadth-analyzer
description: Quantifies market breadth health using data-driven 6-component scoring. Supports US (S&P 500) and Thai (SET50) markets. Use when user asks about market breadth, participation, or general market health assessment in either market.
---

# Market Breadth Analyzer Skill

## Purpose

Quantify market breadth health using a data-driven 6-component scoring system (0-100). Uses TraderMonty's publicly available CSV data to measure how broadly the market is participating in a rally or decline.

**Score direction:** 100 = Maximum health (broad participation), 0 = Critical weakness.

**No API key required** - uses freely available CSV data from GitHub Pages.

## When to Use This Skill

- User asks "Is the market rally broad-based?" or "How healthy is market breadth?"
- User wants to assess market participation rate
- User asks about advance-decline indicators or breadth thrust
- User wants to know if the market is narrowing (fewer stocks participating)
- User asks about equity exposure levels based on breadth conditions

## Prerequisites

- **Python 3.8+** with `requests` library (for fetching CSV data)
- **Internet access** to reach GitHub Pages URLs
- **No API keys required** - uses freely available public CSV data

## Difference from Breadth Chart Analyst

| Aspect | Market Breadth Analyzer | Breadth Chart Analyst |
|--------|------------------------|----------------------|
| Data Source | CSV (automated) | Chart images (manual) |
| API Required | None | None |
| Output | Quantitative 0-100 score | Qualitative chart analysis |
| Components | 6 scored dimensions | Visual pattern recognition |
| Repeatability | Fully reproducible | Analyst-dependent |

---

## Execution Workflow

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

## 6-Component Scoring System

| # | Component | Weight | Key Signal |
|---|-----------|--------|------------|
| 1 | Breadth Level & Trend | **25%** | Current 8MA level + 200MA trend direction + 8MA direction modifier |
| 2 | 8MA vs 200MA Crossover | **20%** | Momentum via MA gap and direction |
| 3 | Peak/Trough Cycle | **20%** | Position in breadth cycle |
| 4 | Bearish Signal | **15%** | Backtested bearish signal flag |
| 5 | Historical Percentile | **10%** | Current vs full history distribution |
| 6 | S&P 500 Divergence | **10%** | Multi-window (20d + 60d) price vs breadth divergence |

**Weight Redistribution:** If any component lacks sufficient data (e.g., no peak/trough markers detected), it is excluded and its weight is proportionally redistributed among the remaining components. The report shows both original and effective weights.

**Score History:** Composite scores are persisted across runs (keyed by data date). The report includes a trend summary (improving/deteriorating/stable) when multiple observations are available.

## Health Zone Mapping (100 = Healthy)

| Score | Zone | Equity Exposure | Action |
|-------|------|-----------------|--------|
| 80-100 | Strong | 90-100% | Full position, growth/momentum favored |
| 60-79 | Healthy | 75-90% | Normal operations |
| 40-59 | Neutral | 60-75% | Selective positioning, tighten stops |
| 20-39 | Weakening | 40-60% | Profit-taking, raise cash |
| 0-19 | Critical | 25-40% | Capital preservation, watch for trough |

---

## Data Sources

**Detail CSV:** `market_breadth_data.csv`
- ~2,500 rows from 2016-02 to present
- Columns: Date, S&P500_Price, Breadth_Index_Raw, Breadth_Index_200MA, Breadth_Index_8MA, Breadth_200MA_Trend, Bearish_Signal, Is_Peak, Is_Trough, Is_Trough_8MA_Below_04

**Summary CSV:** `market_breadth_summary.csv`
- 8 aggregate metrics (average peaks, average troughs, counts, analysis period)

Both are publicly hosted on GitHub Pages - no authentication required.

## Output Files

- JSON: `market_breadth_YYYY-MM-DD_HHMMSS.json`
- Markdown: `market_breadth_YYYY-MM-DD_HHMMSS.md`
- History: `market_breadth_history.json` (persists across runs, max 20 entries)

## Reference Documents

### `references/breadth_analysis_methodology.md`
- Full methodology with component scoring details
- Threshold explanations and zone definitions
- Historical context and interpretation guide

### When to Load References
- **First use:** Load methodology reference for framework understanding
- **Regular execution:** References not needed - script handles scoring
