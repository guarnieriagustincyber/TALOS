import asyncio
from unittest.mock import AsyncMock, MagicMock

from study_engine.pedagogy.memory.extractor import CognitiveExtractor
from study_engine.pedagogy.memory.store import CognitiveProfileStore
from study_engine.student.learning_patterns import LearningPatternsTracker
from study_engine.student.memory_extractor import PedagogicalMemoryExtractor
from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
from study_engine.student.storage import StudentStorage


def test_cognitive_extractor_does_not_persist_single_turn_misconception():
    store = CognitiveProfileStore(":memory:")
    extractor = CognitiveExtractor(store)
    extractor._extract_with_llm = AsyncMock(
        side_effect=AssertionError("ordinary turns must not invoke profile extraction")
    )

    persisted = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="student-test",
            notebook_id="fadena-teleco",
            query="Yo pensaba que la atenuación era equivalente al retardo de fase.",
            response_text="La atenuación y el retardo son propiedades distintas.",
            active_kc="teleco_transmision_datos",
        )
    )

    assert persisted == []
    assert store.get_active_items("student-test") == []


def test_cognitive_extractor_keeps_only_explicit_self_declared_preference():
    store = CognitiveProfileStore(":memory:")
    extractor = CognitiveExtractor(store)

    persisted = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="student-test",
            notebook_id="fadena-teleco",
            query="Prefiero que expliques los conceptos con tablas comparativas.",
            response_text="De acuerdo.",
            active_kc="teleco_transmision_datos",
        )
    )

    assert len(persisted) == 1
    items = store.get_active_items("student-test")
    assert len(items) == 1
    assert items[0]["category"] == "PREFERENCE"


def test_cognitive_extractor_does_not_persist_one_off_format_request():
    store = CognitiveProfileStore(":memory:")
    extractor = CognitiveExtractor(store)

    persisted = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="student-test",
            notebook_id="fadena-teleco",
            query="Dame un ejemplo con una tabla.",
            response_text="De acuerdo.",
            active_kc="teleco_transmision_datos",
        )
    )

    assert persisted == []
    assert store.get_active_items("student-test") == []


def test_cognitive_extractor_does_not_persist_negated_preference():
    store = CognitiveProfileStore(":memory:")
    extractor = CognitiveExtractor(store)

    persisted = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="student-test",
            notebook_id="fadena-teleco",
            query="No prefiero explicaciones con tablas.",
            response_text="Entendido.",
            active_kc="teleco_transmision_datos",
        )
    )

    assert persisted == []
    assert store.get_active_items("student-test") == []


def test_legacy_pedagogical_extractor_does_not_persist_single_turn_misconception():
    storage = StudentStorage(":memory:")
    tracker = PedagogicalMemoryTracker(storage)
    extractor = PedagogicalMemoryExtractor(tracker)

    result = asyncio.run(
        extractor.process_turn_and_persist(
            student_id="student-test",
            query="Pensé que el stack crecía hacia arriba en la memoria RAM.",
            response_text="La pila suele crecer hacia direcciones menores.",
            active_kc="KC-STACK-01",
            pedagogical_mode="resolve_misconception",
            llm_backend=MagicMock(),
        )
    )

    assert result is None
    assert storage.get_pedagogical_memories(
        student_id="student-test",
        category="misconception",
    ) == []


def test_mem0_turn_processing_does_not_persist_single_turn_error_pattern():
    storage = StudentStorage(":memory:")
    patterns = LearningPatternsTracker(storage)
    patterns.analyze_dialogue_turn = MagicMock(
        side_effect=AssertionError("a single turn is not a recurring pattern")
    )
    from study_engine.memory.mem0_manager import Mem0Manager

    manager = Mem0Manager(student_storage=storage, learning_patterns=patterns)
    result = manager.process_turn_memories(
        student_id="student-test",
        user_query="Me confundo con los punteros nulos.",
        response_text="Un puntero nulo no apunta a un objeto.",
        notebook_id="notebook-test",
        active_kc="KC-NULL",
    )

    assert result["patterns_updated"] == []
    assert storage.get_pedagogical_memories(
        student_id="student-test",
        category="recurring_error",
    ) == []
