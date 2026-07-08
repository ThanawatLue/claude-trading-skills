#!/usr/bin/env python3
"""
Yahoo Finance client for CANSLIM Screener — drop-in replacement for FMPClient.

Maps yfinance data to the same shapes expected by CANSLIM calculators:
  get_profile(symbol)                    → [{"companyName":..., "sector":..., "mktCap":...}]
  get_quote(symbol)                      → [{"price":..., "yearHigh":..., "yearLow":..., "volume":..., "avgVolume":...}]
  get_income_statement(sym, period, lim) → [{date, eps, epsdiluted, revenue, netIncome}]
  get_historical_prices(symbol, days)    → {"historical": [{date, close, volume}]}
  get_institutional_ownership(symbol)    → {"institutionalHolders": [...], "percentInsiders":..., "percentInstitutions":...}
  get_sp500_benchmark(days)              → {"historical": [...]}  (uses SPY)

No API key required. All data via yfinance (free).
"""

from __future__ import annotations

import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
    sys.exit(1)

import pandas as pd

# ── Cache (shared with VCP screener) ──────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

try:
    from cache_manager import CacheManager
    _DB_PATH = _PROJECT_ROOT / "state" / "market_cache.db"
    _cache = CacheManager(_DB_PATH)
    _CACHE_OK = True
except Exception:
    _cache = None
    _CACHE_OK = False


def _yf_download(symbol: str, days: int) -> pd.DataFrame:
    """Download OHLCV from yfinance, using cache when available."""
    end = datetime.today()
    start = end - timedelta(days=days + 30)  # buffer for weekends/holidays

    # Try cache first
    if _CACHE_OK and _cache:
        behind = _cache.days_behind(symbol)
        if behind <= 1:
            bars = _cache.get_bars(symbol, days)
            if len(bars) >= days // 2:
                df = pd.DataFrame(bars)
                # Drop rows where 'close' is NaN (legacy or cache corruptions)
                if not df.empty and "close" in df.columns:
                    df = df.dropna(subset=["close"])
                df["Date"] = pd.to_datetime(df["date"])
                df = df.set_index("Date").sort_index()
                df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                                   "close": "Close", "volume": "Volume"}, inplace=True)
                return df.tail(days)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = yf.download(symbol, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"), auto_adjust=True, progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    # Drop rows where 'Close' is NaN from downloaded yfinance data
    if not df.empty and "Close" in df.columns:
        df = df.dropna(subset=["Close"])

    # Save to cache
    if _CACHE_OK and _cache and not df.empty:
        bars = []
        for dt, row in df.iterrows():
            close_val = row.get("Close", 0)
            if pd.isna(close_val):
                continue
            bars.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(close_val),
                "volume": int(row.get("Volume", 0)),
            })
        _cache.upsert_bars(symbol, bars)

    return df.tail(days)


