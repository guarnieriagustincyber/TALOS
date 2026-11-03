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
            session_id="session-test-obs",
            episode_id="ep_test_obs",
            step_id="step_obs_1",
            exercise_id="exercise-test-obs",
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


@pytest.mark.parametrize("answer, correct", [("42", True), ("17", False)])
def test_front_b_api_learning_cycle_persists(tmp_path, answer, correct):
    """Real API/services/SQLite; agent-authored synthetic corpus; only NLI is simulated.

    Proves the session-action grading link, persisted BKT and next intervention,
    not real semantic NLI, SM-2, formal mastery or full Meta 1 acceptance.
    """
    import hashlib
    import json
    from types import SimpleNamespace
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from study_engine.audit.auditor import ForensicAuditor
    from study_engine.audit.nli import MockNLIJudge
    from study_engine.contracts.catalog import SourceRecord
    from study_engine.contracts.ingestion import SourceManifest
    from study_engine.contracts.document import Document
    from study_engine.contracts.chunk import Chunk
    from study_engine.federation.notebook_registry import Notebook as RegistryNotebook
    from study_engine.pedagogy.bridge import ObservationBridge
    from study_engine.pedagogy.concept_builder import ConceptPacketBuilder
    from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler
    from study_engine.pedagogy.exercise_contracts import ExerciseCandidate, ExerciseType, ExerciseVerificationStatus
    from study_engine.pedagogy.exercise_store import ExerciseStore
    from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
    from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
    from study_engine.session.session_store import SessionStore
    from study_engine.student.bkt_tracker import BKTTracker
    from study_engine.web.dependencies import get_container
    from study_engine.web.routes import pedagogy, study_session

    nb, kc, source = "synthetic-front-b", "synthetic-pointers", "synthetic-source"
    texts = [
        "Los punteros contienen direcciones de memoria que identifican objetos almacenados durante la ejecución del programa.",
        "Los punteros permiten acceder a los objetos almacenados mediante sus direcciones de memoria dentro del programa.",
    ]
    source_hash = hashlib.sha256("\n".join(texts).encode()).hexdigest()
    knowledge = KnowledgeStore(tmp_path / "knowledge.db")
    knowledge.initialize()
    knowledge.create_notebook(Notebook(id=nb, name="Synthetic pointers"))
    chunks = [Chunk(id=f"synthetic-chunk-{i}", document_id="synthetic-doc", source_id=source,
                    content=text, page_start=i + 1, page_end=i + 1, index=i) for i, text in enumerate(texts)]
    knowledge.store_ingestion_bundle(
        SourceRecord(source_id=source, manifest=SourceManifest(source_id=source, filename="synthetic.txt",
                     byte_size=len("\n".join(texts).encode()), sha256=source_hash)),
        [Document(id="synthetic-doc", source_id=source, title="Synthetic pointers", content="\n".join(texts))],
        chunks, notebook_id=nb,
    )
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({nb: {"name": "Synthetic pointers", "kcs": [
        {"kc_id": kc, "title": "punteros", "unit": 1, "prerequisites": []},
    ]}}))
    roles = tmp_path / "roles.json"
    roles.write_text(json.dumps({nb: {source: {"roles": ["PRIMARY"], "title": "Synthetic pointers"}}}))
    registry = NotebookRegistry(initial_notebooks=[RegistryNotebook(
        notebook_id=nb, name="Synthetic pointers", subject="Synthetic programming", sources=[source],
    )])
    exercises = ExerciseStore(tmp_path / "exercises.json")
    prompt = "¿Cuál es el desplazamiento en bytes de siete elementos de seis bytes cada uno?"
    exercises.add_exercise(ExerciseCandidate(
        exercise_id="synthetic-exercise", source_id=source, source_location="Synthetic fixture page 1",
        source_hash=source_hash, extractor_version="synthetic-v1", extraction_method="synthetic-fixture",
        verification_status=ExerciseVerificationStatus.QUALIFIABLE, verified_by="synthetic-fixture",
        verification_timestamp=None, content_hash=hashlib.sha256(prompt.encode()).hexdigest(),
        kc_id=kc, prompt=prompt, exercise_type=ExerciseType.NUMERIC, expected_answer="42",
    ), persist=False)
    assembler = MultiSourceEvidenceAssembler(knowledge, roles_config_path=roles)

    def build_container():
        storage = StudentStorage(tmp_path / "academic.db")
        tracker = BKTTracker(storage)
        sessions = SessionStore(tmp_path / "sessions.db")
        orchestrator = PedagogicalOrchestrator(
            registry, assembler, ConceptPacketBuilder(), ForensicAuditor(nli_judge=MockNLIJudge()),
            exercises, tracker, catalog_path=catalog, episode_store=sessions,
        )
        session_orchestrator = StudySessionOrchestrator(registry, orchestrator, student_storage=storage, session_store=sessions)
        return SimpleNamespace(
            student_storage=storage, bkt_tracker=tracker, exercise_store=exercises,
            pedagogical_orchestrator=orchestrator, study_session_orchestrator=session_orchestrator,
            observation_bridge=ObservationBridge(tracker), exact_grader=ExactMatchGrader(), mc_grader=MultiChoiceGrader(),
        )

    container = build_container()
    app = FastAPI()
    app.include_router(study_session.router)
    app.include_router(pedagogy.router)
    app.dependency_overrides[get_container] = lambda: container
    try:
        with TestClient(app) as client:
            opened = client.post("/api/study/session/open", json={"notebook_id": nb})
            assert opened.status_code == 200, opened.text
            sid = opened.json()["session_id"]
            base = f"/api/study/session/{sid}"
            started = client.post(base + "/action", json={"action": "START_EXPLANATION"})
            assert started.status_code == 200, started.text
            episode_id = started.json()["episode_id"]
            explanation = client.get(f"/api/pedagogy/episode/{episode_id}/concept")
            assert explanation.status_code == 200, explanation.text
            concept = explanation.json()
            assert concept["status"] == "PRESENTABLE", concept
            assert concept["audit_verdict"] == "APPROVED"
            citations = concept["packet"]["citations"]
            assert len(citations) == 2
            for citation in citations:
                chunk = next(c for c in chunks if c.id == citation["chunk_id"])
                assert citation["document_id"] == chunk.document_id
                assert citation["page_start"] == chunk.page_start
                assert citation["content_hash"] == hashlib.sha256(chunk.content.encode()).hexdigest()
            intervention = client.get(f"/api/pedagogy/episode/{episode_id}/next")
            assert intervention.status_code == 200, intervention.text
            assert intervention.json()["exercise"]["exercise_id"] == "synthetic-exercise"
            prior = container.bkt_tracker.get_state(kc).p_L
            request = {"action": "SUBMIT_ANSWER", "payload": {"answer": answer}}
            submitted = client.post(base + "/action", json=request)
            assert submitted.status_code == 200, submitted.text
            result = submitted.json()
            evaluation = result["evaluation"]
            assert evaluation["is_correct"] is correct
            assert evaluation["bkt_update"]["kc_id"] == kc
            assert evaluation["bkt_update"]["attempts"] == 1
            after = evaluation["bkt_update"]["p_L"]
            assert (after > prior) if correct else (after <= prior)
            assert result["bkt_estimate"] == after
            assert evaluation["next_eligible_action"]["recommendation"] == ("ADVANCE" if correct else "REINFORCE")
            assert evaluation["next_eligible_action"]["current_p_L"] == after
            assert container.student_storage.get_bkt_state(kc).attempts == 1

        container.student_storage.close()
        container.study_session_orchestrator.session_store.close()
        container = build_container()  # New objects: no in-memory session, episode or BKT reuse.
        with TestClient(app) as client:
            restored = client.get(base + "/snapshot")
            assert restored.status_code == 200, restored.text
            assert restored.json()["episode_id"] == episode_id
            assert restored.json()["bkt_estimate"] == after
            repeated = client.post(base + "/action", json=request)
            assert repeated.status_code == 200, repeated.text
            assert repeated.json()["evaluation"]["was_idempotent_replay"] is True
            assert container.bkt_tracker.get_state(kc).attempts == 1
            conflicting = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "43"}})
            assert conflicting.status_code == 409
            assert container.bkt_tracker.get_state(kc).attempts == 1
    finally:
        container.student_storage.close()
        container.study_session_orchestrator.session_store.close()
        knowledge.close()


