"""Unit and integration tests for ContentRegistryRepository and Backfill (Slice 6.0.5).

Asserts:
1. Cache invalidation: save() of item with solution_chunk_ids immediately updates get_solution_chunk_ids() in the same process (Punto 3).
2. Universal accessor filtering: get_statement_chunks() never returns solution chunks (Punto 2).
3. Backfill idempotence: multiple runs produce identical items with 0 duplicate PK violations.
"""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.source import Source, SourceRole
from study_engine.storage.content_parser import backfill_content_registry, parse_content_items
from study_engine.storage.content_registry import ContentRegistryRepository
from study_engine.storage.knowledge_store import KnowledgeStore


def test_cache_invalidation_immediate_in_same_process() -> None:
    """Invariant Punto 3: save() of an item with solution_chunk_ids invalidates cache immediately."""
    store = KnowledgeStore(":memory:")
    store.initialize()
    repo = store.content_registry

    # Initially cache is empty
    assert repo.get_solution_chunk_ids() == set()

    # Save dummy source to satisfy foreign key constraint
    src_rec = SourceRecord(
        source_id="src-guia-1",
        manifest=SourceManifest(source_id="src-guia-1", filename="guia1.pdf", byte_size=10, sha256="1" * 64),
        source=Source(source_id="src-guia-1", title="Guia 1", author="UTN", role=SourceRole.PRIMARY),
    )
    store.sources.save(src_rec)

    # Save exercise with 1 statement chunk and 1 solution chunk
    item1 = ContentItem(
        content_id="guia_1:ej_1",
        source_id="src-guia-1",
        unit_type=UnitType.EXERCISE,
        statement_text="Calcular el factorial de N.",
        chunk_ids=["chk-stmt-1"],
        solution_chunk_ids=["chk-sol-1"],
        status=ContentStatus.OK,
    )
    repo.save(item1)

    # In same process without restart, cache reflects new solution chunk
    sol_ids = repo.get_solution_chunk_ids()
    assert "chk-sol-1" in sol_ids
    assert "chk-stmt-1" not in sol_ids

    # Save a second item with an additional solution chunk
    item2 = ContentItem(
        content_id="guia_1:ej_2",
        source_id="src-guia-1",
        unit_type=UnitType.EXERCISE,
        statement_text="Invertir una cadena.",
        chunk_ids=["chk-stmt-2"],
        solution_chunk_ids=["chk-sol-2"],
        status=ContentStatus.OK,
    )
    repo.save(item2)

    # Immediately reflects both in the same process
    assert repo.get_solution_chunk_ids() == {"chk-sol-1", "chk-sol-2"}


def test_repository_accessor_filters_solution_chunks() -> None:
    """Invariant Punto 2: get_statement_chunks() applies filter_presentation internally."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    # Create dummy source, doc, and chunks
    src_rec = SourceRecord(
        source_id="src-test",
        manifest=SourceManifest(source_id="src-test", filename="test.pdf", byte_size=10, sha256="a" * 64),
        source=Source(source_id="src-test", title="Test Guide", author="UTN", role=SourceRole.PRIMARY),
    )
    doc = Document(id="doc-1", source_id="src-test", title="Guia 1")
    stmt_chunk = Chunk(
        id="chk-stmt-10",
        document_id="doc-1",
        source_id="src-test",
        content="Ejercicio 10: Escribir algoritmo de ordenamiento.",
        page_start=5,
        token_count=10,
        index=0,
    )
    sol_chunk = Chunk(
        id="chk-sol-10",
        document_id="doc-1",
        source_id="src-test",
        content="Solución: void sort(int* arr) { ... }",
        page_start=6,
        token_count=20,
        index=1,
    )

    store.store_ingestion_bundle(src_rec, [doc], [stmt_chunk, sol_chunk])

    item = ContentItem(
        content_id="guia_1:ej_10",
        source_id="src-test",
        unit_type=UnitType.EXERCISE,
        statement_text="Ejercicio 10",
        chunk_ids=["chk-stmt-10", "chk-sol-10"],  # Note: both associated
        solution_chunk_ids=["chk-sol-10"],
        status=ContentStatus.OK,
    )
    store.content_registry.save(item)

    # Call get_statement_chunks: MUST filter out chk-sol-10
    filtered_chunks, had_sol = store.content_registry.get_statement_chunks("guia_1:ej_10", store.chunks)
    assert had_sol is True
    assert len(filtered_chunks) == 1
    assert filtered_chunks[0].id == "chk-stmt-10"

    # Authorized solution flow: get_solution_chunks returns ONLY the solution
    sol_chunks = store.content_registry.get_solution_chunks("guia_1:ej_10", store.chunks)
    assert len(sol_chunks) == 1
    assert sol_chunks[0].id == "chk-sol-10"


def test_backfill_content_registry_idempotence() -> None:
    """Invariant: running backfill_content_registry twice yields identical counts and 0 duplicates."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    src_rec = SourceRecord(
        source_id="src-tp-alg",
        manifest=SourceManifest(source_id="src-tp-alg", filename="tp.pdf", byte_size=100, sha256="b" * 64),
        source=Source(source_id="src-tp-alg", title="Guia TP Algoritmos", author="UTN", role=SourceRole.PRIMARY),
    )
    doc = Document(id="doc-tp", source_id="src-tp-alg", title="TP 1")
    c1 = Chunk(
        id="chk-tp1-01",
        document_id="doc-tp",
        source_id="src-tp-alg",
        content="TRABAJO PRACTICO Nro. 1\nEjercicio 1: Definir tipo abstracto de datos.",
        page_start=1,
        token_count=15,
        index=0,
    )
    c2 = Chunk(
        id="chk-tp1-02",
        document_id="doc-tp",
        source_id="src-tp-alg",
        content="Ejercicio 2: Implementar lista enlazada simple.",
        page_start=2,
        token_count=20,
        index=1,
    )
    store.store_ingestion_bundle(src_rec, [doc], [c1, c2])

    # Run backfill 1st time
    stats1 = backfill_content_registry(store, force=False)
    assert stats1["total_items"] >= 2

    items_run1 = store.content_registry.list_all()
    count_run1 = len(items_run1)

    # Run backfill 2nd time without force
    stats2 = backfill_content_registry(store, force=False)
    items_run2 = store.content_registry.list_all()
    count_run2 = len(items_run2)

    assert count_run1 == count_run2
    assert [i.content_id for i in items_run1] == [i.content_id for i in items_run2]
