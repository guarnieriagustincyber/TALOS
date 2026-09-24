"""Unit tests for Context Engine 2.0: Late Chunking (Roadmap v1.1 Fase 5).

Covers:
- Preservation of complete function context in code.
- Automatic context detection (code / prose / mixed).
- Strict token boundary constraints (can_process).
- Contextual sensitivity of embeddings across distinct semantic scopes.
- Safe fallback to traditional chunking in KnowledgeStore when disabled or oversized.
- Conversion helper to canonical TALOS Chunk contracts.
"""

import numpy as np
import pytest

from study_engine.config import get_settings
from study_engine.retrieval.late_chunking import LateChunker, to_talos_chunks
from study_engine.storage.knowledge_store import KnowledgeStore


def test_late_chunking_preserves_function_context() -> None:
    """Verifica que una función C completa no se parte al medio y preserva contexto."""
    document = """
    void calcular_suma(int *arr, int n) {
        int suma = 0;
        for (int i = 0; i < n; i++) {
            suma += arr[i];
        }
        return suma;
    }
    """

    chunker = LateChunker()
    chunks = chunker.late_chunk(document, chunk_size=50, overlap=10)

    # Verificar que todos los chunks tienen embeddings
    assert len(chunks) > 0
    for chunk in chunks:
        assert "embedding" in chunk
        assert len(chunk["embedding"]) > 0
        assert chunk["chunking_method"] == "late"

    # Verificar que al menos un chunk contiene la firma de la función
    function_signature = "void calcular_suma"
    assert any(function_signature in chunk["text"] for chunk in chunks)


def test_late_chunking_detects_code_context() -> None:
    """Verifica detección de tipo de contexto (code/prose/mixed)."""
    code_document = """
    int main() {
        printf("Hello World");
        return 0;
    }
    """

    prose_document = """
    La memoria virtual es una técnica de gestión de memoria que permite
    a los procesos usar más memoria de la físicamente disponible.
    """

    chunker = LateChunker()

    code_chunks = chunker.late_chunk(code_document)
    prose_chunks = chunker.late_chunk(prose_document)

    # Verificar detección de contexto
    assert any(chunk["context_type"] == "code" for chunk in code_chunks)
    assert any(chunk["context_type"] == "prose" for chunk in prose_chunks)


def test_late_chunking_detects_mixed_context() -> None:
    """Verifica detección de contexto mixto cuando contiene pocos indicadores de código."""
    mixed_text = "El comando de prueba contiene void como única palabra clave técnica."
    assert LateChunker._detect_context_type(mixed_text) == "mixed"


def test_late_chunking_respects_max_tokens() -> None:
    """Verifica que respeta el límite de max_document_tokens."""
    # Crear documento que exceda el límite
    long_document = "word " * 10000  # ~10k tokens

    chunker = LateChunker(max_document_tokens=5000)

    # Debe rechazar procesar por exceder el límite
    assert not chunker.can_process(long_document)

    # Pero debe poder procesar documentos más cortos
    short_document = "word " * 100
    assert chunker.can_process(short_document)


def test_late_chunking_fallback_to_traditional() -> None:
    """Verifica fallback a chunking tradicional cuando Late Chunking falla o está desactivado."""
    settings = get_settings()
    original_value = settings.enable_late_chunking
    settings.enable_late_chunking = False

    try:
        store = KnowledgeStore()
        document = "Test document " * 100

        chunks = store.chunk_document(document, source_id="test")

        # Verificar que usó chunking tradicional
        assert len(chunks) > 0
        assert all(chunk["chunking_method"] == "traditional" for chunk in chunks)
        assert all("embedding" in chunk and len(chunk["embedding"]) > 0 for chunk in chunks)
    finally:
        settings.enable_late_chunking = original_value


def test_late_chunking_fallback_on_oversized_document() -> None:
    """Verifica fallback a chunking tradicional cuando el documento excede max_document_tokens."""
    settings = get_settings()
    original_enabled = settings.enable_late_chunking
    original_max = settings.late_chunking_max_tokens

    settings.enable_late_chunking = True
    settings.late_chunking_max_tokens = 50  # Límite muy bajo para forzar fallback

    try:
        store = KnowledgeStore()
        long_document = "Palabra de prueba para exceder el limite " * 20

        chunks = store.chunk_document(long_document, source_id="test_oversized")
        assert len(chunks) > 0
        assert all(chunk["chunking_method"] == "traditional" for chunk in chunks)
    finally:
        settings.enable_late_chunking = original_enabled
        settings.late_chunking_max_tokens = original_max


def test_late_chunking_embeddings_are_contextual() -> None:
    """Verifica que embeddings capturan contexto global."""
    # Dos oraciones con la misma palabra 'puntero' pero diferente contexto semántico
    document = """
    El puntero apunta a la memoria del heap.
    El puntero del ratón se movió por la pantalla.
    """

    chunker = LateChunker()
    chunks = chunker.late_chunk(document, chunk_size=15, overlap=5)

    # Verificar que hay al menos 2 chunks
    assert len(chunks) >= 2

    # Los embeddings deben ser diferentes aunque compartan la palabra "puntero"
    # porque el contexto global es diferente (heap vs ratón)
    embedding_1 = chunks[0]["embedding"]
    embedding_2 = chunks[1]["embedding"]

    # No deben ser idénticos
    assert not np.array_equal(embedding_1, embedding_2)


def test_late_chunking_empty_and_whitespace_document() -> None:
    """Verifica manejo robusto de documentos vacíos o con solo espacios."""
    chunker = LateChunker()
    assert chunker.late_chunk("") == []
    assert chunker.late_chunk("   \n\t  ") == []


def test_to_talos_chunks_conversion() -> None:
    """Verifica que to_talos_chunks crea objetos canónicos Chunk con metadatos de late chunking."""
    chunker = LateChunker()
    chunks_dict = chunker.late_chunk("int main() { return 0; }", chunk_size=30, overlap=5)
    talos_chunks = to_talos_chunks(chunks_dict, document_id="doc_test", source_id="src_test")

    assert len(talos_chunks) == len(chunks_dict)
    first = talos_chunks[0]
    assert first.document_id == "doc_test"
    assert first.source_id == "src_test"
    assert first.id == "doc_test:chunk_0000"
    assert first.metadata["chunking_method"] == "late"
    assert first.metadata["context_type"] == "code"
