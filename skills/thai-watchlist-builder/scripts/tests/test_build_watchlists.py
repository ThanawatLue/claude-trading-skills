import pytest
import sys
import build_watchlists
from build_watchlists import to_markdown, has_liquidity, _safe_num, _to_row, in_growth, in_value, in_momentum, in_mean_reversion
from tv_client import is_available


@pytest.fixture
def sample_buckets():
    return {
        "growth": [
            {"symbol": "GROW1", "name": "Growth Stock 1", "sector": "Tech", "price": 100, "rsi": 60, "perf_1m": 5, "perf_3m": 15, "score": 85},
            {"symbol": "GROW2", "name": "Growth Stock 2", "sector": "Finance", "price": 200, "rsi": 65, "perf_1m": 7, "perf_3m": 20, "score": 90},
        ],
        "value": [
            {"symbol": "VAL1", "name": "Value Stock 1", "sector": "Energy", "price": 50, "rsi": 40, "perf_1m": 2, "perf_3m": 8, "score": 75},
        ],
        "momentum": [],
        "mean_reversion": [
            {"symbol": "MR1", "name": "MR Stock 1", "sector": "Industrial", "price": 70, "rsi": 35, "perf_1m": -1, "perf_3m": 3, "score": 60},
        ],
    }

# --- Tests for to_markdown function ---

def test_to_markdown_empty_buckets(sample_buckets):
    empty_buckets = {k: [] for k in sample_buckets.keys()}
    markdown_output = to_markdown(empty_buckets, 0, "2023-01-01_100000", 30)
    assert "No candidates passed the filters." in markdown_output
    assert "GROWTH" in markdown_output
    assert "VALUE" in markdown_output
    assert "MOMENTUM" in markdown_output
    assert "MEAN-REVERSION" in markdown_output
    assert "Total Stocks: 0" not in markdown_output # Should be Universe: 0 SET stocks

def test_to_markdown_full_buckets(sample_buckets):
    markdown_output = to_markdown(sample_buckets, 10, "2023-01-01_100000", 30)

    # Check header and summary table
    assert "**Generated:** 2023-01-01_100000" in markdown_output
    assert "**Universe:** 10 SET stocks  |  **Source:** TradingView" in markdown_output
    assert "| GROWTH | 2 | 87.5 |" in markdown_output
    assert "| VALUE | 1 | 75.0 |" in markdown_output
    assert "| MOMENTUM | 0 | 0.0 |" in markdown_output # Avg score for empty bucket
    assert "| MEAN-REVERSION | 1 | 60.0 |" in markdown_output

    # Check growth section
    assert "## GROWTH - Stage 2 Leaders" in markdown_output
    assert "GROW1" in markdown_output
    assert "GROW2" in markdown_output
    assert "90.0" in markdown_output # Score of GROW2
    assert "85.0" in markdown_output # Score of GROW1

    # Check momentum (empty) section
    assert "## MOMENTUM - Hot Stocks" in markdown_output
    assert "_No candidates passed the filters._" in markdown_output

    # Check table headers and formatting
    assert "| Rank | Symbol | Sector | Price | RSI | 1M% | 3M% | Score |" in markdown_output
    assert "| 1 | GROW2 | Finance | 200.00 | 65 | +7.0% | +20.0% | 90.0 |" in markdown_output # Example row from growth

def test_to_markdown_top_n_limit(sample_buckets):
    # Test with top_n limiting the display, even if buckets have more
    sample_buckets["growth"].append({"symbol": "GROW3", "name": "Growth Stock 3", "sector": "Tech", "price": 150, "rsi": 62, "perf_1m": 6, "perf_3m": 18, "score": 88})
    markdown_output = to_markdown(sample_buckets, 10, "2023-01-01_100000", 1) # Only show top 1

    assert "**Generated:** 2023-01-01_100000" in markdown_output
    assert "**Universe:** 10 SET stocks  |  **Source:** TradingView" in markdown_output
    assert "## GROWTH - Stage 2 Leaders" in markdown_output
    assert "GROW2" in markdown_output # Highest score
    assert "GROW1" not in markdown_output
    assert "GROW3" not in markdown_output

