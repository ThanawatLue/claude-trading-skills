---
name: us-market-bubble-detector
description: Evaluates market bubble risk through quantitative data-driven analysis using the revised Minsky/Kindleberger framework v2.1. Prioritizes objective metrics (Put/Call, VIX, margin debt, breadth, IPO data) over subjective impressions. Features strict qualitative adjustment criteria with confirmation bias prevention. Supports practical investment decisions with mandatory data collection and mechanical scoring. Use when user asks about bubble risk, valuation concerns, or profit-taking timing.
---

# US Market Bubble Detection Skill (Revised v2.1)

## Key Revisions in v2.1

**Critical Changes from v2.0:**
1. ✅ **Mandatory Quantitative Data Collection** - Use measured values, not impressions or speculation
2. ✅ **Clear Threshold Settings** - Specific numerical criteria for each indicator
3. ✅ **Two-Phase Evaluation Process** - Quantitative evaluation → Qualitative adjustment (strict order)
4. ✅ **Stricter Qualitative Criteria** - Max +3 points (reduced from +5), requires measurable evidence
5. ✅ **Confirmation Bias Prevention** - Explicit checklist to avoid over-scoring


---

## When to Use This Skill

Use this skill when:
- User asks "Is the market in a bubble?" or "Are we in a bubble?"
- User seeks advice on profit-taking, new entry timing, or short-selling decisions
- User reports social phenomena (non-investors entering, media frenzy, IPO flood)
- User mentions narratives like "this time is different" or "revolutionary technology" becoming mainstream
- User consults about risk management for existing positions

---

## Prerequisites

This skill requires a working Python environment with `uv` (a fast Python package installer and resolver) and access to the internet for data retrieval. Ensure the following are installed and configured:

- **Python 3.8+**: Ensure Python is installed and available in your PATH.
- **uv**: Install `uv` globally or in your project's virtual environment:
  ```bash
  pip install uv
  ```
- **Internet Access**: Required to fetch real-time market data from sources like CBOE DataShop, Yahoo Finance, FINRA, Renaissance Capital IPO, etc.

---

## Evaluation Process (Strict Order)

### Phase 1: Mandatory Quantitative Data Collection

**CRITICAL: Always collect the following data before starting evaluation**

#### 1.1 Market Structure Data (Highest Priority)
```
□ Put/Call Ratio (CBOE Equity P/C)
  - Source: CBOE DataShop or web_search "CBOE put call ratio"
  - Collect: 5-day moving average

□ VIX (Fear Index)
  - Source: Yahoo Finance ^VIX or web_search "VIX current"
  - Collect: Current value + percentile over past 3 months

□ Volatility Indicators
  - 21-day realized volatility
  - Historical position of VIX (determine if in bottom 10th percentile)
```

#### 1.2 Leverage & Positioning Data
```
□ FINRA Margin Debt Balance
  - Source: web_search "FINRA margin debt latest"
  - Collect: Latest month + Year-over-Year % change

□ Breadth (Market Participation)
  - % of S&P 500 stocks above 50-day MA
  - Source: web_search "S&P 500 breadth 50 day moving average"
```

#### 1.3 IPO & New Issuance Data
```
□ IPO Count & First-Day Performance
  - Source: Renaissance Capital IPO or web_search "IPO market 2025"
  - Collect: Quarterly count + median first-day return
```

**⚠️ CRITICAL: Do NOT proceed with evaluation without Phase 1 data collection**

---

### Phase 2: Quantitative Evaluation (Quantitative Scoring)

Score mechanically based on collected data using 8 quantitative indicators. Each indicator is scored from 0-2 points, leading to a maximum of 16 points for this phase. Refer to the `quick_reference.md` for detailed scoring criteria for each indicator.

---

### Phase 3: Qualitative Adjustment (REVISED v2.1)

**Limit: +3 points maximum (REDUCED from +5 in v2.0)**

**⚠️ CONFIRMATION BIAS PREVENTION CHECKLIST:**
```
Before adding ANY qualitative points:
□ Do I have concrete, measurable data? (not impressions)
□ Would an independent observer reach the same conclusion?
□ Am I avoiding double-counting with Phase 2 scores?
□ Have I documented specific evidence with sources?
```

