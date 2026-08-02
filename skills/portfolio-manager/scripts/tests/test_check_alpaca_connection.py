import os
import unittest
from unittest.mock import MagicMock, patch

import check_alpaca_connection


class TestCheckAlpacaConnection(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "ALPACA_API_KEY": "test_key_id",
                "ALPACA_SECRET_KEY": "test_secret_key",
                "ALPACA_PAPER": "true",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_load_credentials(self):
        api_key, secret_key, paper = check_alpaca_connection.load_credentials()
        self.assertEqual(api_key, "test_key_id")
        self.assertEqual(secret_key, "test_secret_key")
        self.assertTrue(paper)

    def test_get_base_url(self):
        self.assertEqual(
            check_alpaca_connection.get_base_url(paper=True), "https://paper-api.alpaca.markets"
        )
        self.assertEqual(
            check_alpaca_connection.get_base_url(paper=False), "https://api.alpaca.markets"
        )

    def test_load_credentials_missing_env_vars(self):
        del os.environ["ALPACA_API_KEY"]
        del os.environ["ALPACA_SECRET_KEY"]
        with self.assertRaises(check_alpaca_connection.AlpacaCredentialError):
            check_alpaca_connection.load_credentials()

    @patch("requests.get")
    def test_test_account_info_forbidden(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        res = check_alpaca_connection.test_account_info(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertFalse(res)

    @patch("requests.get", side_effect=requests.exceptions.RequestException("Network error"))
    def test_test_account_info_network_error(self, mock_get):
        res = check_alpaca_connection.test_account_info(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertFalse(res)

    @patch("requests.get")
    def test_test_account_info_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ACTIVE",
            "account_number": "123456789",
            "equity": "100000",
            "cash": "50000",
            "buying_power": "200000",
            "portfolio_value": "100000",
        }
        mock_get.return_value = mock_response

        res = check_alpaca_connection.test_account_info(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertTrue(res)

    @patch("requests.get")
    def test_test_account_info_unauthorized(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        res = check_alpaca_connection.test_account_info(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertFalse(res)

    @patch("requests.get")
    def test_test_positions_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        res = check_alpaca_connection.test_positions(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertTrue(res)

    @patch("requests.get")
    def test_test_positions_filled(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "symbol": "AAPL",
                "qty": "10",
                "avg_entry_price": "150",
                "current_price": "155",
                "market_value": "1550",
                "unrealized_pl": "50",
                "unrealized_plpc": "0.033",
            }
        ]
        mock_get.return_value = mock_response

        res = check_alpaca_connection.test_positions(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertTrue(res)

    @patch("requests.get")
    def test_test_positions_forbidden(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_get.return_value = mock_response

        res = check_alpaca_connection.test_positions(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertFalse(res)

    @patch("requests.get", side_effect=requests.exceptions.RequestException("Network error"))
    def test_test_positions_network_error(self, mock_get):
        res = check_alpaca_connection.test_positions(
            "key", "secret", "https://paper-api.alpaca.markets"
        )
        self.assertFalse(res)

    @patch("requests.get")
    def test_test_market_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"quote": {"bp": 150.0, "ap": 150.1}}
        mock_get.return_value = mock_response

        # This should execute and print output without throwing errors
        check_alpaca_connection.test_market_data("key", "secret")

    @patch("requests.get", side_effect=requests.exceptions.RequestException("Network error"))
    def test_test_market_data_network_error(self, mock_get):
        # This should execute and print output without throwing errors,
        # but cover the exception path
        check_alpaca_connection.test_market_data("key", "secret")


if __name__ == "__main__":
    unittest.main()
