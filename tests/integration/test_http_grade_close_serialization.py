"""Real loopback HTTP + independent SQLite stores; synthetic grading only.

Scheduling hooks observe actual transactions/commits, never add closure checks.
No models, corpus, full AppContainer startup, production state or gate claims.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
import socket
import sqlite3
import threading
import time
from types import SimpleNamespace

from fastapi import FastAPI, Request
import httpx
import pytest
import uvicorn

from study_engine.federation.notebook_registry import Notebook, NotebookRegistry
from study_engine.pedagogy.bridge import ObservationBridge
from study_engine.pedagogy.exercise_contracts import ExerciseCandidate, ExerciseType, ExerciseVerificationStatus
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
from study_engine.session.session_store import SessionStore
from study_engine.session.study_session_orchestrator import StudySessionOrchestrator
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage
from study_engine.web.dependencies import get_container
from study_engine.web.routes import pedagogy, study_session


NB, KC, SID = "synthetic-race", "synthetic-numeric", "synthetic-session"


def academic_state(root):
    with sqlite3.connect(f"file:{root / 'student_state.db'}?mode=ro", uri=True) as conn:
        return {table: conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                for table in ("bkt_states", "anchor_states", "student_operation_receipts",
                              "student_exercise_attempts", "student_hints")}


def persisted_session(root):
    with sqlite3.connect(f"file:{root / 'sessions.db'}?mode=ro", uri=True) as conn:
        phase, closed = conn.execute(
            "SELECT episode_phase, is_closed FROM study_sessions WHERE session_id=?", (SID,),
        ).fetchone()
        assert (phase == "CLOSED") == bool(closed)
        return phase


@pytest.fixture
def http_race(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({NB: {"kcs": [{"kc_id": KC, "title": "Synthetic", "unit": 1, "prerequisites": []}]}}))
    registry = NotebookRegistry(initial_notebooks=[Notebook(
        notebook_id=NB, name="Synthetic", subject="Synthetic", sources=[],
    )])
    exercises = ExerciseStore(tmp_path / "exercises.json")
    prompt = "Synthetic: siete por seis"
    exercises.add_exercise(ExerciseCandidate(
        exercise_id="synthetic-exercise", kc_id=KC, prompt=prompt,
        exercise_type=ExerciseType.NUMERIC, expected_answer="42",
        source_id="synthetic-source", source_location="synthetic page 1",
        source_hash=hashlib.sha256(prompt.encode()).hexdigest(),
        content_hash=hashlib.sha256(prompt.encode()).hexdigest(),
        extractor_version="synthetic", extraction_method="TEST_FIXTURE",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE, verified_by="synthetic-owner",
        verification_timestamp=None,
    ))

    def make_worker():
        storage = StudentStorage(tmp_path / "student_state.db")
        sessions = SessionStore(tmp_path / "sessions.db")
        tracker = BKTTracker(storage)
        orch = PedagogicalOrchestrator(
            registry, None, None, None, exercises, tracker, catalog_path=catalog, episode_store=sessions,
        )
        session = StudySessionOrchestrator(registry, orch, storage, session_store=sessions)
        return SimpleNamespace(
            student_storage=storage, bkt_tracker=tracker, observation_bridge=ObservationBridge(tracker),
            study_session_orchestrator=session, pedagogical_orchestrator=orch,
            exercise_store=exercises, exact_grader=ExactMatchGrader(), mc_grader=MultiChoiceGrader(),
        )

    first = make_worker()
    session = first.study_session_orchestrator
    session.open_session(NB, session_id=SID)
    episode, _ = first.pedagogical_orchestrator.start_episode(NB, KC, SID)
    intervention = first.pedagogical_orchestrator.get_next_intervention(episode.episode_id)
    actions = ("SUBMIT_ANSWER", "REQUEST_HINT", "START_NEXT_KC")
    state = replace(session._sessions[SID], episode_id=episode.episode_id, episode_phase="EVALUATING",
                    available_actions=actions)
    state = replace(state, state_hash=state.compute_hash(SID, NB, state.student_id, KC, episode.episode_id, "EVALUATING", actions))
    session.session_store.upsert(session._serialize_state(state))
    session._sessions[SID] = state
    workers = [first, make_worker()]
    assert workers[0].student_storage is not workers[1].student_storage
    assert workers[0].study_session_orchestrator._state_lock is not workers[1].study_session_orchestrator._state_lock
    app = FastAPI()
    app.include_router(pedagogy.router)
    app.include_router(study_session.router)

    def container(request: Request):
        return workers[int(request.headers.get("x-worker", "0"))]

    app.dependency_overrides[get_container] = container
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False, lifespan="off"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started
    with httpx.Client(base_url=f"http://127.0.0.1:{sock.getsockname()[1]}", timeout=8, trust_env=False) as client:
        env = SimpleNamespace(
            client=client, workers=workers, root=tmp_path,
            grade_path=f"/api/pedagogy/episode/{episode.episode_id}/respond",
            close_path=f"/api/study/session/{SID}/close",
            body={"session_id": SID, "step_id": intervention["step_id"], "response_text": "42"},
        )
        try:
            yield env
        finally:
            server.should_exit = True
            thread.join(5)
            sock.close()
            assert not thread.is_alive()
            for worker in workers:
                worker.student_storage.close()
                worker.study_session_orchestrator.session_store.close()


def grade(env, worker=0, **body):
    return env.client.post(env.grade_path, json={**env.body, **body}, headers={"x-worker": str(worker)})


def close(env, worker=1):
    return env.client.post(env.close_path, headers={"x-worker": str(worker)})


def assert_one_observation(env):
    data = academic_state(env.root)
    assert len(data["bkt_states"]) == 1 and data["bkt_states"][0][5] == 1
    assert data["bkt_states"][0][1] > env.workers[0].bkt_tracker.params["p_L0"]
    assert len(data["anchor_states"]) == 1 and data["anchor_states"][0][2] == 1
    assert data["anchor_states"][0][5] == 5
    receipts = data["student_operation_receipts"]
    assert len(receipts) == 2
    assert sum(row[3] == env.body["step_id"] for row in receipts) == 1
    return data


def test_close_cannot_commit_between_open_read_and_grade_commit(http_race, monkeypatch):
    env = http_race
    evaluator, closer = env.workers
    opened, resume, close_progress = threading.Event(), threading.Event(), threading.Event()
    commits = []
    load = evaluator.study_session_orchestrator.session_store.load_session

    def pause_after_open(session_id):
        row = load(session_id)
        if getattr(evaluator.student_storage._thread_local, "transaction_depth", 0) and not opened.is_set():
            assert row["episode_phase"] == "EVALUATING"
            opened.set()
            assert resume.wait(5)
        return row

    transaction = evaluator.student_storage.transaction

    @contextmanager
    def record_grade_commit():
        outer = not getattr(evaluator.student_storage._thread_local, "transaction_depth", 0)
        with transaction() as conn:
            yield conn
        if outer:
            assert_one_observation(env)
            commits.append("grade")

    upsert = closer.study_session_orchestrator.session_store.upsert

    def record_close_commit(state):
        upsert(state)
        if state["episode_phase"] == "CLOSED":
            assert persisted_session(env.root) == "CLOSED"
            commits.append("close")
            close_progress.set()

    get_connection = closer.student_storage._get_connection

    def trace_close_lock():
        conn = get_connection()
        conn.set_trace_callback(lambda sql: close_progress.set() if sql == "BEGIN IMMEDIATE" else None)
        return conn

    monkeypatch.setattr(evaluator.study_session_orchestrator.session_store, "load_session", pause_after_open)
    monkeypatch.setattr(evaluator.student_storage, "transaction", record_grade_commit)
    monkeypatch.setattr(closer.study_session_orchestrator.session_store, "upsert", record_close_commit)
    monkeypatch.setattr(closer.student_storage, "_get_connection", trace_close_lock)
    with ThreadPoolExecutor(max_workers=2) as pool:
        evaluating = pool.submit(grade, env)
        try:
            assert opened.wait(3)
            closing = pool.submit(close, env)
            assert close_progress.wait(3)
            phase_while_suspended = persisted_session(env.root)
        finally:
            resume.set()
        graded, closed = evaluating.result(6), closing.result(6)
    print("CRITICAL_INTERLEAVING", {"phase_after_open_before_resume": phase_while_suspended,
          "commits": commits, "grade_http": graded.status_code, "close_http": closed.status_code,
          "academic": academic_state(env.root)})
    assert graded.status_code == closed.status_code == 200
    assert phase_while_suspended != "CLOSED"
    assert commits == ["grade", "close"]
    before = assert_one_observation(env)
    assert grade(env).status_code in (404, 409)
    assert academic_state(env.root) == before
