"""Adversarial Test Suite for Hito 6 Phase 2: Retrieval Attacks.

Verifies the 12 adversarial retrieval attack cases against the differential oracle
and rigorously validates the invariant:
    RETRIEVED_EVIDENCE ⊆ AUTHORIZED_SCOPE (Bidirectionally enforced)

Rule: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Set, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.enums import SourceRole
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import DeterministicHashEmbedder
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore

ORACLE_PATH = REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json"


@pytest.fixture(scope="module")
def oracle_cases() -> Dict[str, Dict[str, Any]]:
    """Load pre-calculated oracle cases for Phase 2."""
    with open(ORACLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data["phase_2_retrieval_attacks"]["cases"]
    return {c["case_id"]: c for c in cases}


@pytest.fixture(scope="module")
def retrieval_env(tmp_path_factory: pytest.TempPathFactory) -> Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore]:
    """Provide an isolated, fully populated retrieval environment with boundary test chunks."""
    tmp_dir = tmp_path_factory.mktemp("p2_retrieval_env")
    db_path = tmp_dir / "knowledge_store.db"
    vec_path = tmp_dir / "vector_store.db"

    store = KnowledgeStore(db_path=db_path)
    store.initialize()

    sources_dir = REPO_ROOT / "data" / "benchmark" / "sources"
    ingest_benchmark_corpus(
        store=store,
        sources_dir=sources_dir,
        notebook_id="NB-CYBERSECURITY-V1",
    )

    # Refinement 1: Create isolated synthetic boundary chunks
    concurrency_chunks = store.chunks.list_by_document("so_concurrencia.pdf")
    max_idx = max((c.index for c in concurrency_chunks), default=0)

    concurrency_doc = store.documents.get("so_concurrencia.pdf")
    source_id = concurrency_doc.source_id if concurrency_doc else "src_so_concurrencia.pdf"

    chunk_p8 = Chunk(
        id="so_concurrencia.pdf:p08:c_boundary",
        source_id=source_id,
        document_id="so_concurrencia.pdf",
        page_start=8,
        page_end=8,
        index=max_idx + 1,
        content="Sección 2.3.8 Límite exacto de concurrencia en la página ocho: condiciones de carrera en el límite.",
        metadata={"page_number": 8, "synthetic": True, "purpose": "boundary_test"},
    )
    chunk_p9 = Chunk(
        id="so_concurrencia.pdf:p09:c_boundary",
        source_id=source_id,
        document_id="so_concurrencia.pdf",
        page_start=9,
        page_end=9,
        index=max_idx + 2,
        content="Sección 2.3.9 Contenido prohibido de concurrencia fuera de límite en página nueve: condiciones de carrera.",
        metadata={"page_number": 9, "synthetic": True, "purpose": "boundary_test"},
    )
    # Ensure the source for concurrency exists before creating synthetic boundary chunks
    if not store.sources.contains(source_id):
        manifest = SourceManifest(
            source_id=source_id,
            filename="so_concurrencia.pdf",
            sha256="0" * 64,
            byte_size=0,
            media_type="application/pdf",
        )
        source_obj = Source(
            source_id=source_id,
            title="Concurrencia",
            author="Cátedra de Sistemas",
            role=SourceRole.PRIMARY,
            priority=1,
            subject="Operating Systems",
        )
        record = SourceRecord(
            source_id=source_id,
            manifest=manifest,
            source=source_obj,
            metadata={},
        )
        store.sources.save(record)
    # Now create and save synthetic boundary chunks
    store.chunks.save_chunks([chunk_p8, chunk_p9])

    # Index into vector store
    embedder = DeterministicHashEmbedder(dimensions=128)
    vstore = SQLiteVectorStore(db_path=vec_path, read_only=False)
    records: List[VectorRecord] = []
    for doc in store.documents.list_all():
        for c in store.chunks.list_by_document(doc.id):
            vec = embedder.embed_passages([c.content])[0]
            records.append(
                VectorRecord(
                    chunk_id=c.id,
                    source_id=c.source_id,
                    notebook_id="NB-CYBERSECURITY-V1",
                    provider_id=embedder.provider_id,
                    model_id=embedder.model_id,
                    dimensions=embedder.dimensions,
                    vector=vec,
                )
            )
    vstore.save_records(records)

    lexical = LexicalRetriever(store)
    dense = DenseRetriever(store, vstore, embedder)
    hybrid = HybridRetriever(store, lexical, dense)
    service = RetrievalService(store, hybrid)

    registry = CurriculumRegistry(root_dir=REPO_ROOT / "data" / "curriculum")

    return service, registry, store


def assert_bidirectional_subset(
    candidates: List[ScoredCandidate],
    authorized_scopes: List[Dict[str, Any]],
) -> None:
    """Assert RETRIEVED_EVIDENCE ⊆ AUTHORIZED_SCOPE bidirectionally (Refinement 2)."""
    if not candidates:
        return

    authorized_docs: Set[str] = {s["document_id"] for s in authorized_scopes}

    # 1. Forward document check: all candidates belong to authorized documents
    assert all(c.document_id in authorized_docs for c in candidates), (
        f"Forward check failed: {[c.document_id for c in candidates]} not subset of {authorized_docs}"
    )

    # 2. Reverse document check: no candidate belongs to an unauthorized document
    assert not any(c.document_id not in authorized_docs for c in candidates), (
        f"Reverse check failed: found unauthorized documents in {[c.document_id for c in candidates]}"
    )

    # 3. Page range bidirectional check
    for c in candidates:
        cand_page = c.page_start or c.metadata.get("page_number")
        assert cand_page is not None, f"Chunk {c.chunk_id} missing page metadata"

        doc_scopes = [s for s in authorized_scopes if s["document_id"] == c.document_id]
        assert doc_scopes, f"No authorized scope found for candidate document {c.document_id}"

        # Must fall into at least one authorized range
        assert any(
            scope["page_start"] <= cand_page <= scope["page_end"] for scope in doc_scopes
        ), f"Candidate {c.chunk_id} on page {cand_page} is outside authorized ranges {[(s['page_start'], s['page_end']) for s in doc_scopes]}"


def test_p2_ret_01_authorized_sources_single_doc(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-01] Verify single-document node only returns chunks from authorized document."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-01"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert len(candidates) > 0
    assert_bidirectional_subset(candidates, case["authorized_scope"])
    assert all(c.document_id == "so_concurrencia.pdf" for c in candidates)


def test_p2_ret_02_authorized_sources_leakage_prevented(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-02] Adversarial query attempting to elicit pointers content while scoped to concurrency."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-02"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert candidates == []
    assert not any(c.document_id == "prog_punteros.pdf" for c in candidates)


def test_p2_ret_03_authorized_pages(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-03] Candidates retrieved are strictly within authorized pages [1, 10] of so_procesos.pdf."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-03"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert len(candidates) > 0
    assert_bidirectional_subset(candidates, case["authorized_scope"])
    for c in candidates:
        assert c.document_id == "so_procesos.pdf"
        assert 1 <= (c.page_start or 0) <= 10


def test_p2_ret_04_notebook_isolation(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-04] Query specifying foreign non-existent notebook yields zero candidates."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-04"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        notebook_id=case["input"]["notebook_id"],
        registry=registry,
        top_k=5,
    )

    assert candidates == []


def test_p2_ret_05_node_isolation(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-05] Cross-node leakage: concurrency query under SEC-01-C-PTR yields zero concurrency chunks."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-05"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert candidates == []
    assert not any(c.document_id == "so_concurrencia.pdf" for c in candidates)


def test_p2_ret_06_document_isolation_multi_doc(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-06] Multi-document node SEC-05-BIN-SEC legitimately retrieves from authorized documents."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-06"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert len(candidates) > 0
    assert_bidirectional_subset(candidates, case["authorized_scope"])
    allowed_docs = {"prog_archivos.pdf", "so_memoria.pdf"}
    assert all(c.document_id in allowed_docs for c in candidates)


def test_p2_ret_07_document_isolation_leakage(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-07] Multi-document node strictly forbids leakage from unauthorized document so_concurrencia.pdf."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-07"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert candidates == []
    assert not any(c.document_id == "so_concurrencia.pdf" for c in candidates)


def test_p2_ret_08_page_boundary_exact_limit(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-08] Boundary chunk at exact limit page_start=8 of [1, 8] is admitted."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-08"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert len(candidates) > 0
    assert_bidirectional_subset(candidates, case["authorized_scope"])
    assert any(c.page_start == 8 and c.document_id == "so_concurrencia.pdf" for c in candidates)


def test_p2_ret_09_page_boundary_outside_limit(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-09] Boundary chunk at page_start=9 strictly outside [1, 8] is filtered out."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-09"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert not any(c.page_start == 9 for c in candidates)
    assert candidates == []


def test_p2_ret_10_page_fidelity_metadata(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-10] All retrieved candidates carry valid, non-null, ordered page metadata matching store."""
    service, registry, store = retrieval_env
    case = oracle_cases["P2-RET-10"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert len(candidates) > 0
    for c in candidates:
        assert c.page_start is not None
        assert c.page_end is not None
        assert c.page_start <= c.page_end
        stored_chunk = store.chunks.get(c.chunk_id)
        assert stored_chunk.document_id == c.document_id
        assert stored_chunk.page_start == c.page_start


def test_p2_ret_11_unaligned_node_fail_closed(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-11] Querying unaligned node strictly yields fail-closed empty candidates."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-11"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert candidates == []


def test_p2_ret_12_relevance_gate_telemetry(
    retrieval_env: Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore],
    oracle_cases: Dict[str, Dict[str, Any]],
) -> None:
    """[P2-RET-12] Relevance gate logs pruned candidates into last_rejections with full audit schema."""
    service, registry, _ = retrieval_env
    case = oracle_cases["P2-RET-12"]

    candidates = service.retrieve_evidence(
        query=case["input"]["query"],
        node_id=case["input"]["node_id"],
        registry=registry,
        top_k=5,
    )

    assert candidates == []
    rejections = service.last_rejections
    assert len(rejections) > 0
    for r in rejections:
        assert "chunk_id" in r
        assert "document_id" in r
        assert r["reason"] == "LOW_DENSE_NO_LEXICAL"
        assert isinstance(r["dense_score"], float)
        assert r["threshold"] == 0.84