@pytest.fixture
def curricular_api(tmp_path):
    """Real session, graders and stores; synthetic curriculum; no semantic/provider calls."""
    import hashlib
    import json
    from types import SimpleNamespace
    from fastapi import FastAPI
    from study_engine.audit.auditor import ForensicAuditor
    from study_engine.audit.nli import UnavailableNLIJudge
    from study_engine.federation.notebook_registry import Notebook as RegistryNotebook
    from study_engine.pedagogy.bridge import ObservationBridge
    from study_engine.pedagogy.concept_builder import ConceptPacketBuilder
    from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler
    from study_engine.pedagogy.exercise_contracts import ExerciseCandidate, ExerciseType, ExerciseVerificationStatus
    from study_engine.pedagogy.exercise_store import ExerciseStore
    from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
    from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
    from study_engine.session.session_store import SessionStore
    from study_engine.student.bkt_tracker import BKTTracker
    from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
    from study_engine.web.dependencies import get_container
    from study_engine.web.routes import pedagogy, study_session, student, dialogue

    catalog = tmp_path / "curriculum.json"
    catalog.write_text(json.dumps({"synthetic": {"kcs": [
        {"kc_id": "first", "title": "First concept", "prerequisites": []},
        {"kc_id": "second", "title": "Second concept", "prerequisites": ["first"]},
    ]}}))
    registry = NotebookRegistry(initial_notebooks=[RegistryNotebook(
        notebook_id="synthetic", name="Synthetic", subject="Synthetic", sources=[],
    )])
    exercises = ExerciseStore(tmp_path / "exercises.json")
    for kc in ("first", "second"):
        prompt = f"Synthetic numeric question for {kc}"
        exercises.add_exercise(ExerciseCandidate(
            exercise_id=f"exercise-{kc}", source_id="synthetic-fixture", source_location="synthetic fixture",
            source_hash=hashlib.sha256(b"synthetic fixture").hexdigest(), extractor_version="synthetic",
            extraction_method="synthetic", verification_status=ExerciseVerificationStatus.QUALIFIABLE,
            verified_by="synthetic", verification_timestamp=None, content_hash=hashlib.sha256(prompt.encode()).hexdigest(),
            kc_id=kc, prompt=prompt, exercise_type=ExerciseType.NUMERIC, expected_answer="42",
        ), persist=False)

    containers = []
    def build():
        storage = StudentStorage(tmp_path / "academic.db")
        sessions = SessionStore(tmp_path / "sessions.db")
        tracker = BKTTracker(storage)
        pedagogical = PedagogicalOrchestrator(
            registry, MultiSourceEvidenceAssembler(roles_config_path=tmp_path / "no-roles.json"),
            ConceptPacketBuilder(), ForensicAuditor(nli_judge=UnavailableNLIJudge()), exercises, tracker,
            catalog_path=catalog, episode_store=sessions,
        )
        container = SimpleNamespace(
            student_storage=storage, bkt_tracker=tracker, exercise_store=exercises,
            pedagogical_orchestrator=pedagogical,
            study_session_orchestrator=StudySessionOrchestrator(registry, pedagogical, storage, session_store=sessions),
            observation_bridge=ObservationBridge(tracker), exact_grader=ExactMatchGrader(), mc_grader=MultiChoiceGrader(),
            spaced_scheduler=SpacedRepetitionScheduler(storage),
        )
        containers.append(container)
        return container

    current = [build()]
    app = FastAPI()
    app.include_router(study_session.router)
    app.include_router(pedagogy.router)
    app.include_router(student.router)
    app.include_router(dialogue.router)
    app.dependency_overrides[get_container] = lambda: current[0]
    yield app, current, build
    for container in containers:
        container.student_storage.close()
        container.study_session_orchestrator.session_store.close()


