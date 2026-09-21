"""Unit tests for FASE S5: UX & Interfaz.

Verifies:
1. Socratic dialogue evaluation: correct response increases BKT mastery.
2. Socratic dialogue evaluation: incorrect response updates attempts and generates a scaffolding hint without revealing the expected answer.
3. Notebook scope prefix matching: resolves certified exercises by notebook identifier.
4. Epistemic role resolution for consulted sources and citations.
"""

import pytest
from unittest.mock import MagicMock

from study_engine.pedagogy.graders import MultiChoiceGrader, ExactMatchGrader
from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.structured_pipeline import resolve_epistemic_role
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.web.dependencies import AppContainer
from study_engine.web.routes.dialogue import evaluate_socratic_response, SocraticEvaluationRequest


@pytest.fixture
def mock_container(tmp_path):
    container = MagicMock(spec=AppContainer)
    container.bkt_tracker = BKTTracker()
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
    container.pedagogical_orchestrator.get_episode.return_value = None

    return container


def test_evaluate_socratic_correct_increases_bkt(mock_container):
    """Correct answer deterministically updates BKT mastery and returns positive feedback."""
    req = SocraticEvaluationRequest(
        student_response="RBP",
        exercise_id="ex_test_so_01",
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
    assert res["hint"] is None


def test_evaluate_socratic_incorrect_provides_hint_without_revealing_answer(mock_container):
    """Incorrect answer updates BKT attempts and returns a pedagogical hint without exposing canonical key."""
    req = SocraticEvaluationRequest(
        student_response="RSP",  # Wrong answer (RSP instead of RBP)
        exercise_id="ex_test_so_01",
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


def test_evaluate_socratic_resolves_notebook_scope_prefix(mock_container):
    """Passing a notebook scope ID resolves a certified exercise whose KC belongs to that notebook."""
    req = SocraticEvaluationRequest(
        student_response="B",
        kc_id="fase0-soc",  # Notebook scope ID instead of exact KC
        is_mc=True,
    )
    res = evaluate_socratic_response("ep_mock", req, mock_container)

    assert res["status"] == "EVALUATED"
    assert res["is_correct"] is True
    assert res["exercise_id"] in ("ex_test_so_01", "ex_test_mc_01")
    assert res["attempts"] >= 1


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