# --- Tests for has_liquidity function ---

@pytest.mark.parametrize(
    "stock, min_turnover, expected",
    [
        ({"avg_turnover": 30_000_000}, 20_000_000, True),
        ({"avg_turnover": 10_000_000}, 20_000_000, False),
        ({"avg_turnover": 20_000_000}, 20_000_000, True),
        ({"avg_turnover": 0, "price": 10, "avgVolume": 1_000_000}, 20_000_000, False), # 10M turnover
        ({"avg_turnover": 0, "price": 100, "avgVolume": 200_000}, 20_000_000, True), # 20M turnover
        ({"avg_turnover": None}, 20_000_000, False),
        ({}, 20_000_000, False),
        ({"price": 10, "avgVolume": 1_000_000, "avg_turnover": None}, 20_000_000, False), # Should use price*avgVolume, resulting in 10M
        ({"price": 100, "avgVolume": 200_000, "avg_turnover": None}, 20_000_000, True), # Should use price*avgVolume, resulting in 20M
    ],
)
def test_has_liquidity(stock, min_turnover, expected):
    assert has_liquidity(stock, min_turnover) == expected


# --- Tests for _safe_num function ---

@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (10, 10.0),
        (0, 0.0),
        (-5, -5.0),
        (10.5, 10.5),
        (None, 0.0),
        ("abc", 0.0),  # Non-numeric string
        ("", 0.0),     # Empty string
        ("123", 123.0), # Numeric string
        (float('nan'), 0.0), # NaN
        (float('inf'), float('inf')), # Infinity
        (float('-inf'), float('-inf')), # Negative infinity
    ],
)
def test_safe_num(input_value, expected_output):
    if expected_output == float('inf'):
        assert _safe_num(input_value) == float('inf')
    elif expected_output == float('-inf'):
        assert _safe_num(input_value) == float('-inf')
    else:
        assert _safe_num(input_value) == expected_output


# --- Tests for _to_row function ---

def test_to_row_all_fields_present():
    stock_data = {
        "symbol": "TEST",
        "name": "Test Stock",
        "sector": "Tech",
        "price": 100,
        "marketCap": 1_000_000_000,
        "avg_turnover": 50_000_000,
        "liquidity_score": 0.8,
        "rsi": 65,
        "sma50": 95,
        "sma200": 80,
        "perf_1m": 5,
        "perf_3m": 15,
        "perf_y": 20,
        "dividend_yield": 3.5,
        "pe_ratio": 12,
        "extra_field": "should not be included",
    }
    score = 99.9
    expected_row = {
        "symbol": "TEST",
        "name": "Test Stock",
        "sector": "Tech",
        "price": 100,
        "marketCap": 1_000_000_000,
        "avg_turnover": 50_000_000,
        "liquidity_score": 0.8,
        "rsi": 65,
        "sma50": 95,
        "sma200": 80,
        "perf_1m": 5,
        "perf_3m": 15,
        "perf_y": 20,
        "dividend_yield": 3.5,
        "pe_ratio": 12,
        "score": 99.9,
    }
    assert _to_row(stock_data, score) == expected_row

def test_to_row_missing_fields():
    stock_data = {
        "symbol": "MISSING",
        "price": 50,
        "rsi": 30,
    }
    score = 50.0
    expected_row = {
        "symbol": "MISSING",
        "name": "MISSING",  # Defaulted to symbol
        "sector": "Unknown", # Defaulted to Unknown
        "price": 50,
        "marketCap": None,
        "avg_turnover": None,
        "liquidity_score": None,
        "rsi": 30,
        "sma50": None,
        "sma200": None,
        "perf_1m": None,
        "perf_3m": None,
        "perf_y": None,
        "dividend_yield": None,
        "pe_ratio": None,
        "score": 50.0,
    }
    assert _to_row(stock_data, score) == expected_row

