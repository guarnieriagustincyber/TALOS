"""Tests for Spiral Curriculum Engine (Fase 1 - Roadmap v1.1).

Verifies retroactive KC deepening opportunities, BKT polymorphy,
causal relations, directive injection, and integration with chat.
"""

from typing import Dict
from unittest.mock import MagicMock

import pytest

from study_engine.pedagogy.exercise_compiler import HIGH_MASTERY_THRESHOLD
from study_engine.pedagogy.spiral_curriculum import (
    RETROACTIVE_RANGE_DEFAULT,
    SpiralCurriculumEngine,
)


def test_high_mastery_threshold_aligned_with_exercise_compiler():
    """E1: Verifica que MIN_CURRENT_MASTERY esté formalmente alineada con HIGH_MASTERY_THRESHOLD."""
    engine = SpiralCurriculumEngine()
    assert engine.MIN_CURRENT_MASTERY == HIGH_MASTERY_THRESHOLD
    assert engine.MIN_CURRENT_MASTERY == 0.6


def test_retroactive_range_default_constants():
    """E2: Verifica los límites documentados del rango retroactivo [0.4, 0.75]."""
    assert RETROACTIVE_RANGE_DEFAULT == (0.4, 0.75)


def test_detect_spiral_opportunities_mastered_mock_dict():
    """Detecta oportunidades cuando KC nuevo está dominado y previo en rango [0.4, 0.75]."""
    mock_bkt = {
        "race_conditions": {"p_L": 0.72},
        "punteros": {"p_L": 0.65},
        "sincronizacion": {"p_L": 0.50},
    }

    engine = SpiralCurriculumEngine(mock_bkt)
    opportunities = engine.detect_spiral_opportunities(
        current_kc="race_conditions",
        student_id="agustin",
    )

    assert len(opportunities) == 2
    assert opportunities[0]["new_kc"] == "race_conditions"
    assert opportunities[0]["new_mastery"] == 0.72
    # El primero debe ser 'punteros' porque su retro_mastery (0.65) es mayor que el de 'sincronizacion' (0.50)
    assert opportunities[0]["retroactive_kc"] == "punteros"
    assert opportunities[0]["retro_mastery"] == 0.65
    assert "concurrencia" in opportunities[0]["reason"]
    assert opportunities[0]["suggested_exercise"]["type"] == "multi_kc"
    assert "punteros" in opportunities[0]["suggested_exercise"]["kc_ids"]
    assert "race_conditions" in opportunities[0]["suggested_exercise"]["kc_ids"]


def test_no_opportunities_if_current_not_mastered():
    """No sugiere profundización si KC actual no alcanza el umbral de maestría (P(L) < 0.6)."""
    mock_bkt = {
        "race_conditions": {"p_L": 0.45},  # No dominado (< 0.6)
        "punteros": {"p_L": 0.65},
    }

    engine = SpiralCurriculumEngine(mock_bkt)
    opportunities = engine.detect_spiral_opportunities(
        current_kc="race_conditions",
        student_id="agustin",
    )

    assert opportunities == []


def test_no_opportunities_if_retro_out_of_range():
    """Excluye KCs previos con P(L) < 0.4 (no asimilado) o P(L) > 0.75 (ya plenamente dominado)."""
    mock_bkt = {
        "race_conditions": {"p_L": 0.80},
        "punteros": {"p_L": 0.30},          # Demasiado bajo (< 0.4)
        "sincronizacion": {"p_L": 0.90},    # Demasiado alto (> 0.75)
    }

    engine = SpiralCurriculumEngine(mock_bkt)
    opportunities = engine.detect_spiral_opportunities(
        current_kc="race_conditions",
        student_id="agustin",
    )

    assert opportunities == []


def test_opportunities_sorted_by_mastery_descending():
    """Verifica que las oportunidades se ordenen por maestría previa descendente."""
    mock_bkt = {
        "deadlock": {"p_L": 0.85},
        "mutex": {"p_L": 0.55},
        "semaforos": {"p_L": 0.70},
        "concurrencia": {"p_L": 0.60},
    }

    engine = SpiralCurriculumEngine(mock_bkt)
    opps = engine.detect_spiral_opportunities("deadlock", "agustin")

    assert len(opps) == 3
    retro_scores = [o["retro_mastery"] for o in opps]
    assert retro_scores == [0.70, 0.60, 0.55]
    assert opps[0]["retroactive_kc"] == "semaforos"


