"""Compatibility entry point for the shared FMP client (PEAD dict return shape)."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import scripts.lib.fmp_client as _shared
from scripts.lib.fmp_client import ApiCallBudgetExceeded
from scripts.lib.fmp_client import FMPClient as _BaseFMPClient

requests = _shared.requests


class FMPClient(_BaseFMPClient):
    """PEAD screener expects v3-compatible dicts from get_historical_prices."""

    def get_historical_prices(self, symbol: str, days: int = 250) -> dict | None:
        cache_key = f"prices_{symbol}_{days}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if isinstance(cached, dict):
                return cached
            return {"symbol": symbol, "historical": cached}

        data = self._request_with_fallback("historical", symbol, {"timeseries": days})
        if data and "historical" in data:
            self.cache[cache_key] = data
            return data
        return None


__all__ = ["ApiCallBudgetExceeded", "FMPClient", "requests"]
