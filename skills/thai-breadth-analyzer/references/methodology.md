# Thai Breadth Analyzer — Methodology

## What "breadth" means

Market breadth measures **how many stocks** are participating in the move, not just where the index is. A market index can rise on the back of a few mega-caps while most stocks decline — that's bad breadth, fragile rally. Strong breadth = broad participation = sustainable trend.

We compute breadth for the entire SET universe in **one TradingView API call** — no per-stock yfinance loops.

## Composite Score Formula

```
score = 0.40 × pct_above_sma50
      + 0.30 × pct_above_sma200
      + 0.15 × ((advancers - decliners) / total) × 100
      + 0.15 × ((new_highs - new_lows) / total) × 100
```

Components:
- **pct_above_sma50 (40%)** — % of SET stocks trading above their own 50-day SMA. Best short-term trend gauge.
- **pct_above_sma200 (30%)** — % above 200-day SMA. Confirms structural Stage 2 vs Stage 4.
- **A/D ratio (15%)** — Today's advancers minus decliners, normalized. Catches reversals before the SMA shifts.
- **New 52w Hi/Lo (15%)** — Leadership health — are new highs expanding or contracting?

All four components are normalized and clamped to a 0-100 range before being weighted. The final composite score also ranges 0-100.

## Regime Bands

| Score | Regime | Action |
|---|---|---|
| ≥ 70 | **Strong Bull** | Broad participation. Aggressive long entries, more concurrent positions OK. |
| 50-70 | **Healthy Uptrend** | Leaders working. Normal long exposure, focus on best setups. |
| 30-50 | **Mixed / Corrective** | Selectivity required. Tighten stops, reduce concurrent risk. |
| < 30 | **Bear Regime** | Capital preservation. Cash, hedge, or short-side opportunities. |

## Why these specific weights?

- **SMA50 > SMA200 weighting** — 50-day flips faster, gives earlier signal of trend changes. 200-day confirms the move is structural, not noise.
- **A/D and new highs both 15%** — They're complementary: A/D captures today's tape direction, new highs captures the leadership tail.

## Filters before counting

- Symbols ending `.R.BK` (rights), DR certificates, warrants excluded
- Stocks with `price < 1 THB` excluded (penny stock noise)
- "New high/low" defined as within **2% of 52-week extreme** (not strict touch)

## Caveats

- TradingView's `SMA50`/`SMA200` fields are calculated on the close price as of the last data refresh — may be 1-day delayed during pre-market hours TH time.
- A/D counts move toward `total_stocks` as the day progresses; midday snapshots can look weaker than EOD.
- Score is **a regime classifier, not a signal** — don't enter just because score crossed 70.

## How to combine with other skills

1. **Breadth ≥ 50** = green light for VCP/CANSLIM entries (broad market supportive)
2. **Breadth 30-50** = only enter A+ setups (highest score from screeners)
3. **Breadth < 30** = paper-trade only or stay flat
4. **Breadth dropping fast** (today's score 10+ below 5-day avg) = warning, tighten stops on existing positions
