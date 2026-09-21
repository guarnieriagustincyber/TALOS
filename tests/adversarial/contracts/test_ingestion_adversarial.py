"""Adversarial tests for Ingestion subsystem contracts (S1.1).

Attacks:
- Hostile and corrupted SHA-256 strings (wrong lengths, non-hex, null bytes, path traversal strings).
- Negative, float, and non-integer byte sizes.
- IngestionStatus casing, misspelling, and cross-enum mutations.
- State-inconsistency attacks across IngestionResult.
- Malformed error objects and non-dict details.
- JSON tampering post-serialization.
"""

import json
import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    IngestionError,
    IngestionResult,
    IngestionStatus,
    SourceManifest,
    SourceRole,
)

SAMPLE_SHA256 = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"


@pytest.mark.parametrize(
    "corrupted_sha256",
    [
        "12345",  # too short
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcde",  # 63 chars
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdefa",  # 65 chars
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdeg",  # 'g' is non-hex
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcde ",  # trailing space
        " 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # leading space
        "../../../../../../../../etc/passwd",  # path traversal attack
        "' OR '1'='1' --",  # SQL injection attack
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc\x00ef",  # null byte
        "🔥" * 64,  # emoji sequence
        "",
        None,
    ],
)
def test_source_manifest_rejects_corrupted_sha256(corrupted_sha256):
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="src-1",
            filename="file.pdf",
            byte_size=1024,
            sha256=corrupted_sha256,
        )


@pytest.mark.parametrize("invalid_byte_size", [-1, -100, -999999999, "invalid_size", 3.14, [1024], {"size": 1024}])
def test_source_manifest_rejects_invalid_byte_size(invalid_byte_size):
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="src-1",
            filename="file.pdf",
            byte_size=invalid_byte_size,
            sha256=SAMPLE_SHA256,
        )


@pytest.mark.parametrize(
    "corrupted_status",
    [
        "completed",
        "Completed",
        "cOMPLETED",
        "COMPLETE",
        "SUCCESS",
        "FAILED_INGESTION",
        "FAILURE",
        "PRIMARY",  # SourceRole value injected
        "SUPPORTED",  # EvidenceStatus value injected
        "",
        " ",
        1,
        True,
        None,
    ],
)
def test_ingestion_result_rejects_corrupted_status(corrupted_status):
    with pytest.raises(ValidationError):
        IngestionResult(source_id="src-1", status=corrupted_status)


def test_ingestion_result_rejects_tampered_completed_state_with_error():
    """Tampered JSON injecting an error into a COMPLETED result must fail validation."""
    valid_completed_json = json.dumps(
        {
            "source_id": "src-1",
            "status": "COMPLETED",
            "document_id": "doc-1",
            "error": {"code": "FORGED_ERROR", "message": "Injected error into completed state"},
        }
    )
    with pytest.raises(ValidationError) as exc:
        IngestionResult.model_validate_json(valid_completed_json)
    assert "COMPLETED ingestion status cannot contain an error" in str(exc.value)


def test_ingestion_result_rejects_tampered_failed_state_with_document_artifact():
    """Tampered JSON injecting a document_id into a FAILED result must fail validation."""
    valid_failed_json = json.dumps(
        {
            "source_id": "src-1",
            "status": "FAILED",
            "document_id": "forged-doc-artifact-id",
            "error": {"code": "CORRUPT_FILE", "message": "File corruption occurred"},
        }
    )
    with pytest.raises(ValidationError) as exc:
        IngestionResult.model_validate_json(valid_failed_json)
    assert "FAILED ingestion status cannot reference a generated document_id" in str(exc.value)


def test_ingestion_error_rejects_non_dict_details():
    with pytest.raises(ValidationError):
        IngestionError(code="ERR", message="Message", details="not-a-dict")

    with pytest.raises(ValidationError):
        IngestionError(code="ERR", message="Message", details=["item1", "item2"])


def test_source_manifest_metadata_key_shadowing():
    """Manifest metadata with shadowed keys must not collide with root fields."""
    manifest = SourceManifest(
        source_id="root-source",
        filename="physical.pdf",
        byte_size=5000,
        sha256=SAMPLE_SHA256,
        metadata={"source_id": "inner-source", "byte_size": 9999, "sha256": "custom-inner-hash"},
    )
    assert manifest.source_id == "root-source"
    assert manifest.byte_size == 5000
    assert manifest.metadata["source_id"] == "inner-source"
    assert manifest.metadata["byte_size"] == 9999
