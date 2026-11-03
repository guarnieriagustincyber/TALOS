"""Unit tests for FASE S5: UX & Interfaz.

Verifies:
1. Socratic dialogue evaluation: correct response increases BKT mastery.
2. Socratic dialogue evaluation: incorrect response updates attempts and generates a scaffolding hint without revealing the expected answer.
3. Notebook scope prefix matching: resolves certified exercises by notebook identifier.
4. Epistemic role resolution for consulted sources and citations.
"""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

from study_engine.pedagogy.graders import MultiChoiceGrader, ExactMatchGrader
from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.structured_pipeline import resolve_epistemic_role
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
from study_engine.student.storage import StudentStorage
from study_engine.web.dependencies import AppContainer
from study_engine.web.routes.dialogue import (
    accept_exercise,
    evaluate_socratic_response,
    SocraticEvaluationRequest,
)


@pytest.fixture
def mock_container(tmp_path):
    container = MagicMock(spec=AppContainer)
    container.student_storage = StudentStorage(tmp_path / "student-state.db")
    container.bkt_tracker = BKTTracker(storage=container.student_storage)
    container.spaced_scheduler = SpacedRepetitionScheduler(container.student_storage)
    container.exact_grader = ExactMatchGrader()
    container.mc_grader = MultiChoiceGrader()

    # Setup ExerciseStore with certified qualifiable exercises
    store_file = tmp_path / "exercises.json"
    ex_store = ExerciseStore(storage_path=store_file)
    cand1 = ExerciseCandidate(
        exercise_id="ex_test_so_01",
        source_id="test_src",
        source_location="ch1",
        source_hash="sha256_src_01",
        extractor_version="1.0",
        extraction_method="manual",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE,
        verified_by="test_runner",
        verification_timestamp=None,
        content_hash="sha256_mock_01",
        kc_id="fase0-soc-kc-01",
        prompt="¿Cuál es el valor del puntero base en x86?",
        exercise_type=ExerciseType.EXACT_TEXT,
        expected_answer="RBP",
        solution_explanation="El registro RBP mantiene la base del marco de pila actual en la arquitectura x86-64.",
    )
    cand2 = ExerciseCandidate(
        exercise_id="ex_test_mc_01",
        source_id="test_src",
        source_location="ch2",
        source_hash="sha256_src_02",
        extractor_version="1.0",
        extraction_method="manual",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE,
        verified_by="test_runner",
        verification_timestamp=None,
        content_hash="sha256_mock_02",
        kc_id="fase0-soc-kc-02",
        prompt="¿Qué estructura asigna memoria contigua?",
        exercise_type=ExerciseType.MC,
        options=("A) Lista enlazada", "B) Arreglo", "C) Árbol", "D) Grafo"),
        expected_answer="B",
        solution_explanation="Los arreglos garantizan contigüidad espacial en la memoria física y virtual.",
    )
    ex_store.add_exercise(cand1, persist=False)
    ex_store.add_exercise(cand2, persist=False)
    container.exercise_store = ex_store
    container.pedagogical_orchestrator = MagicMock()
    container.pedagogical_orchestrator._kc_catalog = {
        "fase0-soc": {"kcs": [
            {"kc_id": "fase0-soc-kc-01"}, {"kc_id": "fase0-soc-kc-02"}
        ]}
    }
    container.pedagogical_orchestrator.get_episode.return_value = Episode(
        episode_id="ep_mock",
        session_id="session-mock",
        notebook_id="fase0-soc",
        kc_id="fase0-soc-kc-01",
        objective="Ejercicio sintético",
        phase=EpisodePhase.EVALUATING,
        current_step_id="step_eval_ex_test_so_01",
    )
    container.study_session_orchestrator = MagicMock()
    container.study_session_orchestrator.get_snapshot.return_value = SimpleNamespace(
        session_id="session-mock",
        notebook_id="fase0-soc",
    )

    yield container
    container.student_storage.close()


def test_evaluate_socratic_correct_increases_bkt(mock_container):
    """Correct answer deterministically updates BKT mastery and returns positive feedback."""
    req = SocraticEvaluationRequest(
        student_response="RBP",
        exercise_id="ex_test_so_01",
        session_id="session-mock",
        attempt_id="attempt-correct-1",
        kc_id="fase0-soc-kc-01",
    )
    init_state = mock_container.bkt_tracker.get_state("fase0-soc-kc-01")
    init_p_l = init_state.p_L

    res = evaluate_socratic_response("ep_mock", req, mock_container)

    assert res["status"] == "EVALUATED"
    assert res["is_correct"] is True
    assert res["p_L"] > init_p_l
    assert res["attempts"] == 1
    assert "¡Correcto!" in res["feedback"]
    assert "coincide con la opción esperada" in res["feedback"]
    assert "verificado con éxito contra el corpus" not in res["feedback"]
    assert res["hint"] is None


