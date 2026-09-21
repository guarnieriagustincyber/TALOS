"""Unit tests for category-specific regression fallback policy in Semantic Router."""

import json
import logging
from pathlib import Path
import pytest

from study_engine.tutor.semantic_router import (
    DISABLED_FACET_CATEGORIES,
    check_e1_category_policy,
    is_facet_decomposition_allowed,
    load_category_policy,
    reset_category_policy,
    save_category_policy,
)


@pytest.fixture(autouse=True)
def clean_policy_state():
    """Ensure clean policy state before and after each test."""
    reset_category_policy()
    yield
    reset_category_policy()


def test_category_policy_allows_non_degraded_category():
    """Categories with delta_sac >= -0.02 remain enabled."""
    triggered = check_e1_category_policy("multi_source", delta_sac=0.15)
    assert triggered is False
    assert is_facet_decomposition_allowed("multi_source") is True
    assert "multi_source" not in DISABLED_FACET_CATEGORIES


def test_category_policy_triggers_regression_guard_and_logs(caplog):
    """Category degrading SAC by > 2pp triggers REGRESSION_GUARD and is disabled."""
    with caplog.at_level(logging.WARNING):
        triggered = check_e1_category_policy("cross_curricular", delta_sac=-0.0425)

    assert triggered is True
    assert is_facet_decomposition_allowed("cross_curricular") is False
    assert "cross_curricular" in DISABLED_FACET_CATEGORIES
    assert "REGRESSION_GUARD" in caplog.text
    assert "cross_curricular" in caplog.text


def test_is_facet_decomposition_allowed_none_category():
    """None or empty category is allowed by default."""
    assert is_facet_decomposition_allowed(None) is True
    assert is_facet_decomposition_allowed("") is True


def test_save_and_load_category_policy(tmp_path: Path):
    """Verify serialization and deserialization of category policy."""
    policy_file = tmp_path / "e1_category_policy.json"

    # Trigger a regression guard
    check_e1_category_policy("test_category_a", delta_sac=-0.05)
    check_e1_category_policy("test_category_b", delta_sac=-0.03)

    assert is_facet_decomposition_allowed("test_category_a") is False
    assert is_facet_decomposition_allowed("test_category_b") is False

    # Save to file
    save_category_policy(policy_file)
    assert policy_file.exists()

    with open(policy_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["policy_name"] == "E1_CATEGORY_REGRESSION_GUARD"
    assert "test_category_a" in data["disabled_categories"]
    assert "test_category_b" in data["disabled_categories"]

    # Reset in memory and reload
    reset_category_policy()
    assert is_facet_decomposition_allowed("test_category_a") is True

    load_category_policy(policy_file)
    assert is_facet_decomposition_allowed("test_category_a") is False
    assert is_facet_decomposition_allowed("test_category_b") is False


def test_should_activate_facet_decomposition_boundary():
    """Verify E5.3 deterministic boundary activation rule (Enmienda E5-A5)."""
    from study_engine.tutor.semantic_router import should_activate_facet_decomposition

    # 1. Multi-facet category activates
    act, reason = should_activate_facet_decomposition(
        "comparativa de memoria entre heap y stack en sistemas operativos",
        category="multi_source",
        estimated_facets=2,
    )
    assert act is True
    assert "activating E1d" in reason

    # 2. Atomic query below token threshold does NOT activate
    act, reason = should_activate_facet_decomposition(
        "que es fork",
        category="simple",
        estimated_facets=1,
        min_tokens_threshold=5,
    )
    assert act is False
    assert "monolithic retrieval" in reason

    # 3. Category disabled by REGRESSION_GUARD does NOT activate
    check_e1_category_policy("cross_curricular", delta_sac=-0.05)
    act, reason = should_activate_facet_decomposition(
        "concurrencia y memoria en sistemas operativos y ciberseguridad",
        category="cross_curricular",
        estimated_facets=3,
    )
    assert act is False
    assert "REGRESSION_GUARD active" in reason
