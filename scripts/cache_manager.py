"""Market Data Cache Manager — SQLite-backed incremental cache.

DB schema (state/market_cache.db):
  price_bar       — OHLCV per (symbol, date), immutable once a day closes
  company_profile — name/sector/mktCap, TTL 7 days
  earnings_scan   — per-symbol scan result, TTL 24 hours
  universe        — S&P500 / SET50 list, TTL 30 days

Incremental OHLCV logic:
  - No data or latest bar > 7 days old → full refetch (catches splits/adjustments)
  - 2–7 days stale → fetch only missing days
  - Up to 1 day stale → return from cache directly (market may not have closed yet)
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_bar (
    symbol     TEXT NOT NULL,
    date       TEXT NOT NULL,
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL,
    volume     INTEGER,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, date)
);
CREATE INDEX IF NOT EXISTS idx_price_symbol_date ON price_bar(symbol, date DESC);

CREATE TABLE IF NOT EXISTS company_profile (
    symbol     TEXT PRIMARY KEY,
    name       TEXT,
    sector     TEXT,
    industry   TEXT,
    market_cap INTEGER,
    price      REAL,
    exchange   TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS earnings_scan (
    symbol     TEXT PRIMARY KEY,
    checked_at TEXT NOT NULL,
    found_date TEXT,
    timing     TEXT
);

CREATE TABLE IF NOT EXISTS universe (
    symbol     TEXT PRIMARY KEY,
    name       TEXT,
    sector     TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS minute_price_bar (
    symbol     TEXT NOT NULL,
    datetime   TEXT NOT NULL,
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL,
    volume     INTEGER,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (symbol, datetime)
);
CREATE INDEX IF NOT EXISTS idx_minute_price_symbol_datetime ON minute_price_bar(symbol, datetime DESC);
"""

# After this many days without a full refresh, re-download everything for a
# symbol to catch any split/dividend price adjustments from yfinance.
FULL_REFRESH_STALE_DAYS = 7


