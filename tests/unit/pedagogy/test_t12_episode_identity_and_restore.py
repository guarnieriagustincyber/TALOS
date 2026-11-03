"""T12/T13b contracts exercised with synthetic objects and no app startup."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from study_engine.pedagogy.bridge import ObservationBridge
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage
from study_engine.web.routes.chat import ExerciseEvaluateRequest, evaluate_exercise_answer
from study_engine.web.routes.pedagogy import RespondEpisodeRequest, respond_intervention


def _exercise() -> ExerciseCandidate:
    return ExerciseCandidate(
        exercise_id="exercise-t12-certified",
        source_id="synthetic-source",
        source_location="synthetic page 1",
        source_hash="a" * 64,
        extractor_version="test",
        extraction_method="manual",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE,
        verified_by="synthetic-reviewer",
        verification_timestamp=None,
        content_hash="b" * 64,
        kc_id="kc-t12",
        prompt="Synthetic prompt",
        exercise_type=ExerciseType.NUMERIC,
        options=None,
        expected_answer="42",
    )


def _episode(*, phase=EpisodePhase.EVALUATING, step_id="step_eval_exercise-t12-certified"):
    return Episode(
        episode_id="episode-t12",
        notebook_id="notebook-t12",
        kc_id="kc-t12",
        objective="Synthetic objective",
        phase=phase,
        current_step_id=step_id,
        session_id="session-t12",
    )


def test_episode_evaluation_requires_the_persisted_session_identity(tmp_path):
    exercise = _exercise()
    storage = StudentStorage(tmp_path / "student-state.db")
    tracker = BKTTracker(storage)
    episode = _episode()
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(
            get_episode=lambda _episode_id: episode,
            get_next_eligible_action=lambda **_kwargs: {},
        ),
        study_session_orchestrator=SimpleNamespace(
            get_snapshot=lambda session_id: SimpleNamespace(
                session_id=session_id, notebook_id="notebook-t12"
            ),
        ),
        exercise_store=SimpleNamespace(get_evaluable_exercise_by_id=lambda _exercise_id: exercise),
        observation_bridge=ObservationBridge(tracker),
        exact_grader=ExactMatchGrader(),
        mc_grader=MultiChoiceGrader(),
    )

    with pytest.raises(HTTPException) as conflict:
        respond_intervention(
            "episode-t12",
            RespondEpisodeRequest(
                step_id=episode.current_step_id,
                response_text="42",
                session_id="different-session",
            ),
            container,
        )

    assert conflict.value.status_code == 409
    assert tracker.get_state("kc-t12").attempts == 0
    storage.close()


def test_episode_evaluation_rejects_a_session_pointing_to_another_active_episode(tmp_path):
    exercise = _exercise()
    storage = StudentStorage(tmp_path / "active-episode.db")
    tracker = BKTTracker(storage)
    episode = _episode()
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(get_episode=lambda _episode_id: episode),
        study_session_orchestrator=SimpleNamespace(
            get_snapshot=lambda session_id: SimpleNamespace(
                session_id=session_id,
                notebook_id="notebook-t12",
                episode_id="different-active-episode",
            ),
        ),
    )
    with pytest.raises(HTTPException) as conflict:
        respond_intervention(
            episode.episode_id,
            RespondEpisodeRequest(
                step_id=episode.current_step_id,
                response_text="42",
                session_id="session-t12",
            ),
            container,
        )
    assert conflict.value.status_code == 409
    assert tracker.get_state(exercise.kc_id).attempts == 0
    storage.close()


def test_episode_receipt_replays_same_answer_and_rejects_conflicting_content(tmp_path):
    exercise = _exercise()
    storage = StudentStorage(tmp_path / "student-state.db")
    tracker = BKTTracker(storage)
    episode = _episode()
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(
            get_episode=lambda _episode_id: episode,
            get_next_eligible_action=lambda **_kwargs: {"recommendation": "REINFORCE"},
        ),
        study_session_orchestrator=SimpleNamespace(
            get_snapshot=lambda session_id: SimpleNamespace(
                session_id=session_id, notebook_id="notebook-t12"
            ),
        ),
        exercise_store=SimpleNamespace(get_evaluable_exercise_by_id=lambda _exercise_id: exercise),
        observation_bridge=ObservationBridge(tracker),
        exact_grader=ExactMatchGrader(),
        mc_grader=MultiChoiceGrader(),
    )
    request = RespondEpisodeRequest(
        step_id=episode.current_step_id,
        response_text="42",
        session_id="session-t12",
    )

    first = respond_intervention("episode-t12", request, container)
    replay = respond_intervention("episode-t12", request, container)
    assert first["is_correct"] is True
    assert first["session_id"] == "session-t12"
    assert first["episode_id"] == "episode-t12"
    assert first["exercise_id"] == exercise.exercise_id
    assert first["was_idempotent_replay"] is False
    assert replay["was_idempotent_replay"] is True
    assert tracker.get_state("kc-t12").attempts == 1

    with pytest.raises(HTTPException) as conflict:
        respond_intervention(
            "episode-t12",
            request.model_copy(update={"response_text": "different answer"}),
            container,
        )
    assert conflict.value.status_code == 409
    assert tracker.get_state("kc-t12").attempts == 1
    storage.close()


def test_restoring_evaluating_episode_returns_same_exercise_without_mutating_episode_store():
    episode = _episode()
    exercise = _exercise()

    class ExerciseStore:
        def get_evaluable_exercise_by_id(self, exercise_id):
            return exercise if exercise_id == exercise.exercise_id else None

        def get_presentable_exercise_for_kc(self, _kc_id):
            pytest.fail("restoring must not select a different exercise")

    class EpisodeStore:
        saves = 0

        def save_episode(self, _episode):
            self.saves += 1

    orchestrator = PedagogicalOrchestrator.__new__(PedagogicalOrchestrator)
    orchestrator._active_episodes = {episode.episode_id: episode}
    orchestrator.exercise_store = ExerciseStore()
    orchestrator.episode_store = EpisodeStore()

    result = orchestrator.get_next_intervention(episode.episode_id)
    assert result["intervention_type"] == "EXERCISE"
    assert result["exercise"]["exercise_id"] == exercise.exercise_id
    assert result["step_id"] == episode.current_step_id
    assert result["session_id"] == episode.session_id
    assert result["restored"] is True
    assert orchestrator.episode_store.saves == 0


def test_first_exercise_selection_persists_one_transition():
    episode = _episode(phase=EpisodePhase.EXPLAINING, step_id="step_concept")
    exercise = _exercise()

    class ExerciseStore:
        def get_presentable_exercise_for_kc(self, kc_id):
            return exercise if kc_id == exercise.kc_id else None

    class EpisodeStore:
        saved = None

        def save_episode(self, value):
            self.saved = value

    orchestrator = PedagogicalOrchestrator.__new__(PedagogicalOrchestrator)
    orchestrator._active_episodes = {episode.episode_id: episode}
    orchestrator.exercise_store = ExerciseStore()
    orchestrator.episode_store = EpisodeStore()

    result = orchestrator.get_next_intervention(episode.episode_id)
    assert result["intervention_type"] == "EXERCISE"
    assert result["restored"] is False
    assert orchestrator.episode_store.saved.phase == EpisodePhase.EVALUATING
    assert orchestrator.episode_store.saved.current_step_id == f"step_eval_{exercise.exercise_id}"


def test_chat_exercise_evaluation_uses_matching_session_episode_and_durable_attempt(tmp_path):
    exercise = _exercise()
    episode = _episode()
    storage = StudentStorage(tmp_path / "chat-student-state.db")

    class Sessions:
        @staticmethod
        def get_snapshot(session_id):
            if session_id != "session-t12":
                raise ValueError("unknown synthetic session")
            return SimpleNamespace(
                session_id=session_id,
                notebook_id="notebook-t12",
                episode_id=episode.episode_id,
            )

    class Pedagogy:
        _kc_catalog = {"notebook-t12": {"kcs": [{"kc_id": exercise.kc_id}]}}

        @staticmethod
        def get_episode(episode_id):
            return episode if episode_id == episode.episode_id else None

    def build_container():
        return SimpleNamespace(
            student_storage=storage,
            exercise_store=SimpleNamespace(
                get_exercise_by_id=lambda _exercise_id: exercise,
                get_evaluable_exercise_by_id=lambda _exercise_id: exercise,
            ),
            generated_registry=None,
            study_session_orchestrator=Sessions(),
            pedagogical_orchestrator=Pedagogy(),
            bkt_tracker=BKTTracker(storage),
            exact_grader=ExactMatchGrader(),
            mc_grader=MultiChoiceGrader(),
            struggle_tracker=None,
            spaced_scheduler=None,
        )

    request = ExerciseEvaluateRequest(
        exercise_id=exercise.exercise_id,
        user_answer="42",
        notebook_id="notebook-t12",
        session_id="session-t12",
        episode_id=episode.episode_id,
        attempt_id="attempt-t12-chat-1",
    )
    first = asyncio.run(evaluate_exercise_answer(request, build_container()))
    replay = asyncio.run(evaluate_exercise_answer(request, build_container()))
    assert first["status"] == "GRADED"
    assert first["was_idempotent_replay"] is False
    assert replay["was_idempotent_replay"] is True
    assert BKTTracker(storage).get_state(exercise.kc_id).attempts == 1

    conflicting = request.model_copy(update={"user_answer": "different answer"})
    with pytest.raises(HTTPException) as conflict:
        asyncio.run(evaluate_exercise_answer(conflicting, build_container()))
    assert conflict.value.status_code == 409
    assert BKTTracker(storage).get_state(exercise.kc_id).attempts == 1
    storage.close()


def test_chat_exercise_episode_mismatch_is_ungraded_without_learning_mutation(tmp_path):
    exercise = _exercise()
    storage = StudentStorage(tmp_path / "chat-mismatch.db")
    tracker = BKTTracker(storage)
    container = SimpleNamespace(
        student_storage=storage,
        study_session_orchestrator=SimpleNamespace(
            get_snapshot=lambda _session_id: SimpleNamespace(
                session_id="session-t12",
                notebook_id="notebook-t12",
                episode_id="other-episode",
            ),
        ),
        pedagogical_orchestrator=SimpleNamespace(),
        bkt_tracker=tracker,
    )
    result = asyncio.run(evaluate_exercise_answer(
        ExerciseEvaluateRequest(
            exercise_id=exercise.exercise_id,
            user_answer="42",
            notebook_id="notebook-t12",
            session_id="session-t12",
            episode_id="episode-t12",
            attempt_id="attempt-t12-mismatch",
        ),
        container,
    ))
    assert result["status"] == "UNGRADED"
    assert tracker.get_state(exercise.kc_id).attempts == 0
    storage.close()
