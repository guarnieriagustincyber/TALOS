"""Unit tests for Notebook contract."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.notebook import Notebook


def test_notebook_valid_minimal():
    notebook = Notebook(id="fase_0_programacion", name="Fase 0 - Programación")
    assert notebook.id == "fase_0_programacion"
    assert notebook.name == "Fase 0 - Programación"
    assert notebook.curriculum_id is None
    assert notebook.sources == []
    assert notebook.metadata == {}


def test_notebook_valid_full():
    now = datetime.now(timezone.utc)
    notebook = Notebook(
        id="materia_redes",
        name="Redes de Computadoras",
        description="Apuntes y libros de redes",
        subject="Redes",
        curriculum_id="cybersecurity_v1",
        sources=["stallings-redes", "tanenbaum-redes"],
        metadata={"semester": "2026-1", "faculty": "FADENA"},
        created_at=now,
        updated_at=now,
    )
    assert notebook.curriculum_id == "cybersecurity_v1"
    assert len(notebook.sources) == 2
    assert notebook.metadata["faculty"] == "FADENA"
    assert notebook.created_at == now


def test_notebook_missing_required():
    with pytest.raises(ValidationError):
        Notebook(name="Missing ID")

    with pytest.raises(ValidationError):
        Notebook(id="missing_name")


def test_notebook_invalid_types():
    with pytest.raises(ValidationError):
        Notebook(id=123, name="Invalid ID type")  # When strict/type check or string required

    with pytest.raises(ValidationError):
        Notebook(id="valid", name="valid", sources="not-a-list")
