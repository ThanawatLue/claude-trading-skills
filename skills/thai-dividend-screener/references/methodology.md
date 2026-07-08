# Thai Dividend Screener — Methodology

## Philosophy

The single biggest mistake retail dividend investors make: chasing yield without checking trend. A stock yielding 12% with a 2-year downtrend is signalling distress, not opportunity. This screener combines **high yield** AND **uptrend confirmation** to filter out value traps.

## Hard Filters (must all pass)

| Filter | Threshold | Why |
|---|---|---|
| Dividend yield | ≥ 3% | Below this, you're not buying for income |
| Market cap | ≥ 5B THB | Liquidity — avoid micro-caps where exits are hard |
| P/E ratio | 4-25 | Excludes loss-makers (P/E < 0 or > 50) and clear bubbles |
| Price > SMA200 | True | Long-term uptrend intact — the "no value trap" guard |
| Stock type | Common | DRs, warrants, rights excluded |

## Composite Score (0-100)

```
score = 40 × yield_score + 20 × valuation_score + 20 × trend_score + 20 × pullback_score
```

### Yield score (40% weight) — main income signal
- Linear ramp from 3% → 12% yield → 0-100
- **Capped at 12%** — beyond that, treat extra yield as warning, not bonus
- Reasoning: SET dividend payers above 12% yield are usually telling you the dividend is at risk

### Valuation score (20% weight) — Goldilocks P/E
- **P/E 8-15 = sweet spot** (100)
- P/E 5-8 = could be deep value or distress (linear from 70-100)
- P/E 15-20 = paying up (linear from 100 down to 50)
- P/E 20-25 = expensive for a dividend stock (linear from 50 to 0)
- P/E < 4 or > 25 — already excluded by hard filter

### Trend score (20% weight) — uptrend confirmation
Combines two factors:
- **1Y performance** (50% of trend score) — must be positive
- **% above SMA200** (50%) — linear reward (2 points per % above SMA200, capped at 50 points). The range 3-15% above is considered a 'sweet spot' (not extended, not threatening), though the score increases linearly up to 25% above SMA200.

### Pullback opportunity (20% weight) — entry timing
- **RSI 35-55** = best entry zone (pullback, not crashing)
- RSI 55-65 = OK but less attractive (close to overbought)
- RSI > 65 = wait for pullback (no bonus)
- RSI < 35 = potential bounce but check trend score (could be in distress)

## Grading

| Score | Grade | Interpretation |
|---|---|---|
| ≥ 75 | **Excellent** | High yield + healthy uptrend + good entry RSI — top buy candidate |
| 60-74 | **Good** | All criteria pass, just not optimal in 1-2 factors |
| 45-59 | **Fair** | Meets minimums but missing edge — watchlist only |
| < 45 | (filtered) | Doesn't pass hard filters |

## Output Schema

Each candidate row:
```
{
  "symbol":     "TFM.BK",
  "name":       "Thai Foods Group",
  "sector":     "Process Industries",
  "price":      6.55,
  "market_cap": 6.5B,
  "dividend_yield": 9.23,
  "pe_ratio":   8.7,
  "rsi":        48.2,
  "sma50":      6.4,
  "sma200":     5.9,
  "perf_1m":    2.1,
  "perf_y":     33.2,
  "score":      83.7,
  "grade":      "Excellent",
  "score_breakdown": {
    "yield_score":     76,
    "valuation_score": 100,
    "trend_score":     65,
    "pullback_score":  100
  }
}
```

## Caveats

- **Ex-dividend gaps** — TradingView yields are based on trailing 12-month payouts vs current price. Right after ex-dividend date, yield can look inflated.
- **One-time special dividends** are NOT distinguished from regular payouts — manual review for any candidate with yield > 10%.
- **Dividend cuts** are NOT predicted — this is a snapshot screener, not a fundamentals deep-dive. Confirm payout sustainability via the company's IR site before buying.
- **Sector concentration** — Thai dividend payers cluster in Finance / Process Industries / Energy. Top 30 list often has 50%+ from these sectors. Diversify manually.

## Combining with other skills

1. Run this skill weekly to refresh the candidate universe.
2. For each Excellent / Good candidate → check news in last 30 days for any dividend-cut signals.
3. For high-conviction picks → paper-trade entry via dashboard's 📝 button (default fallback: stop -8%, target +25%).
4. Weekly: re-run; downgrade candidates that have moved out of Excellent grade.
