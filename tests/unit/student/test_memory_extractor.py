"""Unit and integration tests for PedagogicalMemoryExtractor (Semana 2)."""

import asyncio
from unittest.mock import MagicMock
import pytest

from study_engine.student.storage import StudentStorage
from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
from study_engine.student.memory_extractor import PedagogicalMemoryExtractor


@pytest.fixture
def mem_storage():
    """In-memory SQLite storage for student state."""
    return StudentStorage(":memory:")


@pytest.fixture
def tracker(mem_storage):
    """PedagogicalMemoryTracker backed by in-memory storage."""
    return PedagogicalMemoryTracker(mem_storage)


@pytest.fixture
def extractor(tracker):
    """PedagogicalMemoryExtractor initialized with tracker."""
    return PedagogicalMemoryExtractor(tracker)


def test_heuristic_misconception_extraction(extractor):
    """Test deterministic regex extraction of epistemic confusion patterns."""
    samples = [
        (
            "Pensé que la pila crecía hacia direcciones de memoria más altas, pero no entiendo",
            "pila crecía hacia direcciones de memoria más altas",
        ),
        (
            "¿Por qué 010 da 8 si en realidad debería ser 10?",
            "010 da 8",
        ),
        (
            "No entiendo por qué el carry flag queda en 1 tras la resta",
            "el carry flag queda en 1 tras la resta",
        ),
        (
            "Me confundo entre registros de propósito general y flags de estado",
            "registros de propósito general",
        ),
        (
            "Yo pensaba que malloc devolvía memoria inicializada en cero",
            "malloc devolvía memoria inicializada en cero",
        ),
    ]

    for query, expected_snippet in samples:
        insight = extractor.extract_heuristic_misconception(query)
        assert insight is not None, f"Expected misconception extracted for: '{query}'"
        assert expected_snippet.lower() in insight.lower(), (
            f"Expected '{expected_snippet}' in '{insight}'"
        )


def test_heuristic_preference_extraction(extractor):
    """Test deterministic extraction of explanation preferences."""
    samples = [
        "Prefiero que me expliques con diagramas de memoria verticales",
        "Me sirve más ver tablas comparativas de código y registros",
        "Mostrame un ejemplo paso a paso de la pila",
    ]

    for query in samples:
        pref = extractor.extract_heuristic_preference(query)
        assert pref is not None, f"Expected preference extracted for: '{query}'"
        assert "Preferencia didáctica" in pref


def test_process_turn_and_persist_misconception(extractor, mem_storage):
    """Test full processing and SQLite persistence of a misconception."""
    query = "Pensé que el stack crecía hacia arriba en la memoria RAM."
    response = "En la arquitectura x86_64, el stack crece hacia direcciones decrecientes."

    # First encounter
    m_id = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="agustin",
            query=query,
            response_text=response,
            active_kc="KC-STACK-01",
        )
    )
    assert m_id is not None
    assert m_id > 0

    memories = mem_storage.get_pedagogical_memories(
        student_id="agustin",
        category="misconception",
        kc_id="KC-STACK-01",
    )
    assert len(memories) == 1
    assert "stack crecía hacia arriba" in memories[0]["insight"]

    # Duplicate encounter should touch timestamp instead of creating duplicate row
    m_id2 = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="agustin",
            query="Pensé que el stack crecía hacia arriba en la memoria RAM.",
            response_text=response,
            active_kc="KC-STACK-01",
        )
    )
    assert m_id2 == m_id

    memories_after = mem_storage.get_pedagogical_memories(
        student_id="agustin",
        category="misconception",
        kc_id="KC-STACK-01",
    )
    assert len(memories_after) == 1


def test_process_turn_and_persist_preference(extractor, mem_storage):
    """Test full processing and SQLite persistence of an explanation preference."""
    query = "Prefiero que me expliques con código en C y casos de prueba."
    response = "Perfecto, acá tenés la implementación paso a paso."

    p_id = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="agustin",
            query=query,
            response_text=response,
            active_kc=None,
        )
    )
    assert p_id is not None
    assert p_id > 0

    prefs = mem_storage.get_pedagogical_memories(
        student_id="agustin",
        category="preference",
    )
    assert len(prefs) == 1
    assert "código en c" in prefs[0]["insight"].lower()


def test_chat_query_background_pedagogical_memory_integration(tmp_path):
    """End-to-end integration: querying chat with a misconception automatically saves to SQLite."""
    import time
    from fastapi.testclient import TestClient
    from datetime import datetime, timezone
    from study_engine.contracts.notebook import Notebook
    from study_engine.hierarchy.folder import Folder
    from study_engine.web.app import create_app
    from study_engine.web.dependencies import AppContainer, set_container

    import shutil
    from pathlib import Path

    existing_db = Path("data/web_state/knowledge_store.db")
    if existing_db.exists():
        shutil.copy2(existing_db, tmp_path / "knowledge_store.db")

    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    store = container.knowledge_store

    now = datetime.now(timezone.utc)
    if not store.contains_folder("f_prog"):
        store.create_folder(
            Folder(
                id="f_prog",
                name="Carrera Programación",
                parent_folder_id="folder_root",
                created_at=now,
                updated_at=now,
            )
        )
    if not store.contains_notebook("nb_prog_1"):
        store.create_notebook(
            Notebook(id="nb_prog_1", name="Punteros y Memoria", folder_id="f_prog")
        )

    from study_engine.web.routes.chat import _trigger_background_memory_extraction

    query_text = "Pensé que el stack crecía hacia arriba en la memoria RAM, pero me da error."
    response_text = "En x86_64, la pila crece hacia direcciones menores de memoria."

    _trigger_background_memory_extraction(
        container=container,
        student_id="student_auto_test",
        prompt_text=query_text,
        response_text=response_text,
        active_kc="KC-STACK-01",
        pedagogical_mode="resolve_misconception",
        llm_backend=None,
    )

    # Allow background asyncio task to execute
    time.sleep(0.3)

    memories = container.student_storage.get_pedagogical_memories(
        student_id="student_auto_test",
        category="misconception",
        kc_id="KC-STACK-01",
    )
    assert len(memories) >= 1
    assert "stack crecía hacia arriba" in memories[0]["insight"].lower()
