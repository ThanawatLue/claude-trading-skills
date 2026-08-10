"""Earnings date lookup with multi-source fallback for Dual-Check."""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from typing import Any


def _parse_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


def _symbol_variants(symbol: str) -> list[str]:
    symbol = (symbol or "").strip()
    if not symbol:
        return []
    variants = [symbol]
    if symbol.endswith(".BK"):
        variants.append(symbol[:-3])
    else:
        # Thai tickers often need .BK for yfinance
        if symbol.isalpha() and symbol.upper() == symbol and len(symbol) <= 10:
            variants.append(f"{symbol}.BK")
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for item in variants:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _from_yfinance(symbol: str) -> dict[str, Any] | None:
    try:
        import yfinance as yf
    except ImportError:
        return None

    for sym in _symbol_variants(symbol):
        try:
            ticker = yf.Ticker(sym)
            earnings_date = None

            cal = getattr(ticker, "calendar", None)
            if isinstance(cal, dict):
                key = next((k for k in cal.keys() if str(k).lower() == "earnings date"), None)
                if key:
                    dates = cal[key]
                    if dates is not None and len(dates) > 0:
                        earnings_date = _parse_date(dates[0])
            elif cal is not None:
                # pandas DataFrame-like
                try:
                    if hasattr(cal, "empty") and not cal.empty:
                        if "Earnings Date" in cal.index:
                            val = cal.loc["Earnings Date"]
                            if hasattr(val, "iloc"):
                                val = val.iloc[0]
                            earnings_date = _parse_date(val)
                except Exception:
                    pass

            if not earnings_date:
                try:
                    ed = ticker.get_earnings_dates(limit=8)
                    if ed is not None and hasattr(ed, "index") and len(ed.index) > 0:
                        today = date.today()
                        for idx in ed.index:
                            parsed = _parse_date(idx)
                            if not parsed:
                                continue
                            if date.fromisoformat(parsed) >= today:
                                earnings_date = parsed
                                break
                except Exception:
                    pass

            if earnings_date:
                return {
                    "symbol": symbol,
                    "date": earnings_date,
                    "time": "unknown",
                    "source": f"yfinance:{sym}",
                    "verified": True,
                }
        except Exception:
            continue
    return None


def _from_fmp(symbol: str) -> dict[str, Any] | None:
    api_key = os.environ.get("FMP_API_KEY") or os.environ.get("FMP_KEY")
    if not api_key:
        return None
    try:
        import requests
    except ImportError:
        return None

    base = symbol.replace(".BK", "")
    # FMP uses bare ticker for US; Thai often SYMBOL.BK
    for query_sym in (symbol, base, f"{base}.BK"):
        try:
            start = date.today().isoformat()
            end = (date.today() + timedelta(days=90)).isoformat()
            url = "https://financialmodelingprep.com/stable/earnings-calendar"
            resp = requests.get(
                url,
                params={"from": start, "to": end, "apikey": api_key, "symbol": query_sym},
                timeout=12,
            )
            if resp.status_code != 200:
                # fallback older endpoint
                url2 = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{query_sym}"
                resp = requests.get(url2, params={"apikey": api_key}, timeout=12)
            if resp.status_code != 200:
                continue
            payload = resp.json()
            if not isinstance(payload, list) or not payload:
                continue
            today = date.today()
            upcoming: list[tuple[date, dict]] = []
            for row in payload:
                if not isinstance(row, dict):
                    continue
                row_sym = str(row.get("symbol") or "").upper()
                if row_sym and row_sym not in {
                    query_sym.upper(),
                    base.upper(),
                    f"{base}.BK".upper(),
                }:
                    # calendar endpoint may return many symbols when filter ignored
                    if "symbol" in row and row_sym != query_sym.upper():
                        continue
                d = _parse_date(row.get("date") or row.get("earningsDate"))
                if not d:
                    continue
                dd = date.fromisoformat(d)
                if dd >= today:
                    upcoming.append((dd, row))
            if not upcoming:
                continue
            upcoming.sort(key=lambda item: item[0])
            best_date, best_row = upcoming[0]
            return {
                "symbol": symbol,
                "date": best_date.isoformat(),
                "time": best_row.get("time") or "unknown",
                "source": f"fmp:{query_sym}",
                "verified": True,
            }
        except Exception:
            continue
    return None


def lookup_earnings(
    symbol: str,
    *,
    cache: Any | None = None,
    ttl_hours: float = 24.0,
    allow_network: bool = True,
) -> dict[str, Any]:
    """Return earnings metadata with verified flag.

    Cache stores either a result dict or None (negative cache).
    """
    symbol = (symbol or "").strip()
    empty = {
        "symbol": symbol,
        "date": None,
        "days_to_earnings": None,
        "source": None,
        "verified": False,
    }
    if not symbol:
        return empty

    if cache is not None:
        try:
            is_cached, cached_res = cache.get_earnings_scan(symbol, ttl_hours=ttl_hours)
            if is_cached:
                if not cached_res:
                    return dict(empty)
                out = dict(cached_res)
                out.setdefault("symbol", symbol)
                out.setdefault("verified", bool(out.get("date")))
                if out.get("date"):
                    try:
                        out["days_to_earnings"] = (
                            date.fromisoformat(str(out["date"])[:10]) - date.today()
                        ).days
                    except Exception:
                        out["days_to_earnings"] = None
                return out
        except Exception as exc:
            print(f"earnings cache read failed for {symbol}: {exc}", file=sys.stderr)

    found: dict[str, Any] | None = None
    if allow_network:
        found = _from_yfinance(symbol) or _from_fmp(symbol)

    if found and found.get("date"):
        try:
            found["days_to_earnings"] = (
                date.fromisoformat(str(found["date"])[:10]) - date.today()
            ).days
        except Exception:
            found["days_to_earnings"] = None
        if cache is not None:
            try:
                cache.save_earnings_scan(symbol, found)
            except Exception as exc:
                print(f"earnings cache write failed for {symbol}: {exc}", file=sys.stderr)
        return found

    if cache is not None:
        try:
            cache.save_earnings_scan(symbol, None)
        except Exception:
            pass
    return dict(empty)
