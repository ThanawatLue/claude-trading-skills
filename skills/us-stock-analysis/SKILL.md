---
name: us-stock-analysis
description: Comprehensive US stock analysis including fundamental analysis (financial metrics, business quality, valuation), technical analysis (indicators, chart patterns, support/resistance), stock comparisons, and investment report generation. Use when user requests analysis of US stock tickers (e.g., "analyze AAPL", "compare TSLA vs NVDA", "give me a report on Microsoft"), evaluation of financial metrics, technical chart analysis, or investment recommendations for American stocks.
---

# US Stock Analysis

## Overview

Perform comprehensive analysis of US stocks covering fundamental analysis (financials, business quality, valuation), technical analysis (indicators, trends, patterns), peer comparisons, and generate detailed investment reports. Fetch real-time market data via web search tools and apply structured analytical frameworks.

## When to Use

Use this skill when the user requests any form of analysis, information, or comparison related to US stocks. This includes:
-   **Fetching basic stock information:** Current prices, key metrics, recent news.
-   **Performing fundamental analysis:** Deep dive into financials, business quality, and valuation.
-   **Conducting technical analysis:** Chart patterns, indicators, and trend analysis.
-   **Generating comprehensive investment reports:** Combining fundamental and technical insights with recommendations.
-   **Comparing multiple US stocks:** Side-by-side analysis of peers.

This skill is suitable for queries such as "analyze AAPL", "compare TSLA vs NVDA", "give me a report on Microsoft", "is Amazon overvalued?", or "technical analysis of TSLA".

## Prerequisites

This skill heavily relies on web search capabilities to fetch real-time and historical market data. Ensure the following tools are available and configured:

-   **`google_web_search`**: This tool is essential for querying financial news, company reports, stock metrics, and technical data from various online sources. It requires proper API key setup (if applicable) and access to function effectively.

Without the proper functioning of `google_web_search`, the skill will be unable to gather the necessary data for analysis.

## Workflow

The `us-stock-analysis` skill follows a systematic workflow to process user requests and generate comprehensive insights:

1.  **Parse User Query**: The skill first interprets the user's natural language request to identify the target stock tickers and the desired type of analysis (e.g., Basic Info, Fundamental, Technical, Comprehensive, Comparison).
2.  **Data Acquisition**: Using `google_web_search`, the skill fetches relevant market data, financial statements, key metrics, news, and technical indicators for the identified tickers from reliable sources. This step is critical for up-to-date and accurate analysis.
3.  **Perform Analysis**: Based on the identified analysis type, the skill applies the appropriate analytical frameworks and methodologies (e.g., fundamental ratios, technical patterns, valuation models) to the acquired data. It references internal knowledge bases (`references/fundamental-analysis.md`, `references/technical-analysis.md`, `references/financial-metrics.md`) for detailed guidance.
4.  **Synthesize and Report**: The analyzed data is then synthesized into a coherent and structured report, formatted according to specified guidelines and report templates (`references/report-template.md`). The output provides clear insights, and where applicable, recommendations or comparisons.
5.  **Error Handling**: Throughout the process, the skill is equipped to handle scenarios such as invalid tickers, missing data, or API failures, providing informative feedback or fallback mechanisms.

## Data Sources

Always use web search tools to gather current market data:

**Primary Data to Fetch:**
1. **Current stock price and trading data** (price, volume, 52-week range)
2. **Financial statements** (income statement, balance sheet, cash flow)
3. **Key metrics** (P/E, EPS, revenue, margins, debt ratios)
4. **Analyst ratings and price targets**
5. **Recent news and developments**
6. **Peer/competitor data** (for comparisons)
7. **Technical data** (moving averages, RSI, MACD when available)

**Search Strategy:**
- Use ticker symbol + specific data needed (e.g., "AAPL financial metrics 2024")
- For comprehensive data: Search for earnings reports, investor presentations, or SEC filings
- For technical data: Search for "AAPL technical analysis" or use financial data sites
- Always verify data recency (prefer data from last quarter)

**Quality Sources:**
- Yahoo Finance, Google Finance, MarketWatch, Seeking Alpha, Bloomberg, CNBC
- Company investor relations pages
- SEC filings (10-K, 10-Q) for detailed financials
- TradingView, StockCharts for technical data

## Analysis Types

This skill supports four types of analysis. Determine which type(s) the user needs:

1. **Basic Stock Info** - Quick overview with key metrics
2. **Fundamental Analysis** - Deep dive into business, financials, valuation
3. **Technical Analysis** - Chart patterns, indicators, trend analysis
4. **Comprehensive Report** - Complete analysis combining all approaches

## Analysis Workflows

### 1. Basic Stock Information

**When to Use:** User asks for quick overview or basic info

**Steps:**
1. Search for current stock data (price, volume, market cap)
2. Gather key metrics (P/E, EPS, revenue growth, margins)
3. Get 52-week range and year-to-date performance
4. Find recent news or major developments
5. Present in concise summary format

**Output Format:**
- Company description (1-2 sentences)
- Current price and trading metrics
- Key valuation metrics (table)
- Recent performance
- Notable recent news (if any)

