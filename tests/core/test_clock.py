from datetime import datetime, timezone

from trading_core.clock import ensure_utc, isoformat_seconds, parse_iso


def test_naive_datetime_is_normalized_as_utc() -> None:
    value = ensure_utc(datetime(2026, 8, 2, 12, 0, 0))
    assert value.tzinfo == timezone.utc
    assert value.hour == 12


def test_iso_round_trip_is_aware_and_second_precision() -> None:
    value = parse_iso(isoformat_seconds(datetime(2026, 8, 2, 12, 0, 0, 123456)))
    assert value == datetime(2026, 8, 2, 12, 0, 0, tzinfo=timezone.utc)
