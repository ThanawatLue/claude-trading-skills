#!/usr/bin/env python3
"""
C Component - Current Quarterly Earnings Calculator

Calculates CANSLIM 'C' component score based on quarterly EPS and revenue growth.

O'Neil's Rule: "Look for companies whose current quarterly earnings per share
are up at least 18-20% compared to the same quarter the prior year."

Scoring:
- 100 points: EPS +50%+ YoY AND Revenue +25%+ YoY (explosive growth)
- 80 points: EPS +30-49% AND Revenue +15%+ (strong growth)
- 60 points: EPS +18-29% AND Revenue +10%+ (meets CANSLIM minimum)
- 40 points: EPS +10-17% (below threshold)
- 0 points: EPS <10% or negative
"""


def find_year_ago_quarter_index(income_statements: list[dict], base_index: int) -> int:
    """Find index of the quarter closest to 365 days before the base_index quarter.
    Falls back to base_index + 4 if no matches found or errors occur.
    """
    from datetime import datetime, timedelta
    
    if base_index >= len(income_statements):
        return base_index + 4
        
    base_date_str = income_statements[base_index].get("date")
    if not base_date_str:
        return base_index + 4
        
    try:
        base_date = datetime.strptime(base_date_str[:10], "%Y-%m-%d")
    except ValueError:
        return base_index + 4
        
    target_date = base_date - timedelta(days=365)
    best_index = base_index + 4
    best_diff = float("inf")
    
    for i in range(base_index + 1, len(income_statements)):
        date_str = income_statements[i].get("date")
        if not date_str:
            continue
        try:
            date_val = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            continue
            
        diff = abs((base_date - date_val).days - 365)
        # We want it to be reasonably close to 365 days, e.g. within 60 days
        if diff < 60 and diff < best_diff:
            best_diff = diff
            best_index = i
            
    return best_index


