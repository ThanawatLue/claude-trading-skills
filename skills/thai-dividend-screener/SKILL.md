---
name: thai-dividend-screener
description: Screen Thai SET stocks for high-quality dividend income opportunities. Uses TradingView Screener (no API key required) to filter for yield, valuation, and trend health. Replaces the US-only value-dividend-screener and dividend-growth-pullback-screener (which require paid FMP API) for Thai-market traders.
---

# Thai Dividend Screener

A pure-TradingView dividend screener for the Thai SET market — produces a ranked list of income candidates with both high yield AND uptrend confirmation.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. You are strictly forbidden from executing live trades. All screened stocks and yield data are for information and portfolio planning.

## Formatting Guidelines
When presenting dividend candidates to the user:
- Use **Emojis** (e.g., 💸 Yield, 📈 Trend, ⚠️ Value Trap).
- Format the output as a Markdown table or clear bulleted list containing Ticker, Yield, P/E, and Grade.
- Bold the tickers and grades for easy scanning.

## When to Use

- Build / rebalance a Thai dividend portfolio (income focus).
- Find pullback entries on SETHD-style dividend payers.
- Avoid "value traps" — stocks with high yield but deteriorating trends.

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.
- Uses `tv_client.py` from `skills/vcp-screener/scripts/` (auto-added to PYTHONPATH).

## Quick Start

```bash
# Default screen — write to reports/
python3 skills/thai-dividend-screener/scripts/screen_thai_dividends.py --output-dir reports/

# Custom: only stocks with yield >= 5%, top 20
python3 skills/thai-dividend-screener/scripts/screen_thai_dividends.py \
  --min-yield 5 --top 20 --output-dir reports/

# Custom liquidity floor: average traded value >= 10M THB/day
python3 skills/thai-dividend-screener/scripts/screen_thai_dividends.py \
  --min-turnover 10000000 --output-dir reports/

# Inspect top picks
python3 -c "
import json, glob
d = json.load(open(sorted(glob.glob('reports/thai_dividends_*.json'))[-1], encoding='utf-8'))
print(f'{len(d[\"candidates\"])} candidates from {d[\"universe_size\"]} SET stocks')
for c in d['candidates'][:5]:
    print(f'  {c[\"symbol\"]:10s} yield={c[\"dividend_yield\"]:.2f}% P/E={c[\"pe_ratio\"]:.1f} grade={c[\"grade\"]}')
"
```

Typical run: **3-5 seconds** for ~900 SET stocks.

## Filter Criteria

### Hard filters (must pass)

Liquidity guardrail: average traded value must be at least 10M THB/day by default. Adjust with `--min-turnover`.
- **Dividend yield** ≥ 3% (configurable via `--min-yield`)
- **Market cap** ≥ 5B THB (sufficient liquidity)
- **P/E ratio** 4-25 (positive earnings, not bubble)
- **Price > SMA200** (long-term uptrend intact — avoids value traps)
- **Common stock only** (DRs, warrants, rights excluded)

### Scoring weights
- **40%** Yield score (higher yield = better, capped at 12% to penalize "yield trap")
- **20%** Valuation score (P/E 8-15 sweet spot)
- **20%** Trend health (1Y performance + distance above SMA200)
- **20%** Pullback opportunity (RSI 35-55 sweet spot for entry)

Score bands: ≥75 Excellent · 60-74 Good · 45-59 Fair · <45 Avoid

## Workflow

1. Execute `scripts/screen_thai_dividends.py --output-dir reports/`.
2. Fetch full SET universe via TradingView Screener.
3. Apply hard filters and compute composite score.
4. Output ranked JSON + markdown report.

## Output

`thai_dividends_<timestamp>.json` — ranked list with score, yield, P/E, sector, trend indicators.

## Resources

- **Script:** `scripts/screen_thai_dividends.py`
- **No API key required** (uses public TradingView Screener data)
