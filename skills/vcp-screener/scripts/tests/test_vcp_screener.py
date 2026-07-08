import os
import sqlite3

# Add parent directory to path for imports
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from screen_vcp import build_near_misses, get_recent_expectancy, summarize_near_miss


class TestGetRecentExpectancy:
    """Tests for the get_recent_expectancy function."""

    @pytest.fixture
    def mock_sqlite3(self):
        """Mocks sqlite3.connect and its cursor/row factory."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.execute.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_sql = MagicMock()
            mock_sql.connect = mock_connect
            yield mock_sql, mock_conn, mock_cursor

    @pytest.fixture
    def mock_db_path(self):
        """Mocks Path.exists() for the database file."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            mock_helper = MagicMock()
            mock_helper.exists = mock_exists
            yield mock_helper

    def test_no_db_file(self, mock_db_path):
        """Should return None, 0 if db file does not exist."""
        mock_db_path.exists.return_value = False
        expectancy, count = get_recent_expectancy("vcp-screener")
        assert expectancy is None
        assert count == 0

    def test_no_paper_trade_table(self, mock_sqlite3, mock_db_path):
        """Should return None, 0 if paper_trade table does not exist."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_cursor.fetchone.return_value = None  # No table found

        expectancy, count = get_recent_expectancy("vcp-screener")
        assert expectancy is None
        assert count == 0
        mock_cursor.execute.assert_called_with(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trade'"
        )

    def test_empty_paper_trade_table(self, mock_sqlite3, mock_db_path):
        """Should return None, 0 if paper_trade table is empty."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_cursor.fetchone.return_value = MagicMock()  # Table exists
        mock_cursor.fetchall.return_value = []  # No rows in table

        expectancy, count = get_recent_expectancy("vcp-screener")
        assert expectancy is None
        assert count == 0
        mock_cursor.execute.assert_called_with(
            """SELECT realized_r FROM paper_trade
               WHERE (source = ? OR source = ?) AND status != 'open'
               ORDER BY exit_at DESC LIMIT ?""",
            ("vcp-screener", "vcp", 15),
        )

    def test_valid_data_calculates_expectancy(self, mock_sqlite3, mock_db_path):
        """Should calculate correct expectancy with valid data."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_cursor.fetchone.return_value = MagicMock()  # Table exists
        # Simulate rows with realized_r values
        mock_cursor.fetchall.return_value = [
            {"realized_r": 2.0},
            {"realized_r": -1.0},
            {"realized_r": 3.0},
        ]

        expectancy, count = get_recent_expectancy("vcp-screener", lookback=3)
        assert expectancy == (2.0 - 1.0 + 3.0) / 3
        assert count == 3

    def test_mixed_data_filters_none(self, mock_sqlite3, mock_db_path):
        """Should filter out None realized_r values."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_cursor.fetchone.return_value = MagicMock()  # Table exists
        mock_cursor.fetchall.return_value = [
            {"realized_r": 2.0},
            {"realized_r": None},
            {"realized_r": 3.0},
        ]

        expectancy, count = get_recent_expectancy("vcp-screener", lookback=3)
        assert expectancy == (2.0 + 3.0) / 2
        assert count == 2

    def test_source_filtering(self, mock_sqlite3, mock_db_path):
        """Should correctly filter by source or source.replace."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_cursor.fetchone.return_value = MagicMock()  # Table exists
        mock_cursor.fetchall.return_value = [{"realized_r": 1.0}]

        get_recent_expectancy("my-custom-screener", lookback=1)
        mock_cursor.execute.assert_called_with(
            """SELECT realized_r FROM paper_trade
               WHERE (source = ? OR source = ?) AND status != 'open'
               ORDER BY exit_at DESC LIMIT ?""",
            ("my-custom-screener", "my-custom", 1),
        )

    def test_db_error_handling(self, mock_sqlite3, mock_db_path, capsys):
        """Should handle database errors gracefully and print warning."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_sql.connect.side_effect = sqlite3.Error("Test DB Error")

        expectancy, count = get_recent_expectancy("vcp-screener")
        assert expectancy is None
        assert count == 0

        captured = capsys.readouterr()
        assert "Could not read paper trade stats: Test DB Error" in captured.err

    def test_no_realized_r_values(self, mock_sqlite3, mock_db_path):
        """Should return None, 0 if no rows have non-None realized_r."""
        mock_sql, mock_conn, mock_cursor = mock_sqlite3
        mock_cursor.fetchone.return_value = MagicMock()  # Table exists
        mock_cursor.fetchall.return_value = [
            {"realized_r": None},
            {"realized_r": None},
        ]

        expectancy, count = get_recent_expectancy("vcp-screener", lookback=2)
        assert expectancy is None
        assert count == 0


def test_summarize_near_miss_explains_vcp_failures():
    result = {
        "symbol": "ABC",
        "company_name": "ABC Corp",
        "sector": "Tech",
        "price": 100,
        "composite_score": 62,
        "valid_vcp": False,
        "entry_ready": False,
        "execution_state": "Extended",
        "vcp_pattern": {
            "score": 10,
            "num_contractions": 1,
            "pivot_price": 105,
            "error": "Fewer than 2 contractions found",
        },
        "volume_pattern": {"score": 20, "dry_up_ratio": 1.4},
        "pivot_proximity": {"score": 30, "risk_pct": 18},
        "relative_strength": {"score": 70},
        "trend_template": {"score": 88},
        "distance_from_pivot_pct": 6.0,
    }

    near_miss = summarize_near_miss(result)

    assert near_miss["symbol"] == "ABC"
    assert "Fewer than 2 contractions found" in near_miss["reasons"]
    assert any("volume not dry enough" in reason for reason in near_miss["reasons"])
    assert any("pivot distance" in reason for reason in near_miss["reasons"])


def test_build_near_misses_keeps_highest_ranked_items():
    low = {"symbol": "LOW", "composite_score": 40, "valid_vcp": False, "entry_ready": False}
    high = {"symbol": "HIGH", "composite_score": 80, "valid_vcp": False, "entry_ready": False}

    rows = build_near_misses([low, high], limit=1)

    assert [row["symbol"] for row in rows] == ["HIGH"]