def begin_curricular_attempt(client):
    opened = client.post("/api/study/session/open", json={"notebook_id": "synthetic"})
    assert opened.status_code == 200, opened.text
    base = f"/api/study/session/{opened.json()['session_id']}"
    started = client.post(base + "/action", json={"action": "START_EXPLANATION"})
    assert started.status_code == 200, started.text
    episode = started.json()["episode_id"]
    # No corpus: explanation abstains honestly. This test targets curricular continuation only.
    intervention = client.get(f"/api/pedagogy/episode/{episode}/next")
    assert intervention.status_code == 200, intervention.text
    return base, episode


def test_curricular_advance_confirmation_restore_and_replay(curricular_api):
    from fastapi.testclient import TestClient
    app, current, build = curricular_api
    with TestClient(app) as client:
        base, episode = begin_curricular_attempt(client)
        evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert evaluated.status_code == 200, evaluated.text
        assert evaluated.json()["current_kc_id"] == "first"  # No automatic advance.
        request = {"action": "START_NEXT_KC", "payload": {"episode_id": episode, "kc_id": "first"}}
        advanced = client.post(base + "/action", json=request)
        assert advanced.status_code == 200, advanced.text
        state = advanced.json()
        assert state["current_kc_id"] == "second" and state["episode_id"] is None
        assert state["opening_brief_facts"]["selected_kc"] == "second"
        assert state["curriculum_position"]["kcs_completed"] == ["first"]
        assert client.post(base + "/action", json=request).status_code == 400
    current[0] = build()
    with TestClient(app) as client:
        restored = client.get(base + "/snapshot")
        assert restored.status_code == 200
        assert restored.json()["current_kc_id"] == "second"
        assert restored.json()["session_state_hash"] == state["session_state_hash"]
        next_episode = client.post(base + "/action", json={"action": "START_EXPLANATION"})
        assert next_episode.status_code == 200, next_episode.text
        next_id = next_episode.json()["episode_id"]
        intervention = client.get(f"/api/pedagogy/episode/{next_id}/next")
        assert intervention.status_code == 200, intervention.text
        assert intervention.json()["exercise"]["kc_id"] == "second"
        assert current[0].bkt_tracker.get_state("first").attempts == 1
        assert current[0].bkt_tracker.get_state("second").attempts == 0


@pytest.mark.parametrize("case", ["insufficient", "incorrect", "prerequisite", "identity", "ungraded"])
def test_curricular_advance_rejects_without_partial_state(curricular_api, case):
    from fastapi.testclient import TestClient
    app, current, _ = curricular_api
    with TestClient(app) as client:
        base, episode = begin_curricular_attempt(client)
        tracker = current[0].bkt_tracker
        if case in ("insufficient", "incorrect"):
            # Synthetic priors isolate progression from already-tested BKT arithmetic.
            prior = tracker.get_state("first").model_copy(update={"p_L": 0.001 if case == "insufficient" else 0.999, "attempts": 1})
            tracker.save_state(prior)
        if case != "ungraded":
            evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "17" if case == "incorrect" else "42"}})
            assert evaluated.status_code == 200, evaluated.text
            if case in ("incorrect", "insufficient"):
                assert evaluated.json()["evaluation"]["next_eligible_action"]["recommendation"] == "REINFORCE"
        if case == "prerequisite":
            current[0].pedagogical_orchestrator._kc_catalog["synthetic"]["kcs"][1]["prerequisites"].append("missing-prerequisite")
        before = client.get(base + "/snapshot").json()
        denied = client.post(base + "/action", json={"action": "START_NEXT_KC", "payload": {
            "episode_id": episode, "kc_id": "wrong" if case == "identity" else "first",
        }})
        assert denied.status_code == 403, denied.text
        after = client.get(base + "/snapshot").json()
        assert after["current_kc_id"] == "first" and after["session_state_hash"] == before["session_state_hash"]


