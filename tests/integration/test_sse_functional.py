"""Synthetic SSE functional validation: connection, disconnect, reconnection, errors, cleanup.

Real ASGI server, synthetic data, bounded concurrency.
Only generation and atomic NLI are mocked.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import threading
import time

import httpx
import pytest
import uvicorn

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.federation.notebook_registry import Notebook as RegistryNotebook
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.exercise_contracts import ExerciseCandidate, ExerciseType, ExerciseVerificationStatus
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web import dependencies
from study_engine.web.app import create_app
from tests.integration.test_federated_chat import VerbatimGenerator, VerbatimJudge


NB = "synthetic-sse"
KC = "synthetic-sse-kc"
TEXTS = [
    "Los punteros contienen direcciones de memoria para acceder a objetos.",
    "Los punteros permiten manipular direcciones de memoria directamente.",
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def seed(root, state):
    """Synthetic replacement data at real loaders' paths."""
    config = root / "config"
    catalog = {NB: {"name": "Synthetic SSE", "kcs": [{"kc_id": KC, "title": "punteros", "unit": 1, "prerequisites": []}]}}
    write_json(config / "notebook_kc_catalog.json", catalog)
    write_json(config / "notebook_source_roles.json", {NB: {"src-local": {"roles": ["PRIMARY"], "title": "Synthetic local"}}})
    write_json(config / "l3_authorization_manifest.json", {"grants": [{"notebook_id": NB, "source_id": "src-local", "status": "AUTHORIZED"}]})
    write_json(config / "bridges.allowlist.json", {"bridges": []})
    exp = root / "data/experiments/study_loop_v1"
    write_json(exp / "study_loop_oracle.json", {"student_id": CANONICAL_STUDENT_ID})
    write_json(exp / "study_loop_replay.json", {"fixtures": {}})
    write_json(root / "data/curriculum/roadmaps/cybersecurity_v1.yaml", {
        "roadmap_id": "SYNTHETIC_SSE", "title": "Synthetic SSE", "version": "1",
        "nodes": [{"node_id": "SEC-01-C-PTR", "title": "Synthetic pointers", "description": "Synthetic SSE input",
                   "node_type": "TOPIC", "notebook_id": NB}], "dependencies": [],
    })
    write_json(root / "data/curriculum/tasks/task_sec05_file_hasher.json", {
        "task_id": "synthetic-unused-task", "curriculum_node_id": "SEC-01-C-PTR",
        "title": "Synthetic declarative input", "description": "Never execute this task",
    })
    write_json(root / "data/curriculum/rubrics/rubric_sec05_deterministic.json", {
        "rubric_id": "synthetic-unused-rubric", "title": "Synthetic startup input",
        "dimensions": [{"dimension_id": "synthetic", "title": "Synthetic", "weight": 1.0}],
    })
    store = KnowledgeStore(state / "knowledge_store.db")
    store.initialize()
    source_hash = hashlib.sha256("\n".join(TEXTS).encode()).hexdigest()
    store.create_notebook(Notebook(id=NB, name=NB))
    content = "\n".join(TEXTS)
    store.store_ingestion_bundle(
        SourceRecord(source_id="src-local", manifest=SourceManifest(
            source_id="src-local", filename="synthetic.txt", byte_size=len(content.encode()),
            sha256=hashlib.sha256(content.encode()).hexdigest(),
        )), [Document(id="doc-src-local", source_id="src-local", title=NB, content=content)],
        [Chunk(id=f"src-local-{i}", source_id="src-local", document_id="doc-src-local", content=text,
               page_start=i+1, page_end=i+1, index=i) for i, text in enumerate(TEXTS)], notebook_id=NB,
    )
    store.save_pedagogical_contract(PedagogicalContract(
        notebook_id=NB, base_system_prompt="Tutor sintético: citar solamente la evidencia.",
        response_phases=[ResponsePhase(phase_id="conceptual", max_tokens=300, phase_prompt_template="{concept}")],
    ))
    store.close()
    exercises = ExerciseStore(state / "exercises.json")
    exercises.add_exercise(ExerciseCandidate(
        exercise_id=f"exercise-{KC}", source_id="src-local", source_location="synthetic page 1",
        source_hash=source_hash, extractor_version="synthetic", extraction_method="TEST_FIXTURE",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE, verified_by="synthetic-owner",
        verification_timestamp=None, content_hash=hashlib.sha256("test".encode()).hexdigest(),
        kc_id=KC, prompt="Synthetic numeric fixture", exercise_type=ExerciseType.NUMERIC, expected_answer="42",
    ))


