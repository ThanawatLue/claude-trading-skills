---
name: thai-sector-heatmap
description: Generate a sector-rotation heatmap for the Thai SET market using TradingView Screener data. Computes median 1M/3M/6M/YTD returns per sector, ranks them by momentum, and outputs a markdown + JSON report suitable for the trading dashboard.
---

# Thai Sector Heatmap

This skill produces a daily sector-rotation snapshot for the Thai SET market.

> [!CAUTION]
> **CRITICAL CONSTRAINT: NO LIVE TRADING**
> This skill is for **analytical purposes ONLY**. You are strictly forbidden from attempting to connect to broker APIs (e.g., Alpaca, Interactive Brokers) or executing live trades. All insights, momentum scores, and stock lists are for informational and "Paper Trading" use only.

## Formatting Guidelines
When presenting the heatmap or sector data to the user via chat:
- Use **Emojis** to indicate momentum (e.g., 🟢 Hot, 🟡 Neutral, 🔴 Cold/Weak).
- Use **Markdown Tables** or bolding for readability.
- Clearly separate leading sectors from lagging sectors.

## When to Use

- Daily morning routine to identify which SET sectors are leading vs lagging.
- Before running individual stock screeners (VCP, CANSLIM, Thai Swing) to focus on sectors with positive momentum.
- To detect sector rotation regime shifts (e.g., Energy weakening while Healthcare strengthens).

## Prerequisites

- **No API keys required** (uses TradingView's public scanner API).
- Python 3.9+ installed.
- Required dependencies: `tradingview-screener>=0.3.0`, `pandas`.
- The `tv_client` helper from `skills/vcp-screener/scripts/` must be on `PYTHONPATH` (auto-added by the script).

## Quick Start

```bash
# Generate today's sector heatmap (writes to reports/)
python3 skills/thai-sector-heatmap/scripts/generate_heatmap.py --output-dir reports/

# Custom output path
python3 skills/thai-sector-heatmap/scripts/generate_heatmap.py --output-dir /path/to/out/

# Programmatic — import and use directly
python3 -c "
import sys; sys.path.insert(0, 'skills/thai-sector-heatmap/scripts')
from generate_heatmap import compute_sector_stats
import sys; sys.path.insert(0, 'skills/vcp-screener/scripts')
from tv_client import get_thai_stocks, filter_common_stocks
stocks = filter_common_stocks(get_thai_stocks(limit=1500))
sectors = compute_sector_stats(stocks)
for s in sectors[:5]: print(s['sector'], s['momentum_score'])
"
```

Typical run completes in **3-5 seconds** for ~900 SET stocks.

## Workflow

1. Execute `scripts/generate_heatmap.py --output-dir reports/`.
2. The script fetches the full SET universe (~900 stocks) via TradingView in a single API call.
3. Filter out DR certificates, warrants, and rights.
4. Group stocks by sector and compute median Perf.1M, Perf.3M, Perf.6M, and Perf.Y per sector.
5. Rank sectors by composite momentum score (weighted average of 1M/3M/6M).
6. Output both markdown report and JSON for dashboard consumption.

## Output Format

### JSON (`thai_sector_heatmap_<timestamp>.json`)

```json
{
  "generated": "2026-05-22_161000",
  "market": "TH",
  "universe_size": 887,
  "sectors": [
    {
      "sector": "Electronic Technology",
      "n_stocks": 23,
      "median_perf_1m": 21.29,
      "median_perf_3m": 18.45,
      "median_perf_6m": 32.10,
      "median_perf_y": 45.20,
      "momentum_score": 25.5,
      "rank": 1,
      "top_stocks": [{"symbol": "DELTA.BK", "perf_3m": 41.3}, ...]
    },
    ...
  ]
}
```

### Markdown Report

Includes a ranked sector table with color-coded momentum indicators (🟢 hot, 🟡 neutral, 🔴 cold), plus top-3 stocks per leading sector.

## Resources

- **Script:** `scripts/generate_heatmap.py`
- **Data Source:** TradingView Screener via `tv_client.py` (from vcp-screener skill)
- **No API key required**

## Integration

The output JSON is consumed by the dashboard's TH View tab. Filenames follow `thai_sector_heatmap_YYYY-MM-DD_HHMMSS.json` so the dashboard's `latest_file_any()` glob pattern catches it.