def test_curricular_advance_failed_write_is_atomic(curricular_api, monkeypatch):
    from fastapi.testclient import TestClient
    app, current, build = curricular_api
    with TestClient(app, raise_server_exceptions=False) as client:
        base, episode = begin_curricular_attempt(client)
        evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert evaluated.status_code == 200, evaluated.text
        before = client.get(base + "/snapshot").json()
        def fail_advance(state):
            if state["current_kc_id"] == "second":
                raise OSError("Synthetic persistence failure")
            return original(state)
        store = current[0].study_session_orchestrator.session_store
        original = store.upsert
        monkeypatch.setattr(store, "upsert", fail_advance)
        failed = client.post(base + "/action", json={"action": "START_NEXT_KC", "payload": {"episode_id": episode, "kc_id": "first"}})
        assert failed.status_code == 500
        assert client.get(base + "/snapshot").json()["session_state_hash"] == before["session_state_hash"]
    current[0] = build()
    with TestClient(app) as client:
        restored = client.get(base + "/snapshot").json()
        assert restored["current_kc_id"] == "first" and restored["episode_id"] == episode


@pytest.fixture
def sm2_clock(monkeypatch):
    from study_engine.student import contracts
    from study_engine.web.routes import student

    class Clock(datetime):
        current = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls.current.astimezone(tz) if tz is not None else cls.current.replace(tzinfo=None)

    monkeypatch.setattr(contracts, "datetime", Clock)
    monkeypatch.setattr(student, "datetime", Clock)
    return Clock


@pytest.mark.parametrize("kind, answer, quality", [("NUMERIC", "42", 5), ("NUMERIC", "17", 1), ("MC", "A", 4)])
def test_sm2_api_grade_agenda_restore_and_replay(curricular_api, sm2_clock, kind, answer, quality):
    from dataclasses import replace
    from datetime import timedelta
    from fastapi.testclient import TestClient
    from study_engine.pedagogy.exercise_contracts import ExerciseType

    app, current, build = curricular_api
    scheduler = current[0].spaced_scheduler
    base_time = sm2_clock.current
    # Synthetic persisted history: the next legitimate success must use interval 6.
    scheduler.schedule_review("first", quality=4, as_of=base_time - timedelta(days=10))
    scheduler.schedule_review("future-control", quality=4, as_of=base_time + timedelta(days=10))
    if kind == "MC":
        exercise = current[0].exercise_store.get_exercise_by_id("exercise-first")
        current[0].exercise_store.add_exercise(replace(exercise, exercise_type=ExerciseType.MC,
            options=("A", "B", "C", "D"), expected_answer="A"), persist=False)
    with TestClient(app) as client:
        base, episode = begin_curricular_attempt(client)
        prior = current[0].bkt_tracker.get_state("first").p_L
        request = {"action": "SUBMIT_ANSWER", "payload": {"answer": answer}}
        evaluated = client.post(base + "/action", json=request)
        assert evaluated.status_code == 200, evaluated.text
        bkt = evaluated.json()["evaluation"]["bkt_update"]
        assert bkt["attempts"] == 1
        assert (bkt["p_L"] <= prior) if quality == 1 else (bkt["p_L"] > prior)
        saved = scheduler.storage.get_anchor_state("first")
        assert saved.last_quality == quality
        assert saved.interval == (1 if quality == 1 else 6)
        assert saved.repetitions == (0 if quality == 1 else 2)
        assert saved.EF == pytest.approx({1: 1.96, 4: 2.5, 5: 2.6}[quality])
        assert saved.updated_at == base_time
        assert saved.next_review == base_time + timedelta(days=saved.interval)
        agenda = client.get("/api/student/spaced-repetition/due")
        assert agenda.status_code == 200, agenda.text
        assert all(item["is_due"] is False for item in agenda.json())
    current[0] = build()
    sm2_clock.current = saved.next_review  # Due is inclusive at the scheduled timestamp.
    with TestClient(app) as client:
        restored = client.get(base + "/snapshot")
        assert restored.status_code == 200 and restored.json()["episode_id"] == episode
        assert current[0].spaced_scheduler.storage.get_anchor_state("first") == saved
        replay = client.post(base + "/action", json=request)
        assert replay.status_code == 200, replay.text
        assert replay.json()["evaluation"]["was_idempotent_replay"] is True
        assert current[0].spaced_scheduler.storage.get_anchor_state("first") == saved
        assert current[0].bkt_tracker.get_state("first").attempts == 1
        agenda = {item["anchor_id"]: item for item in client.get("/api/student/spaced-repetition/due").json()}
        assert agenda["first"]["is_due"] is True
        assert agenda["future-control"]["is_due"] is False
        assert agenda["first"]["due_date"] == saved.next_review.isoformat()


def test_sm2_api_invalid_observation_does_not_schedule(curricular_api, sm2_clock):
    from fastapi.testclient import TestClient
    app, current, _ = curricular_api
    with TestClient(app) as client:
        base, episode = begin_curricular_attempt(client)
        invalid = client.post(f"/api/pedagogy/episode/{episode}/respond", json={
            "session_id": "wrong-session", "step_id": "step_eval_exercise-first", "response_text": "42",
        })
        assert invalid.status_code == 409
        assert client.get("/api/student/spaced-repetition/due").json() == []
        assert current[0].bkt_tracker.get_state("first").attempts == 0


