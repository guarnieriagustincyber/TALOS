"""Tests for QueryRewriter canonical inflections and transformation pipeline (FASE A / BACKLOG-LEX-001).

Covers:
- C4: Initial correctness (pila -> pilas) and idempotence (rewrite(rewrite(q)) == rewrite(q)).
- C2: Transformation sequence: typos -> inflections -> colloquial.
- Word boundary preservation (e.g. compilador -> not compilasdor).
- Accents and diacritics handling.
- C5 / A1: Corpus data validation contract for every pair in _CANONICAL_INFLECTIONS.
- Exclusion of invalid/suspicious terms (heap, fork, lock, slot, arbol).
"""

from pathlib import Path
import sqlite3
import pytest

from study_engine.retrieval.query_rewriter import (
    QueryRewriter,
    _CANONICAL_INFLECTIONS,
    _TYPO_CORRECTIONS,
)
from study_engine.storage.knowledge_store import KnowledgeStore
from scripts.ingest_corpus import ingest_benchmark_corpus


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def rewriter():
    return QueryRewriter()


def test_initial_correctness_canonical_inflections(rewriter):
    """C4: Initial correctness of singular to plural canonical replacement."""
    assert rewriter.rewrite("pila") == "pilas"
    assert rewriter.rewrite("grafo") == "grafos"
    assert rewriter.rewrite("hilo") == "hilos"
    assert rewriter.rewrite("nodo") == "nodos"
    assert rewriter.rewrite("¿qué es una pila?") == "¿qué es una pilas?"
    assert rewriter.rewrite("manejo de hilos en c") == "manejo de hilos en c"


def test_idempotence_canonical_inflections(rewriter):
    """C4: Idempotence contract: rewrite(rewrite(q)) == rewrite(q)."""
    test_queries = [
        "pila",
        "pilas",
        "¿qué es una pila?",
        "el coso de sincronización de hilos",
        "punter a memori dinamica con pila",
        "recursividad en arbol y grafos",
        "interbloqueo cuando dos hilos se traban",
    ]
    for q in test_queries:
        first_pass = rewriter.rewrite(q)
        second_pass = rewriter.rewrite(first_pass)
        third_pass = rewriter.rewrite(second_pass)
        assert second_pass == first_pass, f"Failed idempotence on '{q}': '{first_pass}' != '{second_pass}'"
        assert third_pass == second_pass


def test_word_boundary_isolation(rewriter):
    """Verify word boundaries prevent substring corruption (e.g. compilador != compilasdor)."""
    assert rewriter.rewrite("compilador") == "compilador"
    assert rewriter.rewrite("autopiloto") == "autopiloto"
    assert rewriter.rewrite("nodoy") == "nodoy"
    assert rewriter.rewrite("hilorama") == "hilorama"
    assert rewriter.rewrite("epilogo") == "epilogo"
    assert rewriter.rewrite("fotografia") == "fotografia"


def test_transformation_sequence_order(rewriter):
    """C2: Strict transformation sequence: typos -> canonical inflections -> colloquial expansions."""
    # Query with typo 'punter' -> 'puntero', and inflection 'pila' -> 'pilas'
    q = "punter a una pila"
    res = rewriter.rewrite(q)
    assert "puntero" in res
    assert "punter" not in res.split()
    assert "pilas" in res
    assert "pila" not in res.split()

    # Query with typo + colloquial + inflection
    # 'semaforo' (typo) -> 'semáforo', 'hilo' -> 'hilos', 'el coso de sincronización' -> expands
    raw = "el coso de sincronización de un semaforo e hilo"
    out = rewriter.rewrite(raw)
    assert "semáforo" in out
    assert "hilos" in out
    assert "mecanismos de sincronización concurrente" in out

    # Check terms are only expanded once (no duplicate expansion)
    out2 = rewriter.rewrite(out)
    assert out2 == out


def test_excluded_terms_contract():
    """Verify terms where singular is canonical or english are excluded from _CANONICAL_INFLECTIONS (A1)."""
    excluded = ["heap", "fork", "lock", "slot", "pipe", "tabla", "clave", "arbol", "árbol", "tupla"]
    for term in excluded:
        assert term not in _CANONICAL_INFLECTIONS, f"Term '{term}' should not be in _CANONICAL_INFLECTIONS"


