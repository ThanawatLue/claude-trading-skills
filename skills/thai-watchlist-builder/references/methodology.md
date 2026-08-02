# Thai Watchlist Builder Methodology

This reference document explains the core principles, indicators, and calculation logic used in the Thai Watchlist Builder skill to filter and rank SET stocks.

## The 4 Buckets Explained

### 1. Growth (Stage 2 Leaders)
This bucket targets classic Stage 2 uptrend leaders with strong medium-term momentum.
- **Trend Filters**: Price must be above both its SMA50 and SMA200.
- **Momentum Filters**: 3-month performance must be at least +10%, and 1-month performance must be positive. Daily RSI must be between 50 and 75 (sweet spot for healthy uptrends).
- **Liquidity Filters**: Market cap must be at least 5 Billion THB, and price must be at least 3 THB to avoid illiquid micro-caps.
- **Scoring Formula**:
  $$\text{Score} = (3\text{M Perf} \times 1.5) \times 0.4 + (1\text{M Perf} \times 4.0) \times 0.3 + (100 - |RSI - 62| \times 4) \times 0.3$$

### 2. Value (Cheap with Fundamentals)
This bucket selects stocks that are fundamentally cheap but are not in long-term downtrends (avoiding value traps).
- **Fundamental Filters**: P/E ratio must be between 5 and 15, and dividend yield must be at least 3%. Price must be at least 3 THB.
- **Trend Filters**: Price must be above SMA200, and 1-year performance must be positive.
- **Scoring Formula**:
  - P/E Score (40% weight): $(15 - P/E) \times 6$ (lower P/E is better).
  - Yield Score (40% weight): $\min(100, \text{Dividend Yield} \times 8)$ (higher yield is better).
  - Trend Score (20% weight): $\min(100, 1\text{Y Perf} \times 2)$.

### 3. Momentum (Swing/Breakout Candidates)
This bucket flags highly active momentum plays with recent volume surges.
- **RSI Sweet Spot**: Daily RSI must be between 60 and 78.
- **Volume Surge**: Volume must be at least 1.5x the 10-day average.
- **High Proximity**: Price must be within 8% of the 52-week high.
- **Scoring Formula**:
  - Proximity Score (40% weight): $(1 - (\text{High52} - \text{Price}) / \text{High52}) \times 100$.
  - Volume Score (30% weight): $\min(100, (\text{Vol} / \text{AvgVol} - 1.5) \times 50)$.
  - RSI Score (30% weight): $100 - |RSI - 67| \times 5$.

### 4. Mean-Reversion (Oversold Pullbacks)
This bucket catches oversold pullbacks inside larger long-term uptrends.
- **Oversold Filter**: Daily RSI must be between 28 and 40.
- **Trend Filter**: Price must be above SMA200.
- **Pullback Proximity**: Price must be within 8% of the SMA50.
- **Scoring Formula**:
  - RSI Score (40% weight): $(40 - \text{RSI}) \times 7$.
  - SMA Proximity Score (30% weight): $(1 - \text{SMA50 Dist} / 0.08) \times 100$.
  - Trend Score (30% weight): $\min(100, 1\text{Y Perf} \times 2)$.
ter**: Daily RSI must be between 28 and 40.
- **Trend Filter**: Price must be above SMA200.
- **Pullback Proximity**: Price must be within 8% of the SMA50.
- **Scoring Formula**:
  - RSI Score (40% weight): $(40 - \text{RSI}) \times 7$.
  - SMA Proximity Score (30% weight): $(1 - \text{SMA50 Dist} / 0.08) \times 100$.
  - Trend Score (30% weight): $\min(100, 1\text{Y Perf} \times 2)$.
