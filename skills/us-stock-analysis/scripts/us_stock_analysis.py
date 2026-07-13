#!/usr/bin/env python3
"""
US Stock Analysis skill script.
This script provides various types of analysis for US stocks based on user queries.
It is designed to be invoked by the agent with specific parameters.
"""

import argparse
import json
import sys
import io # Added for capturing stderr

# Assume google_web_search is available in the execution environment as a tool.
# For local development and testing, we can define a mock function.
# In a real skill execution, this would be the actual tool provided by the agent.
def google_web_search(query):
    """
    Placeholder for the actual google_web_search tool.
    Simulates fetching data via web search.
    """
    print(f"DEBUG: Simulating google_web_search for query: {query}") # Added for debugging
    # In a real scenario, this would block and perform an actual web search.
    # For now, it returns a placeholder structure that can be mocked in tests.
    return {
        "search_results": [
            {"title": f"Mock result for {query}", "snippet": f"This is a mock snippet for {query}", "link": f"http://mock.com/{query.replace(' ', '_')}"}
        ]
    }

def basic_info_analysis(ticker):
    """Performs basic stock information analysis."""
    print(f"Performing basic info analysis for {ticker}...")
    # Example: fetch current price, volume, market cap, key ratios
    search_query = f"{ticker} stock basic info"
    data = {}
    summary_message = ""
    try:
        data = google_web_search(search_query)
        if data and data.get('search_results'):
            summary_message = f"Basic info for {ticker}: (Placeholder - actual data would be here. Web search for '{search_query}' returned {len(data['search_results'])} results.)"
        else:
            summary_message = f"Basic info for {ticker}: (Placeholder - actual data would be here). No significant results from web search for '{search_query}'."
    except Exception as e:
        summary_message = f"Error performing basic info analysis for {ticker}: Failed to retrieve data via web search. Error: {str(e)}"
        print(f"ERROR: {summary_message}", file=sys.stderr)
        data = {"error": str(e)}
        
    # Process data and return a summary
    return {
        "ticker": ticker,
        "analysis_type": "basic_info",
        "summary": summary_message,
        "details": data
    }

def fundamental_analysis(ticker, query_context=None):
    """Performs fundamental analysis for a given ticker."""
    print(f"Performing fundamental analysis for {ticker} (Context: {query_context})...")
    
    search_query = f"{ticker} financial statements, key metrics, analyst ratings"
    data = {}
    summary_message = ""
    try:
        data = google_web_search(search_query)
        if data and data.get('search_results'):
            summary_message = f"Fundamental analysis for {ticker}: (Placeholder - actual data and analysis would be here). Web search for '{search_query}' returned {len(data['search_results'])} results."
        else:
            summary_message = f"Fundamental analysis for {ticker}: (Placeholder - actual data would be here). No significant results from web search for '{search_query}'."
    except Exception as e:
        summary_message = f"Error performing fundamental analysis for {ticker}: Failed to retrieve data via web search. Error: {str(e)}"
        print(f"ERROR: {summary_message}", file=sys.stderr)
        data = {"error": str(e)}

    # Process data using financial-metrics.md and fundamental-analysis.md
    return {
        "ticker": ticker,
        "analysis_type": "fundamental_analysis",
        "summary": summary_message,
        "details": {"query_context": query_context, "raw_search_results": data}
    }

def technical_analysis(ticker):
    """Performs technical analysis for a given ticker."""
    print(f"Performing technical analysis for {ticker}...")
    
    search_query = f"{ticker} stock technical analysis chart data indicators"
    data = {}
    summary_message = ""
    try:
        data = google_web_search(search_query)
        if data and data.get('search_results'):
            summary_message = f"Technical analysis for {ticker}: (Placeholder - actual data and analysis would be here). Web search for '{search_query}' returned {len(data['search_results'])} results.)"
        else:
            summary_message = f"Technical analysis for {ticker}: (Placeholder - actual data would be here). No significant results from web search for '{search_query}'."
    except Exception as e:
        summary_message = f"Error performing technical analysis for {ticker}: Failed to retrieve data via web search. Error: {str(e)}"
        print(f"ERROR: {summary_message}", file=sys.stderr)
        data = {"error": str(e)}

    # Process data using technical-analysis.md
    return {
        "ticker": ticker,
        "analysis_type": "technical_analysis",
        "summary": summary_message,
        "details": {"raw_search_results": data}
    }

