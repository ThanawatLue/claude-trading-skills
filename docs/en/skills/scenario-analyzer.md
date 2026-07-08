---
layout: default
title: "Scenario Analyzer"
grand_parent: English
parent: Skill Guides
nav_order: 49
lang_peer: /ja/skills/scenario-analyzer/
permalink: /en/skills/scenario-analyzer/
---

# Scenario Analyzer
{: .no_toc }

Analyze 18-month scenarios from news headlines.
Runs primary analysis using scenario-analyst agent,
and gets a second opinion from strategy-reviewer agent.
Generates a comprehensive report including primary, secondary, and tertiary impact, stock picks, and review in English.
Usage: /scenario-analyzer "Fed raises rates by 50bp"
Trigger: news analysis, scenario analysis, 18-month outlook, mid-to-long-term investment strategy

{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/scenario-analyzer.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/scenario-analyzer){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

This skill analyzes mid-to-long-term (18-month) investment scenarios starting from a news headline.
It sequentially calls two specialist agents (`scenario-analyst` and `strategy-reviewer`) to generate a comprehensive report combining multi-faceted analysis and critical review.

---

## 2. When to Use

Use this skill when you want to:
- Analyze mid-to-long-term investment impact from a news headline.
- Construct multiple scenarios for 18 months into the future.
- Organize impact on sectors and stocks into primary, secondary, and tertiary categories.
- Obtain a comprehensive analysis including a second opinion.
- Generate reports in English.

**Usage Examples:**
```
/scenario-analyzer "Fed raises interest rates by 50bp, signals more hikes ahead"
/scenario-analyzer "China announces new tariffs on US semiconductors"
/scenario-analyzer "OPEC+ agrees to cut oil production by 2 million barrels per day"
```

---

## 3. Prerequisites

- **API Keys**: None (uses WebSearch/WebFetch only)
- **MCP Servers**: None
- **Dependencies**: The `scenario-analyst` and `strategy-reviewer` agents must be available via the Task tool.

---

## 4. Quick Start

```bash
Read `references/headline_event_patterns.md`
Read `references/sector_sensitivity_matrix.md`
Read `references/scenario_playbooks.md`
```

---

## 5. Workflow

### Phase 1: Preparation

#### Step 1.1: Headline Analysis

Analyze the user-input news headline:

1. **Verify Headline**
   - Confirm a news headline is passed as an argument.
   - If not, prompt the user to input a headline.

2. **Extract Keywords**
   - Key entities (companies, countries, organizations).
   - Numerical data (interest rates, prices, quantities).
   - Actions (raise, cut, announce, agree, etc.).

#### Step 1.2: Event Type Classification

Classify the headline into one of the following categories:

| Category | Example |
|---------|-----|
| Monetary Policy | FOMC, ECB, BOJ, rate hikes, rate cuts, QE/QT |
| Geopolitics | War, sanctions, tariffs, trade friction |
| Regulation & Policy | Environmental regs, financial regs, antitrust |
| Technology | AI, EV, renewable energy, semiconductors |
| Commodities | Crude oil, gold, copper, agricultural goods |
| Corporate/M&A | Acquisitions, bankruptcies, earnings, industry consolidation |

#### Step 1.3: Reference Loading

Load the relevant references based on the event type:

```
Read `references/headline_event_patterns.md`
Read `references/sector_sensitivity_matrix.md`
Read `references/scenario_playbooks.md`
```

**Reference Contents:**
- `headline_event_patterns.md`: Past event patterns and market reactions.
- `sector_sensitivity_matrix.md`: Event × sector impact matrix.
- `scenario_playbooks.md`: Templates and best practices for scenario construction.

---

### Phase 2: Agent Invocations

#### Step 2.1: scenario-analyst Invocation

Invoke the main analysis agent using the Agent tool.

```
Agent tool:
- subagent_type: "scenario-analyst"
- prompt: |
    Please perform an 18-month scenario analysis for the following headline.

    ## Target Headline
    [Input Headline]

    ## Event Type
    [Classification Result]

    ## Reference Information
    [Summary of loaded references]

    ## Analysis Requirements
    1. Use WebSearch to collect relevant news from the past 2 weeks.
    2. Construct 3 scenarios (Base/Bull/Bear) with probabilities summing to 100%.
    3. Analyze primary, secondary, and tertiary impact by sector.
    4. Select 3-5 positive and 3-5 negative impact stocks (US market only).
    5. Output everything in English.
```

**Expected Output:**
- List of relevant news articles.
- Details of the 3 scenarios (Base/Bull/Bear).
- Sector impact analysis (primary/secondary/tertiary).
- Recommended stock list.

#### Step 2.2: strategy-reviewer Invocation

Invoke the review agent based on the analysis results from `scenario-analyst`.

```
Agent tool:
- subagent_type: "strategy-reviewer"
- prompt: |
    Please review the following scenario analysis.

    ## Target Headline
    [Input Headline]

    ## Analysis Results
    [Full output from scenario-analyst]

    ## Review Requirements
    Conduct review focusing on:
    1. Overlooked sectors or stocks.
    2. Validity of scenario probability distributions.
    3. Logical consistency of the impact analysis.
    4. Detection of optimistic/pessimistic bias.
    5. Alternative scenario proposals.
    6. Realism of the timeline.

    Provide constructive and specific feedback in English.
```

**Expected Output:**
- Points overlooked.
- Opinions on scenario probabilities.
- Identified biases.
- Alternative scenario suggestions.
- Final recommendations.

---

### Phase 3: Integration & Report Generation

#### Step 3.1: Result Integration

Integrate outputs from both agents to create the final investment thesis.

**Integration Checklist:**
1. Address overlooked items raised during review.
2. Adjust probability distributions (if necessary).
3. Draft final conclusions considering identified biases.
4. Formulate specific action plans.

#### Step 3.2: Report Generation

Generate the final report and save it in the following format.

**Save Path:** `reports/scenario_analysis_<topic>_YYYYMMDD.md`

```markdown
# Headline Scenario Analysis Report

**Analysis Time**: YYYY-MM-DD HH:MM
**Target Headline**: [Input Headline]
**Event Type**: [Classification Category]

---

---

## 6. Resources

**References:**

- `skills/scenario-analyzer/references/headline_event_patterns.md`
- `skills/scenario-analyzer/references/scenario_playbooks.md`
- `skills/scenario-analyzer/references/sector_sensitivity_matrix.md`
