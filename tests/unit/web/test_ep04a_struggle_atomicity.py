"""EP-04A: only committed certified attempts contribute scoped difficulties.

Synthetic SQLite, exact graders and route functions are real; only receipt
completion fails on demand. No provider, production state or ledger is used.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Event
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.pedagogy.exercise_service import StruggleTracker
from study_engine.pedagogy.session_digest import _conn
from study_engine.web.routes.chat import ExerciseEvaluateRequest, evaluate_exercise_answer
from tests.unit.pedagogy.test_t06_persistent_idempotency import _container, _exercise

SESSION = "session-synthetic-1"
NOTEBOOK = "notebook-synthetic-1"
KC = "kc-synthetic-1"


def container_at(path):
    c = _container(path)
    exercise = _exercise()
    c.exercise_store.get_exercise_by_id = lambda eid: exercise if eid == exercise.exercise_id else None
    c.struggle_tracker = StruggleTracker()
    c.generated_registry = None
    c.study_session_orchestrator.get_snapshot = lambda sid: SimpleNamespace(
        session_id=sid, notebook_id=NOTEBOOK, student_id=CANONICAL_STUDENT_ID,
        episode_id="episode-synthetic-1",
    )
    _conn(c.student_storage)
    return c


def request(attempt, answer="wrong", session=SESSION):
    return ExerciseEvaluateRequest(
        exercise_id="exercise-synthetic-1", user_answer=answer,
        session_id=session, attempt_id=attempt,
    )


def evaluate(c, req):
    return asyncio.run(evaluate_exercise_answer(req, c))


def difficulty(c, *, student=CANONICAL_STUDENT_ID, session=SESSION, notebook=NOTEBOOK):
    return c.struggle_tracker.confirmed_state(
        c.student_storage, student_id=student, session_id=session, notebook_id=notebook,
    )


def snapshot(c):
    conn = c.student_storage._get_connection()
    return {
        "bkt": conn.execute("SELECT * FROM bkt_states ORDER BY kc_id").fetchall(),
        "activity": conn.execute("SELECT * FROM session_kc_activity").fetchall(),
        "digest": conn.execute("SELECT * FROM session_digests").fetchall(),
        "difficulty": difficulty(c),
    }


@pytest.mark.parametrize("after_receipt_write", [False, True])
def test_rollback_has_no_academic_effects_and_in_progress_is_not_completed(tmp_path, after_receipt_write):
    c = container_at(tmp_path / "state.db")
    before = snapshot(c)
    req = request("failed")
    complete = c.student_storage.complete_operation_receipt

    def fail_completion(**kwargs):
        if after_receipt_write:
            complete(**kwargs)
        raise RuntimeError("injected")

    with patch.object(c.student_storage, "complete_operation_receipt", fail_completion):
        with pytest.raises(RuntimeError, match="injected"):
            evaluate(c, req)
    assert snapshot(c) == before
    receipt = c.student_storage.get_operation_receipt(
        session_id=SESSION, episode_id="chat-exercise-evaluation",
        exercise_id=req.exercise_id, attempt_id=req.attempt_id,
    )
    assert receipt is not None and receipt[1] == ""
    with pytest.raises(HTTPException) as error:
        evaluate(c, req)
    assert error.value.status_code == 409
    assert snapshot(c) == before
    c.student_storage.close()


def test_commits_replay_conflict_and_success_reset(tmp_path):
    c = container_at(tmp_path / "state.db")
    for i in range(3):
        result = evaluate(c, request(f"failure-{i}"))
        assert result["struggle_consecutive_failures"] == i + 1
        assert result["struggle_mode"] is (i == 2)
        assert "_struggle_state" not in result
    state = difficulty(c)
    assert c.struggle_tracker.is_struggling(KC, state=state)
    assert c.struggle_tracker.directive(KC, state=state)
    before = snapshot(c)
    replay = evaluate(c, request("failure-2"))
    assert replay["was_idempotent_replay"] and "_struggle_state" not in replay
    assert snapshot(c) == before
    with pytest.raises(HTTPException) as error:
        evaluate(c, request("failure-2", answer="different"))
    assert error.value.status_code == 409
    assert snapshot(c) == before
    result = evaluate(c, request("success", answer="synthetic-answer"))
    assert result["struggle_consecutive_failures"] == 0
    assert not result["struggle_mode"]
    assert c.bkt_tracker.get_state(KC).attempts == 4
    conn = c.student_storage._get_connection()
    assert conn.execute("SELECT attempts FROM session_kc_activity").fetchone()[0] == 4
    assert len(conn.execute("SELECT * FROM session_digests").fetchall()) == 1
    c.student_storage.close()


def test_restart_reconstructs_only_confirmed_difficulties(tmp_path):
    path = tmp_path / "state.db"
    c = container_at(path)
    evaluate(c, request("confirmed"))
    with patch.object(c.student_storage, "complete_operation_receipt", side_effect=RuntimeError("injected")):
        with pytest.raises(RuntimeError):
            evaluate(c, request("reverted"))
    before = snapshot(c)
    c.student_storage.close()
    reopened = container_at(path)
    assert snapshot(reopened) == before
    assert difficulty(reopened)["consecutive_failures"] == 1
    assert evaluate(reopened, request("confirmed"))["was_idempotent_replay"]
    assert snapshot(reopened) == before
    reopened.student_storage.close()


def test_concurrent_failure_and_commit_keep_only_legitimate_effects(tmp_path):
    path = tmp_path / "state.db"
    failing = container_at(path)
    succeeding = container_at(path)
    reached_completion = Event()
    release_failure = Event()
    success_started = Event()

    def fail_completion(**kwargs):
        reached_completion.set()
        assert release_failure.wait(5)
        raise RuntimeError("injected concurrent failure")

    def failed_request():
        try:
            with pytest.raises(RuntimeError, match="injected concurrent failure"):
                evaluate(failing, request("failed"))
        finally:
            failing.student_storage.close()

    def successful_request():
        success_started.set()
        try:
            return evaluate(succeeding, request("confirmed"))
        finally:
            succeeding.student_storage.close()

    with patch.object(failing.student_storage, "complete_operation_receipt", fail_completion):
        with ThreadPoolExecutor(max_workers=2) as pool:
            failed = pool.submit(failed_request)
            try:
                assert reached_completion.wait(5)
                success = pool.submit(successful_request)
                assert success_started.wait(5)
            finally:
                release_failure.set()
            failed.result(timeout=10)
            result = success.result(timeout=10)
    assert result["struggle_consecutive_failures"] == 1
    assert difficulty(succeeding)["consecutive_failures"] == 1
    assert succeeding.bkt_tracker.get_state(KC).attempts == 1
    assert succeeding.student_storage._get_connection().execute(
        "SELECT attempts FROM session_kc_activity"
    ).fetchone()[0] == 1
    failing.student_storage.close()
    succeeding.student_storage.close()


def test_two_concurrent_commits_do_not_lose_updates(tmp_path):
    path = tmp_path / "state.db"
    first, second = container_at(path), container_at(path)
    start = Barrier(2)

    def commit(c, attempt):
        try:
            start.wait(timeout=5)
            return evaluate(c, request(attempt))["struggle_consecutive_failures"]
        finally:
            c.student_storage.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(commit, first, "first")
        b = pool.submit(commit, second, "second")
        assert sorted([a.result(timeout=10), b.result(timeout=10)]) == [1, 2]
    assert difficulty(first)["consecutive_failures"] == 2
    assert difficulty(first)["revision"] == 2
    assert first.bkt_tracker.get_state(KC).attempts == 2
    first.student_storage.close()
    second.student_storage.close()


def test_student_session_notebook_and_kc_isolation(tmp_path):
    c = container_at(tmp_path / "state.db")
    for i in range(3):
        evaluate(c, request(f"confirmed-{i}"))
    state = difficulty(c)
    assert c.struggle_tracker.is_struggling(KC, state=state)
    assert not c.struggle_tracker.is_struggling("other-kc", state=state)
    for scope in ({"student": "other-student"}, {"session": "other-session"}, {"notebook": "other-notebook"}):
        assert difficulty(c, **scope)["consecutive_failures"] == 0
    # A legitimate attempt in a different session cannot reset this session.
    evaluate(c, request("other-session-success", answer="synthetic-answer", session="other-session"))
    assert difficulty(c) == state
    # A confirmed KC switch keeps the existing focus-reset rule in this session.
    other = replace(_exercise(), exercise_id="other-exercise", kc_id="other-kc")
    c.exercise_store.get_exercise_by_id = lambda eid: other
    c.exercise_store.get_evaluable_exercise_by_id = lambda eid: other
    c.pedagogical_orchestrator._kc_catalog[NOTEBOOK]["kcs"].append({"kc_id": "other-kc"})
    req = request("other-kc").model_copy(update={"exercise_id": other.exercise_id})
    assert evaluate(c, req)["struggle_consecutive_failures"] == 1
    assert not c.struggle_tracker.is_struggling(KC, state=difficulty(c))
    assert difficulty(c, session="other-session")["consecutive_failures"] == 0
    c.student_storage.close()


def test_legacy_unscoped_memory_cannot_contaminate_certified_attempts(tmp_path):
    c = container_at(tmp_path / "state.db")
    for _ in range(3):
        c.struggle_tracker.record(KC, False)
    assert c.struggle_tracker.is_struggling(KC)
    assert difficulty(c)["consecutive_failures"] == 0
    assert evaluate(c, request("confirmed"))["struggle_consecutive_failures"] == 1
    c.student_storage.close()


def test_foreign_student_session_cannot_mutate_certified_state(tmp_path):
    c = container_at(tmp_path / "state.db")
    c.study_session_orchestrator.get_snapshot = lambda sid: SimpleNamespace(
        session_id=sid, notebook_id=NOTEBOOK, student_id="other-student",
    )
    before = snapshot(c)
    assert evaluate(c, request("foreign"))["status"] == "UNGRADED"
    assert snapshot(c) == before
    c.student_storage.close()


def test_preview_requires_transaction_and_does_not_publish_state(tmp_path):
    c = container_at(tmp_path / "state.db")
    scope = dict(student_id=CANONICAL_STUDENT_ID, session_id=SESSION, notebook_id=NOTEBOOK)
    with pytest.raises(RuntimeError, match="transaction"):
        c.struggle_tracker.preview_certified(c.student_storage, kc_id=KC, correct=False, **scope)
    before = snapshot(c)
    with c.student_storage.transaction():
        pending = c.struggle_tracker.preview_certified(c.student_storage, kc_id=KC, correct=False, **scope)
        assert pending["consecutive_failures"] == 1
        assert difficulty(c)["consecutive_failures"] == 0
    assert snapshot(c) == before
    c.student_storage.close()


def test_completion_order_not_reservation_order_controls_focus(tmp_path):
    c = container_at(tmp_path / "state.db")
    original_begin = c.student_storage.begin_operation_receipt
    result = None

    def out_of_order_begin(**kwargs):
        nonlocal result
        reservation = original_begin(**kwargs)
        # Simulate the second reservation finishing before the first evaluation.
        if kwargs["attempt_id"] == "reserved-first":
            with patch.object(c.student_storage, "begin_operation_receipt", original_begin):
                def complete_other():
                    try:
                        return evaluate(c, request("completed-first"))
                    finally:
                        c.student_storage.close()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    result = pool.submit(complete_other).result(timeout=5)
        return reservation

    with patch.object(c.student_storage, "begin_operation_receipt", out_of_order_begin):
        evaluate(c, request("reserved-first"))
    assert result["struggle_consecutive_failures"] == 1
    assert difficulty(c)["consecutive_failures"] == 2
    assert difficulty(c)["revision"] == 2
    assert c.bkt_tracker.get_state(KC).attempts == 2
    c.student_storage.close()


def test_context_consumer_uses_confirmed_scoped_difficulties_after_restart(tmp_path):
    from study_engine.hierarchy.scope_resolver import ScopeType
    from study_engine.pedagogy.exercise_service import STRUGGLE_DIRECTIVE
    from study_engine.web.routes.chat import ChatQueryRequest, _global_default_contract, _prepare_chat_context

    path = tmp_path / "state.db"
    c = container_at(path)
    for i in range(3):
        evaluate(c, request(f"confirmed-{i}"))
    c.student_storage.close()
    c = container_at(path)
    scope = SimpleNamespace(scope_type=ScopeType.NOTEBOOK, scope_id=NOTEBOOK, notebook_id=NOTEBOOK)
    store = SimpleNamespace(get_pedagogical_contract=lambda nb: _global_default_contract())
    resolver = SimpleNamespace(resolve=lambda **kwargs: scope)
    pack = SimpleNamespace(
        formatted_context="synthetic evidence", abstained=False, is_sufficient=True,
        resolved_item=None, citations=[], chunks=[],
    )

    def directive_for(session):
        req = ChatQueryRequest(prompt=f"Explicame {KC}", notebook_id=NOTEBOOK, session_id=session)
        with patch("study_engine.web.routes.chat._assemble_epistemic_context", return_value=(pack, [SimpleNamespace(content="synthetic evidence")])):
            result = _prepare_chat_context(
                store=store, resolver=resolver, container=c, prompt_text=req.prompt,
                request=req, target_scope_type="notebook", target_scope_id=NOTEBOOK,
            )
        return result[6]

    assert STRUGGLE_DIRECTIVE in directive_for(SESSION)
    assert STRUGGLE_DIRECTIVE not in directive_for("other-session")
    c.student_storage.close()