def test_sm2_api_persistence_failure_rolls_back_learning(curricular_api, sm2_clock, monkeypatch):
    from fastapi.testclient import TestClient
    app, current, _ = curricular_api
    storage = current[0].student_storage
    original = storage.save_anchor_state
    def fail_after_write(state):
        original(state)
        raise OSError("Synthetic agenda persistence failure after SQL write")
    with TestClient(app, raise_server_exceptions=False) as client:
        base, episode = begin_curricular_attempt(client)
        before = client.get(base + "/snapshot").json()["session_state_hash"]
        monkeypatch.setattr(storage, "save_anchor_state", fail_after_write)
        failed = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert failed.status_code == 500
        assert storage.get_anchor_state("first") is None
        assert storage.get_bkt_state("first") is None
        assert storage.get_operation_receipt(session_id=base.split("/")[-1], episode_id=episode,
            exercise_id="exercise-first", attempt_id="step_eval_exercise-first") is None
        assert client.get(base + "/snapshot").json()["session_state_hash"] == before
        monkeypatch.setattr(storage, "save_anchor_state", original)
        retried = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert retried.status_code == 200, retried.text
        assert storage.get_anchor_state("first").repetitions == 1
        assert storage.get_bkt_state("first").attempts == 1


def test_sm2_api_exact_prose_does_not_invent_recall_quality(curricular_api, sm2_clock):
    from dataclasses import replace
    from fastapi.testclient import TestClient
    from study_engine.pedagogy.exercise_contracts import ExerciseType
    app, current, _ = curricular_api
    exercise = current[0].exercise_store.get_exercise_by_id("exercise-first")
    current[0].exercise_store.add_exercise(replace(exercise, exercise_type=ExerciseType.EXACT_TEXT,
        expected_answer="texto exacto"), persist=False)
    with TestClient(app) as client:
        base, _ = begin_curricular_attempt(client)
        result = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "texto exacto"}})
        assert result.status_code == 200, result.text
        assert result.json()["evaluation"]["is_correct"] is True
        assert current[0].student_storage.get_anchor_state("first") is None


def test_session_close_archive_preserves_learning_and_continuity(curricular_api, sm2_clock, monkeypatch):
    from datetime import timedelta
    from fastapi.testclient import TestClient
    from study_engine.session import session_store
    app, current, build = curricular_api
    monkeypatch.setattr(session_store, "datetime", sm2_clock)
    with TestClient(app) as client:
        base, episode_id = begin_curricular_attempt(client)
        evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert evaluated.status_code == 200, evaluated.text
        sid = base.split("/")[-1]
        before = client.get(base + "/snapshot").json()
        storage = current[0].student_storage
        bkt = storage.get_bkt_state("first")
        agenda = storage.get_all_anchor_states()
        history = current[0].pedagogical_orchestrator.get_episode(episode_id)
        receipt = storage.get_operation_receipt(session_id=sid, episode_id=episode_id,
            exercise_id="exercise-first", attempt_id="step_eval_exercise-first")
        closed = client.post(base + "/close")
        assert closed.status_code == 200, closed.text
        state = closed.json()
        assert state["episode_phase"] == "CLOSED" and state["available_actions"] == []
        assert state["current_kc_id"] == before["current_kc_id"] == "first"
        assert state["episode_id"] == episode_id
        store = current[0].study_session_orchestrator.session_store
        first_row = tuple(store._get_conn().execute("SELECT * FROM study_sessions WHERE session_id = ?", (sid,)).fetchone())
        sm2_clock.current += timedelta(days=2)
        repeated = client.post(base + "/close")
        assert repeated.status_code == 200
        assert repeated.json()["session_state_hash"] == state["session_state_hash"]
        assert tuple(store._get_conn().execute("SELECT * FROM study_sessions WHERE session_id = ?", (sid,)).fetchone()) == first_row
        assert client.post(base + "/action", json={"action": "START_NEXT_KC", "payload": {
            "episode_id": episode_id, "kc_id": "first",
        }}).status_code == 400
        assert client.post(f"/api/pedagogy/episode/{episode_id}/respond", json={
            "session_id": sid, "step_id": "step_eval_exercise-first", "response_text": "17",
        }).status_code == 404
        assert client.get(f"/api/pedagogy/episode/{episode_id}/next").status_code == 409
        assert client.post(f"/api/pedagogy/episode/{episode_id}/dialogue", json={"message": "continue"}).status_code == 409
        assert client.post(f"/api/pedagogy/episode/{episode_id}/dialogue/accept-exercise").status_code == 409
        assert client.post(f"/api/pedagogy/episode/{episode_id}/dialogue/reject-exercise").status_code == 409
    current[0] = build()
    assert sid not in current[0].study_session_orchestrator._sessions
    with TestClient(app) as client:
        archived = client.get(base + "/snapshot")
        assert archived.status_code == 200, archived.text
        assert archived.json()["session_state_hash"] == state["session_state_hash"]
        assert archived.json()["episode_phase"] == "CLOSED"
        assert client.post(base + "/close").status_code == 200
        assert current[0].student_storage.get_bkt_state("first") == bkt
        assert current[0].student_storage.get_all_anchor_states() == agenda
        assert current[0].pedagogical_orchestrator.get_episode(episode_id) == history
        assert current[0].student_storage.get_operation_receipt(session_id=sid, episode_id=episode_id,
            exercise_id="exercise-first", attempt_id="step_eval_exercise-first") == receipt
        assert len(client.get("/api/student/spaced-repetition/due").json()) == 1
        opened = client.post("/api/study/session/open", json={"notebook_id": "synthetic"})
        assert opened.status_code == 200, opened.text
        assert opened.json()["session_id"] != sid
        assert opened.json()["current_kc_id"] == "second"
        assert client.get(base + "/snapshot").json()["episode_phase"] == "CLOSED"
        assert current[0].student_storage.get_all_anchor_states() == agenda


