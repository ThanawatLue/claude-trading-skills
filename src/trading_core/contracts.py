"""Versioned domain contracts shared by skills and operational workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

SCHEMA_VERSION = "1"


def _market(value: str | None) -> str:
    result = (value or "US").strip().upper()
    if result not in {"US", "TH"}:
        raise ValueError(f"market must be US or TH, got {value!r}")
    return result


@dataclass(frozen=True)
class SignalContract:
    """Canonical representation of a signal entering the learning loop."""

    signal_id: str
    symbol: str
    source: str
    signal_date: str
    market: str = "US"
    direction: str = "LONG"
    score: float | None = None
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.signal_id.strip():
            raise ValueError("signal_id must not be empty")
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        date.fromisoformat(self.signal_date[:10])
        object.__setattr__(self, "market", _market(self.market))
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "direction", self.direction.strip().upper())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradePlanContract:
    """Validated entry/stop/target plan used by paper execution."""

    symbol: str
    market: str
    side: str
    entry: float
    stop: float
    target: float
    shares: int
    source: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        market = _market(self.market)
        side = self.side.strip().lower()
        if side not in {"long", "short"}:
            raise ValueError("side must be long or short")
        if self.shares <= 0:
            raise ValueError("shares must be > 0")
        if min(self.entry, self.stop, self.target) <= 0:
            raise ValueError("entry, stop, and target must be > 0")
        if side == "long" and not self.stop < self.entry < self.target:
            raise ValueError("long plan requires stop < entry < target")
        if side == "short" and not self.target < self.entry < self.stop:
            raise ValueError("short plan requires target < entry < stop")
        object.__setattr__(self, "market", market)
        object.__setattr__(self, "side", side)
        object.__setattr__(self, "symbol", self.symbol.strip().upper())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunMetadata:
    """Operational provenance attached to pipeline and report outputs."""

    run_id: str
    market: str
    started_at: str
    execution_mode: str = "dry_run"
    config_hash: str | None = None
    code_commit: str | None = None
    data_freshness: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "market", _market(self.market))
        if self.execution_mode not in {"dry_run", "paper", "live"}:
            raise ValueError("execution_mode must be dry_run, paper, or live")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
