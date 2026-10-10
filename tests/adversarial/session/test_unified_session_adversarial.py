"""Adversarial and boundary test suite for Unified Study Session (Directiva Final v2 §7).

Verifies the 10 negative tests demanded by the directive:
1. test_bkt_cannot_skip_prerequisites
2. test_frontend_cannot_set_kc
3. test_frontend_cannot_calculate_transition
4. test_frontend_cannot_interpret_bkt
5. test_unauthorized_action_rejected
6. test_invalid_payload_rejected
7. test_session_not_found
8. test_chat_general_cannot_invent_notebook
9. test_snapshot_mutation_does_not_affect_state
10. test_opening_brief_narrative_cannot_override_facts
"""

from dataclasses import FrozenInstanceError
from pathlib import Path
import pytest

from study_engine.contracts.notebook import Notebook
from study_engine.federation.notebook_registry import NotebookRegistry
from study_engine.session.opening_brief_builder import OpeningBriefBuilder
from study_engine.session.progression_policy import ProgressionPolicy
from study_engine.session.study_session_contracts import (
    ActionNotAllowedForPhaseError,
    ActionNotAvailableError,
    CurriculumPosition,
    InvalidPayloadError,
    OpeningBriefFacts,
    PolicyDeniedError,
    SessionNotFoundError,
    StudySessionSnapshot,
)
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage
from study_engine.web.dependencies import AppContainer


@pytest.fixture
def test_container(tmp_path: Path, knowledge_store_test_copy):
    """Instancia container de prueba con componentes soberanos."""
    if knowledge_store_test_copy is not None:
        import shutil
        shutil.copy2(knowledge_store_test_copy, tmp_path / "knowledge_store.db")
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    return container