def test_session_close_sql_failure_is_atomic(curricular_api, sm2_clock):
    from fastapi.testclient import TestClient
    app, current, build = curricular_api
    with TestClient(app, raise_server_exceptions=False) as client:
        base, episode = begin_curricular_attempt(client)
        sid = base.split("/")[-1]
        before = client.get(base + "/snapshot").json()
        store = current[0].study_session_orchestrator.session_store
        connection = store._get_conn()
        connection.executescript("""
            CREATE TRIGGER synthetic_close_failure AFTER UPDATE ON study_sessions
            WHEN NEW.is_closed = 1 BEGIN SELECT RAISE(ABORT, 'synthetic closure failure'); END;
        """)
        failed = client.post(base + "/close")
        assert failed.status_code == 500
        assert store.load_session(sid)["episode_phase"] == "EVALUATING"
        assert client.get(base + "/snapshot").json()["session_state_hash"] == before["session_state_hash"]
    current[0] = build()
    with TestClient(app) as client:
        restored = client.get(base + "/snapshot").json()
        assert restored["episode_phase"] == "EVALUATING" and restored["episode_id"] == episode
        connection.execute("DROP TRIGGER synthetic_close_failure")
        connection.commit()
        assert client.post(base + "/close").status_code == 200


def test_session_close_does_not_close_other_sessions_or_alias_students(curricular_api, sm2_clock):
    from fastapi.testclient import TestClient
    app, current, _ = curricular_api
    with TestClient(app) as client:
        first = client.post("/api/study/session/open", json={"notebook_id": "synthetic"}).json()
        second = client.post("/api/study/session/open", json={"notebook_id": "synthetic"}).json()
        assert first["session_id"] != second["session_id"]
        assert client.post(f"/api/study/session/{first['session_id']}/close").status_code == 200
        other = client.get(f"/api/study/session/{second['session_id']}/snapshot").json()
        assert other["episode_phase"] == "OPENING_BRIEF"
        assert other["session_state_hash"] == second["session_state_hash"]
        store = current[0].study_session_orchestrator.session_store
        before = store.load_all_active()
        for student in ("synthetic-student-A", "synthetic-student-B"):
            rejected = client.post("/api/study/session/open", json={"notebook_id": "synthetic", "student_id": student})
            assert rejected.status_code == 403
        assert store.load_all_active() == before


def begin_last_curricular_attempt(client):
    """Reach the terminal branch through the existing, directly affected advance path."""
    base, first_episode = begin_curricular_attempt(client)
    evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
    assert evaluated.status_code == 200, evaluated.text
    assert evaluated.json()["curriculum_completed"] is False
    advanced = client.post(base + "/action", json={"action": "START_NEXT_KC", "payload": {
        "episode_id": first_episode, "kc_id": "first",
    }})
    assert advanced.status_code == 200, advanced.text
    assert advanced.json()["current_kc_id"] == "second"
    assert advanced.json()["curriculum_completed"] is False
    started = client.post(base + "/action", json={"action": "START_EXPLANATION"})
    assert started.status_code == 200, started.text
    episode = started.json()["episode_id"]
    intervention = client.get(f"/api/pedagogy/episode/{episode}/next")
    assert intervention.status_code == 200, intervention.text
    assert intervention.json()["exercise"]["kc_id"] == "second"
    return base, episode


def test_terminal_curriculum_confirmation_restore_and_closed_session(curricular_api, sm2_clock, monkeypatch):
    from fastapi.testclient import TestClient
    from unittest.mock import Mock
    app, current, build = curricular_api
    with TestClient(app) as client:
        base, episode = begin_last_curricular_attempt(client)
        evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert evaluated.status_code == 200, evaluated.text
        recommendation = evaluated.json()["evaluation"]["next_eligible_action"]
        assert recommendation["recommendation"] == "ADVANCE" and recommendation["next_kc_id"] is None
        storage = current[0].student_storage
        bkt, agenda = storage.get_all_bkt_states(), storage.get_all_anchor_states()
        sid = base.split("/")[-1]
        store = current[0].study_session_orchestrator.session_store
        upsert = Mock(wraps=store.upsert)
        monkeypatch.setattr(store, "upsert", upsert)
        request = {"action": "START_NEXT_KC", "payload": {"episode_id": episode, "kc_id": "second"}}
        completed = client.post(base + "/action", json=request)
        assert completed.status_code == 200, completed.text
        state = completed.json()
        assert state["curriculum_completed"] is True
        assert state["current_kc_id"] == "second" and state["episode_id"] == episode
        assert state["episode_phase"] == "EVALUATING"  # Completion is not session closure.
        assert set(state["curriculum_position"]["kcs_completed"]) == {"first", "second"}
        persisted = store.load_session(sid)
        assert upsert.call_count == 1
        replay = client.post(base + "/action", json=request)
        assert replay.status_code == 200 and replay.json()["curriculum_completed"] is True
        assert replay.json()["session_state_hash"] == state["session_state_hash"]
        assert upsert.call_count == 1 and store.load_session(sid) == persisted
        assert storage.get_all_bkt_states() == bkt and storage.get_all_anchor_states() == agenda
    current[0] = build()
    with TestClient(app) as client:
        restored = client.get(base + "/snapshot")
        assert restored.status_code == 200, restored.text
        assert restored.json()["curriculum_completed"] is True
        assert restored.json()["session_state_hash"] == state["session_state_hash"]
        assert current[0].student_storage.get_all_bkt_states() == bkt
        assert current[0].student_storage.get_all_anchor_states() == agenda
        closed = client.post(base + "/close")
        assert closed.status_code == 200 and closed.json()["episode_phase"] == "CLOSED"
        assert closed.json()["curriculum_completed"] is True
        assert client.post(base + "/action", json=request).status_code == 400


