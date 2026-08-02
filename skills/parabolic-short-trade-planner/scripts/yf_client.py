"""Compatibility entry point for the shared Yahoo Finance client."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.lib.yf_client import ApiCallBudgetExceeded, YFClient

__all__ = ["ApiCallBudgetExceeded", "YFClient"]
