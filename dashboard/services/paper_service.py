"""Application boundary for the existing paper-trade domain engine."""

from __future__ import annotations

from typing import Any

from paper_trade import (
    VALID_EMOTIONS,
    add_journal,
    check_discipline_warnings,
    close_position,
    compute_fingerprints,
    compute_stats,
    list_positions,
    open_position,
)
from update_marks import update_all


class PaperService:
    """Stable application-facing operations for simulated positions."""

    valid_emotions = VALID_EMOTIONS

    @staticmethod
    def open(**kwargs: Any) -> dict[str, Any]:
        return open_position(**kwargs)

    @staticmethod
    def close(**kwargs: Any) -> dict[str, Any]:
        return close_position(**kwargs)

    @staticmethod
    def list(status: str, market: str | None = None) -> list[dict[str, Any]]:
        return list_positions(status, market)

    @staticmethod
    def stats(market: str | None = None) -> dict[str, Any]:
        return compute_stats(market)

    @staticmethod
    def fingerprints(market: str | None = None) -> dict[str, Any]:
        return compute_fingerprints(market)

    @staticmethod
    def update_marks() -> list[dict[str, Any]]:
        return update_all()

    @staticmethod
    def journal(trade_id: int, text: str, emotion: str | None = None) -> dict[str, Any]:
        return add_journal(trade_id, text, emotion)

    @staticmethod
    def discipline_check() -> dict[str, Any]:
        return check_discipline_warnings()
