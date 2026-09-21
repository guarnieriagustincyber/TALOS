"""Unit tests for SourceManifest, IngestionError, and IngestionResult contracts."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.enums import IngestionStatus
from study_engine.contracts.ingestion import IngestionError, IngestionResult, SourceManifest

VALID_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
VALID_SHA256_UPPER = "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"


def test_source_manifest_valid_minimal():
    manifest = SourceManifest(
        source_id="joyanes-fp-4e",
        filename="joyanes_programacion.pdf",
        byte_size=15420000,
        sha256=VALID_SHA256,
    )
    assert manifest.source_id == "joyanes-fp-4e"
    assert manifest.filename == "joyanes_programacion.pdf"
    assert manifest.byte_size == 15420000
    assert manifest.sha256 == VALID_SHA256
    assert manifest.media_type == "application/pdf"
    assert manifest.file_path is None
    assert manifest.metadata == {}


def test_source_manifest_valid_full():
    manifest = SourceManifest(
        source_id="tanenbaum-redes-5e",
        filename="redes_tanenbaum.pdf",
        file_path="FADENA/Materia-01/redes_tanenbaum.pdf",
        byte_size=24500000,
        sha256=VALID_SHA256_UPPER,
        media_type="application/pdf",
        metadata={"scanned": False, "language_detected": "es"},
    )
    assert manifest.file_path == "FADENA/Materia-01/redes_tanenbaum.pdf"
    assert manifest.metadata["language_detected"] == "es"


def test_source_manifest_zero_byte_size_valid():
    manifest = SourceManifest(
        source_id="empty-src",
        filename="empty.txt",
        byte_size=0,
        sha256=VALID_SHA256,
        media_type="text/plain",
    )
    assert manifest.byte_size == 0


def test_source_manifest_negative_byte_size_rejected():
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="src-1",
            filename="file.pdf",
            byte_size=-1,
            sha256=VALID_SHA256,
        )


@pytest.mark.parametrize(
    "invalid_sha256",
    [
        "too-short",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85",  # 63 chars
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8555",  # 65 chars
        "g3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # 'g' invalid hex
        "",
        "   ",
        None,
        12345,
    ],
)
def test_source_manifest_invalid_sha256_rejected(invalid_sha256):
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="src-1",
            filename="file.pdf",
            byte_size=100,
            sha256=invalid_sha256,
        )


def test_source_manifest_empty_strings_rejected():
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="",
            filename="file.pdf",
            byte_size=100,
            sha256=VALID_SHA256,
        )

    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="src-1",
            filename="",
            byte_size=100,
            sha256=VALID_SHA256,
        )


def test_ingestion_error_valid():
    err = IngestionError(
        code="UNSUPPORTED_ENCODING",
        message="The file contains unsupported binary encoding.",
        details={"offset": 1024},
    )
    assert err.code == "UNSUPPORTED_ENCODING"
    assert err.details["offset"] == 1024


def test_ingestion_error_empty_fields_rejected():
    with pytest.raises(ValidationError):
        IngestionError(code="", message="Message")

    with pytest.raises(ValidationError):
        IngestionError(code="CODE", message="")


def test_ingestion_result_completed_valid():
    manifest = SourceManifest(
        source_id="joyanes-fp-4e",
        filename="joyanes.pdf",
        byte_size=1000,
        sha256=VALID_SHA256,
    )
    res = IngestionResult(
        source_id="joyanes-fp-4e",
        status=IngestionStatus.COMPLETED,
        manifest=manifest,
        document_id="doc-joyanes-001",
        metadata={"duration_ms": 350},
    )
    assert res.status == IngestionStatus.COMPLETED
    assert res.document_id == "doc-joyanes-001"
    assert res.error is None


def test_ingestion_result_failed_valid():
    err = IngestionError(code="CORRUPT_PDF_HEADER", message="PDF header is corrupt.")
    res = IngestionResult(
        source_id="corrupted-src",
        status=IngestionStatus.FAILED,
        error=err,
    )
    assert res.status == IngestionStatus.FAILED
    assert res.error.code == "CORRUPT_PDF_HEADER"
    assert res.document_id is None


def test_ingestion_result_pending_and_processing_valid():
    res_pending = IngestionResult(
        source_id="src-pending",
        status=IngestionStatus.PENDING,
    )
    assert res_pending.status == IngestionStatus.PENDING
    assert res_pending.error is None
    assert res_pending.document_id is None

    res_proc = IngestionResult(
        source_id="src-proc",
        status=IngestionStatus.PROCESSING,
    )
    assert res_proc.status == IngestionStatus.PROCESSING


def test_ingestion_result_with_document_valid():
    from study_engine.contracts.document import Document

    doc = Document(id="doc-1", source_id="src-1", title="Title")
    res = IngestionResult(
        source_id="src-1",
        status=IngestionStatus.COMPLETED,
        document_id="doc-1",
        document=doc,
    )
    assert res.document == doc
    assert res.document_id == "doc-1"


def test_ingestion_result_document_id_mismatch_rejected():
    from study_engine.contracts.document import Document

    doc = Document(id="doc-1", source_id="src-1", title="Title")
    with pytest.raises(ValidationError) as exc:
        IngestionResult(
            source_id="src-1",
            status=IngestionStatus.COMPLETED,
            document_id="different-id",
            document=doc,
        )
    assert "does not match document.id" in str(exc.value)


def test_ingestion_result_failed_with_document_rejected():
    from study_engine.contracts.document import Document

    doc = Document(id="doc-1", source_id="src-1", title="Title")
    err = IngestionError(code="ERR", message="Failed")
    with pytest.raises(ValidationError):
        IngestionResult(
            source_id="src-1",
            status=IngestionStatus.FAILED,
            error=err,
            document=doc,
        )


@pytest.mark.parametrize("status", [IngestionStatus.PENDING, IngestionStatus.PROCESSING])
def test_ingestion_result_pending_processing_with_document_rejected(status):
    from study_engine.contracts.document import Document

    doc = Document(id="doc-1", source_id="src-1", title="Title")
    with pytest.raises(ValidationError):
        IngestionResult(
            source_id="src-1",
            status=status,
            document=doc,
        )
