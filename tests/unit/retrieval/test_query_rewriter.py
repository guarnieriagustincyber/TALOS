"""Unit and integration tests for QueryRewriter (Semana 4)."""

import pytest

from study_engine.retrieval.query_rewriter import QueryRewriter


@pytest.fixture
def rewriter():
    return QueryRewriter()


def test_colloquial_synchronization_expansion(rewriter):
    """Verify informal concurrency questions expand to canonical keywords."""
    samples = [
        ("el coso de sincronización en C", ["semáforos", "mutex", "sección crítica"]),
        ("cómo hacer para que no se pisen los hilos", ["exclusión mutua", "race condition", "mutex"]),
        ("cuando dos procesos se traban y no avanzan", ["deadlock", "interbloqueo", "espera circular"]),
    ]

    for query, expected_tokens in samples:
        rewritten = rewriter.rewrite(query)
        assert len(rewritten) > len(query), f"Expected expansion for: '{query}'"
        for token in expected_tokens:
            assert token.lower() in rewritten.lower(), f"Expected '{token}' in '{rewritten}'"


def test_colloquial_memory_expansion(rewriter):
    """Verify informal memory management questions expand to canonical keywords."""
    samples = [
        ("la memoria a mano en c", ["asignación dinámica", "heap", "malloc", "free"]),
        ("dónde van las variables locales", ["stack", "marco de activación", "stack frame"]),
        ("el coso de la función que guarda las cosas", ["stack frame", "marco de activación", "rbp"]),
    ]

    for query, expected_tokens in samples:
        rewritten = rewriter.rewrite(query)
        assert len(rewritten) > len(query)
        for token in expected_tokens:
            assert token.lower() in rewritten.lower(), f"Expected '{token}' in '{rewritten}'"


def test_colloquial_pointers_and_cpu_expansion(rewriter):
    """Verify informal syntax and CPU hardware questions expand correctly."""
    samples = [
        ("cómo se usa la flechita en c", ["operador de acceso a miembros", "puntero"]),
        ("el asterisco adelante de un puntero", ["desreferenciación", "indirección"]),
        ("las cajitas de la cpu", ["registros del procesador"]),
        ("las banderitas de la cpu", ["rflags", "carry flag", "zero flag"]),
    ]

    for query, expected_tokens in samples:
        rewritten = rewriter.rewrite(query)
        assert len(rewritten) > len(query)
        for token in expected_tokens:
            assert token.lower() in rewritten.lower(), f"Expected '{token}' in '{rewritten}'"


def test_typo_corrections(rewriter):
    """Verify common student spelling errors in technical words are repaired."""
    assert "puntero" in rewriter.rewrite("como declarar un punter")
    assert "sincronización" in rewriter.rewrite("problemas de sincronisacion")
    assert "memoria" in rewriter.rewrite("fuga de memori")


def test_technical_query_preservation(rewriter):
    """Verify already-technical questions remain intact and non-mutated."""
    technical_query = "¿Cómo funciona la instrucción ret con respecto a rsp en x86_64?"
    rewritten = rewriter.rewrite(technical_query)
    assert rewritten == technical_query


def test_knowledge_store_search_hybrid_receives_prerewritten_query(tmp_path):
    """Verify KnowledgeStore.search_hybrid does not re-invoke rewriter, receiving query as-is (C1)."""
    from unittest.mock import MagicMock
    from study_engine.storage.knowledge_store import KnowledgeStore

    store = KnowledgeStore(f"sqlite:///{tmp_path}/test_ks.db")
    store.vector_search = MagicMock(return_value=[])
    store.fts_search = MagicMock(return_value=[])

    effective_query = "el coso de sincronización semáforos mutex"
    store.search_hybrid(
        query=effective_query,
        notebook_id="nb_test",
        limit=5,
    )

    assert store.vector_search.called
    assert store.fts_search.called

    call_query = store.vector_search.call_args[1]["query"]
    assert call_query == effective_query


def test_retrieval_service_is_authoritative_rewriter_chokepoint(tmp_path):
    """Verify RetrievalService.retrieve_evidence is the authoritative chokepoint for query rewriting (C1)."""
    from unittest.mock import MagicMock
    from study_engine.contracts.retrieval import RetrievalStrategy
    from study_engine.retrieval.service import RetrievalService
    from study_engine.storage.knowledge_store import KnowledgeStore

    store = KnowledgeStore(f"sqlite:///{tmp_path}/test_ks.db")
    store.contains_notebook = MagicMock(return_value=True)

    mock_retriever = MagicMock()
    mock_retriever.strategy = RetrievalStrategy.HYBRID
    mock_retriever.retrieve = MagicMock()
    mock_response = MagicMock()
    mock_response.items = []
    mock_retriever.retrieve.return_value = mock_response

    service = RetrievalService(store=store, retriever=mock_retriever)
    service.retrieve_evidence(
        query="¿qué es una pila?",
        notebook_id="nb_test",
        top_k=5,
    )

    assert mock_retriever.retrieve.called
    req = mock_retriever.retrieve.call_args[0][0]
    assert req.query == "¿qué es una pilas?"

