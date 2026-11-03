"""A5 regression: session phase, actions, authorization and hash stay coherent.

Synthetic in-memory SQLite only: no tmp_path, no file reopen, no app startup,
no providers, no corpus. Rehydration uses an explicit SQLite serialize/
deserialize image held by the harness; durable file reopen is NOT exercised
here because external temporary storage is not authorized in this environment.

Doubles: notebook registry subset, concept generation bypass (S4.4/NLI is out
of A5 scope) and an injected :memory: connection for SessionStore. Everything
else (orchestrators, transitions, store methods, routes) is real.
"""

import json
import sqlite3
import threading
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
from study_engine.session.session_store import SessionStore
from study_engine.session.study_session_contracts import (
    ActionNotAvailableError,
    AuthoritativeSessionState,
    CurriculumPosition,
    OpeningBriefFacts,
    PolicyDeniedError,
)
from study_engine.session.study_session_orchestrator import StudySessionOrchestrator
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage
from study_engine.web.routes.pedagogy import get_next_intervention
from tests.unit.pedagogy.test_t06_persistent_idempotency import _exercise

NB = "a5-synthetic-notebook"
KC = "a5-synthetic-kc"
SID = "a5-synthetic-session"
EP = "ep_a5-synthetic-session_a5-synthetic-kc"
EXPLAINING_ACTIONS = ("REQUEST_DIALOGUE", "SKIP_TO_EXERCISE", "REQUEST_EXAMPLE")
EVALUATING_ACTIONS = ("SUBMIT_ANSWER", "REQUEST_HINT")


def _memory_store(image=None):
    """SessionStore over an injected :memory: connection (schema and methods real)."""
    store = SessionStore.__new__(SessionStore)
    store._lock = threading.Lock()
    store._thread_local = threading.local()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    if image is not None:
        conn.deserialize(image)
    store._thread_local.conn = conn
    store._init_db()
    return store


def _circuit(store, student):
    notebook = SimpleNamespace(
        notebook_id=NB, name="A5 synthetic notebook", subject="Synthetic", level="test",
    )
    registry = SimpleNamespace(
        get_notebook=lambda n: notebook if n == NB else None,
        validate_notebook_scope=lambda n: n == NB,
        get_sources_for_notebook=lambda n: [],
    )
    exercise = replace(_exercise(), exercise_id="a5-synthetic-exercise", kc_id=KC)
    exercises = ExerciseStore.__new__(ExerciseStore)
    exercises._exercises = {}
    exercises.add_exercise(exercise, persist=False)
    tracker = BKTTracker(student)
    ped = PedagogicalOrchestrator.__new__(PedagogicalOrchestrator)
    ped.notebook_registry = registry
    ped._kc_catalog = {NB: {"kcs": [{"kc_id": KC, "title": "A5 synthetic KC", "prerequisites": [], "unit": 1}]}}
    ped._active_episodes = {}
    ped.episode_store = store
    ped.exercise_store = exercises
    ped.bkt_tracker = tracker
    # shortcut: S4.4 concept generation is not part of the A5 property under test.
    ped.explain_concept = lambda episode_id: None
    sessions = StudySessionOrchestrator(
        registry, ped, student_storage=student, session_store=store,
    )
    return SimpleNamespace(
        store=store, student=student, tracker=tracker, registry=registry,
        ped=ped, sessions=sessions, exercise=exercise,
    )


@pytest.fixture
def circuit():
    store = _memory_store()
    student = StudentStorage(":memory:")
    with patch(
        "study_engine.session.study_session_orchestrator.get_student_context",
        return_value=None,
    ):
        context = _circuit(store, student)
        try:
            yield context
        finally:
            store.close()
            student.close()


def _container(circuit):
    return SimpleNamespace(
        study_session_orchestrator=circuit.sessions,
        pedagogical_orchestrator=circuit.ped,
    )


def _assert_coherent(sessions, snap):
    """Published phase, actions, authorization and hash come from one state."""
    state = sessions._sessions[snap.session_id]
    assert snap.episode_phase == state.episode_phase
    assert tuple(snap.available_actions) == tuple(state.available_actions)
    for action in snap.available_actions:
        assert sessions._action_allowed_for_phase(action, snap.episode_phase), action
    expected = AuthoritativeSessionState.compute_hash(
        snap.session_id, snap.notebook_id, snap.student_id,
        snap.current_kc_id, snap.episode_id, snap.episode_phase,
        snap.available_actions,
    )
    assert snap.session_state_hash == expected == state.state_hash


def _session_blob(store, session_id):
    row = store._get_conn().execute(
        "SELECT state_blob FROM study_sessions WHERE session_id = ?", (session_id,),
    ).fetchone()
    return json.loads(row[0])


def _bkt_rows(circuit):
    return circuit.student._get_connection().execute(
        "SELECT COUNT(*) FROM bkt_states"
    ).fetchone()[0]


def _open_and_explain(circuit):
    circuit.sessions.open_session(NB, CANONICAL_STUDENT_ID, SID)
    return circuit.sessions.execute_action(SID, "START_EXPLANATION")


