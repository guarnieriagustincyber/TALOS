"""Unit tests for Sovereign Notebook Registry (Phase E4)."""

import pytest
from study_engine.federation.notebook_registry import Notebook, NotebookRegistry, DEFAULT_NOTEBOOKS


def test_default_notebooks_initialized() -> None:
    registry = NotebookRegistry()
    notebooks = registry.list_notebooks()
    assert len(notebooks) >= 3
    ids = {nb.notebook_id for nb in notebooks}
    assert "fadena-prog" in ids
    assert "fadena-so" in ids
    assert "NB-CYBERSECURITY-V1" in ids


def test_notebook_scope_validation() -> None:
    registry = NotebookRegistry()
    assert registry.validate_notebook_scope("fadena-prog") is True
    assert registry.validate_notebook_scope("fadena-so") is True
    assert registry.validate_notebook_scope("NB-CYBERSECURITY-V1") is True
    assert registry.validate_notebook_scope("unknown-nb") is False


def test_authority_weight_lookup_and_clamping() -> None:
    registry = NotebookRegistry()
    # Registered topics
    assert registry.get_authority_weight("fadena-prog", "punteros") == 1.5
    assert registry.get_authority_weight("fadena-so", "procesos") == 1.5
    assert registry.get_authority_weight("NB-CYBERSECURITY-V1", "buffer_overflow") == 1.5

    # Unregistered topic defaults to 1.0
    assert registry.get_authority_weight("fadena-prog", "unregistered_topic") == 1.0

    # Custom notebook with out-of-bounds weight gets clamped to [0.1, 2.0]
    custom = Notebook(
        notebook_id="custom-nb",
        name="Custom",
        subject="Custom",
        authority_matrix_ref={"super_topic": 5.0, "sub_topic": 0.01},
    )
    registry.register_notebook(custom)
    assert registry.get_authority_weight("custom-nb", "super_topic") == 2.0
    assert registry.get_authority_weight("custom-nb", "sub_topic") == 0.1