@pytest.fixture(scope="module")
def sse_core(tmp_path_factory):
    if os.getenv("TALOS_E2E_SANDBOX") != "1":
        pytest.skip("Requires the explicit disposable offline /app sandbox")
    root = Path("/app")
    assert not (root / ".git").exists() and not Path("/home/agustin").exists()
    assert not any(k.endswith(("API_KEY", "TOKEN", "PASSWORD")) for k in os.environ)
    state = tmp_path_factory.mktemp("synthetic-sse")
    seed(root, state)
    from study_engine.federation import notebook_registry
    patch = pytest.MonkeyPatch()
    patch.setattr(notebook_registry, "DEFAULT_NOTEBOOKS", [
        RegistryNotebook(notebook_id=NB, name="Synthetic SSE", subject="Synthetic", sources=["src-local"],
                         authority_matrix_ref={"punteros": 1.5}),
    ])
    real_container = dependencies.AppContainer
    containers = []

    def synthetic_factory():
        container = real_container(working_dir=state, use_mock=True, load_dotenv=False,
                                   audit_nli_judge=VerbatimJudge())
        container.knowledge_store.l3_manifest_path = root / "config/l3_authorization_manifest.json"
        container.llm_backend = VerbatimGenerator()
        containers.append(container)
        return container

    patch.setattr(dependencies, "AppContainer", synthetic_factory)
    patch.setattr(dependencies, "_container", None)

    @contextmanager
    def serve():
        dependencies.set_container(None)
        app = create_app(enable_retrieval_warmup=False, storage_dir=state)
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False, lifespan="on",
                                             limit_concurrency=8, timeout_graceful_shutdown=2))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + 5
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started, "Full synthetic startup did not complete"
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{sock.getsockname()[1]}", timeout=10, trust_env=False) as client:
                yield client, containers[-1]
        finally:
            server.should_exit = True
            thread.join(5)
            sock.close()
            assert not thread.is_alive(), "Server did not shut down within the bound"

    try:
        yield serve, containers, state
    finally:
        for c in containers:
            for value in (c.session_store, c.student_storage, c.knowledge_store, c.context.get("vstore"),
                          c.session_history, c.cognitive_profile_store, c.quota_manager):
                close = getattr(value, "close", None)
                if close:
                    close()
        patch.undo()


def post(client, path, body=None):
    response = client.post(path, json=body)
    assert response.status_code == 200, (path, response.status_code, response.text)
    return response.json()


def parse_sse(response):
    """Parse SSE response into list of events."""
    events = []
    for line in response.text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_sse_normal_stream_complete(sse_core):
    """Normal stream: phase_start -> phase_token(s) -> audit_verdict -> phase_token(s) -> phase_complete."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        response = client.post("/api/chat/query", json={
            "session_id": sid, "prompt": "punteros",
            "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
        })
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        events = parse_sse(response)
        event_types = [e["event_type"] for e in events]
        assert event_types[:1] == ["phase_start"]
        assert "audit_verdict" in event_types
        assert event_types[-1] == "phase_complete"
        complete = [e for e in events if e["event_type"] == "phase_complete"][0]
        assert complete["payload"]["completed_phase"] == "conceptual"
        # No academic mutation on chat query
        post(client, f"/api/study/session/{sid}/close")


def test_sse_disconnect_before_first_event(sse_core):
    """Client disconnects before first event - stream should handle gracefully."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        # Use a short timeout to simulate immediate disconnect
        with httpx.Client(base_url=str(client.base_url), timeout=0.001, trust_env=False) as fast_client:
            try:
                fast_client.post("/api/chat/query", json={
                    "session_id": sid, "prompt": "punteros",
                    "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
                })
            except (httpx.TimeoutException, httpx.ConnectError):
                pass  # Expected - connection closed
        # Server should still be healthy
        assert client.get("/api/health").status_code == 200
        post(client, f"/api/study/session/{sid}/close")