class YFClient:
    """Yahoo Finance client matching FMPClient's interface for CANSLIM."""

    def __init__(self, api_key: Optional[str] = None):
        self._ticker_cache: dict[str, yf.Ticker] = {}

    def _ticker(self, symbol: str) -> yf.Ticker:
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]

    # ── Profile ───────────────────────────────────────────────────────────────

    def get_profile(self, symbol: str) -> Optional[list[dict]]:
        """Return [{companyName, sector, industry, mktCap, exchangeShortName}]."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                info = self._ticker(symbol).info
            return [{
                "companyName": info.get("longName") or info.get("shortName") or symbol,
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "mktCap": info.get("marketCap", 0),
                "exchangeShortName": info.get("exchange", ""),
                "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
            }]
        except Exception:
            return None

    # ── Quote ─────────────────────────────────────────────────────────────────

    def get_quote(self, symbol: str) -> Optional[list[dict]]:
        """Return [{price, yearHigh, yearLow, volume, avgVolume, marketCap}]."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fi = self._ticker(symbol).fast_info
                info = self._ticker(symbol).info

            price = getattr(fi, "last_price", None) or info.get("currentPrice") or info.get("regularMarketPrice", 0)
            year_high = getattr(fi, "year_high", None) or info.get("fiftyTwoWeekHigh")
            year_low = getattr(fi, "year_low", None) or info.get("fiftyTwoWeekLow")
            volume = info.get("volume") or info.get("regularMarketVolume", 0)
            avg_volume = info.get("averageVolume") or info.get("averageVolume10days", 0)

            return [{
                "price": float(price) if price else 0,
                "yearHigh": float(year_high) if year_high else 0,
                "yearLow": float(year_low) if year_low else 0,
                "volume": int(volume) if volume else 0,
                "avgVolume": int(avg_volume) if avg_volume else 0,
                "marketCap": getattr(fi, "market_cap", None) or info.get("marketCap", 0),
            }]
        except Exception:
            return None

    # ── Income Statement ──────────────────────────────────────────────────────

    def get_income_statement(self, symbol: str, period: str = "quarter",
                             limit: int = 8) -> Optional[list[dict]]:
        """Return list of income statements in FMP format (most recent first).

        Fields: date, eps, epsdiluted, revenue, netIncome
        """
        try:
            t = self._ticker(symbol)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if period == "quarter":
                    stmt = t.quarterly_income_stmt
                else:
                    stmt = t.income_stmt

            if stmt is None or stmt.empty:
                return None

            # Get current shares outstanding as fallback
            fallback_shares = None
            try:
                info = t.info
                fallback_shares = info.get("sharesOutstanding") or getattr(t.fast_info, "shares", None)
            except Exception:
                pass

            # yfinance: rows = line items, columns = dates (newest first)
            results = []
            for col in stmt.columns[:limit]:
                date_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)[:10]

                def _get(row_names):
                    for name in row_names:
                        for idx in stmt.index:
                            if name.lower() in str(idx).lower():
                                val = stmt.loc[idx, col]
                                if pd.notna(val):
                                    return float(val)
                    return None

                revenue = _get(["Total Revenue", "Revenue"])
                net_income = _get(["Net Income", "Net Income Common Stockholders"])
                basic_eps = _get(["Basic EPS", "Basic Earnings Per Share"])
                diluted_eps = _get(["Diluted EPS", "Diluted Earnings Per Share"])

                # Shares outstanding for EPS fallback
                if basic_eps is None and net_income is not None:
                    shares = _get(["Basic Average Shares", "Diluted Average Shares"])
                    if not shares or shares <= 0:
                        shares = fallback_shares

                    if shares and shares > 0:
                        basic_eps = net_income / shares
                        diluted_eps = basic_eps

                results.append({
                    "date": date_str,
                    "eps": basic_eps,
                    "epsdiluted": diluted_eps or basic_eps,
                    "revenue": revenue,
                    "netIncome": net_income,
                })

            return results if results else None

        except Exception as e:
            print(f"  Warning: income_statement failed for {symbol}: {e}", file=sys.stderr)
            return None

    # ── Historical Prices ─────────────────────────────────────────────────────

    def get_historical_prices(self, symbol: str, days: int = 365) -> Optional[dict]:
        """Return {"historical": [{date, close, open, high, low, volume}]} (newest first)."""
        try:
            df = _yf_download(symbol, days)
            if df is None or df.empty:
                return None

            historical = []
            for dt, row in df.iloc[::-1].iterrows():  # newest first
                close_val = row.get("Close", 0)
                if pd.isna(close_val):
                    continue
                historical.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "open": round(float(row.get("Open", 0)), 4),
                    "high": round(float(row.get("High", 0)), 4),
                    "low": round(float(row.get("Low", 0)), 4),
                    "close": round(float(close_val), 4),
                    "volume": int(row.get("Volume", 0)),
                })
            return {"historical": historical}

        except Exception:
            return None

    # ── Institutional Ownership ───────────────────────────────────────────────

    def get_institutional_ownership(self, symbol: str) -> Optional[dict]:
        """Return {"institutionalHolders": [...], "percentInstitutions": float}."""
        try:
            t = self._ticker(symbol)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                holders = t.institutional_holders
                info = t.info

            pct_inst = info.get("heldPercentInstitutions", 0) or 0
            pct_insider = info.get("heldPercentInsiders", 0) or 0

            holder_list = []
            if holders is not None and not holders.empty:
                for _, row in holders.iterrows():
                    holder_list.append({
                        "holderName": str(row.get("Holder", "")),
                        "shares": int(row.get("Shares", 0)),
                        "dateReported": str(row.get("Date Reported", "")),
                    })

            return {
                "institutionalHolders": holder_list,
                "percentInstitutions": round(float(pct_inst) * 100, 2),
                "percentInsiders": round(float(pct_insider) * 100, 2),
                "holderCount": len(holder_list),
            }

        except Exception:
            return None

    # ── S&P 500 Benchmark ─────────────────────────────────────────────────────

    def get_sp500_benchmark(self, days: int = 365) -> Optional[dict]:
        """Return SPY historical prices in same shape as get_historical_prices."""
        return self.get_historical_prices("SPY", days)

    # ── S&P 500 Constituents (for universe) ───────────────────────────────────

    def get_api_stats(self) -> dict:
        return {"data_source": "Yahoo Finance (yfinance)", "api_calls": 0, "cache_entries": 0}

    def get_sp500_constituents(self) -> Optional[list[dict]]:
        """Return S&P 500 tickers from Wikipedia (cached in DB)."""
        # Try cache first
        if _CACHE_OK and _cache:
            cached = _cache.get_universe(ttl_days=30)
            if cached:
                return [{"symbol": s, "name": "", "sector": ""} for s in cached]

        try:
            import requests
            from io import StringIO
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            tables = pd.read_html(StringIO(resp.text))
            df = tables[0]
            df.columns = [c.strip() for c in df.columns]
            sym_col = next((c for c in df.columns if "Symbol" in c or "Ticker" in c), None)
            sec_col = next((c for c in df.columns if "GICS Sector" in c or "Sector" in c), None)
            if sym_col is None:
                return None
            constituents = []
            for _, row in df.iterrows():
                sym = str(row[sym_col]).replace(".", "-")
                sec = str(row[sec_col]) if sec_col else "Unknown"
                constituents.append({"symbol": sym, "name": "", "sector": sec})
            if _CACHE_OK and _cache:
                _cache.save_universe(constituents)
            return constituents
        except Exception as e:
            print(f"Warning: could not fetch S&P 500 list: {e}", file=sys.stderr)
            return None

    def get_thai_constituents(self) -> Optional[list[dict]]:
        """Return Thai growth/momentum candidates (SET100 + MAI growth)."""
        growth_symbols = [
            # Technology & Electronics
            "DELTA", "HANA", "KCE", "CCET", "SIS", "SYNEX", "ADVICE",
            # Commerce & Retail
            "CPALL", "CPAXT", "COM7", "MOSHI", "AU", "SINGER", "BEAUTY",
            # Food & Beverage (Exporters/Brands)
            "SAPPE", "ICHI", "COCOCO", "MALEE", "PLUS", "KCG", "BTG", "CBG", "OSP",
            # Finance & Leasing
            "MTC", "SAWAD", "TIDLOR", "AEONTS", "JMT", "BAM",
            # Industrials & Logistics
            "WHA", "AMATA", "SJWD", "III", "MENA",
            # Healthcare & Esthetics
            "BDMS", "BH", "PR9", "MASTER", "CHG",
            # Energy & Utilities
            "GULF", "GPSC", "BGRIM", "EA",
            # Mid-caps & Tourism recovery
            "SIRI", "AP", "SPALI", "DOHOME", "GLOBAL", "MEGA", "PLANB",
            "AOT", "MINT", "CENTEL", "ERW", "SPA", "TRUE"
        ]
        constituents = [
            {"symbol": f"{sym}.BK", "name": sym, "sector": "Thai Growth", "subSector": "Thai Stock"}
            for sym in growth_symbols
        ]
        print(f"  (Thai Growth Universe: {len(constituents)} stocks)", flush=True)
        return constituents
