"""Unit tests for S1.6 Deterministic Document Chunking."""

import pytest
from study_engine.contracts.document import Document
from study_engine.ingestion.chunking import ChunkConfig, chunk_document


def test_chunk_empty_or_whitespace_document():
    doc_none = Document(id="doc-1", source_id="src-1", title="Title", content=None)
    assert chunk_document(doc_none) == []

    doc_empty = Document(id="doc-1", source_id="src-1", title="Title", content="")
    assert chunk_document(doc_empty) == []

    doc_ws = Document(id="doc-1", source_id="src-1", title="Title", content="   \n\t  \n  ")
    assert chunk_document(doc_ws) == []


def test_chunk_text_smaller_than_chunk_size():
    doc = Document(id="doc-small", source_id="src-1", title="Small", content="Contenido breve.")
    config = ChunkConfig(chunk_size=100, chunk_overlap=20)
    chunks = chunk_document(doc, config)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.id == "doc-small:chunk_0000"
    assert chunk.document_id == "doc-small"
    assert chunk.source_id == "src-1"
    assert chunk.content == "Contenido breve."
    assert chunk.index == 0
    assert chunk.token_count is None
    assert chunk.page_start is None
    assert chunk.page_end is None
    assert chunk.metadata["char_start"] == 0
    assert chunk.metadata["char_end"] == len("Contenido breve.")


def test_chunk_exact_chunk_size():
    text = "A" * 100
    doc = Document(id="doc-exact", source_id="src-1", title="Exact", content=text)
    config = ChunkConfig(chunk_size=100, chunk_overlap=20)
    chunks = chunk_document(doc, config)

    assert len(chunks) == 1
    assert chunks[0].content == text
    assert chunks[0].index == 0
    assert chunks[0].id == "doc-exact:chunk_0000"


def test_chunk_barely_larger_than_chunk_size():
    text = ("A" * 80) + " " + ("B" * 30)
    doc = Document(id="doc-split", source_id="src-1", title="Split", content=text)
    config = ChunkConfig(chunk_size=100, chunk_overlap=20)
    chunks = chunk_document(doc, config)

    assert len(chunks) == 2
    assert chunks[0].index == 0
    assert chunks[1].index == 1
    assert chunks[0].id == "doc-split:chunk_0000"
    assert chunks[1].id == "doc-split:chunk_0001"
    for c in chunks:
        assert len(c.content) <= 100


def test_chunk_multiple_paragraphs():
    p1 = "Primer párrafo de prueba con información fundamental."
    p2 = "Segundo párrafo que continúa desarrollando los conceptos clave."
    p3 = "Tercer párrafo de cierre con conclusiones de la sección."
    text = f"{p1}\n\n{p2}\n\n{p3}"

    doc = Document(id="doc-para", source_id="src-1", title="Paragraphs", content=text)
    config = ChunkConfig(chunk_size=70, chunk_overlap=15)
    chunks = chunk_document(doc, config)

    assert len(chunks) >= 3
    for idx, c in enumerate(chunks):
        assert c.index == idx
        assert c.id == f"doc-para:chunk_{idx:04d}"
        assert len(c.content) <= 70
        assert c.token_count is None


def test_chunk_multiple_sentences():
    s1 = "Primera oración de prueba."
    s2 = "Segunda oración que sigue."
    s3 = "¿Tercera oración interrogativa?"
    s4 = "¡Cuarta oración exclamativa!"
    s5 = "Quinta oración con punto y coma; que separa ideas."
    text = f"{s1} {s2} {s3} {s4} {s5}"

    doc = Document(id="doc-sent", source_id="src-1", title="Sentences", content=text)
    config = ChunkConfig(chunk_size=60, chunk_overlap=10)
    chunks = chunk_document(doc, config)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.content) <= 60
        assert c.token_count is None


def test_chunk_fallback_hard_character_cut():
    # 250 characters with no spaces
    text = "X" * 250
    doc = Document(id="doc-mono", source_id="src-1", title="Monolithic", content=text)
    config = ChunkConfig(chunk_size=100, chunk_overlap=20)
    chunks = chunk_document(doc, config)

    assert len(chunks) >= 3
    for c in chunks:
        assert len(c.content) <= 100
        assert c.token_count is None


def test_chunk_overlap_preservation():
    text = "Palabra1 Palabra2 Palabra3 Palabra4 Palabra5 Palabra6 Palabra7 Palabra8 Palabra9 Palabra10"
    doc = Document(id="doc-ov", source_id="src-1", title="Overlap", content=text)
    config = ChunkConfig(chunk_size=40, chunk_overlap=15)
    chunks = chunk_document(doc, config)

    assert len(chunks) > 1
    # Check that adjacent chunks share text
    for i in range(len(chunks) - 1):
        c1 = chunks[i].content
        c2 = chunks[i + 1].content
        # Ensure there is an overlap window or sequential progress
        assert chunks[i + 1].metadata["char_start"] < chunks[i].metadata["char_end"]


def test_chunk_metadata_inheritance():
    doc = Document(
        id="joyanes-fp-4e:capitulo-01",
        source_id="joyanes-fp-4e",
        title="Capítulo 1",
        content="Texto del capítulo de algoritmos y programación.",
        metadata={"chapter": "Capítulo 1", "section": "1.2 Algoritmos", "extra": 123},
    )
    config = ChunkConfig(chunk_size=1000, chunk_overlap=150)
    chunks = chunk_document(doc, config)

    assert len(chunks) == 1
    c = chunks[0]
    assert c.chapter == "Capítulo 1"
    assert c.section == "1.2 Algoritmos"
    assert c.metadata["chunking_strategy"] == "recursive_delimiter"
    assert c.metadata["chunk_size"] == 1000
    assert c.metadata["chunk_overlap"] == 150
    assert c.token_count is None


def test_chunk_unicode_and_accents():
    text = "Programación en C: estructuras, punteros y gestión de memoria dinámica 🚀. ¿Todo claro?"
    doc = Document(id="doc-uni", source_id="src-1", title="Unicode", content=text)
    config = ChunkConfig(chunk_size=45, chunk_overlap=10)
    chunks = chunk_document(doc, config)

    assert len(chunks) >= 2
    reconstructed = "".join(c.content for c in chunks)
    assert "🚀" in reconstructed
    assert "Programación" in reconstructed


def test_chunk_repetitive_content():
    text = "word " * 200
    doc = Document(id="doc-rep", source_id="src-1", title="Repetitive", content=text)
    config = ChunkConfig(chunk_size=80, chunk_overlap=20)
    chunks = chunk_document(doc, config)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.content) <= 80


def test_chunk_mixed_normal_and_monolithic_text():
    # Normal paragraph followed by a huge block of 200 chars without delimiters
    text = "Primer párrafo normal corto.\n\n" + ("M" * 200)
    doc = Document(id="doc-mixed", source_id="src-1", title="Mixed", content=text)
    config = ChunkConfig(chunk_size=50, chunk_overlap=10)
    chunks = chunk_document(doc, config)

    assert len(chunks) >= 4
    for idx, c in enumerate(chunks):
        assert len(c.content) <= 50
        assert c.index == idx

