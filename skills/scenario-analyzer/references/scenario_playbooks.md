# Scenario Playbooks

This reference provides templates and best practices for constructing 18-month scenarios. Use this to maintain consistency and high-quality analysis.

## Core Principles of Scenario Construction

### 1. MECE Principle (Mutually Exclusive, Collectively Exhaustive)
Your scenarios should meet the following conditions:
- **Mutually Exclusive**: Scenarios do not overlap.
- **Collectively Exhaustive**: Cover all major paths of possibility.

### 2. Probability Allocation Guidelines

| Scenario | Typical Range | Allocation Rationale |
|---------|----------|-----------|
| Base Case | 50-65% | Most probable course of development |
| Bull Case | 15-25% | Positive upside outcome |
| Bear Case | 20-30% | Negative downside outcome |
| **Total** | **100%** | Always ensure the sum equals exactly 100% |

**When Asymmetric Allocation is Appropriate:**
- Bull > Bear: Environment with predominantly positive catalysts.
- Bear > Bull: Environment with predominantly risk factors.
- Base > 60%: Scenario uncertainty is relatively low.
- Base < 50%: Scenario uncertainty is extremely high (even the Base Case is highly uncertain).

### 3. Timeline Intervals

**Three-Phase Structure:**
- **0-6 Months**: Short-term reactions, initial market impact.
- **6-12 Months**: Medium-term progression, trend formation.
- **12-18 Months**: Long-term resolution, new equilibrium.

---

## Scenario Templates

### Base Case Template

```markdown
### Base Case (XX% Probability)

**Summary**:
[Summarize the scenario in 1-2 sentences. Describe the most probable course of action.]

**Key Assumptions**:
- [Assumption 1]: [Specific condition]
- [Assumption 2]: [Specific condition]
- [Assumption 3]: [Specific condition]

**Timeline**:

**0-6 Months:**
- [Key development 1]
- [Key development 2]
- [Expected market reaction]

**6-12 Months:**
- [Medium-term development 1]
- [Medium-term development 2]
- [Trend direction]

**12-18 Months:**
- [Long-term resolution 1]
- [New equilibrium state]
- [Structural shifts, if any]

**Impact on Economic Indicators**:
| Metric | Current | 6M Forecast | 12M Forecast | 18M Forecast |
|------|------|------------|-------------|-------------|
| GDP Growth Rate | X% | X% | X% | X% |
| Inflation Rate | X% | X% | X% | X% |
| Policy Rate | X% | X% | X% | X% |
| Unemployment Rate | X% | X% | X% | X% |

**Key Catalysts**:
- [Catalyst 1 supporting this scenario]
- [Catalyst 2 supporting this scenario]

**Invalidation Signals**:
- [Sign 1 that this scenario is breaking down]
- [Sign 2 that this scenario is breaking down]
```

### Bull Case Template

```markdown
### Bull Case (XX% Probability)

**Summary**:
[Summarize the optimistic scenario in 1-2 sentences. Describe what upside develops.]

**Key Assumptions**:
- [Optimistic Assumption 1]: [Specific condition]
- [Optimistic Assumption 2]: [Specific condition]
- [Optimistic Assumption 3]: [Specific condition]

**Timeline**:

**0-6 Months:**
- [Positive development 1]
- [Positive development 2]
- [Expected positive market reaction]

**6-12 Months:**
- [Continuation of upside trend]
- [Additional positive factors]
- [Improved market sentiment]

**12-18 Months:**
- [Resolution of optimistic scenario]
- [State of success achieved]
- [Assessment of sustainability]

**Impact on Economic Indicators**:
[Assume better metrics than the Base Case]

**Upside Catalysts**:
- [Catalyst 1 that drives this scenario]
- [Catalyst 2 that drives this scenario]

**Conditions Enhancing Probability**:
- [Condition 1]
- [Condition 2]
```

### Bear Case Template

```markdown
### Bear Case (XX% Probability)

**Summary**:
[Summarize the risk scenario in 1-2 sentences. Describe what downside develops.]

**Key Assumptions**:
- [Risk Assumption 1]: [Specific condition]
- [Risk Assumption 2]: [Specific condition]
- [Risk Assumption 3]: [Specific condition]

**Timeline**:

**0-6 Months:**
- [Negative development 1]
- [Negative development 2]
- [Expected negative market reaction]

**6-12 Months:**
- [Continuation/deepening of downside trend]
- [Emergence of secondary problems]
- [Deteriorating market sentiment]

**12-18 Months:**
- [Resolution of risk scenario]
- [Worst-case state of affairs]
- [Path to recovery, if any]

**Impact on Economic Indicators**:
[Assume worse metrics than the Base Case]

**Downside Risk Factors**:
- [Risk factor 1 driving this scenario]
- [Risk factor 2 driving this scenario]

**Conditions Enhancing Probability**:
- [Condition 1]
- [Condition 2]

**Risk Mitigation Factors**:
- [Mitigative factor 1 that could soften this scenario]
- [Mitigative factor 2 that could soften this scenario]
```

