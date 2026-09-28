"""Unit tests for CognitiveExtractor (Slice 2)."""

import pytest
import asyncio
from study_engine.pedagogy.memory.store import CognitiveProfileStore
from study_engine.pedagogy.memory.extractor import CognitiveExtractor
from study_engine.pedagogy.memory.schema import MemoryCategory


@pytest.fixture
def store():
    return CognitiveProfileStore(":memory:")


@pytest.fixture
def extractor(store):
    return CognitiveExtractor(store)


def test_extractor_loads_kc_catalog(extractor):
    teleco_kcs = extractor.get_valid_kcs("fadena-teleco")
    assert len(teleco_kcs) > 0
    assert "teleco_transmision_datos" in teleco_kcs


def test_heuristic_preference_extraction(extractor, store, monkeypatch):
    async def no_llm_extraction(**kwargs):
        return None

    monkeypatch.setattr(extractor, "_extract_with_llm", no_llm_extraction)

    async def _run():
        query = "prefiero diagramas de flujo y tablas antes que código largo"
        ids = await extractor.process_turn_and_persist(
            student_id="agustin",
            notebook_id="fadena-teleco",
            query=query,
            response_text="Entendido, usaremos tablas y diagramas.",
            active_kc="teleco_transmision_datos",
        )
        assert len(ids) == 1
        items = store.get_active_items("agustin")
        assert len(items) == 1
        assert items[0]["category"] == MemoryCategory.PREFERENCE.value
        assert "Preferencia didáctica" in items[0]["description"]

    asyncio.run(_run())


def test_heuristic_misconception_extraction(extractor, store, monkeypatch):
    """A heuristic may recognize a confusion without persisting it as profile evidence."""
    async def no_llm_extraction(**kwargs):
        raise AssertionError("single-turn misconceptions must not invoke the LLM")

    monkeypatch.setattr(extractor, "_extract_with_llm", no_llm_extraction)

    async def _run():
        query = "yo pensaba que la atenuacion era equivalente al retardo de fase"
        ids = await extractor.process_turn_and_persist(
            student_id="agustin",
            notebook_id="fadena-teleco",
            query=query,
            response_text="La atenuación es pérdida de energía, mientras que el retardo distorsiona la forma de onda.",
            active_kc="teleco_transmision_datos",
        )
        assert ids == []
        items = store.get_active_items("agustin")
        assert items == []

    asyncio.run(_run())


def test_grounded_kc_validation(extractor):
    # Valid KC in catalog
    valid = extractor.validate_kc("fadena-teleco", "teleco_transmision_datos")
    assert valid == "teleco_transmision_datos"

    # Non-existent KC -> None
    invalid = extractor.validate_kc("fadena-teleco", "non_existent_invented_kc_123")
    assert invalid is None
