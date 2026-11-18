#!/usr/bin/env python3
"""
Exposure Coach - Calculate market posture and exposure recommendation.

Synthesizes signals from multiple upstream skills to produce a unified
exposure ceiling, bias direction, and action recommendation.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Component weights for composite score
WEIGHTS = {
    "regime": 0.25,
    "top_risk": 0.20,
    "breadth": 0.15,
    "uptrend": 0.15,
    "institutional": 0.10,
    "sector": 0.05,
    "theme": 0.05,
    "ftd": 0.05,
}

# Critical inputs that reduce confidence when missing
# This is the default for US market. TH market will use different critical inputs.
US_CRITICAL_INPUTS = {"regime", "top_risk", "breadth"}
TH_CRITICAL_INPUTS = {"breadth"}

# Regime to baseline score mapping
REGIME_SCORES = {
    "broadening": 80,
    "concentration": 60,
    "transitional": 50,
    "inflationary": 40,
    "contraction": 20,
    "strong bull": 80,
    "healthy uptrend": 65,
    "bullish": 75,
    "neutral": 50,
    "mixed / corrective": 42,
    "bear regime": 20,
    "bearish": 20,
}


def load_json_file(path: Optional[Path]) -> Optional[dict]:
    """Load a JSON file if it exists and is valid."""
    if path is None or not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
        return None


def extract_breadth_score(data: Optional[dict]) -> Optional[int]:
    """Extract breadth score from breadth analyzer output."""
    if data is None:
        return None
    # Support various field names from upstream skill
    if "breadth_score" in data:
        return int(data["breadth_score"])
    if "composite_score" in data:
        return int(data["composite_score"])
    if "composite" in data and isinstance(data["composite"], dict):
        c = data["composite"]
        if "composite_score" in c:
            return int(c["composite_score"])
        if "score" in c:
            return int(c["score"])
    if "ad_ratio" in data and "nh_nl_ratio" in data:
        ad = data["ad_ratio"]
        nh_nl = data["nh_nl_ratio"]
        if ad > 1.5 and nh_nl > 3.0:
            return 90
        elif ad >= 1.0 and nh_nl >= 1.0:
            return 65
        elif ad >= 0.7 and nh_nl >= 0.5:
            return 40
        else:
            return 20
    return None


def extract_uptrend_score(data: Optional[dict]) -> Optional[int]:
    """Extract uptrend participation score."""
    if data is None:
        return None
    if "uptrend_score" in data:
        return int(data["uptrend_score"])
    if isinstance(data.get("breadth"), dict) and "pct_above_sma50" in data["breadth"]:
        b = data["breadth"]
        p50 = float(b["pct_above_sma50"])
        p200 = float(b["pct_above_sma200"]) if b.get("pct_above_sma200") is not None else p50
        return max(0, min(100, int(round(0.6 * p50 + 0.4 * p200))))
    if "composite" in data and isinstance(data["composite"], dict):
        c = data["composite"]
        if "composite_score" in c:
            return int(c["composite_score"])
        if "score" in c:
            return int(c["score"])
    if "uptrend_pct" in data:
        pct = data["uptrend_pct"]
        if pct > 50:
            return min(100, int(50 + pct))
        elif pct >= 35:
            return int(35 + pct)
        elif pct >= 20:
            return int(20 + pct)
        else:
            return int(pct)
    return None


def extract_regime_score(data: Optional[dict]) -> Optional[int]:
    """Extract regime score from macro-regime-detector or breadth-regime output."""
    if data is None:
        return None
    if "regime_score" in data:
        return int(data["regime_score"])
    reg = data.get("regime")
    if isinstance(reg, dict):
        curr = reg.get("current_regime") or reg.get("regime_label")
        if curr:
            return REGIME_SCORES.get(str(curr).lower().strip(), 50)
    if isinstance(reg, str) and reg.strip():
        return REGIME_SCORES.get(reg.lower().strip(), 50)
    if "current_regime" in data and data["current_regime"]:
        regime = str(data["current_regime"]).lower().strip()
        return REGIME_SCORES.get(regime, 50)
    comp = data.get("composite")
    if isinstance(comp, dict):
        score = (
            comp.get("composite_score")
            if comp.get("composite_score") is not None
            else comp.get("score")
        )
        if score is not None:
            return max(0, min(100, int(float(score))))
    return None


def extract_regime_name(data: Optional[dict]) -> str:
    """Extract regime name from data."""
    if data is None:
        return "Unknown"
    reg = data.get("regime")
    if isinstance(reg, dict):
        curr = reg.get("regime_label") or reg.get("current_regime")
        if curr:
            return str(curr).capitalize()
    if isinstance(reg, str) and reg.strip():
        return reg.capitalize()
    if "current_regime" in data and data["current_regime"]:
        return str(data["current_regime"]).capitalize()
    comp = data.get("composite")
    if isinstance(comp, dict) and comp.get("zone"):
        return str(comp["zone"]).capitalize()
    return "Unknown"


def extract_top_risk_score(data: Optional[dict]) -> Optional[int]:
    """Extract top risk score (inverted - high risk = low score)."""
    if data is None:
        return None
    if "top_risk_score" in data:
        return int(data["top_risk_score"])
    mds = data.get("market_distribution_state")
    if isinstance(mds, dict):
        risk_map = {"NORMAL": 90, "CAUTION": 65, "HIGH": 35, "SEVERE": 15}
        level = str(mds.get("overall_risk_level") or "").upper()
        if level in risk_map:
            return risk_map[level]
        idx_res = mds.get("index_results") or []
        d25_vals = [
            int(r["d25_count"])
            for r in idx_res
            if isinstance(r, dict) and r.get("d25_count") is not None
        ]
        if d25_vals:
            days = max(d25_vals)
            return 90 if days <= 2 else (65 if days <= 4 else (40 if days <= 6 else 15))
    if "composite" in data and isinstance(data["composite"], dict):
        c = data["composite"]
        score = c.get("composite_score") or c.get("score")
        if score is not None:
            return max(0, min(100, int(100 - float(score))))
    if "top_probability" in data:
        prob = data["top_probability"]
        # Invert: high probability = low score
        return max(0, min(100, int(100 - prob)))
    if "distribution_days" in data:
        days = data["distribution_days"]
        if days <= 2:
            return 90
        elif days <= 4:
            return 65
        elif days <= 6:
            return 40
        else:
            return 15
    return None


def extract_ftd_score(data: Optional[dict]) -> Optional[int]:
    """Extract FTD score from FTD detector output or legacy anomaly payload."""
    if data is None:
        return None
    if "ftd_score" in data:
        return int(data["ftd_score"])
    ms = data.get("market_state")
    if isinstance(ms, dict):
        state = str(ms.get("combined_state") or "").upper()
        qs = (data.get("quality_score") or {}).get("total_score")
        if state == "FTD_CONFIRMED":
            if qs is not None and float(qs) > 0:
                return max(60, min(100, int(round(float(qs)))))
            return 80
        state_map = {
            "FTD_WINDOW": 60,
            "RALLY_ATTEMPT": 50,
            "NO_SIGNAL": 50,
            "CORRECTION": 30,
            "RALLY_FAILED": 25,
            "FTD_INVALIDATED": 20,
        }
        if state in state_map:
            return state_map[state]
    if "anomaly_level" in data:
        level = data["anomaly_level"].lower()
        mapping = {"none": 90, "low": 80, "moderate": 55, "elevated": 35, "critical": 15}
        return mapping.get(level, 50)
    return None


def extract_theme_score(data: Optional[dict]) -> Optional[int]:
    """Extract theme strength score."""
    if data is None:
        return None
    if "theme_score" in data:
        return int(data["theme_score"])
    if "theme_strength" in data:
        strength = data["theme_strength"].lower()
        mapping = {"strong": 85, "stable": 65, "rotating": 40, "collapsing": 20}
        return mapping.get(strength, 50)
    return None


def extract_sector_score(data: Optional[dict]) -> Optional[int]:
    """Extract sector condition score from sector analyst, heatmap, or summary."""
    if data is None:
        return None
    if "sector_score" in data:
        return int(data["sector_score"])
    sectors = data.get("sectors")
    if isinstance(sectors, list) and sectors:
        mom_scores = [
            float(s["momentum_score"])
            for s in sectors
            if isinstance(s, dict) and s.get("momentum_score") is not None
        ]
        if mom_scores:
            sorted_m = sorted(mom_scores)
            n = len(sorted_m)
            med_mom = sorted_m[n // 2] if n % 2 else (sorted_m[n // 2 - 1] + sorted_m[n // 2]) / 2.0
            pos_ratio = sum(1 for m in mom_scores if m > 0) / n
            score = 50.0 + med_mom * 2.0 + (pos_ratio - 0.5) * 30.0
            return max(10, min(95, int(round(score))))
    groups = data.get("groups")
    if isinstance(groups, dict) and groups.get("score") is not None:
        group_score = float(groups["score"])
        trends = data.get("trends")
        if isinstance(trends, dict):
            up = int(trends.get("uptrend_count") or 0)
            down = int(trends.get("downtrend_count") or 0)
            if up + down > 0:
                up_pct = (up / (up + down)) * 100.0
                return max(0, min(100, int(round(0.6 * group_score + 0.4 * up_pct))))
        return max(0, min(100, int(round(group_score))))
    if "dispersion" in data and "leadership" in data:
        disp = data["dispersion"]
        lead = data["leadership"].lower()
        if disp < 0.1 and lead in ["technology", "consumer discretionary"]:
            return 85
        elif disp < 0.2:
            return 65
        elif lead in ["utilities", "staples", "healthcare"]:
            return 35
        else:
            return 50
    return None


def extract_institutional_score(data: Optional[dict]) -> Optional[int]:
    """Extract institutional flow score."""
    if data is None:
        return None
    if "institutional_score" in data:
        return int(data["institutional_score"])
    if "net_flow" in data:
        flow = data["net_flow"]
        if flow > 0.5:
            return 90
        elif flow > 0:
            return 70
        elif flow > -0.5:
            return 40
        else:
            return 20
    if "flow_direction" in data:
        direction = data["flow_direction"].lower()
        mapping = {
            "strong_buying": 90,
            "buying": 70,
            "neutral": 50,
            "selling": 30,
            "strong_selling": 15,
        }
        return mapping.get(direction, 50)
    return None


def calculate_composite_score(
    scores: dict[str, Optional[int]],
    market: str = "US",
) -> tuple[float, list[str], list[str]]:
    """
    Calculate weighted composite score.

    Returns:
        Tuple of (composite_score, inputs_provided, inputs_missing)
    """
    provided = []
    missing = []
    weighted_sum = 0.0
    total_weight = 0.0

    for key, weight in WEIGHTS.items():
        score = scores.get(key)
        if score is not None:
            weighted_sum += score * weight
            total_weight += weight
            provided.append(key)
        else:
            missing.append(key)

    if total_weight == 0:
        return 50.0, provided, missing

    composite = weighted_sum / total_weight

    # Apply haircut for missing critical inputs
    critical_inputs = US_CRITICAL_INPUTS if market == "US" else TH_CRITICAL_INPUTS
    missing_critical = set(missing) & critical_inputs
    haircut = len(missing_critical) * 10
    composite = max(0, composite - haircut)

    return composite, provided, missing


def determine_exposure_ceiling(composite: float) -> int:
    """Map composite score to exposure ceiling percentage."""
    if composite >= 80:
        return min(100, int(90 + (composite - 80)))
    elif composite >= 65:
        return int(70 + (composite - 65) * 1.3)
    elif composite >= 50:
        return int(50 + (composite - 50) * 1.3)
    elif composite >= 35:
        return int(30 + (composite - 35) * 1.3)
    elif composite >= 20:
        return int(10 + (composite - 20) * 1.3)
    else:
        return max(0, int(composite / 2))


def determine_recommendation(
    composite: float, top_risk_score: Optional[int], missing_critical: int, market: str = "US"
) -> str:
    """Determine action recommendation."""
    # CASH_PRIORITY conditions
    if composite < 30:
        return "CASH_PRIORITY"
    if market == "US" and top_risk_score is not None and top_risk_score < 25:
        return "CASH_PRIORITY"

    # REDUCE_ONLY conditions
    if composite < 50:
        return "REDUCE_ONLY"
    if market == "US" and top_risk_score is not None and top_risk_score < 40:
        return "REDUCE_ONLY"
    if missing_critical >= 2:
        return "REDUCE_ONLY"

    return "NEW_ENTRY_ALLOWED"


def determine_bias(
    regime_name: str,
    theme_score: Optional[int],
    sector_data: Optional[dict],
    institutional_data: Optional[dict],
) -> str:
    """Determine growth vs value bias."""
    regime_lower = regime_name.lower()

    # Strong regime signals
    if regime_lower == "inflationary":
        return "VALUE"
    if regime_lower == "contraction":
        return "DEFENSIVE"

    # Theme strength indicates growth momentum
    if theme_score is not None and theme_score > 60:
        if regime_lower in ["broadening", "concentration"]:
            return "GROWTH"

    # Sector leadership
    if sector_data and "leadership" in sector_data:
        lead = sector_data["leadership"].lower()
        if lead in ["technology", "consumer discretionary", "communications"]:
            return "GROWTH"
        if lead in ["financials", "energy", "materials", "industrials"]:
            return "VALUE"
        if lead in ["utilities", "staples", "healthcare"]:
            return "DEFENSIVE"

    if sector_data and isinstance(sector_data.get("sectors"), list) and sector_data["sectors"]:
        top_names = " ".join(
            str(s.get("sector") or "").lower()
            for s in sector_data["sectors"][:2]
            if isinstance(s, dict)
        )
        if any(
            k in top_names
            for k in ("tech", "electronic", "communication", "consumer discretionary")
        ):
            return "GROWTH"
        if any(k in top_names for k in ("financ", "energy", "material", "industrial", "mineral")):
            return "VALUE"
        if any(k in top_names for k in ("utilit", "staple", "health", "non-durables")):
            return "DEFENSIVE"

    if sector_data and isinstance(sector_data.get("groups"), dict):
        diff = sector_data["groups"].get("difference")
        if diff is not None:
            if float(diff) > 0.05:
                return "GROWTH"
            if float(diff) < -0.05:
                return "DEFENSIVE"

    # Institutional flow
    if institutional_data and "sector_flows" in institutional_data:
        flows = institutional_data["sector_flows"]
        if isinstance(flows, dict):
            growth_flow = sum(flows.get(s, 0) for s in ["Technology", "Consumer Discretionary"])
            value_flow = sum(flows.get(s, 0) for s in ["Financials", "Energy", "Industrials"])
            if growth_flow > value_flow + 0.2:
                return "GROWTH"
            if value_flow > growth_flow + 0.2:
                return "VALUE"

    return "NEUTRAL"


def determine_participation(
    uptrend_score: Optional[int], breadth_score: Optional[int], sector_data: Optional[dict]
) -> str:
    """Assess market participation breadth."""
    # Check uptrend and breadth scores
    uptrend_broad = uptrend_score is not None and uptrend_score >= 50
    breadth_broad = breadth_score is not None and breadth_score >= 50

    # Check sector dispersion if available
    low_dispersion = True
    if sector_data and "dispersion" in sector_data:
        low_dispersion = sector_data["dispersion"] < 0.15

    if uptrend_broad and breadth_broad and low_dispersion:
        return "BROAD"
    elif (uptrend_broad or breadth_broad) and low_dispersion:
        return "MODERATE"
    else:
        return "NARROW"


def determine_confidence(provided: list[str], missing: list[str], market: str = "US") -> str:
    """Determine confidence level based on input completeness."""
    n_provided = len(provided)
    critical_inputs = US_CRITICAL_INPUTS if market == "US" else TH_CRITICAL_INPUTS
    missing_critical = len(set(missing) & critical_inputs)

    if market == "TH":
        if n_provided >= 3 and missing_critical == 0:
            return "HIGH"
        elif n_provided >= 2 or missing_critical <= 1:
            return "MEDIUM"
        else:
            return "LOW"
    else:
        if n_provided >= 6 and missing_critical == 0:
            return "HIGH"
        elif n_provided >= 4 or missing_critical <= 1:
            return "MEDIUM"
        else:
            return "LOW"


def generate_rationale(
    composite: float,
    recommendation: str,
    participation: str,
    bias: str,
    scores: dict[str, Optional[int]],
    missing: list[str],
    market: str = "US",
) -> str:
    """Generate human-readable rationale."""
    parts = []

    # Participation assessment
    if participation == "BROAD":
        parts.append("Broad participation indicates healthy market internals.")
    elif participation == "NARROW":
        parts.append("Narrow participation suggests fragile market structure.")

    # Top risk assessment
    top_risk = scores.get("top_risk")
    if top_risk is not None:
        if top_risk >= 70:
            parts.append("Low distribution day count supports risk-on posture.")
        elif top_risk < 40:
            parts.append("Elevated top risk signals warrant caution.")

    # Regime context
    regime = scores.get("regime")
    if regime is not None:
        if regime >= 70:
            parts.append("Favorable macro regime supports elevated exposure.")
        elif regime < 40:
            parts.append("Challenging macro regime limits upside exposure.")

    # Missing inputs
    if missing:
        critical_inputs = US_CRITICAL_INPUTS if market == "US" else TH_CRITICAL_INPUTS
        critical_missing = set(missing) & critical_inputs
        if critical_missing:
            parts.append(
                f"Missing critical inputs ({', '.join(critical_missing)}) reduce confidence."
            )

    # Recommendation context
    if recommendation == "CASH_PRIORITY":
        parts.append("Capital preservation is the priority.")
    elif recommendation == "REDUCE_ONLY":
        parts.append("New entries not recommended; consider trimming on strength.")
    else:
        parts.append(f"New positions allowed within the {int(composite)}% ceiling.")

    return " ".join(parts)


def generate_markdown_report(result: dict) -> str:
    """Generate markdown report from result dict."""
    lines = [
        "# Market Posture Summary",
        f"**Date:** {result['generated_at'][:10]} | **Confidence:** {result['confidence']}",
        "",
        f"## Exposure Ceiling: {result['exposure_ceiling_pct']}%",
        "",
        "| Dimension | Score | Status |",
        "|-----------|-------|--------|",
    ]

    # Add component scores
    status_map = {
        (70, 101): "Strong",
        (50, 70): "Healthy",
        (30, 50): "Cautious",
        (0, 30): "Weak",
    }

    for key in [
        "breadth",
        "uptrend",
        "regime",
        "top_risk",
        "ftd",
        "theme",
        "sector",
        "institutional",
    ]:
        score = result["component_scores"].get(f"{key}_score")
        if score is not None:
            status = "N/A"
            for (lo, hi), label in status_map.items():
                if lo <= score < hi:
                    status = label
                    break
            display_name = key.replace("_", " ").title()
            lines.append(f"| {display_name} | {score} | {status} |")

    lines.extend(
        [
            "",
            f"## Recommendation: {result['recommendation']}",
            "",
            f"**Bias:** {result['bias']}",
            f"**Participation:** {result['participation']}",
            "",
            "### Rationale",
            result["rationale"],
            "",
        ]
    )

    if result["inputs_missing"]:
        lines.extend(
            [
                "### Missing Inputs",
                ", ".join(result["inputs_missing"]),
                "",
            ]
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate market exposure posture from upstream skill outputs"
    )
    parser.add_argument("--market", choices=["US", "TH"], default="US", help="Market context")
    parser.add_argument("--breadth", type=Path, help="Path to breadth analyzer JSON")
    parser.add_argument("--uptrend", type=Path, help="Path to uptrend analyzer JSON")
    parser.add_argument("--regime", type=Path, help="Path to macro-regime-detector JSON")
    parser.add_argument("--top-risk", type=Path, help="Path to market-top-detector JSON")
    parser.add_argument("--ftd", type=Path, help="Path to ftd-detector JSON")
    parser.add_argument("--theme", type=Path, help="Path to theme-detector JSON")
    parser.add_argument("--sector", type=Path, help="Path to sector-analyst JSON")
    parser.add_argument(
        "--institutional", type=Path, help="Path to institutional-flow-tracker JSON"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Output directory for reports (default: reports/)",
    )
    parser.add_argument("--json-only", action="store_true", help="Output JSON only, skip markdown")

    args = parser.parse_args()

    # Load all inputs
    breadth_data = load_json_file(args.breadth)
    uptrend_data = load_json_file(args.uptrend)
    regime_data = load_json_file(args.regime)
    top_risk_data = load_json_file(args.top_risk)
    ftd_data = load_json_file(args.ftd)
    theme_data = load_json_file(args.theme)
    sector_data = load_json_file(args.sector)
    institutional_data = load_json_file(args.institutional)

    # Extract scores
    scores: dict[str, Optional[int]] = {
        "breadth": extract_breadth_score(breadth_data),
        "uptrend": extract_uptrend_score(uptrend_data),
        "regime": extract_regime_score(regime_data),
        "top_risk": extract_top_risk_score(top_risk_data),
        "ftd": extract_ftd_score(ftd_data),
        "theme": extract_theme_score(theme_data),
        "sector": extract_sector_score(sector_data),
        "institutional": extract_institutional_score(institutional_data),
    }

    # Derive local TH uptrend participation directly from TV breadth when --uptrend is omitted
    if (
        scores["uptrend"] is None
        and args.market == "TH"
        and isinstance(breadth_data, dict)
        and isinstance(breadth_data.get("breadth"), dict)
        and "pct_above_sma50" in breadth_data["breadth"]
    ):
        scores["uptrend"] = extract_uptrend_score(breadth_data)

    # Use explicitly passed market arg (defaults to "US")
    market = args.market

    # Calculate composite
    composite, provided, missing = calculate_composite_score(scores, market)

    # Determine outputs
    exposure_ceiling = determine_exposure_ceiling(composite)
    critical_inputs = US_CRITICAL_INPUTS if market == "US" else TH_CRITICAL_INPUTS
    missing_critical = len(set(missing) & critical_inputs)
    recommendation = determine_recommendation(
        composite, scores["top_risk"], missing_critical, market
    )

    regime_name = extract_regime_name(regime_data)
    bias = determine_bias(regime_name, scores["theme"], sector_data, institutional_data)
    participation = determine_participation(scores["uptrend"], scores["breadth"], sector_data)
    confidence = determine_confidence(provided, missing, market)

    rationale = generate_rationale(
        composite, recommendation, participation, bias, scores, missing, market
    )

    # Build result
    now = datetime.now(timezone.utc)

    result = {
        "schema_version": "1.0",
        "market": market,
        "metadata": {"generated_at": now.isoformat(), "market": market},
        "generated_at": now.isoformat(),
        "exposure_ceiling_pct": exposure_ceiling,
        "bias": bias,
        "participation": participation,
        "recommendation": recommendation,
        "confidence": confidence,
        "composite_score": round(composite, 1),
        "component_scores": {f"{k}_score": v for k, v in scores.items() if v is not None},
        "inputs_provided": provided,
        "inputs_missing": missing,
        "rationale": rationale,
    }

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")

    # Write JSON (market-tagged so TH and US files never collide)
    json_path = args.output_dir / f"exposure_posture_{market}_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"JSON report: {json_path}")

    # Write markdown unless --json-only
    if not args.json_only:
        md_content = generate_markdown_report(result)
        md_path = args.output_dir / f"exposure_posture_{market}_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(md_content)
        print(f"Markdown report: {md_path}")

    # Print summary to stdout
    print(f"\nExposure Ceiling: {exposure_ceiling}%")
    print(f"Recommendation: {recommendation}")
    print(f"Bias: {bias}")
    print(f"Confidence: {confidence}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
