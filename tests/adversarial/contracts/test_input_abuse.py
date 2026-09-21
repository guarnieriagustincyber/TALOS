"""Adversarial tests: Input abuse.

Attacks:
- Empty strings on required string fields (min_length=1).
- Extremely long strings and large structures.
- Nulls on non-nullable fields.
- Malformed text encoding / null bytes / control characters.
"""

import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    Notebook,
    Source,
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


@pytest.mark.parametrize(
    "model_cls,kwargs,field_name",
    [
        (Notebook, {"name": "Valid Name"}, "id"),
        (Notebook, {"id": "valid-id"}, "name"),
        (Source, {"title": "Valid Title"}, "source_id"),
        (Source, {"source_id": "valid-id"}, "title"),
        (Document, {"source_id": "src-1", "title": "T"}, "id"),
        (Document, {"id": "doc-1", "title": "T"}, "source_id"),
        (Document, {"id": "doc-1", "source_id": "src-1"}, "title"),
        (Chunk, {"document_id": "d-1", "source_id": "s-1", "content": "C"}, "id"),
        (Chunk, {"id": "c-1", "source_id": "s-1", "content": "C"}, "document_id"),
        (Chunk, {"id": "c-1", "document_id": "d-1", "content": "C"}, "source_id"),
        (Chunk, {"id": "c-1", "document_id": "d-1", "source_id": "s-1"}, "content"),
        (Evidence, {"claim": "Claim", "status": EvidenceStatus.SUPPORTED}, "id"),
        (Evidence, {"id": "ev-1", "status": EvidenceStatus.SUPPORTED}, "claim"),
        (StudentState, {}, "student_id"),
        (StudyPlan, {"module": "Mod", "objective": "Obj"}, "id"),
        (StudyPlan, {"id": "p-1", "objective": "Obj"}, "module"),
        (StudyPlan, {"id": "p-1", "module": "Mod"}, "objective"),
        (LLMRequest, {}, "request_id"),
        (LLMResponse, {"content": "text"}, "request_id"),
        (Event, {"event_type": "type"}, "event_id"),
        (Event, {"event_id": "e-1"}, "event_type"),
    ],
)
def test_rejects_empty_string_on_required_identifiers(model_cls, kwargs, field_name):
    """Empty string (min_length=1 violation) must be rejected on identifiers and titles."""
    test_args = {**kwargs, field_name: ""}
    with pytest.raises(ValidationError):
        model_cls(**test_args)


def test_null_byte_and_control_character_handling():
    """Contracts must accept or safely serialize strings with control characters without crashing."""
    control_str = "Title with null\x00byte and escape \x1b[31mred\x1b[0m and newline\n\r\t"
    source = Source(source_id="src-ctrl", title=control_str)
    assert source.title == control_str
    dumped = source.model_dump_json()
    reloaded = Source.model_validate_json(dumped)
    assert reloaded.title == control_str


def test_huge_token_count_handling():
    """Huge numbers within valid int range must be handled correctly."""
    chunk = Chunk(
        id="chunk-huge",
        document_id="doc-1",
        source_id="src-1",
        content="Some content",
        token_count=100_000_000,
    )
    assert chunk.token_count == 100_000_000
    assert Chunk.model_validate_json(chunk.model_dump_json()).token_count == 100_000_000