class TestUnifiedSessionAdversarial:
    """10 Negative Tests exigidos por §7 de Directiva Final v2."""

    def test_bkt_cannot_skip_prerequisites(self, test_container):
        """1. BKT con P(L)=0.99 no puede hacer elegible un KC cuyos prerequisitos no están cumplidos."""
        policy = ProgressionPolicy()

        curriculum_kcs = [
            {"kc_id": "intro", "title": "Intro", "unit": 1, "prerequisites": []},
            {"kc_id": "advanced", "title": "Avanzado", "unit": 1, "prerequisites": ["intro"]},
        ]
        # intro sin completar (0.1), advanced artificialmente alto (0.99)
        bkt_states = {
            "intro": BKTState(kc_id="intro", p_L=0.1, p_G=0.2, p_S=0.1, p_T=0.1),
            "advanced": BKTState(kc_id="advanced", p_L=0.99, p_G=0.2, p_S=0.1, p_T=0.1),
        }

        eligible = policy.get_eligible_kcs(curriculum_kcs, bkt_states)
        # advanced NO puede ser elegible porque intro tiene P(L)=0.1 < 0.60
        assert "advanced" not in eligible
        assert "intro" in eligible

    def test_frontend_cannot_set_kc(self, test_container):
        """2. El frontend no puede enviar un KC arbitrario fuera de los habilitados por prerequisitos."""
        orch = test_container.study_session_orchestrator
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # Intentar forzar selección de un KC no elegible
        with pytest.raises(PolicyDeniedError) as exc_info:
            orch.execute_action(
                snap.session_id,
                "SELECT_DIFFERENT_KC",
                payload={"kc_id": "kc_inventado_o_bloqueado"},
            )
        assert "no está habilitado por prerequisitos" in str(exc_info.value)

    def test_frontend_cannot_calculate_transition(self, test_container):
        """3. El backend rechaza transiciones ilegales intentadas directamente por el cliente."""
        orch = test_container.study_session_orchestrator
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")
        assert snap.episode_phase == "OPENING_BRIEF"

        # El cliente intenta enviar una acción de evaluación directa sin pasar por el flujo
        with pytest.raises(ActionNotAvailableError):
            orch.execute_action(snap.session_id, "SUBMIT_ANSWER", payload={"answer": "42"})

    def test_frontend_cannot_interpret_bkt(self, test_container):
        """4. El cliente no puede forzar o dictar el valor o interpretación de BKT en la sesión."""
        orch = test_container.study_session_orchestrator
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # El snapshot es derivado por el backend; bkt_estimate proviene únicamente del BKTTracker soberano
        actual_bkt = test_container.bkt_tracker.get_state(snap.current_kc_id).p_L
        assert snap.bkt_estimate == pytest.approx(actual_bkt, 0.01)

    def test_unauthorized_action_rejected(self, test_container):
        """5. Cualquier acción no autorizada para la fase actual es rechazada (400)."""
        orch = test_container.study_session_orchestrator
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        with pytest.raises(ActionNotAllowedForPhaseError):
            # Intentar REQUEST_DIALOGUE directamente en OPENING_BRIEF
            orch._sessions[snap.session_id] = orch._sessions[snap.session_id].__class__(
                **{**orch._sessions[snap.session_id].__dict__, "available_actions": ("REQUEST_DIALOGUE",)}
            )
            orch.execute_action(snap.session_id, "REQUEST_DIALOGUE")

    def test_invalid_payload_rejected(self, test_container):
        """6. Payload con campos faltantes o inválidos es rechazado deterministamente (422)."""
        orch = test_container.study_session_orchestrator
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # SELECT_DIFFERENT_KC sin 'kc_id'
        with pytest.raises(InvalidPayloadError):
            orch.execute_action(snap.session_id, "SELECT_DIFFERENT_KC", payload={})

        # SELECT_DIFFERENT_KC con 'kc_id' no string
        with pytest.raises(InvalidPayloadError):
            orch.execute_action(snap.session_id, "SELECT_DIFFERENT_KC", payload={"kc_id": 12345})

    def test_session_not_found(self, test_container):
        """7. Intentar accionar o consultar una sesión inexistente arroja SessionNotFoundError (404)."""
        orch = test_container.study_session_orchestrator

        with pytest.raises(SessionNotFoundError):
            orch.get_snapshot("sess_inexistente_999")

        with pytest.raises(SessionNotFoundError):
            orch.execute_action("sess_inexistente_999", "START_EXPLANATION")

    def test_chat_general_cannot_invent_notebook(self, test_container):
        """8. Chat General no puede inventar un cuaderno ni consultar un ID no registrado."""
        reg = test_container.notebook_registry
        assert reg.get_notebook("root_global") is None
        assert reg.get_notebook("non_existent_notebook_123") is None

        # Si el usuario pregunta sin cuaderno activo, el frontend debe mantenerse en Chat General
        # y rechazar apertura con 404
        orch = test_container.study_session_orchestrator
        with pytest.raises(ValueError) as exc_info:
            orch.open_session("root_global", "agustin")
        assert "no encontrado o inactivo" in str(exc_info.value)

    def test_snapshot_mutation_does_not_affect_state(self, test_container):
        """9. Mutar el StudySessionSnapshot (si fuera mutable o por reflejo) no afecta el estado soberano."""
        orch = test_container.study_session_orchestrator
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # StudySessionSnapshot es inmutable (frozen dataclass)
        with pytest.raises(FrozenInstanceError):
            snap.episode_phase = "HACKED_PHASE"

        with pytest.raises(FrozenInstanceError):
            snap.bkt_estimate = 1.0

        # Verificar que el estado interno sigue intacto
        internal_state = orch._sessions[snap.session_id]
        assert internal_state.episode_phase == "OPENING_BRIEF"

    def test_opening_brief_narrative_cannot_override_facts(self, test_container):
        """10. La narrativa de bienvenida jamás puede anular o sobreescribir los hechos deterministas."""
        builder = OpeningBriefBuilder()
        nb = Notebook(id="nb_test", name="Test NB", folder_id="f1")
        kcs = [{"kc_id": "kc1", "title": "KC 1", "unit": 1, "prerequisites": []}]
        bkt = {"kc1": BKTState(kc_id="kc1", p_L=0.75)}

        facts, narrative = builder.build(
            notebook=nb,
            curriculum_kcs=kcs,
            bkt_states=bkt,
            student_context=None,
            unit_info=("Unidad 1", "Sistemas"),
        )

        # Los hechos son frozen
        with pytest.raises(FrozenInstanceError):
            facts.selected_kc = "otro_kc"

        assert facts.notebook_id == "nb_test"
        assert facts.selected_kc == "kc1"
        assert facts.bkt_estimate == 0.75
        # La narrativa menciona el nombre del cuaderno y la unidad sin contradecir
        assert "Test NB" in narrative
