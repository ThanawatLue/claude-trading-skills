#!/usr/bin/env python3
"""
Thai Fundamental Data Client — wraps thaifin for SET market fundamentals.

Provides EPS, revenue, and growth data for Thai stocks via the thaifin
library (pip install thaifin), which fetches data from SET's public portal.

Optional dependency: thaifin
Falls back gracefully to an empty result if the package is not installed.

Usage:
    from thai_fundamental_client import ThaiFinClient
    client = ThaiFinClient()
    profile = client.get_profile("AOT")      # No .BK suffix needed
    eps = client.get_eps_growth("AOT")
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_THAIFIN_AVAILABLE = False
try:
    from thaifin import Stock  # noqa: F401

    _THAIFIN_AVAILABLE = True
except ImportError:
    pass


class ThaiFinClient:
    """Wrapper around thaifin for CANSLIM fundamental analysis of Thai stocks."""

    def __init__(self):
        if not _THAIFIN_AVAILABLE:
            logger.warning(
                "thaifin not installed. Run: pip install thaifin. "
                "Thai fundamental data will be unavailable."
            )

    @staticmethod
    def is_available() -> bool:
        return _THAIFIN_AVAILABLE

    @staticmethod
    def _clean_symbol(symbol: str) -> str:
        """Strip .BK suffix that yfinance uses."""
        return symbol.replace(".BK", "").upper()

    def get_profile(self, symbol: str) -> Optional[dict]:
        """
        Get company profile: name, sector, industry, market.

        Returns:
            Dict with profile fields, or None on failure.
        """
        if not _THAIFIN_AVAILABLE:
            return None

        clean = self._clean_symbol(symbol)
        try:
            from thaifin import Stock  # noqa: F811

            s = Stock(clean)
            return {
                "symbol": symbol,
                "company_name": s.company_name,
                "sector": s.sector,
                "industry": s.industry,
                "market": s.market,
                "website": s.website,
            }
        except Exception as e:
            logger.debug("thaifin profile error for %s: %s", symbol, e)
            return None

    def get_yearly_financials(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get yearly financial statements as a DataFrame.

        Columns vary by SET disclosure but typically include:
        Revenue, NetProfit, EPS, DPS, ROE, D/E, etc.

        Returns:
            DataFrame indexed by year, or None on failure.
        """
        if not _THAIFIN_AVAILABLE:
            return None

        clean = self._clean_symbol(symbol)
        try:
            from thaifin import Stock  # noqa: F811

            s = Stock(clean)
            df = s.yearly_dataframe
            return df if df is not None and not df.empty else None
        except Exception as e:
            logger.debug("thaifin yearly financials error for %s: %s", symbol, e)
            return None

    def get_quarterly_financials(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get quarterly financial statements as a DataFrame.

        Returns:
            DataFrame indexed by quarter, or None on failure.
        """
        if not _THAIFIN_AVAILABLE:
            return None

        clean = self._clean_symbol(symbol)
        try:
            from thaifin import Stock  # noqa: F811

            s = Stock(clean)
            df = s.quarter_dataframe
            return df if df is not None and not df.empty else None
        except Exception as e:
            logger.debug("thaifin quarterly financials error for %s: %s", symbol, e)
            return None

    def get_eps_growth(self, symbol: str, periods: int = 4) -> Optional[dict]:
        """
        Calculate recent EPS growth rate for CANSLIM 'E' factor.

        Args:
            symbol: Thai stock symbol (with or without .BK)
            periods: Number of years to look back

        Returns:
            Dict with eps_values, yoy_growth_pct, avg_growth_pct, or None.
        """
        df = self.get_yearly_financials(symbol)
        if df is None:
            return None

        # Try to find EPS column (thaifin column names vary by version)
        eps_col = None
        for candidate in ["EPS", "eps", "Earnings Per Share", "กำไรต่อหุ้น"]:
            if candidate in df.columns:
                eps_col = candidate
                break

        if eps_col is None:
            return None

        try:
            eps_series = df[eps_col].dropna().head(periods)
            if len(eps_series) < 2:
                return None

            eps_values = eps_series.tolist()
            growths = []
            for i in range(len(eps_values) - 1):
                prev = eps_values[i + 1]
                curr = eps_values[i]
                if prev and prev != 0:
                    growths.append((curr - prev) / abs(prev) * 100)

            return {
                "eps_values": eps_values,
                "yoy_growth_pct": growths,
                "avg_growth_pct": sum(growths) / len(growths) if growths else None,
                "latest_eps": eps_values[0] if eps_values else None,
            }
        except Exception as e:
            logger.debug("EPS growth calc error for %s: %s", symbol, e)
            return None

    def get_revenue_growth(self, symbol: str, periods: int = 4) -> Optional[dict]:
        """
        Calculate recent revenue growth rate for CANSLIM 'A' factor.

        Returns:
            Dict with revenue_values, yoy_growth_pct, avg_growth_pct, or None.
        """
        df = self.get_yearly_financials(symbol)
        if df is None:
            return None

        rev_col = None
        for candidate in ["Revenue", "revenue", "Total Revenue", "รายได้รวม", "รายได้"]:
            if candidate in df.columns:
                rev_col = candidate
                break

        if rev_col is None:
            return None

        try:
            rev_series = df[rev_col].dropna().head(periods)
            if len(rev_series) < 2:
                return None

            rev_values = rev_series.tolist()
            growths = []
            for i in range(len(rev_values) - 1):
                prev = rev_values[i + 1]
                curr = rev_values[i]
                if prev and prev != 0:
                    growths.append((curr - prev) / abs(prev) * 100)

            return {
                "revenue_values": rev_values,
                "yoy_growth_pct": growths,
                "avg_growth_pct": sum(growths) / len(growths) if growths else None,
                "latest_revenue": rev_values[0] if rev_values else None,
            }
        except Exception as e:
            logger.debug("Revenue growth calc error for %s: %s", symbol, e)
            return None
