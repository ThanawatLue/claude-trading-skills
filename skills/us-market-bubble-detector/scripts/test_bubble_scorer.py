import unittest

from bubble_scorer import BubbleScorer


class TestBubbleScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = BubbleScorer()
        self.default_scores = {
            "mass_penetration": 0,
            "media_saturation": 0,
            "new_accounts": 0,
            "new_issuance": 0,
            "leverage": 0,
            "price_acceleration": 0,
            "valuation_disconnect": 0,
            "breadth_expansion": 0,
        }

    def test_initialization(self):
        self.assertIsInstance(self.scorer, BubbleScorer)
        self.assertEqual(len(self.scorer.indicators), 8)

    def test_calculate_score_min(self):
        scores = self.default_scores
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["total_score"], 0)
        self.assertEqual(result["phase"], "正常域")
        self.assertEqual(result["risk_level"], "低")
        self.assertEqual(result["percentage"], 0.0)
        self.assertIn("timestamp", result)
        self.assertIn("detailed_indicators", result)

    def test_calculate_score_max(self):
        scores = {key: 2 for key in self.scorer.indicators}
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["total_score"], 16)
        self.assertEqual(result["phase"], "臨界域")
        self.assertEqual(result["risk_level"], "極めて高")
        self.assertEqual(result["percentage"], 100.0)

    def test_calculate_score_mid_caution(self):
        scores = self.default_scores.copy()
        scores["mass_penetration"] = 1
        scores["media_saturation"] = 1
        scores["new_accounts"] = 1
        scores["new_issuance"] = 1
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["total_score"], 4)  # Still normal, as <= 4
        self.assertEqual(result["phase"], "正常域")

        scores["leverage"] = 1  # Total 5
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["total_score"], 5)
        self.assertEqual(result["phase"], "警戒域")
        self.assertEqual(result["risk_level"], "中")

    def test_calculate_score_mid_euphoria(self):
        scores = {key: 1 for key in self.scorer.indicators}  # Total 8
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["total_score"], 8)
        self.assertEqual(result["phase"], "警戒域")  # Still caution, as <= 8

        scores["mass_penetration"] = 2  # Total 9
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["total_score"], 9)
        self.assertEqual(result["phase"], "熱狂域")
        self.assertEqual(result["risk_level"], "高")

    def test_minsky_phase_estimation(self):
        # Displacement/Early Boom
        scores = self.default_scores.copy()
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["minsky_phase"], "Displacement/Early Boom (きっかけ・初期拡張)")

        # Boom
        scores = self.default_scores.copy()
        scores["media_saturation"] = 1
        scores["price_acceleration"] = 1
        scores["new_accounts"] = 1  # Total 3
        result = self.scorer.calculate_score(scores)
        self.assertEqual(
            result["minsky_phase"], "Displacement/Early Boom (きっかけ・初期拡張)"
        )  # Total <= 4

        scores["leverage"] = 1  # Total 4
        result = self.scorer.calculate_score(scores)
        self.assertEqual(
            result["minsky_phase"], "Displacement/Early Boom (きっかけ・初期拡張)"
        )  # Total <= 4

        scores["new_issuance"] = 1  # Total 5, media=1, price_acc=1
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["minsky_phase"], "Boom (拡張期)")

        # Euphoria
        scores = {key: 1 for key in self.scorer.indicators}  # Total 8
        scores["mass_penetration"] = 2
        scores["media_saturation"] = 2  # Total 10, mass_pen=2, media=2
        result = self.scorer.calculate_score(scores)
        self.assertEqual(result["minsky_phase"], "Euphoria (熱狂期) - FOMOが制度化")

        # Peak Euphoria/Profit Taking
        scores = {key: 2 for key in self.scorer.indicators}  # Total 16, mass_pen=2
        result = self.scorer.calculate_score(scores)
        self.assertEqual(
            result["minsky_phase"], "Peak Euphoria/Profit Taking (熱狂ピーク・利確開始) - 反転間近"
        )

    def test_format_output(self):
        scores = {key: 1 for key in self.scorer.indicators}
        result = self.scorer.calculate_score(scores)
        output = self.scorer.format_output(result)
        self.assertIn("総合スコア", output)
        self.assertIn("市場フェーズ", output)
        self.assertIn("推奨アクション", output)
        self.assertIn("指標別スコア", output)
        self.assertIn("🟡中 大衆浸透度: 1/2点", output)

    def test_missing_score_input_validation(self):
        incomplete_scores = {
            "mass_penetration": 1,
            "media_saturation": 1,
            # Missing others
        }
        with self.assertRaisesRegex(ValueError, "Missing score for indicator: new_accounts"):
            self.scorer.calculate_score(incomplete_scores)

    def test_invalid_score_range_input_validation(self):
        invalid_scores = self.default_scores.copy()
        invalid_scores["mass_penetration"] = 3  # Invalid score
        with self.assertRaisesRegex(
            ValueError, "Score for mass_penetration must be between 0 and 2."
        ):
            self.scorer.calculate_score(invalid_scores)


if __name__ == "__main__":
    unittest.main()