def test_accept_exercise_returns_server_identity_without_answer_key(mock_container):
    candidate = mock_container.exercise_store.get_exercise_by_id("ex_test_so_01")
    mock_container.pedagogical_orchestrator.get_next_intervention.return_value = {
        "intervention_type": "EXERCISE",
        "step_id": "step_eval_ex_test_so_01",
        "exercise": candidate.to_dict(),
    }

    result = accept_exercise("ep_mock", mock_container)

    assert result["exercise_id"] == "ex_test_so_01"
    assert result["step_id"] == "step_eval_ex_test_so_01"
    assert "expected_answer" not in result
    assert "solution_explanation" not in result


def test_evaluate_socratic_incorrect_provides_hint_without_revealing_answer(mock_container):
    """Incorrect answer updates BKT attempts and returns a pedagogical hint without exposing canonical key."""
    req = SocraticEvaluationRequest(
        student_response="RSP",  # Wrong answer (RSP instead of RBP)
        exercise_id="ex_test_so_01",
        session_id="session-mock",
        attempt_id="attempt-incorrect-1",
        kc_id="fase0-soc-kc-01",
    )
    res = evaluate_socratic_response("ep_mock", req, mock_container)

    assert res["status"] == "EVALUATED"
    assert res["is_correct"] is False
    assert res["attempts"] == 1
    assert res["hint"] is not None
    assert len(res["hint"]) > 10
    # CRITICAL: Do NOT reveal the expected canonical answer ("RBP")
    assert "RBP" not in res["hint"]
    assert "RBP" not in res["feedback"]
    assert "No es del todo exacto" in res["feedback"]


def test_evaluate_socratic_does_not_infer_exercise_from_notebook_scope(mock_container):
    """A notebook name alone cannot identify the exercise presented in the episode."""
    req = SocraticEvaluationRequest(
        student_response="B",
        kc_id="fase0-soc",
        is_mc=True,
    )
    before = mock_container.bkt_tracker.get_state("fase0-soc-kc-01").attempts
    res = evaluate_socratic_response("ep_mock", req, mock_container)

    assert res["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-01").attempts == before


def test_evaluate_socratic_mc_uses_certified_type_and_options(mock_container):
    from dataclasses import replace

    episode = mock_container.pedagogical_orchestrator.get_episode.return_value
    mock_container.pedagogical_orchestrator.get_episode.return_value = replace(
        episode, kc_id="fase0-soc-kc-02", current_step_id="step_eval_ex_test_mc_01"
    )
    req = SocraticEvaluationRequest(
        student_response="B", exercise_id="ex_test_mc_01", kc_id="fase0-soc-kc-02",
        session_id="session-mock", attempt_id="attempt-mc-1",
        options_count=4,
    )

    res = evaluate_socratic_response("ep_mock", req, mock_container)

    assert res["status"] == "EVALUATED"
    assert res["is_correct"] is True
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-02").attempts == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"kc_id": "fase0-soc-kc-02"},
        {"exercise_id": "missing-exercise"},
        {"exercise_id": "ex_test_mc_01"},
        {"is_mc": True},
        {"options_count": 4},
    ],
)
def test_evaluate_socratic_rejects_client_identity_or_type_changes_without_mutation(
    mock_container, changes
):
    payload = {
        "student_response": "RBP", "exercise_id": "ex_test_so_01",
        "kc_id": "fase0-soc-kc-01", "session_id": "session-mock",
        "attempt_id": "attempt-tamper-1",
    }
    payload.update(changes)
    result = evaluate_socratic_response(
        "ep_mock", SocraticEvaluationRequest(**payload), mock_container
    )
    assert result["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-01").attempts == 0


