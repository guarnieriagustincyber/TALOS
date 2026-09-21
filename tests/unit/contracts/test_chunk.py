"""Unit tests for Chunk contract."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.chunk import Chunk


def test_chunk_valid_minimal():
    chunk = Chunk(
        id="chunk-001",
        document_id="doc-001",
        source_id="src-001",
        content="Un algoritmo es un conjunto ordenado de instrucciones...",
    )
    assert chunk.id == "chunk-001"
    assert chunk.document_id == "doc-001"
    assert chunk.source_id == "src-001"
    assert chunk.index == 0
    assert chunk.metadata == {}


def test_chunk_valid_full():
    chunk = Chunk(
        id="chunk-joyanes-1-12",
        document_id="doc-joyanes-ch1",
        source_id="joyanes-fp-4e",
        content="Los diagramas de flujo representan gráficamente un algoritmo.",
        page_start=12,
        page_end=13,
        chapter="Capítulo 1",
        section="1.4 Diagramas de Flujo",
        token_count=180,
        index=3,
        metadata={"extraction_method": "pdfplumber"},
    )
    assert chunk.page_start == 12
    assert chunk.page_end == 13
    assert chunk.token_count == 180
    assert chunk.index == 3


def test_chunk_missing_required():
    with pytest.raises(ValidationError):
        Chunk(document_id="doc-1", source_id="src-1", content="Text")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", source_id="src-1", content="Text")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="doc-1", content="Text")

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="doc-1", source_id="src-1")


def test_chunk_invalid_numbers():
    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="doc-1", source_id="src-1", content="Text", page_start=0)

    with pytest.raises(ValidationError):
        Chunk(id="c-1", document_id="doc-1", source_id="src-1", content="Text", token_count=-1)
