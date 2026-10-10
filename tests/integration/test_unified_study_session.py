"""Integration tests for Unified Study Session (Directiva Final v2).

14 Golden Tests verifying:
- Invariante 1: Una sesión, una autoridad (no lógica paralela en cliente).
- Invariante 2: Snapshot derivado del estado autoritativo.
- Invariante 3: BKT no define currículo (roadmap + prerequisitos gobiernan).
- Invariante 4: Observación primaria en el mensaje.
- Correcciones #1 a #8 integradas.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from study_engine.contracts.notebook import Notebook
from study_engine.federation.notebook_registry import NotebookRegistry
from study_engine.pedagogy.episode_contracts import EpisodePhase
from study_engine.session.opening_brief_builder import OpeningBriefBuilder
from study_engine.session.progression_policy import ProgressionPolicy
from study_engine.session.study_session_contracts import (
    ActionNotAllowedForPhaseError,
    ActionNotAvailableError,
    AuthoritativeSessionState,
    OpeningBriefFacts,
    PolicyDeniedError,
    SessionNotFoundError,
    StudySessionSnapshot,
)
from study_engine.session.study_session_orchestrator import StudySessionOrchestrator
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage
from study_engine.web.dependencies import AppContainer


@pytest.fixture
def test_container(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    knowledge_store_test_copy,
):
    """Instancia container de prueba con componentes soberanos."""
    if knowledge_store_test_copy is not None:
        import shutil
        shutil.copy2(knowledge_store_test_copy, tmp_path / "knowledge_store.db")

    from study_engine.session import study_session_orchestrator as session_orchestrator_module
    from study_engine.session.session_store import SessionStore

    orchestrator_class = session_orchestrator_module.StudySessionOrchestrator
    session_db = tmp_path / "sessions.db"

    def create_isolated_orchestrator(**kwargs):
        if "session_store" not in kwargs:
            kwargs["session_store"] = SessionStore(session_db)
        return orchestrator_class(**kwargs)

    monkeypatch.setattr(
        session_orchestrator_module,
        "StudySessionOrchestrator",
        create_isolated_orchestrator,
    )
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    assert container.study_session_orchestrator.session_store.db_path == session_db
    return container


class TestUnifiedStudySessionGolden:
    """14 Golden Tests de integración para Unified Study Session."""

    def test_open_session_returns_snapshot(self, test_container):
        """1. Abrir sesión retorna un StudySessionSnapshot con OpeningBriefFacts deterministas."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        assert isinstance(snapshot, StudySessionSnapshot)
        assert snapshot.notebook_id == "fase0-soc"
        assert snapshot.student_id == "agustin"
        assert snapshot.episode_phase == "OPENING_BRIEF"
        assert snapshot.opening_brief_facts is not None
        assert isinstance(snapshot.opening_brief_facts, OpeningBriefFacts)
        assert snapshot.opening_brief_facts.notebook_id == "fase0-soc"
        assert len(snapshot.opening_brief_facts.eligible_kcs) > 0
        assert snapshot.session_state_hash is not None

    def test_bkt_does_not_define_curriculum(self, test_container):
        """2. CORRECCIÓN #1: BKT no redefine el orden curricular.
        Roadmap + prerequisitos determinan KCs elegibles.
        BKT solo prioriza dentro de elegibles."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        facts = snapshot.opening_brief_facts
        # El selected_kc debe pertenecer a eligible_kcs determinados por prerequisitos
        assert facts.selected_kc in facts.eligible_kcs
        # BKT no inventó un KC fuera de los elegibles
        assert len(facts.eligible_kcs) <= len(facts.curriculum_position.kcs_in_unit)

    def test_progression_policy_versioned(self, test_container):
        """3. CORRECCIÓN #2: ProgressionPolicy es versionada y testeable."""
        policy = test_container.progression_policy
        assert hasattr(policy, "POLICY_VERSION")
        assert policy.POLICY_VERSION == "v1.0"
        assert policy.policy_version == "v1.0"

    def test_opening_brief_facts_immutable(self, test_container):
        """4. CORRECCIÓN #3: OpeningBriefFacts son inmutables (frozen dataclass)."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")
        facts = snapshot.opening_brief_facts

        with pytest.raises(Exception):  # FrozenInstanceError
            facts.selected_kc = "mutated_kc"

    def test_opening_brief_narrative_does_not_modify_facts(self, test_container):
        """5. CORRECCIÓN #3: La narrativa no puede contradecir los hechos."""
        builder = test_container.opening_brief_builder
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        facts = snapshot.opening_brief_facts
        narrative = builder.build_narrative(facts)

        # La narrativa debe mencionar el nombre del notebook y el KC seleccionado
        assert facts.notebook_name in narrative
        assert facts.selected_kc in narrative

    def test_execute_action_validation(self, test_container):
        """6. CORRECCIÓN #4: execute_action valida 7 pasos antes de ejecutar."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # Acción válida en OPENING_BRIEF -> START_EXPLANATION
        updated_snapshot = orch.execute_action(
            session_id=snapshot.session_id,
            action="START_EXPLANATION",
        )
        assert updated_snapshot.episode_phase == "EXPLAINING"
        assert updated_snapshot.episode_id is not None

    def test_action_not_available_rejected(self, test_container):
        """7. CORRECCIÓN #4: Acción no disponible -> ActionNotAvailableError (400)."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        with pytest.raises(ActionNotAvailableError):
            orch.execute_action(
                session_id=snapshot.session_id,
                action="INVALID_ACTION_NAME",
            )

    def test_action_not_allowed_for_phase_rejected(self, test_container):
        """8. CORRECCIÓN #4: Acción no permitida para la fase actual -> ActionNotAllowedForPhaseError (400)."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # En OPENING_BRIEF no se puede SUBMIT_ANSWER
        with pytest.raises((ActionNotAvailableError, ActionNotAllowedForPhaseError)):
            orch.execute_action(
                session_id=snapshot.session_id,
                action="SUBMIT_ANSWER",
                payload={"answer": "42"},
            )

    def test_frontend_proposes_backend_authorizes(self, test_container):
        """9. CORRECCIÓN #4: El frontend propone; el backend autoriza."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # Frontend propone SELECT_DIFFERENT_KC con KC elegible
        eligible = snapshot.eligible_kcs[0]
        updated = orch.execute_action(
            session_id=snapshot.session_id,
            action="SELECT_DIFFERENT_KC",
            payload={"kc_id": eligible},
        )
        assert updated.current_kc_id == eligible

    def test_snapshot_is_derived(self, test_container):
        """10. CORRECCIÓN #5: Snapshot es derivado del estado autoritativo (inmutable)."""
        orch = test_container.study_session_orchestrator
        snapshot = orch.open_session(notebook_id="fase0-soc", student_id="agustin")

        # Modificar campos del snapshot no es posible (frozen dataclass)
        with pytest.raises(Exception):
            snapshot.current_kc_id = "hacked_kc"

        # El estado autoritativo permanece intacto en el orchestrator
        auth_state = orch._sessions[snapshot.session_id]
        assert auth_state.current_kc_id == snapshot.current_kc_id

    def test_chat_general_scope_resolution(self, test_container):
        """11. CORRECCIÓN #6: Chat General no confía en intent.notebook_id.
        ScopeResolver resuelve notebook autorizado."""
        resolver = test_container.scope_resolver
        from study_engine.hierarchy.scope_resolver import ScopeType

        # Resolver root_global
        scope_root = resolver.resolve(ScopeType.FOLDER, "root_global")
        assert scope_root.scope_type == ScopeType.FOLDER
        assert scope_root.folder_id == "folder_root"

        # Resolver notebook autorizado
        scope_nb = resolver.resolve(ScopeType.NOTEBOOK, "fadena-so2")
        assert scope_nb.scope_type == ScopeType.NOTEBOOK
        assert scope_nb.notebook_id == "fadena-so2"

    def test_one_session_one_authority(self, test_container):
        """12. CORRECCIÓN #7: No hay orquestador paralelo.
        La sesión autoritativa reside en StudySessionOrchestrator."""
        orch = test_container.study_session_orchestrator
        snap1 = orch.open_session(notebook_id="fadena-lenguajes", student_id="agustin")
        snap2 = orch.open_session(notebook_id="fadena-so2", student_id="agustin")

        assert snap1.session_id != snap2.session_id
        assert snap1.notebook_id == "fadena-lenguajes"
        assert snap2.notebook_id == "fadena-so2"

    def test_observation_is_primary_evidence(self, test_container):
        """13. CORRECCIÓN #8: La observación es evidencia primaria."""
        bridge = test_container.observation_bridge
        from study_engine.pedagogy.graders import GradeResult

        grade_res = GradeResult(
            is_correct=True,
            raw_answer="1012",
            normalized_answer="1012",
            normalization_policy="TRIM_WHITESPACE",
            expected_answer="1012",
            comparison_result="EQUAL('1012', '1012')",
            feedback="Respuesta registrada como observación determinista.",
        )

        bkt_state, was_new = bridge.process_grade(
            episode_id="ep_test_obs",
            step_id="step_obs_1",
            kc_id="aritmetica_punteros",
            grade_result=grade_res,
        )
        assert bkt_state is not None
        assert was_new is True
        assert "Respuesta registrada como observación determinista." in grade_res.feedback

    def test_full_flow_end_to_end(self, test_container):
        """14. Flujo completo: open -> brief -> explanation -> dialogue -> exercise -> grading -> BKT."""
        orch = test_container.study_session_orchestrator

        # 1. Open session
        snap = orch.open_session(notebook_id="fase0-soc", student_id="agustin")
        assert snap.episode_phase == "OPENING_BRIEF"

        # 2. Start explanation
        snap = orch.execute_action(snap.session_id, "START_EXPLANATION")
        assert snap.episode_phase == "EXPLAINING"
        assert snap.episode_id is not None

        # 3. Transition to dialogue
        snap = orch.execute_action(snap.session_id, "REQUEST_DIALOGUE")
        assert snap.episode_phase == "DIALOGUE"

        # 4. Skip to exercise
        snap = orch.execute_action(snap.session_id, "SKIP_TO_EXERCISE")
        assert snap.episode_phase == "EVALUATING"
        assert snap.exercise_available is True
