"""A1 regression: real graders/routes/BKT/receipts, synthetic SQLite :memory:.

Only session lookup is a behavioral-subset double; no HTTP, startup, provider,
production certification, disk persistence or restart behavior is exercised.
"""

import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.pedagogy.bridge import ObservationBridge
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.exercise_contracts import ExerciseVerificationStatus
from study_engine.pedagogy.exercise_service import StruggleTracker
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
from study_engine.pedagogy.observation_admissibility import admit_generated_observation
from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
from study_engine.pedagogy.session_digest import _conn
from study_engine.student.bkt_tracker import BKTTracker, load_bkt_params
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
from study_engine.student.storage import StudentStorage
from study_engine.web.routes.chat import ExerciseEvaluateRequest, evaluate_exercise_answer
from study_engine.web.routes.dialogue import SocraticEvaluationRequest, evaluate_socratic_response
from study_engine.web.routes.pedagogy import RespondEpisodeRequest, respond_intervention
from tests.unit.pedagogy.test_t06_persistent_idempotency import _exercise


@pytest.fixture
def academic_context():
    exercise = _exercise()
    storage = StudentStorage(":memory:")
    _conn(storage)
    tracker = BKTTracker(storage, default_params=load_bkt_params())
    # Bypass only disk-loading constructors; keep lookup, scope and grading real.
    store = ExerciseStore.__new__(ExerciseStore)
    store._exercises = {}
    store.add_exercise(exercise, persist=False)
    episode = Episode(
        episode_id="episode-synthetic-1", session_id="session-synthetic-1",
        notebook_id="notebook-synthetic-1", kc_id=exercise.kc_id,
        objective="Synthetic A1 regression", phase=EpisodePhase.EVALUATING,
        current_step_id=f"step_eval_{exercise.exercise_id}",
    )
    pedagogy = PedagogicalOrchestrator.__new__(PedagogicalOrchestrator)
    pedagogy._active_episodes = {episode.episode_id: episode}
    pedagogy.episode_store = None
    pedagogy._kc_catalog = {
        episode.notebook_id: {"kcs": [{"kc_id": exercise.kc_id, "prerequisites": []}]}
    }
    pedagogy.bkt_tracker = tracker

    def snapshot(session_id):
        if session_id != episode.session_id:
            raise ValueError("unknown synthetic session")
        return SimpleNamespace(
            session_id=session_id, notebook_id=episode.notebook_id,
            episode_id=episode.episode_id, student_id=CANONICAL_STUDENT_ID,
        )

    container = SimpleNamespace(
        student_storage=storage, bkt_tracker=tracker, exercise_store=store,
        pedagogical_orchestrator=pedagogy,
        study_session_orchestrator=SimpleNamespace(get_snapshot=snapshot),
        exact_grader=ExactMatchGrader(), mc_grader=MultiChoiceGrader(),
        spaced_scheduler=SpacedRepetitionScheduler(storage),
        observation_bridge=ObservationBridge(tracker),
        struggle_tracker=StruggleTracker(), generated_registry=None,
    )
    try:
        yield container, episode, exercise
    finally:
        storage.close()


def evaluate(route, context, answer, attempt="attempt-synthetic-a1", **changes):
    container, episode, exercise = context
    if route == "chat":
        request = ExerciseEvaluateRequest(
            exercise_id=exercise.exercise_id, user_answer=answer,
            notebook_id=episode.notebook_id, session_id=episode.session_id,
            episode_id=episode.episode_id, attempt_id=attempt,
        ).model_copy(update=changes)
        return asyncio.run(evaluate_exercise_answer(request, container))
    if route == "socratic":
        request = SocraticEvaluationRequest(
            student_response=answer, exercise_id=exercise.exercise_id,
            session_id=episode.session_id, attempt_id=attempt, kc_id=exercise.kc_id,
        ).model_copy(update=changes)
        return evaluate_socratic_response(episode.episode_id, request, container)
    request = RespondEpisodeRequest(
        session_id=episode.session_id, step_id=episode.current_step_id,
        response_text=answer,
    ).model_copy(update=changes)
    return respond_intervention(episode.episode_id, request, container)


def database_state(container):
    connection = container.student_storage._get_connection()
    return {
        table: connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
        for table in ("bkt_states", "student_operation_receipts", "session_kc_activity", "student_hints", "anchor_states")
    }


