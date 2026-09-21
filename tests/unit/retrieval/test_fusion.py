"""Unit tests for FusionStrategy and ReciprocalRankFusion in S3.5."""

import pytest

from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.retrieval.fusion import (
    FusedCandidate,
    FusionStrategy,
    ReciprocalRankFusion,
)


def make_candidate(
    cid: str, rank: int, score: float, method: str
) -> ScoredCandidate:
    return ScoredCandidate(
        chunk_id=cid,
        document_id="doc-1",
        source_id="src-1",
        notebook_id="nb-1",
        rank=rank,
        score=score,
        content=f"Content for {cid}",
        retrieval_method=method,
    )


def test_fusion_strategy_protocol_compliance():
    rrf = ReciprocalRankFusion(k=60)
    assert isinstance(rrf, FusionStrategy)


def test_rrf_initialization_validation():
    with pytest.raises(ValueError) as exc1:
        ReciprocalRankFusion(k=0)
    assert "k must be > 0" in str(exc1.value)

    with pytest.raises(ValueError) as exc2:
        ReciprocalRankFusion(lexical_weight=-0.5)
    assert "Weights cannot be negative" in str(exc2.value)

    with pytest.raises(ValueError) as exc3:
        ReciprocalRankFusion(dense_weight=-0.1)
    assert "Weights cannot be negative" in str(exc3.value)

    with pytest.raises(ValueError) as exc4:
        ReciprocalRankFusion(lexical_weight=0.0, dense_weight=0.0)
    assert "At least one weight must be positive" in str(exc4.value)


def test_rrf_empty_candidate_lists():
    rrf = ReciprocalRankFusion(k=60)
    assert rrf.fuse([], [], top_k=5) == []
    assert rrf.fuse([], [], top_k=0) == []


def test_rrf_absent_candidates_no_penalty():
    """Verify that absent candidates have rank=None and receive no penalty."""
    rrf = ReciprocalRankFusion(k=60)

    lex_items = [
        make_candidate("c_lex_only", rank=1, score=10.0, method="lexical")
    ]
    dense_items = [
        make_candidate("c_dense_only", rank=1, score=0.9, method="dense")
    ]

    fused = rrf.fuse(lex_items, dense_items, top_k=5)
    assert len(fused) == 2

    # Both have rank 1 in their respective stream: score is 1 / (60 + 1)
    expected_score = 1.0 / 61.0
    by_id = {fc.chunk_id: fc for fc in fused}

    assert pytest.approx(by_id["c_lex_only"].score) == expected_score
    assert by_id["c_lex_only"].lexical_rank == 1
    assert by_id["c_lex_only"].dense_rank is None
    assert by_id["c_lex_only"].lexical_score == 10.0
    assert by_id["c_lex_only"].dense_score is None

    assert pytest.approx(by_id["c_dense_only"].score) == expected_score
    assert by_id["c_dense_only"].lexical_rank is None
    assert by_id["c_dense_only"].dense_rank == 1
    assert by_id["c_dense_only"].lexical_score is None
    assert by_id["c_dense_only"].dense_score == 0.9


def test_rrf_candidate_in_both_streams():
    """Verify additive fusion when candidate appears in both streams."""
    rrf = ReciprocalRankFusion(k=60)

    # c_both is rank 1 in lex, rank 2 in dense
    lex_items = [
        make_candidate("c_both", rank=1, score=15.0, method="lexical"),
        make_candidate("c_other", rank=2, score=12.0, method="lexical"),
    ]
    dense_items = [
        make_candidate("c_dense_top", rank=1, score=0.95, method="dense"),
        make_candidate("c_both", rank=2, score=0.88, method="dense"),
    ]

    fused = rrf.fuse(lex_items, dense_items, top_k=5)
    # c_both score: 1/(60+1) + 1/(60+2) = 1/61 + 1/62
    expected_c_both_score = (1.0 / 61.0) + (1.0 / 62.0)
    top1 = fused[0]

    assert top1.chunk_id == "c_both"
    assert pytest.approx(top1.score) == expected_c_both_score
    assert top1.lexical_rank == 1
    assert top1.dense_rank == 2
    assert top1.lexical_score == 15.0
    assert top1.dense_score == 0.88


def test_rrf_deterministic_tie_breaking():
    """Verify tie-breaking on identical RRF scores."""
    rrf = ReciprocalRankFusion(k=60)

    # c_lex and c_dense both have rank 1 in single stream -> score (1/61)
    # Primary: score DESC
    # Secondary: lexical_rank ASC (b_chunk has lex_rank=1, a_chunk None)
    lex_items = [
        make_candidate("b_chunk", rank=1, score=5.0, method="lexical")
    ]
    dense_items = [
        make_candidate("a_chunk", rank=1, score=0.9, method="dense")
    ]

    fused = rrf.fuse(lex_items, dense_items, top_k=2)
    assert fused[0].chunk_id == "b_chunk"  # Has lexical rank 1
    assert fused[1].chunk_id == "a_chunk"

    # Both have no lexical rank -> dense_rank ASC
    dense_only_1 = [
        make_candidate("chunk_z", rank=1, score=0.9, method="dense"),
        make_candidate("chunk_a", rank=2, score=0.8, method="dense"),
    ]
    fused_dense = rrf.fuse([], dense_only_1, top_k=2)
    assert fused_dense[0].chunk_id == "chunk_z"
    assert fused_dense[1].chunk_id == "chunk_a"

    # Pure tie on all ranks and score -> chunk_id lexicographical
    lex_tie = [
        make_candidate("chunk_b", rank=1, score=5.0, method="lexical"),
        make_candidate("chunk_a", rank=1, score=5.0, method="lexical"),
    ]
    fused_pure_tie = rrf.fuse(lex_tie, [], top_k=2)
    assert fused_pure_tie[0].chunk_id == "chunk_a"
    assert fused_pure_tie[1].chunk_id == "chunk_b"


def test_fused_candidate_validation():
    with pytest.raises(ValueError):
        FusedCandidate(
            chunk_id="c1",
            document_id="doc1",
            source_id="src1",
            notebook_id="nb1",
            score=float("nan"),
            content="content",
        )
