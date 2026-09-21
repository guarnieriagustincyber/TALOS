"""Tests verifying dynamic curricular intelligence and BKT inspection in FolderOrchestrator."""

import pytest
from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def mock_store():
    store = KnowledgeStore(":memory:")
    store.initialize()
    return store


def test_folder_orchestrator_greeting(mock_store):
    """Greeting query returns warm dynamic greeting with canonical notebooks."""
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=mock_store)
    decision = orch.route_query("hola")

    assert decision["action"] == "folder_response"
    assert decision["handler"] == "get_aggregated_progress"
    assert "Hola Agustín" in decision["message"]
    assert "Lenguajes de Programación" in decision["message"]
    assert "Sistemas Operativos II" in decision["message"]
    assert "Sistema de Tratamiento de Datos" in decision["message"]
    assert "Infraestructura de Telecomunicaciones" in decision["message"]
    assert "Fase 0" in decision["message"]


def test_folder_orchestrator_all_notebooks_query(mock_store):
    """Querying about all notebooks returns 5 canonical notebooks with sources breakdown."""
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=mock_store)
    
    queries = [
        "que informacion tenes sobre mis cuadernos?",
        "¿Cuáles son mis cuadernos?",
        "que materias tengo?",
        "resumen de las materias",
    ]
    for q in queries:
        decision = orch.route_query(q)
        assert decision["action"] == "folder_response"
        assert decision["handler"] == "get_aggregated_progress"
        assert "5 cuadernos canónicos" in decision["message"]
        assert "fadena-lenguajes" in decision["message"]
        assert "fadena-so2" in decision["message"]
        assert "fadena-std" in decision["message"]
        assert "fadena-teleco" in decision["message"]
        assert "fase0-soc" in decision["message"]


def test_folder_orchestrator_specific_notebook_briefing(mock_store):
    """Mentioning a specific notebook returns its detailed curricular briefing."""
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=mock_store)

    queries = [
        "y en lenguaje de programacion?",
        "lenguajes de programacion",
        "cuaderno de lenguajes de programación",
    ]
    for q in queries:
        decision = orch.route_query(q)
        assert decision["action"] == "folder_response"
        assert decision["handler"] == "get_aggregated_progress"
        assert decision.get("suggested_notebook_id") == "fadena-lenguajes"
        assert "Lenguajes de Programación" in decision["message"]
        assert "FADENA / 1er Año / 2do Cuatrimestre" in decision["message"]
        assert "Joyanes" in decision["message"] or "Programación" in decision["message"]


def test_folder_orchestrator_notebook_progress_and_pending(mock_store):
    """Asking for progress and pending topics in SO2 reports BKT states and syllabus topics."""
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=mock_store)

    queries = [
        "en sistemas operativos II, que avance tengo pendientes?",
        "cuál es mi avance en sistemas operativos 2?",
        "que temas tengo pendientes en so2?",
    ]
    for q in queries:
        decision = orch.route_query(q)
        assert decision["action"] == "folder_response"
        assert decision["handler"] == "get_aggregated_progress"
        assert decision.get("suggested_notebook_id") == "fadena-so2"
        assert "Sistemas Operativos II" in decision["message"]
        assert "Concurrencia" in decision["message"] or "Planificación" in decision["message"]


def test_folder_orchestrator_activity_query(mock_store):
    """Asking where user left off reports recent activity and remediation."""
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=mock_store)

    queries = [
        "donde me quede?",
        "dónde me quedé?",
        "que estaba haciendo?",
        "cuál fue mi última actividad?",
    ]
    for q in queries:
        decision = orch.route_query(q)
        assert decision["action"] == "folder_response"
        assert decision["handler"] == "get_aggregated_progress"
        assert "Sistemas Operativos II" in decision["message"] or "actividad" in decision["message"]


def test_folder_orchestrator_technical_delegation_with_notebook(mock_store):
    """Technical question with notebook context delegates and preserves zero technical authority."""
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=mock_store)

    decision = orch.route_query("¿Cómo funciona la función malloc en C?")
    assert decision["action"] == "delegate_to_notebook"
    assert "técnica" in decision["message"]
    assert orch.epistemic_authority is False
