"""Integration tests for generate_heatmap.py.

These tests call the main() function with mocked external dependencies (TradingView API calls)
and verify the generation of output files (JSON and Markdown) and their content.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import generate_heatmap  # noqa: E402


@pytest.fixture
def mock_tv_client():
    """Mocks the tv_client functions used by generate_heatmap.py."""
    with mock.patch("generate_heatmap.get_thai_stocks") as mock_get_thai_stocks, 
         mock.patch("generate_heatmap.filter_common_stocks") as mock_filter_common_stocks, 
         mock.patch("generate_heatmap.tv_available") as mock_tv_available:

        mock_tv_available.return_value = True
        mock_get_thai_stocks.return_value = [
            # Tech sector
            {"symbol": "A", "sector": "Tech", "price": 10.0, "perf_1m": 5.0, "perf_3m": 10.0, "perf_6m": 15.0, "perf_y": 20.0, "name": "Stock A"},
            {"symbol": "B", "sector": "Tech", "price": 12.0, "perf_1m": 7.0, "perf_3m": 12.0, "perf_6m": 18.0, "perf_y": 22.0, "name": "Stock B"},
            {"symbol": "C", "sector": "Tech", "price": 8.0, "perf_1m": 3.0, "perf_3m": 8.0, "perf_6m": 10.0, "perf_y": 15.0, "name": "Stock C"},
            # Energy sector
            {"symbol": "D", "sector": "Energy", "price": 20.0, "perf_1m": -2.0, "perf_3m": -5.0, "perf_6m": -10.0, "perf_y": -15.0, "name": "Stock D"},
            {"symbol": "E", "sector": "Energy", "price": 22.0, "perf_1m": -1.0, "perf_3m": -4.0, "perf_6m": -8.0, "perf_y": -12.0, "name": "Stock E"},
            {"symbol": "F", "sector": "Energy", "price": 18.0, "perf_1m": -3.0, "perf_3m": -6.0, "perf_6m": -12.0, "perf_y": -18.0, "name": "Stock F"},
            # Finance sector (fewer than min_stocks_per_sector)
            {"symbol": "G", "sector": "Finance", "price": 5.0, "perf_1m": 1.0, "perf_3m": 2.0, "perf_6m": 3.0, "perf_y": 4.0, "name": "Stock G"},
            {"symbol": "H", "sector": "Finance", "price": 6.0, "perf_1m": 2.0, "perf_3m": 3.0, "perf_6m": 4.0, "perf_y": 5.0, "name": "Stock H"},
            # Stock with price below MIN_STOCK_PRICE
            {"symbol": "I", "sector": "Tech", "price": 0.5, "perf_1m": 1.0, "perf_3m": 2.0, "perf_6m": 3.0, "perf_y": 4.0, "name": "Stock I"},
        ]
        # filter_common_stocks just passes through in this mock setup
        mock_filter_common_stocks.side_effect = lambda x: x
        yield


@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for output files and cleans it up afterwards."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_main_generates_files(mock_tv_client, temp_output_dir):
    """Test that main() correctly generates JSON and Markdown files."""
    # Simulate command-line arguments
    test_args = [
        "generate_heatmap.py",  # Script name
        "--output-dir", str(temp_output_dir),
        "--min-stocks", "2",  # To include Finance sector in mock data
        "--w-1m", "0.5",
        "--w-3m", "0.25",
        "--w-6m", "0.15",
        "--w-y", "0.10",
        "--min-price", "1.0",
    ]
    with mock.patch.object(sys, "argv", test_args):
        generate_heatmap.main()

    # Verify JSON file
    json_files = list(temp_output_dir.glob("*.json"))
    assert len(json_files) == 1
    json_path = json_files[0]
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "sectors" in data
    assert len(data["sectors"]) > 0
    assert data["min_stock_price"] == 1.0
    assert data["weights"] == {"1m": 0.5, "3m": 0.25, "6m": 0.15, "y": 0.10}

    # Verify Markdown file
    md_files = list(temp_output_dir.glob("*.md"))
    assert len(md_files) == 1
    md_path = md_files[0]
    assert md_path.exists()

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# Thai Sector Heatmap" in content
    assert "## Sector Momentum Ranking" in content
    assert "## Top 5 Sectors — Leading Stocks" in content
    assert "## Methodology" in content
    assert f"- **Minimum stock price:** {generate_heatmap.MIN_STOCK_PRICE:.2f} THB" in content
    assert f"- **Momentum score:** {0.5:.0%}×1M + {0.25:.0%}×3M + {0.15:.0%}×6M + {0.10:.0%}×1Y" in content

    # Check for specific sector presence and ranking in Markdown
    # Tech sector should have higher momentum given mocked data
    assert "Tech" in content
    assert "Energy" in content
    assert "Finance" not in content # Should be filtered out by min_stocks_per_sector = 3 by default, unless overriden by argument.
    # We overrode min_stocks to 2, so Finance should be there
    assert "Finance" in content

    # Check for top stocks in markdown
    assert "- **B** Stock B — 3M: 12.00% @ 12.00 THB" in content # Tech's top stock based on 3m perf in mock_tv_client

    # Check that stock I (price 0.5) is filtered out and not in any sector's top stocks.
    assert "Stock I" not in content


def test_main_with_different_min_price_filter(mock_tv_client, temp_output_dir):
    """Test main() with a higher min-price to ensure filtering works."""
    test_args = [
        "generate_heatmap.py",
        "--output-dir", str(temp_output_dir),
        "--min-stocks", "2",
        "--min-price", "10.0",  # Set min price higher
    ]
    with mock.patch.object(sys, "argv", test_args):
        generate_heatmap.main()

    json_files = list(temp_output_dir.glob("*.json"))
    assert len(json_files) == 1
    json_path = json_files[0]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Stock A, B, C (Tech) have prices 10, 12, 8. Stock C should be filtered out.
    # Stock D, E, F (Energy) have prices 20, 22, 18. None should be filtered out.
    # Stock G, H (Finance) have prices 5, 6. Both should be filtered out.
    # Stock I (Tech) has price 0.5. Should be filtered out.
    # Expected stocks after filtering: A, B, D, E, F (5 stocks)
    expected_universe_size = 5 # A, B, D, E, F (C, G, H, I filtered)
    assert data["universe_size"] == expected_universe_size
    assert data["min_stock_price"] == 10.0

    md_files = list(temp_output_dir.glob("*.md"))
    assert len(md_files) == 1
    md_path = md_files[0]

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "- **Minimum stock price:** 10.00 THB" in content
    assert "Stock C" not in content # Should be filtered out
    assert "Finance" not in content # Both Finance stocks are below 10.0


def test_main_with_different_momentum_weights(mock_tv_client, temp_output_dir):
    """Test main() with different momentum weights."""
    test_args = [
        "generate_heatmap.py",
        "--output-dir", str(temp_output_dir),
        "--min-stocks", "2",
        "--w-1m", "0.1",
        "--w-3m", "0.2",
        "--w-6m", "0.3",
        "--w-y", "0.4",
    ]
    with mock.patch.object(sys, "argv", test_args):
        generate_heatmap.main()

    json_files = list(temp_output_dir.glob("*.json"))
    assert len(json_files) == 1
    json_path = json_files[0]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["weights"] == {"1m": 0.1, "3m": 0.2, "6m": 0.3, "y": 0.4}

    # Recalculate expected momentum scores based on new weights and mock data
    # Tech stocks: A (5,10,15,20), B (7,12,18,22), C (3,8,10,15)
    # Median Tech: perf_1m=5, perf_3m=10, perf_6m=15, perf_y=20
    # Energy stocks: D (-2,-5,-10,-15), E (-1,-4,-8,-12), F (-3,-6,-12,-18)
    # Median Energy: perf_1m=-2, perf_3m=-5, perf_6m=-10, perf_y=-15
    # Finance stocks: G (1,2,3,4), H (2,3,4,5)
    # Median Finance: perf_1m=1.5, perf_3m=2.5, perf_6m=3.5, perf_y=4.5

    # Tech momentum: 0.1*5 + 0.2*10 + 0.3*15 + 0.4*20 = 0.5 + 2 + 4.5 + 8 = 15.0
    # Energy momentum: 0.1*-2 + 0.2*-5 + 0.3*-10 + 0.4*-15 = -0.2 - 1 - 3 - 6 = -10.2
    # Finance momentum: 0.1*1.5 + 0.2*2.5 + 0.3*3.5 + 0.4*4.5 = 0.15 + 0.5 + 1.05 + 1.8 = 3.5

    # Tech should still be ranked first due to positive performance
    tech_sector_data = next(s for s in data["sectors"] if s["sector"] == "Tech")
    energy_sector_data = next(s for s in data["sectors"] if s["sector"] == "Energy")
    finance_sector_data = next(s for s in data["sectors"] if s["sector"] == "Finance")

    assert tech_sector_data["momentum_score"] == pytest.approx(15.0)
    assert energy_sector_data["momentum_score"] == pytest.approx(-10.2)
    assert finance_sector_data["momentum_score"] == pytest.approx(3.5)

    assert tech_sector_data["rank"] == 1
    assert finance_sector_data["rank"] == 2
    assert energy_sector_data["rank"] == 3

    md_files = list(temp_output_dir.glob("*.md"))
    assert len(md_files) == 1
    md_path = md_files[0]

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "- **Momentum score:** 10%×1M + 20%×3M + 30%×6M + 40%×1Y" in content
    assert "Tech" in content
    assert "Energy" in content
    assert "Finance" in content