def _run_next(circuit):
    return get_next_intervention(EP, _container(circuit))


def test_r1_open_session_publishes_a_coherent_opening_brief(circuit):
    snap = circuit.sessions.open_session(NB, CANONICAL_STUDENT_ID, SID)

    assert snap.episode_phase == "OPENING_BRIEF"
    assert snap.episode_id is None
    assert snap.current_kc_id == KC
    assert set(snap.available_actions) == {
        "START_EXPLANATION", "REVIEW_PREREQUISITE", "SELECT_DIFFERENT_KC",
    }
    _assert_coherent(circuit.sessions, snap)


def test_r2_start_explanation_publishes_a_coherent_explaining_state(circuit):
    snap = _open_and_explain(circuit)

    assert snap.episode_phase == "EXPLAINING"
    assert snap.episode_id == EP
    assert tuple(snap.available_actions) == EXPLAINING_ACTIONS
    _assert_coherent(circuit.sessions, snap)
    episode = circuit.ped.get_episode(EP)
    assert episode.phase == EpisodePhase.EXPLAINING
    assert episode.session_id == SID
    assert _session_blob(circuit.store, SID)["episode_phase"] == "EXPLAINING"


def test_r3_next_intervention_no_longer_publishes_stale_actions(circuit):
    _open_and_explain(circuit)

    result = _run_next(circuit)

    assert result["intervention_type"] == "EXERCISE"
    assert result["restored"] is False
    snap = circuit.sessions.get_snapshot(SID)
    assert snap.episode_phase == "EVALUATING"
    assert tuple(snap.available_actions) == EVALUATING_ACTIONS
    assert "REQUEST_DIALOGUE" not in snap.available_actions
    assert snap.exercise_available is True
    _assert_coherent(circuit.sessions, snap)
    blob = _session_blob(circuit.store, SID)
    assert blob["episode_phase"] == "EVALUATING"
    assert tuple(blob["available_actions"]) == EVALUATING_ACTIONS


def test_r4_stale_dialogue_action_is_rejected_after_next(circuit):
    _open_and_explain(circuit)
    _run_next(circuit)

    with pytest.raises(ActionNotAvailableError):
        circuit.sessions.execute_action(SID, "REQUEST_DIALOGUE")

    snap = circuit.sessions.get_snapshot(SID)
    assert snap.episode_phase == "EVALUATING"
    _assert_coherent(circuit.sessions, snap)
    assert _bkt_rows(circuit) == 0


def test_r4b_skip_to_exercise_action_path_stays_coherent(circuit):
    _open_and_explain(circuit)

    snap = circuit.sessions.execute_action(SID, "SKIP_TO_EXERCISE")

    assert snap.episode_phase == "EVALUATING"
    assert tuple(snap.available_actions) == EVALUATING_ACTIONS
    assert circuit.ped.get_episode(EP).phase == EpisodePhase.EVALUATING
    _assert_coherent(circuit.sessions, snap)


def test_r5_rehydration_from_memory_image_restores_a_coherent_state(circuit):
    _open_and_explain(circuit)
    _run_next(circuit)
    before = circuit.sessions.get_snapshot(SID)

    image = circuit.store._get_conn().serialize()
    circuit.store.close()
    restored_store = _memory_store(image)
    restored = _circuit(restored_store, circuit.student)

    snap = restored.sessions.get_snapshot(SID)
    assert (snap.session_id, snap.episode_id, snap.current_kc_id) == (
        before.session_id, before.episode_id, before.current_kc_id,
    )
    assert snap.episode_phase == before.episode_phase == "EVALUATING"
    assert tuple(snap.available_actions) == tuple(before.available_actions)
    assert snap.session_state_hash == before.session_state_hash
    episode = restored.ped.get_episode(EP)
    assert episode.current_step_id == f"step_eval_{circuit.exercise.exercise_id}"
    _assert_coherent(restored.sessions, snap)
    restored_store.close()


def test_r6_next_replay_does_not_select_another_exercise_or_transition(circuit):
    _open_and_explain(circuit)
    first = _run_next(circuit)

    second = _run_next(circuit)

    assert second["restored"] is True
    assert second["step_id"] == first["step_id"]
    assert second["exercise"]["exercise_id"] == first["exercise"]["exercise_id"]
    episodes = circuit.store._get_conn().execute(
        "SELECT COUNT(*) FROM study_episodes WHERE episode_id = ?", (EP,),
    ).fetchone()[0]
    assert episodes == 1
    snap_before = circuit.sessions.get_snapshot(SID)
    snap_after = circuit.sessions.get_snapshot(SID)
    assert snap_after.session_state_hash == snap_before.session_state_hash
    _assert_coherent(circuit.sessions, snap_after)