#### Adjustment A: Social Penetration (0-1 points, STRICT CRITERIA)
```
+1 point: ALL THREE criteria must be met:
  ✓ Direct user report of non-investor recommendations
  ✓ Specific examples with names/dates/conversations
  ✓ Multiple independent sources (minimum 3)

+0 points: Any criteria missing

⚠️ INVALID EXAMPLES:
- "AI narrative is prevalent" (unmeasurable)
- "I saw articles about retail investors" (not direct report)
- "Everyone is talking about stocks" (vague, unverified)

✅ VALID EXAMPLE:
"My barber asked about NVDA (Nov 1), dentist mentioned AI stocks (Nov 2),
Uber driver discussed crypto (Nov 3)"
```

#### Adjustment B: Media/Search Trends (0-1 points, REQUIRES MEASUREMENT)
```
+1 point: BOTH criteria must be met:
  ✓ Google Trends showing 5x+ YoY increase (measured)
  ✓ Mainstream coverage confirmed (Time covers, TV specials with dates)

+0 points: Search trends <5x OR no mainstream coverage

⚠️ CRITICAL: "Elevated narrative" without data = +0 points

HOW TO VERIFY:
1. Search "[topic] Google Trends 2025" and document numbers
2. Search "[topic] Time magazine cover" for specific dates
3. Search "[topic] CNBC special" for episode confirmation

✅ VALID EXAMPLE:
"Google Trends: 'AI stocks' at 780 (baseline 150 = 5.2x).
Time cover 'AI Revolution' (Oct 15, 2025).
CNBC 'AI Investment Special' (3 episodes Oct 2025)."

⚠️ INVALID EXAMPLE:
"AI/technology narrative seems elevated" (unmeasurable)
```

#### Adjustment C: Valuation Disconnect (0-1 points, AVOID DOUBLE-COUNTING)
```
+1 point: ALL criteria must be met:
  ✓ P/E >25 (if NOT already counted in Phase 2 quantitative)
  ✓ Fundamentals explicitly ignored in mainstream discourse
  ✓ "This time is different" documented in major media

+0 points: P/E <25 OR fundamentals support valuations

⚠️ SELF-CHECK QUESTIONS (if ANY is YES, score = 0):
- Is P/E already in Phase 2 quantitative scoring?
- Do companies have real earnings supporting valuations?
- Is the narrative backed by fundamental improvements?

✅ VALID EXAMPLE for +1:
"S&P P/E = 35x (vs historical 18x).
CNBC article: 'Earnings don't matter in AI era' (Oct 2025).
Bloomberg: 'Traditional metrics obsolete' (Nov 2025)."

⚠️ INVALID EXAMPLE:
"P/E 30.8 but companies have real earnings and AI has fundamental backing"
(fundamentals support = +0 points)
```

**Phase 3 Total: Maximum +3 points**

---

### Phase 4: Final Judgment (REVISED v2.1)

```
Final Score = Phase 2 Total (0-16 points) + Phase 3 Adjustment (0 to +3 points)
Range: 0 to 19 points

Judgment Criteria (with Risk Budget):
- 0-4 points: Normal (Risk Budget: 100%)
- 5-8 points: Caution (Risk Budget: 70-80%)
- 9-12 points: Euphoria (Risk Budget: 40-50%)
- 13-19 points: Critical (Risk Budget: 20-30%)
```

---

## Data Sources (Required)

### US Market
- **Put/Call**: https://www.cboe.com/tradable_products/vix/
- **VIX**: Yahoo Finance (^VIX) or https://www.cboe.com/
- **Margin Debt**: https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics
- **Breadth**: https://www.barchart.com/stocks/indices/sp/sp500?viewName=advanced
- **IPO**: https://www.renaissancecapital.com/IPO-Center/Stats

### Japanese Market
- **Nikkei Futures P/C**: https://www.barchart.com/futures/quotes/NO*0/options
- **JNIVE**: https://www.investing.com/indices/nikkei-volatility-historical-data
- **Margin Debt**: JSF (Japan Securities Finance) Monthly Report
- **Breadth**: https://en.macromicro.me/series/31841/japan-topix-index-200ma-breadth
- **IPO**: https://www.pwc.co.uk/services/audit/insights/global-ipo-watch.html

