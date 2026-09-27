from unittest.mock import Mock

from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.retrieval.service import RetrievalService


def _candidate(
    chunk_id: str,
    *,
    lexical_score: float,
    dense_score: float,
    metadata: dict,
) -> ScoredCandidate:
    return ScoredCandidate(
        chunk_id=chunk_id,
        document_id="doc-1",
        source_id="src-1",
        notebook_id="nb-1",
        rank=1,
        score=dense_score,
        lexical_score=lexical_score,
        dense_score=dense_score,
        retrieval_method="hybrid",
        content=f"Content for {chunk_id}",
        metadata=metadata,
    )


def test_gate_actual_bypass_por_conjunto():
    """Un hit léxico en el lote actualmente admite también un candidato denso débil."""
    service = RetrievalService(
        store=Mock(),
        retriever=Mock(),
        dense_threshold=0.84,
    )
    lexical_candidate = _candidate(
        "lexical-hit",
        lexical_score=0.9,
        dense_score=0.3,
        metadata={"in_lexical": True},
    )
    weak_dense_candidate = _candidate(
        "weak-dense",
        lexical_score=0.0,
        dense_score=0.05,
        metadata={},
    )

    admitted = service._apply_relevance_gate(
        [lexical_candidate, weak_dense_candidate]
    )

    assert [candidate.chunk_id for candidate in admitted] == [
        "lexical-hit",
        "weak-dense",
    ]
