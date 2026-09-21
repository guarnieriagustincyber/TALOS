"""Integration test for Live Socratic Evaluation and BKT Update Endpoint."""

import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container, get_container


@pytest.fixture
def client_and_container():
    container = AppContainer(use_mock=True)
    set_container(container)
    app = create_app()
    with TestClient(app) as client:
        yield client, container


def test_live_socratic_evaluation_updates_bkt(client_and_container):
    client, container = client_and_container
    kc = "aritmetica_punteros"

    # Prior state before answer
    prior_state = container.bkt_tracker.get_state(kc)
    prior_p_L = prior_state.p_L
    prior_attempts = prior_state.attempts

    # Send student response to socratic challenge using registered exercise
    payload = {
        "student_response": "1012",
        "exercise_id": "ex_fase0_ptr_01",
        "kc_id": kc,
        "is_mc": False,
    }
    resp = client.post(
        "/api/pedagogy/episode/ep_test_session/dialogue/evaluate-socratic",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "EVALUATED"
    assert data["kc_id"] == kc
    assert data["is_correct"] is True
    assert data["attempts"] == prior_attempts + 1
    # Under Corbett & Anderson, correct answer increases P(L)
    assert data["p_L"] > prior_p_L

    # Verify persisted in storage
    post_state = container.bkt_tracker.get_state(kc)
    assert post_state.attempts == prior_attempts + 1
    assert round(post_state.p_L, 4) == round(data["p_L"], 4)


def test_client_cannot_inject_expected_answer(client_and_container):
    """Verify that an attacker attempting to pass expected_answer in client payload cannot hack BKT."""
    client, container = client_and_container
    kc = "aritmetica_punteros"

    # Prior state
    prior_state = container.bkt_tracker.get_state(kc)
    prior_attempts = prior_state.attempts

    # Attempt to inject wrong student answer with matching injected expected_answer
    # The backend MUST ignore client expected_answer and grade against backend "1012"
    payload = {
        "student_response": "HACKED_ANSWER",
        "expected_answer": "HACKED_ANSWER",  # ← Attacker injection attempt
        "exercise_id": "ex_fase0_ptr_01",
        "kc_id": kc,
    }
    resp = client.post(
        "/api/pedagogy/episode/ep_test_session/dialogue/evaluate-socratic",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "EVALUATED"
    assert data["is_correct"] is False  # Must be graded FALSE against backend truth ("1012")
    assert "no equivalente" in data["feedback"].lower() or "incorrecta" in data["feedback"].lower()


def test_uncertified_kc_returns_ungraded_without_bkt_mutation(client_and_container):
    """Verify that answering a challenge without backend certified key returns UNGRADED with zero BKT change."""
    client, container = client_and_container
    unknown_kc = "nonexistent_kc_without_exercise"

    prior_state = container.bkt_tracker.get_state(unknown_kc)
    prior_p_L = prior_state.p_L
    prior_attempts = prior_state.attempts

    payload = {
        "student_response": "Some freeform reasoning without certified answer in catalog",
        "kc_id": unknown_kc,
    }
    resp = client.post(
        "/api/pedagogy/episode/ep_test_session/dialogue/evaluate-socratic",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "UNGRADED"
    assert data["is_correct"] is None
    # BKT must NOT have mutated
    post_state = container.bkt_tracker.get_state(unknown_kc)
    assert post_state.attempts == prior_attempts
    assert post_state.p_L == prior_p_L


def test_live_socratic_evaluation_incorrect_handles_decay(client_and_container):
    client, container = client_and_container
    kc = "arrays_direccionamiento_contiguo"

    # Reset or record initial
    container.bkt_tracker.reset(kc)
    prior_p_L = container.bkt_tracker.get_state(kc).p_L

    # ex_fase0_contig_01 has correct answer "B"
    payload = {
        "student_response": "C",  # Incorrect
        "exercise_id": "ex_fase0_contig_01",
        "kc_id": kc,
        "is_mc": True,
        "options_count": 4,
    }
    resp = client.post(
        "/api/pedagogy/episode/ep_test_session/dialogue/evaluate-socratic",
        json=payload,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert "incorrecta" in data["feedback"].lower()
    assert data["p_L"] < prior_p_L or data["attempts"] == 1
