"""Unit tests for CognitiveProfileStore (Slice 1)."""

import pytest
from datetime import datetime, timezone, timedelta
from study_engine.pedagogy.memory.schema import (
    CognitiveItem,
    MemoryCategory,
    MemoryStatus,
)
from study_engine.pedagogy.memory.store import CognitiveProfileStore


@pytest.fixture
def store():
    return CognitiveProfileStore(":memory:")


def test_upsert_and_retrieve_item(store):
    item = CognitiveItem(
        user_id="agustin",
        kc_id="teleco_transmision_datos",
        category=MemoryCategory.WEAKNESS,
        description="Confunde atenuación con distorsión por retardo",
        evidence_quote="la atenuacion desfasaba",
        confidence=0.85,
    )
    uid = store.upsert_item(item)
    assert uid is not None

    items = store.get_active_items("agustin")
    assert len(items) == 1
    assert items[0]["kc_id"] == "teleco_transmision_datos"
    assert items[0]["occurrences"] == 1
    assert items[0]["category"] == "WEAKNESS"


def test_upsert_deduplication_and_auto_promotion(store):
    item1 = CognitiveItem(
        user_id="agustin",
        kc_id="teleco_transmision_datos",
        category=MemoryCategory.WEAKNESS,
        description="Confunde atenuación con distorsión por retardo en cables",
        evidence_quote="primera vez",
    )
    uid1 = store.upsert_item(item1)

    # Similar prefix description -> should de-duplicate and increment occurrences
    item2 = CognitiveItem(
        user_id="agustin",
        kc_id="teleco_transmision_datos",
        category=MemoryCategory.WEAKNESS,
        description="Confunde atenuación con distorsión por retardo en cables coaxiles",
        evidence_quote="segunda vez",
    )
    uid2 = store.upsert_item(item2)

    assert uid1 == uid2
    items = store.get_active_items("agustin")
    assert len(items) == 1
    assert items[0]["occurrences"] == 2
    # Auto-promotion: WEAKNESS + occurrences >= 2 -> RECURRING_MISCONCEPTION
    assert items[0]["category"] == "RECURRING_MISCONCEPTION"


def test_mark_resolved(store):
    item = CognitiveItem(
        user_id="agustin",
        kc_id="fase0_tramo1_metodologia",
        category=MemoryCategory.WEAKNESS,
        description="Error en prueba de escritorio",
    )
    uid = store.upsert_item(item)
    assert store.count_active("agustin") == 1

    store.mark_resolved(uid)
    assert store.count_active("agustin") == 0
    active = store.get_active_items("agustin")
    assert len(active) == 0


def test_priority_ordering_for_injection(store):
    # Insert items of different categories
    store.upsert_item(
        CognitiveItem(
            user_id="agustin",
            kc_id="kc_strength",
            category=MemoryCategory.STRENGTH,
            description="Domina diagramas ANSI",
        )
    )
    store.upsert_item(
        CognitiveItem(
            user_id="agustin",
            kc_id="kc_pref",
            category=MemoryCategory.PREFERENCE,
            description="Prefiere diagramas de flujo",
        )
    )
    store.upsert_item(
        CognitiveItem(
            user_id="agustin",
            kc_id="kc_recur",
            category=MemoryCategory.RECURRING_MISCONCEPTION,
            description="Confusión recurrente",
            occurrences=3,
        )
    )

    injection_items = store.get_for_injection("agustin", max_items=10)
    assert len(injection_items) == 3
    # Top priority must be RECURRING_MISCONCEPTION
    assert injection_items[0]["category"] == "RECURRING_MISCONCEPTION"
    assert injection_items[1]["category"] == "PREFERENCE"
