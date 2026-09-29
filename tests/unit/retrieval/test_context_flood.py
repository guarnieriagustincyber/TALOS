"""Unit test verifying Context Flood (Fix S2.1) and Multi-Source Packing."""

from unittest.mock import MagicMock
from study_engine.contracts.search import SearchResult
from study_engine.web.dependencies import AppContainer
from study_engine.web.routes.chat import _assemble_epistemic_context


def test_assemble_epistemic_context_supports_30_chunks_and_diversity(
    web_state_test_copy,
):
    # Setup mock store returning 30 search results across 3 sources
    mock_store = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("src_tanenbaum", "Sistemas Operativos Modernos", "hash1", "Andrew S. Tanenbaum"),
        ("src_silberschatz", "Operating System Concepts", "hash2", "Silberschatz et al."),
        ("src_stallings", "Operating Systems Internals", "hash3", "William Stallings"),
    ]
    mock_conn.cursor.return_value = mock_cursor
    mock_store.engine.transaction.return_value.__enter__.return_value = mock_conn

    # 30 simulated chunks from 3 sources
    results = []
    sources = ["src_tanenbaum", "src_silberschatz", "src_stallings"]
    for i in range(30):
        src = sources[i % 3]
        results.append(
            SearchResult(
                chunk_id=f"c_{i}",
                document_id=f"doc_{i}",
                source_id=src,
                score=0.95 - (i * 0.01),
                snippet=f"Snippet for chunk {i}",
                content=f"Detailed textbook explanation for chunk {i} discussing synchronization.",
                index=i,
                page_start=10 + i,
                page_end=11 + i,
            )
        )
    mock_store.search_hybrid.return_value = results

    container = AppContainer(working_dir=web_state_test_copy, use_mock=True)
    pack, raw_chunks = _assemble_epistemic_context(
        store=mock_store,
        container=container,
        prompt_text="¿Cómo funciona la sincronización entre procesos?",
        target_notebook_id="fadena-so2",
    )

    assert pack is not None
    assert len(raw_chunks) == 30
    assert len(pack.chunks) == 30

    # Verify multi-source representation in the 30 chunks
    sources_in_chunks = {c["source_id"] for c in raw_chunks}
    assert len(sources_in_chunks) == 3
    assert "src_tanenbaum" in sources_in_chunks
    assert "src_silberschatz" in sources_in_chunks
    assert "src_stallings" in sources_in_chunks

    # Verify formatted context has 30 citations
    assert "[30] [E30]" in pack.formatted_context