def calculate_quarterly_growth(income_statements: list[dict]) -> dict:
    """
    Calculate quarterly EPS and revenue growth (year-over-year)

    Args:
        income_statements: List of quarterly income statements from FMP API
                          (most recent quarter first, needs at least 5 quarters)

    Returns:
        Dict with:
            - score: 0-100 points
            - latest_qtr_eps_growth: YoY EPS growth percentage
            - latest_qtr_revenue_growth: YoY revenue growth percentage
            - latest_eps: Most recent quarterly EPS
            - year_ago_eps: EPS from same quarter last year
            - latest_revenue: Most recent quarterly revenue
            - year_ago_revenue: Revenue from same quarter last year
            - interpretation: Human-readable interpretation
            - error: Error message if calculation failed

    Example:
        >>> income_stmts = client.get_income_statement("NVDA", period="quarter", limit=8)
        >>> result = calculate_quarterly_growth(income_stmts)
        >>> print(f"C Score: {result['score']}, EPS Growth: {result['latest_qtr_eps_growth']:.1f}%")
    """
    # Validate input
    if not income_statements or len(income_statements) < 5:
        return {
            "score": 0,
            "error": "Insufficient quarterly data (need at least 5 quarters for YoY comparison)",
            "latest_qtr_eps_growth": None,
            "latest_qtr_revenue_growth": None,
            "latest_eps": None,
            "year_ago_eps": None,
            "latest_revenue": None,
            "year_ago_revenue": None,
            "interpretation": "Data unavailable",
        }

    # Extract most recent quarter (index 0) and year-ago quarter (dynamic search)
    latest = income_statements[0]
    year_ago_idx = find_year_ago_quarter_index(income_statements, 0)
    if year_ago_idx is None or year_ago_idx >= len(income_statements):
        return {
            "score": 0,
            "error": "Insufficient quarterly data (cannot find year-ago quarter)",
            "latest_qtr_eps_growth": None,
            "latest_qtr_revenue_growth": None,
            "latest_eps": None,
            "year_ago_eps": None,
            "latest_revenue": None,
            "year_ago_revenue": None,
            "interpretation": "Data unavailable",
        }
    year_ago = income_statements[year_ago_idx]

    # Extract EPS (try multiple field names for compatibility)
    latest_eps = latest.get("eps") or latest.get("epsdiluted") or latest.get("netIncomePerShare")
    year_ago_eps = (
        year_ago.get("eps") or year_ago.get("epsdiluted") or year_ago.get("netIncomePerShare")
    )

    # Extract revenue
    latest_revenue = latest.get("revenue")
    year_ago_revenue = year_ago.get("revenue")

    # Validate extracted data
    if latest_eps is None or year_ago_eps is None:
        return {
            "score": 0,
            "error": "EPS data missing or invalid",
            "latest_qtr_eps_growth": None,
            "latest_qtr_revenue_growth": None,
            "latest_eps": latest_eps,
            "year_ago_eps": year_ago_eps,
            "latest_revenue": latest_revenue,
            "year_ago_revenue": year_ago_revenue,
            "interpretation": "EPS data unavailable",
        }

    if latest_revenue is None or year_ago_revenue is None or year_ago_revenue == 0:
        return {
            "score": 0,
            "error": "Revenue data missing or invalid",
            "latest_qtr_eps_growth": None,
            "latest_qtr_revenue_growth": None,
            "latest_eps": latest_eps,
            "year_ago_eps": year_ago_eps,
            "latest_revenue": latest_revenue,
            "year_ago_revenue": year_ago_revenue,
            "interpretation": "Revenue data unavailable",
        }

    # Calculate year-over-year growth
    # Use abs() for denominator to handle negative EPS (turnaround situations)
    if year_ago_eps == 0:
        # Handle zero/negative EPS edge case
        if latest_eps > 0 and year_ago_eps <= 0:
            # Turnaround situation (negative to positive)
            eps_growth = 500.0  # Cap at high growth
        else:
            eps_growth = 0
    else:
        eps_growth = ((latest_eps - year_ago_eps) / abs(year_ago_eps)) * 100
        if eps_growth > 500.0:
            eps_growth = 500.0  # Cap EPS growth outlier at 500%

    revenue_growth = ((latest_revenue - year_ago_revenue) / year_ago_revenue) * 100

    # Detect earnings acceleration trend
    accel_data = detect_earnings_acceleration(income_statements)
    accel_trend = accel_data.get("trend", "stable")

    # Calculate base score using additive model
    score = score_current_earnings(eps_growth, revenue_growth)

    # Apply acceleration bonus (+10) or penalty (-10)
    if accel_trend == "accelerating":
        score = min(score + 10, 100)
    elif accel_trend == "decelerating":
        score = max(score - 10, 0)

    # Generate base interpretation
    interpretation = interpret_earnings_score(score, eps_growth, revenue_growth)
    if accel_data.get("interpretation"):
        interpretation += f" | {accel_data['interpretation']}"

    # Quality check: flag if revenue growth significantly lags EPS growth
    quality_warning = None
    if revenue_growth < (eps_growth * 0.5) and eps_growth > 20:
        # If it's a massive turnaround (EPS > 100%), relax the warning since revenue lagging is normal initially
        if eps_growth < 100.0:
            quality_warning = (
                "Revenue growth significantly lags EPS growth - "
                "investigate earnings quality (potential buyback-driven)"
            )

    return {
        "score": score,
        "latest_qtr_eps_growth": round(eps_growth, 1),
        "latest_qtr_revenue_growth": round(revenue_growth, 1),
        "latest_eps": latest_eps,
        "year_ago_eps": year_ago_eps,
        "latest_revenue": latest_revenue,
        "year_ago_revenue": year_ago_revenue,
        "latest_qtr_date": latest.get("date"),
        "year_ago_qtr_date": year_ago.get("date"),
        "interpretation": interpretation,
        "quality_warning": quality_warning,
        "error": None,
        "acceleration_trend": accel_trend,
        "acceleration_details": accel_data.get("interpretation", ""),
    }


def score_current_earnings(eps_growth: float, revenue_growth: float) -> int:
    """
    Score C component based on quarterly EPS and revenue growth (Additive Model)

    Args:
        eps_growth: Year-over-year EPS growth percentage (capped)
        revenue_growth: Year-over-year revenue growth percentage

    Returns:
        Score (0-100)
    """
    # 1. Base score from EPS growth
    if eps_growth >= 50:
        base_score = 75
    elif eps_growth >= 30:
        base_score = 60
    elif eps_growth >= 18:
        base_score = 50
    elif eps_growth >= 10:
        base_score = 30
    else:
        base_score = 0

    # If EPS growth is negative or very weak, do not grant revenue bonus
    if base_score == 0:
        return 0

    # 2. Additive bonus from Revenue growth
    if revenue_growth >= 25:
        bonus = 25
    elif revenue_growth >= 15:
        bonus = 20
    elif revenue_growth >= 10:
        bonus = 10
    elif revenue_growth >= 5:
        bonus = 5
    else:
        bonus = 0

    score = base_score + bonus
    return min(score, 100)


