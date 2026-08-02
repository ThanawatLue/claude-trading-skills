"""Yahoo Finance OHLCV client for IBD Distribution Day Monitor.

Drop-in replacement for FMPClient — only get_historical_prices() is needed.
Returns data in the same most-recent-first list[dict] format as FMPClient.
No API key required.

Caching:
  OHLCV bars stored in state/market_cache.db (project root, shared with other skills).
  - Fresh (≤1 day stale): served entirely from cache.
  - 2-7 days stale: only missing bars fetched.
  - >7 days stale or no data: full re-download (catches split/dividend adjustments).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
    sys.exit(1)

# ── Cache setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]   # skills/ibd-distribution-day-monitor/scripts -> skills/<name> -> skills -> trading
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from cache_manager import CacheManager  # noqa: E402

_DB_PATH = _PROJECT_ROOT / "state" / "market_cache.db"
_cache = CacheManager(_DB_PATH)


def _df_to_bars(df) -> list[dict]:
    """Convert a yfinance DataFrame to most-recent-first list[dict]."""
    bars = []
    for dt, row in df.iterrows():
        bars.append({
            "date": dt.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 4),
            "high": round(float(row["High"]), 4),
            "low": round(float(row["Low"]), 4),
            "close": round(float(row["Close"]), 4),
            "volume": int(row["Volume"]),
        })
    bars.reverse()  # most-recent first
    return bars


class YFClient:
    """Minimal Yahoo Finance client for IBD Distribution Day Monitor."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_calls = 0

    def get_historical_prices(self, symbol: str, days: int = 90) -> Optional[dict]:
        """Fetch daily OHLCV. Returns FMP-compatible dict {"symbol": ..., "historical": [...]}.

        Serves from cache when possible; only fetches missing bars.
        """
        bars = self._get_bars_incremental(symbol, days)
        if not bars:
            return None
        return {"symbol": symbol, "historical": bars}

    def _get_bars_incremental(self, symbol: str, days: int) -> list[dict]:
        from datetime import date as _date

        today = _date.today()

        if _cache.needs_full_refresh(symbol):
            return self._fetch_full(symbol, days)

        latest = _cache.latest_bar_date(symbol)
        behind = (today - latest).days

        if behind <= 1:
            return _cache.get_bars(symbol, days)

        # Partial update: fetch only missing days (+5 buffer for weekends)
        fetch_days = behind + 5
        self._api_calls += 1
        try:
            df = yf.Ticker(symbol).history(period=f"{int(fetch_days * 1.5)}d", auto_adjust=True)
            if not df.empty:
                new_bars = _df_to_bars(df)
                new_only = [b for b in new_bars if _date.fromisoformat(b["date"]) > latest]
                if new_only:
                    _cache.upsert_bars(symbol, new_only)
        except Exception as e:
            print(f"WARNING: partial fetch error for {symbol}: {e}", file=sys.stderr)

        return _cache.get_bars(symbol, days)

    def _fetch_full(self, symbol: str, days: int) -> list[dict]:
        period_days = int(days * 1.5)
        self._api_calls += 1
        try:
            df = yf.Ticker(symbol).history(period=f"{period_days}d", auto_adjust=True)
            if df.empty:
                return []
            df = df.tail(days)
            bars = _df_to_bars(df)
            _cache.upsert_bars(symbol, bars)
            return bars
        except Exception as e:
            print(f"WARNING: full fetch error for {symbol}: {e}", file=sys.stderr)
            return []
