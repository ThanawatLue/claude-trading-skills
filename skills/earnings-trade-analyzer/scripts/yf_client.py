"""Yahoo Finance client for Earnings Trade Analyzer.

Drop-in replacement for FMPClient. No API key required.

Key differences vs FMPClient:
  - get_earnings_calendar(): scans S&P 500 via Wikipedia + concurrent yfinance calls.
    Slower than FMP (~30-60s for lookback 2-7 days) but free.
    Results cached 24 h in state/market_cache.db (earnings_scan table).
  - get_company_profiles(): uses yfinance fast_info; always passes US exchange check.
    Profiles cached 7 days (company_profile table).
  - get_historical_prices(): returns most-recent-first list[dict] (same as FMP).
    OHLCV cached with incremental updates (price_bar table).

Caching:
  All data stored in state/market_cache.db (project root, shared with other skills).

Thread safety: each worker creates its own yf.Ticker, safe for ThreadPoolExecutor.
"""

from __future__ import annotations

import html
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
    sys.exit(1)

try:
    import requests as _requests
except ImportError:
    _requests = None  # type: ignore

# ── Cache setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]   # skills/earnings-trade-analyzer/scripts -> skills/<name> -> skills -> trading
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from cache_manager import CacheManager  # noqa: E402

_DB_PATH = _PROJECT_ROOT / "state" / "market_cache.db"
_cache = CacheManager(_DB_PATH)

# Accepted US exchanges (mirrors FMPClient.US_EXCHANGES — kept for compatibility)
US_EXCHANGES = ["NYSE", "NASDAQ", "AMEX", "NYSEArca", "BATS", "NMS", "NGM", "NCM"]

# Worker threads for concurrent earnings-date scanning
_EARNINGS_WORKERS = 20
# Seconds to wait between yfinance calls per thread to avoid throttling
_THREAD_DELAY = 0.05


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
            "adjClose": round(float(row["Close"]), 4),
        })
    bars.reverse()  # most-recent first
    return bars


def _fetch_sp500_wikipedia() -> list[str]:
    """Return S&P 500 symbol list from Wikipedia. Returns [] on failure."""
    if _requests is None:
        return []
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; EarningsAnalyzer/1.0)"}
        resp = _requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        table_match = re.search(
            r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>',
            resp.text, re.DOTALL,
        )
        if not table_match:
            return []

        table_html = table_match.group(1)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL)

        def strip(s: str) -> str:
            return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

        symbols = []
        for row in rows[1:]:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)
            if cells:
                sym = strip(cells[0]).replace(".", "-")
                if sym:
                    symbols.append(sym)
        return symbols
    except Exception as e:
        print(f"WARNING: Wikipedia S&P500 fetch error: {e}", file=sys.stderr)
        return []


def _check_symbol_earnings(
    symbol: str,
    from_date: date,
    to_date: date,
) -> Optional[dict]:
    """Check if a symbol reported earnings in [from_date, to_date].

    Returns an earnings dict compatible with FMP's earning_calendar format,
    or None if no earnings found in the window.
    """
    time.sleep(_THREAD_DELAY)
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.get_earnings_dates(limit=8)
        if df is None or df.empty:
            return None

        for dt_idx in df.index:
            try:
                report_date = dt_idx.date() if hasattr(dt_idx, "date") else dt_idx
            except Exception:
                continue

            if from_date <= report_date <= to_date:
                row = df.loc[dt_idx]
                reported_eps = row.get("Reported EPS") if hasattr(row, "get") else None
                timing = "unknown"
                if reported_eps is not None and str(reported_eps) not in ("nan", "None", ""):
                    timing = "unknown"

                return {
                    "symbol": symbol,
                    "date": report_date.isoformat(),
                    "time": timing,
                }
    except Exception:
        pass
    return None


