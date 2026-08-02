"""Shared fixtures for FTD Detector tests"""

import os
import sys
from pathlib import Path

# Add scripts directory to path so modules can be imported
SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

# Multiple skills historically expose a top-level ``fmp_client`` module.
# Purge a previously imported sibling module before this suite imports its
# local implementation, otherwise monkeypatches target the wrong class.
loaded_fmp = sys.modules.get("fmp_client")
if loaded_fmp is not None:
    loaded_path = getattr(loaded_fmp, "__file__", None)
    if not loaded_path or Path(loaded_path).resolve() != SCRIPT_DIR / "fmp_client.py":
        del sys.modules["fmp_client"]
# Add tests directory to path so helpers can be imported
sys.path.insert(0, os.path.dirname(__file__))
