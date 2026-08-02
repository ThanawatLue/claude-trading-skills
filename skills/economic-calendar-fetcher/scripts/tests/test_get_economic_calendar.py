import argparse
import io
import json
import os
import sys
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from get_economic_calendar import (
    fetch_economic_calendar,
    format_event_output,
    get_api_key,
    main,
    validate_date_range,
)


class TestGetApiKey(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_not_set(self):
        """Test that get_api_key returns None and prints a warning when FMP_API_KEY is not set."""
        with patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            self.assertIsNone(get_api_key())
            self.assertIn("Warning: FMP_API_KEY environment variable not set", mock_stderr.getvalue())

    @patch.dict(os.environ, {"FMP_API_KEY": "test_key"}, clear=True)
    def test_get_api_key_set(self):
        """Test that get_api_key returns the API key when set."""
        self.assertEqual(get_api_key(), "test_key")


class TestFetchEconomicCalendar(unittest.TestCase):
    API_KEY = "test_api_key"
    BASE_URL = "https://financialmodelingprep.com/api/v3/economic_calendar"

    @patch("urllib.request.urlopen")
    @patch("urllib.request.Request")
    def test_successful_fetch_with_data(self, mock_request, mock_urlopen):
        """Test successful fetching of economic calendar data."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps([{"event": "GDP", "date": "2024-01-01"}]).encode(
            "utf-8"
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        data = fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["event"], "GDP")
        mock_request.assert_called_once_with(
            f"{self.BASE_URL}?from=2024-01-01&to=2024-01-01&apikey={self.API_KEY}"
        )

    @patch("urllib.request.urlopen")
    @patch("urllib.request.Request")
    def test_successful_fetch_no_data(self, mock_request, mock_urlopen):
        """Test successful fetch when API returns an empty list."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps([]).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        data = fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)

        self.assertEqual(len(data), 0)
        mock_request.assert_called_once_with(
            f"{self.BASE_URL}?from=2024-01-01&to=2024-01-01&apikey={self.API_KEY}"
        )

    @patch("urllib.request.urlopen")
    def test_http_error_401(self, mock_urlopen):
        """Test handling of 401 Unauthorized error."""
        http_error = urllib.error.HTTPError(
            url="some_url", code=401, msg="Unauthorized", hdrs={}, fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = http_error

        with self.assertRaisesRegex(urllib.error.HTTPError, "FMP API error: Unauthorized"):
            fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)

    @patch("urllib.request.urlopen")
    def test_http_error_429(self, mock_urlopen):
        """Test handling of 429 Too Many Requests error."""
        http_error = urllib.error.HTTPError(
            url="some_url", code=429, msg="Too Many Requests", hdrs={}, fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = http_error

        with self.assertRaisesRegex(urllib.error.HTTPError, "FMP API error: Too Many Requests"):
            fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)

    @patch("urllib.request.urlopen")
    def test_http_error_500(self, mock_urlopen):
        """Test handling of 500 Internal Server Error."""
        http_error = urllib.error.HTTPError(
            url="some_url", code=500, msg="Internal Server Error", hdrs={}, fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = http_error

        with self.assertRaisesRegex(urllib.error.HTTPError, "FMP API error: Internal Server Error"):
            fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)

    @patch("urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        """Test handling of network-related URLError."""
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

        with self.assertRaisesRegex(ValueError, "Network error: Network unreachable"):
            fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)

    @patch("urllib.request.urlopen")
    @patch("urllib.request.Request")
    def test_404_empty_response_body_v3_api(self, mock_request, mock_urlopen):
        """
        Test handling of 404 with empty response body in v3 API.
        The v3 API typically returns 200 with an empty list for no events,
        but this tests the specific case if a 404 with empty body occurs.
        """
        http_error = urllib.error.HTTPError(
            url="some_url", code=404, msg="Not Found", hdrs={}, fp=io.BytesIO(b"[]")
        )
        mock_urlopen.side_effect = http_error

        # The current code specifically checks for `error_body.strip() == "[]"`
        # in the 404 handler. So it should return an empty list.
        events = fetch_economic_calendar("2024-01-01", "2024-01-01", self.API_KEY)
        self.assertEqual(events, [])


class TestValidateDateRange(unittest.TestCase):
    def test_valid_date_range(self):
        """Test valid date range within 90 days."""
        validate_date_range("2024-01-01", "2024-03-30")  # 89 days, valid
        self.assertIsNone(None) # No exception means success

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with self.assertRaisesRegex(ValueError, "Invalid date format"):
            validate_date_range("01-01-2024", "2024-01-02")

    def test_start_date_after_end_date(self):
        """Test start date after end date."""
        with self.assertRaisesRegex(ValueError, "Start date 2024-01-02 is after end date 2024-01-01"):
            validate_date_range("2024-01-02", "2024-01-01")

    def test_date_range_exceeds_90_days(self):
        """Test date range exceeding 90 days."""
        with self.assertRaisesRegex(ValueError, "Date range \(91 days\) exceeds maximum of 90 days"):
            validate_date_range("2024-01-01", "2024-04-01")

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_end_date_in_past_warning(self, mock_stderr):
        """Test warning for end date in the past."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        validate_date_range(two_days_ago, yesterday)
        self.assertIn("Warning: End date", mock_stderr.getvalue())
        self.assertIn("is in the past", mock_stderr.getvalue())


class TestFormatEventOutput(unittest.TestCase):
    def setUp(self):
        self.events = [
            {
                "date": "2024-01-01",
                "country": "US",
                "event": "Holiday",
                "currency": "USD",
                "impact": "Low",
                "previous": None,
                "estimate": None,
                "actual": None,
                "change": None,
                "changePercentage": None,
            },
            {
                "date": "2024-01-02",
                "country": "EU",
                "event": "GDP Growth Rate",
                "currency": "EUR",
                "impact": "High",
                "previous": "1.0%",
                "estimate": "1.2%",
                "actual": "1.1%",
                "change": "0.1",
                "changePercentage": "10.0",
            },
        ]

    def test_format_json_output(self):
        """Test JSON output format."""
        output = format_event_output(self.events, "json")
        parsed_output = json.loads(output)
        self.assertEqual(parsed_output, self.events)

    def test_format_text_output(self):
        """Test text output format."""
        output = format_event_output(self.events, "text")
        self.assertIn("Economic Calendar Events (Total: 2)", output)
        self.assertIn("Date: 2024-01-01", output)
        self.assertIn("Country: US", output)
        self.assertIn("Previous: 1.0%", output)
        self.assertIn("Change %: 10.0%", output)
        self.assertNotIn("Previous: None", output) # Ensure None values are not printed

    def test_unknown_output_format(self):
        """Test handling of unknown output format."""
        with self.assertRaisesRegex(ValueError, "Unknown output format: xml"):
            format_event_output(self.events, "xml")


class TestMain(unittest.TestCase):
    @patch("get_economic_calendar.get_api_key", return_value=None)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.exit")
    def test_main_no_api_key(self, mock_exit, mock_stderr, mock_get_api_key):
        """Test main function exits with error if no API key is available."""
        mock_exit.side_effect = SystemExit
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                from_date="2024-01-01", to_date="2024-01-01", api_key=None, format="json", output=None
            )
            with self.assertRaises(SystemExit):
                main()
            mock_exit.assert_called_once_with(1)
            self.assertIn(
                "Error: FMP API key is required. Set FMP_API_KEY environment variable or use --api-key",
                mock_stderr.getvalue(),
            )

    @patch("get_economic_calendar.validate_date_range", side_effect=ValueError("Invalid range"))
    @patch("get_economic_calendar.get_api_key", return_value="test_key")
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.exit")
    def test_main_invalid_date_range(self, mock_exit, mock_stderr, mock_get_api_key, mock_validate_date_range):
        """Test main function exits with error for invalid date range."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                from_date="2024-01-02", to_date="2024-01-01", api_key="test_key", format="json", output=None
            )
            main()
            mock_exit.assert_called_once_with(1)
            self.assertIn("Error: Invalid range", mock_stderr.getvalue())

    @patch("get_economic_calendar.fetch_economic_calendar", return_value=[])
    @patch("get_economic_calendar.get_api_key", return_value="test_key")
    @patch("get_economic_calendar.validate_date_range")
    @patch("get_economic_calendar.format_event_output", return_value="[]")
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.exit")
    def test_main_successful_execution_default_args(
        self,
        mock_exit,
        mock_stderr,
        mock_stdout,
        mock_format_event_output,
        mock_validate_date_range,
        mock_get_api_key,
        mock_fetch_economic_calendar,
    ):
        """Test main function executes successfully with default arguments."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            today = datetime.now().date()
            default_from = today.strftime("%Y-%m-%d")
            default_to = (today + timedelta(days=7)).strftime("%Y-%m-%d")

            mock_parse_args.return_value = argparse.Namespace(
                from_date=default_from,
                to_date=default_to,
                api_key=None,
                format="json",
                output=None,
            )
            main()
            mock_fetch_economic_calendar.assert_called_once_with(
                default_from, default_to, "test_key"
            )
            mock_format_event_output.assert_called_once_with([], "json")
            mock_exit.assert_called_once_with(0)
            self.assertIn(f"Fetching economic calendar from {default_from}", mock_stderr.getvalue())
            self.assertIn("Retrieved 0 events", mock_stderr.getvalue())
            self.assertEqual(sys.stdout.getvalue(), "[]\n")

    @patch("get_economic_calendar.fetch_economic_calendar", return_value=[{"event": "Test", "date": "2024-01-01"}])
    @patch("get_economic_calendar.get_api_key", return_value="test_key")
    @patch("get_economic_calendar.validate_date_range")
    @patch("get_economic_calendar.format_event_output", return_value='[{"event": "Test", "date": "2024-01-01"}]')
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.exit")
    def test_main_successful_execution_to_file(
        self,
        mock_exit,
        mock_stderr,
        mock_stdout,
        mock_open,
        mock_format_event_output,
        mock_validate_date_range,
        mock_get_api_key,
        mock_fetch_economic_calendar,
    ):
        """Test main function executes successfully and writes to a file."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                from_date="2024-01-01", to_date="2024-01-01", api_key="test_key", format="json", output="output.json"
            )
            main()
            mock_fetch_economic_calendar.assert_called_once_with(
                "2024-01-01", "2024-01-01", "test_key"
            )
            mock_open.assert_called_once_with("output.json", "w", encoding="utf-8")
            mock_open().write.assert_called_once_with(
                '[{"event": "Test", "date": "2024-01-01"}]'
            )
            mock_exit.assert_called_once_with(0)
            self.assertIn("Output written to output.json", mock_stderr.getvalue())
            self.assertEqual(sys.stdout.getvalue(), "")  # No output to stdout when writing to file

    @patch("get_economic_calendar.fetch_economic_calendar", return_value=[])
    @patch("get_economic_calendar.get_api_key", return_value="test_key")
    @patch("get_economic_calendar.validate_date_range")
    @patch("get_economic_calendar.format_event_output", return_value="Formatted text output")
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.exit")
    def test_main_successful_execution_text_format(
        self,
        mock_exit,
        mock_stderr,
        mock_stdout,
        mock_format_event_output,
        mock_validate_date_range,
        mock_get_api_key,
        mock_fetch_economic_calendar,
    ):
        """Test main function executes successfully with text output format."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                from_date="2024-01-01", to_date="2024-01-01", api_key="test_key", format="text", output=None
            )
            main()
            mock_fetch_economic_calendar.assert_called_once_with(
                "2024-01-01", "2024-01-01", "test_key"
            )
            mock_format_event_output.assert_called_once_with([], "text")
            mock_exit.assert_called_once_with(0)
            self.assertEqual(sys.stdout.getvalue(), "Formatted text output\n")


if __name__ == "__main__":
    unittest.main()