def interpret_earnings_score(score: int, eps_growth: float, revenue_growth: float) -> str:
    """
    Generate human-readable interpretation of C component score

    Args:
        score: Component score (0-100)
        eps_growth: YoY EPS growth percentage
        revenue_growth: YoY revenue growth percentage

    Returns:
        Interpretation string
    """
    if score >= 90:
        return (
            f"Exceptional - Explosive earnings acceleration "
            f"(EPS +{eps_growth:.1f}%, Revenue +{revenue_growth:.1f}%)"
        )

    elif score >= 70:
        return (
            f"Strong - Well above CANSLIM threshold "
            f"(EPS +{eps_growth:.1f}%, Revenue +{revenue_growth:.1f}%)"
        )

    elif score >= 50:
        return (
            f"Acceptable - Meets CANSLIM minimum 18% threshold "
            f"(EPS +{eps_growth:.1f}%, Revenue +{revenue_growth:.1f}%)"
        )

    elif score >= 30:
        return (
            f"Below threshold - Insufficient growth "
            f"(EPS +{eps_growth:.1f}%, Revenue +{revenue_growth:.1f}%)"
        )

    else:
        return (
            f"Weak - Does not meet CANSLIM criteria "
            f"(EPS {eps_growth:+.1f}%, Revenue {revenue_growth:+.1f}%)"
        )


def detect_earnings_acceleration(income_statements: list[dict]) -> dict:
    """
    Detect if earnings are accelerating or decelerating (trend analysis)

    Args:
        income_statements: List of quarterly income statements (recent first)

    Returns:
        Dict with:
            - trend: "accelerating", "stable", or "decelerating"
            - recent_growth: Most recent quarter YoY growth
            - prior_growth: Prior quarter YoY growth
            - interpretation: Trend description

    Note:
        Earnings acceleration (recent > prior) is bullish signal per O'Neil.
        Deceleration is early warning of potential weakness.
    """
    if len(income_statements) < 6:
        return {
            "trend": "unknown",
            "recent_growth": None,
            "prior_growth": None,
            "interpretation": "Insufficient data for trend analysis",
        }

    # Helper to extract EPS safely
    def _get_eps(stmt):
        if not stmt:
            return 0.0
        val = stmt.get("eps")
        if val is None:
            val = stmt.get("epsdiluted")
        if val is None:
            val = stmt.get("netIncomePerShare")
        return float(val) if val is not None else 0.0

    # Most recent quarter vs year-ago
    recent_eps = _get_eps(income_statements[0])
    recent_year_ago_idx = find_year_ago_quarter_index(income_statements, 0)
    if recent_year_ago_idx is None or recent_year_ago_idx >= len(income_statements):
        return {
            "trend": "unknown",
            "recent_growth": None,
            "prior_growth": None,
            "interpretation": "Insufficient data for trend analysis",
        }
    recent_year_ago_eps = _get_eps(income_statements[recent_year_ago_idx])
    
    if recent_year_ago_eps == 0:
        recent_growth = 500.0 if recent_eps > 0 else 0.0
    else:
        recent_growth = ((recent_eps - recent_year_ago_eps) / abs(recent_year_ago_eps)) * 100
        if recent_growth > 500.0:
            recent_growth = 500.0

    # Prior quarter vs its year-ago
    prior_eps = _get_eps(income_statements[1])
    prior_year_ago_idx = find_year_ago_quarter_index(income_statements, 1)
    if prior_year_ago_idx is None or prior_year_ago_idx >= len(income_statements):
        return {
            "trend": "unknown",
            "recent_growth": None,
            "prior_growth": None,
            "interpretation": "Insufficient data for trend analysis",
        }
    prior_year_ago_eps = _get_eps(income_statements[prior_year_ago_idx])
    
    if prior_year_ago_eps == 0:
        prior_growth = 500.0 if prior_eps > 0 else 0.0
    else:
        prior_growth = ((prior_eps - prior_year_ago_eps) / abs(prior_year_ago_eps)) * 100
        if prior_growth > 500.0:
            prior_growth = 500.0

    # Determine trend
    if recent_growth > prior_growth + 5:  # 5% threshold for significance
        trend = "accelerating"
        interpretation = (
            f"Earnings accelerating ({recent_growth:.1f}% vs {prior_growth:.1f}% prior quarter)"
        )
    elif recent_growth < prior_growth - 5:
        trend = "decelerating"
        interpretation = f"Earnings decelerating ({recent_growth:.1f}% vs {prior_growth:.1f}% prior quarter) - Warning sign"
    else:
        trend = "stable"
        interpretation = (
            f"Earnings stable ({recent_growth:.1f}% vs {prior_growth:.1f}% prior quarter)"
        )

    return {
        "trend": trend,
        "recent_growth": round(recent_growth, 1),
        "prior_growth": round(prior_growth, 1),
        "interpretation": interpretation,
    }


