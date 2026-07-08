"""yfinance-based data client for downtrend-duration-analyzer.

Replaces FMP endpoints with free yfinance data:
  - fetch_sp500_list()       → S&P 500 constituents with sector + market cap
  - fetch_historical_prices() → OHLCV DataFrame via yf.download()
"""

from __future__ import annotations

import io
import warnings
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


_WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
_WIKI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

_SESSION = None


def _get_session() -> requests.Session:
    """Get or create a requests Session with robust retry logic."""
    global _SESSION
    if _SESSION is None:
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _SESSION = session
    return _SESSION


def _fetch_wiki_tables() -> list:
    """Fetch Wikipedia S&P 500 table, bypassing 403 with browser User-Agent."""
    from io import StringIO

    try:
        session = _get_session()
        resp = session.get(_WIKI_SP500_URL, headers=_WIKI_HEADERS, timeout=20)
        resp.raise_for_status()
        return pd.read_html(StringIO(resp.text))
    except Exception as e:
        print(f"Warning: could not fetch S&P 500 list from Wikipedia: {e}")
        return []


def fetch_sp500_list(sector: str | None = None, limit: int | None = None) -> list[dict]:
    """Return S&P 500 stocks with symbol, sector, and marketCap.

    Pulls the constituent table from Wikipedia, then fetches market cap
    from yfinance in bulk (one Ticker() call per symbol — cached).
    """
    tables = _fetch_wiki_tables()
    if not tables:
        return []

    df = tables[0]
    # Normalise column names across Wikipedia table variants
    df.columns = [c.strip() for c in df.columns]
    symbol_col = next((c for c in df.columns if "Symbol" in c or "Ticker" in c), None)
    sector_col = next((c for c in df.columns if "GICS Sector" in c or "Sector" in c), None)

    if symbol_col is None:
        return []

    records = []
    for _, row in df.iterrows():
        sym = str(row[symbol_col]).replace(".", "-")  # BRK.B → BRK-B for yfinance
        sec = str(row[sector_col]) if sector_col else "Unknown"

        if sector and sec != sector:
            continue

        records.append({"symbol": sym, "sector": sec, "marketCap": None})

    if limit is not None:
        records = records[:limit]

    # Fetch market caps in batch using yfinance fast_info
    for rec in records:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ticker = yf.Ticker(rec["symbol"])
                info = ticker.fast_info
                rec["marketCap"] = getattr(info, "market_cap", None)
        except Exception as e:
            print(f"Warning: failed to fetch market cap for {rec['symbol']}: {e}")
            rec["marketCap"] = None

    return records


def fetch_historical_prices(
    symbol: str, from_date: str, to_date: str
) -> pd.DataFrame:
    """Download daily OHLCV for *symbol* between from_date and to_date.

    Returns a DataFrame with columns: date, open, high, low, close, volume
    sorted ascending by date.  Returns empty DataFrame on failure.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw = yf.download(
                symbol,
                start=from_date,
                end=to_date,
                auto_adjust=True,
                progress=False,
            )
        if raw is None or not isinstance(raw, pd.DataFrame) or raw.empty:
            return pd.DataFrame()

        # yfinance returns MultiIndex columns when downloading a single ticker
        # in some versions — flatten if needed.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [c[0].lower() for c in raw.columns]
        else:
            raw.columns = [c.lower() for c in raw.columns]

        raw = raw.reset_index()
        raw.rename(columns={"index": "date", "Date": "date"}, inplace=True)
        
        if "date" not in raw.columns:
            return pd.DataFrame()

        raw["date"] = pd.to_datetime(raw["date"])
        raw = raw.sort_values("date").reset_index(drop=True)

        # Drop rows where critical columns are NaN
        critical_cols = [c for c in ["date", "close"] if c in raw.columns]
        raw = raw.dropna(subset=critical_cols)

        if raw.empty:
            return pd.DataFrame()

        keep = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in raw.columns]
        return raw[keep]

    except Exception as e:
        print(f"Warning: yfinance download failed for {symbol}: {e}")
        return pd.DataFrame()
