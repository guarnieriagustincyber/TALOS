"""Unit tests for retrieval contracts in S3.1."""

from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)


def test_retrieval_strategy_enum_values():
    assert RetrievalStrategy.LEXICAL.value == "lexical"
    assert RetrievalStrategy.DENSE.value == "dense"
    assert RetrievalStrategy.HYBRID.value == "hybrid"
    # Ensure AUTO is strictly excluded from V1
    strategy_values = {s.value for s in RetrievalStrategy}
    assert "auto" not in strategy_values
    assert len(strategy_values) == 3


def test_retrieval_request_defaults_and_explicit():
    # Default strategy is LEXICAL, default top_k is 10
    req = RetrievalRequest(query="memoria virtual", notebook_id="fadena-so")
    assert req.query == "memoria virtual"
    assert req.notebook_id == "fadena-so"
    assert req.top_k == 10
    assert req.strategy == RetrievalStrategy.LEXICAL
    assert req.source_ids is None
    assert req.document_ids is None

    # Explicit customization
    req_custom = RetrievalRequest(
        query="árbol binario",
        notebook_id="fadena-prog",
        top_k=25,
        source_ids=["joyanes-prog"],
        document_ids=["joyanes-prog:cap05"],
        strategy=RetrievalStrategy.HYBRID,
    )
    assert req_custom.top_k == 25
    assert req_custom.strategy == RetrievalStrategy.HYBRID
    assert req_custom.source_ids == ["joyanes-prog"]
    assert req_custom.document_ids == ["joyanes-prog:cap05"]


def test_scored_candidate_instantiation_and_score_independence():
    candidate = ScoredCandidate(
        chunk_id="doc1:c0",
        document_id="doc1",
        source_id="src1",
        notebook_id="nb1",
        rank=1,
        score=14.5,  # Raw BM25 or RRF score, not bounded to [0, 1]
        content="Paginación y marcos de página",
        lexical_score=14.5,
        dense_score=0.88,
        retrieval_method="hybrid_rrf",
        page_start=120,
        page_end=121,
        pos_index=0,
        metadata={"chapter": 4},
    )
    assert candidate.rank == 1
    assert candidate.score == 14.5
    assert candidate.lexical_score == 14.5
    assert candidate.dense_score == 0.88
    assert candidate.metadata["chapter"] == 4


def test_retrieval_diagnostics():
    diag = RetrievalDiagnostics(
        lexical_candidates_count=45,
        dense_candidates_count=50,
        unique_candidates_count=62,
        latencies_ms={"lexical_ms": 1.2, "dense_ms": 3.4, "total_ms": 5.1},
    )
    assert diag.lexical_candidates_count == 45
    assert diag.dense_candidates_count == 50
    assert diag.unique_candidates_count == 62
    assert diag.latencies_ms["total_ms"] == 5.1


def test_retrieval_response_and_json_roundtrip():
    candidate1 = ScoredCandidate(
        chunk_id="c1",
        document_id="d1",
        source_id="s1",
        notebook_id="nb-so",
        rank=1,
        score=0.033,
        content="Texto uno",
        retrieval_method="lexical",
    )
    candidate2 = ScoredCandidate(
        chunk_id="c2",
        document_id="d1",
        source_id="s1",
        notebook_id="nb-so",
        rank=2,
        score=0.016,
        content="Texto dos",
        retrieval_method="lexical",
    )

    response = RetrievalResponse(
        query="procesos",
        notebook_id="nb-so",
        strategy_used=RetrievalStrategy.LEXICAL,
        items=[candidate1, candidate2],
        diagnostics=RetrievalDiagnostics(unique_candidates_count=2),
    )

    assert len(response.items) == 2
    assert response.items[0].rank == 1
    assert response.items[1].rank == 2

    # Roundtrip serialization test
    json_str = response.model_dump_json()
    reconstructed = RetrievalResponse.model_validate_json(json_str)
    assert reconstructed.query == response.query
    assert reconstructed.notebook_id == response.notebook_id
    assert len(reconstructed.items) == 2
    assert reconstructed.items[0].chunk_id == "c1"

def test_retrieval_request_explicit_none_filters():
    req = RetrievalRequest(query="test", notebook_id="nb", source_ids=None, document_ids=None)
    assert req.source_ids is None
    assert req.document_ids is None
