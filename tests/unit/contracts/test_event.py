"""Unit tests for Event contract."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.event import Event


def test_event_valid_minimal():
    ev = Event(event_id="evt-001", event_type="session_start")
    assert ev.event_id == "evt-001"
    assert ev.event_type == "session_start"
    assert isinstance(ev.timestamp, datetime)
    assert ev.payload == {}
    assert ev.session_id is None


def test_event_valid_full():
    now = datetime.now(timezone.utc)
    ev = Event(
        event_id="evt-002",
        session_id="sess-abc-123",
        event_type="evaluation_completed",
        timestamp=now,
        payload={"topic": "Punteros", "score": 9.0, "duration_sec": 120},
        metadata={"client": "webui"},
    )
    assert ev.session_id == "sess-abc-123"
    assert ev.payload["score"] == 9.0
    assert ev.timestamp == now


def test_event_missing_required():
    with pytest.raises(ValidationError):
        Event(event_type="evaluation")

    with pytest.raises(ValidationError):
        Event(event_id="evt-1")