def test_r7_session_persistence_failure_does_not_publish_incoherent_success(circuit, monkeypatch):
    _open_and_explain(circuit)
    real_upsert = circuit.store.upsert

    def failing_upsert(state_dict):
        if tuple(state_dict.get("available_actions", ())) == EVALUATING_ACTIONS:
            raise RuntimeError("synthetic session persistence failure")
        return real_upsert(state_dict)

    monkeypatch.setattr(circuit.store, "upsert", failing_upsert)
    with pytest.raises(RuntimeError, match="synthetic session persistence failure"):
        _run_next(circuit)

    # Intermediate divergence: the episode advanced, the session row did not.
    assert circuit.ped.get_episode(EP).phase == EpisodePhase.EVALUATING
    blob = _session_blob(circuit.store, SID)
    assert blob["episode_phase"] == "EXPLAINING"
    assert tuple(blob["available_actions"]) == EXPLAINING_ACTIONS

    monkeypatch.undo()
    retried = _run_next(circuit)
    assert retried["restored"] is True
    assert retried["step_id"] == f"step_eval_{circuit.exercise.exercise_id}"
    snap = circuit.sessions.get_snapshot(SID)
    _assert_coherent(circuit.sessions, snap)
    assert snap.episode_phase == "EVALUATING"
    assert tuple(snap.available_actions) == EVALUATING_ACTIONS
    assert _bkt_rows(circuit) == 0


def _legacy_session(store, phase, actions, episode_id):
    position = CurriculumPosition(
        unit_or_module="unit-1", unit_name="synthetic unit",
        kcs_in_unit=(KC,), kcs_completed=(), kcs_in_progress=(), kcs_pending=(KC,),
    )
    facts = OpeningBriefFacts(
        notebook_id=NB, notebook_name="A5 synthetic notebook",
        notebook_purpose="synthetic", curriculum_position=position,
        eligible_kcs=(KC,), selected_kc=KC, selected_kc_rationale="synthetic",
        bkt_estimate=0.0, bkt_note="synthetic", student_context=None,
        student_context_note="synthetic", proposed_action="START_FOUNDATIONS",
        proposed_action_rationale="synthetic",
    )
    state = AuthoritativeSessionState(
        session_id=SID, notebook_id=NB, student_id=CANONICAL_STUDENT_ID,
        created_at=datetime.now(timezone.utc), curriculum_id=f"curr-{NB}",
        current_kc_id=KC, episode_id=episode_id, episode_phase=phase,
        available_actions=actions, bkt_state_ref=KC, student_context_ref=None,
        opening_brief_facts=facts, opening_brief_narrative=None,
        state_hash=AuthoritativeSessionState.compute_hash(
            SID, NB, CANONICAL_STUDENT_ID, KC, episode_id, phase, actions,
        ),
    )
    store.upsert(StudySessionOrchestrator._serialize_state(None, state))
    return state


def test_r9a_legacy_divergent_bound_state_is_reconciled_coherently(circuit):
    stale = _legacy_session(circuit.store, "EXPLAINING", EXPLAINING_ACTIONS, EP)
    circuit.store.save_episode(Episode(
        episode_id=EP, notebook_id=NB, kc_id=KC, objective="A5 synthetic objective",
        phase=EpisodePhase.EVALUATING,
        current_step_id=f"step_eval_{circuit.exercise.exercise_id}",
        created_at=datetime.now(timezone.utc), session_id=SID,
    ))

    # A fresh orchestrator rehydrates the historical divergent rows, as after a restart.
    sessions = StudySessionOrchestrator(
        circuit.registry, circuit.ped, student_storage=circuit.student,
        session_store=circuit.store,
    )
    snap = sessions.get_snapshot(SID)

    assert snap.episode_phase == "EVALUATING"
    assert tuple(snap.available_actions) == EVALUATING_ACTIONS
    assert snap.session_state_hash != stale.state_hash
    _assert_coherent(sessions, snap)
    blob = _session_blob(circuit.store, SID)
    assert blob["episode_phase"] == "EVALUATING"
    assert tuple(blob["available_actions"]) == EVALUATING_ACTIONS


def test_r9b_legacy_divergent_unbound_episode_fails_closed_without_mutation(circuit):
    stale = _legacy_session(circuit.store, "EXPLAINING", EXPLAINING_ACTIONS, EP)
    circuit.store.save_episode(Episode(
        episode_id=EP, notebook_id=NB, kc_id=KC, objective="A5 synthetic objective",
        phase=EpisodePhase.EVALUATING,
        current_step_id=f"step_eval_{circuit.exercise.exercise_id}",
        created_at=datetime.now(timezone.utc), session_id=None,
    ))
    sessions = StudySessionOrchestrator(
        circuit.registry, circuit.ped, student_storage=circuit.student,
        session_store=circuit.store,
    )

    with pytest.raises(PolicyDeniedError):
        sessions.get_snapshot(SID)

    blob = _session_blob(circuit.store, SID)
    assert blob["episode_phase"] == "EXPLAINING"
    assert blob["state_hash"] == stale.state_hash
    assert circuit.store.load_episode(EP).phase == EpisodePhase.EVALUATING
    assert sessions._sessions[SID].episode_phase == "EXPLAINING"
