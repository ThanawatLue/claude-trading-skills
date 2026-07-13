---
layout: default
title: "Paper Trade Simulator"
grand_parent: English
parent: Skill Guides
nav_order: 44
lang_peer: /ja/skills/paper-trade-simulator/
permalink: /en/skills/paper-trade-simulator/
---

# Paper Trade Simulator
{: .no_toc }

Simulate trades without real money to test strategy and emotional discipline. Track open positions, P/L in R-multiples, MAE/MFE, journal entries, and discipline metrics. Auto-checks stop/target on mark updates.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/paper-trade-simulator){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

Practice trading with virtual money to:
- Test the **discipline** to honor stop-loss and target-take-profit
- Track **emotional patterns** (panic exits, FOMO buys, holding losers too long)
- Measure **strategy performance** in R-multiples without capital risk
- Build **muscle memory** for the trading workflow before real-money execution

---

## 2. When to Use

- ก่อนเปิด position จริง — ลอง "ซื้อ" บน paper แล้วดูว่าตัวเองทนถือได้ไหม
- ทดสอบ screener output (VCP / CANSLIM / Thai Swing) ว่าได้ผลจริงไหม
- Track emotional triggers — เมื่อราคาตก 50% ของ stop รู้สึกอย่างไร?
- Build journal สำหรับ self-review เป็น weekly retrospective

---

## 3. Prerequisites

- Python 3.x with standard packages installed.
- SQLite database configured at `state/market_cache.db`.

---

## 4. Quick Start

```bash
python3 scripts/paper_trade.py open \
  --symbol BAY.BK --market TH --shares 100 \
  --entry 29.25 --stop 27.94 --target 31.88 \
  --source thai-swing-momentum --source-score 77.7 \
  --notes "SET50 bank, breakout setup from Friday close"
```

---

## 5. Workflow

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

---

## 6. Resources

**References:**

- `skills/paper-trade-simulator/references/discipline_rules.md`

**Scripts:**

- `skills/paper-trade-simulator/scripts/paper_trade.py`
- `skills/paper-trade-simulator/scripts/update_marks.py`
