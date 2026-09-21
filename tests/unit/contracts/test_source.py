"""Unit tests for Source contract."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.source import Source
from study_engine.contracts.enums import SourceRole


def test_source_valid_minimal():
    source = Source(source_id="src-001", title="Fundamentos de Programación")
    assert source.source_id == "src-001"
    assert source.title == "Fundamentos de Programación"
    assert source.role == SourceRole.PRIMARY
    assert source.priority == 1
    assert source.language == "es"
    assert source.metadata == {}


def test_source_valid_full():
    source = Source(
        source_id="joyanes-fp-4e",
        title="Fundamentos de Programación",
        author="Luis Joyanes Aguilar",
        type="book",
        language="es",
        role=SourceRole.PRIMARY,
        priority=1,
        subject="Programación",
        course="Fase-0",
        phase="Fase-0",
        chapter="Capítulo 1",
        section="1.2",
        page=15,
        metadata={"edition": "4th", "publisher": "McGraw-Hill"},
    )
    assert source.author == "Luis Joyanes Aguilar"
    assert source.role == SourceRole.PRIMARY
    assert source.page == 15
    assert source.metadata["edition"] == "4th"


def test_source_incomplete_metadata_allowed():
    # Specification rule: incomplete metadata must NOT block ingestion
    source = Source(source_id="src-sparse", title="Sparse Document")
    assert source.author is None
    assert source.chapter is None
    assert source.page is None


def test_source_invalid_missing_required():
    with pytest.raises(ValidationError):
        Source(title="Missing ID")

    with pytest.raises(ValidationError):
        Source(source_id="src-123")


def test_source_invalid_empty_strings():
    with pytest.raises(ValidationError):
        Source(source_id="", title="Valid Title")

    with pytest.raises(ValidationError):
        Source(source_id="src-123", title="")


def test_source_invalid_role():
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", role="NON_EXISTENT_ROLE")


def test_source_invalid_priority_range():
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", priority=0)


def test_source_roles_all_valid():
    for role in SourceRole:
        source = Source(source_id=f"src-{role.value}", title="Title", role=role)
        assert source.role == role