### 2. Fundamental Analysis

**When to Use:** User wants financial analysis, valuation assessment, or business evaluation

**Steps:**
1. **Gather comprehensive financial data:**
   - Revenue, earnings, cash flow (3-5 year trends)
   - Balance sheet metrics (debt, cash, working capital)
   - Profitability metrics (margins, ROE, ROIC)

2. **Read references/fundamental-analysis.md** for analytical framework

3. **Read references/financial-metrics.md** for metric definitions and calculations

4. **Analyze business quality:**
   - Competitive advantages
   - Management track record
   - Industry position

5. **Perform valuation analysis:**
   - Calculate key ratios (P/E, PEG, P/B, EV/EBITDA)
   - Compare to historical averages
   - Compare to peer group
   - Estimate fair value range

6. **Identify risks:**
   - Company-specific risks
   - Market/macro risks
   - Red flags from financial data

7. **Generate output** following references/report-template.md structure

**Critical Analyses:**
- Profitability trends (improving/declining margins)
- Cash flow quality (FCF vs earnings)
- Balance sheet strength (debt levels, liquidity)
- Growth sustainability
- Valuation vs peers and historical average

### 3. Technical Analysis

**When to Use:** User asks for technical analysis, chart patterns, or trading signals

**Steps:**
1. **Gather technical data:**
   - Current price and recent price action
   - Volume trends
   - Moving averages (20-day, 50-day, 200-day)
   - Technical indicators (RSI, MACD, Bollinger Bands)

2. **Read references/technical-analysis.md** for indicator definitions and patterns

3. **Identify trend:**
   - Uptrend, downtrend, or sideways
   - Strength of trend

4. **Locate support and resistance levels:**
   - Recent highs and lows
   - Moving average levels
   - Round numbers

5. **Analyze indicators:**
   - RSI: Overbought (>70) or oversold (<30)
   - MACD: Crossovers and divergences
   - Volume: Confirmation or divergence
   - Bollinger Bands: Squeeze or expansion

6. **Identify chart patterns:**
   - Reversal patterns (head and shoulders, double top/bottom)
   - Continuation patterns (flags, triangles)

7. **Generate technical outlook:**
   - Current trend assessment
   - Key levels to watch
   - Risk/reward analysis
   - Short and medium-term outlook

**Interpretation Guidelines:**
- Confirm signals with multiple indicators
- Consider volume for validation
- Note divergences between price and indicators
- Always identify risk levels (stop-loss)

### 4. Comprehensive Investment Report

**When to Use:** User asks for detailed report, investment recommendation, or complete analysis

**Steps:**
1. **Perform data gathering** (as in Basic Info)

2. **Execute fundamental analysis** (follow workflow above)

3. **Execute technical analysis** (follow workflow above)

4. **Read references/report-template.md** for complete report structure

5. **Synthesize findings:**
   - Integrate fundamental and technical insights
   - Develop bull and bear cases
   - Assess risk/reward

6. **Generate recommendation:**
   - Buy/Hold/Sell rating
   - Target price with timeframe
   - Conviction level
   - Entry strategy

7. **Create formatted report** following template structure

**Report Must Include:**
- Executive summary with recommendation
- Company overview
- Investment thesis (bull and bear cases)
- Fundamental analysis section
- Technical analysis section
- Valuation analysis
- Risk assessment
- Catalysts and timeline
- Conclusion

## Stock Comparison Analysis

**When to Use:** User asks to compare two or more stocks (e.g., "compare AAPL vs MSFT")

**Steps:**
1. **Gather data for all stocks:**
   - Follow data gathering steps for each ticker
   - Ensure comparable timeframes

2. **Read references/fundamental-analysis.md** and references/financial-metrics.md

3. **Create side-by-side comparison:**
   - Business models comparison
   - Financial metrics table (all key ratios)
   - Valuation metrics table
   - Growth rates comparison
   - Profitability comparison
   - Balance sheet strength

4. **Identify relative strengths:**
   - Where each company excels
   - Quantified advantages

5. **Technical comparison:**
   - Relative strength
   - Momentum comparison
   - Which is in better technical position

6. **Generate recommendation:**
   - Which stock is more attractive and why
   - Consider both fundamental and technical factors
   - Portfolio allocation suggestion
   - Risk-adjusted return assessment

**Output Format:** Follow "Comparison Report Structure" in references/report-template.md

## Output Guidelines

**General Principles:**
- Use tables for financial data and comparisons (easy to scan)
- Bold key metrics and findings
- Include data sources and dates
- Quantify whenever possible
- Present both bull and bear perspectives
- Be clear about assumptions and uncertainties

**Formatting:**
- **Headers** for clear section separation
- **Tables** for metrics, comparisons, historical data
- **Bullet points** for lists, factors, risks
- **Bold text** for key findings, important metrics
- **Percentages** for growth rates, returns, margins
- **Currency** formatted consistently ($B for billions, $M for millions)

**Tone:**
- Objective and balanced
- Acknowledge uncertainty
- Support claims with data
- Avoid hyperbole
- Present risks clearly