def test_to_row_name_from_symbol():
    stock_data = {
        "symbol": "SYM",
        "price": 10,
    }
    score = 10.0
    row = _to_row(stock_data, score)
    assert row["name"] == "SYM"



@pytest.mark.parametrize(
    "stock_data, expected_ok, expected_score",
    [
        # Happy path
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, True, 45.0),
        # Below min price
        ({"price": 2, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Price below SMA50
        ({"price": 80, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Price below SMA200
        ({"price": 70, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # perf_3m too low
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 9, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # perf_1m too low
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": -1, "perf_3m": 15, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # RSI too low
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 49, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # RSI too high
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 76, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Market cap too low
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 62, "marketCap": 4_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Low liquidity (avg_turnover)
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "rsi": 62, "marketCap": 6_000_000_000, "avg_turnover": 10_000_000}, False, 0.0),
        # Test score calculation
        ({"price": 100, "sma50": 90, "sma200": 80, "perf_1m": 10, "perf_3m": 20, "rsi": 60, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, True, 51.6),
    ],
)
def test_in_growth(stock_data, expected_ok, expected_score, monkeypatch):
    monkeypatch.setattr("build_watchlists.has_liquidity", lambda s, min_avg_turnover=None: stock_data.get("avg_turnover", 0) >= 20_000_000)
    ok, score = build_watchlists.in_growth(stock_data)
    assert ok == expected_ok
    assert score == expected_score


# --- Tests for in_value function ---

@pytest.mark.parametrize(
    "stock_data, expected_ok, expected_score",
    [
        # Happy path
        ({"price": 50, "sma200": 45, "pe_ratio": 10, "dividend_yield": 4, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, True, 28.8),
        # Below min price
        ({"price": 2, "sma200": 45, "pe_ratio": 10, "dividend_yield": 4, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Price below SMA200
        ({"price": 40, "sma200": 45, "pe_ratio": 10, "dividend_yield": 4, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # PE too low
        ({"price": 50, "sma200": 45, "pe_ratio": 4, "dividend_yield": 4, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # PE too high
        ({"price": 50, "sma200": 45, "pe_ratio": 16, "dividend_yield": 4, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Yield too low
        ({"price": 50, "sma200": 45, "pe_ratio": 10, "dividend_yield": 2, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # perf_y too low
        ({"price": 50, "sma200": 45, "pe_ratio": 10, "dividend_yield": 4, "perf_y": -1, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Market cap too low
        ({"price": 50, "sma200": 45, "pe_ratio": 10, "dividend_yield": 4, "perf_y": 10, "marketCap": 4_000_000_000, "avg_turnover": 30_000_000}, False, 0.0),
        # Low liquidity
        ({"price": 50, "sma200": 45, "pe_ratio": 10, "dividend_yield": 4, "perf_y": 10, "marketCap": 6_000_000_000, "avg_turnover": 10_000_000}, False, 0.0),
        # Test score calculation
        ({"price": 50, "sma200": 45, "pe_ratio": 5, "dividend_yield": 5, "perf_y": 15, "marketCap": 6_000_000_000, "avg_turnover": 30_000_000}, True, 46.0),
    ],
)
def test_in_value(stock_data, expected_ok, expected_score, monkeypatch):
    monkeypatch.setattr("build_watchlists.has_liquidity", lambda s, min_avg_turnover=None: stock_data.get("avg_turnover", 0) >= 20_000_000)
    ok, score = build_watchlists.in_value(stock_data)
    assert ok == expected_ok
    assert score == expected_score


# --- Tests for in_momentum function ---

@pytest.mark.parametrize(
    "stock_data, expected_ok, expected_score",
    [
        # Happy path
        ({"price": 100, "yearHigh": 105, "avgVolume": 100_000, "volume": 160_000, "rsi": 67, "perf_1m": 6, "avg_turnover": 30_000_000}, True, 69.60),
        # Below min price
        ({"price": 2, "yearHigh": 105, "avgVolume": 100_000, "volume": 160_000, "rsi": 67, "perf_1m": 6, "avg_turnover": 30_000_000}, False, 0.0),
        # RSI too low
        ({"price": 100, "yearHigh": 105, "avgVolume": 100_000, "volume": 160_000, "rsi": 59, "perf_1m": 6, "avg_turnover": 30_000_000}, False, 0.0),
        # RSI too high
        ({"price": 100, "yearHigh": 105, "avgVolume": 100_000, "volume": 160_000, "rsi": 79, "perf_1m": 6, "avg_turnover": 30_000_000}, False, 0.0),
        # perf_1m too low
        ({"price": 100, "yearHigh": 105, "avgVolume": 100_000, "volume": 160_000, "rsi": 67, "perf_1m": 4, "avg_turnover": 30_000_000}, False, 0.0),
        # Volume too low
        ({"price": 100, "yearHigh": 105, "avgVolume": 100_000, "volume": 140_000, "rsi": 67, "perf_1m": 6, "avg_turnover": 30_000_000}, False, 0.0),
        # Too far from 52w high
        ({"price": 100, "yearHigh": 120, "avgVolume": 100_000, "volume": 160_000, "rsi": 67, "perf_1m": 6, "avg_turnover": 30_000_000}, False, 0.0),
        # Low liquidity
        ({"price": 100, "yearHigh": 105, "avgVolume": 100_000, "volume": 160_000, "rsi": 67, "perf_1m": 6, "avg_turnover": 10_000_000}, False, 0.0),
        # Test score calculation
        ({"price": 104, "yearHigh": 105, "avgVolume": 100_000, "volume": 200_000, "rsi": 70, "perf_1m": 10, "avg_turnover": 30_000_000}, True, 72.62),
    ],
)
def test_in_momentum(stock_data, expected_ok, expected_score, monkeypatch):
    monkeypatch.setattr("build_watchlists.has_liquidity", lambda s, min_avg_turnover=None: stock_data.get("avg_turnover", 0) >= 20_000_000)
    ok, score = build_watchlists.in_momentum(stock_data)
    assert ok == expected_ok
    assert score == expected_score


# --- Tests for in_mean_reversion function ---

@pytest.mark.parametrize(
    "stock_data, expected_ok, expected_score",
    [
        # Happy path
        ({"price": 95, "sma50": 100, "sma200": 80, "rsi": 35, "perf_y": 10, "avg_turnover": 30_000_000}, True, 31.25),
        # Below min price
        ({"price": 2, "sma50": 100, "sma200": 80, "rsi": 35, "perf_y": 10, "avg_turnover": 30_000_000}, False, 0.0),
        # Price below SMA200
        ({"price": 70, "sma50": 100, "sma200": 80, "rsi": 35, "perf_y": 10, "avg_turnover": 30_000_000}, False, 0.0),
        # RSI too low
        ({"price": 95, "sma50": 100, "sma200": 80, "rsi": 27, "perf_y": 10, "avg_turnover": 30_000_000}, False, 0.0),
        # RSI too high
        ({"price": 95, "sma50": 100, "sma200": 80, "rsi": 41, "perf_y": 10, "avg_turnover": 30_000_000}, False, 0.0),
        # perf_y too low
        ({"price": 95, "sma50": 100, "sma200": 80, "rsi": 35, "perf_y": -1, "avg_turnover": 30_000_000}, False, 0.0),
        # Too far from SMA50
        ({"price": 80, "sma50": 100, "sma200": 80, "rsi": 35, "perf_y": 10, "avg_turnover": 30_000_000}, False, 0.0),
        # Low liquidity
        ({"price": 95, "sma50": 100, "sma200": 80, "rsi": 35, "perf_y": 10, "avg_turnover": 10_000_000}, False, 0.0),
        # Test score calculation
        ({"price": 98, "sma50": 100, "sma200": 80, "rsi": 30, "perf_y": 15, "avg_turnover": 30_000_000}, True, 59.5),
    ],
)
def test_in_mean_reversion(stock_data, expected_ok, expected_score, monkeypatch):
    monkeypatch.setattr("build_watchlists.has_liquidity", lambda s, min_avg_turnover=None: stock_data.get("avg_turnover", 0) >= 20_000_000)
    ok, score = build_watchlists.in_mean_reversion(stock_data)
    assert ok == expected_ok
    assert score == expected_score


# --- End-to-end tests for main function ---
def test_main_function_e2e(tmp_path, monkeypatch):
    monkeypatch.setattr("tv_client.is_available", lambda: True)
    monkeypatch.setattr("build_watchlists.get_thai_stocks", lambda limit: [
        # Growth Stock (Meets growth criteria, avg_turnover=30M for liquidity)
        {"symbol": "GROWTH1.BK", "name": "Growth Stock 1", "sector": "Tech", "price": 100, "marketCap": 6_000_000_000, "avgVolume": 300_000, "avg_turnover": 30_000_000, "rsi": 62, "sma50": 90, "sma200": 80, "perf_1m": 5, "perf_3m": 15, "perf_y": 20, "dividend_yield": 0, "pe_ratio": 20, "yearHigh": 110},
        # Value Stock (Meets value criteria, avg_turnover=30M for liquidity)
        {"symbol": "VALUE1.BK", "name": "Value Stock 1", "sector": "Finance", "price": 50, "marketCap": 6_000_000_000, "avgVolume": 600_000, "avg_turnover": 30_000_000, "rsi": 40, "sma50": 55, "sma200": 45, "perf_1m": 2, "perf_3m": 8, "perf_y": 10, "dividend_yield": 4, "pe_ratio": 10, "yearHigh": 60},
        # Momentum Stock (Meets momentum criteria, avg_turnover=30M for liquidity)
        {"symbol": "MOMEN1.BK", "name": "Momentum Stock 1", "sector": "Energy", "price": 100, "marketCap": 7_000_000_000, "avgVolume": 100_000, "avg_turnover": 30_000_000, "rsi": 67, "sma50": 95, "sma200": 80, "perf_1m": 6, "perf_3m": 10, "perf_y": 15, "dividend_yield": 1, "pe_ratio": 18, "yearHigh": 105, "volume": 160_000},
        # Mean Reversion Stock (Meets mean_reversion criteria, avg_turnover=30M for liquidity)
        {"symbol": "MR1.BK", "name": "Mean Reversion 1", "sector": "Industrial", "price": 95, "marketCap": 5_500_000_000, "avgVolume": 400_000, "avg_turnover": 30_000_000, "rsi": 35, "sma50": 100, "sma200": 80, "perf_1m": -1, "perf_3m": 3, "perf_y": 10, "dividend_yield": 2, "pe_ratio": 16, "yearHigh": 120},
        # Illiquid Stock (Fails liquidity check)
        {"symbol": "ILLIQ.BK", "name": "Illiquid Stock", "sector": "Other", "price": 10, "marketCap": 1_000_000_000, "avgVolume": 10_000, "avg_turnover": 100_000, "rsi": 50, "sma50": 9, "sma200": 8, "perf_1m": 1, "perf_3m": 2, "perf_y": 3, "dividend_yield": 0, "pe_ratio": 10, "yearHigh": 12},
        # Stock that does not fit any bucket but has liquidity (avg_turnover=30M)
        {"symbol": "NONE1.BK", "name": "No Bucket Stock", "sector": "Tech", "price": 100, "marketCap": 6_000_000_000, "avgVolume": 300_000, "avg_turnover": 30_000_000, "rsi": 45, "sma50": 90, "sma200": 80, "perf_1m": -5, "perf_3m": 5, "perf_y": -10, "dividend_yield": 0, "pe_ratio": 20, "yearHigh": 110},
    ])

    # Ensure the temporary output directory exists
    output_dir = tmp_path / "reports"
    output_dir.mkdir()

    # Run the main function
    monkeypatch.setattr(sys, "argv", ["build_watchlists.py", "--output-dir", str(output_dir), "--top", "2"])
    build_watchlists.main()

    # Assert output files are created
    json_files = list(output_dir.glob("*.json"))
    md_files = list(output_dir.glob("*.md"))
    assert len(json_files) == 1
    assert len(md_files) == 1

    # Detailed content validation for JSON
    with open(json_files[0], "r") as f:
        data = json.load(f)
        assert "buckets" in data
        assert data["universe_size"] == 5 # 6 stocks mocked, 1 illiquid removed by has_liquidity
        assert data["top_per_bucket"] == 2

        # Check Growth bucket
        assert "growth" in data["buckets"]
        assert len(data["buckets"]["growth"]) == 1 # Only one stock meets criteria
        assert data["buckets"]["growth"][0]["symbol"] == "GROWTH1.BK"
        assert data["buckets"]["growth"][0]["score"] == 45.0

        # Check Value bucket
        assert "value" in data["buckets"]
        assert len(data["buckets"]["value"]) == 1
        assert data["buckets"]["value"][0]["symbol"] == "VALUE1.BK"
        assert data["buckets"]["value"][0]["score"] == 28.8

        # Check Momentum bucket
        assert "momentum" in data["buckets"]
        assert len(data["buckets"]["momentum"]) == 1
        assert data["buckets"]["momentum"][0]["symbol"] == "MOMEN1.BK"
        assert data["buckets"]["momentum"][0]["score"] == 69.60

        # Check Mean Reversion bucket
        assert "mean_reversion" in data["buckets"]
        assert len(data["buckets"]["mean_reversion"]) == 1
        assert data["buckets"]["mean_reversion"][0]["symbol"] == "MR1.BK"
        assert data["buckets"]["mean_reversion"][0]["score"] == 31.25

        # Check illiquid stock is not in any bucket
        assert not any(s["symbol"] == "ILLIQ.BK" for bucket in data["buckets"].values() for s in bucket)
        # Check 'NONE1.BK' is not in any bucket
        assert not any(s["symbol"] == "NONE1.BK" for bucket in data["buckets"].values() for s in bucket)

    # Detailed content validation for Markdown
    with open(md_files[0], "r") as f:
        content = f.read()
        assert "Thai Watchlist Builder" in content
        assert "Universe: 5 SET stocks" in content # Illiquid stock is filtered out

        # Verify summary table
        assert "| GROWTH | 1 | 45.0 |" in content
        assert "| VALUE | 1 | 28.8 |" in content
        assert "| MOMENTUM | 1 | 69.6 |" in content
        assert "| MEAN-REVERSION | 1 | 31.2 |" in content # Rounded score

        # Verify stock presence in markdown sections
        assert "## GROWTH - Stage 2 Leaders" in content
        assert "GROWTH1.BK" in content

        assert "## VALUE - Cheap with Fundamentals" in content
        assert "VALUE1.BK" in content

        assert "## MOMENTUM - Hot Stocks" in content
        assert "MOMEN1.BK" in content

        assert "## MEAN-REVERSION - Oversold Bounces" in content
        assert "MR1.BK" in content

        # Ensure that stocks not fitting criteria or illiquid ones are not present
        assert "ILLIQ.BK" not in content
        assert "NONE1.BK" not in content
        assert "No candidates passed the filters." not in content # All buckets have candidates