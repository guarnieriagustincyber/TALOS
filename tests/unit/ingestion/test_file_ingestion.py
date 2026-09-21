"""Unit tests for S1.2 File Ingestion component."""

import hashlib
from pathlib import Path
import pytest

from study_engine.contracts.enums import IngestionStatus
from study_engine.ingestion.file_ingestion import (
    compute_file_sha256,
    create_source_manifest,
    detect_media_type,
    ingest_file,
)


def test_detect_media_type_known_formats():
    assert detect_media_type("sample.pdf") == "application/pdf"
    assert detect_media_type("notes.md") == "text/markdown"
    assert detect_media_type("notes.markdown") == "text/markdown"
    assert detect_media_type("plain.txt") == "text/plain"
    assert detect_media_type("data.json") == "application/json"
    assert detect_media_type("config.yaml") == "application/yaml"
    assert detect_media_type("config.yml") == "application/yaml"
    assert detect_media_type("doc.epub") == "application/epub+zip"
    assert detect_media_type("script.py") == "text/x-python"


def test_detect_media_type_fallback():
    assert detect_media_type("unknown.unknownextension123") == "application/octet-stream"


def test_compute_file_sha256_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    expected_empty_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert compute_file_sha256(empty_file) == expected_empty_sha256


def test_compute_file_sha256_known_content(tmp_path):
    content = b"Study Engine Ingestion Test Content 2026\n"
    sample_file = tmp_path / "sample.txt"
    sample_file.write_bytes(content)

    expected_sha256 = hashlib.sha256(content).hexdigest()
    assert compute_file_sha256(sample_file) == expected_sha256


def test_compute_file_sha256_small_chunks(tmp_path):
    content = b"A" * 1000
    sample_file = tmp_path / "large_chunked.txt"
    sample_file.write_bytes(content)

    expected_sha256 = hashlib.sha256(content).hexdigest()
    assert compute_file_sha256(sample_file, chunk_size=16) == expected_sha256


def test_create_source_manifest_valid_file(tmp_path):
    pdf_file = tmp_path / "joyanes_algoritmos.pdf"
    content = b"%PDF-1.4 Mock PDF binary content"
    pdf_file.write_bytes(content)

    manifest = create_source_manifest(
        file_path=pdf_file,
        source_id="joyanes-fp-4e",
        metadata={"subject": "Algoritmos"},
    )

    assert manifest.source_id == "joyanes-fp-4e"
    assert manifest.filename == "joyanes_algoritmos.pdf"
    assert manifest.byte_size == len(content)
    assert manifest.sha256 == hashlib.sha256(content).hexdigest()
    assert manifest.media_type == "application/pdf"
    assert manifest.metadata["subject"] == "Algoritmos"


def test_create_source_manifest_default_source_id(tmp_path):
    text_file = tmp_path / "tanenbaum_redes.txt"
    text_file.write_text("Redes de computadoras")

    manifest = create_source_manifest(file_path=text_file)
    assert manifest.source_id == "tanenbaum_redes"


def test_create_source_manifest_with_corpus_root(tmp_path):
    corpus_root = tmp_path / "StudyCorpus"
    fase_dir = corpus_root / "Fase-0" / "Joyanes"
    fase_dir.mkdir(parents=True)
    pdf_file = fase_dir / "capitulo_01.pdf"
    pdf_file.write_bytes(b"Capitulo 1")

    manifest = create_source_manifest(
        file_path=pdf_file,
        corpus_root=corpus_root,
    )
    assert manifest.file_path == "Fase-0/Joyanes/capitulo_01.pdf"


def test_create_source_manifest_file_not_found(tmp_path):
    non_existent = tmp_path / "non_existent.pdf"
    with pytest.raises(FileNotFoundError):
        create_source_manifest(file_path=non_existent)


def test_create_source_manifest_directory_path(tmp_path):
    dir_path = tmp_path / "some_dir"
    dir_path.mkdir()
    with pytest.raises(IsADirectoryError):
        create_source_manifest(file_path=dir_path)


def test_create_source_manifest_empty_path():
    with pytest.raises(ValueError):
        create_source_manifest(file_path="")