---

## Event-Specific Playbooks

### 1. Monetary Policy Events (Rate Hikes)

**Base Case (55%):**
- Rate hike implemented as expected.
- Market has largely priced it in.
- Minor stock correction, slight rise in bond yields.

**Bull Case (20%):**
- Rate hike size is smaller than expected.
- Dovish forward guidance.
- Stock market rally.

**Bear Case (25%):**
- Rate hike size is larger than expected.
- Hawkish forward guidance.
- Stock market drops sharply, credit spreads widen.

### 2. Geopolitical Events (Outbreak of Conflict)

**Base Case (50%):**
- Conflict remains localized.
- Short-term rise in commodity prices.
- Conditions stabilize within a few months.

**Bull Case (15%):**
- Early ceasefire or peace agreement.
- Commodity prices normalize.
- Markets recover quickly.

**Bear Case (35%):**
- Conflict prolongs and expands.
- Severe disruption of commodity supply.
- Global inflation accelerates, recession risk increases.

### 3. Technological Shifts (AI Regulation)

**Base Case (50%):**
- Moderate regulations introduced.
- Focused primarily on industry self-regulation.
- Limited impact on innovation.

**Bull Case (25%):**
- Regulation designed in favor of the industry.
- Clarified regulation accelerates investment.
- Establishes barriers to entry favoring large incumbents.

**Bear Case (25%):**
- Strict regulations implemented.
- Substantial restrictions on AI development.
- Decline in competitiveness of affected firms.

### 4. Corporate Events (Mega M&A)

**Base Case (60%):**
- Regulatory approval obtained.
- Transaction closes on schedule.
- Gradual realization of merger synergies.

**Bull Case (15%):**
- Realized synergies exceed expectations.
- Integration proceeds smoothly.
- Complementary M&A strategies succeed.

**Bear Case (25%):**
- Regulatory block or conditional approval.
- Integration delayed or fails.
- Synergies fail to materialize.

---

## Scenario Quality Checklist

### Internal Consistency
- [ ] Are the assumptions for each scenario logically consistent?
- [ ] Are causal relationships clear across the timeline?
- [ ] Are the economic indicator forecasts mutually consistent?

### External Validity
- [ ] Is the scenario consistent with historical precedents?
- [ ] Does it accurately reflect current market conditions?
- [ ] Does it avoid extreme divergence from expert opinions?

### Actionability
- [ ] Is it specific enough to aid investment decisions?
- [ ] Are trackable catalysts identified?
- [ ] Are invalidation signals clear?

### Comprehensiveness
- [ ] Are the key risk scenarios covered?
- [ ] Is upside potential appropriately weighed?
- [ ] Are tail risks addressed?

---

## Common Pitfalls and Mitigation

### 1. Status Quo Bias
- **Problem**: Allocating too high a probability to the Base Case (above 70%).
- **Mitigation**: Recognize that historically, the probability of "nothing changing" is low.

### 2. Recency Bias
- **Problem**: Overestimating the impact of the most recent events.
- **Mitigation**: Maintain a long-term perspective and reference historical patterns.

### 3. Confirmation Bias
- **Problem**: Adapting only interpretations that support the headline event.
- **Mitigation**: Actively search for opposing views.

### 4. Spurious Precision
- **Problem**: Forecasting metrics 18 months out to decimal points.
- **Mitigation**: Acknowledge uncertainty and express estimates in ranges.

### 5. Overlapping Scenarios
- **Problem**: Base, Bull, and Bear cases overlap.
- **Mitigation**: Define boundary conditions clearly.

---

## Probability Updating Guidelines

When new information arrives, adjust probabilities as follows:

| Nature of New Information | Probability Adjustment |
|-------------|---------------|
| Data supporting a scenario | +5% to +15% |
| Data contradicting a scenario | -5% to -15% |
| Decisive evidence | +20% to +30% or -20% to -30% |
| Appearance of new risk factors | Bear Case +5% to +10% |
| Resolution of risk factors | Bear Case -5% to -10% |

**Always normalize the total probability back to 100% after adjustments.**

---

## Output Quality Standards

High-quality scenarios exhibit:
1. **Specificity**: Contains numbers, dates, and names.
2. **Logic**: Causal chains are clear.
3. **Verifiability**: Can be proven right or wrong in hindsight.
4. **Actionability**: Directly maps to investment decisions.
5. **Humility**: Appropriately reflects uncertainty.
