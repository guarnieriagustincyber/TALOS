"""Contract tests for SourceRecord and SourceCatalog interfaces."""

import json
import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import (
    SourceCatalogError,
    SourceConflictError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source

SAMPLE_SHA256 = "c0ffee1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

CANONICAL_MANIFEST_DATA = {
    "source_id": "joyanes-fp-4e",
    "filename": "joyanes.pdf",
    "byte_size": 1048576,
    "sha256": SAMPLE_SHA256,
    "file_path": "Fase-0/Joyanes/joyanes.pdf",
    "media_type": "application/pdf",
    "metadata": {"pages": 700},
}


def test_source_record_canonical_construction_and_roundtrip():
    manifest = SourceManifest.model_validate(CANONICAL_MANIFEST_DATA)
    source = Source(
        source_id="joyanes-fp-4e",
        title="Fundamentos de Programación",
    )

    record = SourceRecord(
        source_id="joyanes-fp-4e",
        manifest=manifest,
        source=source,
        metadata={"indexed": False},
    )

    # Dict roundtrip
    dumped_dict = record.model_dump()
    reconstructed_dict = SourceRecord.model_validate(dumped_dict)
    assert reconstructed_dict == record

    # JSON roundtrip
    dumped_json = record.model_dump_json()
    reconstructed_json = SourceRecord.model_validate_json(dumped_json)
    assert reconstructed_json == record


def test_source_record_enforces_source_id_consistency():
    manifest = SourceManifest.model_validate(CANONICAL_MANIFEST_DATA)

    # Mismatched manifest source_id
    with pytest.raises(ValidationError) as exc:
        SourceRecord(
            source_id="different-id",
            manifest=manifest,
        )
    assert "does not match manifest.source_id" in str(exc.value)

    # Mismatched source metadata source_id
    wrong_source = Source(source_id="mismatched-source-id", title="Title")
    with pytest.raises(ValidationError) as exc:
        SourceRecord(
            source_id="joyanes-fp-4e",
            manifest=manifest,
            source=wrong_source,
        )
    assert "does not match source.source_id" in str(exc.value)


def test_source_record_rejects_unknown_root_fields():
    manifest = SourceManifest.model_validate(CANONICAL_MANIFEST_DATA)
    with pytest.raises(ValidationError) as exc:
        SourceRecord(
            source_id="joyanes-fp-4e",
            manifest=manifest,
            unauthorized_field="malicious",
        )
    assert "extra_forbidden" in str(exc.value)


def test_source_record_json_schema_structure():
    schema = SourceRecord.model_json_schema()
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert "source_id" in schema["properties"]
    assert "manifest" in schema["properties"]


def test_catalog_exceptions_hierarchy():
    assert issubclass(SourceNotFoundError, SourceCatalogError)
    assert issubclass(SourceConflictError, SourceCatalogError)
    assert issubclass(SourceCatalogError, Exception)

    not_found = SourceNotFoundError("src-1")
    assert not_found.source_id == "src-1"
    assert "src-1" in str(not_found)

    conflict = SourceConflictError("src-1", "hashA", "hashB")
    assert conflict.source_id == "src-1"
    assert conflict.existing_sha256 == "hashA"
    assert conflict.new_sha256 == "hashB"
    assert "hashA" in str(conflict)
    assert "hashB" in str(conflict)
