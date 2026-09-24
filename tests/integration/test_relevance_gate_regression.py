"""Regression test suite for Hybrid Relevance Gate (Hito 6 Paso 2).

Verifies that the relevance gate in RetrievalService:
1. Loads threshold θ = 0.84 from data/config/retrieval_config.json.
2. Strictly blocks 100% of out-of-domain queries (0 candidates, reason LOW_DENSE_NO_LEXICAL).
3. Correctly admits legitimate in-corpus queries (≥ 1 candidate).
4. Preserves Golden Path E2E execution with 0 mismatches.
5. Preserves Epistemic Isolation across curricular nodes.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.calibrate_relevance_threshold import (
    LEGITIMATE_QUERIES,
    OUT_OF_DOMAIN_QUERIES,
)
from scripts.experiments.run_golden_path_e2e import run_golden_path_e2e
from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.contracts.retrieval import RetrievalRequest, ScoredCandidate
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import (
    DeterministicHashEmbedder,
    LocalONNXEmbeddingProvider,
)
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService, load_retrieval_config
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture(scope="module")
def benchmark_env(tmp_path_factory: pytest.TempPathFactory) -> Dict[str, Any]:
    """Initialize shared benchmark environment with ingested corpus and ONNX embeddings."""
    tmp_dir = tmp_path_factory.mktemp("relevance_gate_bench")
    db_path = tmp_dir / "benchmark_kstore.db"
    vec_path = tmp_dir / "benchmark_vstore.db"

    store = KnowledgeStore(db_path=db_path)
    store.initialize()
    sources_fixture = REPO_ROOT / "data" / "fixtures" / "benchmark_sources"
    sources_dir = sources_fixture if sources_fixture.is_dir() else (REPO_ROOT / "data" / "benchmark" / "sources")
    ingest_benchmark_corpus(
        store=store,
        sources_dir=sources_dir,
        notebook_id="NB-CYBERSECURITY-V1",
    )

    provider = LocalONNXEmbeddingProvider()
    vstore = SQLiteVectorStore(db_path=vec_path)
    all_chunks = []
    for doc in store.list_documents():
        all_chunks.extend(store.list_chunks_by_document(doc.id))

    records: List[VectorRecord] = []
    for i in range(0, len(all_chunks), 32):
        batch = all_chunks[i : i + 32]
        texts = [c.content for c in batch]
        vectors = provider.embed_passages(texts)
        for c, vec in zip(batch, vectors):
            records.append(
                VectorRecord(
                    chunk_id=c.id,
                    source_id=c.source_id,
                    notebook_id="NB-CYBERSECURITY-V1",
                    provider_id=provider.provider_id,
                    model_id=provider.model_id,
                    dimensions=provider.dimensions,
                    vector=vec,
                )
            )
    vstore.save_records(records)

    dense = DenseRetriever(store, vstore, provider)
    lexical = LexicalRetriever(store)
    hybrid = HybridRetriever(store, lexical, dense)
    retrieval_service = RetrievalService(store, hybrid)
    registry = CurriculumRegistry(root_dir=REPO_ROOT / "data" / "curriculum")

    return {
        "store": store,
        "vstore": vstore,
        "retrieval_service": retrieval_service,
        "registry": registry,
    }


def test_relevance_gate_configuration_loaded() -> None:
    """Relevance gate correctly loads external configuration."""
    config = load_retrieval_config()
    assert "relevance_gate" in config
    assert config["relevance_gate"]["dense_threshold_no_lexical"] == 0.84
    assert config["relevance_gate"]["calibration_model"] == "Qwen/Qwen3-Embedding-8B"

    service = RetrievalService(store=KnowledgeStore(":memory:"))
    assert service.dense_threshold == 0.84
    assert service.last_rejections == []


def test_relevance_gate_blocks_all_12_ood_queries(benchmark_env: Dict[str, Any]) -> None:
    """Relevance gate strictly blocks 100% of out-of-domain queries."""
    ret_service: RetrievalService = benchmark_env["retrieval_service"]
    registry: CurriculumRegistry = benchmark_env["registry"]

    blocked_count = 0
    for node_id, query, note in OUT_OF_DOMAIN_QUERIES:
        candidates = ret_service.retrieve_evidence(
            query=query,
            node_id=node_id,
            registry=registry,
            top_k=5,
        )
        assert len(candidates) == 0, (
            f"OOD query was not blocked by relevance gate: [{node_id}] '{query}' "
            f"returned {len(candidates)} candidates."
        )
        blocked_count += 1
        assert len(ret_service.last_rejections) > 0
        assert all(
            r["reason"] == "LOW_DENSE_NO_LEXICAL"
            for r in ret_service.last_rejections
        )

    assert blocked_count == len(OUT_OF_DOMAIN_QUERIES) == 12


def test_relevance_gate_admits_in_corpus_legitimate_queries(
    benchmark_env: Dict[str, Any],
) -> None:
    """Legitimate queries whose topics exist in benchmark PDFs return ≥ 1 candidates."""
    ret_service: RetrievalService = benchmark_env["retrieval_service"]
    registry: CurriculumRegistry = benchmark_env["registry"]

    # Queries whose keywords and concepts are physically present in data/benchmark/sources
    in_corpus_legit_queries = [
        ("SEC-04-CONCURR", "¿Qué es una condición de carrera?"),
        ("SEC-04-CONCURR", "condiciones de carrera"),
        ("SEC-04-CONCURR", "comunicación entre procesos y concurrencia"),
        ("SEC-01-C-PTR", "¿Qué es un puntero en C?"),
        ("SEC-01-C-PTR", "punteros y direcciones de memoria en C"),
        ("SEC-03-MEM-MGMT", "gestión de memoria dinámica heap y stack"),
        ("SEC-02-OS-PROC", "¿Qué es un proceso en sistemas operativos?"),
        ("SEC-02-OS-PROC", "estados de un proceso y PCB"),
    ]

    for node_id, query in in_corpus_legit_queries:
        candidates = ret_service.retrieve_evidence(
            query=query,
            node_id=node_id,
            registry=registry,
            top_k=5,
        )
        assert len(candidates) >= 1, (
            f"Legitimate in-corpus query was falsely rejected: [{node_id}] '{query}'"
        )
        assert all(isinstance(c, ScoredCandidate) for c in candidates)


def test_relevance_gate_behavior_on_out_of_corpus_syllabus_queries(
    benchmark_env: Dict[str, Any],
) -> None:
    """Queries for concepts not in 8 benchmark PDFs (e.g. mutex, deadlock) fail closed.

    This test verifies that the system does NOT hallucinate or return unrelated
    chunks (e.g. printer spoolers) when asked about concepts absent from the ingested PDFs.
    """
    ret_service: RetrievalService = benchmark_env["retrieval_service"]
    registry: CurriculumRegistry = benchmark_env["registry"]

    out_of_corpus_queries = [
        ("SEC-04-CONCURR", "¿Cómo funcionan los mutexes?"),
        ("SEC-04-CONCURR", "¿Qué es un deadlock?"),
        ("SEC-04-CONCURR", "sección crítica y exclusión mutua"),
        ("SEC-01-C-PTR", "¿Cómo se declara int *p?"),
        ("SEC-03-MEM-MGMT", "¿Qué es malloc?"),
        ("SEC-03-MEM-MGMT", "¿Cómo funciona el stack?"),
    ]

    for node_id, query in out_of_corpus_queries:
        candidates = ret_service.retrieve_evidence(
            query=query,
            node_id=node_id,
            registry=registry,
            top_k=5,
        )
        # Absence of evidence must fail closed (0 candidates) rather than return unrelated noise
        assert len(candidates) == 0, (
            f"Expected fail-closed 0 candidates for out-of-corpus query '{query}', got {len(candidates)}"
        )


def test_golden_path_e2e_regression_passes() -> None:
    """Golden Path E2E campaign runs with 0 mismatches with relevance gate active."""
    res = run_golden_path_e2e()
    comparison = res["oracle_comparison"]
    assert comparison["status"] == "PASS"
    assert comparison["mismatch_count"] == 0
    assert comparison["mismatches"] == []
    assert res["phases"]["phase_1_conceptual"]["session_status"] == "APPROVED"
    assert res["phases"]["phase_1_conceptual"]["candidate_count"] == 5


def test_epistemic_isolation_maintained_with_gate(benchmark_env: Dict[str, Any]) -> None:
    """Curricular cross-node epistemic containment is preserved with relevance gate."""
    ret_service: RetrievalService = benchmark_env["retrieval_service"]
    registry: CurriculumRegistry = benchmark_env["registry"]

    query = "condiciones de carrera procesos memoria compartida"

    # Scoped to SEC-01-C-PTR (Punteros) -> must NOT leak so_concurrencia.pdf
    cands_punteros = ret_service.retrieve_evidence(
        query=query,
        node_id="SEC-01-C-PTR",
        registry=registry,
        top_k=5,
    )
    for c in cands_punteros:
        assert c.document_id == "prog_punteros.pdf"

    # Scoped to SEC-04-CONCURR -> admits so_concurrencia.pdf
    cands_concurr = ret_service.retrieve_evidence(
        query=query,
        node_id="SEC-04-CONCURR",
        registry=registry,
        top_k=5,
    )
    assert len(cands_concurr) > 0
    assert all(c.document_id == "so_concurrencia.pdf" for c in cands_concurr)


def test_relevance_gate_recall_four_char_term_with_plural_inflection(
    benchmark_env: Dict[str, Any],
) -> None:
    """Recall test for 4-character terms with plural/inflectional variants (Punch-list Ítem 3).

    1. Term with both singular (4 chars) and plural (5 chars) in corpus: 'hilo' / 'hilos'
       on SEC-04-CONCURR admits >= 1 candidates in both forms.
    2. Term where corpus contains only plural: 'pilas' (5 chars) in prog_lineales.pdf
       admits >= 1 candidate on notebook NB-CYBERSECURITY-V1.
    3. Boundary finding: 'pila' (4 chars) yields 0 candidates when the corpus
       only contains 'pilas' because Commit 6 restricts prefix wildcards to terms of len >= 5
       to prevent noisy matches (e.g. 'int *p'). Per specification, this threshold is NOT lowered.
    """
    ret_service: RetrievalService = benchmark_env["retrieval_service"]
    registry: CurriculumRegistry = benchmark_env["registry"]

    # 1. 'hilo' / 'hilos' on SEC-04-CONCURR (so_concurrencia.pdf has both)
    cands_hilos = ret_service.retrieve_evidence(
        query="hilos",
        node_id="SEC-04-CONCURR",
        registry=registry,
        top_k=5,
    )
    assert len(cands_hilos) >= 1, "Plural 'hilos' must admit >= 1 candidate"
    assert any(c.document_id == "so_concurrencia.pdf" for c in cands_hilos)

    cands_hilo = ret_service.retrieve_evidence(
        query="hilo",
        node_id="SEC-04-CONCURR",
        registry=registry,
        top_k=5,
    )
    assert len(cands_hilo) >= 1, "Singular 'hilo' (4 chars) must admit >= 1 candidate"
    assert any(c.document_id == "so_concurrencia.pdf" for c in cands_hilo)

    # 2. 'pilas' on NB-CYBERSECURITY-V1 (where prog_lineales.pdf is ingested)
    cands_pilas = ret_service.retrieve_evidence(
        query="pilas",
        notebook_id="NB-CYBERSECURITY-V1",
        top_k=5,
    )
    assert len(cands_pilas) >= 1, "Plural 'pilas' must admit >= 1 candidate in prog_lineales.pdf"
    assert any(c.document_id == "prog_lineales.pdf" for c in cands_pilas)

    # 3. BACKLOG-LEX-001: 'pila' (4 chars) now canonicalizes to 'pilas' via QueryRewriter,
    # resolving the prefix wildcard constraint without lowering the len >= 5 threshold.
    cands_pila = ret_service.retrieve_evidence(
        query="pila",
        notebook_id="NB-CYBERSECURITY-V1",
        top_k=5,
    )
    assert len(cands_pila) >= 1, (
        "Singular 'pila' must admit >= 1 candidate in prog_lineales.pdf via canonical inflection"
    )
    assert any(c.document_id == "prog_lineales.pdf" for c in cands_pila)

    # 4. Student question with singular 'pila'
    cands_pregunta_pila = ret_service.retrieve_evidence(
        query="¿qué es una pila?",
        notebook_id="NB-CYBERSECURITY-V1",
        top_k=5,
    )
    assert len(cands_pregunta_pila) >= 1, (
        "Conversational query '¿qué es una pila?' must admit >= 1 candidate in prog_lineales.pdf"
    )
    assert any(c.document_id == "prog_lineales.pdf" for c in cands_pregunta_pila)