def test_canonical_inflections_corpus_validation(tmp_path):
    """A1 / C5: Data-validation contract against benchmark corpus.
    
    Every pair (sing, plur) in _CANONICAL_INFLECTIONS must satisfy:
    (a) hits(plural) > 0 in FTS
    (b) hits(singular) <= hits(plural) in FTS
    """
    db_path = tmp_path / "bench_val.db"
    store = KnowledgeStore(db_path=db_path)
    store.initialize()

    sources_fixture = REPO_ROOT / "data" / "fixtures" / "benchmark_sources"
    sources_dir = sources_fixture if sources_fixture.is_dir() else (REPO_ROOT / "data" / "benchmark" / "sources")
    assert sources_dir.is_dir(), f"Sources directory {sources_dir} not found"

    ingest_benchmark_corpus(
        store=store,
        sources_dir=sources_dir,
        notebook_id="NB-VAL-CORPUS",
    )

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    assert len(_CANONICAL_INFLECTIONS) > 0, "_CANONICAL_INFLECTIONS must not be empty"

    for sing, plur in _CANONICAL_INFLECTIONS.items():
        # (a) Check plural hits > 0
        try:
            cursor.execute("SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH ?", (plur,))
            hits_plur = cursor.fetchone()[0]
        except Exception as e:
            pytest.fail(f"FTS match failed for plural '{plur}': {e}")

        assert hits_plur > 0, (
            f"Corpus validation failed: plural form '{plur}' has 0 FTS hits in benchmark corpus"
        )

        # (b) Check singular hits <= plural hits
        try:
            cursor.execute("SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH ?", (sing,))
            hits_sing = cursor.fetchone()[0]
        except Exception as e:
            pytest.fail(f"FTS match failed for singular '{sing}': {e}")

        assert hits_sing <= hits_plur, (
            f"Corpus validation failed for '{sing}' -> '{plur}': "
            f"singular hits ({hits_sing}) > plural hits ({hits_plur})"
        )

    conn.close()


def test_coverage_guard_miss_telemetry_logging(caplog):
    """A5: Structured telemetry logging COVERAGE_GUARD_MISS for 4-5 char terms rejected or missing."""
    import logging
    from study_engine.contracts.catalog import SourceRecord
    from study_engine.contracts.chunk import Chunk
    from study_engine.contracts.document import Document
    from study_engine.contracts.ingestion import SourceManifest
    from study_engine.contracts.notebook import Notebook

    store = KnowledgeStore(":memory:")
    store.initialize()

    # Create notebook and document with only 'binario' (not 'árbol')
    manifest = SourceManifest(
        source_id="src-1",
        filename="src-1.pdf",
        byte_size=1024,
        sha256="a" * 64,
    )
    record = SourceRecord(source_id="src-1", manifest=manifest)
    doc = Document(
        id="doc-1",
        source_id="src-1",
        title="Doc 1",
        content="este es un archivo binario ejecutable compilado en c",
        page_count=1,
    )
    chunk = Chunk(
        id="chk-1",
        document_id="doc-1",
        source_id="src-1",
        content="este es un archivo binario ejecutable compilado en c",
        index=0,
    )
    nb = Notebook(id="NB-TELEMETRY", name="Telemetry Notebook")
    store.create_notebook(nb)
    store.store_ingestion_bundle(record, [doc], [chunk], notebook_id="NB-TELEMETRY")

    # Query with 4-5 char word with accent ('árbol') + 'binario'
    # 'binario' matches via disjunctive FTS, but coverage guard rejects because 'árbol' is missing
    with caplog.at_level(logging.WARNING):
        results = store.search(
            query="árbol binario",
            notebook_id="NB-TELEMETRY",
        )
        assert len(results) == 0

    # Verify structured log contains COVERAGE_GUARD_MISS
    log_records = [rec.message for rec in caplog.records if "COVERAGE_GUARD_MISS" in rec.message]
    assert len(log_records) > 0, "Expected COVERAGE_GUARD_MISS log record when query yields 0 admissions"
    assert any("term='árbol'" in msg for msg in log_records)


