"""Unit tests for Document contract."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.document import Document


def test_document_valid_minimal():
    doc = Document(id="doc-001", source_id="src-001", title="Capítulo 1")
    assert doc.id == "doc-001"
    assert doc.source_id == "src-001"
    assert doc.title == "Capítulo 1"
    assert doc.content is None
    assert doc.page_count is None
    assert doc.language == "es"


def test_document_valid_full():
    now = datetime.now(timezone.utc)
    doc = Document(
        id="doc-joyanes-ch1",
        source_id="joyanes-fp-4e",
        title="Introducción a la Ciencia de la Computación",
        content="Texto completo del capítulo...",
        path="Fase-0/Joyanes/capitulo_01.pdf",
        page_count=35,
        language="es",
        metadata={"checksum": "a1b2c3d4"},
        created_at=now,
    )
    assert doc.page_count == 35
    assert doc.path == "Fase-0/Joyanes/capitulo_01.pdf"
    assert doc.created_at == now


def test_document_missing_required():
    with pytest.raises(ValidationError):
        Document(source_id="src-1", title="Title")

    with pytest.raises(ValidationError):
        Document(id="doc-1", title="Title")

    with pytest.raises(ValidationError):
        Document(id="doc-1", source_id="src-1")


def test_document_invalid_page_count():
    with pytest.raises(ValidationError):
        Document(id="doc-1", source_id="src-1", title="Title", page_count=-5)
