"""Adversarial Integration Tests for Epistemic Isolation and Curricular Gatekeeping (Hito 2).

INVARIANTS:
1. Hard Epistemic Boundary: If a student or agent requests knowledge while working on
   node N1, the retrieval subsystem MUST NOT return knowledge from node N2, even when
   content in N2 is semantically or lexically identical to the query.
2. Page-Fidelity Isolation: Document scopes define strictly allowed page boundaries.
   Chunks outside the authorized page ranges are filtered out a priori.
3. Fail-Closed Default: If an unmapped or invalid node_id is queried, retrieval
   MUST return an empty candidate list ([]) rather than falling back to unisolated corpus.
4. Deterministic Citations: ContextPacker formats candidates as:
   '[E#] (Fuente: document_id, pág. P) {content}'
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.context.packer import ContextPacker
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.retrieval.embedding import DeterministicHashEmbedder
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_store(tmp_path: Path) -> KnowledgeStore:
    """Fixture providing an authoritative KnowledgeStore ingested with real benchmark PDFs."""
    db_file = tmp_path / "test_epistemic.db"
    store = KnowledgeStore(db_path=db_file)
    store.initialize()
    sources_fixture = Path("data/fixtures/benchmark_sources")
    sources_dir = sources_fixture if sources_fixture.is_dir() else Path("data/benchmark/sources")
    ingest_benchmark_corpus(
        store=store,
        sources_dir=sources_dir,
        notebook_id="NB-CYBERSECURITY-V1",
    )
    return store


@pytest.fixture
def curriculum_registry() -> CurriculumRegistry:
    """Fixture providing CurriculumRegistry loaded with real cybersecurity curriculum."""
    return CurriculumRegistry()


@pytest.fixture
def retrieval_service(populated_store: KnowledgeStore, tmp_path: Path) -> RetrievalService:
    """Fixture providing RetrievalService backed by HybridRetriever with DeterministicHashEmbedder."""
    lexical = LexicalRetriever(populated_store)
    vector_store = SQLiteVectorStore(db_path=tmp_path / "test_vectors.db")

    embedder = DeterministicHashEmbedder(dimensions=128)

    # Index chunks in vector store
    chunks = (
        populated_store.chunks.list_by_document("so_concurrencia.pdf")
        + populated_store.chunks.list_by_document("prog_punteros.pdf")
        + populated_store.chunks.list_by_document("so_memoria.pdf")
    )

    records = []
    from study_engine.retrieval.vector_store import VectorRecord

    for chunk in chunks:
        vec = embedder.embed_passages([chunk.content])[0]
        records.append(
            VectorRecord(
                chunk_id=chunk.id,
                source_id=chunk.source_id,
                notebook_id="NB-CYBERSECURITY-V1",
                provider_id=embedder.provider_id,
                model_id=embedder.model_id,
                dimensions=embedder.dimensions,
                vector=vec,
            )
        )
    vector_store.save_records(records)

    dense = DenseRetriever(
        store=populated_store,
        vector_store=vector_store,
        embedding_provider=embedder,
    )
    hybrid = HybridRetriever(
        store=populated_store,
        lexical_retriever=lexical,
        dense_retriever=dense,
    )
    return RetrievalService(store=populated_store, retriever=hybrid)


def test_adversarial_cross_node_leakage_blocked(
    retrieval_service: RetrievalService,
    curriculum_registry: CurriculumRegistry,
) -> None:
    """Adversarial Test: Querying for Concurrency concepts while scoped to C Pointers node.

    - Query: 'condiciones de carrera procesos memoria compartida' (exists in so_concurrencia.pdf).
    - Scope: 'SEC-01-C-PTR' (ONLY allows prog_punteros.pdf, pages 1-15).
    - Expected Verdict: 0 candidates from so_concurrencia.pdf are admitted!
    """
    query = "condiciones de carrera procesos memoria compartida"

    # 1. Query scoped to SEC-01-C-PTR (Punteros)
    blocked_candidates = retrieval_service.retrieve_evidence(
        query=query,
        node_id="SEC-01-C-PTR",
        registry=curriculum_registry,
        top_k=5,
    )

    # Assert strict epistemic containment: zero chunks from so_concurrencia.pdf
    for cand in blocked_candidates:
        assert cand.document_id == "prog_punteros.pdf", (
            f"EPISTEMIC BREACH: Document '{cand.document_id}' was leaked under node 'SEC-01-C-PTR'!"
        )

    # 2. Query scoped to SEC-04-CONCURR (Concurrencia)
    authorized_candidates = retrieval_service.retrieve_evidence(
        query=query,
        node_id="SEC-04-CONCURR",
        registry=curriculum_registry,
        top_k=5,
    )

    # Assert that concurrency chunks ARE retrieved when authorized
    assert len(authorized_candidates) > 0
    assert all(c.document_id == "so_concurrencia.pdf" for c in authorized_candidates)
    assert any("condiciones de carrera" in c.content.lower() for c in authorized_candidates)


def test_unregistered_node_fails_closed(
    retrieval_service: RetrievalService,
    curriculum_registry: CurriculumRegistry,
) -> None:
    """Unregistered or hostile node_id strictly returns empty list (Fail-Closed)."""
    candidates = retrieval_service.retrieve_evidence(
        query="punteros memoria procesos",
        node_id="HOSTILE-UNREGISTERED-NODE-666",
        registry=curriculum_registry,
        top_k=10,
    )
    assert candidates == [], "Fail-closed invariant violated: unaligned node must yield []"


def test_page_fidelity_range_filtering(
    retrieval_service: RetrievalService,
    curriculum_registry: CurriculumRegistry,
) -> None:
    """Candidates are bounded by the exact page ranges in the alignment matrix."""
    # Node SEC-02-OS-PROC allows so_procesos.pdf pages 1-10
    candidates = retrieval_service.retrieve_evidence(
        query="procesos",
        node_id="SEC-02-OS-PROC",
        registry=curriculum_registry,
        top_k=5,
    )
    for cand in candidates:
        assert cand.document_id == "so_procesos.pdf"
        page = cand.page_start or cand.metadata.get("page_number")
        if page is not None:
            assert 1 <= page <= 10, f"Page {page} out of authorized range [1, 10]"


def test_context_packer_citations_format(
    retrieval_service: RetrievalService,
    curriculum_registry: CurriculumRegistry,
) -> None:
    """ContextPacker formats ScoredCandidates with citation tag [E#] and source metadata."""
    candidates = retrieval_service.retrieve_evidence(
        query="condiciones de carrera",
        node_id="SEC-04-CONCURR",
        registry=curriculum_registry,
        top_k=3,
    )
    assert len(candidates) > 0

    packer = ContextPacker()
    # Test single candidate citation format
    first_citation = packer.format_candidate(candidates[0], index=1)
    assert first_citation.startswith("[E1] (Fuente: so_concurrencia.pdf, pág.")
    assert candidates[0].content in first_citation

    # Test complete budgeted packing
    packed_context = packer.pack_candidates(candidates, max_characters=2000)
    assert "=== POLÍTICA EPISTÉMICA DE RESPUESTA" in packed_context
    assert "[E1]" in packed_context
    assert "(Fuente: so_concurrencia.pdf" in packed_context


def test_deterministic_hash_embedder_properties() -> None:
    """DeterministicHashEmbedder produces fixed 128-dimensional normalized vectors."""
    embedder = DeterministicHashEmbedder(dimensions=128)
    assert embedder.dimensions == 128
    assert embedder.is_test_mock is True

    q_vec = embedder.embed_query("prueba determinista")
    assert len(q_vec) == 128
    # L2-norm should be close to 1.0
    import math
    norm = math.sqrt(sum(x * x for x in q_vec))
    assert abs(norm - 1.0) < 1e-5

    # Determinism: same query yields identical vector
    q_vec2 = embedder.embed_query("prueba determinista")
    assert q_vec == q_vec2