def test_evaluate_socratic_rejects_incompatible_or_unpresented_episode(mock_container):
    from dataclasses import replace

    episode = mock_container.pedagogical_orchestrator.get_episode.return_value
    for changed in (
        replace(episode, phase=EpisodePhase.DIALOGUE),
        replace(episode, current_step_id="step_eval_other"),
        replace(episode, kc_id="fase0-soc-kc-02"),
        None,
    ):
        mock_container.pedagogical_orchestrator.get_episode.return_value = changed
        result = evaluate_socratic_response(
            "ep_mock",
            SocraticEvaluationRequest(
                student_response="RBP", exercise_id="ex_test_so_01",
                session_id="session-mock", attempt_id="attempt-incompatible-1",
            ),
            mock_container,
        )
        assert result["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-01").attempts == 0


def test_evaluate_socratic_rejects_wrong_notebook_scope(mock_container):
    from dataclasses import replace

    episode = mock_container.pedagogical_orchestrator.get_episode.return_value
    mock_container.pedagogical_orchestrator.get_episode.return_value = replace(
        episode, notebook_id="other-notebook"
    )
    result = evaluate_socratic_response(
        "ep_mock",
        SocraticEvaluationRequest(
            student_response="RBP", exercise_id="ex_test_so_01",
            session_id="session-mock", attempt_id="attempt-wrong-notebook-1",
        ),
        mock_container,
    )
    assert result["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-01").attempts == 0


def test_evaluate_socratic_rejects_tampered_mc_options(mock_container):
    from dataclasses import replace

    episode = mock_container.pedagogical_orchestrator.get_episode.return_value
    mock_container.pedagogical_orchestrator.get_episode.return_value = replace(
        episode, kc_id="fase0-soc-kc-02", current_step_id="step_eval_ex_test_mc_01"
    )
    result = evaluate_socratic_response(
        "ep_mock",
        SocraticEvaluationRequest(
            student_response="B", exercise_id="ex_test_mc_01",
            session_id="session-mock", attempt_id="attempt-mc-tampered-1",
            kc_id="fase0-soc-kc-02", is_mc=True, options_count=2,
        ),
        mock_container,
    )
    assert result["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-02").attempts == 0


def test_evaluate_socratic_rejects_mc_labeled_as_open(mock_container):
    from dataclasses import replace

    episode = mock_container.pedagogical_orchestrator.get_episode.return_value
    mock_container.pedagogical_orchestrator.get_episode.return_value = replace(
        episode, kc_id="fase0-soc-kc-02", current_step_id="step_eval_ex_test_mc_01"
    )
    result = evaluate_socratic_response(
        "ep_mock",
        SocraticEvaluationRequest(
            student_response="B", exercise_id="ex_test_mc_01",
            session_id="session-mock", attempt_id="attempt-mc-type-1",
            kc_id="fase0-soc-kc-02", is_mc=False,
        ),
        mock_container,
    )
    assert result["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-02").attempts == 0


def test_evaluate_socratic_rejects_nonpresentable_exercise(mock_container):
    from dataclasses import replace

    exercise = mock_container.exercise_store.get_exercise_by_id("ex_test_so_01")
    mock_container.exercise_store.add_exercise(
        replace(exercise, verification_status=ExerciseVerificationStatus.UNVERIFIED),
        persist=False,
    )
    result = evaluate_socratic_response(
        "ep_mock",
        SocraticEvaluationRequest(
            student_response="RBP", exercise_id="ex_test_so_01",
            session_id="session-mock", attempt_id="attempt-unverified-1",
        ),
        mock_container,
    )
    assert result["status"] == "UNGRADED"
    assert mock_container.bkt_tracker.get_state("fase0-soc-kc-01").attempts == 0


def test_resolve_epistemic_role():
    """Validates mapping of authors and sources to pedagogical, formal, or technical roles."""
    # Tanenbaum in so2 -> pedagogical
    role_tan = resolve_epistemic_role(source_id="tanenbaum_os", notebook_id="fadena-so2")
    assert role_tan == "pedagogical"

    # Stallings in so2 -> technical
    role_stall = resolve_epistemic_role(source_id="stallings_os_internals", notebook_id="fadena-so2")
    assert role_stall == "technical"

    # Silberschatz in so2 -> formal
    role_silb = resolve_epistemic_role(source_id="silberschatz_so", notebook_id="fadena-so2")
    assert role_silb == "formal"

    # Date in std -> formal
    role_date = resolve_epistemic_role(source_title="Date - Introducción a Sistemas de BD", notebook_id="fadena-std")
    assert role_date == "formal"

    # Kurose in teleco -> pedagogical
    role_kur = resolve_epistemic_role(author="Kurose", notebook_id="fadena-teleco")
    assert role_kur == "pedagogical"
