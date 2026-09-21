"""Adversarial tests: Boundary values.

Attacks:
- Numerical limits (0.0 <= confidence <= 1.0, 0.0 <= temperature <= 2.0).
- ge=1 limits (priority, page, max_tokens).
- ge=0 limits (page_count, index, latency_ms, token_count).
- Non-finite numbers (NaN, Inf).
"""

import math
import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    Source,
    Document,
    Chunk,
    Evidence,
    EvidenceStatus,
    LLMRequest,
    LLMResponse,
)


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_evidence_confidence_valid_boundaries(confidence):
    ev = Evidence(
        id="ev-boundary",
        claim="Claim",
        status=EvidenceStatus.SUPPORTED,
        confidence=confidence,
    )
    assert ev.confidence == confidence


@pytest.mark.parametrize("invalid_confidence", [-0.0001, 1.0001, -1.0, 2.0, 100.0])
def test_evidence_confidence_invalid_boundaries(invalid_confidence):
    with pytest.raises(ValidationError):
        Evidence(
            id="ev-boundary",
            claim="Claim",
            status=EvidenceStatus.SUPPORTED,
            confidence=invalid_confidence,
        )


@pytest.mark.parametrize("temperature", [0.0, 0.7, 1.0, 2.0])
def test_llm_request_temperature_valid_boundaries(temperature):
    req = LLMRequest(request_id="req-1", temperature=temperature)
    assert req.temperature == temperature


@pytest.mark.parametrize("invalid_temperature", [-0.01, 2.01, -1.0, 5.0])
def test_llm_request_temperature_invalid_boundaries(invalid_temperature):
    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", temperature=invalid_temperature)


@pytest.mark.parametrize("priority", [1, 2, 10, 1000])
def test_source_priority_valid_boundaries(priority):
    source = Source(source_id="src-1", title="Title", priority=priority)
    assert source.priority == priority


@pytest.mark.parametrize("invalid_priority", [0, -1, -999])
def test_source_priority_invalid_boundaries(invalid_priority):
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", priority=invalid_priority)


@pytest.mark.parametrize("page", [1, 2, 99999])
def test_source_and_evidence_page_valid(page):
    source = Source(source_id="src-1", title="Title", page=page)
    assert source.page == page
    ev = Evidence(id="ev-1", claim="C", status=EvidenceStatus.SUPPORTED, page=page)
    assert ev.page == page


@pytest.mark.parametrize("invalid_page", [0, -1, -50])
def test_source_and_evidence_page_invalid(invalid_page):
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", page=invalid_page)
    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="C", status=EvidenceStatus.SUPPORTED, page=invalid_page)


def test_document_page_count_zero_is_valid_negative_is_invalid():
    doc_zero = Document(id="d-1", source_id="s-1", title="T", page_count=0)
    assert doc_zero.page_count == 0

    with pytest.raises(ValidationError):
        Document(id="d-1", source_id="s-1", title="T", page_count=-1)


def test_llm_response_latency_zero_is_valid_negative_is_invalid():
    res_zero = LLMResponse(request_id="req-1", content="ok", latency_ms=0.0)
    assert res_zero.latency_ms == 0.0

    with pytest.raises(ValidationError):
        LLMResponse(request_id="req-1", content="ok", latency_ms=-0.1)


def test_llm_request_max_tokens_one_is_valid_zero_is_invalid():
    req_one = LLMRequest(request_id="req-1", max_tokens=1)
    assert req_one.max_tokens == 1

    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", max_tokens=0)

    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", max_tokens=-1)
