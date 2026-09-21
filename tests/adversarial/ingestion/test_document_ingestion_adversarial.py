"""Adversarial and boundary tests for S1.5 Document Ingestion."""

import os
from pathlib import Path
import pytest
from pypdf import PdfWriter

from study_engine.contracts.enums import IngestionStatus
from study_engine.ingestion.document_ingestion import ingest_document, slugify_filename


def test_adversarial_file_not_found():
    result = ingest_document("non_existent_file.pdf", "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "FILE_NOT_FOUND"


def test_adversarial_path_is_directory(tmp_path):
    sub_dir = tmp_path / "my_dir"
    sub_dir.mkdir()

    result = ingest_document(sub_dir, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "IS_DIRECTORY"


def test_adversarial_empty_file(tmp_path):
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.touch()

    result = ingest_document(empty_pdf, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "EMPTY_FILE"


def test_adversarial_corrupt_pdf(tmp_path):
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4\nInvalid binary junk \x00\xff\xfe random non-pdf streams")

    result = ingest_document(corrupt_pdf, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "INVALID_PDF"


def test_adversarial_encrypted_pdf(tmp_path):
    enc_pdf = tmp_path / "secret.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("super_secret_password")
    with open(enc_pdf, "wb") as f:
        writer.write(f)

    result = ingest_document(enc_pdf, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "ENCRYPTED_PDF"


def test_adversarial_unsupported_media_type(tmp_path):
    bin_file = tmp_path / "image.png"
    bin_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    result = ingest_document(bin_file, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "UNSUPPORTED_MEDIA_TYPE"


def test_adversarial_corpus_root_escape(tmp_path):
    corpus_root = tmp_path / "Corpus"
    corpus_root.mkdir()

    outside_file = tmp_path / "outside.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(outside_file, "wb") as f:
        writer.write(f)

    result = ingest_document(outside_file, "src-1", corpus_root=corpus_root)
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "PATH_TRAVERSAL"


@pytest.mark.parametrize("invalid_source_id", ["", "   ", None])
def test_adversarial_invalid_source_id(tmp_path, invalid_source_id):
    txt_file = tmp_path / "file.txt"
    txt_file.write_text("Hello")

    with pytest.raises(ValueError):
        ingest_document(txt_file, invalid_source_id)



@pytest.mark.parametrize("empty_path", ["", "   "])
def test_adversarial_empty_file_path(empty_path):
    result = ingest_document(empty_path, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "FILE_NOT_FOUND"


def test_adversarial_filename_slug_extreme_cases(tmp_path):
    # Emojis, unusual punctuation and accents
    extreme_name = "📄-Capítulo #01 (Versión 2.0) [Final] - ñ & % 🚀.pdf"
    pdf_file = tmp_path / extreme_name
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(pdf_file, "wb") as f:
        writer.write(f)

    result = ingest_document(pdf_file, "src-unicode")
    assert result.status == IngestionStatus.COMPLETED
    assert result.document.id == "src-unicode:capitulo-01-version-2-0-final-n"
    assert result.document.title == extreme_name[:-4]


def test_adversarial_broken_symlink(tmp_path):
    broken_link = tmp_path / "broken_link.pdf"
    os.symlink(tmp_path / "does_not_exist.pdf", broken_link)

    result = ingest_document(broken_link, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "FILE_NOT_FOUND"


def test_adversarial_large_text_file(tmp_path):
    large_txt = tmp_path / "large.txt"
    # Write 1 MB of text
    large_txt.write_text("A" * 1_000_000, encoding="utf-8")

    result = ingest_document(large_txt, "src-large")
    assert result.status == IngestionStatus.COMPLETED
    assert len(result.document.content) == 1_000_000
    assert result.document.page_count == 1


def test_adversarial_pdf_decrypt_exception(tmp_path, monkeypatch):
    from pypdf import PdfReader

    pdf_file = tmp_path / "enc.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("pw")
    with open(pdf_file, "wb") as f:
        writer.write(f)

    def mock_decrypt(self, pw):
        raise Exception("Decryption hardware fault")

    monkeypatch.setattr(PdfReader, "decrypt", mock_decrypt)

    result = ingest_document(pdf_file, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "ENCRYPTED_PDF"


def test_adversarial_txt_read_error(tmp_path, monkeypatch):
    txt_file = tmp_path / "read_err.txt"
    txt_file.write_text("hello")

    def mock_open(*args, **kwargs):
        raise OSError("I/O device error")

    import builtins
    monkeypatch.setattr(builtins, "open", mock_open)

    result = ingest_document(txt_file, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "READ_ERROR"


def test_adversarial_non_regular_file(tmp_path, monkeypatch):
    txt_file = tmp_path / "special.txt"
    txt_file.write_text("hello")

    # Mock is_file to return False while exists returns True
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    result = ingest_document(txt_file, "src-1")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "FILE_NOT_FOUND"
    assert "not a regular file" in result.error.message

