---
name: us-watchlist-builder
description: Auto-build 4 curated watchlists from the US market (Growth, Value, Momentum, Mean-Reversion) using TradingView Screener filters. Reduce thousands of US stocks to 20-50 candidates per bucket for focused analysis.
---

# US Watchlist Builder

Daily auto-curated watchlists for US stocks. Splits the US universe into 4 actionable buckets based on technical and fundamental criteria.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. All insights and lists are for informational and "Paper Trading" use only.

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `pandas`, `requests`.

## Quick Start

```bash
# Default: build today's watchlists (writes to reports/)
python3 skills/us-watchlist-builder/scripts/build_us_watchlists.py --output-dir reports/
```