@pytest.mark.parametrize("case", ["insufficient", "incorrect", "prerequisite", "earlier-pending", "invalid-catalog"])
def test_terminal_curriculum_blocked_is_not_completion(curricular_api, sm2_clock, case):
    from fastapi.testclient import TestClient
    app, current, _ = curricular_api
    with TestClient(app) as client:
        base, episode = begin_last_curricular_attempt(client)
        tracker = current[0].bkt_tracker
        if case == "insufficient":
            tracker.save_state(tracker.get_state("second").model_copy(update={"p_L": 0.001, "attempts": 1}))
        evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "17" if case == "incorrect" else "42"}})
        assert evaluated.status_code == 200, evaluated.text
        if case == "prerequisite":
            current[0].pedagogical_orchestrator._kc_catalog["synthetic"]["kcs"][1]["prerequisites"].append("missing")
        elif case == "earlier-pending":
            tracker.save_state(tracker.get_state("first").model_copy(update={"p_L": 0.7}))
        elif case == "invalid-catalog":
            current[0].pedagogical_orchestrator._kc_catalog["synthetic"]["kcs"] = []
            recommendation = current[0].pedagogical_orchestrator.get_next_eligible_action("synthetic", "second")
            assert recommendation["recommendation"] == "REINFORCE"
            assert recommendation["next_kc_title"] != "Módulo completado"
        store = current[0].study_session_orchestrator.session_store
        before = store.load_session(base.split("/")[-1])
        rejected = client.post(base + "/action", json={"action": "START_NEXT_KC", "payload": {"episode_id": episode, "kc_id": "second"}})
        assert rejected.status_code == 403, rejected.text
        after = client.get(base + "/snapshot").json()
        assert after["curriculum_completed"] is False and after["current_kc_id"] == "second"
        assert store.load_session(base.split("/")[-1]) == before


def test_terminal_curriculum_sql_failure_preserves_state(curricular_api, sm2_clock):
    from fastapi.testclient import TestClient
    app, current, build = curricular_api
    with TestClient(app, raise_server_exceptions=False) as client:
        base, episode = begin_last_curricular_attempt(client)
        evaluated = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert evaluated.status_code == 200, evaluated.text
        sid = base.split("/")[-1]
        store = current[0].study_session_orchestrator.session_store
        before = store.load_session(sid)
        bkt = current[0].student_storage.get_all_bkt_states()
        agenda = current[0].student_storage.get_all_anchor_states()
        connection = store._get_conn()
        connection.executescript("""
            CREATE TRIGGER synthetic_terminal_failure AFTER UPDATE ON study_sessions
            WHEN json_array_length(json_extract(NEW.state_blob, '$.available_actions')) = 1
            BEGIN SELECT RAISE(ABORT, 'synthetic terminal persistence failure'); END;
        """)
        request = {"action": "START_NEXT_KC", "payload": {"episode_id": episode, "kc_id": "second"}}
        assert client.post(base + "/action", json=request).status_code == 500
        assert store.load_session(sid) == before
        assert client.get(base + "/snapshot").json()["curriculum_completed"] is False
    current[0] = build()
    with TestClient(app) as client:
        assert client.get(base + "/snapshot").json()["curriculum_completed"] is False
        assert current[0].student_storage.get_all_bkt_states() == bkt
        assert current[0].student_storage.get_all_anchor_states() == agenda
        connection.execute("DROP TRIGGER synthetic_terminal_failure")
        connection.commit()
        completed = client.post(base + "/action", json=request)
        assert completed.status_code == 200, completed.text
        assert completed.json()["curriculum_completed"] is True


def begin_review_from_agenda(client, anchor_id):
    """Use existing session selection, exercise and grading routes; no review-only API."""
    opened = client.post("/api/study/session/open", json={"notebook_id": "synthetic"})
    assert opened.status_code == 200, opened.text
    base = f"/api/study/session/{opened.json()['session_id']}"
    selected = client.post(base + "/action", json={"action": "SELECT_DIFFERENT_KC", "payload": {"kc_id": anchor_id}})
    assert selected.status_code == 200, selected.text
    assert selected.json()["current_kc_id"] == anchor_id
    started = client.post(base + "/action", json={"action": "START_EXPLANATION"})
    assert started.status_code == 200, started.text
    episode = started.json()["episode_id"]
    exercise = client.get(f"/api/pedagogy/episode/{episode}/next")
    assert exercise.status_code == 200, exercise.text
    assert exercise.json()["exercise"]["kc_id"] == anchor_id
    return base, episode


