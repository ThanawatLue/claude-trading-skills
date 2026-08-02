"""Yahoo Finance client — drop-in replacement for FMPClient.

Provides the same interface as fmp_client.FMPClient but uses
yfinance (Yahoo Finance) instead. No API key required.

Caching:
  All OHLCV data is stored in state/market_cache.db (project root).
  - First run: full download for all symbols.
  - Subsequent runs same day: served entirely from cache.
  - Next trading day: only the missing bars are fetched (one small batch call).
  - After 7 days without refresh: full re-download to catch split/dividend adjustments.

Public methods (identical signatures to FMPClient):
    get_sp500_constituents() -> list[dict] | None
    get_thai_constituents()  -> list[dict] | None
    get_quote(symbols: str)  -> list[dict] | None
    get_historical_prices(symbol, days) -> dict | None
    get_batch_quotes(symbols) -> dict[str, dict]
    get_batch_historical(symbols, days) -> dict[str, list[dict]]
    get_api_stats() -> dict
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# ── Cache setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]   # skills/vcp-screener/scripts -> skills/vcp-screener -> skills -> trading
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from cache_manager import CacheManager  # noqa: E402

_DB_PATH = _PROJECT_ROOT / "state" / "market_cache.db"
_cache = CacheManager(_DB_PATH)


# ── DataFrame → list[dict] helper ─────────────────────────────────────────────

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
    """Yahoo Finance client with the same interface as FMPClient."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_calls = 0
        self._quote_cache: dict = {}

    # ── S&P 500 Constituents ──────────────────────────────────────────────────

    def get_sp500_constituents(self) -> Optional[list[dict]]:
        """Return S&P 500 list — cached 30 days, falls back to Wikipedia."""
        cached = _cache.get_universe(ttl_days=30)
        if cached:
            print(f"  (S&P 500 list from cache: {len(cached)} stocks)", flush=True)
            # Return full dicts; names/sectors not critical for VCP pipeline
            return [{"symbol": s, "name": s, "sector": "Unknown", "subSector": ""} for s in cached]

        data = self._fetch_sp500_wikipedia()
        if data:
            _cache.save_universe(data)
        return data

    def _fetch_sp500_wikipedia(self) -> Optional[list[dict]]:
        if requests is None:
            print("WARNING: requests library not found, Wikipedia fallback for S&P 500 constituents is unavailable.", file=sys.stderr)
            return None
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            headers = {"User-Agent": "Mozilla/5.0 (compatible; VCPScreener/2.0)"}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return None

            table_match = re.search(
                r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>',
                resp.text, re.DOTALL,
            )
            if not table_match:
                return None

            table_html = table_match.group(1)
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL)

            def strip(s: str) -> str:
                return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

            constituents = []
            for row in rows[1:]:
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)
                if len(cells) < 4:
                    continue
                symbol = strip(cells[0]).replace(".", "-")
                name = strip(cells[1])
                sector = strip(cells[2])
                sub_sector = strip(cells[3])
                if symbol:
                    constituents.append(
                        {"symbol": symbol, "name": name, "sector": sector, "subSector": sub_sector}
                    )

            if constituents:
                print(f"  (Wikipedia S&P 500: {len(constituents)} stocks)", flush=True)
            return constituents or None
        except Exception as e:
            print(f"WARNING: Wikipedia S&P500 error: {e}", file=sys.stderr)
            return None

    # ── SET50 Constituents ────────────────────────────────────────────────────

    def get_thai_constituents(self, index: str = "SET50") -> Optional[list[dict]]:
        try:
            from scripts.lib.tv_client import get_thai_set50, get_thai_set100, is_available
            if is_available():
                if index == "SET100":
                    stocks = get_thai_set100(limit=100)
                else:
                    stocks = get_thai_set50(limit=50)
                
                if stocks:
                    constituents = [
                        {
                            "symbol": f"{s['name']}.BK",
                            "name": s['name'],
                            "sector": s.get("sector", index),
                            "subSector": s.get("industry", "Thai Stock")
                        }
                        for s in stocks
                    ]
                    print(f"  (Thai {index} via TradingView: {len(constituents)} stocks)", flush=True)
                    return constituents
        except Exception as e:
            import sys
            print(f"WARNING: tv_client fetch failed ({e}). Falling back to hardcoded SET50.", file=sys.stderr)

        # Fallback to hardcoded SET50
        set50_symbols = [
            "ADVANC", "AOT", "AWC", "BANPU", "BBL", "BCP", "BDMS", "BEM", "BGRIM",
            "BH", "BTS", "CBG", "CENTEL", "COM7", "CPALL", "CPF", "CPN", "CRC",
            "DELTA", "EA", "EGCO", "GLOBAL", "GULF", "HANA", "HMPRO", "INTUCH",
            "IRPC", "IVL", "KBANK", "KCE", "KTB", "KTC", "LH", "MINT", "MTC",
            "OR", "OSP", "PTT", "PTTEP", "PTTGC", "SAWAD", "SCB", "SCC", "SCGP",
            "TISCO", "TOP", "TRUE", "TTB", "TU", "WHA",
        ]
        constituents = [
            {"symbol": f"{sym}.BK", "name": sym, "sector": "SET50", "subSector": "Thai Stock"}
            for sym in set50_symbols
        ]
        print(f"  (Thai {index} fallback: {len(constituents)} stocks)", flush=True)
        return constituents

    # ── Quote ─────────────────────────────────────────────────────────────────

    def get_quote(self, symbols: str) -> Optional[list[dict]]:
        cache_key = f"quote_{symbols}"
        if cache_key in self._quote_cache:
            return self._quote_cache[cache_key]

        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        result = self._fetch_quotes(symbol_list)
        if result:
            self._quote_cache[cache_key] = result
        return result or None

    def _fetch_quotes(self, symbols: list[str]) -> list[dict]:
        self._api_calls += 1
        try:
            tickers = yf.Tickers(" ".join(symbols))
            quotes = []
            for sym in symbols:
                try:
                    info = tickers.tickers[sym].info
                    quotes.append(self._info_to_fmp_quote(sym, info))
                except Exception:
                    pass
            return quotes
        except Exception as e:
            print(f"WARNING: yfinance quote error: {e}", file=sys.stderr)
            return []

    @staticmethod
    def _info_to_fmp_quote(symbol: str, info: dict) -> dict:
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "price": float(price),
            "yearHigh": float(info.get("fiftyTwoWeekHigh") or 0),
            "yearLow": float(info.get("fiftyTwoWeekLow") or 0),
            "avgVolume": int(info.get("averageVolume") or 0),
            "marketCap": int(info.get("marketCap") or 0),
            "sector": info.get("sector") or "Unknown",
            "exchange": info.get("exchange") or "",
            "changesPercentage": float(info.get("regularMarketChangePercent") or 0),
        }

    # ── Historical Prices (single symbol) ────────────────────────────────────

    def get_historical_prices(self, symbol: str, days: int = 365) -> Optional[dict]:
        """Return FMP-compatible dict {"symbol": ..., "historical": [...]}.

        Serves from cache when possible; only fetches missing bars.
        """
        bars = self._get_bars_incremental(symbol, days)
        if not bars:
            return None
        return {"symbol": symbol, "historical": bars}

    def _get_bars_incremental(self, symbol: str, days: int) -> list[dict]:
        """Core incremental fetch logic for a single symbol."""
        from datetime import date as _date

        today = _date.today()

        # Full refresh if no data or stale beyond threshold
        if _cache.needs_full_refresh(symbol):
            return self._fetch_full(symbol, days)

        latest = _cache.latest_bar_date(symbol)
        behind = (today - latest).days

        if behind <= 1:
            # Cache is current — serve directly
            return _cache.get_bars(symbol, days)

        # Partial update: fetch only missing days (+5 day buffer for weekends)
        fetch_days = behind + 5
        self._api_calls += 1
        try:
            df = yf.Ticker(symbol).history(period=f"{int(fetch_days * 1.5)}d", auto_adjust=True)
            if not df.empty:
                new_bars = _df_to_bars(df)
                # Filter to only bars newer than what we already have
                new_only = [b for b in new_bars if _date.fromisoformat(b["date"]) > latest]
                if new_only:
                    _cache.upsert_bars(symbol, new_only)
        except Exception as e:
            print(f"WARNING: partial fetch error for {symbol}: {e}", file=sys.stderr)

        return _cache.get_bars(symbol, days)

    def _fetch_full(self, symbol: str, days: int) -> list[dict]:
        """Download full history, upsert to cache, return bars."""
        period_days = int(days * 1.45)
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

    # ── Batch Methods ──────────────────────────────────────────────────────────

    def get_batch_quotes(self, symbols: list[str]) -> dict[str, dict]:
        """Fetch live quotes for many symbols."""
        if not symbols:
            return {}

        self._api_calls += 1
        results: dict[str, dict] = {}
        batch_size = 100

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            try:
                tickers = yf.Tickers(" ".join(batch))
                for sym in batch:
                    try:
                        info = tickers.tickers[sym].fast_info
                        price = getattr(info, "last_price", None) or 0.0
                        year_high = getattr(info, "year_high", None) or 0.0
                        year_low = getattr(info, "year_low", None) or 0.0
                        avg_vol = getattr(info, "three_month_average_volume", None) or 0
                        market_cap = getattr(info, "market_cap", None) or 0
                        results[sym] = {
                            "symbol": sym,
                            "name": sym,
                            "price": float(price),
                            "yearHigh": float(year_high),
                            "yearLow": float(year_low),
                            "avgVolume": int(avg_vol),
                            "marketCap": int(market_cap),
                            "sector": "Unknown",
                        }
                    except Exception:
                        pass
            except Exception as e:
                print(f"WARNING: batch quote error (batch {i}): {e}", file=sys.stderr)

        total = len(results)
        if total:
            print(f"    Fetched quotes ({total}/{len(symbols)})...", flush=True)
        return results

    def get_batch_historical(self, symbols: list[str], days: int = 260) -> dict[str, list[dict]]:
        """Fetch historical prices for many symbols with intelligent caching.

        Splits symbols into three groups:
          need_full   → batch yf.download() for full history
          need_update → batch yf.download() for only missing days
          fresh       → served directly from cache (no network call)
        """
        if not symbols:
            return {}

        need_full, need_update, fresh = _cache.classify_symbols(symbols)

        results: dict[str, list[dict]] = {}

        # --- Fresh: return from cache, no network ----
        if fresh:
            for sym in fresh:
                bars = _cache.get_bars(sym, days)
                if bars:
                    results[sym] = bars
            print(f"    Cache hit: {len(fresh)} symbols (no fetch needed)", flush=True)

        # --- Full refresh: one big batch download ----
        if need_full:
            print(
                f"    Full download: {len(need_full)} symbols ({days}-day history)...",
                flush=True,
            )
            period_days = int(days * 1.45)
            self._api_calls += 1
            try:
                raw = yf.download(
                    need_full,
                    period=f"{period_days}d",
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                )
                for sym in need_full:
                    try:
                        df = raw if len(need_full) == 1 else raw[sym]
                        df = df.dropna(subset=["Close"]).tail(days)
                        if df.empty:
                            continue
                        bars = _df_to_bars(df)
                        _cache.upsert_bars(sym, bars)
                        results[sym] = bars
                    except Exception:
                        pass
            except Exception as e:
                print(f"WARNING: batch full download error: {e}", file=sys.stderr)

        # --- Incremental update: fetch only missing bars ----
        if need_update:
            from datetime import date as _date

            today = _date.today()
            max_behind = max((_date.today() - (_cache.latest_bar_date(s) or _date(2000, 1, 1))).days
                             for s in need_update) + 5
            fetch_period = int(max_behind * 1.5)
            print(
                f"    Incremental update: {len(need_update)} symbols ({max_behind} days)...",
                flush=True,
            )
            self._api_calls += 1
            try:
                raw = yf.download(
                    need_update,
                    period=f"{fetch_period}d",
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                )
                for sym in need_update:
                    try:
                        df = raw if len(need_update) == 1 else raw[sym]
                        df = df.dropna(subset=["Close"])
                        if df.empty:
                            continue
                        new_bars = _df_to_bars(df)
                        latest = _cache.latest_bar_date(sym)
                        if latest:
                            new_bars = [b for b in new_bars if _date.fromisoformat(b["date"]) > latest]
                        if new_bars:
                            _cache.upsert_bars(sym, new_bars)
                        full_bars = _cache.get_bars(sym, days)
                        if full_bars:
                            results[sym] = full_bars
                    except Exception:
                        pass
            except Exception as e:
                print(f"WARNING: batch incremental download error: {e}", file=sys.stderr)

        return results

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_api_stats(self) -> dict:
        stats = _cache.stats()
        stats["api_calls_made"] = self._api_calls
        stats["rate_limit_reached"] = False
        stats["data_source"] = "yfinance + SQLite cache"
        return stats
