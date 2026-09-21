"""Adversarial tests: Type confusion.

Attacks:
- Passing dict where list is expected.
- Passing list where dict is expected.
- Passing invalid element types inside typed collections.
- Passing non-dict objects inside list-of-dicts.
- Passing complex structures into scalar fields.
"""

import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    Notebook,
    Source,
    StudentState,
    StudyPlan,
    LLMRequest,
    LLMResponse,
    Event,
)


def test_rejects_dict_where_list_of_strings_expected():
    """Notebook.sources and StudyPlan.concepts must reject dicts."""
    with pytest.raises(ValidationError):
        Notebook(id="nb-1", name="Name", sources={"key": "val"})

    with pytest.raises(ValidationError):
        StudyPlan(id="p-1", module="M", objective="O", concepts={"key": "val"})


def test_rejects_list_where_dict_expected():
    """StudentState.understanding and Event.payload must reject lists."""
    with pytest.raises(ValidationError):
        StudentState(student_id="s-1", understanding=["not", "a", "dict"])

    with pytest.raises(ValidationError):
        Event(event_id="e-1", event_type="type", payload=["item1", "item2"])


def test_rejects_non_string_elements_in_string_lists():
    """StudyPlan.prerequisites and LLMRequest.stop_sequences must reject nested objects/dicts."""
    with pytest.raises(ValidationError):
        StudyPlan(id="p-1", module="M", objective="O", prerequisites=[{"nested": "dict"}])

    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", stop_sequences=[["nested", "list"]])


def test_rejects_malformed_messages_structure_in_llm_request():
    """LLMRequest.messages must be a list of dicts with string keys and values."""
    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", messages=["just a string"])

    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", messages=[12345])

    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", messages=[{"role": ["nested", "list"], "content": "hello"}])


def test_rejects_complex_structure_in_scalar_fields():
    """Scalar fields like source_id or title must reject nested dicts and lists."""
    with pytest.raises(ValidationError):
        Source(source_id={"injected": "id"}, title="Title")

    with pytest.raises(ValidationError):
        Source(source_id="src-1", title=["title", "in", "a", "list"])

    with pytest.raises(ValidationError):
        LLMResponse(request_id="req-1", content={"not": "a string"})
