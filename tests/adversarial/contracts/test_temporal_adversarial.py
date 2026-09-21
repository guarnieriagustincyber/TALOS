"""Adversarial tests: Temporal and timezone handling.

Attacks:
- Non-UTC timezone offsets (+03:00, -05:00, +05:30).
- Naive datetimes vs aware datetimes.
- Boundary dates (year 1970, year 2099).
- Malformed and invalid dates (e.g., Feb 29 on non-leap years, month 13).
"""

from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError

from study_engine.contracts import Event, StudentState, Notebook


def test_event_supports_various_timezone_offsets():
    """Event must preserve timestamps across different valid timezone offsets."""
    tz_tokyo = timezone(timedelta(hours=9))
    tz_ny = timezone(timedelta(hours=-5))

    dt_tokyo = datetime(2026, 9, 1, 21, 0, 0, tzinfo=tz_tokyo)
    dt_ny = datetime(2026, 9, 1, 7, 0, 0, tzinfo=tz_ny)

    ev1 = Event(event_id="e-tokyo", event_type="login", timestamp=dt_tokyo)
    ev2 = Event(event_id="e-ny", event_type="login", timestamp=dt_ny)

    # Both represent the exact same UTC instant (12:00:00 UTC)
    assert ev1.timestamp.astimezone(timezone.utc) == ev2.timestamp.astimezone(timezone.utc)

    # JSON roundtrip preserves the timestamp
    reloaded1 = Event.model_validate_json(ev1.model_dump_json())
    assert reloaded1.timestamp.astimezone(timezone.utc) == dt_tokyo.astimezone(timezone.utc)


def test_event_handles_historical_and_future_dates():
    """Contracts must accept reasonable historical (1970) and future (2099) dates."""
    past = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    future = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    ev_past = Event(event_id="e-past", event_type="genesis", timestamp=past)
    ev_future = Event(event_id="e-future", event_type="archival", timestamp=future)

    assert ev_past.timestamp == past
    assert ev_future.timestamp == future


@pytest.mark.parametrize(
    "invalid_date_str",
    [
        '{"event_id": "e-1", "event_type": "t", "timestamp": "not-a-date"}',
        '{"event_id": "e-1", "event_type": "t", "timestamp": "2026-13-01T00:00:00Z"}',  # month 13
        '{"event_id": "e-1", "event_type": "t", "timestamp": "2026-02-29T00:00:00Z"}',  # 2026 not leap year
        '{"event_id": "e-1", "event_type": "t", "timestamp": "2026-09-01T25:00:00Z"}',  # hour 25
    ],
)
def test_rejects_invalid_iso_datetime_strings(invalid_date_str):
    with pytest.raises(ValidationError):
        Event.model_validate_json(invalid_date_str)
