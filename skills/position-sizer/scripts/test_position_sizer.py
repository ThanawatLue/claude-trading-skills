import json
import os
import shutil

# Assume SizingParameters, get_latest_posture, calculate_position are imported or defined here
# For the purpose of this test file, we'll import them relative to the current directory
import sys
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from position_sizer import (
    SizingParameters,
    calculate_position,
    get_latest_posture,
)


class TestPositionSizer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test reports
        self.test_reports_dir = Path("test_reports")
        self.test_reports_dir.mkdir(exist_ok=True, parents=True)

    def tearDown(self):
        # Clean up the temporary directory
        time.sleep(0.05)
        if self.test_reports_dir.exists():
            shutil.rmtree(self.test_reports_dir)

    def _create_posture_file(self, filename: str, content: dict):
        filepath = self.test_reports_dir / filename
        with open(filepath, "w") as f:
            json.dump(content, f)
        return filepath

    @patch("glob.glob")
    def test_get_latest_posture_no_files(self, mock_glob):
        mock_glob.return_value = []
        posture = get_latest_posture("US", reports_dir=str(self.test_reports_dir))
        self.assertIsNone(posture)

    def test_get_latest_posture_malformed_json(self):
        self._create_posture_file("exposure_posture_2024-01-01_120000.json", {"invalid": "json"})
        # Intentionally write malformed content
        with open(self.test_reports_dir / "exposure_posture_2024-01-02_120000.json", "w") as f:
            f.write("this is not json")

        posture = get_latest_posture("US", reports_dir=str(self.test_reports_dir))
        # It should skip the malformed file and return the valid one
        self.assertIsNotNone(posture)
        self.assertEqual(posture.get("invalid"), "json")

    def test_get_latest_posture_correct_latest_selection(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        posture_yesterday = {
            "metadata": {"market": "US", "generated_at": yesterday.isoformat()},
            "recommendation": "REDUCE_ONLY",
        }
        posture_today = {
            "metadata": {"market": "US", "generated_at": today.isoformat()},
            "recommendation": "NEW_ENTRY_ALLOWED",
        }
        posture_tomorrow = {
            "metadata": {"market": "US", "generated_at": tomorrow.isoformat()},
            "recommendation": "CASH_PRIORITY",
        }

        self._create_posture_file(
            f"exposure_posture_{yesterday.strftime('%Y-%m-%d_%H%M%S')}.json", posture_yesterday
        )
        self._create_posture_file(
            f"exposure_posture_{today.strftime('%Y-%m-%d_%H%M%S')}.json", posture_today
        )
        self._create_posture_file(
            f"exposure_posture_{tomorrow.strftime('%Y-%m-%d_%H%M%S')}.json", posture_tomorrow
        )

        posture = get_latest_posture("US", reports_dir=str(self.test_reports_dir))
        self.assertIsNotNone(posture)
        self.assertEqual(posture["recommendation"], "CASH_PRIORITY")
        self.assertEqual(posture["metadata"]["generated_at"], tomorrow.isoformat())

    def test_get_latest_posture_market_filtering(self):
        today = datetime.now()
        us_posture = {
            "metadata": {"market": "US", "generated_at": today.isoformat()},
            "recommendation": "NEW_ENTRY_ALLOWED",
        }
        th_posture = {
            "metadata": {"market": "TH", "generated_at": today.isoformat()},
            "recommendation": "CASH_PRIORITY",
        }
        self._create_posture_file(
            f"exposure_posture_{today.strftime('%Y-%m-%d_%H%M%S')}.json", us_posture
        )
        self._create_posture_file(
            f"exposure_posture_{today.strftime('%Y-%m-%d_%H%M%S')}_TH.json", th_posture
        )

        us_result = get_latest_posture("US", reports_dir=str(self.test_reports_dir))
        th_result = get_latest_posture("TH", reports_dir=str(self.test_reports_dir))
        none_result = get_latest_posture("EU", reports_dir=str(self.test_reports_dir))

        self.assertIsNotNone(us_result)
        self.assertEqual(us_result["recommendation"], "NEW_ENTRY_ALLOWED")
        self.assertIsNotNone(th_result)
        self.assertEqual(th_result["recommendation"], "CASH_PRIORITY")
        self.assertIsNone(none_result)

    @patch("position_sizer.get_latest_posture")
    def test_calculate_position_posture_cash_priority(self, mock_get_latest_posture):
        mock_get_latest_posture.return_value = {
            "metadata": {"market": "US"},
            "recommendation": "CASH_PRIORITY",
            "exposure_ceiling_pct": 0,
        }
        params = SizingParameters(
            account_size=100000, entry_price=100, stop_price=99, risk_pct=1.0, market="US"
        )
        result = calculate_position(params)
        self.assertEqual(result["posture_applied"]["risk_multiplier"], 0.0)
        self.assertEqual(result["final_recommended_shares"], 0)  # 0 shares due to 0 risk_pct

    @patch("position_sizer.get_latest_posture")
    def test_calculate_position_posture_reduce_only(self, mock_get_latest_posture):
        mock_get_latest_posture.return_value = {
            "metadata": {"market": "US"},
            "recommendation": "REDUCE_ONLY",
            "exposure_ceiling_pct": 50,
        }
        params = SizingParameters(
            account_size=100000, entry_price=100, stop_price=99, risk_pct=1.0, market="US"
        )
        result = calculate_position(params)
        self.assertEqual(result["posture_applied"]["risk_multiplier"], 0.5)
        # Original shares would be 1000. With multiplier 0.5, it should be 500
        # dollar_risk = 100000 * (1.0 * 0.5) / 100 = 500
        # shares = 500 / (100-99) = 500
        self.assertEqual(result["final_recommended_shares"], 500)
        self.assertAlmostEqual(result["final_risk_pct"], 0.5)

    @patch("position_sizer.get_latest_posture")
    def test_calculate_position_posture_new_entry_allowed(self, mock_get_latest_posture):
        mock_get_latest_posture.return_value = {
            "metadata": {"market": "US"},
            "recommendation": "NEW_ENTRY_ALLOWED",
            "exposure_ceiling_pct": 100,
        }
        params = SizingParameters(
            account_size=100000, entry_price=100, stop_price=99, risk_pct=1.0, market="US"
        )
        result = calculate_position(params)
        self.assertEqual(result["posture_applied"]["risk_multiplier"], 1.0)
        self.assertEqual(result["final_recommended_shares"], 1000)
        self.assertAlmostEqual(result["final_risk_pct"], 1.0)

    @patch("position_sizer.get_latest_posture")
    def test_calculate_position_ignore_posture_flag(self, mock_get_latest_posture):
        mock_get_latest_posture.return_value = {
            "metadata": {"market": "US"},
            "recommendation": "CASH_PRIORITY",  # This should be ignored
            "exposure_ceiling_pct": 0,
        }
        params = SizingParameters(
            account_size=100000,
            entry_price=100,
            stop_price=99,
            risk_pct=1.0,
            market="US",
            ignore_posture=True,
        )
        result = calculate_position(params)
        mock_get_latest_posture.assert_not_called()
        self.assertEqual(result["posture_applied"]["risk_multiplier"], 1.0)
        self.assertEqual(result["final_recommended_shares"], 1000)
        self.assertAlmostEqual(result["final_risk_pct"], 1.0)

    @patch("position_sizer.get_latest_posture")
    def test_calculate_position_no_posture_data_found(self, mock_get_latest_posture):
        mock_get_latest_posture.return_value = None  # Simulate no posture data file found
        params = SizingParameters(
            account_size=100000, entry_price=100, stop_price=99, risk_pct=1.0, market="US"
        )
        result = calculate_position(params)
        self.assertEqual(result["posture_applied"]["risk_multiplier"], 1.0)
        self.assertEqual(result["final_recommended_shares"], 1000)
        self.assertAlmostEqual(result["final_risk_pct"], 1.0)
        self.assertEqual(result["posture_applied"]["recommendation"], "NEW_ENTRY_ALLOWED")

    @patch("position_sizer.get_latest_posture")
    def test_calculate_position_kelly_posture_scaling(self, mock_get_latest_posture):
        mock_get_latest_posture.return_value = {
            "metadata": {"market": "US"},
            "recommendation": "REDUCE_ONLY",  # Should scale Kelly by 0.5
            "exposure_ceiling_pct": 50,
        }
        params = SizingParameters(
            account_size=100000,
            win_rate=0.55,
            avg_win=2.5,
            avg_loss=1.0,
            entry_price=10,
            stop_price=9,
            market="US",
        )
        result = calculate_position(params)
        # Half Kelly for 0.55 win, 2.5/1 R is 18.5%. Multiplied by 0.5 -> 9.25%
        self.assertAlmostEqual(result["calculations"]["kelly"]["half_kelly_pct"], 9.25, places=2)
        # dollar_risk = 100000 * 0.0925 = 9250
        # shares = 9250 / (10-9) = 9250
        self.assertEqual(result["final_recommended_shares"], 9250)
        self.assertAlmostEqual(result["final_risk_pct"], 9.25, places=2)


if __name__ == "__main__":
    unittest.main()
