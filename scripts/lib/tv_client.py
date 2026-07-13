#!/usr/bin/env python3
"""
TradingView Screener Client — Thai SET market enrichment.

Uses tradingview-screener (pip install tradingview-screener) to fetch
all SET stocks in a single API call with pre-computed technicals.
This is dramatically faster than fetching individual yfinance quotes
for the Thai universe and provides RSI, SMAs, sector, performance,
dividend, and fundamental data.

Optional dependency: tradingview-screener>=0.3.0
Falls back gracefully to an empty result if the package is not installed.

Public API:
    is_available()         → bool
    get_thai_stocks()      → list[dict]   (full SET universe)
    get_thai_set50()       → list[dict]   (SET50 proxy: top 50 by mcap)
    get_thai_set100()      → list[dict]   (SET100 proxy: top 100 by mcap)
    get_thai_sethd()       → list[dict]   (high-dividend: yield ≥ 3%, mcap ≥ 5B)
    get_thai_by_sector()   → list[dict]   (filter by sector name)
    get_thai_breadth()     → dict         (% above SMAs, A/D, RSI dist, etc.)
    filter_common_stocks() → list[dict]   (remove DRs + warrants)

Note: TradingView's Thailand scanner does NOT expose index_of(SET50/100/HD)
filters. SET50/100/HD helpers use market-cap and dividend-yield proxies.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_TV_AVAILABLE = False
try:
    from tradingview_screener import Query, col  # noqa: F401

    _TV_AVAILABLE = True
except ImportError:
    pass

# Core TradingView fields — keep stable; downstream code depends on these keys
_TV_FIELDS = [
    "name",
    "close",
    "volume",
    "market_cap_basic",
    "average_volume_10d_calc",
    # Technicals
    "RSI",
    "RSI|1W",
    "SMA10",
    "SMA20",
    "SMA50",
    "SMA200",
    "price_52_week_high",
    "price_52_week_low",
    "change",
    # Sector/industry
    "sector",
    "industry",
    # Performance (NEW — for RS rank and momentum scoring)
    "Perf.W",
    "Perf.1M",
    "Perf.3M",
    "Perf.6M",
    "Perf.Y",
    # Fundamentals (NEW — for value/dividend screeners)
    "dividend_yield_recent",
    "price_earnings_ttm",
    "price_book_fq",
    "earnings_per_share_basic_ttm",
    # Float / liquidity (NEW)
    "total_shares_outstanding_current",
]


def is_available() -> bool:
    """Return True if tradingview-screener is installed."""
    return _TV_AVAILABLE


# ---------------------------------------------------------------------------
# Row → dict adapter (shared by all helpers)
# ---------------------------------------------------------------------------

_LIQUIDITY_SCORE_FULL_THB = 50_000_000


def _safe_float(value) -> float:
    """Return value as float, treating None/NaN/non-numeric values as 0."""
    try:
        n = float(value) if value is not None else 0.0
        return 0.0 if n != n else n
    except (TypeError, ValueError):
        return 0.0


def _turnover_value(price, volume) -> float:
    """Approximate traded value in THB from price and share volume."""
    return _safe_float(price) * _safe_float(volume)


def _liquidity_score(avg_turnover: float) -> float:
    """Normalize average turnover to a 0-100 score for Thai screening."""
    if avg_turnover <= 0:
        return 0.0
    return round(min(100.0, avg_turnover / _LIQUIDITY_SCORE_FULL_THB * 100), 2)


def _row_to_stock(row) -> dict:
    """Convert a TradingView row to a yfinance-compatible quote dict."""
    ticker = row.get("ticker", "")
    raw = ticker.replace("SET:", "").replace("MAI:", "")
    symbol = f"{raw}.BK"

    board = "MAI" if ticker.startswith("MAI:") else "SET"
    price = _safe_float(row.get("close"))
    volume = _safe_float(row.get("volume"))
    avg_volume = _safe_float(row.get("average_volume_10d_calc"))
    turnover = _turnover_value(price, volume)
    avg_turnover = _turnover_value(price, avg_volume)

    return {
        "symbol": symbol,
        "name": row.get("name", raw),
        "sector": row.get("sector") or "Unknown",
        "industry": row.get("industry") or "Unknown",
        "board": board,
        # Quote-compatible fields (used by pre_filter_stock and downstream)
        "price": price,
        "yearHigh": row.get("price_52_week_high") or 0,
        "yearLow": row.get("price_52_week_low") or 0,
        "avgVolume": avg_volume,
        "volume": volume,
        "marketCap": row.get("market_cap_basic") or 0,
        # Technicals
        "rsi": row.get("RSI"),
        "rsi_weekly": row.get("RSI|1W"),
        "sma10": row.get("SMA10"),
        "sma20": row.get("SMA20"),
        "sma50": row.get("SMA50"),
        "sma200": row.get("SMA200"),
        "change_pct": row.get("change"),
        # Performance (NEW)
        "perf_w": row.get("Perf.W"),
        "perf_1m": row.get("Perf.1M"),
        "perf_3m": row.get("Perf.3M"),
        "perf_6m": row.get("Perf.6M"),
        "perf_y": row.get("Perf.Y"),
        # Fundamentals (NEW)
        "dividend_yield": row.get("dividend_yield_recent"),
        "pe_ratio": row.get("price_earnings_ttm"),
        "pb_ratio": row.get("price_book_fq"),
        "eps_ttm": row.get("earnings_per_share_basic_ttm"),
        # Liquidity (NEW)
        "shares_outstanding": row.get("total_shares_outstanding_current"),
        "turnover": turnover,
        "avg_turnover": avg_turnover,
        "liquidity_score": _liquidity_score(avg_turnover),
        "_source": "tradingview",
    }


def _safe_query(builder_fn, label: str) -> list[dict]:
    """Run a TV query and convert rows; return [] on any failure."""
    if not _TV_AVAILABLE:
        logger.warning(
            "tradingview-screener not installed. Run: pip install tradingview-screener"
        )
        return []
    try:
        n, df = builder_fn().get_scanner_data()
        logger.info("TradingView: fetched %d rows for %s", n, label)
        return [_row_to_stock(row) for _, row in df.iterrows()]
    except Exception as e:
        logger.error("TradingView %s query error: %s", label, e)
        return []


# ---------------------------------------------------------------------------
# Universe fetchers
# ---------------------------------------------------------------------------

def get_thai_stocks(
    limit: int = 1000,
    min_market_cap: Optional[float] = None,
    min_avg_volume: Optional[float] = None,
) -> list[dict]:
    """Fetch full Thai market (SET + MAI) with technicals and fundamentals."""
    def build():
        q = Query().set_markets("thailand").select(*_TV_FIELDS).limit(limit)
        if min_market_cap is not None:
            q = q.where(col("market_cap_basic") > min_market_cap)
        if min_avg_volume is not None:
            q = q.where(col("average_volume_10d_calc") > min_avg_volume)
        return q
    return _safe_query(build, "thai_full")


# NOTE: TradingView's Thailand scanner does not expose index_of(SET50/100/HD)
# filters (those work only on US markets). We approximate via market-cap and
# liquidity ranking on the full SET+MAI universe.

_MIN_LIQ_SET50_THB = 50_000_000   # avg 10d volume value floor (very rough)


def get_thai_set50(limit: int = 50) -> list[dict]:
    """SET50 proxy: top 50 by market cap with liquidity filter on Main board."""
    full = get_thai_stocks(limit=1000)
    main = [s for s in full if s.get("board") == "SET"]
    main.sort(key=lambda s: s.get("marketCap") or 0, reverse=True)
    return main[:limit]


def get_thai_set100(limit: int = 100) -> list[dict]:
    """SET100 proxy: top 100 by market cap on Main board."""
    full = get_thai_stocks(limit=1000)
    main = [s for s in full if s.get("board") == "SET"]
    main.sort(key=lambda s: s.get("marketCap") or 0, reverse=True)
    return main[:limit]


def get_thai_sethd(limit: int = 30) -> list[dict]:
    """SETHD proxy: top N by dividend yield, min mcap 5B THB, min yield 3%."""
    full = get_thai_stocks(limit=1000)
    pool = [
        s for s in full
        if s.get("board") == "SET"
        and (s.get("dividend_yield") or 0) >= 3.0
        and (s.get("marketCap") or 0) >= 5_000_000_000
    ]
    pool.sort(key=lambda s: s.get("dividend_yield") or 0, reverse=True)
    return pool[:limit]


import re as _re

# DR pattern: TICKERnn.BK (e.g., BRKB80.BK, JPMUS06.BK, SNOW23.BK)
_DR_RE = _re.compile(r"^[A-Z]+\d{2}\.BK$")


import math as _math


def clean_for_json(obj):
    """
    Recursively replace NaN / +Inf / -Inf with None so the output is valid JSON.

    JavaScript's JSON.parse() rejects NaN/Infinity, so we must scrub them before
    writing to disk or sending to a browser.
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(clean_for_json(v) for v in obj)
    if isinstance(obj, float):
        if _math.isnan(obj) or _math.isinf(obj):
            return None
        return obj
    return obj


