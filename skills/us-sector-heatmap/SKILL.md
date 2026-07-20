---
name: us-sector-heatmap
description: Generate a sector-rotation heatmap for the US market using TradingView Screener data. Computes median 1M/3M/6M/YTD returns per sector, ranks them by momentum, and outputs a markdown + JSON report.
---

# US Sector Heatmap

Generate a sector-rotation heatmap for the US market using TradingView Screener data. Computes median returns per sector and ranks them by momentum.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. All insights, momentum scores, and stock lists are for informational and "Paper Trading" use only.

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.

## Quick Start

```bash
# Generate today's US sector heatmap (writes to reports/)
python3 skills/us-sector-heatmap/scripts/generate_us_heatmap.py --output-dir reports/
```
