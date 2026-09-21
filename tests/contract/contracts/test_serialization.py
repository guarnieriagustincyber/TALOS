"""Contract tests for model serialization, deserialization, and JSON schema generation.

Ensures that all 10 models provide predictable, stable serialization interfaces
for downstream subsystems (S1 Ingestion, S2 Storage, S5 Context Packer, S6 LLM Gateway).
"""

import json
from datetime import datetime, timezone
import pytest

from study_engine.contracts import (
    Notebook,
    Source,
    SourceRole,
    Document,
    Chunk,
    Evidence,
    EvidenceStatus,
    StudentState,
    StudyPlan,
    LLMRequest,
    LLMResponse,
    Event,
)
from .canonical_payloads import (
    CANONICAL_NOTEBOOK_FULL,
    CANONICAL_SOURCE_FULL,
    CANONICAL_DOCUMENT_FULL,
    CANONICAL_CHUNK_FULL,
    CANONICAL_EVIDENCE_FULL,
    CANONICAL_STUDENT_STATE_FULL,
    CANONICAL_STUDY_PLAN_FULL,
    CANONICAL_LLM_REQUEST_FULL,
    CANONICAL_LLM_RESPONSE_FULL,
    CANONICAL_EVENT_FULL,
)

ALL_CONTRACT_CLASSES = [
    Notebook,
    Source,
    Document,
    Chunk,
    Evidence,
    StudentState,
    StudyPlan,
    LLMRequest,
    LLMResponse,
    Event,
]

FULL_INSTANCES = [
    Notebook.model_validate(CANONICAL_NOTEBOOK_FULL),
    Source.model_validate(CANONICAL_SOURCE_FULL),
    Document.model_validate(CANONICAL_DOCUMENT_FULL),
    Chunk.model_validate(CANONICAL_CHUNK_FULL),
    Evidence.model_validate(CANONICAL_EVIDENCE_FULL),
    StudentState.model_validate(CANONICAL_STUDENT_STATE_FULL),
    StudyPlan.model_validate(CANONICAL_STUDY_PLAN_FULL),
    LLMRequest.model_validate(CANONICAL_LLM_REQUEST_FULL),
    LLMResponse.model_validate(CANONICAL_LLM_RESPONSE_FULL),
    Event.model_validate(CANONICAL_EVENT_FULL),
]


@pytest.mark.parametrize("contract_cls", ALL_CONTRACT_CLASSES)
def test_contracts_json_schema_structure(contract_cls):
    """Verify that every domain model exports a valid, complete JSON Schema."""
    schema = contract_cls.model_json_schema()
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert "properties" in schema
    assert "title" in schema
    assert schema["title"] == contract_cls.__name__


@pytest.mark.parametrize("instance", FULL_INSTANCES)
def test_serialization_to_dict(instance):
    """Verify model_dump() produces a valid dictionary preserving all contract fields."""
    dumped = instance.model_dump()
    assert isinstance(dumped, dict)
    for field_name in type(instance).model_fields.keys():
        assert field_name in dumped


@pytest.mark.parametrize("instance", FULL_INSTANCES)
def test_serialization_to_json(instance):
    """Verify model_dump_json() produces standard, parseable JSON."""
    json_str = instance.model_dump_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    for field_name in type(instance).model_fields.keys():
        assert field_name in parsed


def test_enum_serialization_values():
    """Verify that Enums serialize to their raw string values, not repr or objects."""
    src = Source.model_validate(CANONICAL_SOURCE_FULL)
    dumped_dict = src.model_dump()
    assert dumped_dict["role"] == "PRIMARY"

    parsed_json = json.loads(src.model_dump_json())
    assert parsed_json["role"] == "PRIMARY"

    ev = Evidence.model_validate(CANONICAL_EVIDENCE_FULL)
    dumped_ev_dict = ev.model_dump()
    assert dumped_ev_dict["status"] == "SUPPORTED"

    parsed_ev_json = json.loads(ev.model_dump_json())
    assert parsed_ev_json["status"] == "SUPPORTED"


def test_datetime_serialization_iso_format():
    """Verify datetimes are serialized to standard ISO-8601 strings in JSON."""
    now = datetime(2026, 9, 1, 15, 30, 0, tzinfo=timezone.utc)
    evt = Event(event_id="evt-iso-test", event_type="telemetry", timestamp=now)

    json_data = json.loads(evt.model_dump_json())
    assert "2026-09-01T15:30:00" in json_data["timestamp"]

    reconstructed = Event.model_validate_json(evt.model_dump_json())
    assert reconstructed.timestamp == now
