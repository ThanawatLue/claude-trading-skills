import json
import pytest
import requests
from unittest.mock import patch, MagicMock
from fetch_earnings_fmp import FMPEarningsCalendar

@pytest.fixture
def mock_fmp_client():
    """Returns an FMP client instance with a dummy API key."""
    return FMPEarningsCalendar(api_key="test_api_key")

class TestFMPEarningsCalendarIntegration:

    # Test for fetch_earnings_calendar
    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_success(self, mock_get, mock_fmp_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "AAPL", "date": "2025-11-05", "time": "AMC"},
            {"symbol": "MSFT", "date": "2025-11-04", "time": "BMO"}
        ]
        mock_get.return_value = mock_response

        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert len(earnings) == 2
        assert earnings[0]["symbol"] == "AAPL"
        mock_get.assert_called_once()
        assert "earnings-calendar" in mock_get.call_args[0][0]

    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_401_error(self, mock_get, mock_fmp_client, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert earnings is None
        outerr = capsys.readouterr()
        assert "ERROR: Invalid API key" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_429_error(self, mock_get, mock_fmp_client, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert earnings is None
        outerr = capsys.readouterr()
        assert "ERROR: Rate limit exceeded" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_empty_response(self, mock_get, mock_fmp_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert len(earnings) == 0

    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_api_error_message(self, mock_get, mock_fmp_client, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Error Message": "Some API error"}
        mock_get.return_value = mock_response

        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert earnings is None
        outerr = capsys.readouterr()
        assert "❌ API Error: Some API error" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_timeout(self, mock_get, mock_fmp_client, capsys):
        mock_get.side_effect = requests.exceptions.Timeout
        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert earnings is None
        outerr = capsys.readouterr()
        assert "ERROR: Request timeout" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_earnings_calendar_connection_error(self, mock_get, mock_fmp_client, capsys):
        mock_get.side_effect = requests.exceptions.ConnectionError
        earnings = mock_fmp_client.fetch_earnings_calendar("2025-11-03", "2025-11-09")
        assert earnings is None
        outerr = capsys.readouterr()
        assert "ERROR: Connection error" in outerr.err

    # Tests for fetch_company_profiles (batch API)
    @patch('requests.Session.get')
    def test_fetch_company_profiles_success(self, mock_get, mock_fmp_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "AAPL", "companyName": "Apple Inc.", "marketCap": 3e12},
            {"symbol": "MSFT", "companyName": "Microsoft Corp", "marketCap": 2.5e12}
        ]
        mock_get.return_value = mock_response

        profiles = mock_fmp_client.fetch_company_profiles(["AAPL", "MSFT"])
        assert len(profiles) == 2
        assert profiles["AAPL"]["companyName"] == "Apple Inc."
        mock_get.assert_called_once()
        assert "/profile/AAPL,MSFT" in mock_get.call_args[0][0]

    @patch('requests.Session.get')
    def test_fetch_company_profiles_401_error(self, mock_get, mock_fmp_client, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        profiles = mock_fmp_client.fetch_company_profiles(["AAPL"])
        assert profiles == {}
        outerr = capsys.readouterr()
        assert "ERROR: Invalid API key during profile fetch" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_company_profiles_429_error(self, mock_get, mock_fmp_client, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        profiles = mock_fmp_client.fetch_company_profiles(["AAPL"])
        assert profiles == {}
        outerr = capsys.readouterr()
        assert "ERROR: Rate limit exceeded during profile fetch" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_company_profiles_empty_response(self, mock_get, mock_fmp_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        profiles = mock_fmp_client.fetch_company_profiles(["AAPL"])
        assert profiles == {}

    @patch('requests.Session.get')
    def test_fetch_company_profiles_unexpected_response_format(self, mock_get, mock_fmp_client, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not_a_list": "data"} # Expected a list of profiles
        mock_get.return_value = mock_response

        profiles = mock_fmp_client.fetch_company_profiles(["AAPL"])
        assert profiles == {}
        outerr = capsys.readouterr()
        assert "Warning: Unexpected response format for profiles" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_company_profiles_timeout(self, mock_get, mock_fmp_client, capsys):
        mock_get.side_effect = requests.exceptions.Timeout
        profiles = mock_fmp_client.fetch_company_profiles(["AAPL"])
        assert profiles == {}
        outerr = capsys.readouterr()
        assert "ERROR: Request timeout during profile fetch" in outerr.err

    @patch('requests.Session.get')
    def test_fetch_company_profiles_connection_error(self, mock_get, mock_fmp_client, capsys):
        mock_get.side_effect = requests.exceptions.ConnectionError
        profiles = mock_fmp_client.fetch_company_profiles(["AAPL"])
        assert profiles == {}
        outerr = capsys.readouterr()
        assert "ERROR: Connection error during profile fetch" in outerr.err

    def test_fetch_company_profiles_no_symbols(self, mock_fmp_client):
        profiles = mock_fmp_client.fetch_company_profiles([])
        assert profiles == {}
