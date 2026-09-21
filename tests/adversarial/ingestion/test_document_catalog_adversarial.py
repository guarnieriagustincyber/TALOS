"""Adversarial tests for DocumentCatalog and Document boundaries."""

import json
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import (
    DocumentConflictError,
    DocumentNotFoundError,
    SourceNotFoundError,
)
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.ingestion.catalog import SourceCatalog
from study_engine.ingestion.document_catalog import DocumentCatalog

HASH_A = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"


def test_document_rejects_empty_or_whitespace_fields():
    with pytest.raises(ValidationError):
        Document(id="", source_id="src-1", title="Title")

    with pytest.raises(ValidationError):
        Document(id="doc-1", source_id="", title="Title")

    with pytest.raises(ValidationError):
        Document(id="doc-1", source_id="src-1", title="")

    with pytest.raises(ValidationError):
        Document(id="doc-1", source_id="src-1", title="Title", page_count=-1)


def test_document_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        Document(
            id="doc-1",
            source_id="src-1",
            title="Title",
            unauthorized_field="malicious_payload",
        )


def test_document_handles_complex_unicode_and_emojis():
    unicode_id = "📄-capítulo_01_algoritmos_#1_🔥"
    doc = Document(
        id=unicode_id,
        source_id="src-unicode-📚",
        title="Capítulo con símbolos: ñ, á, é, í, ó, ú, ü, 🚀",
        content="Contenido con texto en varios idiomas: 日本語, العربية, Русский",
        metadata={"emoji_key_💡": "valor_🎯"},
    )
    assert doc.id == unicode_id

    catalog = DocumentCatalog()
    catalog.register(doc)
    assert catalog.get(unicode_id) == doc
    assert catalog.find_by_source_id("src-unicode-📚")[0] == doc


def test_document_catalog_stress_idempotency():
    catalog = DocumentCatalog()
    doc = Document(
        id="stress-doc",
        source_id="stress-src",
        title="Stress Test Document",
        metadata={"counter": 0},
    )

    first_reg = catalog.register(doc)
    for _ in range(100):
        res = catalog.register(doc)
        assert res == first_reg

    assert catalog.count() == 1


def test_document_catalog_state_preserved_after_failed_conflict():
    catalog = DocumentCatalog()
    original_doc = Document(
        id="critical-doc",
        source_id="critical-src",
        title="Original Title",
        metadata={"security_level": "RESTRICTED"},
    )
    catalog.register(original_doc)

    tampered_doc = Document(
        id="critical-doc",
        source_id="critical-src",
        title="Original Title",
        metadata={"security_level": "PUBLIC"},
    )

    for _ in range(10):
        with pytest.raises(DocumentConflictError):
            catalog.register(tampered_doc)

    assert catalog.count() == 1
    assert catalog.get("critical-doc").metadata["security_level"] == "RESTRICTED"


@pytest.mark.parametrize(
    "corrupted_snapshot",
    [
        {"records": {"key": None}},
        {"records": {"key": "string-payload"}},
        {"records": {"key": 12345}},
        {"records": {"key": []}},
        {"records": {"": {"id": "doc", "source_id": "src", "title": "t"}}},
        {"records": {"outer": {"id": "different-inner", "source_id": "src", "title": "t"}}},
    ],
)
def test_adversarial_snapshot_corruption_rejected(corrupted_snapshot):
    with pytest.raises((ValueError, ValidationError)):
        DocumentCatalog.from_dict(corrupted_snapshot)


def test_adversarial_missing_source_referential_integrity():
    source_cat = SourceCatalog()
    source_cat.register(SourceManifest(source_id="valid-src", filename="f.pdf", byte_size=10, sha256=HASH_A))
    doc_cat = DocumentCatalog(source_catalog=source_cat)

    # Registering document with non-existent source
    with pytest.raises(SourceNotFoundError) as exc:
        doc_cat.register(Document(id="doc-bad-source", source_id="invalid-src", title="Title"))
    assert exc.value.source_id == "invalid-src"
    assert doc_cat.count() == 0


def test_adversarial_large_content_payload():
    large_text = "A" * 1_000_000  # 1 MB of text
    doc = Document(
        id="doc-large",
        source_id="src-1",
        title="Large Document",
        content=large_text,
    )
    catalog = DocumentCatalog()
    catalog.register(doc)

    retrieved = catalog.get("doc-large")
    assert len(retrieved.content) == 1_000_000
    assert retrieved == doc
