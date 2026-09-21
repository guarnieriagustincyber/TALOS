"""Contract tests for validation boundaries and invariants in S3.1."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)


def test_retrieval_request_rejects_blank_inputs():
    with pytest.raises(ValidationError):
        RetrievalRequest(query="   ", notebook_id="nb-1")

    with pytest.raises(ValidationError):
        RetrievalRequest(query="valid query", notebook_id="   ")

    with pytest.raises(ValidationError):
        RetrievalRequest(query="", notebook_id="nb-1")


def test_retrieval_request_rejects_out_of_bounds_top_k():
    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", top_k=0)

    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", top_k=-5)

    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", top_k=101)


def test_retrieval_request_rejects_invalid_strategy():
    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", strategy="auto")  # type: ignore

    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", strategy="unknown_strategy")  # type: ignore


def test_retrieval_request_rejects_blank_filter_items():
    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", source_ids=["valid-src", "  "])

    with pytest.raises(ValidationError):
        RetrievalRequest(query="test", notebook_id="nb-1", document_ids=[""])


def test_scored_candidate_rejects_invalid_rank_and_nan():
    with pytest.raises(ValidationError):
        ScoredCandidate(
            chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb1",
            rank=0, score=1.0, content="txt", retrieval_method="m",
        )

    with pytest.raises(ValidationError):
        ScoredCandidate(
            chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb1",
            rank=1, score=float("nan"), content="txt", retrieval_method="m",
        )

    with pytest.raises(ValidationError):
        ScoredCandidate(
            chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb1",
            rank=1, score=float("inf"), content="txt", retrieval_method="m",
        )


def test_retrieval_response_enforces_curricular_isolation_invariant():
    """Ensure RetrievalResponse rejects any candidate whose notebook_id differs from response.notebook_id."""
    valid_cand = ScoredCandidate(
        chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb-so",
        rank=1, score=1.0, content="txt", retrieval_method="m",
    )
    leaked_cand = ScoredCandidate(
        chunk_id="c2", document_id="d2", source_id="s2", notebook_id="nb-algebra",  # Contamination!
        rank=2, score=0.8, content="txt", retrieval_method="m",
    )

    with pytest.raises(ValidationError) as exc_info:
        RetrievalResponse(
            query="test",
            notebook_id="nb-so",
            strategy_used=RetrievalStrategy.LEXICAL,
            items=[valid_cand, leaked_cand],
        )

    assert "Curricular isolation violated" in str(exc_info.value)
    assert "nb-algebra" in str(exc_info.value)


def test_retrieval_response_enforces_rank_order_invariant():
    """Ensure candidate.rank strictly follows 1, 2, ..., N sequence matching its position."""
    c1 = ScoredCandidate(
        chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb-so",
        rank=1, score=1.0, content="txt", retrieval_method="m",
    )
    # Discontinuous rank
    c2 = ScoredCandidate(
        chunk_id="c2", document_id="d1", source_id="s1", notebook_id="nb-so",
        rank=5, score=0.8, content="txt", retrieval_method="m",
    )

    with pytest.raises(ValidationError) as exc_info:
        RetrievalResponse(
            query="test",
            notebook_id="nb-so",
            strategy_used=RetrievalStrategy.LEXICAL,
            items=[c1, c2],
        )

    assert "Ranking sequence invariant violated" in str(exc_info.value)
