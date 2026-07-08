# Thai Sector Heatmap — Methodology

## Why sector rotation matters in TH

Thai equities (SET) divide into ~20 GICS-style sectors. Capital rotates between them as macro conditions shift — Energy leads when oil rises, Financials lead when rates rise, Electronic Technology leads when global semiconductor cycle turns up, etc.

Tracking which sector is leading/lagging on a 1M/3M/6M horizon gives early signals of regime change before individual stock screeners pick them up.

## Scoring formula

`momentum_score` is a weighted blend of median sector performance across three horizons:

```
momentum_score = 0.40 × median_perf_1m
               + 0.35 × median_perf_3m
               + 0.20 × median_perf_6m
               + 0.05 × median_perf_y
```

Why this weighting:
- **1M (40%)** — captures the freshest rotation move
- **3M (35%)** — confirms that the 1M move isn't a one-week bounce
- **6M (20%)** — anchors to medium-term trend (avoids chasing dead-cat bounces)
- **1Y (5%)** — small tilt toward sustained leadership without anchoring too heavily to last year

We use **median** not mean per sector to avoid a single mega-cap distorting the picture (e.g., DELTA dominating Electronic Technology).

## Filters before scoring

Before grouping by sector, we exclude:
- Symbols ending `.R.BK` (rights)
- DR certificates (e.g., `SNOW23.BK`)
- Warrants
- Stocks with `price < 1 THB` (penny stock noise)
- Sectors with fewer than **3 stocks** (median is unreliable below this threshold)

## Output schema

| Field | Type | Meaning |
|---|---|---|
| `sector` | string | GICS-style sector name from TradingView |
| `n_stocks` | int | Number of stocks contributing to the median |
| `median_perf_1m/3m/6m/y` | float | Median % return over the period |
| `momentum_score` | float | Weighted blend (see formula above) |
| `rank` | int | 1 = highest momentum_score |
| `top_stocks` | array | Top 3 by 3M perf within the sector (with symbol + perf_3m) |

## Color-coding thresholds (markdown output)

- 🟢 `momentum_score ≥ 10` — leading sector
- 🟡 `0 ≤ momentum_score < 10` — neutral
- 🔴 `momentum_score < 0` — lagging

## Caveats

- TradingView's `sector` field occasionally returns `null` for newly listed stocks — these are dropped silently.
- TH sectors are smaller than US S&P sector ETFs; some sectors have only 10-15 stocks total, so single-stock moves can swing the median by a few percent.
- 1M perf is anchored to ~21 trading days; if a public holiday falls in the window, results are still based on the trailing 21 trading days.

## How to interpret

| Pattern | Read |
|---|---|
| All 4 horizons strongly positive | Sector in confirmed Stage 2 uptrend — chase pullbacks |
| 1M strong but 3M+6M negative | Mean-reversion bounce — fade or wait for confirmation |
| 6M positive but 1M negative | Late-cycle — start tightening stops, look for rotation |
| All negative | Stage 4 — avoid; possibly short-side candidate |
