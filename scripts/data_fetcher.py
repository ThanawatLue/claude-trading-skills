#!/usr/bin/env python3
"""
Hourly SET100 Data Fetcher
Fetches both daily and 1-minute candles from yfinance and caches them in state/market_cache.db.
Can be run once (--once) or scheduled (--schedule) Mon-Fri, 10:00-17:00 BKK time.
"""

import sys
import os
import argparse
import time
import warnings
from datetime import datetime
from pathlib import Path

# Add project root and scripts directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    import yfinance as yf
    import pandas as pd
    from apscheduler.schedulers.blocking import BlockingScheduler
    from cache_manager import CacheManager
    from scripts.lib.tv_client import get_thai_set100
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please install required dependencies: pip install yfinance pandas apscheduler tradingview-screener")
    sys.exit(1)

# Initialize Cache
DB_PATH = PROJECT_ROOT / "state" / "market_cache.db"
cache = CacheManager(DB_PATH)

def fetch_symbol_daily(symbol: str) -> bool:
    """Fetch daily data for a symbol and cache it."""
    yf_symbol = symbol if symbol.endswith(".BK") else f"{symbol}.BK"
    clean_symbol = symbol.replace(".BK", "")
    
    print(f"Fetching Daily for {clean_symbol} ({yf_symbol})...")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_daily = yf.download(yf_symbol, period="2d", interval="1d", auto_adjust=True, progress=False)
            
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = [c[0] for c in df_daily.columns]
            
        if not df_daily.empty:
            daily_bars = []
            for dt, row in df_daily.iterrows():
                daily_bars.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)),
                })
            cache.upsert_bars(yf_symbol, daily_bars)
            print(f"  -> Daily: Cached {len(daily_bars)} bars")
            return True
    except Exception as e:
        print(f"  -> Error fetching daily data for {yf_symbol}: {e}", file=sys.stderr)
    return False

def fetch_symbol_minute(symbol: str) -> bool:
    """Fetch 1-minute data for a symbol and cache it."""
    yf_symbol = symbol if symbol.endswith(".BK") else f"{symbol}.BK"
    clean_symbol = symbol.replace(".BK", "")
    
    print(f"Fetching Minute for {clean_symbol} ({yf_symbol})...")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_minute = yf.download(yf_symbol, period="2d", interval="1m", auto_adjust=True, progress=False)
            
        if isinstance(df_minute.columns, pd.MultiIndex):
            df_minute.columns = [c[0] for c in df_minute.columns]
            
        if not df_minute.empty:
            minute_bars = []
            for dt, row in df_minute.iterrows():
                minute_bars.append({
                    "datetime": dt.isoformat(),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)),
                })
            cache.upsert_minute_bars(yf_symbol, minute_bars)
            print(f"  -> Minute: Cached {len(minute_bars)} bars")
            return True
    except Exception as e:
        print(f"  -> Error fetching minute data for {yf_symbol}: {e}", file=sys.stderr)
    return False

def get_symbols() -> list[str]:
    """Retrieve symbols from tv_client or fallback list."""
    try:
        set100_data = get_thai_set100()
        symbols = [s["symbol"] for s in set100_data if "symbol" in s]
    except Exception as e:
        print(f"Error fetching SET100 list from tv_client: {e}", file=sys.stderr)
        symbols = [
            "ADVANC.BK", "AOT.BK", "AWC.BK", "BANPU.BK", "BBL.BK", "BCH.BK", "BCP.BK",
            "BDMS.BK", "BEM.BK", "BGRIM.BK", "BH.BK", "BJC.BK", "BTS.BK", "CBG.BK",
            "CENTEL.BK", "CK.BK", "CKP.BK", "COM7.BK", "CPALL.BK", "CPF.BK", "CPN.BK",
            "CRC.BK", "DELTA.BK", "EGCO.BK", "GLOBAL.BK", "GPSC.BK", "GULF.BK",
            "GUNKUL.BK", "HANA.BK", "HMPRO.BK", "INTUCH.BK", "IRPC.BK", "IVL.BK",
            "JMART.BK", "JMT.BK", "KBANK.BK", "KCE.BK", "KTB.BK", "KTC.BK", "LH.BK",
            "MINT.BK", "MTC.BK", "OR.BK", "OSP.BK", "PLANB.BK", "PTG.BK", "PTT.BK",
            "PTTEP.BK", "PTTGC.BK", "RATCH.BK", "SAWAD.BK", "SCB.BK", "SCC.BK",
            "SCGP.BK", "SIRI.BK", "SPALI.BK", "SPRC.BK", "STA.BK", "TASCO.BK",
            "TCAP.BK", "TIDLOR.BK", "TISCO.BK", "TOP.BK", "TRUE.BK", "TTB.BK",
            "TU.BK", "VGI.BK", "WHA.BK"
        ]
    return symbols

def run_daily_fetch_job():
    """Run Daily candle fetch."""
    print(f"[{datetime.now()}] Starting SET100 Daily candle fetch job...")
    start_time = time.time()
    symbols = get_symbols()
    if not symbols:
        return
    
    total = len(symbols)
    ok = 0
    for i, sym in enumerate(symbols, 1):
        print(f"[{i}/{total}] ", end="")
        if fetch_symbol_daily(sym):
            ok += 1
        time.sleep(0.5)
        
    duration = time.time() - start_time
    print(f"[{datetime.now()}] Daily job completed. Successfully fetched: {ok}/{total} in {duration:.1f}s")

def run_minute_fetch_job():
    """Run Minute candle fetch."""
    print(f"[{datetime.now()}] Starting SET100 Minute candle fetch job...")
    start_time = time.time()
    symbols = get_symbols()
    if not symbols:
        return
    
    total = len(symbols)
    ok = 0
    for i, sym in enumerate(symbols, 1):
        print(f"[{i}/{total}] ", end="")
        if fetch_symbol_minute(sym):
            ok += 1
        time.sleep(0.5)
        
    duration = time.time() - start_time
    print(f"[{datetime.now()}] Minute job completed. Successfully fetched: {ok}/{total} in {duration:.1f}s")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Hourly/Daily SET100 Candle Fetcher")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Run both fetch jobs once and exit")
    group.add_argument("--schedule", action="store_true", help="Run scheduled fetch jobs (blocking)")
    
    args = parser.parse_args()
    
    if args.once:
        run_daily_fetch_job()
        run_minute_fetch_job()
    elif args.schedule:
        print("Starting Scheduled Fetcher Service (Mon-Fri)...")
        # Run both once on startup to bootstrap cache
        run_daily_fetch_job()
        run_minute_fetch_job()
        
        scheduler = BlockingScheduler(timezone="Asia/Bangkok")
        
        # 1. Schedule minute bars hourly Mon-Fri 10:00-17:00 BKK Time
        scheduler.add_job(
            run_minute_fetch_job,
            'cron',
            day_of_week='mon-fri',
            hour='10-17',
            minute=0
        )
        
        # 2. Schedule daily bars daily Mon-Fri at 17:00 BKK Time (Market Close)
        scheduler.add_job(
            run_daily_fetch_job,
            'cron',
            day_of_week='mon-fri',
            hour=17,
            minute=0
        )
        
        print("Scheduler configured:")
        print("  - Minute candles: Mon-Fri, hourly 10:00 - 17:00")
        print("  - Daily candles: Mon-Fri, daily at 17:00")
        print("Scheduler running. Press Ctrl+C to exit.")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("Scheduler stopped.")
