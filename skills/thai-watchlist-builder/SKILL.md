---
name: thai-watchlist-builder
description: Auto-build 4 curated watchlists from the Thai SET market (Growth, Value, Momentum, Mean-Reversion) using TradingView Screener filters. Reduces the ~900-stock SET universe to ~20-50 candidates per bucket — feed these to deeper screeners (VCP, CANSLIM) for focused analysis.
---

# Thai Watchlist Builder

Daily auto-curated watchlists for Thai stocks. Splits the SET universe into 4 actionable buckets based on technical and fundamental criteria — each bucket feeds a different trading style.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. Watchlist generation does not constitute trading execution. You are strictly forbidden from connecting to broker APIs.

## Formatting Guidelines
When presenting watchlists to the user:
- Use **Emojis** for each bucket category (e.g., 🚀 Growth, 💰 Value, 🔥 Momentum, 🔄 Mean-Reversion).
- Limit the displayed stocks to the top 3-5 per bucket unless asked otherwise, to prevent chat clutter.
- Use bold text for Tickers and Scores.

## When to Use

- Daily morning routine before running deep screeners.
- Reduce the universe from ~900 → ~30-50 per bucket for targeted analysis.
- Different traders pick different buckets (Growth, Value, Momentum, Mean-Reversion).

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `pandas`, `requests`.

## The 4 Buckets

### 1. Growth (Stage 2 leaders with momentum)
- Above SMA50 AND above SMA200
- 3-month performance ≥ +10%
- 1-month performance positive
- RSI 50-75
- Market cap ≥ 5B THB (mid+ cap for liquidity)

### 2. Value (Cheap with fundamentals)
- P/E between 5 and 15 (excludes loss-makers and bubbles)
- Dividend yield ≥ 3%
- Price above SMA200 (long-term uptrend confirmed)
- 1Y performance positive (avoid value traps)
- Market cap ≥ 5B THB

### 3. Momentum (Hot stocks for swing/breakout)
- RSI 60-78 (strong but not extreme)
- 1-month performance ≥ +5%
- Volume > 1.5× 10-day avg
- Within 8% of 52-week high
- Price ≥ 3 THB

### 4. Mean-Reversion (Oversold bounces)
- RSI 28-40 (oversold but not crashing)
- Price above SMA200 (long-term uptrend intact)
- Within 8% of SMA50 (pullback to support)
- 1Y performance positive (good uptrend in pullback)
- Price ≥ 3 THB

## Workflow

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

## Output

The script generates two reports in the specified `--output-dir` (default: `reports/`):
- `thai_watchlists_YYYY-MM-DD_HHMMSS.json`: A machine-readable JSON file containing the raw data for each stock across the four watchlists (Growth, Value, Momentum, Mean-Reversion). This file is typically consumed by dashboards or other automated systems.
- `thai_watchlists_YYYY-MM-DD_HHMMSS.md`: A human-readable Markdown report summarizing the contents of each watchlist bucket. This report provides a quick overview for manual review.

## Resources

- `references/methodology.md`: In-depth breakdown of filters, composite scores, and interpretation guides.
- `scripts/build_watchlists.py`: Main builder script connecting to TradingView and applying filters.
