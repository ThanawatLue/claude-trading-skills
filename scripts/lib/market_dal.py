#!/usr/bin/env python3
"""
Data Access Layer (DAL) for Market Data
Wraps SQLite (state/market_cache.db) with yfinance API fallback.
Provides uniform access to both daily and 1-minute candle datasets.
"""

import sys
import warnings
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import yfinance as yf

# Resolve paths
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

try:
    from cache_manager import CacheManager
    _DB_PATH = _PROJECT_ROOT / "state" / "market_cache.db"
    _cache = CacheManager(_DB_PATH)
    _CACHE_OK = True
except Exception as e:
    print(f"DAL Warning: CacheManager failed to initialize: {e}", file=sys.stderr)
    _cache = None
    _CACHE_OK = False


class MarketDAL:
    """
    Central Data Access Layer (DAL) for TH/US market data.
    Implements a transparent fallback chain: SQLite Cache -> yfinance API.
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = str(db_path) if db_path else str(_DB_PATH)
        if db_path:
            try:
                self.cache = CacheManager(self.db_path)
                self.cache_ok = True
            except Exception as e:
                print(f"DAL Warning: Failed to load custom cache: {e}", file=sys.stderr)
                self.cache = _cache
                self.cache_ok = _CACHE_OK
        else:
            self.cache = _cache
            self.cache_ok = _CACHE_OK

    def is_db_available(self) -> bool:
        """Check if SQLite database is available and initialized."""
        return self.cache_ok and self.cache is not None

    # ─── Daily Candles (Daily OHLCV) ──────────────────────────────────────────

    def get_daily_candles(self, symbol: str, days: int = 250) -> pd.DataFrame:
        """
        Get daily OHLCV bars for the given symbol.
        Queries SQLite cache first; falls back to yfinance if stale (>1 day behind).
        Returns a pandas DataFrame with columns: [Open, High, Low, Close, Volume] indexed by Date.
        """
        yf_symbol = symbol if symbol.endswith(".BK") else f"{symbol}.BK"
        
        # Try cache first
        if self.is_db_available():
            behind = self.cache.days_behind(yf_symbol)
            if behind <= 1:
                bars = self.cache.get_bars(yf_symbol, days)
                if len(bars) >= days // 2:
                    df = pd.DataFrame(bars)
                    df["Date"] = pd.to_datetime(df["date"])
                    df = df.set_index("Date").sort_index()
                    df.rename(columns={
                        "open": "Open", "high": "High", "low": "Low",
                        "close": "Close", "volume": "Volume"
                    }, inplace=True)
                    return df.tail(days)

        # Cache miss or stale -> fetch from yfinance
        print(f"DAL Cache Miss/Stale (Daily) for {symbol}. Fetching from yfinance...")
        end = datetime.today()
        start = end - timedelta(days=days + 30)
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = yf.download(yf_symbol, start=start.strftime("%Y-%m-%d"),
                                 end=end.strftime("%Y-%m-%d"), auto_adjust=True, progress=False)
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
                
            if not df.empty:
                # Save to cache
                if self.is_db_available():
                    bars = []
                    for dt, row in df.iterrows():
                        bars.append({
                            "date": dt.strftime("%Y-%m-%d"),
                            "open": float(row.get("Open", 0)),
                            "high": float(row.get("High", 0)),
                            "low": float(row.get("Low", 0)),
                            "close": float(row.get("Close", 0)),
                            "volume": int(row.get("Volume", 0)),
                        })
                    self.cache.upsert_bars(yf_symbol, bars)
                return df.tail(days)
        except Exception as e:
            print(f"DAL Error downloading daily data for {yf_symbol}: {e}", file=sys.stderr)
            
        # Return empty DataFrame on failure
        return pd.DataFrame()

    # ─── Minute Candles (1-Minute Intraday) ───────────────────────────────────

    def get_minute_candles(self, symbol: str, limit: int = 1000) -> pd.DataFrame:
        """
        Get 1-minute OHLCV bars for the given symbol.
        Queries SQLite cache first; falls back to yfinance if no data exists.
        Returns a pandas DataFrame with columns: [Open, High, Low, Close, Volume] indexed by Datetime.
        """
        yf_symbol = symbol if symbol.endswith(".BK") else f"{symbol}.BK"
        
        # Try cache first
        if self.is_db_available():
            bars = self.cache.get_minute_bars(yf_symbol, limit)
            if bars:
                df = pd.DataFrame(bars)
                df["Datetime"] = pd.to_datetime(df["datetime"])
                df = df.set_index("Datetime").sort_index()
                df.rename(columns={
                    "open": "Open", "high": "High", "low": "Low",
                    "close": "Close", "volume": "Volume"
                }, inplace=True)
                return df.tail(limit)

        # Cache miss -> fetch from yfinance (limit to 2 days for 1m data to avoid rate limits)
        print(f"DAL Cache Miss (1-Minute) for {symbol}. Fetching from yfinance...")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = yf.download(yf_symbol, period="2d", interval="1m", auto_adjust=True, progress=False)
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
                
            if not df.empty:
                # Save to cache
                if self.is_db_available():
                    bars = []
                    for dt, row in df.iterrows():
                        bars.append({
                            "datetime": dt.isoformat(),
                            "open": float(row.get("Open", 0)),
                            "high": float(row.get("High", 0)),
                            "low": float(row.get("Low", 0)),
                            "close": float(row.get("Close", 0)),
                            "volume": int(row.get("Volume", 0)),
                        })
                    self.cache.upsert_minute_bars(yf_symbol, bars)
                
                df.index.name = "Datetime"
                return df.tail(limit)
        except Exception as e:
            print(f"DAL Error downloading minute data for {yf_symbol}: {e}", file=sys.stderr)
            
        return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest close price for the symbol from cache (minute or daily), falling back to live quote."""
        yf_symbol = symbol if symbol.endswith(".BK") else f"{symbol}.BK"
        
        # Try minute cache first (most granular)
        if self.is_db_available():
            min_bars = self.cache.get_minute_bars(yf_symbol, limit=1)
            if min_bars:
                return float(min_bars[0].get("close"))
            
            # Try daily cache
            daily_bars = self.cache.get_bars(yf_symbol, days=1)
            if daily_bars:
                return float(daily_bars[0].get("close"))
                
        # Live fallback
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.fast_info
            return float(info.get("last_price", 0))
        except Exception:
            return None


if __name__ == '__main__':
    # Simple self-test
    dal = MarketDAL()
    print(f"DB Available: {dal.is_db_available()}")
    if dal.is_db_available():
        print("Fetching daily candles for PTT...")
        df_daily = dal.get_daily_candles("PTT", days=5)
        print(df_daily)
        print("\nFetching minute candles for PTT...")
        df_min = dal.get_minute_candles("PTT", limit=5)
        print(df_min)
        print(f"\nLatest Price for PTT: {dal.get_latest_price('PTT')}")
