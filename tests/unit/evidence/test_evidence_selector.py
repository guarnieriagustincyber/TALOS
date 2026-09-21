"""Unit tests for EvidenceSelector (V1.1 Fase B)."""

import pytest

from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.selector import EvidenceSelector


def make_candidate(
    chunk_id: str,
    source_id: str,
    score: float,
    content: str,
    rank: int = 1,
    notebook_id: str = "NB-TEST",
    trust_level: str = "canonical",
    sub_query_id: str = None,
) -> ScoredCandidate:
    meta = {"trust_level": trust_level}
    if sub_query_id:
        meta["sub_query_id"] = sub_query_id
    return ScoredCandidate(
        chunk_id=chunk_id,
        document_id=f"doc_{source_id}",
        source_id=source_id,
        notebook_id=notebook_id,
        rank=rank,
        score=score,
        content=content,
        retrieval_method="hybrid",
        metadata=meta,
    )


def test_evidence_selector_deduplication():
    selector = EvidenceSelector(max_total_chunks=5)
    c1 = make_candidate("c1", "src_a", 0.9, "TCP handshake explanation")
    # Exact duplicate chunk_id with lower score
    c1_dup = make_candidate("c1", "src_a", 0.7, "TCP handshake explanation")
    # Duplicate content with different chunk_id
    c2 = make_candidate("c2", "src_a", 0.85, "TCP handshake explanation")
    # Unique chunk
    c3 = make_candidate("c3", "src_b", 0.8, "Suricata rule inspection")

    selected = selector.select([c1, c1_dup, c2, c3])
    assert len(selected) == 2
    assert [c.chunk_id for c in selected] == ["c1", "c3"]
    assert selected[0].rank == 1
    assert selected[1].rank == 2


def test_evidence_selector_source_cap_diversity():
    selector = EvidenceSelector(max_total_chunks=4, max_chunks_per_source=2)
    # 5 candidates from src_a with very high scores
    c_a = [
        make_candidate(f"ca_{i}", "src_a", 0.95 - (i * 0.01), f"Content A {i}")
        for i in range(5)
    ]
    # 2 candidates from src_b with slightly lower scores
    c_b = [
        make_candidate(f"cb_{i}", "src_b", 0.80 - (i * 0.01), f"Content B {i}")
        for i in range(2)
    ]

    selected = selector.select(c_a + c_b)
    # Total selected must be 4
    assert len(selected) == 4
    # Max 2 from src_a, and 2 from src_b
    src_a_count = sum(1 for c in selected if c.source_id == "src_a")
    src_b_count = sum(1 for c in selected if c.source_id == "src_b")
    assert src_a_count == 2
    assert src_b_count == 2


def test_evidence_selector_soft_limit_fallback():
    # If only 1 source exists, it shouldn't starve the context
    selector = EvidenceSelector(max_total_chunks=4, max_chunks_per_source=2)
    c_a = [
        make_candidate(f"ca_{i}", "src_a", 0.90 - (i * 0.01), f"Unique Content A {i}")
        for i in range(5)
    ]
    selected = selector.select(c_a)
    assert len(selected) == 4
    for rank_idx, c in enumerate(selected, start=1):
        assert c.rank == rank_idx


def test_evidence_selector_inter_subquery_balancing():
    selector = EvidenceSelector(max_total_chunks=4, max_chunks_per_source=3)
    dict_candidates = {
        "sq_tcp": [
            make_candidate("c_tcp_1", "src_tcp", 0.99, "TCP 1"),
            make_candidate("c_tcp_2", "src_tcp", 0.98, "TCP 2"),
            make_candidate("c_tcp_3", "src_tcp", 0.97, "TCP 3"),
        ],
        "sq_suricata": [
            make_candidate("c_suri_1", "src_suri", 0.82, "Suricata 1"),
        ],
        "sq_flags": [
            make_candidate("c_flag_1", "src_tcp", 0.85, "Flags 1"),
        ]
    }

    selected = selector.select(dict_candidates)
    selected_subqueries = {c.metadata.get("sub_query_id") for c in selected}
    # All 3 subqueries must have representation
    assert "sq_tcp" in selected_subqueries
    assert "sq_suricata" in selected_subqueries
    assert "sq_flags" in selected_subqueries


def test_evidence_selector_trust_level_weighting():
    selector = EvidenceSelector(max_total_chunks=2, canonical_trust_bonus=0.2)
    c_unverified = make_candidate("c_unv", "src_a", 0.85, "Content unv", trust_level="unverified")
    c_canonical = make_candidate("c_can", "src_b", 0.80, "Content can", trust_level="canonical")

    # Canonical should leapfrog unverified due to trust weighting and bonus
    selected = selector.select([c_unverified, c_canonical])
    assert selected[0].chunk_id == "c_can"
