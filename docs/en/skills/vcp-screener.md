---
layout: default
title: "VCP Screener"
grand_parent: English
parent: Skill Guides
nav_order: 69
lang_peer: /ja/skills/vcp-screener/
permalink: /en/skills/vcp-screener/
---

# VCP Screener
{: .no_toc }

Screen S&P 500 (US) or SET50 (Thai) stocks for Mark Minervini's Volatility Contraction Pattern (VCP). Identifies Stage 2 uptrend stocks forming tight bases with contracting volatility near breakout pivot points.
{: .fs-6 .fw-300 }

<span class="badge badge-api">FMP Required</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/vcp-screener.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/vcp-screener){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# VCP Screener - Minervini Volatility Contraction Pattern

---

## 2. When to Use

- User asks for VCP screening or Minervini-style setups
- User wants to find tight base / volatility contraction patterns
- User requests Stage 2 momentum stock scanning in US or Thai markets
- User asks for breakout candidates with defined risk

---

## 3. Prerequisites

- FMP API key (for US market full scans) or yfinance (free, default for Thai and selective US universes)
- Python 3.9+ with `yfinance` and `pandas`

---

## 4. Quick Start

```bash
# US Market: Default (top 100 S&P 500)
python3 skills/vcp-screener/scripts/screen_vcp.py --market US

# Thai Market: SET50 constituents
python3 skills/vcp-screener/scripts/screen_vcp.py --market TH

# Custom universe
python3 skills/vcp-screener/scripts/screen_vcp.py --universe AAPL NVDA --market US
```

---

## 5. Workflow

### Step 1: Prepare and Execute Screening

Execute the VCP screener script for the desired market:

```bash
# US Market: Default (top 100 S&P 500)
python3 skills/vcp-screener/scripts/screen_vcp.py --market US

# Thai Market: SET50 constituents
python3 skills/vcp-screener/scripts/screen_vcp.py --market TH

# Custom universe
python3 skills/vcp-screener/scripts/screen_vcp.py --universe AAPL NVDA --market US
```

### Strict Mode (Minervini pure setup)

Only return stocks with `valid_vcp=True` AND `execution_state` in `(Pre-breakout, Breakout)`:

```bash
python3 skills/vcp-screener/scripts/screen_vcp.py --strict --output-dir reports/
```

### Advanced Tuning (for backtesting)

Adjust VCP detection parameters for research and backtesting:

```bash
python3 skills/vcp-screener/scripts/screen_vcp.py \
  --min-contractions 3 \
  --t1-depth-min 12.0 \
  --breakout-volume-ratio 2.0 \
  --trend-min-score 90 \
  --atr-multiplier 1.5 \
  --output-dir reports/
```

**Screener Parameters Reference:**
| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `--min-contractions` | 2 | 2-4 | Higher = fewer but higher-quality patterns |
| `--t1-depth-min` | 10.0% | 1-50 | Higher = excludes shallow first corrections |
| `--breakout-volume-ratio` | 1.5x | 0.5-10 | Higher = stricter volume confirmation |
| `--trend-min-score` | 85 | 0-100 | Higher = stricter Stage 2 filter |
| `--atr-multiplier` | 1.5 | 0.5-5 | Lower = more sensitive swing detection |
| `--contraction-ratio` | 0.70 | 0.1-1 | Lower = requires tighter contractions |
| `--min-contraction-days` | 5 | 1-30 | Higher = longer minimum contraction |
| `--lookback-days` | 120 | 30-365 | Longer = finds older patterns |
| `--max-sma200-extension` | 50.0% | — | SMA200 distance threshold for Overextended state and penalty |
| `--wide-and-loose-threshold` | 15.0% | — | Final contraction depth above which wide-and-loose flag triggers |
| `--strict` | off | — | Minervini strict mode: only Pre-breakout or Breakout with valid VCP |

### Step 2: Review Results

1. Read the generated JSON and Markdown reports
2. Load `references/vcp_methodology.md` for pattern interpretation context
3. Load `references/scoring_system.md` for score threshold guidance

### Step 3: Present Analysis

For each top candidate, present:
- **Quality** (`composite_score` / rating) — how well-formed is the VCP pattern?
- **Execution State** (`execution_state`) — is it buyable now? (Pre-breakout / Breakout = actionable)
- **Pattern Type** (`pattern_type`) — Textbook VCP / VCP-adjacent / Post-breakout / Extended Leader / Damaged
- `★` marker if a State Cap was applied (raw score was downgraded)
- Contraction details (T1/T2/T3 depths and ratios)
- Trade setup: pivot price, stop-loss, risk percentage
- Volume dry-up ratio and breakout_volume_score
- Relative strength rank

### Step 4: Provide Actionable Guidance

**By Execution State (primary filter):**
- **Pre-breakout / Breakout:** Pattern is in the active entry window — apply rating-based sizing
- **Early-post-breakout:** Breakout underway but above ideal entry — reduced size or wait for pullback
- **Extended / Overextended:** Trade missed — add to watchlist for next base
- **Damaged / Invalid:** Setup invalidated — do not enter

**By Rating (secondary, after state confirms actionability):**
- **Textbook VCP (90+):** Buy at pivot with aggressive sizing (1.5-2x)
- **Strong VCP (80-89):** Buy at pivot with standard sizing (1x)
- **Good VCP (70-79):** Buy on volume confirmation above pivot (0.75x)
- **Developing (60-69):** Add to watchlist, wait for tighter contraction
- **Weak/No VCP (<60):** Monitor only or skip

> **⚠️ CRITICAL CONSTRAINT:** You are an analyst, not an execution engine. Do NOT attempt to execute live trades or connect to brokerage APIs to buy these stocks. All position sizing and buy recommendations are strictly for "Paper Trading" or analytical discussion purposes only.

---

## 6. Resources

**References:**

- `skills/vcp-screener/references/fmp_api_endpoints.md`
- `skills/vcp-screener/references/scoring_system.md`
- `skills/vcp-screener/references/vcp_methodology.md`

**Scripts:**

- `skills/vcp-screener/scripts/fmp_client.py`
- `skills/vcp-screener/scripts/report_generator.py`
- `skills/vcp-screener/scripts/scorer.py`
- `skills/vcp-screener/scripts/screen_thai_swing.py`
- `skills/vcp-screener/scripts/screen_vcp.py`
- `skills/vcp-screener/scripts/yf_client.py`