def _is_dr_or_warrant(symbol: str) -> bool:
    """Detect Thai Depository Receipts (DRs), warrants, and rights."""
    if _DR_RE.match(symbol):
        return True
    # Rights: TICKER.R.BK (e.g., KWM.R.BK, PTT.R.BK)
    if symbol.endswith(".R.BK"):
        return True
    base = symbol.replace(".BK", "")
    # Warrants: TICKER-Wn
    if base.endswith(("-W", "-W1", "-W2", "-W3", "-W4", "-W5", "-R")):
        return True
    return False


def filter_common_stocks(stocks: list[dict]) -> list[dict]:
    """Remove DR certificates, warrants, and rights from a list."""
    return [s for s in stocks if not _is_dr_or_warrant(s["symbol"])]


def get_set_memberships() -> dict[str, set[str]]:
    """
    Return SET50 / SET100 / SETHD membership sets (proxy-based).

    Returns:
        dict with keys 'set50', 'set100', 'sethd' → set of symbols (e.g., 'PTT.BK')

    Cached at call time — call sparingly (issues 3 separate TV queries).
    """
    return {
        "set50": {s["symbol"] for s in get_thai_set50()},
        "set100": {s["symbol"] for s in get_thai_set100()},
        "sethd": {s["symbol"] for s in get_thai_sethd()},
    }


