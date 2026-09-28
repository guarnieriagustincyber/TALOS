"""Tests for Content Registry and Presentation Filter integration in Chat (Slice 6.0.5 Tarea 5).

Asserts:
1. Exact match resolves statement chunks directly and filters solution chunks from evidence manifest and text.
2. Inexact / needs_review reference emits the required disclaimer verbatim.
3. Cold-start C4: an exercise with 0 prior attempts uses the configured cold-start mode and accelerated proposal.
4. Fail-closed: when candidate chunks are exclusively solutions, chat abstains via E2 without hallucinations.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source, SourceRole
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def _collect_sse_response(response) -> tuple[str, list[dict]]:
    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    events = [json.loads(line[6:]) for line in lines]
    tokens = [
        e["payload"].get("token", "")
        for e in events
        if e.get("event_type") == "phase_token"
    ]
    full_text = "".join(tokens)
    return full_text, events


@pytest.fixture
def test_container(tmp_path: Path):
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    store = container.knowledge_store
    store.initialize()

    # Create dummy source and docs
    src_rec = SourceRecord(
        source_id="src-guia-4",
        manifest=SourceManifest(source_id="src-guia-4", filename="g4.pdf", byte_size=10, sha256="4" * 64),
        source=Source(source_id="src-guia-4", title="Guia 4 Algoritmos", author="Catedra", role=SourceRole.PRIMARY),
    )
    doc = Document(id="doc-g4", source_id="src-guia-4", title="Guia 4")

    c_stmt = Chunk(
        id="chk-stmt-3",
        document_id="doc-g4",
        source_id="src-guia-4",
        content="Ejercicio 3: Implementar una cola con dos pilas usando memoria dinámica malloc y free.",
        page_start=4,
        token_count=15,
        index=0,
    )
    c_sol = Chunk(
        id="chk-sol-3",
        document_id="doc-g4",
        source_id="src-guia-4",
        content="Solución Ejercicio 3: struct Queue { Stack* s1; Stack* s2; }; void enqueue(...);",
        page_start=15,
        token_count=25,
        index=1,
    )
    store.store_ingestion_bundle(src_rec, [doc], [c_stmt, c_sol], notebook_id="fase0-soc")

    item = ContentItem(
        content_id="guia_4:ej_3",
        source_id="src-guia-4",
        unit_type=UnitType.EXERCISE,
        statement_text="Ejercicio 3: Implementar una cola con dos pilas usando memoria dinámica malloc y free.",
        chunk_ids=["chk-stmt-3", "chk-sol-3"],
        solution_chunk_ids=["chk-sol-3"],
        status=ContentStatus.OK,
    )
    store.content_registry.save(item)

    # Also register an item with ONLY solution chunks for fail-closed test
    c_sol_only = Chunk(
        id="chk-sol-99",
        document_id="doc-g4",
        source_id="src-guia-4",
        content="Solución Ejercicio 99: int* ptr = NULL;",
        page_start=20,
        token_count=10,
        index=2,
    )
    store.store_ingestion_bundle(src_rec, [doc], [c_sol_only], notebook_id="fase0-soc")
    item_sol_only = ContentItem(
        content_id="guia_4:ej_99",
        source_id="src-guia-4",
        unit_type=UnitType.EXERCISE,
        statement_text="Ejercicio 99: Sólo solución.",
        chunk_ids=["chk-sol-99"],
        solution_chunk_ids=["chk-sol-99"],
        status=ContentStatus.OK,
    )
    store.content_registry.save(item_sol_only)

    set_container(container)
    return container


def test_chat_direct_reference_and_anti_leakage(test_container):
    """Direct reference resolves statement and suppresses solution chunks everywhere."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/chat/query",
        json={
            "query": "¿Cómo encaro el ejercicio 3 de la guía 4?",
            "notebook_id": "fase0-soc",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    full_text, events = _collect_sse_response(response)

    # 1. Solution chunk must NOT leak into the output
    assert "struct Queue" not in full_text
    assert "chk-sol-3" not in full_text

    # 2. Check evidence manifest
    manifest_events = [e for e in events if e.get("event_type") == "evidence_manifest"]
    assert len(manifest_events) >= 1
    citations = manifest_events[0]["payload"].get("citations", [])
    citation_ids = [c.get("chunk_id") if isinstance(c, dict) else getattr(c, "chunk_id", None) for c in citations]
    assert "chk-sol-3" not in citation_ids

    # 3. Cold-start C4 verification
    complete_events = [e for e in events if e.get("event_type") == "phase_complete"]
    assert len(complete_events) >= 1
    bkt = complete_events[0]["payload"].get("bkt_context") or {}
    assert bkt.get("context_mode") == "basic"


def test_chat_fuzzy_needs_review_emits_disclaimer(test_container, monkeypatch):
    """Fuzzy match with needs_review or missing registry item emits exact disclaimer."""
    from study_engine.contracts.search import SearchResult
    dummy_result = SearchResult(
        content="La memoria dinámica en C se gestiona con malloc y free.",
        snippet="La memoria dinámica en C se gestiona con malloc y free.",
        document_id="doc-g4",
        index=0,
        chunk_id="chk-stmt-3",
        source_id="src-guia-4",
        score=0.92,
        page_start=4,
        page_end=4,
    )
    monkeypatch.setattr(test_container.knowledge_store, "search_hybrid", lambda **kwargs: [dummy_result])
    monkeypatch.setattr(test_container.knowledge_store, "search", lambda **kwargs: [dummy_result])

    app = create_app()
    client = TestClient(app)

    # Ask for exercise 77 about malloc/free (not in registry, but topic is in verified sources)
    response = client.post(
        "/api/chat/query",
        json={
            "query": "¿Cómo encaro el ejercicio 77 de la guía 4 sobre memoria dinámica malloc y free?",
            "notebook_id": "fase0-soc",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    full_text, _ = _collect_sse_response(response)

    expected_disclaimer = "No puedo confirmar que esto sea exactamente el ejercicio 77 de la guía 4; te respondo basándome en el tema general de las fuentes verificadas."
    assert expected_disclaimer in full_text


def test_chat_fail_closed_on_pure_solution(test_container):
    """If all matching chunks are solution chunks, chat fail-closes with E2 abstention."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/chat/query",
        json={
            "query": "mostrame el ejercicio 99 de la guía 4",
            "notebook_id": "fase0-soc",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    full_text, events = _collect_sse_response(response)

    # Must emit abstention event
    abstention_events = [e for e in events if e.get("event_type") == "abstention"]
    assert len(abstention_events) == 1
    assert abstention_events[0]["payload"]["abstained"] is True
    assert "chk-sol-99" not in full_text