def test_kcs_without_causal_relations_e3(caplog):
    """E3: KCs sin relación causal definida retornan lista vacía y loguean debug sin error."""
    mock_bkt = {
        "kc_desconocido_sin_causa": {"p_L": 0.99},
    }

    engine = SpiralCurriculumEngine(mock_bkt)
    opps = engine.detect_spiral_opportunities("kc_desconocido_sin_causa", "agustin")

    assert opps == []


def test_inject_spiral_directive_formatting_and_agency_e4():
    """E4: Verifica que la directiva preserve la agencia del estudiante y mencione el endpoint."""
    mock_opps = [{
        "new_kc": "use_after_free",
        "retroactive_kc": "punteros",
        "new_mastery": 0.80,
        "retro_mastery": 0.60,
        "reason": "Volvamos a punteros con contexto de ciclo de vida.",
        "suggested_exercise": {
            "type": "multi_kc",
            "kc_ids": ["punteros", "use_after_free"],
        },
    }]

    engine = SpiralCurriculumEngine()
    directive = engine.inject_spiral_directive(mock_opps)

    assert directive is not None
    assert "=== PROFUNDIZACIÓN RETROACTIVA (CURRÍCULO EN ESPIRAL) ===" in directive
    assert "use_after_free" in directive
    assert "punteros" in directive
    assert "/api/student/exercises/generate/multi-kc" in directive
    # E4 cláusula explícita
    assert "IMPORTANTE: NO generar el ejercicio automáticamente. Solo sugerirlo." in directive
    assert "El estudiante debe aceptar explícitamente antes de generar." in directive

    # Lista vacía retorna None
    assert engine.inject_spiral_directive([]) is None


def test_bkt_tracker_polymorphism():
    """Verifica compatibilidad con objetos reales BKTTracker que usan get_state()."""
    class MockBKTState:
        def __init__(self, p_L: float):
            self.p_L = p_L

    class MockTracker:
        def __init__(self):
            self.states = {
                "buffer_overflow": MockBKTState(0.75),
                "punteros": MockBKTState(0.68),
            }

        def get_state(self, kc_id: str):
            return self.states.get(kc_id, MockBKTState(0.1))

    tracker = MockTracker()
    engine = SpiralCurriculumEngine(tracker)
    opps = engine.detect_spiral_opportunities("buffer_overflow", "student_1")

    assert len(opps) >= 1
    assert opps[0]["retroactive_kc"] == "punteros"
    assert opps[0]["new_mastery"] == 0.75
    assert opps[0]["retro_mastery"] == 0.68


def test_chat_integration_spiral_directive_injected(caplog, web_state_test_copy):
    """Verifica que _prepare_chat_context inyecte la directiva espiral y emita log forense."""
    import logging
    from study_engine.contracts.notebook import Notebook
    from study_engine.hierarchy.folder import Folder
    from study_engine.student.contracts import BKTState
    from study_engine.web.dependencies import AppContainer
    from study_engine.web.routes.chat import ChatQueryRequest, _prepare_chat_context
    from datetime import datetime, timezone

    container = AppContainer(working_dir=web_state_test_copy, use_mock=True)
    container.pedagogical_orchestrator._kc_catalog["fase0-soc"] = {
        "kcs": [{"kc_id": "race_conditions", "title": "Race Conditions"}]
    }

    # Preparar estados de BKT para race_conditions y punteros
    now = datetime.now(timezone.utc)
    container.bkt_tracker.save_state(
        BKTState(kc_id="race_conditions", p_L=0.85, p_T=0.3, p_G=0.25, p_S=0.1, attempts=3, last_update=now)
    )
    container.bkt_tracker.save_state(
        BKTState(kc_id="punteros", p_L=0.65, p_T=0.3, p_G=0.25, p_S=0.1, attempts=2, last_update=now)
    )

    caplog.set_level(logging.INFO)

    req = ChatQueryRequest(
        prompt="Pregunta sobre race_conditions en sistemas concurrentes",
        notebook_id="fase0-soc",
        requested_phase="conceptual",
    )

    result = _prepare_chat_context(
        store=container.knowledge_store,
        resolver=container.scope_resolver,
        container=container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )
    bkt_directive = result[6]

    # La directiva de bkt_directive debe contener la sección espiral
    assert bkt_directive is not None
    assert "=== PROFUNDIZACIÓN RETROACTIVA (CURRÍCULO EN ESPIRAL) ===" in bkt_directive
    assert "race_conditions" in bkt_directive
    assert "punteros" in bkt_directive

    # Verificar emisión de log forense
    found_log = False
    for rec in caplog.records:
        if "SPIRAL_OPPORTUNITY_DETECTED" in rec.message:
            found_log = True
            assert "race_conditions" in rec.message
            assert "punteros" in rec.message
            break
    assert found_log, "Debe registrarse el log forense SPIRAL_OPPORTUNITY_DETECTED"


