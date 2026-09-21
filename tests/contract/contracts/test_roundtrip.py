"""Contract tests for round-trip serialization and deserialization fidelity.

Validates that:
  Model -> model_dump() -> model_validate() -> Model (Identity/Equivalence)
  Model -> model_dump_json() -> model_validate_json() -> Model (Identity/Equivalence)
"""

import pytest

from study_engine.contracts import (
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
)
from .canonical_payloads import (
    CANONICAL_NOTEBOOK_MINIMAL,
    CANONICAL_NOTEBOOK_FULL,
    CANONICAL_SOURCE_MINIMAL,
    CANONICAL_SOURCE_FULL,
    CANONICAL_DOCUMENT_MINIMAL,
    CANONICAL_DOCUMENT_FULL,
    CANONICAL_CHUNK_MINIMAL,
    CANONICAL_CHUNK_FULL,
    CANONICAL_EVIDENCE_MINIMAL,
    CANONICAL_EVIDENCE_FULL,
    CANONICAL_STUDENT_STATE_MINIMAL,
    CANONICAL_STUDENT_STATE_FULL,
    CANONICAL_STUDY_PLAN_MINIMAL,
    CANONICAL_STUDY_PLAN_FULL,
    CANONICAL_LLM_REQUEST_MINIMAL,
    CANONICAL_LLM_REQUEST_FULL,
    CANONICAL_LLM_RESPONSE_MINIMAL,
    CANONICAL_LLM_RESPONSE_FULL,
    CANONICAL_EVENT_MINIMAL,
    CANONICAL_EVENT_FULL,
)

ALL_CANONICAL_CASES = [
    (Notebook, CANONICAL_NOTEBOOK_MINIMAL),
    (Notebook, CANONICAL_NOTEBOOK_FULL),
    (Source, CANONICAL_SOURCE_MINIMAL),
    (Source, CANONICAL_SOURCE_FULL),
    (Document, CANONICAL_DOCUMENT_MINIMAL),
    (Document, CANONICAL_DOCUMENT_FULL),
    (Chunk, CANONICAL_CHUNK_MINIMAL),
    (Chunk, CANONICAL_CHUNK_FULL),
    (Evidence, CANONICAL_EVIDENCE_MINIMAL),
    (Evidence, CANONICAL_EVIDENCE_FULL),
    (StudentState, CANONICAL_STUDENT_STATE_MINIMAL),
    (StudentState, CANONICAL_STUDENT_STATE_FULL),
    (StudyPlan, CANONICAL_STUDY_PLAN_MINIMAL),
    (StudyPlan, CANONICAL_STUDY_PLAN_FULL),
    (LLMRequest, CANONICAL_LLM_REQUEST_MINIMAL),
    (LLMRequest, CANONICAL_LLM_REQUEST_FULL),
    (LLMResponse, CANONICAL_LLM_RESPONSE_MINIMAL),
    (LLMResponse, CANONICAL_LLM_RESPONSE_FULL),
    (Event, CANONICAL_EVENT_MINIMAL),
    (Event, CANONICAL_EVENT_FULL),
]


@pytest.mark.parametrize("model_cls,payload", ALL_CANONICAL_CASES)
def test_dict_roundtrip_fidelity(model_cls, payload):
    """Model -> model_dump() -> model_validate() must produce an equivalent object."""
    original = model_cls.model_validate(payload)
    dumped = original.model_dump()
    reconstructed = model_cls.model_validate(dumped)

    assert reconstructed == original
    assert reconstructed.model_dump() == original.model_dump()


@pytest.mark.parametrize("model_cls,payload", ALL_CANONICAL_CASES)
def test_json_roundtrip_fidelity(model_cls, payload):
    """Model -> model_dump_json() -> model_validate_json() must produce an equivalent object."""
    original = model_cls.model_validate(payload)
    json_str = original.model_dump_json()
    reconstructed = model_cls.model_validate_json(json_str)

    assert reconstructed == original
    assert reconstructed.model_dump_json() == original.model_dump_json()
