---
name: us-breadth-analyzer-tv
description: Compute fast market-breadth snapshot for the US market via TradingView Screener — % above SMA50/200, advance-decline, new highs/lows, RSI distribution, and a composite breadth score. Covers thousands of US stocks in seconds.
---

# US Breadth Analyzer (TradingView version)

A US market breadth analyzer using TradingView's pre-computed indicators — completes in seconds without paid APIs.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. All regime classifications are for informational use only.

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.

## Quick Start

```bash
# Default: write today's snapshot to reports/
python3 skills/us-breadth-analyzer-tv/scripts/analyze_us_breadth_tv.py --output-dir reports/
```