def test_struggle_precedence_over_spiral(web_state_test_copy):
    """Verifica que ante struggle_active, el Protocolo de Lucha prevalezca y NO se inyecte la espiral."""
    from study_engine.student.contracts import BKTState
    from study_engine.web.dependencies import AppContainer
    from study_engine.web.routes.chat import ChatQueryRequest, _prepare_chat_context
    from datetime import datetime, timezone

    container = AppContainer(working_dir=web_state_test_copy, use_mock=True)
    container.pedagogical_orchestrator._kc_catalog["fase0-soc"] = {
        "kcs": [{"kc_id": "race_conditions", "title": "Race Conditions"}]
    }

    now = datetime.now(timezone.utc)
    container.bkt_tracker.save_state(
        BKTState(kc_id="race_conditions", p_L=0.85, p_T=0.3, p_G=0.25, p_S=0.1, attempts=5, last_update=now)
    )
    container.bkt_tracker.save_state(
        BKTState(kc_id="punteros", p_L=0.65, p_T=0.3, p_G=0.25, p_S=0.1, attempts=2, last_update=now)
    )

    # Forzar 3 fallos consecutivos en race_conditions para activar struggle mode
    for _ in range(3):
        container.struggle_tracker.record("race_conditions", correct=False)

    assert container.struggle_tracker.is_struggling("race_conditions") is True

    req = ChatQueryRequest(
        prompt="Pregunta sobre race_conditions",
        notebook_id="fase0-soc",
        requested_phase="conceptual",
    )

    result = _prepare_chat_context(
        store=container.knowledge_store,
        resolver=container.scope_resolver,
        container=container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )
    bkt_directive = result[6]

    # Protocolo de lucha debe estar presente
    assert bkt_directive is not None
    assert "PROHIBIDO repetir" in bkt_directive or "LUCHA" in bkt_directive or "ESTUDIANTE EN DIFICULTAD" in bkt_directive
    # Directiva espiral NO debe estar presente
    assert "=== PROFUNDIZACIÓN RETROACTIVA (CURRÍCULO EN ESPIRAL) ===" not in bkt_directive


def test_evaluate_exercise_returns_spiral_opportunities(
    tmp_path, web_state_test_copy
):
    """Verifica que /api/chat/evaluate devuelva oportunidades en espiral tras acierto con P(L) >= 0.6."""
    import json
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient
    from study_engine.pedagogy.exercise_store import ExerciseStore
    from study_engine.student.contracts import BKTState
    from study_engine.web.app import create_app
    from study_engine.web.dependencies import AppContainer, set_container

    container = AppContainer(working_dir=web_state_test_copy, use_mock=True)
    ex_file = tmp_path / "exercises.json"
    ex_file.write_text(json.dumps([{
        "exercise_id": "ex_spiral_1",
        "source_id": "src_test",
        "source_location": "p.1",
        "source_hash": "0" * 64,
        "extractor_version": "test",
        "extraction_method": "test",
        "verification_status": "QUALIFIABLE",
        "verified_by": "test",
        "verification_timestamp": None,
        "content_hash": "1" * 64,
        "kc_id": "race_conditions",
        "prompt": "Test race conditions",
        "exercise_type": "NUMERIC",
        "options": None,
        "expected_answer": "42",
        "solution_explanation": None,
    }]), encoding="utf-8")
    container.exercise_store = ExerciseStore(storage_path=ex_file)

    now = datetime.now(timezone.utc)
    container.bkt_tracker.save_state(
        BKTState(kc_id="race_conditions", p_L=0.75, p_T=0.1, p_G=0.25, p_S=0.1, attempts=2, last_update=now)
    )
    container.bkt_tracker.save_state(
        BKTState(kc_id="punteros", p_L=0.60, p_T=0.1, p_G=0.25, p_S=0.1, attempts=2, last_update=now)
    )

    app = create_app()
    set_container(container)
    client = TestClient(app)

    r = client.post("/api/chat/evaluate", json={"exercise_id": "ex_spiral_1", "user_answer": "42"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_correct"] is True
    assert "spiral_opportunities" in data
    assert len(data["spiral_opportunities"]) >= 1
    assert data["spiral_opportunities"][0]["retroactive_kc"] == "punteros"
