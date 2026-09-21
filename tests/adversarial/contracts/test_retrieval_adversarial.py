"""Adversarial stress and abuse testing for retrieval contracts in S3.1."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)


def test_adversarial_query_payload_fuzzing():
    """Ensure raw code, regex symbols, SQL statements and emojis are accepted as valid queries."""
    fuzz_queries = [
        "C++",
        "*ptr = malloc(sizeof(int));",
        "O(log N) vs O(N^2)",
        "SELECT * FROM chunks WHERE 1=1;",
        "<script>alert('pwn')</script>",
        "🔥 Concurrencia y semáforos en Linux ⚡",
        "a" * 2000,
        "   leading and trailing spaces should be stripped   ",
    ]

    for q in fuzz_queries:
        req = RetrievalRequest(query=q, notebook_id="fadena-so")
        assert len(req.query) > 0
        assert req.query == q.strip()


def test_adversarial_candidate_unbounded_scores():
    """Verify that scores are not bounded to [0, 1] and accept negative floats and large BM25 values."""
    # Negative score (e.g. log likelihood or raw distance)
    c_neg = ScoredCandidate(
        chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb1",
        rank=1, score=-124.55, lexical_score=-124.55, content="text", retrieval_method="bm25",
    )
    assert c_neg.score == -124.55

    # Large score (e.g. high frequency match)
    c_large = ScoredCandidate(
        chunk_id="c2", document_id="d1", source_id="s1", notebook_id="nb1",
        rank=1, score=987654.321, content="text", retrieval_method="custom",
    )
    assert c_large.score == 987654.321


def test_adversarial_empty_retrieval_response():
    """Verify that a response with 0 candidates is valid and enforces invariants cleanly."""
    resp = RetrievalResponse(
        query="no_matching_term_xyz",
        notebook_id="fadena-so",
        strategy_used=RetrievalStrategy.LEXICAL,
        items=[],
        diagnostics=RetrievalDiagnostics(unique_candidates_count=0),
    )
    assert len(resp.items) == 0
    assert resp.diagnostics.unique_candidates_count == 0


def test_adversarial_contract_immutability_and_type_abuse():
    """Verify contracts protect against non-string and non-float corruption."""
    with pytest.raises(ValidationError):
        RetrievalRequest(query=12345, notebook_id="nb-1")  # type: ignore

    with pytest.raises(ValidationError):
        RetrievalRequest(query="valid", notebook_id=["not-a-string"])  # type: ignore

    with pytest.raises(ValidationError):
        ScoredCandidate(
            chunk_id="c1", document_id="d1", source_id="s1", notebook_id="nb1",
            rank="not-an-int", score=1.0, content="txt", retrieval_method="m",  # type: ignore
        )
