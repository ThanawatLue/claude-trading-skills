import json
import os
import sys
import subprocess
import unittest
import unittest.mock


class TestSkill(unittest.TestCase):
    def _run_scorer(self, extra_args, input_data=None):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "skills/us-market-bubble-detector/scripts/bubble_scorer.py"] + extra_args,
            capture_output=True,
            encoding="utf-8",
            env=env,
            input=input_data
        )

    @unittest.mock.patch('builtins.input', side_effect=['0'] * 8)
    def test_manual_mode_output_format(self, mock_input):
        print("\nRunning manual mode test with mocked inputs (all 0s).")
        process = self._run_scorer(["--manual"])
        self.assertEqual(process.returncode, 0)
        self.assertIn("総合スコア", process.stdout)
        self.assertIn("市場フェーズ", process.stdout)
        self.assertIn("推奨アクション", process.stdout)
        # Verify the total score for all 0s
        self.assertIn("0/16点", process.stdout)
        self.assertIn("現在: 正常域", process.stdout)

    def test_scores_mode_text_output(self):
        scores_json = json.dumps(
            {
                "mass_penetration": 1,
                "media_saturation": 1,
                "new_accounts": 1,
                "new_issuance": 1,
                "leverage": 1,
                "price_acceleration": 1,
                "valuation_disconnect": 1,
                "breadth_expansion": 1,
            }
        )
        process = self._run_scorer(["--scores", scores_json, "--output", "text"])
        self.assertEqual(process.returncode, 0)
        self.assertIn("総合スコア", process.stdout)
        self.assertIn("8/16点", process.stdout)
        self.assertIn("市場フェーズ", process.stdout)
        self.assertIn("現在: 警戒域", process.stdout)
        self.assertIn("推奨アクション", process.stdout)
        self.assertIn("部分利確の開始", process.stdout)

    def test_scores_mode_json_output(self):
        scores_json = json.dumps(
            {
                "mass_penetration": 2,
                "media_saturation": 2,
                "new_accounts": 2,
                "new_issuance": 2,
                "leverage": 2,
                "price_acceleration": 2,
                "valuation_disconnect": 2,
                "breadth_expansion": 2,
            }
        )
        process = self._run_scorer(["--scores", scores_json, "--output", "json"])
        self.assertEqual(process.returncode, 0)
        output_json = json.loads(process.stdout)
        self.assertEqual(output_json["total_score"], 16)
        self.assertEqual(output_json["phase"], "臨界域")
        self.assertEqual(output_json["risk_level"], "極めて高")

    def test_invalid_scores_input(self):
        invalid_scores_json = json.dumps({"mass_penetration": 5})
        process = self._run_scorer(["--scores", invalid_scores_json])
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("エラー: 無効なJSON形式またはスコアです", process.stderr)

    def test_missing_scores_input(self):
        process = self._run_scorer([])
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("エラー: --manual または --scores を指定してください", process.stderr)


if __name__ == "__main__":
    unittest.main()
