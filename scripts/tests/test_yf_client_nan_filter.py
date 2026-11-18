"""Tests for YFClient NaN-row filtering on incomplete trailing market bars."""

from __future__ import annotations

import pandas as pd


def test_get_historical_prices_drops_nan_close_rows(monkeypatch):
    from scripts.lib import yf_client

    dates = pd.to_datetime(["2026-11-14", "2026-11-15", "2026-11-16", "2026-11-17"])
    mock_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, float("nan")],
            "High": [101.0, 102.0, 103.0, float("nan")],
            "Low": [99.0, 100.0, 101.0, float("nan")],
            "Close": [100.5, 101.5, 102.5, float("nan")],
            "Volume": [1000, 1100, 1200, 500],
        },
        index=dates,
    )

    monkeypatch.setattr(yf_client, "_CACHE_OK", False)
    monkeypatch.setattr(yf_client.yf, "download", lambda *a, **kw: mock_df)

    client = yf_client.YFClient()
    res = client.get_historical_prices("SPY", days=10)
    assert res is not None
    hist = res["historical"]
    assert len(hist) == 3
    assert hist[0]["date"] == "2026-11-16"
    assert all(row["close"] == row["close"] for row in hist)
