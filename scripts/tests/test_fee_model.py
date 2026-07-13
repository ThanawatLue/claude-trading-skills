from __future__ import annotations

import pytest

from scripts.fee_model import effective_transaction_cost_bps, fee_model_from_config


def test_innovestx_fee_model_calculates_broker_fees_and_vat() -> None:
    model = fee_model_from_config(
        {
            "broker": "innovestx",
            "commission_pct": 0.15,
            "trading_fee_pct": 0.005,
            "clearing_fee_pct": 0.001,
            "vat_pct": 7,
            "slippage_bps": 0,
        }
    )

    assert model.broker_fee_bps == pytest.approx(16.692)
    assert model.breakdown(30_000)["broker_total"] == pytest.approx(50.076)


def test_effective_cost_includes_configured_slippage() -> None:
    model = fee_model_from_config({"slippage_bps": 5})

    assert effective_transaction_cost_bps({"slippage_bps": 5}) == pytest.approx(21.692)
    assert model.breakdown(6_000)["total"] == pytest.approx(13.0152)
