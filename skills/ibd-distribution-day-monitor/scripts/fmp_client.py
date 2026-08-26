"""Compatibility entry point for the shared FMP client."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import scripts.lib.fmp_client as _shared
from scripts.lib.fmp_client import ApiCallBudgetExceeded, FMPClient

requests = _shared.requests

__all__ = ["ApiCallBudgetExceeded", "FMPClient", "requests"]
