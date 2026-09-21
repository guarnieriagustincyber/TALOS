"""Contract tests for Ingestion subsystem contracts (S1.1).

Covers:
- Canonical payloads for SourceManifest, IngestionError, IngestionResult.
- Strict semantic invariants between IngestionStatus, error descriptors, and generated document artifacts.
- IngestionStatus enum exactness.
- Serialization, JSON schema structure, and round-trip fidelity.
- Rejection of unknown root fields and preservation of metadata extensibility.
"""

import json
import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    IngestionError,
    IngestionResult,
    IngestionStatus,
    SourceManifest,
)

SAMPLE_SHA256 = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"

CANONICAL_SOURCE_MANIFEST_MINIMAL = {
    "source_id": "joyanes-fp-4e",
    "filename": "joyanes_fp_4e.pdf",
    "byte_size": 18234500,
    "sha256": SAMPLE_SHA256,
}

CANONICAL_SOURCE_MANIFEST_FULL = {
    "source_id": "joyanes-fp-4e",
    "filename": "joyanes_fp_4e.pdf",
    "file_path": "Fase-0/Joyanes/joyanes_fp_4e.pdf",
    "byte_size": 18234500,
    "sha256": SAMPLE_SHA256,
    "media_type": "application/pdf",
    "metadata": {"pages_estimated": 750, "ocr_required": False},
}

CANONICAL_INGESTION_ERROR_FULL = {
    "code": "CORRUPT_DOCUMENT_BODY",
    "message": "Encountered corrupted stream at byte offset 2048.",
    "details": {"offset": 2048, "retry_allowed": False},
}

CANONICAL_INGESTION_RESULT_COMPLETED = {
    "source_id": "joyanes-fp-4e",
    "status": "COMPLETED",
    "manifest": CANONICAL_SOURCE_MANIFEST_FULL,
    "document_id": "doc-joyanes-fp-4e-v1",
    "metadata": {"duration_seconds": 1.25},
}

CANONICAL_INGESTION_RESULT_FAILED = {
    "source_id": "corrupted-source",
    "status": "FAILED",
    "manifest": CANONICAL_SOURCE_MANIFEST_FULL,
    "error": CANONICAL_INGESTION_ERROR_FULL,
    "metadata": {"attempt": 1},
}


def test_ingestion_status_exact_members():
    """IngestionStatus must contain exactly the 4 permitted lifecycle statuses."""
    expected = {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}
    actual = {member.value for member in IngestionStatus}
    assert actual == expected, f"IngestionStatus drift detected: {actual} != {expected}"
    assert len(IngestionStatus) == 4


def test_source_manifest_canonical_construction_and_roundtrip():
    """SourceManifest must validate canonical payloads and roundtrip cleanly."""
    manifest = SourceManifest.model_validate(CANONICAL_SOURCE_MANIFEST_FULL)
    assert manifest.source_id == "joyanes-fp-4e"
    assert manifest.sha256 == SAMPLE_SHA256
    assert manifest.byte_size == 18234500

    dumped_dict = manifest.model_dump()
    reconstructed = SourceManifest.model_validate(dumped_dict)
    assert reconstructed == manifest

    dumped_json = manifest.model_dump_json()
    reconstructed_json = SourceManifest.model_validate_json(dumped_json)
    assert reconstructed_json == manifest


def test_ingestion_result_completed_invariant_rules():
    """COMPLETED status must not allow error descriptors."""
    # Valid completed result
    result = IngestionResult.model_validate(CANONICAL_INGESTION_RESULT_COMPLETED)
    assert result.status == IngestionStatus.COMPLETED
    assert result.error is None
    assert result.document_id == "doc-joyanes-fp-4e-v1"

    # Invalid: COMPLETED with error
    with pytest.raises(ValidationError) as exc:
        IngestionResult(
            source_id="s-1",
            status=IngestionStatus.COMPLETED,
            document_id="doc-1",
            error=IngestionError(code="ERR", message="msg"),
        )
    assert "COMPLETED ingestion status cannot contain an error" in str(exc.value)


def test_ingestion_result_failed_invariant_rules():
    """FAILED status requires error descriptor and forbids document_id."""
    # Valid failed result
    result = IngestionResult.model_validate(CANONICAL_INGESTION_RESULT_FAILED)
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "CORRUPT_DOCUMENT_BODY"
    assert result.document_id is None

    # Invalid: FAILED without error
    with pytest.raises(ValidationError) as exc:
        IngestionResult(source_id="s-1", status=IngestionStatus.FAILED)
    assert "FAILED ingestion status requires an error descriptor" in str(exc.value)

    # Invalid: FAILED with document_id
    with pytest.raises(ValidationError) as exc:
        IngestionResult(
            source_id="s-1",
            status=IngestionStatus.FAILED,
            document_id="doc-1",
            error=IngestionError(code="ERR", message="msg"),
        )
    assert "FAILED ingestion status cannot reference a generated document_id" in str(exc.value)


@pytest.mark.parametrize("status", [IngestionStatus.PENDING, IngestionStatus.PROCESSING])
def test_ingestion_result_pending_processing_invariant_rules(status):
    """PENDING and PROCESSING statuses must not contain errors or document artifacts."""
    # Valid pending/processing
    res = IngestionResult(source_id="s-1", status=status)
    assert res.status == status
    assert res.error is None
    assert res.document_id is None

    # Invalid: with error
    with pytest.raises(ValidationError) as exc:
        IngestionResult(
            source_id="s-1",
            status=status,
            error=IngestionError(code="ERR", message="msg"),
        )
    assert f"{status.value} ingestion status cannot contain an error" in str(exc.value)

    # Invalid: with document_id
    with pytest.raises(ValidationError) as exc:
        IngestionResult(
            source_id="s-1",
            status=status,
            document_id="doc-1",
        )
    assert f"{status.value} ingestion status cannot reference a generated document_id" in str(exc.value)


@pytest.mark.parametrize("model_cls", [SourceManifest, IngestionError, IngestionResult])
def test_ingestion_models_json_schema_structure(model_cls):
    """Verify that Ingestion models export valid JSON Schemas."""
    schema = model_cls.model_json_schema()
    assert isinstance(schema, dict)
    assert schema.get("type") == "object"
    assert "properties" in schema
    assert "title" in schema


def test_ingestion_models_reject_unknown_root_fields():
    """Ingestion models must strictly reject unknown root fields."""
    with pytest.raises(ValidationError) as exc:
        SourceManifest(
            source_id="s-1",
            filename="f.pdf",
            byte_size=10,
            sha256=SAMPLE_SHA256,
            injected_unknown_field="hack",
        )
    assert "extra_forbidden" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        IngestionError(
            code="ERR",
            message="Msg",
            unknown_root="invalid",
        )
    assert "extra_forbidden" in str(exc.value)