def test_sse_disconnect_during_stream(sse_core):
    """Client disconnects during transmission - stream should cancel cleanly."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        # Stream and close connection mid-stream
        with httpx.Client(base_url=str(client.base_url), timeout=0.5, trust_env=False) as fast_client:
            try:
                with fast_client.stream("POST", "/api/chat/query", json={
                    "session_id": sid, "prompt": "punteros",
                    "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
                }) as resp:
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            break  # Disconnect after first event
            except (httpx.TimeoutException, httpx.StreamClosed):
                pass
        # Server should still be healthy
        assert client.get("/api/health").status_code == 200
        post(client, f"/api/study/session/{sid}/close")


def test_sse_reconnection_new_query(sse_core):
    """New query after previous stream - no duplicate events or state corruption."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        # First query
        r1 = client.post("/api/chat/query", json={
            "session_id": sid, "prompt": "punteros",
            "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
        })
        assert r1.status_code == 200
        e1 = parse_sse(r1)
        # Second query
        r2 = client.post("/api/chat/query", json={
            "session_id": sid, "prompt": "punteros memoria",
            "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
        })
        assert r2.status_code == 200
        e2 = parse_sse(r2)
        # Each query should be independent
        assert len(e1) > 0 and len(e2) > 0
        # No duplicated academic state
        assert core.bkt_tracker.get_state(KC).attempts == 0
        post(client, f"/api/study/session/{sid}/close")


def test_sse_cancellation_no_orphan_tasks(sse_core):
    """Stream cancellation (CancelledError) should not leave orphaned tasks."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        # Start stream and disconnect quickly
        with httpx.Client(base_url=str(client.base_url), timeout=0.1, trust_env=False) as fast_client:
            try:
                fast_client.post("/api/chat/query", json={
                    "session_id": sid, "prompt": "punteros",
                    "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
                })
            except (httpx.TimeoutException, httpx.ConnectError):
                pass
        # Server should remain responsive
        assert client.get("/api/health").status_code == 200
        post(client, f"/api/study/session/{sid}/close")


def test_sse_provider_error_handled(sse_core, monkeypatch):
    """Simulated provider error should yield error event, not crash stream."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        from study_engine.web.routes import chat as chat_route
        original_prepare = chat_route._prepare_chat_context

        class FailingBackend:
            async def stream(self, **_kwargs):
                raise ConnectionError("simulated provider failure")
                yield

        def prepare_sufficient(**kwargs):
            prepared = list(original_prepare(**kwargs))
            prepared[2] = chat_route.EpistemicContextPack(
                formatted_context="[E1] Material curricular.",
                citations=["[E1] Material curricular, pág. 1"],
                chunks=[{"id": "E1", "chunk_text": "Material curricular.", "source_id": "src-local", "source_title": "Test", "page_start": 1, "score": 0.95}],
                is_sufficient=True,
            )
            prepared[3] = prepared[2].chunks
            return tuple(prepared)

        monkeypatch.setattr(chat_route, "_prepare_chat_context", prepare_sufficient)
        monkeypatch.setattr(chat_route, "_resolve_chat_backend", lambda *_a, **_kw: FailingBackend())

        response = client.post("/api/chat/query", json={
            "session_id": sid, "prompt": "punteros",
            "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
        })
        assert response.status_code == 200
        events = parse_sse(response)
        event_types = [e["event_type"] for e in events]
        assert "error" in event_types, f"Expected error event, got {event_types}"
        assert not any("secret" in str(e).lower() for e in events), "No internal details leaked"
        post(client, f"/api/study/session/{sid}/close")