---

## Implementation Checklist

For a detailed implementation checklist and best practices, please refer to `references/implementation_guide.md` and `references/quick_reference.md`.

---

## Important Principles (Revised)

### 1. Data > Impressions
Ignore "many news reports" or "experts are cautious" without quantitative data.

### 2. Strict Order: Quantitative → Qualitative
Always evaluate in this order: Phase 1 (Data Collection) → Phase 2 (Quantitative) → Phase 3 (Qualitative Adjustment).

### 3. Upper Limit on Subjective Indicators
Qualitative adjustment has a total limit of +5 points. It cannot override quantitative evaluation.

### 4. "Taxi Driver" is Symbolic
Do not readily acknowledge mass penetration without direct recommendations from non-investors.

---

## Common Failures and Solutions (Revised)

### Failure 1: Evaluating Based on News Articles
❌ "Many reports on Takaichi Trade" → Media saturation 2 points
✅ Verify Google Trends numbers → Evaluate with measured values

### Failure 2: Overreaction to Expert Comments
❌ "Warning of overheating" → Euphoria zone
✅ Judge with measured values of Put/Call, VIX, margin debt

### Failure 3: Emotional Reaction to Price Rise
❌ 4.5% rise in 1 day → Price acceleration 2 points
✅ Verify position in 10-year distribution → Objective evaluation

### Failure 4: Judgment Based on Valuation Alone
❌ P/E 17 → Valuation disconnect 2 points
✅ P/E + narrative dependence + other quantitative indicators for comprehensive judgment

---

## Recommended Actions by Bubble Stage

For detailed recommended actions, risk budgets, and short-selling guidelines for each bubble stage, please refer to the "Action Matrix by Bubble Stage" in `quick_reference.md`.

---

## Composite Conditions for Short-Selling

For detailed composite conditions for short-selling, please refer to `quick_reference.md`.

---

## Output Format

### Evaluation Report Structure (v2.1)

```markdown
# [Market Name] Bubble Evaluation Report (Revised v2.1)

## Overall Assessment
- Final Score: X/19 points
- Phase: [Normal/Caution/Euphoria/Critical]
- Risk Level: [Low/Medium/High/Extremely High]
- Evaluation Date: YYYY-MM-DD

## Quantitative Evaluation (Phase 2)

| Indicator           | Measured Value | Score | Rationale |
|---------------------|----------------|-------|-----------|
| Mass Penetration    | [value]        | [0-2] | [reason]  |
| Media Saturation    | [value]        | [0-2] | [reason]  |
| New Entrants        | [value]        | [0-2] | [reason]  |
| Issuance Flood      | [value]        | [0-2] | [reason]  |
| Leverage            | [value]        | [0-2] | [reason]  |
| Price Acceleration  | [value]        | [0-2] | [reason]  |
| Valuation Disconnect| [value]        | [0-2] | [reason]  |
| Correlation & Breadth| [value]       | [0-2] | [reason]  |

**Phase 2 Total: X/16 points**

## Qualitative Adjustment (Phase 3) - STRICT CRITERIA

**⚠️ Confirmation Bias Check:**
- [ ] All qualitative points have measurable evidence
- [ ] No double-counting with Phase 2
- [ ] Independent observer would agree

### A. Social Penetration (0-1 points)
- Evidence: [REQUIRED: Direct user reports with dates/names]
- Score: [+0 or +1]
- Justification: [Must meet ALL three criteria]

### B. Media/Search Trends (0-1 points)
- Google Trends Data: [REQUIRED: Measured numbers, YoY multiplier]
- Mainstream Coverage: [REQUIRED: Specific Time covers, TV specials with dates]
- Score: [+0 or +1]
- Justification: [Must have 5x+ search AND mainstream confirmation]

### C. Valuation Disconnect (0-1 points)
- P/E Ratio: [Current value]
- Fundamental Backing: [Yes/No - if Yes, score = 0]
- Narrative Analysis: [REQUIRED: Specific media quotes ignoring fundamentals]
- Score: [+0 or +1]
- Justification: [Must show fundamentals actively ignored]

**Phase 3 Total: +X/3 points (max reduced from +5 in v2.0)**

## Recommended Actions

**Risk Budget: X%** (Phase: [Normal/Caution/Euphoria/Critical])
- [Specific action 1]
- [Specific action 2]
- [Specific action 3]

**Short-Selling: [Not Allowed/Consider Cautiously/Active/Recommended]**
- Composite conditions: X/7 met
- Minimum required: [0/2/3/5] for current phase

## Key Changes in v2.1
- Stricter qualitative criteria (max +3, down from +5)
- Added "Elevated Risk" phase for 8-9 points
- Confirmation bias prevention checklist
- All qualitative points require measurable evidence
```