@pytest.mark.parametrize("answer, timing", [("42", "due"), ("17", "due"), ("42", "early")])
def test_review_cycle_agenda_new_attempt_restore_and_replay(curricular_api, sm2_clock, answer, timing):
    from datetime import timedelta
    from fastapi.testclient import TestClient
    app, current, build = curricular_api
    with TestClient(app) as client:
        old_base, old_episode = begin_curricular_attempt(client)
        first = client.post(old_base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert first.status_code == 200, first.text
        prior = current[0].student_storage.get_anchor_state("first")
        assert prior.interval == 1 and prior.repetitions == 1 and prior.EF == pytest.approx(2.6)
        assert client.post(old_base + "/close").status_code == 200
        sm2_clock.current = prior.next_review if timing == "due" else prior.updated_at + timedelta(hours=12)
        agenda = client.get("/api/student/spaced-repetition/due")
        assert agenda.status_code == 200, agenda.text
        item = next(item for item in agenda.json() if item["anchor_id"] == "first")
        assert item["is_due"] is (timing == "due")
        # Early review is an explicit selection already allowed by the curriculum contract.
        base, episode = begin_review_from_agenda(client, item["anchor_id"])
        assert base != old_base and episode != old_episode
        review_time = sm2_clock.current
        request = {"action": "SUBMIT_ANSWER", "payload": {"answer": answer}}
        result = client.post(base + "/action", json=request)
        assert result.status_code == 200, result.text
        evaluation = result.json()["evaluation"]
        assert evaluation["is_correct"] is (answer == "42")
        assert evaluation["was_idempotent_replay"] is False
        assert evaluation["bkt_update"]["kc_id"] == item["anchor_id"]
        assert evaluation["bkt_update"]["attempts"] == 2
        saved = current[0].student_storage.get_anchor_state("first")
        assert saved.last_quality == (5 if answer == "42" else 1)
        assert saved.interval == (6 if answer == "42" else 1)
        assert saved.repetitions == (2 if answer == "42" else 0)
        assert saved.EF == pytest.approx(2.7 if answer == "42" else 2.06)
        assert saved.next_review == review_time + timedelta(days=saved.interval)
        assert saved.updated_at == review_time
        for session_base, episode_id in ((old_base, old_episode), (base, episode)):
            assert current[0].student_storage.get_operation_receipt(
                session_id=session_base.split("/")[-1], episode_id=episode_id,
                exercise_id="exercise-first", attempt_id="step_eval_exercise-first",
            ) is not None
        sm2_clock.current += timedelta(days=2)
        repeated = client.post(base + "/action", json=request)
        assert repeated.status_code == 200 and repeated.json()["evaluation"]["was_idempotent_replay"] is True
        assert current[0].student_storage.get_anchor_state("first") == saved
        assert current[0].bkt_tracker.get_state("first").attempts == 2
    current[0] = build()
    with TestClient(app) as client:
        restored = client.get(base + "/snapshot")
        assert restored.status_code == 200 and restored.json()["episode_id"] == episode
        assert current[0].student_storage.get_anchor_state("first") == saved
        updated = next(item for item in client.get("/api/student/spaced-repetition/due").json() if item["anchor_id"] == "first")
        assert updated["due_date"] == saved.next_review.isoformat()
        assert updated["interval_days"] == saved.interval and updated["ef"] == round(saved.EF, 2)
        assert updated["is_due"] is (saved.next_review <= sm2_clock.current)
        assert client.get(old_base + "/snapshot").json()["episode_phase"] == "CLOSED"
        assert client.post(base + "/close").status_code == 200
        assert client.post(base + "/action", json=request).status_code == 400
        assert current[0].student_storage.get_anchor_state("first") == saved
        assert current[0].bkt_tracker.get_state("first").attempts == 2


def test_review_cycle_sql_failure_and_invalid_reference(curricular_api, sm2_clock):
    from fastapi.testclient import TestClient
    app, current, build = curricular_api
    with TestClient(app, raise_server_exceptions=False) as client:
        old_base, _ = begin_curricular_attempt(client)
        evaluated = client.post(old_base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert evaluated.status_code == 200, evaluated.text
        storage = current[0].student_storage
        before_agenda = storage.get_all_anchor_states()
        before_bkt = storage.get_all_bkt_states()
        sm2_clock.current = before_agenda["first"].next_review
        opened = client.post("/api/study/session/open", json={"notebook_id": "synthetic"}).json()
        rejected = client.post(f"/api/study/session/{opened['session_id']}/action", json={
            "action": "SELECT_DIFFERENT_KC", "payload": {"kc_id": "invalid-anchor"},
        })
        assert rejected.status_code == 403
        assert storage.get_all_anchor_states() == before_agenda and storage.get_all_bkt_states() == before_bkt
        base, episode = begin_review_from_agenda(client, "first")
        connection = storage._get_connection()
        connection.executescript("""
            CREATE TRIGGER synthetic_review_failure AFTER UPDATE ON anchor_states
            BEGIN SELECT RAISE(ABORT, 'synthetic review write failure'); END;
        """)
        failed = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert failed.status_code == 500
        assert storage.get_all_anchor_states() == before_agenda and storage.get_all_bkt_states() == before_bkt
        assert storage.get_operation_receipt(session_id=base.split("/")[-1], episode_id=episode,
            exercise_id="exercise-first", attempt_id="step_eval_exercise-first") is None
    current[0] = build()
    with TestClient(app) as client:
        assert current[0].student_storage.get_all_anchor_states() == before_agenda
        assert current[0].student_storage.get_all_bkt_states() == before_bkt
        assert client.get(base + "/snapshot").json()["episode_id"] == episode
        connection.execute("DROP TRIGGER synthetic_review_failure")
        connection.commit()
        retried = client.post(base + "/action", json={"action": "SUBMIT_ANSWER", "payload": {"answer": "42"}})
        assert retried.status_code == 200, retried.text
        assert retried.json()["evaluation"]["bkt_update"]["attempts"] == 2
        assert current[0].student_storage.get_anchor_state("first").repetitions == 2
