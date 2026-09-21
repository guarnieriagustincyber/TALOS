"""Tests for FolderOrchestrator read-only invariants and routing (Fase 5.7)."""

from datetime import datetime, timezone
import pytest

from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    EpistemologicalAuthority,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def test_setup():
    store = KnowledgeStore(":memory:")
    store.initialize()

    now = datetime.now(timezone.utc)
    folder = Folder(
        id="f_prog",
        name="Carrera de Programación",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(folder)

    nb1 = Notebook(id="nb_c", name="C Básico", folder_id="f_prog")
    nb2 = Notebook(id="nb_ds", name="Estructuras de Datos", folder_id="f_prog")
    store.create_notebook(nb1)
    store.create_notebook(nb2)

    ledger = EvidenceLedger()

    # Append one record scoped to f_prog
    rec = EvidenceRecord(
        record_id="rec_p1",
        student_id="student_01",
        node_id="NODE-C-INTRO",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor_module",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        metadata={"folder_id": "f_prog"},
    )
    ledger.append_evidence(rec)

    return store, ledger, folder


def test_folder_orchestrator_invariants(test_setup):
    """FolderOrchestrator is strictly read-only and possesses zero technical authority."""
    store, ledger, folder = test_setup
    orch = FolderOrchestrator(folder_id=folder.id, knowledge_store=store, ledger=ledger)

    assert orch.mutation_allowed is False
    assert orch.execution_allowed is False
    assert orch.epistemic_authority is False


def test_folder_orchestrator_list_notebooks(test_setup):
    """FolderOrchestrator lists only notebooks inside its assigned folder."""
    store, ledger, folder = test_setup
    orch = FolderOrchestrator(folder_id=folder.id, knowledge_store=store, ledger=ledger)

    nbs = orch.list_notebooks()
    assert len(nbs) == 2
    assert {nb.id for nb in nbs} == {"nb_c", "nb_ds"}


def test_folder_orchestrator_aggregated_progress_read_only(test_setup):
    """get_aggregated_progress calculates metrics without modifying storage or ledger."""
    store, ledger, folder = test_setup
    orch = FolderOrchestrator(folder_id=folder.id, knowledge_store=store, ledger=ledger)

    initial_entries = ledger.total_entries

    progress = orch.get_aggregated_progress("student_01")
    assert progress["folder_id"] == "f_prog"
    assert progress["student_id"] == "student_01"
    assert progress["total_notebooks"] == 2
    assert progress["total_evidence_entries"] == 1
    assert "NODE-C-INTRO" in progress["nodes_recorded"]
    assert progress["read_only"] is True

    # Invariant: Ledger was NOT mutated
    assert ledger.total_entries == initial_entries


def test_folder_orchestrator_suggest_study_plan(test_setup):
    """suggest_study_plan produces read-only guidance for notebook order."""
    store, ledger, folder = test_setup
    orch = FolderOrchestrator(folder_id=folder.id, knowledge_store=store, ledger=ledger)

    plan = orch.suggest_study_plan("student_01")
    assert plan["folder_id"] == "f_prog"
    assert plan["suggested_notebook_id"] in ["nb_c", "nb_ds"]
    assert len(plan["plan_sequence"]) == 2


def test_folder_orchestrator_route_query_organizational(test_setup):
    """Organizational queries are handled at folder level."""
    store, ledger, folder = test_setup
    orch = FolderOrchestrator(folder_id=folder.id, knowledge_store=store, ledger=ledger)

    queries = [
        "¿Cuál es mi progreso en esta carpeta?",
        "Mostrame el avance general",
        "¿Cómo es la planificación de la semana?",
        "¿Qué cuadernos tengo acá?",
        "Resumen del roadmap",
    ]
    for q in queries:
        decision = orch.route_query(q)
        assert decision["action"] == "folder_response"
        assert decision["handler"] == "get_aggregated_progress"


def test_folder_orchestrator_route_query_delegates_technical(test_setup):
    """Technical queries delegate strictly to notebook scope (Clarification 2)."""
    store, ledger, folder = test_setup
    orch = FolderOrchestrator(folder_id=folder.id, knowledge_store=store, ledger=ledger)

    tech_queries = [
        "¿Cómo funciona la función malloc en C?",
        "Explicame árboles binarios y balanceo AVL",
        "¿Por qué se produce un segmentation fault?",
        "Escribí un código en C para reservar un array",
    ]
    for q in tech_queries:
        decision = orch.route_query(q)
        assert decision["action"] == "delegate_to_notebook"
        assert "técnica" in decision["message"]