class CacheManager:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Connection ────────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=60.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ── OHLCV ─────────────────────────────────────────────────────────────────

    def latest_bar_date(self, symbol: str) -> Optional[date]:
        """Return the most recent date we have for symbol, or None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT MAX(date) AS d FROM price_bar WHERE symbol = ?", (symbol,)
            ).fetchone()
        if row and row["d"]:
            return date.fromisoformat(row["d"])
        return None

    def needs_full_refresh(self, symbol: str) -> bool:
        """True when no data or latest bar is older than FULL_REFRESH_STALE_DAYS."""
        latest = self.latest_bar_date(symbol)
        if latest is None:
            return True
        return (date.today() - latest).days > FULL_REFRESH_STALE_DAYS

    def days_behind(self, symbol: str) -> int:
        """How many calendar days behind today the cache is (0 = fresh)."""
        latest = self.latest_bar_date(symbol)
        if latest is None:
            return 9999
        return (date.today() - latest).days

    def get_bars(self, symbol: str, days: int) -> list[dict]:
        """Return up to `days` most-recent bars, most-recent-first."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT date, open, high, low, close, volume
                   FROM price_bar WHERE symbol = ?
                   ORDER BY date DESC LIMIT ?""",
                (symbol, days),
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert_bars(self, symbol: str, bars: list[dict]) -> None:
        """Insert or replace bars (date order doesn't matter)."""
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO price_bar
                   (symbol, date, open, high, low, close, volume, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                [
                    (
                        symbol,
                        b["date"],
                        b.get("open"),
                        b.get("high"),
                        b.get("low"),
                        b.get("close"),
                        b.get("volume"),
                        now,
                    )
                    for b in bars
                ],
            )

    def latest_minute_bar_datetime(self, symbol: str) -> Optional[datetime]:
        """Return the most recent datetime we have for symbol, or None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT MAX(datetime) AS dt FROM minute_price_bar WHERE symbol = ?", (symbol,)
            ).fetchone()
        if row and row["dt"]:
            try:
                # Expecting ISO format like '2026-06-30T10:00:00' or similar
                # Using fromisoformat if it ends with Z/timezone or not
                dt_str = row["dt"]
                if dt_str.endswith("Z"):
                    dt_str = dt_str[:-1]
                return datetime.fromisoformat(dt_str)
            except ValueError:
                return None
        return None

    def get_minute_bars(self, symbol: str, limit: int = 1000) -> list[dict]:
        """Return up to `limit` most-recent minute bars, most-recent-first."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT datetime, open, high, low, close, volume
                   FROM minute_price_bar WHERE symbol = ?
                   ORDER BY datetime DESC LIMIT ?""",
                (symbol, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert_minute_bars(self, symbol: str, bars: list[dict]) -> None:
        """Insert or replace minute bars."""
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO minute_price_bar
                   (symbol, datetime, open, high, low, close, volume, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                [
                    (
                        symbol,
                        b["datetime"],
                        b.get("open"),
                        b.get("high"),
                        b.get("low"),
                        b.get("close"),
                        b.get("volume"),
                        now,
                    )
                    for b in bars
                ],
            )

    def classify_symbols(
        self, symbols: list[str]
    ) -> tuple[list[str], list[str], list[str]]:
        """Split symbols into (need_full, need_update, fresh).

        need_full   — no data or >FULL_REFRESH_STALE_DAYS old
        need_update — 2–FULL_REFRESH_STALE_DAYS days behind
        fresh       — 0–1 day behind (up to date)
        """
        need_full, need_update, fresh = [], [], []
        today = date.today()
        for sym in symbols:
            latest = self.latest_bar_date(sym)
            if latest is None:
                need_full.append(sym)
            else:
                behind = (today - latest).days
                if behind > FULL_REFRESH_STALE_DAYS:
                    need_full.append(sym)
                elif behind <= 1:
                    fresh.append(sym)
                else:
                    need_update.append(sym)
        return need_full, need_update, fresh

    # ── Company Profiles ──────────────────────────────────────────────────────

    def get_profile(self, symbol: str, ttl_days: int = 7) -> Optional[dict]:
        cutoff = (datetime.utcnow() - timedelta(days=ttl_days)).isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM company_profile WHERE symbol = ? AND fetched_at >= ?",
                (symbol, cutoff),
            ).fetchone()
        if row:
            return {
                "symbol": row["symbol"],
                "companyName": row["name"],
                "sector": row["sector"],
                "industry": row["industry"],
                "mktCap": row["market_cap"],
                "price": row["price"],
                "exchangeShortName": row["exchange"],
            }
        return None

    def get_profiles_batch(
        self, symbols: list[str], ttl_days: int = 7
    ) -> tuple[dict, list[str]]:
        """Return (cached_dict, symbols_needing_fetch)."""
        cached: dict = {}
        missing: list[str] = []
        for sym in symbols:
            p = self.get_profile(sym, ttl_days)
            if p:
                cached[sym] = p
            else:
                missing.append(sym)
        return cached, missing

    def upsert_profile(self, symbol: str, profile: dict) -> None:
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO company_profile
                   (symbol, name, sector, industry, market_cap, price, exchange, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    symbol,
                    profile.get("companyName") or profile.get("name"),
                    profile.get("sector"),
                    profile.get("industry"),
                    profile.get("mktCap") or profile.get("market_cap"),
                    profile.get("price"),
                    profile.get("exchangeShortName") or profile.get("exchange"),
                    now,
                ),
            )

    def upsert_profiles(self, profiles: dict) -> None:
        for sym, p in profiles.items():
            self.upsert_profile(sym, p)

    # ── Earnings Scan ─────────────────────────────────────────────────────────

    def get_earnings_scan(
        self, symbol: str, ttl_hours: float = 24.0
    ) -> tuple[bool, Optional[dict]]:
        """Return (is_cached, result).

        is_cached=False → need to re-scan this symbol.
        result=None     → cached "no earnings found".
        result=dict     → cached earnings entry.
        """
        cutoff = (datetime.utcnow() - timedelta(hours=ttl_hours)).isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM earnings_scan WHERE symbol = ? AND checked_at >= ?",
                (symbol, cutoff),
            ).fetchone()
        if row is None:
            return False, None
        if row["found_date"]:
            return True, {
                "symbol": symbol,
                "date": row["found_date"],
                "time": row["timing"] or "unknown",
            }
        return True, None  # cached "nothing found"

    def save_earnings_scan(self, symbol: str, result: Optional[dict]) -> None:
        """result=None means 'checked, found nothing'."""
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO earnings_scan
                   (symbol, checked_at, found_date, timing) VALUES (?,?,?,?)""",
                (
                    symbol,
                    now,
                    result["date"] if result else None,
                    result.get("time") if result else None,
                ),
            )

    def classify_earnings_symbols(
        self, symbols: list[str], ttl_hours: float = 24.0
    ) -> tuple[list[dict], list[str]]:
        """Split into (cached_results, symbols_needing_scan).

        cached_results contains only non-None results (earnings found).
        """
        cached_results: list[dict] = []
        need_scan: list[str] = []
        for sym in symbols:
            is_cached, result = self.get_earnings_scan(sym, ttl_hours)
            if is_cached:
                if result:
                    cached_results.append(result)
            else:
                need_scan.append(sym)
        return cached_results, need_scan

    # ── Universe ──────────────────────────────────────────────────────────────

    def get_universe(self, ttl_days: int = 30) -> Optional[list[str]]:
        """Return cached symbol list or None if stale/empty."""
        cutoff = (datetime.utcnow() - timedelta(days=ttl_days)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT symbol FROM universe WHERE fetched_at >= ? ORDER BY symbol",
                (cutoff,),
            ).fetchall()
        return [r["symbol"] for r in rows] if rows else None

    def save_universe(self, constituents: list[dict]) -> None:
        """constituents: list of {symbol, name?, sector?}."""
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute("DELETE FROM universe")
            conn.executemany(
                "INSERT INTO universe (symbol, name, sector, fetched_at) VALUES (?,?,?,?)",
                [
                    (c["symbol"], c.get("name", ""), c.get("sector", ""), now)
                    for c in constituents
                ],
            )

    def save_universe_symbols(self, symbols: list[str]) -> None:
        self.save_universe([{"symbol": s} for s in symbols])

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        with self._conn() as conn:
            n_syms = conn.execute(
                "SELECT COUNT(DISTINCT symbol) FROM price_bar"
            ).fetchone()[0]
            n_bars = conn.execute("SELECT COUNT(*) FROM price_bar").fetchone()[0]
            n_prof = conn.execute("SELECT COUNT(*) FROM company_profile").fetchone()[0]
            n_earn = conn.execute("SELECT COUNT(*) FROM earnings_scan").fetchone()[0]
            n_univ = conn.execute("SELECT COUNT(*) FROM universe").fetchone()[0]
            oldest = conn.execute(
                "SELECT MIN(date) FROM price_bar"
            ).fetchone()[0]
            newest = conn.execute(
                "SELECT MAX(date) FROM price_bar"
            ).fetchone()[0]
        return {
            "symbols_with_prices": n_syms,
            "total_price_bars": n_bars,
            "oldest_bar": oldest,
            "newest_bar": newest,
            "cached_profiles": n_prof,
            "earnings_scans": n_earn,
            "universe_size": n_univ,
            "db_path": self.db_path,
        }
