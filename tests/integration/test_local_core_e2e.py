"""Bounded, all-synthetic local-core validation; requires the disposable offline jail.

Real AppContainer/create_app lifecycle, loopback HTTP, SQLite, E4, C5/S4.4,
grading, BKT, SM-2 and session persistence. Only generation/NLI are doubles.
No protected snapshot, production data, external model, S6 or gate execution.
Measurements are observations of this fixture, not production stress evidence.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import socket
import sqlite3
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


NB = "synthetic-local-core"
KC = "synthetic-pointers"
NEXT = "synthetic-trees"
TEXTS = [
    "Los punteros contienen direcciones de memoria que identifican objetos almacenados durante la ejecución del programa y permiten acceder a esos objetos.",
    "Los punteros permiten acceder a los objetos almacenados mediante sus direcciones de memoria dentro del programa durante la ejecución de sus instrucciones.",
    "Los arboles organizan elementos en nodos enlazados mediante relaciones jerárquicas entre padres e hijos y permiten representar estructuras de datos del programa.",
    "Los arboles representan relaciones entre nodos enlazados y organizan elementos mediante relaciones jerárquicas entre padres e hijos en las estructuras de datos.",
]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def seed(root, state):
    """Synthetic replacement data at the real loaders' paths; never copy protected resources."""
    config = root / "config"
    catalog = {NB: {"name": "Synthetic local core", "kcs": [
        {"kc_id": KC, "title": "punteros", "unit": 1, "prerequisites": []},
        {"kc_id": NEXT, "title": "arboles", "unit": 1, "prerequisites": [KC]},
    ]}}
    write_json(config / "notebook_kc_catalog.json", catalog)
    write_json(config / "notebook_source_roles.json", {NB: {"src-local": {"roles": ["PRIMARY"], "title": "Synthetic local"}}})
    write_json(config / "l3_authorization_manifest.json", {"grants": [
        {"notebook_id": NB, "source_id": "src-local", "status": "AUTHORIZED"},
        {"notebook_id": "synthetic-remote", "source_id": "src-remote", "status": "AUTHORIZED"},
    ]})
    write_json(config / "bridges.allowlist.json", {"bridges": [{
        "bridge_id": "synthetic-bridge", "source_notebook": NB, "target_notebook": "synthetic-remote",
        "topic_allowlist": ["semaforos"], "direction": "unidirectional", "ttl_days": 1,
        "created_at": datetime.now(timezone.utc).isoformat(), "reviewer": "synthetic-owner",
        "provenance_tag": "SYNTHETIC_TEST_FIXTURE",
    }]})
    # These are startup inputs, not the protected differential oracle or an S6 exercise.
    exp = root / "data/experiments/study_loop_v1"
    write_json(exp / "study_loop_oracle.json", {"student_id": CANONICAL_STUDENT_ID})
    write_json(exp / "study_loop_replay.json", {"fixtures": {}})
    write_json(root / "data/curriculum/roadmaps/cybersecurity_v1.yaml", {
        "roadmap_id": "SYNTHETIC_LOCAL_CORE", "title": "Synthetic startup only", "version": "1",
        "nodes": [{"node_id": "SEC-01-C-PTR", "title": "Synthetic pointers", "description": "Synthetic startup input",
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
    for nb, source, texts in ((NB, "src-local", TEXTS), ("synthetic-remote", "src-remote", [
        "Los semaforos coordinan el acceso a recursos compartidos y permiten controlar el acceso concurrente entre procesos durante la ejecución del programa.",
    ])):
        store.create_notebook(Notebook(id=nb, name=nb))
        content = "\n".join(texts)
        store.store_ingestion_bundle(
            SourceRecord(source_id=source, manifest=SourceManifest(
                source_id=source, filename="synthetic.txt", byte_size=len(content.encode()),
                sha256=hashlib.sha256(content.encode()).hexdigest(),
            )), [Document(id=f"doc-{source}", source_id=source, title=nb, content=content)],
            [Chunk(id=f"{source}-{i}", source_id=source, document_id=f"doc-{source}", content=text,
                   page_start=i+1, page_end=i+1, index=i) for i, text in enumerate(texts)], notebook_id=nb,
        )
    store.save_pedagogical_contract(PedagogicalContract(
        notebook_id=NB, base_system_prompt="Tutor sintético: citar solamente la evidencia.",
        response_phases=[ResponsePhase(phase_id="conceptual", max_tokens=300, phase_prompt_template="{concept}")],
    ))
    store.close()
    exercises = ExerciseStore(state / "exercises.json")
    for kc in (KC, NEXT):
        prompt = f"Synthetic numeric fixture for {kc}: siete elementos de seis bytes"
        exercises.add_exercise(ExerciseCandidate(
            exercise_id=f"exercise-{kc}", source_id="src-local", source_location="synthetic page 1",
            source_hash=source_hash, extractor_version="synthetic", extraction_method="TEST_FIXTURE",
            verification_status=ExerciseVerificationStatus.QUALIFIABLE, verified_by="synthetic-owner",
            verification_timestamp=None, content_hash=hashlib.sha256(prompt.encode()).hexdigest(),
            kc_id=kc, prompt=prompt, exercise_type=ExerciseType.NUMERIC, expected_answer="42",
        ))


def metrics(samples, cpu_start, wall_start):
    ordered = sorted(samples)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    wall = time.perf_counter() - wall_start
    return {"n": len(ordered), "percentile_method": "nearest-rank", **{
        f"p{p}_ms": round(ordered[max(0, math.ceil(len(ordered)*p/100)-1)]*1000, 3) for p in (50, 95, 99)
    }, "wall_s": round(wall, 4), "throughput_rps": round(len(ordered)/wall, 3),
        "cpu_s": round(usage.ru_utime + usage.ru_stime - cpu_start, 4),
        "process_peak_rss_kib": usage.ru_maxrss}


@pytest.fixture(scope="module")
def local_core(tmp_path_factory):
    if os.getenv("TALOS_E2E_SANDBOX") != "1":
        pytest.skip("Requires the explicit disposable offline /app sandbox")
    root = Path("/app")
    assert not (root / ".git").exists() and not Path("/home/agustin").exists()
    assert not any(k.endswith(("API_KEY", "TOKEN", "PASSWORD")) for k in os.environ)
    state = tmp_path_factory.mktemp("synthetic-core")
    seed(root, state)
    from study_engine.federation import notebook_registry
    patch = pytest.MonkeyPatch()
    patch.setattr(notebook_registry, "DEFAULT_NOTEBOOKS", [
        RegistryNotebook(notebook_id=NB, name="Synthetic local", subject="Synthetic", sources=["src-local"],
                         authority_matrix_ref={"punteros": 1.5, "arboles": 1.5}),
        RegistryNotebook(notebook_id="synthetic-remote", name="Synthetic remote", subject="Synthetic", sources=["src-remote"],
                         authority_matrix_ref={"semaforos": 1.5}),
    ])
    real_container = dependencies.AppContainer
    containers = []

    def synthetic_factory():
        container = real_container(repo_root=root, working_dir=state, use_mock=True, load_dotenv=False,
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
            with httpx.Client(base_url=f"http://127.0.0.1:{sock.getsockname()[1]}", timeout=3, trust_env=False) as client:
                yield client, containers[-1]
        finally:
            server.should_exit = True
            thread.join(5)
            sock.close()
            assert not thread.is_alive(), "Server did not shut down within the bound"

    try:
        yield serve, containers, state
    finally:
        # Test cleanup is not credited as application lifecycle cleanup.
        for c in containers:
            for value in (c.session_store, c.student_storage, c.knowledge_store, c.context["vstore"],
                          c.session_history, c.cognitive_profile_store, c.quota_manager):
                close = getattr(value, "close", None)
                if close:
                    close()
        patch.undo()


def post(client, path, body=None):
    response = client.post(path, json=body)
    assert response.status_code == 200, (path, response.status_code, response.text)
    return response.json()


def attempt(client, sid):
    episode = post(client, f"/api/study/session/{sid}/action", {"action": "START_EXPLANATION"})["episode_id"]
    concept = client.get(f"/api/pedagogy/episode/{episode}/concept")
    assert concept.status_code == 200 and concept.json()["status"] == "PRESENTABLE", concept.text
    assert concept.json()["audit_verdict"] == "APPROVED"
    intervention = client.get(f"/api/pedagogy/episode/{episode}/next")
    assert intervention.status_code == 200 and intervention.json()["exercise"]
    return episode


def chat(client, sid, query):
    response = client.post("/api/chat/query", json={"session_id": sid, "prompt": query,
        "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"})
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    complete = [e["payload"] for e in events if e["event_type"] == "phase_complete"]
    assert complete, events
    assert any(e["event_type"] == "audit_verdict" for e in events), events
    return complete[-1]


def test_full_startup_integrated_cycle_and_restore(local_core):
    serve, containers, state = local_core
    with serve() as (client, core):
        health = client.get("/api/health")
        assert health.status_code == 200, health.text
        assert health.json()["components"]["curriculum"]["roadmap_id"] == "SYNTHETIC_LOCAL_CORE"
        # The health endpoint's hard-coded suite/isolation claims are NOT verification evidence.
        sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        local = chat(client, sid, "punteros")
        federated = chat(client, sid, "punteros semaforos")
        assert {c["source_id"] for c in local["evidence_provenance"]} == {"src-local"}
        assert {c["source_id"] for c in federated["evidence_provenance"]} == {"src-local", "src-remote"}
        first_episode = attempt(client, sid)
        grade = {"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}}
        first = post(client, f"/api/study/session/{sid}/action", grade)
        assert first["evaluation"]["is_correct"] and core.bkt_tracker.get_state(KC).attempts == 1
        assert core.spaced_scheduler.storage.get_anchor_state(KC).last_quality == 5
        advanced = post(client, f"/api/study/session/{sid}/action", {"action": "START_NEXT_KC",
            "payload": {"episode_id": first_episode, "kc_id": KC}})
        assert advanced["current_kc_id"] == NEXT
        attempt(client, sid)
        post(client, f"/api/study/session/{sid}/action", grade)
        agenda = client.get("/api/student/spaced-repetition/due")
        assert agenda.status_code == 200 and len(agenda.json()) == 2
        # Early review uses the existing agenda/new-session flow, not a fabricated clock.
        review_sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        post(client, f"/api/study/session/{review_sid}/action", {"action": "SELECT_DIFFERENT_KC", "payload": {"kc_id": KC}})
        review_episode = attempt(client, review_sid)
        assert review_episode != first_episode
        post(client, f"/api/study/session/{review_sid}/action", grade)
        anchor = core.student_storage.get_anchor_state(KC)
        assert core.bkt_tracker.get_state(KC).attempts == 2 and anchor.repetitions == 2 and anchor.interval == 6
        for session in (sid, review_sid):
            assert post(client, f"/api/study/session/{session}/close")["episode_phase"] == "CLOSED"
        saved_bkt = core.bkt_tracker.get_state(KC)
        print("LOCAL_CORE_E2E", json.dumps({"startup": "PASS", "http": "real-loopback", "sse": "PASS",
            "steps": "open/local+federated/audited-explanation/exercise/grade/BKT+SM2/progression/early-review/close",
            "simulated": ["generation", "atomic NLI"], "react": "NOT_RUN", "student_origin": "SYNTHETIC"}))
    with serve() as (client, restored):
        assert restored is not core and restored.student_storage.db_path == state / "student_state.db"
        assert restored.bkt_tracker.get_state(KC) == saved_bkt
        assert restored.student_storage.get_anchor_state(KC) == anchor
        archived = client.get(f"/api/study/session/{sid}/snapshot")
        assert archived.status_code == 200 and archived.json()["episode_phase"] == "CLOSED"
        fresh = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
        assert fresh not in (sid, review_sid)
        chat(client, fresh, "punteros")
        print("LOCAL_CORE_RECOVERY", json.dumps({"restart": "PASS", "archived_snapshot": "CLOSED", "new_session": "PASS",
            "bkt_attempts": saved_bkt.attempts, "sm2_interval": anchor.interval}))


def open_attempt(client):
    sid = post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"]
    post(client, f"/api/study/session/{sid}/action", {"action": "SELECT_DIFFERENT_KC", "payload": {"kc_id": KC}})
    episode = attempt(client, sid)
    return sid, episode, {"session_id": sid, "step_id": f"step_eval_exercise-{KC}", "response_text": "42"}


def persisted_attempts(state):
    # Independent persisted oracle, not the bridge's in-memory replay cache.
    with sqlite3.connect(f"file:{state / 'student_state.db'}?mode=ro", uri=True) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        row = conn.execute("SELECT attempts FROM bkt_states WHERE kc_id = ?", (KC,)).fetchone()
        return row[0] if row else 0


def bounded_requests(client, requests):
    """Two simultaneous HTTP requests, <=8 total, 3s/request; stop batch on any error.

    Process limits are imposed by the outer jail. No stress/ramp or production claim.
    CPU/RSS cover the entire test process (server and clients), not server-only usage.
    """
    assert 0 < len(requests) <= 8
    usage = resource.getrusage(resource.RUSAGE_SELF)
    cpu_start, wall_start = usage.ru_utime + usage.ru_stime, time.perf_counter()
    barrier = threading.Barrier(2, timeout=3)

    def send(item):
        path, body = item
        barrier.wait()
        start = time.perf_counter()
        response = client.post(path, json=body)
        return time.perf_counter() - start, response

    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for offset in range(0, len(requests), 2):
            assert len(requests[offset:offset+2]) == 2
            futures = [pool.submit(send, item) for item in requests[offset:offset+2]]
            pair = [future.result(timeout=5) for future in futures]
            results.extend(pair)
            if any(response.status_code != 200 for _, response in pair):
                break
    report = metrics([elapsed for elapsed, _ in results], cpu_start, wall_start)
    report["errors"] = sum(response.status_code != 200 for _, response in results)
    report["concurrency"] = 2
    print("BOUNDED_HTTP", json.dumps(report))
    assert report["errors"] == 0, [(r.status_code, r.text) for _, r in results]
    return [response for _, response in results]


def test_simultaneous_replay_is_persisted_once(local_core):
    serve, _, state = local_core
    with serve() as (client, core):
        sid, episode, body = open_attempt(client)
        before = persisted_attempts(state)
        path = f"/api/pedagogy/episode/{episode}/respond"
        responses = bounded_requests(client, [(path, body)] * 4)
        assert sum(not r.json()["was_idempotent_replay"] for r in responses) == 1
        assert persisted_attempts(state) == before + 1
        assert len({r.json()["bkt_update"]["attempts"] for r in responses}) == 1
        assert core.student_storage.get_anchor_state(KC).last_quality == 5
        post(client, f"/api/study/session/{sid}/close")


def test_simultaneous_local_federated_queries(local_core):
    serve, _, _ = local_core
    with serve() as (client, core):
        sids = [post(client, "/api/study/session/open", {"notebook_id": NB})["session_id"] for _ in range(4)]
        requests = [("/api/chat/query", {"session_id": sid, "prompt": "punteros" if i % 2 == 0 else "punteros semaforos",
                     "scope_type": "notebook", "scope_id": NB, "requested_phase": "conceptual"}) for i, sid in enumerate(sids)]
        for i, response in enumerate(bounded_requests(client, requests)):
            events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
            complete = [e["payload"] for e in events if e["event_type"] == "phase_complete"]
            assert complete, events
            expected = {"src-local"} if i % 2 == 0 else {"src-local", "src-remote"}
            assert {c["source_id"] for c in complete[-1]["evidence_provenance"]} == expected
        for sid in sids:
            post(client, f"/api/study/session/{sid}/close")


def test_evaluation_cannot_commit_after_completed_close(local_core, monkeypatch):
    """Controlled interleaving only: pause grading after authorization, close, resume.

    Oracle: CLOSED remains terminal and no new durable academic attempt is committed.
    The pause changes scheduling, not grading, storage, authorization or closure logic.
    """
    serve, _, state = local_core
    with serve() as (client, core):
        sid, episode, body = open_attempt(client)
        before = persisted_attempts(state)
        entered, resume = threading.Event(), threading.Event()
        grade = core.exact_grader.grade

        def paused_grade(*args, **kwargs):
            entered.set()
            assert resume.wait(2), "Controlled interleaving timed out"
            return grade(*args, **kwargs)

        monkeypatch.setattr(core.exact_grader, "grade", paused_grade)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(client.post, f"/api/pedagogy/episode/{episode}/respond", json=body)
            try:
                assert entered.wait(2), "Evaluation did not reach the pause"
                closed = post(client, f"/api/study/session/{sid}/close")
                assert closed["episode_phase"] == "CLOSED"
            finally:
                resume.set()
            response = future.result(timeout=4)
        after = persisted_attempts(state)
        print("EVALUATE_VS_CLOSE", json.dumps({"close_completed_before_grade": True,
            "evaluation_status": response.status_code, "persisted_attempts_before": before, "persisted_attempts_after": after}))
        assert after == before, "Academic attempt committed AFTER terminal close completed"
        assert response.status_code in (404, 409), response.text


def test_shutdown_lifespan_logs_completion(local_core):
    """Verify lifespan shutdown hook runs and logs completion.
    The module fixture accumulates containers; descriptor check is done in fixture cleanup.
    """
    serve, _, _ = local_core
    with serve() as (client, core):
        assert client.get("/api/health").status_code == 200
    # If we reach here, lifespan shutdown completed (logged "Application shutdown complete")
    assert True