@pytest.mark.parametrize("route", ["chat", "socratic", "episode"])
@pytest.mark.parametrize(
    "key,answer,correct",
    [
        ("la pila crece hacia abajo", "LA PILA  crece hacia abajo", True),
        ("array", "arreglo", True),
        ("la pila crece hacia abajo", "la pila no crece hacia abajo", False),
        ("la memoria virtual permite aislar procesos", "la memoria virtual no permite aislar procesos", False),
        ("la operacion es valida si x es mayor que cero", "la operacion es valida si x es menor que cero", False),
    ],
)
def test_certified_route_only_records_admissible_correctness(academic_context, route, key, answer, correct):
    container, episode, exercise = academic_context
    container.exercise_store.add_exercise(replace(exercise, expected_answer=key), persist=False)
    prior = container.bkt_tracker.get_state(exercise.kc_id).p_L

    result = evaluate(route, academic_context, answer)

    assert result["is_correct"] is correct
    state = container.bkt_tracker.get_state(exercise.kc_id)
    assert state.attempts == 1
    # This configured strict policy allows an incorrect observation, not credit.
    assert state.p_L == pytest.approx(0.875 if correct else 0.011210762331838567)
    assert (state.p_L > prior) is correct
    storage = container.student_storage
    attempt = episode.current_step_id if route == "episode" else "attempt-synthetic-a1"
    receipt = storage.get_operation_receipt(
        session_id=episode.session_id, episode_id=episode.episode_id,
        exercise_id=exercise.exercise_id, attempt_id=attempt,
    )
    assert receipt is not None and receipt[1]
    returned_kc = result["bkt_update"]["kc_id"] if route == "episode" else result["kc_id"]
    assert returned_kc == exercise.kc_id
    if route == "chat":
        activity = storage._get_connection().execute(
            "SELECT attempts, errors, corrects FROM session_kc_activity WHERE session_id=? AND kc_id=?",
            (episode.session_id, exercise.kc_id),
        ).fetchone()
        assert activity == (1, int(not correct), int(correct))
    after = database_state(container)
    sm2 = storage.get_anchor_state(exercise.kc_id)
    replay = evaluate(route, academic_context, answer)
    assert replay["was_idempotent_replay"] is True
    assert database_state(container) == after
    assert storage.get_anchor_state(exercise.kc_id) == sm2
    with pytest.raises(HTTPException) as conflict:
        evaluate(route, academic_context, "different synthetic answer")
    assert conflict.value.status_code == 409
    assert database_state(container) == after


@pytest.mark.parametrize("route", ["chat", "socratic", "episode"])
def test_unverified_exercise_cannot_gain_credit(academic_context, route):
    container, _, exercise = academic_context
    container.exercise_store.add_exercise(
        replace(exercise, verification_status=ExerciseVerificationStatus.UNVERIFIED, verified_by=None),
        persist=False,
    )
    if route == "episode":
        with pytest.raises(HTTPException) as error:
            evaluate(route, academic_context, exercise.expected_answer)
        assert error.value.status_code == 400
    else:
        assert evaluate(route, academic_context, exercise.expected_answer)["status"] == "UNGRADED"
    assert container.student_storage._get_connection().execute("SELECT COUNT(*) FROM bkt_states").fetchone()[0] == 0
    assert container.student_storage._get_connection().execute("SELECT COUNT(*) FROM session_kc_activity").fetchone()[0] == 0


@pytest.mark.parametrize("route", ["chat", "socratic", "episode"])
def test_foreign_session_cannot_mutate_bkt(academic_context, route):
    container, _, exercise = academic_context
    if route == "episode":
        with pytest.raises(HTTPException) as error:
            evaluate(route, academic_context, exercise.expected_answer, session_id="session-synthetic-foreign")
        assert error.value.status_code == 409
    else:
        assert evaluate(route, academic_context, exercise.expected_answer, session_id="session-synthetic-foreign")["status"] == "UNGRADED"
    assert container.student_storage._get_connection().execute("SELECT COUNT(*) FROM bkt_states").fetchone()[0] == 0


@pytest.mark.parametrize("route", ["chat", "socratic", "episode"])
def test_receipt_failure_rolls_back_academic_writes(academic_context, route, monkeypatch):
    container, episode, exercise = academic_context
    container.exercise_store.add_exercise(
        replace(exercise, expected_answer="la pila crece hacia abajo"), persist=False,
    )
    initial = container.bkt_tracker.get_state(exercise.kc_id)
    container.bkt_tracker.save_state(initial)
    before = container.bkt_tracker.get_state(exercise.kc_id).model_dump()

    def fail_receipt(**kwargs):
        raise RuntimeError("synthetic receipt failure")

    method = "complete_operation_receipt" if route == "chat" else "store_operation_receipt"
    monkeypatch.setattr(container.student_storage, method, fail_receipt)
    with pytest.raises(RuntimeError, match="synthetic receipt failure"):
        evaluate(route, academic_context, "la pila no crece hacia abajo")
    assert container.bkt_tracker.get_state(exercise.kc_id).model_dump() == before
    assert container.student_storage._get_connection().execute("SELECT COUNT(*) FROM session_kc_activity").fetchone()[0] == 0
    receipts = container.student_storage._get_connection().execute("SELECT status FROM student_operation_receipts").fetchall()
    assert receipts == ([("IN_PROGRESS",)] if route == "chat" else [])


@pytest.mark.parametrize("kind", ["multi_kc", "debugging", "trace", "unknown"])
def test_inadmissible_generated_observations_stay_nonacademic(kind):
    assert admit_generated_observation(kind=kind, kc_ids=["kc-synthetic-1"]).academic_effects is False