class YFClient:
    """Yahoo Finance replacement for FMPClient in Earnings Trade Analyzer."""

    # Expose for compatibility with analyze_earnings_trades.py exchange filter
    US_EXCHANGES = US_EXCHANGES

    def __init__(self, api_key: Optional[str] = None, max_api_calls: int = 9999):
        self._sp500_cache: Optional[list[str]] = None

    def _get_sp500(self) -> list[str]:
        if self._sp500_cache is not None:
            return self._sp500_cache

        # Check universe cache first (30-day TTL)
        cached = _cache.get_universe(ttl_days=30)
        if cached:
            print(f"  (S&P 500 list from cache: {len(cached)} stocks)", flush=True)
            self._sp500_cache = cached
            return cached

        print("  Fetching S&P 500 list from Wikipedia...", end=" ", flush=True)
        symbols = _fetch_sp500_wikipedia()
        if symbols:
            print(f"OK ({len(symbols)} stocks)")
            _cache.save_universe_symbols(symbols)
        else:
            print("WARN — using built-in top-100 fallback")
            symbols = [
                "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "BRK-B", "LLY",
                "AVGO", "JPM", "TSLA", "V", "UNH", "XOM", "MA", "JNJ", "PG", "COST", "HD",
                "NFLX", "ABBV", "BAC", "WMT", "ORCL", "CRM", "CVX", "MRK", "KO", "AMD",
                "PEP", "ACN", "LIN", "TMO", "MCD", "CSCO", "ABT", "ADBE", "PM", "GE",
                "QCOM", "TXN", "DHR", "IBM", "ISRG", "CAT", "INTU", "AMGN", "SPGI", "BKNG",
                "GS", "VZ", "AXP", "UNP", "CMCSA", "NOW", "LOW", "RTX", "MS", "NEE",
                "HON", "PFE", "UBER", "AMAT", "T", "BMY", "SYK", "SCHW", "C", "BLK",
                "ETN", "BA", "DE", "MDT", "ADP", "REGN", "VRTX", "GILD", "BSX", "ADI",
                "MMC", "MO", "PLD", "TJX", "ZTS", "PANW", "SBUX", "CB", "AMT", "SO",
                "LRCX", "CME", "CI", "DUK", "COP", "NOC", "WM", "FI", "MCO", "USB",
            ]
        self._sp500_cache = symbols
        return symbols

    # ── Earnings Calendar ────────────────────────────────────────────────────

    def get_earnings_calendar(self, from_date: str, to_date: str) -> Optional[list]:
        """Scan S&P 500 for stocks that reported earnings in [from_date, to_date].

        Results are cached 24 h per symbol in the earnings_scan table.
        On subsequent runs, only symbols without a cached result are re-scanned.

        Returns list of {"symbol": ..., "date": ..., "time": ...} dicts.
        """
        from_dt = date.fromisoformat(from_date)
        to_dt = date.fromisoformat(to_date)

        universe = self._get_sp500()

        # Split into cached vs needs-scan using 24-h TTL
        cached_results, need_scan = _cache.classify_earnings_symbols(universe, ttl_hours=24.0)

        if need_scan:
            print(
                f"  Scanning {len(need_scan)} stocks for earnings "
                f"{from_date} -> {to_date} ({_EARNINGS_WORKERS} workers)...",
                flush=True,
            )
        else:
            print(f"  Earnings scan: all {len(universe)} stocks served from cache.", flush=True)

        fresh_results = []
        completed = 0

        if need_scan:
            with ThreadPoolExecutor(max_workers=_EARNINGS_WORKERS) as executor:
                futures = {
                    executor.submit(_check_symbol_earnings, sym, from_dt, to_dt): sym
                    for sym in need_scan
                }
                for future in as_completed(futures):
                    completed += 1
                    if completed % 50 == 0:
                        print(f"    Scanned {completed}/{len(need_scan)}...", flush=True)
                    sym = futures[future]
                    result = future.result()
                    _cache.save_earnings_scan(sym, result)
                    if result:
                        fresh_results.append(result)

        # Filter cached results to the requested window
        window_cached = [
            r for r in cached_results
            if from_dt <= date.fromisoformat(r["date"]) <= to_dt
        ]

        all_results = window_cached + fresh_results
        print(f"  Found {len(all_results)} earnings reporters in window.")
        return all_results or None

    # ── Company Profiles ─────────────────────────────────────────────────────

    def get_company_profiles(self, symbols: list[str]) -> dict[str, dict]:
        """Fetch company profiles using yfinance fast_info + info.

        Profiles are cached 7 days in the company_profile table.
        Returns dict keyed by symbol with FMP-compatible fields:
            mktCap, companyName, sector, industry, price, exchangeShortName
        """
        profiles, missing = _cache.get_profiles_batch(symbols, ttl_days=7)

        if missing:
            print(f"  Fetching profiles for {len(missing)} symbols...", flush=True)
            batch_size = 50
            for i in range(0, len(missing), batch_size):
                batch = missing[i: i + batch_size]
                try:
                    tickers = yf.Tickers(" ".join(batch))
                    for sym in batch:
                        try:
                            t = tickers.tickers[sym]
                            fi = t.fast_info
                            info = t.info or {}
                            profile = {
                                "symbol": sym,
                                "companyName": info.get("longName") or info.get("shortName") or sym,
                                "mktCap": int(getattr(fi, "market_cap", None) or info.get("marketCap") or 0),
                                "price": float(getattr(fi, "last_price", None) or info.get("currentPrice") or 0),
                                "sector": info.get("sector") or "Unknown",
                                "industry": info.get("industry") or "Unknown",
                                "exchangeShortName": info.get("exchange") or "NASDAQ",
                            }
                            _cache.upsert_profile(sym, profile)
                            profiles[sym] = profile
                        except Exception:
                            fallback = {
                                "symbol": sym,
                                "companyName": sym,
                                "mktCap": 0,
                                "price": 0,
                                "sector": "Unknown",
                                "industry": "Unknown",
                                "exchangeShortName": "NASDAQ",
                            }
                            _cache.upsert_profile(sym, fallback)
                            profiles[sym] = fallback
                except Exception as e:
                    print(f"WARNING: profile batch error: {e}", file=sys.stderr)
        else:
            print(f"  Profiles: all {len(symbols)} from cache.", flush=True)

        return profiles

    # ── Historical Prices ────────────────────────────────────────────────────

    def get_historical_prices(self, symbol: str, days: int = 250) -> Optional[list[dict]]:
        """Fetch daily OHLCV. Returns most-recent-first list[dict] (same as FMPClient).

        Serves from cache when possible; only fetches missing bars.
        """
        bars = self._get_bars_incremental(symbol, days)
        return bars if bars else None

    def _get_bars_incremental(self, symbol: str, days: int) -> list[dict]:
        from datetime import date as _date

        today = _date.today()

        if _cache.needs_full_refresh(symbol):
            return self._fetch_full(symbol, days)

        latest = _cache.latest_bar_date(symbol)
        behind = (today - latest).days

        if behind <= 1:
            return _cache.get_bars(symbol, days)

        fetch_days = behind + 5
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
        period_days = int(days * 1.45)
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

    # ── Stats (compatibility) ────────────────────────────────────────────────

    def get_api_stats(self) -> dict:
        stats = _cache.stats()
        stats["api_calls_made"] = 0
        stats["max_api_calls"] = 9999
        stats["rate_limit_reached"] = False
        stats["data_source"] = "yfinance + SQLite cache"
        return stats
