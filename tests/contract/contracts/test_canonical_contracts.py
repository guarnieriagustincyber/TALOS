"""Contract matrix tests for all 10 domain models.

Covers:
A. Valid construction (minimal and full canonical payloads)
B. Required fields validation
C. Optional fields and defaults preservation
D. Unknown root field rejection
E. Extensible metadata integrity
"""

import copy
import pytest
from pydantic import ValidationError

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

MODELS_AND_CANONICAL_PAYLOADS = [
    (Notebook, CANONICAL_NOTEBOOK_MINIMAL, CANONICAL_NOTEBOOK_FULL, ["id", "name"]),
    (Source, CANONICAL_SOURCE_MINIMAL, CANONICAL_SOURCE_FULL, ["source_id", "title"]),
    (Document, CANONICAL_DOCUMENT_MINIMAL, CANONICAL_DOCUMENT_FULL, ["id", "source_id", "title"]),
    (Chunk, CANONICAL_CHUNK_MINIMAL, CANONICAL_CHUNK_FULL, ["id", "document_id", "source_id", "content"]),
    (Evidence, CANONICAL_EVIDENCE_MINIMAL, CANONICAL_EVIDENCE_FULL, ["id", "claim", "status"]),
    (StudentState, CANONICAL_STUDENT_STATE_MINIMAL, CANONICAL_STUDENT_STATE_FULL, ["student_id"]),
    (StudyPlan, CANONICAL_STUDY_PLAN_MINIMAL, CANONICAL_STUDY_PLAN_FULL, ["id", "module", "objective"]),
    (LLMRequest, CANONICAL_LLM_REQUEST_MINIMAL, CANONICAL_LLM_REQUEST_FULL, ["request_id"]),
    (LLMResponse, CANONICAL_LLM_RESPONSE_MINIMAL, CANONICAL_LLM_RESPONSE_FULL, ["request_id", "content"]),
    (Event, CANONICAL_EVENT_MINIMAL, CANONICAL_EVENT_FULL, ["event_id", "event_type"]),
]


@pytest.mark.parametrize("model_cls,min_payload,full_payload,required_fields", MODELS_AND_CANONICAL_PAYLOADS)
def test_contract_canonical_construction(model_cls, min_payload, full_payload, required_fields):
    """Every model must construct cleanly from minimal and full canonical payloads."""
    instance_min = model_cls.model_validate(min_payload)
    assert isinstance(instance_min, model_cls)

    instance_full = model_cls.model_validate(full_payload)
    assert isinstance(instance_full, model_cls)


@pytest.mark.parametrize("model_cls,min_payload,full_payload,required_fields", MODELS_AND_CANONICAL_PAYLOADS)
def test_contract_required_fields_enforcement(model_cls, min_payload, full_payload, required_fields):
    """Removing any required field must raise a ValidationError."""
    for req_field in required_fields:
        corrupted = copy.deepcopy(min_payload)
        corrupted.pop(req_field, None)
        with pytest.raises(ValidationError):
            model_cls.model_validate(corrupted)


@pytest.mark.parametrize("model_cls,min_payload,full_payload,required_fields", MODELS_AND_CANONICAL_PAYLOADS)
def test_contract_rejects_unknown_root_fields(model_cls, min_payload, full_payload, required_fields):
    """All models must reject unknown top-level attributes (extra='forbid')."""
    injected = copy.deepcopy(full_payload)
    injected["unexpected_injected_root_field"] = "malicious_or_drifted_data"
    with pytest.raises(ValidationError) as exc_info:
        model_cls.model_validate(injected)
    assert "extra_forbidden" in str(exc_info.value)


@pytest.mark.parametrize("model_cls,min_payload,full_payload,required_fields", MODELS_AND_CANONICAL_PAYLOADS)
def test_contract_metadata_extensibility(model_cls, min_payload, full_payload, required_fields):
    """The declared metadata dictionary must accept arbitrary valid structured metadata without error."""
    custom_metadata = {
        "tag": "custom_tag",
        "nested": {"key": 42, "flags": [True, False]},
        "verified": True,
    }
    extended = copy.deepcopy(min_payload)
    extended["metadata"] = custom_metadata
    instance = model_cls.model_validate(extended)
    assert instance.metadata["tag"] == "custom_tag"
    assert instance.metadata["nested"]["key"] == 42
    assert instance.metadata["nested"]["flags"] == [True, False]


def test_notebook_contract_defaults():
    nb = Notebook.model_validate(CANONICAL_NOTEBOOK_MINIMAL)
    assert nb.sources == []
    assert nb.metadata == {}
    assert nb.description is None
    assert nb.subject is None


def test_source_contract_defaults():
    src = Source.model_validate(CANONICAL_SOURCE_MINIMAL)
    assert src.role == SourceRole.PRIMARY
    assert src.priority == 1
    assert src.language == "es"
    assert src.metadata == {}
    assert src.author is None


def test_document_contract_defaults():
    doc = Document.model_validate(CANONICAL_DOCUMENT_MINIMAL)
    assert doc.language == "es"
    assert doc.content is None
    assert doc.path is None
    assert doc.page_count is None
    assert doc.metadata == {}


def test_chunk_contract_defaults():
    chunk = Chunk.model_validate(CANONICAL_CHUNK_MINIMAL)
    assert chunk.index == 0
    assert chunk.page_start is None
    assert chunk.page_end is None
    assert chunk.token_count is None
    assert chunk.metadata == {}


def test_student_state_contract_defaults():
    state = StudentState.model_validate(CANONICAL_STUDENT_STATE_MINIMAL)
    assert state.status == "developing"
    assert state.understanding == {}
    assert state.strengths == []
    assert state.weaknesses == []
    assert state.recurring_errors == []
    assert state.metadata == {}


def test_study_plan_contract_defaults():
    plan = StudyPlan.model_validate(CANONICAL_STUDY_PLAN_MINIMAL)
    assert plan.depth == "standard"
    assert plan.prerequisites == []
    assert plan.concepts == []
    assert plan.sources == []
    assert plan.order == []
    assert plan.exercises == []
    assert plan.metadata == {}


def test_llm_request_contract_defaults():
    req = LLMRequest.model_validate(CANONICAL_LLM_REQUEST_MINIMAL)
    assert req.mode == "tutor"
    assert req.temperature == 0.7
    assert req.messages == []
    assert req.stop_sequences == []
    assert req.metadata == {}


def test_event_contract_defaults():
    evt = Event.model_validate(CANONICAL_EVENT_MINIMAL)
    assert evt.session_id is None
    assert evt.payload == {}
    assert evt.metadata == {}
    assert evt.timestamp is not None
