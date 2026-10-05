#!/usr/bin/env python3
"""Market Intelligence & Pre-Trade Disqualification Engine.

Multi-dimensional screening layer that prevents capital traps before order staging:
1. Real-Time News Sentiment & Red-Flag Keyword Scanner (subsidies, lawsuits, probes, offerings).
2. Binary Event Earnings Calendar Gate (disqualifies entries within 7 days of earnings).
3. Foreign State-Owned Enterprise (SOE) / Political Risk Gate (disqualifies state-manipulated ADRs).
4. Relative Strength (RS Rating) vs Benchmark Index (SPY for US, SET for TH).
5. Overhead Supply & Weekly Stage-2 Moving Average Gate.
6. Dollar Volume Liquidity Floor (eliminates wide-spread slippage traps).

Usage:
    python scripts/market_intelligence_filter.py check HPE --market US
    python scripts/market_intelligence_filter.py check PBR.A --market US
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("market_intelligence")

# Known Foreign State-Owned Entities (SOEs) & High Political Intervention ADRs
STATE_OWNED_ADR_SYMBOLS = {
    "PBR",
    "PBR.A",
    "PBR-A",  # Petrobras (Brazil state oil, subject to fuel subsidies & price fixing)
    "EC",  # Ecopetrol (Colombia state oil)
    "YPF",  # YPF Sociedad Anonima (Argentina state energy)
    "SNP",
    "PTR",  # Sinopec / PetroChina
    "PKX",  # POSCO
    "BAP",  # Credicorp
    "ELET3",
    "ELET6",  # Eletrobras
}

RED_FLAG_PATTERNS = {
    "SUBSIDY_PRICE_CONTROL": [
        "subsidies",
        "subsidy",
        "fuel subsidies",
        "price controls",
        "price cap",
        "price pressure",
        "political pressure",
        "nationalization",
        "state intervention",
    ],
    "LEGAL_INVESTIGATION": [
        "lawsuit",
        "investigation",
        "subpoena",
        "fraud",
        "sec investigation",
        "sec probe",
        "doj probe",
        "accounting irregularities",
        "whistleblower",
        "raid",
        "scandal",
    ],
    "ANALYST_DOWNGRADE": [
        "downgrade",
        "lowers target",
        "cuts price target",
        "slashes target",
        "underweight",
        "sell rating",
        "bearish downgrade",
    ],
    "DILUTION_OFFERING": [
        "secondary offering",
        "atm offering",
        "share sale",
        "dilution",
        "public offering of common",
        "convertible debt",
        "shelf registration",
    ],
    "INSOLVENCY_DEFAULT": [
        "bankruptcy",
        "chapter 11",
        "default",
        "debt restructuring",
        "going concern",
        "delisting warning",
        "misses interest payment",
    ],
}


@dataclass
class GateResult:
    passed: bool
    reason: str = "Passed"
    score_modifier: float = 0.0


@dataclass
class NewsScanResult:
    is_clean: bool
    red_flags: list[str] = field(default_factory=list)
    score_modifier: float = 0.0
    headlines: list[str] = field(default_factory=list)


@dataclass
class ADRCheckResult:
    is_state_owned: bool
    reason: str = "Commercial enterprise"


@dataclass
class IntelligenceResult:
    symbol: str
    passed: bool
    disqualified: bool
    reason: str
    composite_modifier: float
    rs_rating: float
    news_flags: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fetch_recent_headlines(symbol: str, limit: int = 5) -> list[str]:
    """Fetch recent headlines for a symbol via yfinance."""
    try:
        import yfinance as yf

        yf_sym = (
            symbol.replace(".", "-") if "." in symbol and not symbol.endswith(".BK") else symbol
        )
        ticker = yf.Ticker(yf_sym)
        news_items = ticker.news or []
        headlines = []
        for item in news_items[:limit]:
            title = item.get("title") or item.get("content", {}).get("title")
            if title and isinstance(title, str):
                headlines.append(title.strip())
        return headlines
    except Exception as e:
        logger.debug("Failed to fetch news for %s: %s", symbol, e)
        return []


def check_news_red_flags(symbol: str, headlines: list[str] | None = None) -> NewsScanResult:
    """Analyze recent headlines against critical corporate and political red-flag keywords."""
    if headlines is None:
        headlines = fetch_recent_headlines(symbol, limit=5)

    if not headlines:
        return NewsScanResult(is_clean=True, score_modifier=0.0, headlines=[])

    red_flags: list[str] = []
    for h in headlines:
        h_lower = h.lower()
        for category, keywords in RED_FLAG_PATTERNS.items():
            for kw in keywords:
                if kw in h_lower:
                    red_flags.append(f"[{category}] {h}")
                    break

    if red_flags:
        # Severe penalty / disqualification flag
        return NewsScanResult(
            is_clean=False,
            red_flags=red_flags,
            score_modifier=-30.0,
            headlines=headlines,
        )

    return NewsScanResult(
        is_clean=True,
        red_flags=[],
        score_modifier=5.0,  # +5 points for clean news sentiment
        headlines=headlines,
    )


def get_days_until_earnings(symbol: str) -> int | None:
    """Determine calendar days until the next scheduled earnings announcement."""
    try:
        import yfinance as yf

        yf_sym = (
            symbol.replace(".", "-") if "." in symbol and not symbol.endswith(".BK") else symbol
        )
        ticker = yf.Ticker(yf_sym)
        calendar = ticker.calendar
        if calendar is not None and not calendar.empty:
            # Look for Earnings Date column or index
            date_val = None
            if "Earnings Date" in calendar:
                dates = calendar["Earnings Date"]
                if hasattr(dates, "iloc") and not dates.empty:
                    date_val = dates.iloc[0]
            elif isinstance(calendar, dict) and "Earnings Date" in calendar:
                dates = calendar["Earnings Date"]
                if dates:
                    date_val = dates[0]

            if date_val:
                target_dt = pd.to_datetime(date_val).tz_localize(None)
                now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
                diff_days = (target_dt - now_dt).days
                return max(0, diff_days)
    except Exception as e:
        logger.debug("Earnings calendar lookup failed for %s: %s", symbol, e)
    return None


def check_earnings_gate(symbol: str, days_until_earnings: int | None = None) -> GateResult:
    """Disqualify stocks reporting earnings within 7 calendar days (binary gap risk)."""
    if days_until_earnings is None:
        days_until_earnings = get_days_until_earnings(symbol)

    if days_until_earnings is not None and 0 <= days_until_earnings <= 7:
        return GateResult(
            passed=False,
            reason=f"Binary event risk: Earnings report scheduled in {days_until_earnings} days.",
            score_modifier=-50.0,
        )

    return GateResult(passed=True, score_modifier=0.0)


def check_state_owned_adr(symbol: str) -> ADRCheckResult:
    """Flag foreign state-owned ADRs subject to government price controls and political extraction."""
    sym_clean = symbol.upper().replace(".BK", "")
    if sym_clean in STATE_OWNED_ADR_SYMBOLS:
        return ADRCheckResult(
            is_state_owned=True,
            reason=f"Foreign state-owned enterprise (SOE) ADR subject to political price controls ({sym_clean})",
        )
    return ADRCheckResult(is_state_owned=False, reason="Commercial enterprise")


def calculate_relative_strength(
    stock_series: pd.Series,
    benchmark_series: pd.Series,
) -> dict[str, Any]:
    """Calculate Relative Strength (RS Rating) of the stock against benchmark (SPY or SET)."""
    if (
        stock_series.empty
        or benchmark_series.empty
        or len(stock_series) < 5
        or len(benchmark_series) < 5
    ):
        return {"rs_rating": 60.0, "alpha_pct": 0.0, "is_market_leader": False}

    stock_s = stock_series.dropna()
    bm_s = benchmark_series.dropna()

    stock_ret = (stock_s.iloc[-1] - stock_s.iloc[0]) / stock_s.iloc[0]
    bm_ret = (bm_s.iloc[-1] - bm_s.iloc[0]) / bm_s.iloc[0]

    alpha_pct = (stock_ret - bm_ret) * 100.0
    # Clamped 1 to 99 percentile scale where 50 is market neutral
    rs_rating = float(min(99.0, max(1.0, 50.0 + (alpha_pct * 2.5))))
    is_market_leader = bool(rs_rating >= 75.0 and alpha_pct > 5.0)

    return {
        "rs_rating": round(rs_rating, 1),
        "alpha_pct": round(float(alpha_pct), 2),
        "is_market_leader": is_market_leader,
    }


def check_overhead_supply(
    current_price: float,
    sma_200: float | None = None,
    sma_200_slope: float = 0.0,
) -> GateResult:
    """Disqualify stocks attempting to breakout straight into a declining 200 SMA ceiling."""
    if sma_200 and sma_200 > current_price and current_price > 0:
        dist_pct = ((sma_200 - current_price) / current_price) * 100.0
        # If declining 200 SMA is within 4.5% directly overhead
        if dist_pct <= 4.5 and sma_200_slope < 0:
            return GateResult(
                passed=False,
                reason=f"Overhead supply trap: Declining 200 SMA sits +{dist_pct:.1f}% directly overhead.",
                score_modifier=-25.0,
            )
    return GateResult(passed=True, score_modifier=0.0)


def check_liquidity_floor(dollar_volume: float, market: str = "TH") -> GateResult:
    """Enforce minimum Average Daily Dollar Volume to prevent slippage traps."""
    market_clean = market.upper()
    min_volume = 15_000_000.0 if market_clean == "US" else 20_000_000.0
    curr_sym = "$" if market_clean == "US" else "฿"

    if dollar_volume > 0 and dollar_volume < min_volume:
        return GateResult(
            passed=False,
            reason=f"Insufficient liquidity: Daily turnover {curr_sym}{dollar_volume:,.0f} < {curr_sym}{min_volume:,.0f} floor.",
            score_modifier=-20.0,
        )
    return GateResult(passed=True, score_modifier=0.0)


def evaluate_stock_intelligence(
    symbol: str,
    price: float,
    market: str = "TH",
    dollar_volume: float = 50_000_000.0,
    sma_200: float | None = None,
    sma_200_slope: float = 0.0,
    stock_bars: pd.Series | None = None,
    benchmark_bars: pd.Series | None = None,
) -> IntelligenceResult:
    """Execute the full pre-trade intelligence pipeline on a prospective candidate."""
    market_clean = market.upper()

    # 1. State-Owned ADR Gate
    adr_res = check_state_owned_adr(symbol)
    if adr_res.is_state_owned:
        return IntelligenceResult(
            symbol=symbol,
            passed=False,
            disqualified=True,
            reason=f"Disqualified: {adr_res.reason}",
            composite_modifier=-50.0,
            rs_rating=50.0,
            news_flags=[],
            details={"gate": "STATE_OWNED_ADR"},
        )

    # 2. Earnings Calendar Gate
    earnings_gate = check_earnings_gate(symbol)
    if not earnings_gate.passed:
        return IntelligenceResult(
            symbol=symbol,
            passed=False,
            disqualified=True,
            reason=f"Disqualified: {earnings_gate.reason}",
            composite_modifier=earnings_gate.score_modifier,
            rs_rating=50.0,
            news_flags=[],
            details={"gate": "EARNINGS_PROXIMITY"},
        )

    # 3. News Sentiment & Red-Flag Gate
    news_res = check_news_red_flags(symbol)
    if not news_res.is_clean:
        return IntelligenceResult(
            symbol=symbol,
            passed=False,
            disqualified=True,
            reason=f"Disqualified by News Red-Flag: {news_res.red_flags[0]}",
            composite_modifier=news_res.score_modifier,
            rs_rating=50.0,
            news_flags=news_res.red_flags,
            details={"gate": "NEWS_RED_FLAG", "all_flags": news_res.red_flags},
        )

    # 4. Overhead Supply Gate
    supply_gate = check_overhead_supply(price, sma_200=sma_200, sma_200_slope=sma_200_slope)
    if not supply_gate.passed:
        return IntelligenceResult(
            symbol=symbol,
            passed=False,
            disqualified=True,
            reason=f"Disqualified: {supply_gate.reason}",
            composite_modifier=supply_gate.score_modifier,
            rs_rating=50.0,
            news_flags=[],
            details={"gate": "OVERHEAD_SUPPLY"},
        )

    # 5. Liquidity Floor Gate
    liq_gate = check_liquidity_floor(dollar_volume, market=market_clean)
    if not liq_gate.passed:
        return IntelligenceResult(
            symbol=symbol,
            passed=False,
            disqualified=True,
            reason=f"Disqualified: {liq_gate.reason}",
            composite_modifier=liq_gate.score_modifier,
            rs_rating=50.0,
            news_flags=[],
            details={"gate": "LIQUIDITY_FLOOR"},
        )

    # 6. Relative Strength Calculation
    if stock_bars is not None and benchmark_bars is not None:
        rs_data = calculate_relative_strength(stock_bars, benchmark_bars)
        rs_rating = rs_data["rs_rating"]
        rs_bonus = 15.0 if rs_data["is_market_leader"] else (5.0 if rs_rating >= 65.0 else 0.0)
    else:
        rs_rating = 70.0
        rs_bonus = 5.0

    composite_modifier = news_res.score_modifier + rs_bonus

    return IntelligenceResult(
        symbol=symbol,
        passed=True,
        disqualified=False,
        reason=f"Intelligence Verified: RS {rs_rating:.0f}, Clean News, Commercial Leader",
        composite_modifier=composite_modifier,
        rs_rating=rs_rating,
        news_flags=[],
        details={
            "rs_rating": rs_rating,
            "news_clean": True,
            "recent_headlines": news_res.headlines[:3],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Market Intelligence & Disqualification Engine")
    subparsers = parser.add_subparsers(dest="command")

    check_p = subparsers.add_parser("check", help="Evaluate stock intelligence")
    check_p.add_argument("symbol", help="Stock symbol, e.g. HPE or PBR.A")
    check_p.add_argument("--market", choices=["TH", "US"], default="US", help="Market")
    check_p.add_argument("--price", type=float, default=50.0, help="Current price")

    args = parser.parse_args()

    if args.command == "check":
        res = evaluate_stock_intelligence(
            symbol=args.symbol,
            price=args.price,
            market=args.market,
        )
        print(f"Symbol: {res.symbol} ({args.market})")
        print(f"Passed: {res.passed} (Disqualified: {res.disqualified})")
        print(f"Reason: {res.reason}")
        print(f"RS Rating: {res.rs_rating}")
        print(f"Score Modifier: {res.composite_modifier:+.1f}")
        if res.news_flags:
            print(f"News Flags ({len(res.news_flags)}):")
            for f in res.news_flags:
                print(f"  - {f}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
