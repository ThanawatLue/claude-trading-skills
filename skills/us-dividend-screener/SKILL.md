---
name: us-dividend-screener
description: Screen US stocks for high-quality dividend income opportunities. Uses TradingView Screener (no API key required) to filter for yield, valuation, and trend health. Replaces the US-only value-dividend-screener and dividend-growth-pullback-screener (which require paid FMP API) for US-market traders.
---

# US Dividend Screener

A pure-TradingView dividend screener for the US market — produces a ranked list of income candidates with both high yield AND uptrend confirmation.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. All screened stocks and yield data are for information and portfolio planning.

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.

## Quick Start

```bash
# Default screen — write to reports/
python3 skills/us-dividend-screener/scripts/screen_us_dividends.py --output-dir reports/
```
