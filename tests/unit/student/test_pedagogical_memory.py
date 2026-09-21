"""Unit tests for sovereign student pedagogical memory in SQLite (Fase 3)."""

import pytest
from unittest.mock import MagicMock

from study_engine.student.storage import StudentStorage
from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
from study_engine.tutor.fastpath_service import FastPathConversationalService, RouteKind


@pytest.fixture
def mem_storage():
    """Isolated in-memory SQLite student storage."""
    return StudentStorage(":memory:")


@pytest.fixture
def tracker(mem_storage):
    """Tracker backed by in-memory SQLite storage."""
    return PedagogicalMemoryTracker(mem_storage)


def test_pedagogical_memory_storage_crud(mem_storage):
    """Direct CRUD operations on student_pedagogical_memory table."""
    # 1. Create
    m_id1 = mem_storage.save_pedagogical_memory(
        student_id="student_1",
        category="misconception",
        kc_id="KC-REGS-01",
        insight="Confunde el valor del Carry Flag tras una resta sin signo.",
        confidence=0.9,
    )
    m_id2 = mem_storage.save_pedagogical_memory(
        student_id="student_1",
        category="preference",
        kc_id=None,
        insight="Prefiere analogías físicas o mecánicas sobre metáforas de alto nivel.",
        confidence=1.0,
    )
    assert m_id1 > 0
    assert m_id2 > m_id1

    # 2. Read with category filter
    misc_memories = mem_storage.get_pedagogical_memories(
        student_id="student_1",
        category="misconception",
    )
    assert len(misc_memories) == 1
    assert misc_memories[0]["kc_id"] == "KC-REGS-01"
    assert "Carry Flag" in misc_memories[0]["insight"]

    # 3. Read with KC filter
    kc_memories = mem_storage.get_pedagogical_memories(
        student_id="student_1",
        kc_id="KC-REGS-01",
    )
    assert len(kc_memories) == 1
    assert kc_memories[0]["id"] == m_id1

    # 4. Touch (update last_accessed)
    initial_access = misc_memories[0]["last_accessed"]
    touched = mem_storage.touch_pedagogical_memory(m_id1)
    assert touched is True

    # 5. Delete
    deleted = mem_storage.delete_pedagogical_memory(m_id1)
    assert deleted is True
    remaining = mem_storage.get_pedagogical_memories(student_id="student_1")
    assert len(remaining) == 1
    assert remaining[0]["id"] == m_id2


def test_pedagogical_memory_tracker_recording(tracker):
    """PedagogicalMemoryTracker records misconceptions, preferences, and analogy affinity."""
    id_misc = tracker.record_misconception(
        student_id="agustin",
        kc_id="KC-OCTAL-01",
        misconception="Asume que 010 y 10 representan el mismo valor numérico.",
    )
    id_pref = tracker.record_preference(
        student_id="agustin",
        preference_text="Explicaciones paso a paso con tablas ASCII/Hex.",
    )
    id_aff = tracker.record_analogy_affinity(
        student_id="agustin",
        domain="electrónica digital y compuertas lógicas",
    )

    assert id_misc > 0
    assert id_pref > 0
    assert id_aff > 0

    all_notes = tracker.storage.get_pedagogical_memories(student_id="agustin")
    assert len(all_notes) == 3


def test_tutor_guidance_notes_formatting(tracker):
    """Formatting qualitative insights into structured prompt directives."""
    # Empty case
    empty_notes = tracker.get_tutor_guidance_notes(student_id="unknown_student")
    assert empty_notes == ""

    # Seed data
    tracker.record_misconception(
        student_id="agustin",
        kc_id="KC-STACK-01",
        misconception="Cree que la pila crece hacia direcciones de memoria más altas.",
    )
    tracker.record_preference(
        student_id="agustin",
        preference_text="Usa diagramas de memoria verticales descendentes.",
    )

    # Directive for specific KC
    notes_stack = tracker.get_tutor_guidance_notes(
        student_id="agustin",
        kc_id="KC-STACK-01",
        max_notes=2,
    )
    assert "NOTAS DE APRENDIZAJE PREVIO DEL ESTUDIANTE:" in notes_stack
    assert "[MISCONCEPTION]" in notes_stack
    assert "pila crece" in notes_stack

    # Fallback to preferences if KC has no notes
    notes_fallback = tracker.get_tutor_guidance_notes(
        student_id="agustin",
        kc_id="KC-UNSEEN-99",
        max_notes=2,
    )
    assert "[PREFERENCE]" in notes_fallback
    assert "diagramas de memoria" in notes_fallback

    # format_tutor_directive alias behaves identically
    alias_notes = tracker.format_tutor_directive(
        student_id="agustin",
        kc_id="KC-STACK-01",
        limit=2,
    )
    assert alias_notes == notes_stack


def test_fastpath_integration_with_pedagogical_memory(mem_storage):
    """FastPathService extracts and integrates pedagogical memories into contextual context."""
    import asyncio

    tracker = PedagogicalMemoryTracker(mem_storage)
    tracker.record_misconception(
        student_id="default_student",
        kc_id="KC-REGS-01",
        misconception="Confunde registros de propósito general con flags de estado.",
    )
    tracker.record_preference(
        student_id="default_student",
        preference_text="Evitar rodeos y ser socrático.",
    )

    container = MagicMock()
    container.pedagogical_memory_tracker = tracker
    container.student_storage = mem_storage
    nb_mock = MagicMock()
    nb_mock.name = "Sistemas Digitales"
    container.knowledge_store.get_notebook.return_value = nb_mock
    container.pedagogical_orchestrator._kc_catalog = {
        "nb_test": {"kcs": [{"title": "Registros y Banderas"}]}
    }

    fastpath = FastPathConversationalService()
    context = fastpath.extract_student_context(container, "nb_test")

    assert context["notebook_title"] == "Sistemas Digitales"
    assert context["last_kc_title"] == "Registros y Banderas"
    assert "NOTAS DE APRENDIZAJE PREVIO DEL ESTUDIANTE:" in context["pedagogical_directive"]
    assert "Confunde registros" in context["misconceptions"]

    # Generate fastpath greeting fallback with context
    response = asyncio.run(
        fastpath.generate_response(
            query="Hola KASIU!",
            route_kind=RouteKind.GREETING,
            context=context,
            llm_backend=None,
        )
    )
    assert len(response) > 10
    assert "Agustín" in response
