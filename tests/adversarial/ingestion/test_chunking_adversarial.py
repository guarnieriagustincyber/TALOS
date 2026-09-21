"""Adversarial and boundary tests for S1.6 Deterministic Document Chunking."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.document import Document
from study_engine.ingestion.chunking import ChunkConfig, chunk_document


@pytest.mark.parametrize("invalid_size", [0, -1, -500])
def test_adversarial_invalid_chunk_size(invalid_size):
    with pytest.raises((ValidationError, ValueError)):
        ChunkConfig(chunk_size=invalid_size)


@pytest.mark.parametrize("invalid_overlap", [-1, -100])
def test_adversarial_invalid_negative_overlap(invalid_overlap):
    with pytest.raises((ValidationError, ValueError)):
        ChunkConfig(chunk_size=500, chunk_overlap=invalid_overlap)


@pytest.mark.parametrize("overlap", [500, 600, 1000])
def test_adversarial_overlap_greater_or_equal_to_size(overlap):
    with pytest.raises((ValidationError, ValueError)):
        ChunkConfig(chunk_size=500, chunk_overlap=overlap)


def test_adversarial_invalid_document_type():
    with pytest.raises(TypeError):
        chunk_document("not-a-document")

    with pytest.raises(TypeError):
        chunk_document(None)


@pytest.mark.parametrize("invalid_id", ["", "   "])
def test_adversarial_invalid_document_id(invalid_id):
    with pytest.raises((ValidationError, ValueError)):
        doc = Document(id=invalid_id, source_id="src-1", title="Title", content="Content")
        chunk_document(doc)


@pytest.mark.parametrize("invalid_source_id", ["", "   "])
def test_adversarial_invalid_document_source_id(invalid_source_id):
    with pytest.raises((ValidationError, ValueError)):
        doc = Document(id="doc-1", source_id=invalid_source_id, title="Title", content="Content")
        chunk_document(doc)



def test_adversarial_monolithic_100k_characters():
    text = "Z" * 100_000
    doc = Document(id="doc-giant", source_id="src-1", title="Giant", content=text)
    config = ChunkConfig(chunk_size=1000, chunk_overlap=150)
    chunks = chunk_document(doc, config)

    assert len(chunks) > 100
    for idx, c in enumerate(chunks):
        assert len(c.content) <= 1000
        assert c.index == idx
        assert c.id == f"doc-giant:chunk_{idx:04d}"


def test_adversarial_null_bytes_and_control_chars():
    text = "Texto con \x00 null bytes y \x01\x02\x03 caracteres de control \n\n Segundo párrafo."
    doc = Document(id="doc-ctrl", source_id="src-1", title="Control", content=text)
    config = ChunkConfig(chunk_size=30, chunk_overlap=5)
    chunks = chunk_document(doc, config)

    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.content) <= 30


def test_adversarial_large_10mb_document():
    # 5 MB of text (approx 50,000 lines)
    paragraph = "Este es un párrafo de prueba con contenido técnico para medir rendimiento y estabilidad de memoria.\n\n"
    text = paragraph * 50_000
    doc = Document(id="doc-huge", source_id="src-huge", title="Huge", content=text)
    config = ChunkConfig(chunk_size=2000, chunk_overlap=200)

    chunks = chunk_document(doc, config)
    assert len(chunks) > 1000
    assert chunks[0].index == 0
    assert chunks[-1].index == len(chunks) - 1
    assert chunks[0].token_count is None


def test_adversarial_repeated_determinism():
    text = "Texto determinista con múltiples párrafos.\n\nSegundo párrafo.\n\nTercer párrafo."
    doc = Document(id="doc-det", source_id="src-det", title="Det", content=text)
    config = ChunkConfig(chunk_size=40, chunk_overlap=10)

    run1 = chunk_document(doc, config)
    run2 = chunk_document(doc, config)

    assert run1 == run2
