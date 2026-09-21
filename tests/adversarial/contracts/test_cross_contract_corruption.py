"""Adversarial tests: Cross-contract reference corruption.

Attacks:
- Empty strings in reference identifiers.
- None passed to non-nullable foreign reference fields.
- Non-string elements in reference collections (Notebook.sources, StudyPlan.sources).
- Dict/List structures passed into scalar reference fields.
"""

import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    Notebook,
    Document,
    Chunk,
    Evidence,
    StudyPlan,
    LLMResponse,
)


def test_rejects_empty_string_foreign_keys():
    """Document, Chunk, and Evidence must reject empty string references."""
    with pytest.raises(ValidationError):
        Document(id="d-1", source_id="", title="Title")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="", source_id="s-1", content="Text")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="d-1", source_id="", content="Text")


def test_rejects_none_on_required_foreign_keys():
    """Required foreign references must not accept None."""
    with pytest.raises(ValidationError):
        Document(id="d-1", source_id=None, title="Title")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id=None, source_id="s-1", content="Text")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="d-1", source_id=None, content="Text")


def test_rejects_invalid_elements_in_source_reference_lists():
    """Notebook.sources and StudyPlan.sources must reject non-string items."""
    with pytest.raises(ValidationError):
        Notebook(id="nb-1", name="N", sources=[123, 456])

    with pytest.raises(ValidationError):
        Notebook(id="nb-1", name="N", sources=[None])

    with pytest.raises(ValidationError):
        StudyPlan(id="p-1", module="M", objective="O", sources=[{"source": "src-1"}])


def test_rejects_structural_corruption_in_llm_request_id():
    """LLMResponse.request_id must be a valid non-empty string."""
    with pytest.raises(ValidationError):
        LLMResponse(request_id="", content="Response")

    with pytest.raises(ValidationError):
        LLMResponse(request_id=None, content="Response")

    with pytest.raises(ValidationError):
        LLMResponse(request_id={"id": 1}, content="Response")
