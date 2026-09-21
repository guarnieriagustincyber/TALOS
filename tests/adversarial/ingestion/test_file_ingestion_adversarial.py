"""Adversarial tests for S1.2 File Ingestion component.

Attacks:
- Path traversal attempts outside corpus root.
- Hostile, empty, and whitespace paths.
- Directories passed where regular files are expected.
- Strange and complex filenames (spaces, emojis, unicode, special symbols).
- Large binary files (streaming memory test).
- Binary random bytes and arbitrary file formats.
"""

import hashlib
import os
from pathlib import Path
import pytest

from study_engine.contracts.enums import IngestionStatus
from study_engine.ingestion.file_ingestion import (
    compute_file_sha256,
    create_source_manifest,
    ingest_file,
)


def test_adversarial_path_traversal_outside_corpus_root(tmp_path):
    corpus_root = tmp_path / "CorpusRoot"
    corpus_root.mkdir()

    outside_file = tmp_path / "sensitive_outside.pdf"
    outside_file.write_bytes(b"Sensitive Host Content")

    # Ingesting outside file when corpus_root is restricted must fail
    result = ingest_file(
        file_path=outside_file,
        corpus_root=corpus_root,
    )
    assert result.status == IngestionStatus.FAILED
    assert result.error is not None
    assert result.error.code == "PATH_TRAVERSAL_DETECTED"

    with pytest.raises(ValueError) as exc:
        create_source_manifest(
            file_path=outside_file,
            corpus_root=corpus_root,
        )
    assert "is outside corpus root" in str(exc.value)


@pytest.mark.parametrize("invalid_path", ["", "   ", "\t\n"])
def test_adversarial_empty_or_whitespace_paths(invalid_path):
    result = ingest_file(file_path=invalid_path)
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "EMPTY_PATH"


def test_adversarial_directory_as_file(tmp_path):
    fake_file_dir = tmp_path / "not_a_file.pdf"
    fake_file_dir.mkdir()

    result = ingest_file(file_path=fake_file_dir)
    assert result.status == IngestionStatus.FAILED
    assert result.error.code == "NOT_A_FILE"


def test_adversarial_complex_unicode_and_special_filenames(tmp_path):
    complex_filename = "📚 Joyanes — Cap 1 (Algoritmos) & Ejercicios #1 + [2026] 🔥.pdf"
    complex_file = tmp_path / complex_filename
    content = b"%PDF-1.4 Unicode Filename Test"
    complex_file.write_bytes(content)

    manifest = create_source_manifest(file_path=complex_file)
    assert manifest.filename == complex_filename
    assert manifest.sha256 == hashlib.sha256(content).hexdigest()
    assert manifest.byte_size == len(content)

    result = ingest_file(file_path=complex_file)
    assert result.status == IngestionStatus.COMPLETED
    assert result.manifest.filename == complex_filename


def test_adversarial_large_file_streaming(tmp_path):
    """5 MB file must hash correctly in streaming mode without loading entire file at once."""
    large_file = tmp_path / "large_corpus_book.pdf"
    chunk_pattern = b"0123456789ABCDEF" * 4096  # 64 KB block
    total_blocks = 80  # ~5.12 MB

    hasher = hashlib.sha256()
    with open(large_file, "wb") as f:
        for _ in range(total_blocks):
            f.write(chunk_pattern)
            hasher.update(chunk_pattern)

    expected_hash = hasher.hexdigest()

    manifest = create_source_manifest(file_path=large_file, chunk_size=32768)
    assert manifest.byte_size == total_blocks * len(chunk_pattern)
    assert manifest.sha256 == expected_hash


def test_adversarial_random_binary_content(tmp_path):
    binary_file = tmp_path / "binary_data.bin"
    random_bytes = os.urandom(65536)
    binary_file.write_bytes(random_bytes)

    manifest = create_source_manifest(file_path=binary_file)
    assert manifest.media_type == "application/octet-stream"
    assert manifest.sha256 == hashlib.sha256(random_bytes).hexdigest()
