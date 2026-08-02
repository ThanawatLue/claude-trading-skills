#!/usr/bin/env python3
"""
Bubble-O-Meter: 米国株式市場のバブル度を多面的に評価するスクリプト

8つの指標を0-2点で評価し、合計スコア(0-16点)でバブル度を判定:
- 0-4: 正常域
- 5-8: 警戒域
- 9-12: 熱狂域
- 13-16: 臨界域

使用方法:
    python bubble_scorer.py --ticker SPY --period 1y
"""

import argparse
import json
from datetime import datetime
import gettext

# Initialize gettext for internationalization (i18n)
_ = gettext.gettext

LANGUAGE_DATA = {
    "en": {
        "title": "US Market Bubble Evaluation - Bubble-O-Meter",
        "manual_assessment_title": "US Market Bubble Evaluation - Manual Assessment",
        "score_prompt": "Evaluate each indicator from 0-2:",
        "indicator_name_mass_penetration": "Mass Penetration",
        "indicator_desc_mass_penetration": "Recommendations/mentions from non-investors",
        "indicator_name_media_saturation": "Media Saturation",
        "indicator_desc_media_saturation": "Surge in searches, social media, and media exposure",
        "indicator_name_new_accounts": "New Accounts & Inflows",
        "indicator_desc_new_accounts": "Acceleration in account openings and fund inflows",
        "indicator_name_new_issuance": "New Issuance Flood",
        "indicator_desc_new_issuance": "Proliferation of IPOs/SPACs/related products",
        "indicator_name_leverage": "Leverage",
        "indicator_desc_leverage": "Bias in margin balance, credit, and funding rates",
        "indicator_name_price_acceleration": "Price Acceleration",
        "indicator_desc_price_acceleration": "Returns reach upper historical distribution percentiles",
        "indicator_name_valuation_disconnect": "Valuation Disconnect",
        "indicator_desc_valuation_disconnect": "Fundamental explanations replaced by narratives",
        "indicator_name_breadth_expansion": "Breadth & Correlation",
        "indicator_desc_breadth_expansion": "Even low-quality stocks rise across the board",

        "phase_normal": "Normal",
        "phase_caution": "Caution",
        "phase_euphoria": "Euphoria",
        "phase_critical": "Critical",

        "risk_low": "Low",
        "risk_medium": "Medium",
        "risk_high": "High",
        "risk_extremely_high": "Extremely High",

        "action_normal": "Continue normal investment strategy",
        "action_caution": "Start partial profit-taking, reduce new position sizing",
        "action_euphoria": "Accelerate stair-step profit-taking, tighten ATR trailing stops, reduce total risk budget by 30-50%",
        "action_critical": "Significant profit-taking or full hedge, halt new entries, consider short positions after reversal confirmation",

        "minsky_displacement": "1. Displacement (Trigger) - Legitimate innovation & early investment",
        "minsky_extended_displacement_early_boom": "1.5. Extended Displacement/Early Boom - Early expansion",
        "minsky_boom": "2. Boom (Expansion) - Accelerating prices, increasing participation",
        "minsky_late_boom_early_euphoria": "2.5. Late Boom/Early Euphoria - Late expansion/Early fervor",
        "minsky_euphoria": "3. Euphoria (Exuberance) - Mass participation, narrative driven",
        "minsky_peak_euphoria_profit_taking": "4. Peak Euphoria/Profit Taking (Reversal imminent) - Extreme exuberance",
        "minsky_critical_late_profit_taking": "4.5. Critical/Late Profit Taking - Extreme risk",
        "minsky_panic": "5. Panic (Reversal) - Full reversal / Liquidation cascade",

        "guidelines_title": "Bubble Scoring Guidelines",
        "guidelines_mass_penetration": """
### 1. Mass Penetration
- 0 points: Discussion limited to experts/investors
- 1 point: Recognized by general public but limited as investment target
- 2 points: Non-investors (taxi drivers, hairdressers, family) actively recommending/mentioning
""",
        "guidelines_media_saturation": """
### 2. Media Saturation
- 0 points: Normal level of reporting/search trends
- 1 point: Search trends, social media mentions 2-3x normal
- 2 points: TV specials, magazine covers, search trends surge (5x+ normal)
""",
        "guidelines_new_accounts": """
### 3. New Accounts & Inflows
- 0 points: Normal pace of account openings/deposits
- 1 point: Account openings +50-100% YoY
- 2 points: Account openings +200%+ YoY, massive influx of "first-time investors"
""",
        "guidelines_new_issuance": """
### 4. New Issuance Flood
- 0 points: Normal level of IPOs/product formation
- 1 point: IPOs/SPACs/related ETFs increase 50%+ YoY
- 2 points: Proliferation of low-quality IPOs, "XX-related" funds/ETFs
""",
        "guidelines_leverage": """
### 5. Leverage Indicators
- 0 points: Margin balance/credit P&L within normal range
- 1 point: Margin balance 1.5x historical average, futures positions skewed
- 2 points: Margin balance at all-time high, funding rates elevated, extreme position bias
""",
        "guidelines_price_acceleration": """
### 6. Price Acceleration
- 0 points: Annual return near historical median
- 1 point: Annual return exceeds 90th percentile
- 2 points: Annual return 95-99th percentile, or acceleration (2nd derivative) positive and increasing
""",
        "guidelines_valuation_disconnect": """
### 7. Valuation Disconnect
- 0 points: Rationally explainable by fundamentals
- 1 point: High valuation but "growth expectations" provide some explanation
- 2 points: Explanation entirely dependent on "narrative," "revolution," "paradigm shift," "this time is different"
""",
        "guidelines_breadth_expansion": """
### 8. Breadth & Correlation
- 0 points: Only a few leading stocks rising
- 1 point: Spread to entire sector, mid-caps rising
- 2 points: Even low-quality/low-cap stocks rise across the board, "zombie companies" rallying (last buyers enter)
""",
        "error_invalid_json": "Error: Invalid JSON format.",
        "error_missing_args": "Error: --manual or --scores must be specified.",
        "score_value_error": "Please enter a number.",
        "score_range_error": "Please enter 0, 1, or 2.",
        "score_for": "Score for {}: ",
        "overall_score": "Overall Score",
        "market_phase": "Market Phase",
        "recommended_action": "Recommended Action",
        "indicator_scores": "Indicator Scores",
        "evaluation_timestamp": "Evaluation Timestamp",
        "status_high": "🔴High",
        "status_medium": "🟡Medium",
        "status_low": "🟢Low",
    },
    "ja": {
        "title": "米国市場バブル度評価 - Bubble-O-Meter",
        "manual_assessment_title": "米国市場バブル度評価 - Manual Assessment",
        "score_prompt": "各指標を0-2点で評価してください:",
        "indicator_name_mass_penetration": "大衆浸透度",
        "indicator_desc_mass_penetration": "非投資家層からの推奨・言及",
        "indicator_name_media_saturation": "メディア飽和",
        "indicator_desc_media_saturation": "検索・SNS・メディア露出の急騰",
        "indicator_name_new_accounts": "新規参入",
        "indicator_desc_new_accounts": "口座開設・資金流入の加速",
        "indicator_name_new_issuance": "新規発行氾濫",
        "indicator_desc_new_issuance": "IPO/SPAC/関連商品の乱立",
        "indicator_name_leverage": "レバレッジ",
        "indicator_desc_leverage": "証拠金・信用・資金調達レートの偏り",
        "indicator_name_price_acceleration": "価格加速度",
        "indicator_desc_price_acceleration": "リターンが歴史分布上位に到達",
        "indicator_name_valuation_disconnect": "バリュエーション逸脱",
        "indicator_desc_valuation_disconnect": "ファンダ説明が物語一辺倒に",
        "indicator_name_breadth_expansion": "相関と幅",
        "indicator_desc_breadth_expansion": "低質銘柄まで全面高",

        "phase_normal": "正常域",
        "phase_caution": "警戒域",
        "phase_euphoria": "熱狂域",
        "phase_critical": "臨界域",

        "risk_low": "低",
        "risk_medium": "中",
        "risk_high": "高",
        "risk_extremely_high": "極めて高",

        "action_normal": "通常通りの投資戦略を継続",
        "action_caution": "部分利確の開始、新規ポジションのサイズ縮小",
        "action_euphoria": "階段状利確の加速、ATRトレーリングストップ厳格化、総リスク予算30-50%削減",
        "action_critical": "大幅な利確またはフルヘッジ、新規参入停止、反転確認後のショートポジション検討",

        "minsky_displacement": "1. Displacement (きっかけ・初期拡張) - Legitimate innovation & early investment",
        "minsky_extended_displacement_early_boom": "1.5. Extended Displacement/Early Boom - Early expansion",
        "minsky_boom": "2. Boom (拡張期) - Accelerating prices, increasing participation",
        "minsky_late_boom_early_euphoria": "2.5. Late Boom/Early Euphoria - Late expansion/Early fervor",
        "minsky_euphoria": "3. Euphoria (熱狂期) - Mass participation, narrative driven",
        "minsky_peak_euphoria_profit_taking": "4. Peak Euphoria/Profit Taking (熱狂ピーク・利確開始) - Reversal imminent",
        "minsky_critical_late_profit_taking": "4.5. Critical/Late Profit Taking - Extreme risk",
        "minsky_panic": "5. Panic (パニック) - Full reversal / Liquidation cascade",

        "guidelines_title": "バブルスコアリング・ガイドライン",
        "guidelines_mass_penetration": """
### 1. 大衆浸透度 (Mass Penetration)
- 0点: 専門家・投資家層のみの議論
- 1点: 一般層にも認知されるが、まだ投資対象としては限定的
- 2点: 非投資家（タクシー運転手、美容師、家族）が積極的に推奨・言及
""",
        "guidelines_media_saturation": """
### 2. メディア飽和 (Media Saturation)
- 0点: 通常レベルの報道・検索トレンド
- 1点: 検索トレンド、SNS言及が平常の2-3倍
- 2点: テレビ特集、雑誌表紙、検索トレンド急騰（平常の5倍以上）
""",
        "guidelines_new_accounts": """
### 3. 新規参入 (New Accounts & Inflows)
- 0点: 通常レベルの口座開設・入金
- 1点: 口座開設が前年比50-100%増
- 2点: 口座開設が前年比200%以上、「初めての投資」層の大量流入
""",
        "guidelines_new_issuance": """
### 4. 新規発行氾濫 (New Issuance Flood)
- 0点: 通常レベルのIPO/商品組成
- 1点: IPO/SPAC/関連ETFが前年比50%以上増加
- 2点: 低質なIPO乱立、「○○関連」ファンド・ETFの濫造
""",
        "guidelines_leverage": """
### 5. レバレッジ (Leverage Indicators)
- 0点: 証拠金残高・信用評価損益が正常範囲
- 1点: 証拠金残高が過去平均の1.5倍、先物ポジション偏り
- 2点: 証拠金残高が過去最高更新、資金調達レート高止まり、極端なポジション偏り
""",
        "guidelines_price_acceleration": """
### 6. 価格加速度 (Price Acceleration)
- 0点: 年率リターンが歴史分布の中央値付近
- 1点: 年率リターンが過去90パーセンタイル超
- 2点: 年率リターンが過去95-99パーセンタイル、または加速度（2階微分）が正で増加
""",
        "guidelines_valuation_disconnect": """
### 7. バリュエーション逸脱 (Valuation Disconnect)
- 0点: ファンダメンタルで合理的に説明可能
- 1点: 高バリュエーションだが「成長期待」で一応説明可能
- 2点: 説明が完全に「物語」「革命」「パラダイムシフト」に依存、「今回は違う」
""",
        "guidelines_breadth_expansion": """
### 8. 相関と幅 (Breadth & Correlation)
- 0点: 一部のリーダー銘柄のみ上昇
- 1点: セクター全体に波及、mid-capまで上昇
- 2点: 低質・low-cap銘柄まで全面高、「ゾンビ企業」も上昇（最後の買い手参入）
""",
        "error_invalid_json": "エラー: 無効なJSON形式です",
        "error_missing_args": "エラー: --manual または --scores を指定してください",
        "score_value_error": "数値を入力してください",
        "score_range_error": "0, 1, 2 のいずれかを入力してください",
        "score_for": "{} (0-2): ",
        "overall_score": "【総合スコア】",
        "market_phase": "【市場フェーズ】",
        "recommended_action": "【推奨アクション】",
        "indicator_scores": "【指標別スコア】",
        "evaluation_timestamp": "評価日時",
        "status_high": "🔴高",
        "status_medium": "🟡中",
        "status_low": "🟢低",
    }
}


