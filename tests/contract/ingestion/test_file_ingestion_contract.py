"""Contract tests for S1.2 File Ingestion output models."""

import json
from pathlib import Path
import pytest

from study_engine.contracts import (
    IngestionResult,
    IngestionStatus,
    SourceManifest,
)
from study_engine.ingestion import create_source_manifest, ingest_file


def test_source_manifest_contract_conformance(tmp_path):
    sample_file = tmp_path / "stallings_redes.pdf"
    content = b"%PDF-1.5 Stallings Data and Computer Communications"
    sample_file.write_bytes(content)

    manifest = create_source_manifest(
        file_path=sample_file,
        source_id="stallings-redes-7e",
        metadata={"subject": "Redes"},
    )

    # Must be valid SourceManifest instance
    assert isinstance(manifest, SourceManifest)

    # Dict roundtrip
    dumped_dict = manifest.model_dump()
    reconstructed_dict = SourceManifest.model_validate(dumped_dict)
    assert reconstructed_dict == manifest

    # JSON roundtrip
    dumped_json = manifest.model_dump_json()
    reconstructed_json = SourceManifest.model_validate_json(dumped_json)
    assert reconstructed_json == manifest

    # Ensure SHA-256 conforms strictly to 64 hex characters
    assert len(manifest.sha256) == 64
    assert all(c in "0123456789abcdefABCDEF" for c in manifest.sha256)


def test_ingestion_result_completed_contract_conformance(tmp_path):
    sample_file = tmp_path / "valid.pdf"
    sample_file.write_bytes(b"Valid PDF binary")

    result = ingest_file(file_path=sample_file, source_id="src-valid")

    assert isinstance(result, IngestionResult)
    assert result.status == IngestionStatus.COMPLETED
    assert result.error is None
    assert result.document_id is None

    # JSON serialization and roundtrip
    json_data = json.loads(result.model_dump_json())
    assert json_data["status"] == "COMPLETED"
    assert json_data["error"] is None

    reconstructed = IngestionResult.model_validate_json(result.model_dump_json())
    assert reconstructed == result


def test_ingestion_result_failed_contract_conformance(tmp_path):
    missing_file = tmp_path / "not_there.pdf"
    result = ingest_file(file_path=missing_file, source_id="src-missing")

    assert isinstance(result, IngestionResult)
    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.document_id is None

    # JSON serialization and roundtrip
    reconstructed = IngestionResult.model_validate_json(result.model_dump_json())
    assert reconstructed == result
    assert reconstructed.error.code == "FILE_NOT_FOUND"