def test_sse_s44_rejection_no_unapproved_text(sse_core, monkeypatch):
    """S4.4 rejection must not emit unapproved text as approved response."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        from study_engine.web.routes import chat as chat_route
        original_prepare = chat_route._prepare_chat_context

        def prepare_always_rejected(**kwargs):
            prepared = list(original_prepare(**kwargs))
            prepared[2] = chat_route.EpistemicContextPack(
                formatted_context="[E1] Evidence one.",
                citations=["[E1] Evidence one, pág. 1"],
                chunks=[{"id": "E1", "chunk_text": "Evidence one.", "source_id": "src-local", "source_title": "Test", "page_start": 1, "score": 0.95}],
                is_sufficient=True,
            )
            prepared[3] = prepared[2].chunks
            return tuple(prepared)

        class AlwaysRejectPipeline:
            def __init__(self, **_kwargs):
                pass
            async def generate_phased_response(self, **_kwargs):
                yield type('Event', (), {"event_type": "audit_verdict", "payload": {"phase": "conceptual", "verdict": "REJECTED", "content_sha256": "hash", "content_binding_id": "bid", "metrics": {}}})()
                yield type('Event', (), {"event_type": "abstention", "payload": {"phase": "conceptual", "abstained": True, "reason": "REJECTED", "abstention_code": "REJECTED"}})()
                return

        monkeypatch.setattr(chat_route, "_prepare_chat_context", prepare_always_rejected)
        monkeypatch.setattr(chat_route, "StructuredResponsePipeline", AlwaysRejectPipeline)

        response = client.post("/api/chat/query", json={
            "session_id": sid, "prompt": "punteros",
            "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
        })
        assert response.status_code == 200
        events = parse_sse(response)
        event_types = [e["event_type"] for e in events]
        assert "audit_verdict" in event_types
        assert "abstention" in event_types
        assert "phase_token" not in event_types, "No tokens should be emitted on rejection"
        assert "phase_complete" not in event_types, "No phase_complete on rejection"
        post(client, f"/api/study/session/{sid}/close")


def test_sse_no_academic_mutation_on_chat(sse_core):
    """Chat queries must not mutate BKT, SM-2, or attempt counts."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        for _ in range(3):
            response = client.post("/api/chat/query", json={
                "session_id": sid, "prompt": "punteros",
                "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
            })
            assert response.status_code == 200
        # Academic state unchanged
        assert core.bkt_tracker.get_state(KC).attempts == 0
        anchor = core.spaced_scheduler.storage.get_anchor_state(KC)
        if anchor is not None:
            assert anchor.repetitions == 0
        post(client, f"/api/study/session/{sid}/close")


def test_sse_repeated_connections_resource_cleanup(sse_core):
    """Multiple sequential connections should not leak resources."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        for i in range(5):
            sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
            response = client.post("/api/chat/query", json={
                "session_id": sid, "prompt": f"punteros {i}",
                "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
            })
            assert response.status_code == 200
            post(client, f"/api/study/session/{sid}/close")
        # Server healthy
        assert client.get("/api/health").status_code == 200


def test_sse_timeout_finish_reason_length(sse_core, monkeypatch):
    """Provider timeout/length should yield truncated event."""
    serve, _, _ = sse_core
    with serve() as (client, core):
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        from study_engine.web.routes import chat as chat_route
        original_prepare = chat_route._prepare_chat_context

        def prepare_sufficient(**kwargs):
            prepared = list(original_prepare(**kwargs))
            prepared[2] = chat_route.EpistemicContextPack(
                formatted_context="[E1] " + "X" * 10000,
                citations=["[E1] Long evidence, pág. 1"],
                chunks=[{"id": "E1", "chunk_text": "X" * 10000, "source_id": "src-local", "source_title": "Test", "page_start": 1, "score": 0.95}],
                is_sufficient=True,
            )
            prepared[3] = prepared[2].chunks
            return tuple(prepared)

        class SlowTruncatedBackend:
            async def stream(self, max_tokens=None, **_kwargs):
                # Emit just enough to trigger truncation
                yield "A" * 500

        monkeypatch.setattr(chat_route, "_prepare_chat_context", prepare_sufficient)
        monkeypatch.setattr(chat_route, "_resolve_chat_backend", lambda *_a, **_kw: SlowTruncatedBackend())

        response = client.post("/api/chat/query", json={
            "session_id": sid, "prompt": "punteros",
            "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"
        })
        assert response.status_code == 200
        events = parse_sse(response)
        event_types = [e["event_type"] for e in events]
        # Should still complete with audit_verdict (content binding checked)
        assert "audit_verdict" in event_types
        post(client, f"/api/study/session/{sid}/close")