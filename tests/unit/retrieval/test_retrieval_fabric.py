"""Integration & unit tests for RetrievalFabricLite and web endpoints (Fase 7 / F4, F5, F6)."""

import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.retrieval.adaptive_router import AdaptiveRetrievalRouter, RoutingStrategy
from study_engine.retrieval.fabric import RetrievalFabricLite, get_retrieval_trace_logger
from study_engine.retrieval.query_rewriter import QueryRewriter
from study_engine.retrieval.reranker import DeterministicLocalReranker
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container
from study_engine.web.routes.retrieval import limiter


@pytest.fixture
def populated_knowledge_store(tmp_path: Path) -> KnowledgeStore:
    """Populates a temporary KnowledgeStore for fabric testing."""
    db_path = tmp_path / "fabric_test.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    nb = Notebook(
        id="fase0-soc",
        name="Sistemas Operativos",
        description="SO course",
        subject="Computer Science",
    )
    store.create_notebook(nb)

    manifest = SourceManifest(
        source_id="tanenbaum-so",
        filename="so.pdf",
        byte_size=1000,
        sha256="a" * 64,
        metadata={"role": "PRIMARY", "priority": 1},
    )
    store.save_source(SourceRecord(source_id="tanenbaum-so", manifest=manifest))
    store.link_source_to_notebook("fase0-soc", "tanenbaum-so")

    doc = Document(
        id="doc-1",
        source_id="tanenbaum-so",
        title="Procesos",
        content="Los procesos y la memoria.",
    )
    store.save_document(doc)

    chunks = [
        Chunk(
            id="chk:proc:1",
            document_id="doc-1",
            source_id="tanenbaum-so",
            content="Un proceso es un programa en ejecucion que consume memoria virtual y stack.",
            index=0,
        ),
        Chunk(
            id="chk:proc:2",
            document_id="doc-1",
            source_id="tanenbaum-so",
            content="La sincronizacion con mutex pthread_mutex_lock previene condiciones de carrera.",
            index=1,
        ),
        Chunk(
            id="chk:sol:3",
            document_id="doc-1",
            source_id="tanenbaum-so",
            content="Solucion completa: pthread_mutex_lock(&m); x++; pthread_mutex_unlock(&m);",
            index=2,
        ),
    ]
    store.save_chunks(chunks)
    return store


def test_fabric_pipeline_execution_and_presentation_filter_f6(populated_knowledge_store: KnowledgeStore, tmp_path: Path):
    """F6: Pipeline ordenado en RetrievalFabricLite.retrieve() y filtro anti-leakage preservado."""
    # Configurar content registry con solución
    item = ContentItem(
        content_id="ex_mutex",
        source_id="tanenbaum-so",
        unit_type=UnitType.EXERCISE,
        statement_text="Ejercicio Mutex",
        chunk_ids=["chk:proc:2"],
        solution_chunk_ids=["chk:sol:3"],  # tagged solution chunk!
    )
    populated_knowledge_store.content_registry.save(item)

    fabric = RetrievalFabricLite(
        store=populated_knowledge_store,
        router=AdaptiveRetrievalRouter(),
        reranker=DeterministicLocalReranker(),
        query_rewriter=QueryRewriter(),
        content_registry=populated_knowledge_store.content_registry,
    )

    # Consulta que empareja con la solución pero NUNCA debe incluir chk:sol:3
    candidates = fabric.retrieve(
        query="sincronizacion con mutex",
        notebook_id="fase0-soc",
        top_k=5,
    )

    assert len(candidates) >= 1
    chunk_ids = [c.chunk_id for c in candidates]
    # F6 Invariante: chk:sol:3 filtrado por filter_presentation
    assert "chk:sol:3" not in chunk_ids
    assert "chk:proc:2" in chunk_ids
    # Ranks ordenados 1..N
    assert [c.rank for c in candidates] == list(range(1, len(candidates) + 1))


def test_fabric_trace_logger_rotation_and_json_event_f5(populated_knowledge_store: KnowledgeStore, monkeypatch, tmp_path: Path):
    """F5: Logger configurado con RotatingFileHandler (maxBytes=10MB, backupCount=5) y emisión JSON."""
    trace_logger = get_retrieval_trace_logger()
    from logging.handlers import RotatingFileHandler
    rotating_handlers = [h for h in trace_logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(rotating_handlers) >= 1
    h = rotating_handlers[0]
    assert h.maxBytes == 10_485_760
    assert h.backupCount == 5

    # Ejecutar retrieve y capturar emisión
    logged_lines = []

    def mock_info(msg):
        logged_lines.append(msg)

    monkeypatch.setattr(trace_logger, "info", mock_info)

    fabric = RetrievalFabricLite(
        store=populated_knowledge_store,
        router=AdaptiveRetrievalRouter(),
        reranker=DeterministicLocalReranker(),
    )

    results = fabric.retrieve(
        query="explicar proceso y memoria virtual",
        notebook_id="fase0-soc",
        top_k=2,
    )

    assert len(logged_lines) >= 1
    event = json.loads(logged_lines[-1])
    assert event["event"] == "RETRIEVAL_FABRIC_TRACE"
    assert event["query"] == "explicar proceso y memoria virtual"
    assert "strategy" in event
    assert "pool_depth" in event
    assert "top_k_returned" in event
    assert "reranker_used" in event
    assert "latency_ms" in event


def test_fabric_status_endpoint(tmp_path: Path):
    """GET /api/retrieval/fabric/status retorna diagnóstico y capacidades del subsistema."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    r = client.get("/api/retrieval/fabric/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["subsystem"] == "RetrievalFabricLite"
    assert "jina_model" in data
    assert "supported_strategies" in data
    assert data["rate_limit_inspect"] == "10/minute"


def test_fabric_inspect_endpoint_rate_limiting_and_auth_f4(tmp_path: Path):
    """F4: POST /api/retrieval/fabric/inspect protegido con X-Admin-Token (403) y rate limit (10/min -> 429)."""
    limiter.reset()  # Reset rate limiter
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    url = "/api/retrieval/fabric/inspect"
    payload = {"query": "sincronizacion con mutex", "notebook_id": "fase0-soc", "top_k": 3}

    # 1. Sin header: 403 Forbidden
    r_no_auth = client.post(url, json=payload)
    assert r_no_auth.status_code == 403
    assert "X-Admin-Token" in r_no_auth.json()["detail"]

    # 2. Con token inválido: 403 Forbidden
    r_bad_auth = client.post(url, json=payload, headers={"X-Admin-Token": "bad-token"})
    assert r_bad_auth.status_code == 403

    # 3. Con token válido: 10 llamadas exitosas (200 OK)
    limiter.reset()
    admin_headers = {"X-Admin-Token": "talos-admin-secret-dev"}
    for i in range(10):
        r_ok = client.post(url, json=payload, headers=admin_headers)
        assert r_ok.status_code == 200, f"Fallo en llamada {i+1}: {r_ok.text}"
        data = r_ok.json()
        assert data["status"] == "OK"
        assert "routing_decision" in data
        assert "candidates" in data

    # 4. Llamada 11: 429 Too Many Requests (F4 Rate Limit)
    r_limited = client.post(url, json=payload, headers=admin_headers)
    assert r_limited.status_code == 429
    assert "Too Many Requests" in r_limited.json()["detail"]