class BubbleScorer:
    """バブルスコアリングシステム"""

    def __init__(self, lang="en"):
        self.lang_data = LANGUAGE_DATA.get(lang, LANGUAGE_DATA["en"])
        self.indicators = {
            "mass_penetration": {
                "name": self.lang_data["indicator_name_mass_penetration"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_mass_penetration"],
            },
            "media_saturation": {
                "name": self.lang_data["indicator_name_media_saturation"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_media_saturation"],
            },
            "new_accounts": {
                "name": self.lang_data["indicator_name_new_accounts"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_new_accounts"],
            },
            "new_issuance": {
                "name": self.lang_data["indicator_name_new_issuance"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_new_issuance"],
            },
            "leverage": {
                "name": self.lang_data["indicator_name_leverage"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_leverage"],
            },
            "price_acceleration": {
                "name": self.lang_data["indicator_name_price_acceleration"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_price_acceleration"],
            },
            "valuation_disconnect": {
                "name": self.lang_data["indicator_name_valuation_disconnect"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_valuation_disconnect"],
            },
            "breadth_expansion": {
                "name": self.lang_data["indicator_name_breadth_expansion"],
                "weight": 2,
                "description": self.lang_data["indicator_desc_breadth_expansion"],
            },
        }

    def calculate_score(self, scores: dict[str, int]) -> dict:
        """
        各指標のスコアから総合評価を計算

        Args:
            scores: 各指標のスコア辞書 (0-2点)

        Returns:
            評価結果の辞書
        """
        total_score = sum(scores.values())
        max_score = len(self.indicators) * 2

        # バブル段階の判定
        if total_score <= 4:
            phase = self.lang_data["phase_normal"]
            risk_level = self.lang_data["risk_low"]
            action = self.lang_data["action_normal"]
        elif total_score <= 8:
            phase = self.lang_data["phase_caution"]
            risk_level = self.lang_data["risk_medium"]
            action = self.lang_data["action_caution"]
        elif total_score <= 12:
            phase = self.lang_data["phase_euphoria"]
            risk_level = self.lang_data["risk_high"]
            action = self.lang_data["action_euphoria"]
        else:
            phase = self.lang_data["phase_critical"]
            risk_level = self.lang_data["risk_extremely_high"]
            action = self.lang_data["action_critical"]

        # Minskyフェーズの推定
        minsky_phase = self._estimate_minsky_phase(scores, total_score)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_score": total_score,
            "max_score": max_score,
            "percentage": round(total_score / max_score * 100, 1),
            "phase": phase,
            "risk_level": risk_level,
            "minsky_phase": minsky_phase,
            "recommended_action": action,
            "indicator_scores": scores,
            "detailed_indicators": self._format_indicator_details(scores),
        }

    def _estimate_minsky_phase(self, scores: dict[str, int], total: int) -> str:
        """Minsky/Kindlebergerフェーズの推定"""
        mass_pen = scores.get("mass_penetration", 0)
        media = scores.get("media_saturation", 0)
        price_acc = scores.get("price_acceleration", 0)
        leverage = scores.get("leverage", 0)
        valuation_disc = scores.get("valuation_disconnect", 0)
        new_accounts = scores.get("new_accounts", 0)
        new_issuance = scores.get("new_issuance", 0)

        # 1. Displacement (きっかけ・初期拡張)
        if total <= 4:
            return self.lang_data["minsky_displacement"]

        # 2. Boom (拡張期)
        # Characterized by accelerating prices, increasing participation, but not yet mass hysteria.
        # Total scores up to 8 (Caution phase)
        if total <= 8:
            # Stronger signs of boom
            if price_acc >= 1 or new_accounts >= 1 or media >= 1:
                return self.lang_data["minsky_boom"]
            else:
                # If total is in caution range but specific boom indicators are low, it's a slower boom or extended displacement
                return self.lang_data["minsky_extended_displacement_early_boom"]

        # 3. Euphoria (熱狂期)
        # Characterized by mass participation, narrative dominance, high leverage/new issuance, disregard for fundamentals.
        # Total scores up to 12 (Euphoria phase)
        if total <= 12:
            # Stronger signs of euphoria
            if mass_pen >= 1 or media >= 2 or leverage >= 1 or valuation_disc >= 1 or new_issuance >= 1:
                return self.lang_data["minsky_euphoria"]
            else:
                # If in euphoria total range but core euphoria indicators are not strong
                return self.lang_data["minsky_late_boom_early_euphoria"]

        # 4. Profit Taking (利確開始) and 5. Panic (パニック)
        # Total scores > 12 (Critical phase)
        # These phases are harder to distinguish solely by score, but can be inferred from extreme indicators.
        if total > 12: # Critical range (13-19)
            # If mass penetration, media, and other key indicators are at their peak
            if mass_pen >= 2 and media >= 2 and (leverage >= 2 or valuation_disc >= 2 or new_issuance >= 2):
                return self.lang_data["minsky_peak_euphoria_profit_taking"]
            elif total >= 16: # Very high total score, implying widespread issues
                 return self.lang_data["minsky_panic"]
            else:
                return self.lang_data["minsky_critical_late_profit_taking"]

    def _format_indicator_details(self, scores: dict[str, int]) -> list[dict]:
        """指標の詳細情報をフォーマット"""
        details = []
        for key, value in scores.items():
            indicator = self.indicators.get(key, {})
            status = self.lang_data["status_high"] if value == 2 else self.lang_data["status_medium"] if value == 1 else self.lang_data["status_low"]
            details.append(
                {
                    "indicator": indicator.get("name", key),
                    "score": value,
                    "status": status,
                    "description": indicator.get("description", ""),
                }
            )
        return details

    def get_scoring_guidelines(self) -> str:
        """各指標のスコアリングガイドラインを返す"""
        guidelines = f"""
## {self.lang_data["guidelines_title"]}

{self.lang_data["guidelines_mass_penetration"]}
{self.lang_data["guidelines_media_saturation"]}
{self.lang_data["guidelines_new_accounts"]}
{self.lang_data["guidelines_new_issuance"]}
{self.lang_data["guidelines_leverage"]}
{self.lang_data["guidelines_price_acceleration"]}
{self.lang_data["guidelines_valuation_disconnect"]}
{self.lang_data["guidelines_breadth_expansion"]}
"""
        return guidelines

    def format_output(self, result: dict) -> str:
        """結果を読みやすくフォーマット"""
        output = f"""
{"=" * 60}
🔍 {self.lang_data["title"]}
{"=" * 60}

{self.lang_data["evaluation_timestamp"]}: {result["timestamp"]}

{self.lang_data["overall_score"]}
{result["total_score"]}/{result["max_score"]}点 ({result["percentage"]}%)

{self.lang_data["market_phase"]}
{_("Current")}: {result["phase"]} ({_("Risk")}: {result["risk_level"]})
Minsky{_("Phase")}: {result["minsky_phase"]}

{self.lang_data["recommended_action"]}
{result["recommended_action"]}

{"=" * 60}
{self.lang_data["indicator_scores"]}
{"=" * 60}
"""
        for detail in result["detailed_indicators"]:
            output += f"\n{detail['status']} {detail['indicator']}: {detail['score']}/2{_('points')}\n"
            output += f"   └─ {detail['description']}\n"

        output += f"\n{'=' * 60}\n"

        return output


def manual_assessment(lang: str) -> dict[str, int]:
    """対話型の手動評価"""
    scorer = BubbleScorer(lang=lang)
    print("\n" + "=" * 60)
    print(f"🔍 {scorer.lang_data['manual_assessment_title']}")
    print("=" * 60)
    print(f"\n{scorer.lang_data['score_prompt']}")
    print(scorer.get_scoring_guidelines())

    scores = {}
    for key, indicator in scorer.indicators.items():
        while True:
            try:
                score = int(input(f"\n{scorer.lang_data['score_for'].format(indicator['name'])}"))
                if 0 <= score <= 2:
                    scores[key] = score
                    break
                else:
                    print(scorer.lang_data["score_range_error"])
            except ValueError:
                print(scorer.lang_data["score_value_error"])

    return scores


def main():
    parser = argparse.ArgumentParser(description=_("US Market Bubble Evaluation - Bubble-O-Meter"))
    parser.add_argument("--manual", action="store_true", help=_("Interactive manual assessment mode"))
    parser.add_argument(
        "--scores",
        type=str,
        help=_('JSON formatted score string (e.g., \'{"mass_penetration":2,"media_saturation":1,...}\')'),
    )
    parser.add_argument("--output", choices=["text", "json"], default="text", help=_("Output format"))
    parser.add_argument("--lang", choices=["en", "ja"], default="en", help=_("Output language"))


    args = parser.parse_args()
    scorer = BubbleScorer(lang=args.lang)

    # Use gettext to set the current language for _() calls outside the class
    current_lang = args.lang
    try:
        local_translation = gettext.translation('bubble_scorer',
                                                localedir='skills/us-market-bubble-detector/locale',
                                                languages=[current_lang])
        local_translation.install()
        global _
        _ = local_translation.gettext
    except Exception:
        # Fallback if translation files are not found or configured
        pass


    # スコアの取得
    if args.manual:
        scores = manual_assessment(args.lang)
    elif args.scores:
        try:
            scores = json.loads(args.scores)
        except json.JSONDecodeError:
            print(scorer.lang_data["error_invalid_json"])
            return 1
    else:
        print(scorer.lang_data["error_missing_args"])
        print("\n" + scorer.lang_data["guidelines_title"] + ":")
        print(scorer.get_scoring_guidelines())
        return 1

    # 評価の実行
    result = scorer.calculate_score(scores)

    # 出力
    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(scorer.format_output(result))

    return 0


if __name__ == "__main__":
    exit(main())
