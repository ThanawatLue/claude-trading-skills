import pytest

from trading_core.contracts import SignalContract, TradePlanContract


def test_signal_contract_normalizes_market_and_symbol() -> None:
    signal = SignalContract(
        signal_id="sig_1",
        symbol=" aapl ",
        source="vcp-screener",
        signal_date="2026-08-02",
        market="us",
    )
    assert signal.symbol == "AAPL"
    assert signal.market == "US"
    assert signal.to_dict()["schema_version"] == "1"


def test_trade_plan_rejects_invalid_long_geometry() -> None:
    with pytest.raises(ValueError, match="stop < entry < target"):
        TradePlanContract("AAPL", "US", "long", 100, 110, 120, 100)


def test_trade_plan_accepts_short_geometry() -> None:
    plan = TradePlanContract("AAPL", "US", "short", 100, 110, 80, 100)
    assert plan.side == "short"