---

## Runnable Examples

To run the US Market Bubble Detector skill, you typically invoke it through a Python script that orchestrates the data collection and evaluation process.

**Example 1: Run the bubble detection for the US market in manual assessment mode**

```bash
# Navigate to the project root directory
cd D:\\ex_work\\trading

# Ensure dependencies are installed (if not already)
uv pip install -e .

# Execute the skill (run in manual mode for interactive scoring, outputting as text)
python -m skills.us_market-bubble-detector.scripts.bubble_scorer --manual --output text
```

**Example 2: Run the bubble detection by providing scores directly (non-interactive)**

```bash
# Navigate to the project root directory
cd D:\\ex_work\\trading

# Ensure dependencies are installed (if not already)
uv pip install -e .

# Execute the skill with predefined scores (outputting as JSON)
python -m skills.us_market-bubble-detector.scripts.bubble_scorer --scores '{"mass_penetration":2,"media_saturation":1,"new_accounts":2,"new_issuance":1,"leverage":1,"price_acceleration":2,"valuation_disconnect":2,"breadth_expansion":1}' --output json
```

---

## Reference Documents

### `references/implementation_guide.md` (English) - **RECOMMENDED FOR FIRST USE**
- Step-by-step evaluation process with mandatory data collection
- NG examples vs OK examples
- Self-check quality criteria (4 levels)
- Red flags during review
- Best practices for objective evaluation

### `references/bubble_framework.md` (English)
- Detailed theoretical framework
- Explanation of Minsky/Kindleberger model
- Behavioral psychology elements

### `references/historical_cases.md` (English)
- Analysis of past bubble cases
- Dotcom, Crypto, Pandemic bubbles
- Common pattern extraction

### `references/quick_reference.md` (English)
- Daily checklist
- Emergency 3-question assessment
- Quick scoring guide
- Key data sources

### When to Load References
- **First use or need detailed guidance:** Load `implementation_guide.md`
- **Need theoretical background:** Load `bubble_framework.md`
- **Need historical context:** Load `historical_cases.md`
- **Daily operations:** Load `quick_reference.md` (English)

---

## Summary: Essence of v2.1 Revision

**v2.0 Problem (Identified Nov 2025):**
- Qualitative adjustment too loose (+5 max)
- "AI narrative elevated" → +1 point (no data)
- "P/E 30.8" → +1 point (double-counting with quantitative)
- **Result: 11/16 points - overly bearish without evidence**

**v2.1 Solution:**
- Qualitative adjustment stricter (+3 max)
- "AI narrative elevated" → 0 points (unmeasured)
- "P/E 30.8 but AI has fundamental backing" → 0 points (fundamentals support)
- **Result: 9/15 points - balanced, data-driven assessment**

Key Improvements:
1. **Confirmation Bias Prevention**: Explicit checklist before adding qualitative points
2. **Measurable Evidence Required**: No points without concrete data (Google Trends, media coverage)
3. **Double-Counting Prevention**: Valuation must not duplicate Phase 2 quantitative

**Core Principle:**
> "In God we trust; all others must bring data." - W. Edwards Deming

**2025 Lesson:**
Even data-driven frameworks can be undermined by subjective qualitative adjustments.
v2.1 requires MEASURABLE evidence for ALL qualitative points.
Independent observers must be able to verify each adjustment.

---

**Version History:**
- **v2.0** (Oct 27, 2025): Mandatory quantitative data collection
- **v2.1** (Nov 3, 2025): Stricter qualitative criteria, confirmation bias prevention, granular risk phases

**Reason for v2.1 Revision:**
Prevent over-scoring through unmeasured "narrative" assessments and double-counting.
Ensure all bubble risk evaluations are independently verifiable and free from confirmation bias.