def test_ingest_file_success(tmp_path):
    pdf_file = tmp_path / "intro.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 Mock Introduction")

    result = ingest_file(
        file_path=pdf_file,
        source_id="intro-src",
        metadata={"phase": "Fase-0"},
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.source_id == "intro-src"
    assert result.manifest is not None
    assert result.manifest.filename == "intro.pdf"
    assert result.error is None
    assert result.document_id is None


def test_ingest_file_not_found(tmp_path):
    missing_file = tmp_path / "missing.pdf"
    result = ingest_file(file_path=missing_file, source_id="missing-src")

    assert result.status == IngestionStatus.FAILED
    assert result.source_id == "missing-src"
    assert result.error is not None
    assert result.error.code == "FILE_NOT_FOUND"
    assert result.manifest is None


def test_ingest_file_is_directory(tmp_path):
    dir_path = tmp_path / "nested_dir"
    dir_path.mkdir()

    result = ingest_file(file_path=dir_path, source_id="dir-src")

    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "NOT_A_FILE"


def test_ingest_file_empty_path():
    result = ingest_file(file_path="")

    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "EMPTY_PATH"


def test_ingest_file_permission_error(tmp_path, monkeypatch):
    test_file = tmp_path / "secret.pdf"
    test_file.write_bytes(b"secret binary")

    def mock_open(*args, **kwargs):
        raise PermissionError("Access is denied")

    monkeypatch.setattr("builtins.open", mock_open)
    result = ingest_file(file_path=test_file, source_id="src-perm")
    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "PERMISSION_DENIED"


def test_ingest_file_os_error(tmp_path, monkeypatch):
    test_file = tmp_path / "bad_disk.pdf"
    test_file.write_bytes(b"content")

    def mock_open(*args, **kwargs):
        raise OSError("Disk I/O failure")

    monkeypatch.setattr("builtins.open", mock_open)
    result = ingest_file(file_path=test_file, source_id="src-io")
    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "IO_ERROR"


def test_compute_file_sha256_chunk_size_boundaries(tmp_path):
    content = b"Deterministic chunk boundary test payload."
    test_file = tmp_path / "boundary.txt"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    # chunk_size = 1
    assert compute_file_sha256(test_file, chunk_size=1) == expected_hash

    # chunk_size extremely large
    assert compute_file_sha256(test_file, chunk_size=100_000_000) == expected_hash

    # chunk_size <= 0 must raise ValueError
    with pytest.raises(ValueError):
        compute_file_sha256(test_file, chunk_size=0)

    with pytest.raises(ValueError):
        compute_file_sha256(test_file, chunk_size=-1)


def test_create_source_manifest_invalid_chunk_size(tmp_path):
    test_file = tmp_path / "valid.txt"
    test_file.write_bytes(b"Valid")

    with pytest.raises(ValueError):
        create_source_manifest(file_path=test_file, chunk_size=0)

    with pytest.raises(ValueError):
        create_source_manifest(file_path=test_file, chunk_size=-100)


def test_ingest_file_invalid_chunk_size(tmp_path):
    test_file = tmp_path / "valid.txt"
    test_file.write_bytes(b"Valid")

    result = ingest_file(file_path=test_file, chunk_size=0)
    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "INVALID_CHUNK_SIZE"


def test_sha256_hash_integrity_independent_of_metadata(tmp_path):
    """Demonstrate that SHA-256 strictly reflects physical binary content and is invariant to metadata."""
    import os
    import time

    content = b"Identical physical byte stream."
    expected_hash = hashlib.sha256(content).hexdigest()

    # 1. Different filenames in different directories produce identical hash
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()

    file1 = dir1 / "book_edition_1.pdf"
    file2 = dir2 / "completely_different_name.txt"
    file1.write_bytes(content)
    file2.write_bytes(content)

    assert compute_file_sha256(file1) == expected_hash
    assert compute_file_sha256(file2) == expected_hash

    # 2. Modifying timestamps (mtime/atime) does NOT change hash
    old_time = time.time() - 100000
    os.utime(file1, (old_time, old_time))
    assert compute_file_sha256(file1) == expected_hash

    # 3. Two files of identical byte size but different content produce different hashes (size is not a proxy)
    file_a = tmp_path / "file_a.bin"
    file_b = tmp_path / "file_b.bin"
    file_a.write_bytes(b"AAAAAAAAAAAAAAAA")  # 16 bytes
    file_b.write_bytes(b"BBBBBBBBBBBBBBBB")  # 16 bytes

    assert file_a.stat().st_size == file_b.stat().st_size
    assert compute_file_sha256(file_a) != compute_file_sha256(file_b)


def test_ingest_file_generic_value_error(tmp_path, monkeypatch):
    test_file = tmp_path / "valid.txt"
    test_file.write_bytes(b"content")

    def mock_manifest(*args, **kwargs):
        raise ValueError("Generic invalid format value")

    monkeypatch.setattr("study_engine.ingestion.file_ingestion.create_source_manifest", mock_manifest)
    result = ingest_file(file_path=test_file, source_id="src-val")
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "INVALID_PATH"



