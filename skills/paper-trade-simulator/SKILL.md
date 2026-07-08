---
name: paper-trade-simulator
description: Simulate trades without real money to test strategy and emotional discipline. Track open positions, P/L in R-multiples, MAE/MFE, journal entries, and discipline metrics. Auto-checks stop/target on mark updates.
---

# Paper Trade Simulator

## Overview

Practice trading with virtual money to:
- Test the **discipline** to honor stop-loss and target-take-profit
- Track **emotional patterns** (panic exits, FOMO buys, holding losers too long)
- Measure **strategy performance** in R-multiples without capital risk
- Build **muscle memory** for the trading workflow before real-money execution

## Prerequisites

- Python 3.x with standard packages installed.
- SQLite database configured at `state/market_cache.db`.

## When to Use

- ก่อนเปิด position จริง — ลอง "ซื้อ" บน paper แล้วดูว่าตัวเองทนถือได้ไหม
- ทดสอบ screener output (VCP / CANSLIM / Thai Swing) ว่าได้ผลจริงไหม
- Track emotional triggers — เมื่อราคาตก 50% ของ stop รู้สึกอย่างไร?
- Build journal สำหรับ self-review เป็น weekly retrospective

## Workflow

### Opening a position
```bash
python3 scripts/paper_trade.py open \
  --symbol BAY.BK --market TH --shares 100 \
  --entry 29.25 --stop 27.94 --target 31.88 \
  --source thai-swing-momentum --source-score 77.7 \
  --notes "SET50 bank, breakout setup from Friday close"
```

### Closing manually
```bash
python3 scripts/paper_trade.py close \
  --id 1 --exit-price 31.50 --emotion calm \
  --notes "Hit profit target near 31.88, took 90% off"
```

### Refresh prices + auto-trigger stop/target
```bash
python3 scripts/update_marks.py
# Output: 3 positions updated, 1 hit target (auto-closed), 0 hit stop
```

### List positions + stats
```bash
python3 scripts/paper_trade.py list --status open
python3 scripts/paper_trade.py stats
```

`stats` includes aggregate performance plus calibration breakdowns:
- `by_source`: win rate, expectancy, average R, and average source score per strategy/source.
- `by_score_bucket`: the same metrics grouped into `<50`, `50-69`, `70-84`, `85+`, and `unknown` score buckets.

## Data Storage

Single shared SQLite DB at `state/market_cache.db` — adds one table `paper_trade`. No new files; integrates with existing dashboard cache.

## Discipline Metrics

| Metric | Formula | Healthy Range |
|---|---|---|
| **Stop respect rate** | `closed_stop / (closed_stop + closed_manual_loss)` | > 80% (don't override stops) |
| **Patience score** | `1 − (early_cuts / eligible_winners)` where early_cut = realized_r leaves > 0.5R unrealized vs MFE | > 70% (let winners run) |
| **Target hit rate** | `closed_target / total_closed` | > 30% (depends on strategy) |
| **Avg R per win** | `avg(realized_r WHERE realized_r > 0)` | > 1.5R |
| **Avg R per loss** | `avg(realized_r WHERE realized_r < 0)` | between -0.8 and -1R |
| **Expectancy** | `win_rate × avg_win_R − loss_rate × avg_loss_R` | > 0.3R |

## Psychology Features

- **Emotion tagging**: 7 options with emoji (😎 confident · 😌 calm · 😨 fearful · 🤑 greedy · 😤 frustrated · 🤩 fomo · 🤔 uncertain) at entry + exit + journal
- **MAE/MFE tracking**: max adverse + favorable excursion → identify "trades I should have held"
- **Drawdown alerts**: position at -25% (⚠️) and -50% (🚨) of risk shown in P/L column
- **"Left on table" R-multiple**: shown on closed trades — `MFE_R − realized_R` (how much you cut early)
- **Journal log**: append-able timestamped notes per position; visible in expandable row detail

## Dashboard Integration

- 📝 buttons next to ★ favourite on VCP / CANSLIM / Thai Swing / Thai Dividend rows
- Click → styled modal with live risk calculator + emotion pills + notes textarea
- Paper Portfolio card at bottom of dashboard shows live stats + open/closed tables
- Click any row → expand to see embedded 1Y chart with Entry/Stop/Target/MAE/MFE overlay lines
- Stale-price color coding (green < 5 min, gold 1-24h, red > 24h)
- Toast notifications instead of blocking alerts

## Output

Reports go to `reports/paper_portfolio_<date>.{md,json}`:
- Open positions snapshot
- Closed trades log
- Performance stats
- Discipline scorecard
- Source and score-bucket calibration breakdowns
- Journal extracts

## Resources

- `references/discipline_rules.md`
