"""Unit tests for StudentContext (consultive only) and ObservationBridge (idempotency).

INVARIANTS TESTED:
1. StudentContext does not mutate BKT.
2. ObservationBridge guarantees that the same (episode_id, step_id) yields at most 1 BKT update.
"""

from pathlib import Path

import pytest
from study_engine.pedagogy.bridge import ObservationBridge
from study_engine.pedagogy.graders import GradeResult
from study_engine.pedagogy.student_context import get_student_context
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage


def test_student_context_is_consultive_without_mastery_mutation() -> None:
    storage = StudentStorage(":memory:")
    bkt = BKTTracker(storage=storage)

    ctx = get_student_context("fase0-soc")
    assert ctx.notebook_id == "fase0-soc"
    assert "aritmetica_punteros" in ctx.topics_seen
    assert len(ctx.errors_recurring) >= 7

    # BKT must remain unaffected with default initial prior
    state = bkt.get_state("aritmetica_punteros")
    assert state.attempts == 0
    assert state.p_L == 0.1  # Initial default prior, zero false mastery


def test_observation_bridge_idempotency() -> None:
    storage = StudentStorage(":memory:")
    bkt = BKTTracker(storage=storage)
    bridge = ObservationBridge(bkt_tracker=bkt)

    grade_ok = GradeResult(
        is_correct=True,
        raw_answer="1012",
        normalized_answer="1012",
        normalization_policy="numeric",
        expected_answer="1012",
        comparison_result="MATCH",
        feedback="OK",
    )

    # First attempt: mutations applied
    state_1, was_new_1 = bridge.process_grade(
        session_id="session-test-01",
        episode_id="ep_test_01",
        step_id="step_01",
        exercise_id="exercise-test-01",
        kc_id="aritmetica_punteros",
        grade_result=grade_ok,
    )
    assert was_new_1 is True
    assert state_1.attempts == 1
    p_L_after_first = state_1.p_L
    assert p_L_after_first > 0.1

    # Duplicate attempt (same episode_id and step_id due to double click / network retry)
    state_2, was_new_2 = bridge.process_grade(
        session_id="session-test-01",
        episode_id="ep_test_01",
        step_id="step_01",
        exercise_id="exercise-test-01",
        kc_id="aritmetica_punteros",
        grade_result=grade_ok,
    )
    assert was_new_2 is False
    assert state_2.attempts == 1
    assert state_2.p_L == p_L_after_first  # No double increment!


def test_observation_bridge_receipt_survives_sqlite_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "student-state.db"
    first_storage = StudentStorage(db_path)
    first_bridge = ObservationBridge(BKTTracker(storage=first_storage))
    grade = GradeResult(
        is_correct=True,
        raw_answer="1012",
        normalized_answer="1012",
        normalization_policy="numeric",
        expected_answer="1012",
        comparison_result="MATCH",
        feedback="OK",
    )
    state_one, was_new_one = first_bridge.process_grade(
        session_id="session-persisted",
        episode_id="episode-persisted",
        step_id="step-persisted",
        exercise_id="exercise-persisted",
        kc_id="kc-persisted",
        grade_result=grade,
    )
    assert was_new_one is True
    first_storage.close()

    reopened_storage = StudentStorage(db_path)
    reopened_bridge = ObservationBridge(BKTTracker(storage=reopened_storage))
    state_two, was_new_two = reopened_bridge.process_grade(
        session_id="session-persisted",
        episode_id="episode-persisted",
        step_id="step-persisted",
        exercise_id="exercise-persisted",
        kc_id="kc-persisted",
        grade_result=grade,
    )

    assert was_new_two is False
    assert state_two.attempts == state_one.attempts == 1
    assert state_two.p_L == state_one.p_L
    reopened_storage.close()
