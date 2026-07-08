from __future__ import annotations

import logging
import math as _math
import re as _re
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


# DR pattern: TICKERnn.BK (e.g., BRKB80.BK, JPMUS06.BK, SNOW23.BK)
_DR_RE = _re.compile(r"^[A-Z]+\d{2}\.BK$")


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
    base = symbol.replace(".BK", "")
    # Rights: TICKER.R.BK (e.g., KWM.R.BK, PTT.R.BK)
    if base.endswith(".R.BK"):
        return True
    # Warrants: TICKER-Wn
    if base.endswith(("-W", "-W1", "-W2", "-W3", "-W4", "-W5", "-R")):
        return True
    return False


def filter_common_stocks(stocks: list[dict]) -> list[dict]:
    """Remove DR certificates, warrants, and rights from a list."""
    return [s for s in stocks if not _is_dr_or_warrant(s["symbol"])]