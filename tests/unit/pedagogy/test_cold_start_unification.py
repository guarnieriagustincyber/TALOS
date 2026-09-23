"""Commit 4 — Tests para regla única de cold-start P(L) ausente y propuesta acelerada.

Contrato:
- KC no evaluado (attempts == 0) asigna modo 'intermediate' (neutral).
- Flag cold_start_mode configurable en bkt_params.json.
- Propuesta de ejercicios acelerada a 2 turnos para KCs no evaluados (attempts == 0).
- Telemetría estructurada [COLD_START_FIRST_ATTEMPT] al evaluar por primera vez un KC cold-start.
"""

import logging
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from study_engine.pedagogy.exercise_service import (
    PROPOSAL_COLD_START_THRESHOLD,
    PROPOSAL_STREAK_THRESHOLD,
    should_propose,
)
from study_engine.pedagogy.student_context import determine_pedagogical_context_mode
from study_engine.student.contracts import BKTState
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def test_cold_start_unassessed_kc_assigns_intermediate():
    """KC con attempts == 0 asigna 'intermediate' sin importar si p_L0 < 0.30."""
    tracker = MagicMock()
    # Unassessed KC: p_L = 0.10, attempts = 0
    tracker.get_state.return_value = BKTState(kc_id="kc_unassessed", p_L=0.10, attempts=0)
    tracker.params = {"cold_start_mode": "intermediate"}

    mode, meta = determine_pedagogical_context_mode(
        target_kc_id="kc_unassessed",
        bkt_tracker=tracker,
        kc_catalog={"fase0-soc": {"kcs": [{"kc_id": "kc_unassessed", "prerequisites": []}]}},
        notebook_id="fase0-soc",
    )

    assert mode == "intermediate"
    assert meta["attempts"] == 0
    assert meta["cold_start_mode"] == "intermediate"


def test_cold_start_respects_custom_config_flag():
    """Si cold_start_mode se configura a otro valor, se respeta para attempts == 0."""
    tracker = MagicMock()
    tracker.get_state.return_value = BKTState(kc_id="kc_custom", p_L=0.10, attempts=0)
    tracker.params = {"cold_start_mode": "basic"}

    mode, meta = determine_pedagogical_context_mode(
        target_kc_id="kc_custom",
        bkt_tracker=tracker,
        kc_catalog={"fase0-soc": {"kcs": [{"kc_id": "kc_custom", "prerequisites": []}]}},
        notebook_id="fase0-soc",
    )

    assert mode == "basic"
    assert meta["cold_start_mode"] == "basic"


def test_accelerated_proposal_threshold_for_unassessed_kcs():
    """Unassessed KC propone al turno 2; assessed KC al turno 3."""
    assert should_propose(1, attempts=0) is False
    assert should_propose(PROPOSAL_COLD_START_THRESHOLD, attempts=0) is True

    assert should_propose(2, attempts=1) is False
    assert should_propose(PROPOSAL_STREAK_THRESHOLD, attempts=1) is True


def test_first_attempt_cold_start_emits_structured_telemetry(tmp_path, caplog):
    """El primer intento evaluado sobre un KC emite telemetría [COLD_START_FIRST_ATTEMPT]."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    # KC nunca evaluado
    state_prior = container.bkt_tracker.get_state("punteros")
    assert state_prior.attempts == 0

    # Generar y evaluar
    r_gen = client.post(
        "/api/student/exercises/generate/debugging",
        json={"kc_id": "punteros", "bug_type": "buffer_overflow"},
    )
    ex_id = r_gen.json()["exercise_id"]

    with caplog.at_level(logging.INFO):
        r_eval = client.post(
            "/api/chat/evaluate",
            json={"exercise_id": ex_id, "user_answer": "buffer overflow"},
        )
        assert r_eval.status_code == 200

    assert any("[COLD_START_FIRST_ATTEMPT]" in r.message for r in caplog.records)