def comprehensive_report(ticker):
    """Generates a comprehensive investment report for a given ticker."""
    print(f"Generating comprehensive report for {ticker}...")
    
    fundamental_res = fundamental_analysis(ticker)
    technical_res = technical_analysis(ticker)

    summary_message = f"Comprehensive report for {ticker}: (Placeholder - combined analysis would be here). "
    details = {
        "fundamental_analysis": fundamental_res,
        "technical_analysis": technical_res
    }

    if "Placeholder" in fundamental_res["summary"] or "Placeholder" in technical_res["summary"]:
        summary_message += "Note: Some parts of the analysis are still placeholder due to incomplete implementation."

    # Synthesize using report-template.md
    return {
        "ticker": ticker,
        "analysis_type": "comprehensive_report",
        "summary": summary_message,
        "details": details
    }

def comparison_analysis(tickers):
    """Compares multiple stock tickers."""
    print(f"Performing comparison analysis for {', '.join(tickers)}...")
    
    all_ticker_results = []
    for ticker in tickers:
        basic_res = basic_info_analysis(ticker)
        all_ticker_results.append(basic_res)

    summary_message = f"Comparison analysis for {', '.join(tickers)}: (Placeholder - comparison would be here). "
    
    # Check if any of the sub-analyses returned placeholder summaries
    if any("Placeholder" in res["summary"] for res in all_ticker_results):
        summary_message += "Note: Some individual stock analyses are still placeholder due to incomplete implementation."

    # Process results into a comparison table/summary
    return {
        "tickers": tickers,
        "analysis_type": "comparison_analysis",
        "summary": summary_message,
        "details": {"individual_stock_results": all_ticker_results}
    }

def run_analysis_from_args(args_list):
    parser = argparse.ArgumentParser(description="US Stock Analysis skill script.")
    parser.add_argument("--ticker", nargs='+', help="One or more stock ticker symbols (e.g., AAPL, MSFT)")
    parser.add_argument("--analysis_type", type=str, required=True,
                        choices=["basic", "fundamental", "technical", "comprehensive", "comparison"],
                        help="Type of analysis to perform")
    parser.add_argument("--query_context", type=str,
                        help="Additional context for the query, e.g., 'Is Amazon overvalued?'")

    # Capture stderr to get argparse error messages
    old_stderr = sys.stderr
    sys.stderr = new_stderr = io.StringIO()
    args = None
    try:
        args = parser.parse_args(args_list)
    except SystemExit as e:
        sys.stderr = old_stderr # Restore stderr before returning
        return {"error": new_stderr.getvalue().strip(), "exit_code": e.code}
    finally:
        sys.stderr = old_stderr # Ensure stderr is restored even if other errors occur

    if not args.ticker and args.analysis_type != "comparison":
        print("Error: --ticker is required for analysis types 'basic', 'fundamental', 'technical', and 'comprehensive'.", file=sys.stderr)
        return {"error": "Ticker required for this analysis type."}
    if len(args.ticker) > 1 and args.analysis_type != "comparison":
        print("Error: Only one ticker allowed for 'basic', 'fundamental', 'technical', 'comprehensive' analysis types. Use 'comparison' for multiple tickers.", file=sys.stderr)
        return {"error": "Only one ticker allowed for this analysis type."}
    if len(args.ticker) < 2 and args.analysis_type == "comparison":
        print("Error: 'comparison' analysis type requires at least two tickers.", file=sys.stderr)
        return {"error": "'comparison' analysis type requires at least two tickers."}

    result = {}
    if args.analysis_type == "basic":
        result = basic_info_analysis(args.ticker[0])
    elif args.analysis_type == "fundamental":
        result = fundamental_analysis(args.ticker[0], args.query_context)
    elif args.analysis_type == "technical":
        result = technical_analysis(args.ticker[0])
    elif args.analysis_type == "comprehensive":
        result = comprehensive_report(args.ticker[0])
    elif args.analysis_type == "comparison":
        result = comparison_analysis(args.ticker)
    
    return result

def main():
    result = run_analysis_from_args(sys.argv[1:])
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())