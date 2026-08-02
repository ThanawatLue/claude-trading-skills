---
name: thai-breadth-analyzer
description: Compute fast market-breadth snapshot for the Thai SET market via TradingView Screener — % above SMA50/200, advance-decline, new highs/lows, RSI distribution, and a composite breadth score. Single API call covering the entire SET universe in ~5 seconds.
---

# Thai Breadth Analyzer

A Thai-market analogue of the US market-breadth-analyzer, but using TradingView's pre-computed indicators instead of looping yfinance — completes in seconds vs minutes.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. You are strictly forbidden from attempting to execute live trades based on market breadth data. All regime classifications are for informational use only.

## Formatting Guidelines
When presenting breadth data to the user:
- Use **Emojis** for market regimes (e.g., 🟢 Strong Bull, 🔴 Bear).
- Clearly state the **Actionable Advice** (e.g., "Increase Risk", "Selectivity Required", "Capital Preservation") in bold.
- Present metrics (%>SMA50, A/D line) using clean markdown lists.

## When to Use

- Daily morning routine to assess overall SET market health.
- Before entering new long positions to confirm broad participation.
- Detect regime shifts (e.g., from healthy uptrend to deteriorating breadth).

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.
- Uses `tv_client.py` from `skills/vcp-screener/scripts/`. **WARNING**: This creates a tight dependency on the exact relative path of the `vcp-screener` skill. For standalone execution outside the agent's environment, ensure `skills/vcp-screener/scripts/` is explicitly added to your `PYTHONPATH` or that `vcp-screener` is installed as a separate package.

## Quick Start

```bash
# Default: write today's snapshot to reports/
python3 skills/thai-breadth-analyzer/scripts/analyze_thai_breadth.py --output-dir reports/

# Inspect output directly
python3 -c "
import json, glob
latest = sorted(glob.glob('reports/thai_market_breadth_*.json'))[-1]
d = json.load(open(latest, encoding='utf-8'))
print(f'regime: {d[\"regime\"]}  score: {d[\"composite_score\"]}')
print(f'  %>SMA50: {d[\"breadth\"][\"pct_above_sma50\"]:.1f}%')
print(f'  %>SMA200: {d[\"breadth\"][\"pct_above_sma200\"]:.1f}%')
print(f'  A/D: {d[\"breadth\"][\"advancers\"]}/{d[\"breadth\"][\"decliners\"]}')
"
```

Typical run: **3-5 seconds** for ~900 SET stocks.

## Workflow

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

## Composite Breadth Score

Weighted average of normalized components:
- 40% × `pct_above_sma50` (trend participation)
- 30% × `pct_above_sma200` (long-term trend)
- 15% × `(advancers - decliners) / total` (today's tape)
- 15% × `(new_highs - new_lows) / total` (leadership)

Score bands:
- **≥ 70**: Strong bull regime — broad participation
- **50-70**: Healthy uptrend — leaders working
- **30-50**: Mixed / corrective — selectivity required
- **< 30**: Bear regime — capital preservation

## Output Format

JSON: `thai_market_breadth_<timestamp>.json`
Markdown: `thai_market_breadth_<timestamp>.md`

JSON shape mirrors `market_breadth_<date>.json` so the dashboard's existing breadth-rendering code can consume it (with `metadata.market = "TH"`).

## Resources

- **Script:** `scripts/analyze_thai_breadth.py`
- **Data source:** TradingView Screener via `tv_client.get_thai_breadth()`
- **No API key required**
