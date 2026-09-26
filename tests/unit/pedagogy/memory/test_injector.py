"""Unit tests for ProfileInjector and SessionBriefingGenerator integration (Slice 3)."""

import pytest
from study_engine.pedagogy.memory.schema import (
    CognitiveItem,
    MemoryCategory,
)
from study_engine.pedagogy.memory.store import CognitiveProfileStore
from study_engine.pedagogy.memory.injector import ProfileInjector
from study_engine.memory.session_briefing import SessionBriefingGenerator


@pytest.fixture
def store():
    return CognitiveProfileStore(":memory:")


@pytest.fixture
def injector(store):
    return ProfileInjector(store)


def test_injector_empty_when_no_items(injector):
    block = injector.build_injection_block("agustin")
    assert block == ""


def test_injector_xml_structure_under_120_tokens(injector, store):
    store.upsert_item(
        CognitiveItem(
            user_id="agustin",
            kc_id="teleco_transmision_datos",
            category=MemoryCategory.WEAKNESS,
            description="Confunde atenuacion con distorsion",
        )
    )
    store.upsert_item(
        CognitiveItem(
            user_id="agustin",
            kc_id="teleco_transmision_datos",
            category=MemoryCategory.PREFERENCE,
            description="Preferencia por tablas",
        )
    )

    block = injector.build_injection_block("agustin")
    assert "<student_cognitive_profile>" in block
    assert "</student_cognitive_profile>" in block
    assert '<weakness kc="teleco_transmision_datos"' in block
    assert "<preference>" in block
    # Check token/character budget (< 500 chars guaranteed < 120 tokens)
    assert len(block) < 500


def test_injector_3_failures_remedial_rule(injector, store):
    # Simulate 3 occurrences of same misconception
    item = CognitiveItem(
        user_id="agustin",
        kc_id="teleco_transmision_datos",
        category=MemoryCategory.WEAKNESS,
        description="Confunde atenuacion con retardo",
    )
    store.upsert_item(item)
    store.upsert_item(item)
    store.upsert_item(item)

    block = injector.build_injection_block("agustin", active_kc="teleco_transmision_datos")
    assert "3_failures_remedial" in block
    assert "PROHIBIDO dar la solución directa" in block


def test_session_briefing_enriched_with_profile(store):
    store.upsert_item(
        CognitiveItem(
            user_id="agustin",
            kc_id="teleco_transmision_datos",
            category=MemoryCategory.WEAKNESS,
            description="Confunde atenuacion con distorsion",
            occurrences=2,
        )
    )

    generator = SessionBriefingGenerator(
        cognitive_profile_store=store,
    )
    brief = generator.generate_with_cognitive_profile(
        student_id="agustin",
        notebook_id="fadena-teleco",
        student_name="Agustín",
    )
    assert "Agustín" in brief
    assert "teleco_transmision_datos" in brief
    assert "Atención en 'teleco_transmision_datos'" in brief
