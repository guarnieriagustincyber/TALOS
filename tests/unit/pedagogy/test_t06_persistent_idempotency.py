"""Synthetic endpoint-level idempotency tests for BKT and SM-2 mutations."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
from study_engine.student.storage import StudentStorage
from study_engine.web.routes.chat import ExerciseEvaluateRequest, evaluate_exercise_answer
from study_engine.web.routes.dialogue import (
    SocraticEvaluationRequest,
    evaluate_socratic_response,
)


def _exercise() -> ExerciseCandidate:
    return ExerciseCandidate(
        exercise_id="exercise-synthetic-1",
        source_id="synthetic-source",
        source_location="synthetic://unit-test/page/1",
        source_hash="a" * 64,
        extractor_version="test-v1",
        extraction_method="synthetic-fixture",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE,
        verified_by="test-authority",
        verification_timestamp=datetime(2026, 10, 19, tzinfo=timezone.utc),
        content_hash="b" * 64,
        kc_id="kc-synthetic-1",
        prompt="Synthetic exact answer exercise",
        exercise_type=ExerciseType.EXACT_TEXT,
        expected_answer="synthetic-answer",
        solution_explanation="A synthetic conceptual clue that does not reveal the expected answer.",
    )


def _container(db_path: Path):
    storage = StudentStorage(db_path)
    episode = Episode(
        episode_id="episode-synthetic-1",
        session_id="session-synthetic-1",
        notebook_id="notebook-synthetic-1",
        kc_id="kc-synthetic-1",
        objective="Synthetic objective",
        phase=EpisodePhase.EVALUATING,
        current_step_id="step_eval_exercise-synthetic-1",
    )

    class _Pedagogy:
        _kc_catalog = {
            episode.notebook_id: {"kcs": [{"kc_id": episode.kc_id}]}
        }

        @staticmethod
        def get_episode(episode_id: str):
            return episode if episode_id == episode.episode_id else None

    class _Sessions:
        @staticmethod
        def get_snapshot(session_id: str):
            if session_id != episode.session_id:
                raise ValueError("unknown synthetic session")
            return SimpleNamespace(session_id=session_id, notebook_id=episode.notebook_id)

    class _ExerciseStore:
        @staticmethod
        def get_evaluable_exercise_by_id(exercise_id: str):
            return _exercise() if exercise_id == "exercise-synthetic-1" else None

    return SimpleNamespace(
        student_storage=storage,
        pedagogical_orchestrator=_Pedagogy(),
        study_session_orchestrator=_Sessions(),
        exercise_store=_ExerciseStore(),
        bkt_tracker=BKTTracker(storage),
        spaced_scheduler=SpacedRepetitionScheduler(storage),
        mc_grader=MultiChoiceGrader(),
        exact_grader=ExactMatchGrader(),
    )


def _request(attempt_id: str, answer: str = "synthetic-answer") -> SocraticEvaluationRequest:
    return SocraticEvaluationRequest(
        student_response=answer,
        exercise_id="exercise-synthetic-1",
        session_id="session-synthetic-1",
        attempt_id=attempt_id,
        kc_id="kc-synthetic-1",
    )


def test_same_operation_replays_after_sqlite_reopen_without_second_bkt_or_sm2(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "student-state.db"
    first_container = _container(db_path)
    first = evaluate_socratic_response("episode-synthetic-1", _request("attempt-1"), first_container)
    first_bkt = first_container.bkt_tracker.get_state("kc-synthetic-1")
    first_sm2 = first_container.spaced_scheduler.get_anchor_state("kc-synthetic-1")
    first_container.student_storage.close()

    reopened_container = _container(db_path)
    replay = evaluate_socratic_response("episode-synthetic-1", _request("attempt-1"), reopened_container)

    assert first["status"] == "EVALUATED"
    assert replay["status"] == "EVALUATED"
    assert replay["was_idempotent_replay"] is True
    assert replay["p_L"] == first["p_L"]
    assert reopened_container.bkt_tracker.get_state("kc-synthetic-1").attempts == first_bkt.attempts == 1
    assert reopened_container.spaced_scheduler.get_anchor_state("kc-synthetic-1") == first_sm2
    reopened_container.student_storage.close()


def test_reused_attempt_identity_with_different_answer_conflicts_without_mutation(
    tmp_path: Path,
) -> None:
    container = _container(tmp_path / "student-state.db")
    evaluate_socratic_response("episode-synthetic-1", _request("attempt-1"), container)
    before_bkt = container.bkt_tracker.get_state("kc-synthetic-1")
    before_sm2 = container.spaced_scheduler.get_anchor_state("kc-synthetic-1")

    with pytest.raises(HTTPException) as conflict:
        evaluate_socratic_response(
            "episode-synthetic-1",
            _request("attempt-1", answer="different-content"),
            container,
        )

    assert conflict.value.status_code == 409
    assert container.bkt_tracker.get_state("kc-synthetic-1") == before_bkt
    assert container.spaced_scheduler.get_anchor_state("kc-synthetic-1") == before_sm2
    container.student_storage.close()


def test_distinct_attempt_ids_are_independent_mutations(tmp_path: Path) -> None:
    container = _container(tmp_path / "student-state.db")
    first = evaluate_socratic_response("episode-synthetic-1", _request("attempt-1"), container)
    second = evaluate_socratic_response("episode-synthetic-1", _request("attempt-2"), container)

    assert first["attempts"] == 1
    assert second["attempts"] == 2
    assert second["was_idempotent_replay"] is False
    assert container.spaced_scheduler.get_anchor_state("kc-synthetic-1").repetitions == 2
    container.student_storage.close()


def test_failed_sm2_write_rolls_back_bkt_and_receipt(tmp_path: Path) -> None:
    container = _container(tmp_path / "student-state.db")

    def fail_sm2(**kwargs):
        raise RuntimeError("synthetic SM-2 failure")

    container.spaced_scheduler.record_review = fail_sm2
    with pytest.raises(RuntimeError, match="synthetic SM-2 failure"):
        evaluate_socratic_response("episode-synthetic-1", _request("attempt-rollback"), container)

    assert container.bkt_tracker.get_state("kc-synthetic-1").attempts == 0
    assert container.student_storage.get_operation_receipt(
        session_id="session-synthetic-1",
        episode_id="episode-synthetic-1",
        exercise_id="exercise-synthetic-1",
        attempt_id="attempt-rollback",
    ) is None
    container.student_storage.close()


def test_chat_exercise_evaluation_uses_durable_session_attempt_receipt(
    tmp_path: Path,
) -> None:
    exercise = _exercise()

    class _ExerciseStore:
        @staticmethod
        def get_exercise_by_id(exercise_id: str):
            return exercise if exercise_id == exercise.exercise_id else None

        @staticmethod
        def get_evaluable_exercise_by_id(exercise_id: str):
            return exercise if exercise_id == exercise.exercise_id else None

    class _Sessions:
        @staticmethod
        def get_snapshot(session_id: str):
            if session_id != "session-chat-synthetic":
                raise ValueError("unknown synthetic session")
            return SimpleNamespace(session_id=session_id, notebook_id="notebook-synthetic-1")

    class _Pedagogy:
        _kc_catalog = {
            "notebook-synthetic-1": {"kcs": [{"kc_id": exercise.kc_id}]}
        }

    db_path = tmp_path / "chat-student-state.db"

    def build_container():
        storage = StudentStorage(db_path)
        return SimpleNamespace(
            student_storage=storage,
            exercise_store=_ExerciseStore(),
            generated_registry=None,
            study_session_orchestrator=_Sessions(),
            pedagogical_orchestrator=_Pedagogy(),
            bkt_tracker=BKTTracker(storage),
            exact_grader=ExactMatchGrader(),
            mc_grader=MultiChoiceGrader(),
            struggle_tracker=None,
        )

    request = ExerciseEvaluateRequest(
        exercise_id=exercise.exercise_id,
        user_answer="synthetic-answer",
        session_id="session-chat-synthetic",
        attempt_id="attempt-chat-1",
    )
    first_container = build_container()
    first = asyncio.run(evaluate_exercise_answer(request, first_container))
    assert first["status"] == "GRADED"
    assert first_container.bkt_tracker.get_state(exercise.kc_id).attempts == 1
    first_container.student_storage.close()

    reopened = build_container()
    replay = asyncio.run(evaluate_exercise_answer(request, reopened))
    assert replay["was_idempotent_replay"] is True
    assert replay["p_L"] == first["p_L"]
    assert reopened.bkt_tracker.get_state(exercise.kc_id).attempts == 1

    conflicting = request.model_copy(update={"user_answer": "different-answer"})
    with pytest.raises(HTTPException) as conflict:
        asyncio.run(evaluate_exercise_answer(conflicting, reopened))
    assert conflict.value.status_code == 409
    assert reopened.bkt_tracker.get_state(exercise.kc_id).attempts == 1
    reopened.student_storage.close()
