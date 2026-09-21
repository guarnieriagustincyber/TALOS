"""Contract tests for S1.5 Document Ingestion outputs."""

import json
from pathlib import Path
import pytest
from pypdf import PdfWriter

from study_engine.contracts.enums import IngestionStatus
from study_engine.contracts.ingestion import IngestionError, IngestionResult
from study_engine.ingestion.document_catalog import DocumentCatalog
from study_engine.ingestion.document_ingestion import ingest_document


def create_minimal_pdf(file_path: Path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(file_path, "wb") as f:
        writer.write(f)


def test_ingestion_result_completed_contract(tmp_path):
    pdf_file = tmp_path / "doc.pdf"
    create_minimal_pdf(pdf_file)

    result = ingest_document(pdf_file, "source-123")

    assert isinstance(result, IngestionResult)
    assert result.status == IngestionStatus.COMPLETED
    assert result.error is None
    assert result.document is not None
    assert result.document_id == result.document.id
    assert result.source_id == "source-123"

    # JSON roundtrip
    json_str = result.model_dump_json()
    reconstructed = IngestionResult.model_validate_json(json_str)
    assert reconstructed == result


def test_ingestion_result_failed_contract(tmp_path):
    missing_file = tmp_path / "non_existent.pdf"

    result = ingest_document(missing_file, "source-123")

    assert isinstance(result, IngestionResult)
    assert result.status == IngestionStatus.FAILED
    assert result.document is None
    assert result.document_id is None
    assert isinstance(result.error, IngestionError)
    assert result.error.code == "FILE_NOT_FOUND"

    # JSON roundtrip
    json_str = result.model_dump_json()
    reconstructed = IngestionResult.model_validate_json(json_str)
    assert reconstructed == result


def test_document_catalog_registration_compatibility(tmp_path):
    """Verify that IngestionResult.document is immediately registerable in DocumentCatalog."""
    pdf_file = tmp_path / "ch01.pdf"
    create_minimal_pdf(pdf_file)

    ingest_res = ingest_document(pdf_file, "joyanes-fp-4e", title="Capítulo 1")
    assert ingest_res.status == IngestionStatus.COMPLETED

    catalog = DocumentCatalog()
    registered_doc = catalog.register(ingest_res.document)

    assert registered_doc == ingest_res.document
    assert catalog.count() == 1
    assert catalog.get("joyanes-fp-4e:ch01") == ingest_res.document
