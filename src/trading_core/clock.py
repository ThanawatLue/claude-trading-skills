"""UTC-first time helpers used by jobs, ledgers, and paper trading."""

from __future__ import annotations

from datetime import datetime, timezone

UTC = timezone.utc


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC.

    Naive values are treated as UTC for backward compatibility with the old
    local SQLite records. New callers should always provide aware values.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def isoformat_seconds(value: datetime | None = None) -> str:
    """Serialize a timestamp consistently for SQLite and JSON contracts."""

    return ensure_utc(value or utc_now()).isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime:
    """Parse an ISO timestamp and return an aware UTC datetime."""

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return ensure_utc(datetime.fromisoformat(text))
