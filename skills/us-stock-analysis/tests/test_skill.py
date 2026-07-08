import subprocess
import sys
import unittest
import json
from unittest.mock import patch

# Correct the import path for the script based on its actual location
sys.path.append("skills/us-stock-analysis/scripts")
import us_stock_analysis # Import the script as a module

class TestUSStockAnalysis(unittest.TestCase):
    SCRIPT_PATH = "skills/us-stock-analysis/scripts/us_stock_analysis.py"

    @patch('us_stock_analysis.google_web_search')
    def run_script(self, mock_google_web_search, args_list, mock_return_value=None, side_effect=None):
        if mock_return_value is not None:
            mock_google_web_search.return_value = mock_return_value
        if side_effect is not None:
            mock_google_web_search.side_effect = side_effect
        
        # Directly call the function from the imported module
        result = us_stock_analysis.run_analysis_from_args(args_list)
        return result

    def test_missing_analysis_type(self):
        result = self.run_script(["--ticker", "AAPL"])
        self.assertIn("error", result)
        self.assertIn("argument --analysis_type is required", result["error"])

    def test_invalid_analysis_type(self):
        result = self.run_script(["--ticker", "AAPL", "--analysis_type", "invalid"])
        self.assertIn("error", result)
        self.assertIn("argument --analysis_type: invalid choice: 'invalid'", result["error"])
        self.assertEqual(result["exit_code"], 2)

    def test_basic_analysis_aapl(self):
        mock_web_search_result = {"search_results": [{"title": "AAPL info", "snippet": "some snippet"}]}
        result = self.run_script(["--ticker", "AAPL", "--analysis_type", "basic"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["analysis_type"], "basic_info")
        self.assertIn("Basic info for AAPL", result["summary"])
        self.assertIn("returned 1 results", result["summary"])
        self.assertEqual(result["details"], mock_web_search_result)

    def test_fundamental_analysis_nvda(self):
        mock_web_search_result = {"search_results": [{"title": "NVDA financials", "snippet": "some financial data"}]}
        result = self.run_script(["--ticker", "NVDA", "--analysis_type", "fundamental"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "NVDA")
        self.assertEqual(result["analysis_type"], "fundamental_analysis")
        self.assertIn("Fundamental analysis for NVDA", result["summary"])
        self.assertIn("returned 1 results", result["summary"])
        self.assertIn("raw_search_results", result["details"])
        self.assertEqual(result["details"]["raw_search_results"], mock_web_search_result)

    def test_fundamental_analysis_amzn_with_context(self):
        mock_web_search_result = {"search_results": [{"title": "AMZN valuation", "snippet": "some valuation data"}]}
        result = self.run_script(["--ticker", "AMZN", "--analysis_type", "fundamental", "--query_context", "Is Amazon overvalued?"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "AMZN")
        self.assertEqual(result["analysis_type"], "fundamental_analysis")
        self.assertIn("Fundamental analysis for AMZN", result["summary"])
        self.assertIn("returned 1 results", result["summary"])
        self.assertEqual(result["details"]["query_context"], "Is Amazon overvalued?")
        self.assertIn("raw_search_results", result["details"])
        self.assertEqual(result["details"]["raw_search_results"], mock_web_search_result)

    def test_technical_analysis_tsla(self):
        mock_web_search_result = {"search_results": [{"title": "TSLA technicals", "snippet": "some chart data"}]}
        result = self.run_script(["--ticker", "TSLA", "--analysis_type", "technical"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "TSLA")
        self.assertEqual(result["analysis_type"], "technical_analysis")
        self.assertIn("Technical analysis for TSLA", result["summary"])
        self.assertIn("returned 1 results", result["summary"])
        self.assertIn("raw_search_results", result["details"])
        self.assertEqual(result["details"]["raw_search_results"], mock_web_search_result)

    def test_comprehensive_report_msft(self):
        mock_fundamental_web_search_result = {"search_results": [{"title": "MSFT financials", "snippet": "some financial data"}]}
        mock_technical_web_search_result = {"search_results": [{"title": "MSFT technicals", "snippet": "some chart data"}]}
        
        result = self.run_script(["--ticker", "MSFT", "--analysis_type", "comprehensive"], side_effect=[mock_fundamental_web_search_result, mock_technical_web_search_result])
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "MSFT")
        self.assertEqual(result["analysis_type"], "comprehensive_report")
        self.assertIn("Comprehensive report for MSFT", result["summary"])
        self.assertIn("Note: Some parts of the analysis are still placeholder", result["summary"]) # Because the sub-analysis summaries are placeholders
        
        # Verify details structure and content
        self.assertIn("fundamental_analysis", result["details"])
        self.assertIn("technical_analysis", result["details"])
        
        self.assertEqual(result["details"]["fundamental_analysis"]["ticker"], "MSFT")
        self.assertIn("Fundamental analysis for MSFT", result["details"]["fundamental_analysis"]["summary"])
        self.assertEqual(result["details"]["fundamental_analysis"]["details"]["raw_search_results"], mock_fundamental_web_search_result)
        
        self.assertEqual(result["details"]["technical_analysis"]["ticker"], "MSFT")
        self.assertIn("Technical analysis for MSFT", result["details"]["technical_analysis"]["summary"])
        self.assertEqual(result["details"]["technical_analysis"]["details"]["raw_search_results"], mock_technical_web_search_result)

    def test_comparison_analysis_aapl_msft(self):
        mock_aapl_web_search_result = {"search_results": [{"title": "AAPL basic info", "snippet": "AAPL data"}]}
        mock_msft_web_search_result = {"search_results": [{"title": "MSFT basic info", "snippet": "MSFT data"}]}
        
        result = self.run_script(["--ticker", "AAPL", "MSFT", "--analysis_type", "comparison"], side_effect=[mock_aapl_web_search_result, mock_msft_web_search_result])
        self.assertNotIn("error", result)
        self.assertIn("AAPL", result["tickers"])
        self.assertIn("MSFT", result["tickers"])
        self.assertEqual(result["analysis_type"], "comparison_analysis")
        self.assertIn("Comparison analysis for AAPL, MSFT", result["summary"])
        self.assertIn("Note: Some individual stock analyses are still placeholder", result["summary"])
        
        self.assertIsInstance(result["details"]["individual_stock_results"], list)
        self.assertEqual(len(result["details"]["individual_stock_results"]), 2)
        
        aapl_res = result["details"]["individual_stock_results"][0]
        self.assertEqual(aapl_res["ticker"], "AAPL")
        self.assertIn("Basic info for AAPL", aapl_res["summary"])
        self.assertEqual(aapl_res["details"], mock_aapl_web_search_result)
        
        msft_res = result["details"]["individual_stock_results"][1]
        self.assertEqual(msft_res["ticker"], "MSFT")
        self.assertIn("Basic info for MSFT", msft_res["summary"])
        self.assertEqual(msft_res["details"], mock_msft_web_search_result)

    def test_comparison_analysis_single_ticker_error(self):
        result = self.run_script(["--ticker", "AAPL", "--analysis_type", "comparison"])
        self.assertIn("error", result)
        self.assertIn("'comparison' analysis type requires at least two tickers.", result["error"])

    def test_single_ticker_for_multi_ticker_analysis_error(self):
        result = self.run_script(["--ticker", "AAPL", "MSFT", "--analysis_type", "basic"])
        self.assertIn("error", result)
        self.assertIn("Only one ticker allowed for 'basic'", result["error"])

    def test_basic_analysis_empty_web_search_results(self):
        mock_web_search_result = {"search_results": []} # Empty results
        result = self.run_script(["--ticker", "GOOGL", "--analysis_type", "basic"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "GOOGL")
        self.assertEqual(result["analysis_type"], "basic_info")
        self.assertIn("No significant results from web search", result["summary"])
        self.assertEqual(result["details"], mock_web_search_result)

    def test_fundamental_analysis_empty_web_search_results(self):
        mock_web_search_result = {"search_results": []} # Empty results
        result = self.run_script(["--ticker", "IBM", "--analysis_type", "fundamental"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "IBM")
        self.assertEqual(result["analysis_type"], "fundamental_analysis")
        self.assertIn("No significant results from web search", result["summary"])
        self.assertIn("raw_search_results", result["details"])
        self.assertEqual(result["details"]["raw_search_results"], mock_web_search_result)

    def test_technical_analysis_empty_web_search_results(self):
        mock_web_search_result = {"search_results": []} # Empty results
        result = self.run_script(["--ticker", "SPY", "--analysis_type", "technical"], mock_return_value=mock_web_search_result)
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "SPY")
        self.assertEqual(result["analysis_type"], "technical_analysis")
        self.assertIn("No significant results from web search", result["summary"])
        self.assertIn("raw_search_results", result["details"])
        self.assertEqual(result["details"]["raw_search_results"], mock_web_search_result)

    def test_comprehensive_report_empty_web_search_results(self):
        mock_empty_web_search_result = {"search_results": []}
        result = self.run_script(["--ticker", "MSFT", "--analysis_type", "comprehensive"], side_effect=[mock_empty_web_search_result, mock_empty_web_search_result])
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "MSFT")
        self.assertEqual(result["analysis_type"], "comprehensive_report")
        self.assertIn("Note: Some parts of the analysis are still placeholder", result["summary"])
        self.assertIn("No significant results from web search", result["details"]["fundamental_analysis"]["summary"])
        self.assertIn("No significant results from web search", result["details"]["technical_analysis"]["summary"])

    def test_comparison_analysis_empty_web_search_results(self):
        mock_empty_web_search_result = {"search_results": []}
        result = self.run_script(["--ticker", "AAPL", "MSFT", "--analysis_type", "comparison"], side_effect=[mock_empty_web_search_result, mock_empty_web_search_result])
        self.assertNotIn("error", result)
        self.assertIn("AAPL", result["tickers"])
        self.assertIn("MSFT", result["tickers"])
        self.assertEqual(result["analysis_type"], "comparison_analysis")
        self.assertIn("Note: Some individual stock analyses are still placeholder", result["summary"])
        self.assertIn("No significant results from web search", result["details"]["individual_stock_results"][0]["summary"])
        self.assertIn("No significant results from web search", result["details"]["individual_stock_results"][1]["summary"])

    def test_basic_analysis_web_search_exception(self):
        result = self.run_script(["--ticker", "GOOGL", "--analysis_type", "basic"], side_effect=Exception("Web search failed"))
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "GOOGL")
        self.assertEqual(result["analysis_type"], "basic_info")
        self.assertIn("Error performing basic info analysis", result["summary"])
        self.assertIn("Web search failed", result["summary"])
        self.assertIn("error", result["details"])
        self.assertIn("Web search failed", result["details"]["error"])

    def test_fundamental_analysis_web_search_exception(self):
        result = self.run_script(["--ticker", "IBM", "--analysis_type", "fundamental"], side_effect=Exception("Web search failed for financials"))
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "IBM")
        self.assertEqual(result["analysis_type"], "fundamental_analysis")
        self.assertIn("Error performing fundamental analysis", result["summary"])
        self.assertIn("Web search failed for financials", result["summary"])
        self.assertIn("error", result["details"]["raw_search_results"])
        self.assertIn("Web search failed for financials", result["details"]["raw_search_results"]["error"])

    def test_technical_analysis_web_search_exception(self):
        result = self.run_script(["--ticker", "SPY", "--analysis_type", "technical"], side_effect=Exception("Web search failed for technical data"))
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "SPY")
        self.assertEqual(result["analysis_type"], "technical_analysis")
        self.assertIn("Error performing technical analysis", result["summary"])
        self.assertIn("Web search failed for technical data", result["summary"])
        self.assertIn("error", result["details"]["raw_search_results"])
        self.assertIn("Web search failed for technical data", result["details"]["raw_search_results"]["error"])

    def test_comprehensive_report_web_search_exception(self):
        result = self.run_script(["--ticker", "MSFT", "--analysis_type", "comprehensive"], side_effect=[Exception("Fundamental search failed"), Exception("Technical search failed")])
        self.assertNotIn("error", result)
        self.assertEqual(result["ticker"], "MSFT")
        self.assertEqual(result["analysis_type"], "comprehensive_report")
        self.assertIn("Comprehensive report for MSFT", result["summary"])
        self.assertIn("Note: Some parts of the analysis are still placeholder", result["summary"]) # Due to incomplete implementation and exceptions
        self.assertIn("Error performing fundamental analysis", result["details"]["fundamental_analysis"]["summary"])
        self.assertIn("Fundamental search failed", result["details"]["fundamental_analysis"]["summary"])
        self.assertIn("Error performing technical analysis", result["details"]["technical_analysis"]["summary"])
        self.assertIn("Technical search failed", result["details"]["technical_analysis"]["summary"])

    def test_comparison_analysis_web_search_exception(self):
        result = self.run_script(["--ticker", "AAPL", "MSFT", "--analysis_type", "comparison"], side_effect=[Exception("AAPL search failed"), Exception("MSFT search failed")])
        self.assertNotIn("error", result)
        self.assertIn("AAPL", result["tickers"])
        self.assertIn("MSFT", result["tickers"])
        self.assertEqual(result["analysis_type"], "comparison_analysis")
        self.assertIn("Note: Some individual stock analyses are still placeholder", result["summary"])
        self.assertIn("Error performing basic info analysis for AAPL", result["details"]["individual_stock_results"][0]["summary"])
        self.assertIn("AAPL search failed", result["details"]["individual_stock_results"][0]["summary"])
        self.assertIn("Error performing basic info analysis for MSFT", result["details"]["individual_stock_results"][1]["summary"])
        self.assertIn("MSFT search failed", result["details"]["individual_stock_results"][1]["summary"])

if __name__ == "__main__":
    unittest.main()