def tag_with_memberships(stocks: list[dict],
                         memberships: dict[str, set[str]] | None = None) -> list[dict]:
    """
    Add SET membership tags to a list of stock dicts (in-place compatible).

    Each stock gains:
        set_membership: list[str]   e.g., ["SET50", "SET100"]
        is_set50:   bool
        is_set100:  bool
        is_sethd:   bool

    Args:
        stocks: list of stock dicts with 'symbol' key
        memberships: pre-fetched memberships dict (saves API calls); if None,
                     fetches fresh memberships internally.
    """
    if memberships is None:
        memberships = get_set_memberships()
    for s in stocks:
        sym = s.get("symbol")
        if not sym:
            continue
        s["is_set50"] = sym in memberships.get("set50", set())
        s["is_set100"] = sym in memberships.get("set100", set())
        s["is_sethd"] = sym in memberships.get("sethd", set())
        tags = []
        if s["is_set50"]:
            tags.append("SET50")
        elif s["is_set100"]:
            tags.append("SET100")
        if s["is_sethd"]:
            tags.append("SETHD")
        s["set_membership"] = tags
    return stocks


def get_thai_by_sector(sector_name: str, limit: int = 200,
                       exclude_drs: bool = True) -> list[dict]:
    """Filter Thai stocks by sector (e.g. 'Energy Minerals', 'Finance').
    By default excludes DR certificates (BRKB80.BK etc.) and warrants.
    Note: Finance/Tech sectors in TV are dominated by DRs of US stocks; we
    fetch a large pool then filter client-side to ensure adequate coverage."""
    def build():
        return (
            Query()
            .set_markets("thailand")
            .select(*_TV_FIELDS)
            .where(col("sector") == sector_name)
            .limit(1000)  # fetch all matching, filter client-side
        )
    out = _safe_query(build, f"sector:{sector_name}")
    if exclude_drs:
        out = filter_common_stocks(out)
    return out[:limit]


