"""Contract tests for DocumentCatalog interfaces and exceptions."""

import json
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import (
    DocumentCatalogError,
    DocumentConflictError,
    DocumentNotFoundError,
    SourceCatalogError,
    SourceNotFoundError,
)
from study_engine.contracts.document import Document
from study_engine.ingestion.document_catalog import DocumentCatalog


def test_document_catalog_exceptions_hierarchy():
    assert issubclass(DocumentCatalogError, Exception)
    assert issubclass(DocumentNotFoundError, DocumentCatalogError)
    assert issubclass(DocumentConflictError, DocumentCatalogError)

    # DocumentNotFoundError contract
    not_found = DocumentNotFoundError("doc-404")
    assert not_found.document_id == "doc-404"
    assert "doc-404" in str(not_found)

    # DocumentConflictError contract
    conflict = DocumentConflictError("doc-conflict", reason="Attribute mismatch")
    assert conflict.document_id == "doc-conflict"
    assert conflict.reason == "Attribute mismatch"
    assert "doc-conflict" in str(conflict)
    assert "Attribute mismatch" in str(conflict)

    default_conflict = DocumentConflictError("doc-conflict-2")
    assert default_conflict.document_id == "doc-conflict-2"
    assert "doc-conflict-2" in str(default_conflict)


def test_document_contract_canonical_roundtrip():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    doc = Document(
        id="doc-canonical",
        source_id="src-joyanes",
        title="Capítulo 1: Fundamentos",
        content="Texto de prueba...",
        path="Fase-0/Joyanes/ch01.pdf",
        page_count=40,
        language="es",
        metadata={"priority": 1, "topics": ["variables", "control_flow"]},
        created_at=now,
    )

    # Dict roundtrip
    dumped_dict = doc.model_dump()
    reconstructed_dict = Document.model_validate(dumped_dict)
    assert reconstructed_dict == doc

    # JSON roundtrip
    dumped_json = doc.model_dump_json()
    reconstructed_json = Document.model_validate_json(dumped_json)
    assert reconstructed_json == doc


def test_document_schema_structure():
    schema = Document.model_json_schema()
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert "id" in schema["properties"]
    assert "source_id" in schema["properties"]
    assert "title" in schema["properties"]
    assert "required" in schema
    assert set(schema["required"]) == {"id", "source_id", "title"}


def test_document_catalog_serialization_contract():
    catalog = DocumentCatalog()
    doc = Document(
        id="doc-serialized",
        source_id="src-1",
        title="Doc Title",
        metadata={"key": "val"},
    )
    catalog.register(doc)

    serialized = catalog.to_dict()
    assert isinstance(serialized, dict)
    assert "records" in serialized
    assert isinstance(serialized["records"], dict)
    assert "doc-serialized" in serialized["records"]

    # Verify JSON serializability
    json_str = json.dumps(serialized)
    assert "doc-serialized" in json_str

    deserialized_data = json.loads(json_str)
    restored = DocumentCatalog.from_dict(deserialized_data)
    assert restored.count() == 1
    assert restored.get("doc-serialized") == doc
