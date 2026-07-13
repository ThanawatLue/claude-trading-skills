"""Transaction-cost models used by paper trading.

Rates are expressed as percentages unless explicitly named ``*_bps``.
The InnovestX model mirrors the published online cash-balance rates and
keeps estimated execution slippage separate from broker and market fees.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FeeModel:
    broker: str
    commission_pct: float
    trading_fee_pct: float
    clearing_fee_pct: float
    vat_pct: float
    slippage_bps: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "commission_pct",
            "trading_fee_pct",
            "clearing_fee_pct",
            "vat_pct",
            "slippage_bps",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")

    @property
    def broker_fee_bps(self) -> float:
        base_pct = self.commission_pct + self.trading_fee_pct + self.clearing_fee_pct
        return base_pct * (1 + self.vat_pct / 100) * 100

    @property
    def effective_bps(self) -> float:
        return self.broker_fee_bps + self.slippage_bps

    def breakdown(self, notional: float) -> dict[str, float | str]:
        if notional < 0:
            raise ValueError("notional must be >= 0")
        commission = notional * self.commission_pct / 100
        trading_fee = notional * self.trading_fee_pct / 100
        clearing_fee = notional * self.clearing_fee_pct / 100
        pre_vat = commission + trading_fee + clearing_fee
        vat = pre_vat * self.vat_pct / 100
        slippage = notional * self.slippage_bps / 10_000
        broker_total = pre_vat + vat
        return {
            "broker": self.broker,
            "notional": round(notional, 4),
            "commission": round(commission, 4),
            "trading_fee": round(trading_fee, 4),
            "clearing_fee": round(clearing_fee, 4),
            "vat": round(vat, 4),
            "broker_total": round(broker_total, 4),
            "slippage": round(slippage, 4),
            "total": round(broker_total + slippage, 4),
            "effective_bps": round(self.effective_bps, 4),
        }


def fee_model_from_config(config: dict[str, Any] | None) -> FeeModel:
    """Build a fee model from YAML values, defaulting to InnovestX."""
    values = config or {}
    return FeeModel(
        broker=str(values.get("broker", "innovestx")),
        commission_pct=float(values.get("commission_pct", 0.15)),
        trading_fee_pct=float(values.get("trading_fee_pct", 0.005)),
        clearing_fee_pct=float(values.get("clearing_fee_pct", 0.001)),
        vat_pct=float(values.get("vat_pct", 7.0)),
        slippage_bps=float(values.get("slippage_bps", 0.0)),
    )


def effective_transaction_cost_bps(config: dict[str, Any] | None) -> float:
    return fee_model_from_config(config).effective_bps