# Example usage and testing
if __name__ == "__main__":
    print("Testing Earnings Calculator (C Component)...\n")

    # Test case 1: Exceptional growth (should score 100)
    test_data_exceptional = [
        {"date": "2023-06-30", "eps": 2.70, "revenue": 13507000000},  # Q2 2023
        {"date": "2023-03-31", "eps": 1.09, "revenue": 7192000000},
        {"date": "2022-12-31", "eps": 0.88, "revenue": 6051000000},
        {"date": "2022-09-30", "eps": 0.58, "revenue": 5931000000},
        {"date": "2022-06-30", "eps": 0.51, "revenue": 6704000000},  # Q2 2022 (year-ago)
    ]

    result1 = calculate_quarterly_growth(test_data_exceptional)
    print("Test 1: Exceptional Growth (NVDA-like)")
    print(f"  Score: {result1['score']}/100")
    print(f"  EPS Growth: {result1['latest_qtr_eps_growth']}%")
    print(f"  Revenue Growth: {result1['latest_qtr_revenue_growth']}%")
    print(f"  Interpretation: {result1['interpretation']}\n")

    # Test case 2: Meets minimum (should score 60)
    test_data_minimum = [
        {"date": "2023-06-30", "eps": 1.20, "revenue": 10500000000},
        {"date": "2023-03-31", "eps": 1.15, "revenue": 10200000000},
        {"date": "2022-12-31", "eps": 1.10, "revenue": 10000000000},
        {"date": "2022-09-30", "eps": 1.05, "revenue": 9800000000},
        {"date": "2022-06-30", "eps": 1.00, "revenue": 9500000000},  # +20% EPS, +10.5% revenue
    ]

    result2 = calculate_quarterly_growth(test_data_minimum)
    print("Test 2: Meets CANSLIM Minimum")
    print(f"  Score: {result2['score']}/100")
    print(f"  EPS Growth: {result2['latest_qtr_eps_growth']}%")
    print(f"  Revenue Growth: {result2['latest_qtr_revenue_growth']}%")
    print(f"  Interpretation: {result2['interpretation']}\n")

    # Test case 3: Below threshold (should score 40)
    test_data_weak = [
        {"date": "2023-06-30", "eps": 1.12, "revenue": 10200000000},
        {"date": "2023-03-31", "eps": 1.08, "revenue": 10100000000},
        {"date": "2022-12-31", "eps": 1.05, "revenue": 10000000000},
        {"date": "2022-09-30", "eps": 1.02, "revenue": 9900000000},
        {"date": "2022-06-30", "eps": 1.00, "revenue": 9800000000},  # +12% EPS, +4% revenue
    ]

    result3 = calculate_quarterly_growth(test_data_weak)
    print("Test 3: Below Threshold")
    print(f"  Score: {result3['score']}/100")
    print(f"  EPS Growth: {result3['latest_qtr_eps_growth']}%")
    print(f"  Revenue Growth: {result3['latest_qtr_revenue_growth']}%")
    print(f"  Interpretation: {result3['interpretation']}\n")

    # Test case 4: Turnaround (negative to positive EPS)
    test_data_turnaround = [
        {"date": "2023-06-30", "eps": 0.50, "revenue": 10000000000},
        {"date": "2023-03-31", "eps": 0.20, "revenue": 9500000000},
        {"date": "2022-12-31", "eps": -0.10, "revenue": 9000000000},
        {"date": "2022-09-30", "eps": -0.30, "revenue": 8500000000},
        {"date": "2022-06-30", "eps": -0.40, "revenue": 8000000000},  # Turnaround situation
    ]

    result4 = calculate_quarterly_growth(test_data_turnaround)
    print("Test 4: Turnaround (Negative to Positive)")
    print(f"  Score: {result4['score']}/100")
    print(f"  EPS Growth: {result4['latest_qtr_eps_growth']}%")
    print(f"  Revenue Growth: {result4['latest_qtr_revenue_growth']}%")
    print(f"  Interpretation: {result4['interpretation']}\n")

    # Test acceleration detection
    print("Test 5: Acceleration Detection")
    accel = detect_earnings_acceleration(test_data_exceptional)
    print(f"  Trend: {accel['trend']}")
    print(f"  Recent growth: {accel['recent_growth']}%")
    print(f"  Prior growth: {accel['prior_growth']}%")
    print(f"  Interpretation: {accel['interpretation']}")

    print("\n✓ All tests completed")