## Reference Files

Load these references as needed during analysis:

**references/technical-analysis.md**
- When: Performing technical analysis or interpreting indicators
- Contains: Indicator definitions, chart patterns, support/resistance concepts, analysis workflow

**references/fundamental-analysis.md**
- When: Performing fundamental analysis or business evaluation
- Contains: Business quality assessment, financial health analysis, valuation frameworks, risk assessment, red flags

**references/financial-metrics.md**
- When: Need definitions or calculation methods for financial ratios
- Contains: All key metrics with formulas (profitability, valuation, growth, liquidity, leverage, efficiency, cash flow)

**references/report-template.md**
- When: Creating comprehensive report or comparison
- Contains: Complete report structure, formatting guidelines, section templates, comparison format

## Example Queries
## Example Queries

The following examples demonstrate how to invoke the `us-stock-analysis` skill using `invoke_skill` with various parameters for different analysis types.

### Python `invoke_skill` Examples

```bash
# Basic Stock Information for Apple
invoke_skill('us-stock-analysis', ticker='AAPL', analysis_type='basic')

# Fundamental Analysis for Nvidia
invoke_skill('us-stock-analysis', ticker='NVDA', analysis_type='fundamental')

# Technical Analysis for Tesla
invoke_skill('us-stock-analysis', ticker='TSLA', analysis_type='technical')

# Comprehensive Report for Microsoft
invoke_skill('us-stock-analysis', ticker='MSFT', analysis_type='comprehensive')

# Comparison of Apple vs. Microsoft
invoke_skill('us-stock-analysis', ticker=['AAPL', 'MSFT'], analysis_type='comparison')

# Basic Stock Information for Google (Alphabet Class A)
invoke_skill('us-stock-analysis', ticker='GOOGL', analysis_type='basic')

# Fundamental Analysis for Amazon, checking for overvaluation
invoke_skill('us-stock-analysis', ticker='AMZN', analysis_type='fundamental', query_context='Is Amazon overvalued?')
```

### Python Examples

```python
# Basic Stock Information for Apple
invoke_skill('us-stock-analysis', ticker='AAPL', analysis_type='basic')

# Fundamental Analysis for Nvidia
invoke_skill('us-stock-analysis', ticker='NVDA', analysis_type='fundamental')

# Technical Analysis for Tesla
invoke_skill('us-stock-analysis', ticker='TSLA', analysis_type='technical')

# Comprehensive Report for Microsoft
invoke_skill('us-stock-analysis', ticker='MSFT', analysis_type='comprehensive')

# Comparison of Apple vs. Microsoft
invoke_skill('us-stock-analysis', ticker=['AAPL', 'MSFT'], analysis_type='comparison')

# Basic Stock Information for Google (Alphabet Class A)
invoke_skill('us-stock-analysis', ticker='GOOGL', analysis_type='basic')

# Fundamental Analysis for Amazon, checking for overvaluation
invoke_skill('us-stock-analysis', ticker='AMZN', analysis_type='fundamental', query_context='Is Amazon overvalued?')
```

## Error Handling and Limitations

This section outlines how the skill manages errors, known limitations, and fallback strategies to ensure robust operation.

### Error Handling

-   **Invalid Ticker Symbols**: If an invalid or unrecognized ticker symbol is provided, the skill will return an error message indicating that the ticker could not be found and suggest verifying the symbol.
-   **Missing Data**: In cases where essential data (e.g., financial statements, key metrics) cannot be retrieved via web search, the skill will report the missing data and attempt to proceed with available information, clearly stating any gaps in the analysis. For critical missing data, it may indicate that a full analysis cannot be performed.
-   **Web Search Failures**: If `google_web_search` encounters issues (e.g., API errors, rate limits, no relevant results), the skill will notify the user of the search failure and may suggest retrying the operation or performing a manual search.
-   **API Limitations**: Be aware of potential rate limits or access restrictions from data sources. The skill will attempt to handle these gracefully, but persistent issues may require manual intervention or a different data acquisition strategy.

### Limitations

-   **Real-time Data**: While the skill attempts to fetch the most current data, there might be a slight delay in real-time information due to the nature of web scraping and data aggregation. It is not designed for ultra-low latency trading decisions.
-   **Data Interpretation**: The skill performs analysis based on structured frameworks. Nuance in qualitative factors (e.g., management quality, competitive landscape) is interpreted from available textual data, but human judgment may still offer deeper insights.
-   **Completeness of Information**: The comprehensiveness of the analysis is dependent on the availability and quality of information accessible via web search. Proprietary or paywalled data will not be included.
-   **Recommendation Disclaimer**: Any investment recommendations generated are based on algorithmic analysis and publicly available data. They should not be considered as financial advice without independent verification and consultation with a financial professional.

### Fallback Strategies

-   If a primary data source fails, the skill should attempt to query alternative reputable sources.
-   If a specific analysis type cannot be fully completed due to missing data, the skill will inform the user and provide the most complete analysis possible with the available information.
-   For persistent issues with `google_web_search`, manual intervention by the agent to perform web searches and provide the data to the skill might be necessary.