# ---------------------------------------------------------------------------
# Breadth snapshot — aggregate stats across the whole market
# ---------------------------------------------------------------------------

def get_thai_breadth(min_price: float = 1.0, limit: int = 1000) -> dict:
    """
    Compute market-breadth snapshot for Thai market in a single call.

    Returns a dict with:
        total_stocks            : count after price filter
        pct_above_sma50         : % of stocks with close > SMA50
        pct_above_sma200        : % of stocks with close > SMA200
        advancers / decliners   : count (change > 0 / < 0)
        new_52w_highs           : count within 2% of 52w high
        new_52w_lows            : count within 2% of 52w low
        rsi_oversold            : count with RSI < 30
        rsi_overbought          : count with RSI > 70
        median_rsi              : median daily RSI
        sector_breakdown        : dict[sector] → median Perf.1M
    """
    stocks = get_thai_stocks(limit=limit)
    stocks = [s for s in stocks if (s.get("price") or 0) >= min_price]
    n = len(stocks)
    if n == 0:
        return {"total_stocks": 0}

    def _pct(predicate) -> float:
        c = sum(1 for s in stocks if predicate(s))
        return round(c * 100.0 / n, 2)

    def _count(predicate) -> int:
        return sum(1 for s in stocks if predicate(s))

    def _median(values: list[float]) -> float:
        vs = sorted(v for v in values if v is not None)
        if not vs:
            return 0.0
        m = len(vs) // 2
        return float(vs[m] if len(vs) % 2 else (vs[m - 1] + vs[m]) / 2)

    # Sector breakdown — median Perf.1M per sector
    sectors: dict[str, list[float]] = {}
    for s in stocks:
        sec = s.get("sector") or "Unknown"
        p1m = s.get("perf_1m")
        if p1m is not None:
            sectors.setdefault(sec, []).append(p1m)
    sector_breakdown = {
        sec: round(_median(vals), 2)
        for sec, vals in sectors.items()
        if len(vals) >= 3  # need at least 3 stocks per sector to be meaningful
    }

    return {
        "total_stocks": n,
        "pct_above_sma50": _pct(
            lambda s: (s.get("price") or 0) > 0
            and (s.get("sma50") or 0) > 0
            and s["price"] > s["sma50"]
        ),
        "pct_above_sma200": _pct(
            lambda s: (s.get("price") or 0) > 0
            and (s.get("sma200") or 0) > 0
            and s["price"] > s["sma200"]
        ),
        "advancers": _count(lambda s: (s.get("change_pct") or 0) > 0),
        "decliners": _count(lambda s: (s.get("change_pct") or 0) < 0),
        "unchanged": _count(lambda s: (s.get("change_pct") or 0) == 0),
        "new_52w_highs": _count(
            lambda s: (s.get("yearHigh") or 0) > 0
            and (s.get("price") or 0) >= s["yearHigh"] * 0.98
        ),
        "new_52w_lows": _count(
            lambda s: (s.get("yearLow") or 0) > 0
            and (s.get("price") or 0) <= s["yearLow"] * 1.02
        ),
        "rsi_oversold": _count(lambda s: (s.get("rsi") or 50) < 30),
        "rsi_overbought": _count(lambda s: (s.get("rsi") or 50) > 70),
        "median_rsi": round(_median([s.get("rsi") for s in stocks]), 2),
        "median_perf_1m": round(_median([s.get("perf_1m") for s in stocks]), 2),
        "median_perf_3m": round(_median([s.get("perf_3m") for s in stocks]), 2),
        "sector_breakdown": dict(sorted(sector_breakdown.items(),
                                        key=lambda kv: kv[1], reverse=True)),
    }
