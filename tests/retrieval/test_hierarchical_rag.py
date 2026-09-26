"""Hierarchical RAG Test Suite (Fase 3 - Enmienda E-M6).

Validates:
1. GranularityRouter routing deterministic logic for MACRO, MICRO, and HYBRID queries.
2. Hybrid deduplication (E-M4): filters redundant chunks (>0.85 overlap) while preserving code blocks.
3. MACRO retrieval: searches chapter_summaries with latency < 8s.
4. MICRO retrieval: searches leaf chunks with latency < 4s.
5. HYBRID retrieval: returns parent summary + deduplicated leaf chunks with latency < 6s.
6. Deictic follow-up query rewriting and hierarchical routing without false abstention.
7. Cryptographic Merkle Root computation and invalidation upon summary mutation.
"""

import time
import pytest
from unittest.mock import MagicMock

from study_engine.contracts.chunk import Chunk
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.search import SearchResult
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.style_contracts import ConversationStyle
from study_engine.retrieval.granularity_router import (
    GranularityRouter,
    RetrievalGranularity,
    RoutingDecision,
    deduplicate_hybrid_chunks,
)
from study_engine.retrieval.query_rewriter import (
    QueryRewriter,
    has_deictic_markers,
    should_rewrite_contextual,
)
from study_engine.storage.knowledge_store import ChapterSummary, KnowledgeStore
from study_engine.web.routes.chat import (
    ChatQueryRequest,
    EpistemicContextPack,
    _LAST_EPISTEMIC_PACK,
    _assemble_epistemic_context,
    _prepare_chat_context,
)
from study_engine.hierarchy.scope_resolver import ScopeResolver


@pytest.fixture
def memory_store():
    """In-memory KnowledgeStore initialized with schema_v6 and pilot chapter summaries."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    # Create test notebook
    nb = Notebook(
        id="fase0-soc",
        name="Roadmap KASIU TECH v4 - Fase 0",
        description="Fundamentos de Sistemas Operativos y C",
        subject="Sistemas",
    )
    store.create_notebook(nb)

    # Insert test chapter summaries (Level 2)
    chap1 = ChapterSummary(
        id="chap_fase0-soc_joyanes_1",
        notebook_id="fase0-soc",
        source_id="src_joyanes",
        chapter_number=1,
        title="Metodología y Pensamiento Algorítmico",
        page_start=1,
        page_end=100,
        summary_text="Visión general de metodología de programación, diseño algorítmico y estructuras básicas en C.",
        knowledge_components=["kc_metodologia", "kc_algoritmos"],
        core_invariants=["Diseño descendente", "Modularidad"],
    )
    chap2 = ChapterSummary(
        id="chap_fase0-soc_joyanes_2",
        notebook_id="fase0-soc",
        source_id="src_joyanes",
        chapter_number=2,
        title="Punteros, Direcciones de Memoria y Aritmética",
        page_start=750,
        page_end=775,
        summary_text="Punteros en C, direcciones de memoria hexadecimales, operador & y operador de indirección *.",
        knowledge_components=["kc_punteros", "kc_operadores"],
        core_invariants=["Un puntero contiene una dirección de memoria", "El tipo determina el paso aritmético"],
    )
    chap3 = ChapterSummary(
        id="chap_fase0-soc_joyanes_3",
        notebook_id="fase0-soc",
        source_id="src_joyanes",
        chapter_number=3,
        title="Paso de Parámetros, Marcos de Pila y Memoria",
        page_start=776,
        page_end=796,
        summary_text="Paso por valor vs paso por referencia mediante punteros. Marcos de pila (stack frames) y ciclo de vida de variables locales.",
        knowledge_components=["kc_paso_parametros", "kc_stack_frame"],
        core_invariants=["En C todo paso es por valor", "El paso por referencia se emula pasando la dirección"],
    )

    store.add_chapter_summary(chap1)
    store.add_chapter_summary(chap2)
    store.add_chapter_summary(chap3)

    # Insert source and document records to satisfy foreign keys
    with store.engine.transaction() as conn:
        conn.execute(
            "INSERT INTO sources (source_id, title, role) VALUES (?, ?, ?);",
            ("src_joyanes", "Joyanes Aguilar - Fundamentos de Programación", "PRIMARY"),
        )
        conn.execute(
            "INSERT INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
            ("fase0-soc", "src_joyanes"),
        )
        conn.execute(
            "INSERT INTO documents (id, source_id, title) VALUES (?, ?, ?);",
            ("doc_joyanes_c", "src_joyanes", "Fundamentos de Programación en C"),
        )

    # Insert leaf chunks (Level 3)
    chunk1 = Chunk(
        id="chk_leaf_1",
        document_id="doc_joyanes_c",
        source_id="src_joyanes",
        content="El operador & permite obtener la dirección de memoria de una variable. Por ejemplo int x = 5; int *p = &x;",
        page_start=755,
        page_end=755,
    )
    chunk2 = Chunk(
        id="chk_leaf_2",
        document_id="doc_joyanes_c",
        source_id="src_joyanes",
        content="Cuando se llama a swap(a, b) sin punteros, los valores se copian en el marco de pila de swap y no se modifica main.",
        page_start=778,
        page_end=779,
        index=1,
    )
    store.chunks.save_chunks([chunk1, chunk2])
    store.link_chunk_to_chapter("chk_leaf_1", "chap_fase0-soc_joyanes_2")
    store.link_chunk_to_chapter("chk_leaf_2", "chap_fase0-soc_joyanes_3")

    # Warmup embedding model so latency tests measure pure retrieval rather than PyTorch cold-start
    try:
        store.search_hybrid("warmup", "fase0-soc")
    except Exception:
        pass

    return store


def test_granularity_router_rules():
    """Validates deterministic routing into MACRO, MICRO, and HYBRID."""
    # 1. MACRO queries
    macro_q1 = "¿Qué temas cubre la unidad de memoria y punteros en C según el libro de Joyanes?"
    macro_q2 = "Haceme un resumen panorámico de los capítulos de arquitectura"
    macro_q3 = "¿Cuál es el temario y visión general del curso?"

    assert GranularityRouter.route(macro_q1).granularity == RetrievalGranularity.MACRO
    assert GranularityRouter.route(macro_q2).granularity == RetrievalGranularity.MACRO
    assert GranularityRouter.route(macro_q3).granularity == RetrievalGranularity.MACRO

    # 2. MICRO queries (Code blocks, forensic crash, specific error)
    micro_q1 = "Tengo este código: int *p; *p = 10; y crashea con Segmentation fault (SIGSEGV)"
    micro_q2 = "Error en línea 42: fallo de segmentación al desreferenciar puntero"
    micro_q3 = "Mirá este snippet: ```c\nvoid swap(int a, int b) { ... }\n```"

    assert GranularityRouter.route(micro_q1).granularity == RetrievalGranularity.MICRO
    assert GranularityRouter.route(micro_q2).granularity == RetrievalGranularity.MICRO
    assert GranularityRouter.route(micro_q3, has_code_block=True).granularity == RetrievalGranularity.MICRO

    # 3. HYBRID queries (Deep conceptual, multi-topic, trade-offs)
    hybrid_q1 = "Explicame paso por valor vs paso por referencia con punteros en C y cómo afecta al stack frame"
    hybrid_q2 = "Diferencia entre stack y heap en la gestión de memoria dinámica"
    hybrid_q3 = "¿Por qué ocurre el desbordamiento de búfer y qué impacto tiene en la seguridad?"

    assert GranularityRouter.route(hybrid_q1).granularity == RetrievalGranularity.HYBRID
    assert GranularityRouter.route(hybrid_q2).granularity == RetrievalGranularity.HYBRID
    assert GranularityRouter.route(hybrid_q3).granularity == RetrievalGranularity.HYBRID


def test_deduplicate_hybrid_chunks_filtering():
    """Validates Enmienda E-M4 deduplication: filters redundant text (>0.85) while keeping code."""
    parent = ChapterSummary(
        id="chap_p1",
        notebook_id="fase0-soc",
        source_id="src_joyanes",
        chapter_number=1,
        title="Punteros y Memoria",
        page_start=1,
        page_end=10,
        summary_text="Un puntero almacena la dirección de memoria de una variable. Se utiliza el operador ampersand para obtener la dirección y el asterisco para desreferenciar.",
    )

    # Chunk with 95% word overlap with parent summary
    redundant_chunk = SearchResult(
        chunk_id="c_redundant",
        document_id="doc1",
        source_id="s1",
        score=0.9,
        snippet="",
        content="Un puntero almacena la dirección de memoria de una variable. Se utiliza el operador ampersand para obtener la dirección y el asterisco para desreferenciar el valor.",
        index=0,
    )

    # Chunk with distinct content
    distinct_chunk = SearchResult(
        chunk_id="c_distinct",
        document_id="doc1",
        source_id="s1",
        score=0.85,
        snippet="",
        content="En la arquitectura x86-64, la instrucción LEA calcula la dirección efectiva en tiempo de ejecución sin acceder a la memoria física.",
        index=1,
    )

    # Chunk with high overlap BUT containing a code block -> must be preserved
    code_chunk = SearchResult(
        chunk_id="c_code",
        document_id="doc1",
        source_id="s1",
        score=0.88,
        snippet="",
        content="Un puntero almacena la dirección de memoria: ```c\nint *p = &x;\n*p = 20;\n```",
        index=2,
    )

    candidates = [redundant_chunk, distinct_chunk, code_chunk]
    deduped = deduplicate_hybrid_chunks(
        candidate_chunks=candidates,
        parent_summary=parent,
        similarity_threshold=0.85,
        max_leaves=5,
    )

    deduped_ids = [c.chunk_id for c in deduped]
    assert "c_redundant" not in deduped_ids, "Redundant chunk must be pruned"
    assert "c_distinct" in deduped_ids, "Distinct chunk must be preserved"
    assert "c_code" in deduped_ids, "Chunk with code block must be preserved despite overlap"


def test_macro_routing_and_retrieval(memory_store):
    """Canonical Query 1: MACRO routing for synthesis queries, validates chapter_summaries returned, latency < 8s."""
    query = "¿Qué temas cubre la unidad de memoria y punteros en C según el libro de Joyanes?"
    start_time = time.perf_counter()

    decision = GranularityRouter.route(query)
    assert decision.granularity == RetrievalGranularity.MACRO

    summaries = memory_store.search_chapter_summaries(
        query=query,
        notebook_id="fase0-soc",
        limit=decision.max_parent_nodes,
    )
    elapsed = time.perf_counter() - start_time

    assert elapsed < 8.0, f"MACRO latency budget exceeded: {elapsed:.3f}s >= 8.0s"
    assert len(summaries) > 0
    assert any("Punteros" in s.title or "Memoria" in s.title for s in summaries)
    assert all(isinstance(s, ChapterSummary) for s in summaries)


def test_micro_routing_and_retrieval(memory_store):
    """Canonical Query 2: MICRO routing for forensic/debug queries, validates leaf chunks returned, latency < 4s."""
    query = "Tengo este código: int *p; *p = 10; y crashea con Segmentation fault (SIGSEGV)"
    start_time = time.perf_counter()

    decision = GranularityRouter.route(query)
    assert decision.granularity == RetrievalGranularity.MICRO

    results = memory_store.search_hybrid(
        query=query,
        notebook_id="fase0-soc",
        limit=decision.max_leaf_chunks,
    )
    elapsed = time.perf_counter() - start_time

    assert elapsed < 4.0, f"MICRO latency budget exceeded: {elapsed:.3f}s >= 4.0s"
    # Ensure returns leaf chunks, not chapter summaries
    for r in results:
        assert getattr(r, "document_id", "") != "chapter_summary"


def test_hybrid_routing_and_deduplication(memory_store):
    """Canonical Query 3: HYBRID routing for conceptual queries, validates parent summary + deduplicated chunks, latency < 6s."""
    query = "Explicame paso por valor vs paso por referencia con punteros en C y cómo afecta al stack frame"
    start_time = time.perf_counter()

    decision = GranularityRouter.route(query)
    assert decision.granularity == RetrievalGranularity.HYBRID

    mock_container = MagicMock()
    mock_container.knowledge_store = memory_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})

    pack, raw_chunks = _assemble_epistemic_context(
        store=memory_store,
        container=mock_container,
        prompt_text=query,
        target_notebook_id="fase0-soc",
        granularity_decision=decision,
    )
    elapsed = time.perf_counter() - start_time

    assert elapsed < 6.0, f"HYBRID latency budget exceeded: {elapsed:.3f}s >= 6.0s"
    assert getattr(pack, "abstained", False) is False
    assert len(raw_chunks) > 0

    # Must contain at least one chapter summary parent node
    has_parent_node = any(c.get("document_id") == "chapter_summary" for c in raw_chunks)
    has_parent_citation = any(getattr(c, "document_id", "") == "chapter_summary" for c in pack.citations)
    assert has_parent_node is True or has_parent_citation is True


def test_deictic_rewritten_hierarchical_retrieval(memory_store):
    """Canonical Query 4: Turn 4 follow-up ('¿Y cómo uso el ampersand ahí?') rewritten and routed to MICRO without abstention."""
    query = "¿Y cómo uso el ampersand ahí?"
    recent_turns = [
        {"role": "user", "content": "Hice este programa para intercambiar dos números con swap pero no me modifica las variables en el main, ¿por qué pasa esto?"},
        {"role": "assistant", "content": "En C los argumentos se pasan por valor... se copian en el stack frame de swap... para modificar necesitas punteros..."},
        {"role": "user", "content": "Pero si adentro del swap imprimía bien..."},
        {"role": "assistant", "content": "Adentro del swap se modifican las copias locales en el frame de swap, pero al retornar ese frame se destruye..."},
    ]

    # Rewriter expands context
    rewriter = QueryRewriter()
    rewritten = rewriter.rewrite_contextual(query, recent_turns=recent_turns)

    # Granularity decision on rewritten query
    decision = GranularityRouter.route(rewritten)
    assert decision.granularity in (RetrievalGranularity.MICRO, RetrievalGranularity.HYBRID)

    session_id = "test_hierarchical_turn_4"
    history_key = f"{session_id}:fase0-soc"

    # Pre-seed verified epistemic pack in conversation cache
    saved_pack = EpistemicContextPack(
        formatted_context="[1] Joyanes: Paso por referencia y operador &",
        citations=[MagicMock()],
        chunks=[{"id": "chk_leaf_1", "content": "El operador & permite obtener la dirección"}],
        abstained=False,
    )
    _LAST_EPISTEMIC_PACK[history_key] = (saved_pack, [{"id": "chk_leaf_1", "content": "El operador & permite obtener la dirección"}])

    req = ChatQueryRequest(
        prompt=query,
        notebook_id="fase0-soc",
        session_id=session_id,
        recent_turns=recent_turns,
    )

    mock_container = MagicMock()
    mock_container.knowledge_store = memory_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    mock_container.bkt_tracker = None
    mock_container.struggle_tracker = None
    mock_container.student_storage = None
    mock_container.mem0_manager = None

    resolver = ScopeResolver(memory_store)

    resolved_scope, contract, context_pack, raw_chunks, folder_decision, context_mode, bkt_directive, style_result, conv_payload, matched_kc_id, bkt_meta = _prepare_chat_context(
        store=memory_store,
        resolver=resolver,
        container=mock_container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )

    assert style_result.style == ConversationStyle.FORMAL_EXPLANATION
    assert getattr(context_pack, "abstained", False) is False
    assert len(raw_chunks) > 0


def test_notebook_merkle_root_invalidation(memory_store):
    """Validates deterministic computation of Merkle Root and invalidation on chapter summary change."""
    root1 = memory_store.compute_notebook_merkle_root("fase0-soc")
    assert len(root1) == 64  # SHA256 hex string

    # Recomputing without changes produces identical root
    root2 = memory_store.compute_notebook_merkle_root("fase0-soc")
    assert root1 == root2

    # Add a new summary -> Merkle root must change
    new_chap = ChapterSummary(
        id="chap_fase0-soc_extra",
        notebook_id="fase0-soc",
        source_id="src_joyanes",
        chapter_number=4,
        title="Gestión Dinámica de Memoria: malloc y free",
        page_start=800,
        page_end=850,
        summary_text="Asignación dinámica de memoria con malloc, calloc, realloc y liberación con free.",
        knowledge_components=["kc_malloc", "kc_heap"],
        core_invariants=["Toda memoria asignada debe liberarse"],
    )
    memory_store.add_chapter_summary(new_chap)

    root3 = memory_store.compute_notebook_merkle_root("fase0-soc")
    assert root3 != root1
    assert len(root3) == 64


def test_macro_query(memory_store):
    """Test macro query: '¿Cómo se articula la protección de memoria entre CPU y Kernel en todo el programa?' -> MACRO, <8s."""
    query = "¿Cómo se articula la protección de memoria entre CPU y Kernel en todo el programa?"
    t0 = time.perf_counter()
    decision = GranularityRouter.route(query)
    assert decision.granularity == RetrievalGranularity.MACRO
    summaries = memory_store.search_chapter_summaries(query, notebook_id="fase0-soc", limit=2)
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0
    assert len(summaries) > 0


def test_micro_query(memory_store):
    """Test micro query: 'char *s; strcpy(s, "hola") crashea' -> MICRO, <4s."""
    query = 'char *s; strcpy(s, "hola") crashea'
    t0 = time.perf_counter()
    decision = GranularityRouter.route(query)
    assert decision.granularity == RetrievalGranularity.MICRO
    results = memory_store.search_hybrid(query, notebook_id="fase0-soc", limit=decision.max_leaf_chunks)
    elapsed = time.perf_counter() - t0
    assert elapsed < 4.0


def test_hybrid_query(memory_store):
    """Test hybrid query: 'Explicame la paginación en x86-64' -> HYBRID, <6s."""
    query = "Explicame la paginación en x86-64"
    t0 = time.perf_counter()
    decision = GranularityRouter.route(query)
    assert decision.granularity == RetrievalGranularity.HYBRID
    mock_container = MagicMock()
    mock_container.knowledge_store = memory_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    pack, raw_chunks = _assemble_epistemic_context(
        store=memory_store,
        container=mock_container,
        prompt_text=query,
        target_notebook_id="fase0-soc",
        granularity_decision=decision,
    )
    elapsed = time.perf_counter() - t0
    assert elapsed < 6.0


def test_router_deterministic():
    """Validates that 100 consecutive calls with the same query produce identical RoutingDecision."""
    query = "Explicame la paginación en x86-64"
    reference = GranularityRouter.route(query)
    for _ in range(100):
        decision = GranularityRouter.route(query)
        assert decision.granularity == reference.granularity
        assert decision.max_parent_nodes == reference.max_parent_nodes
        assert decision.max_leaf_chunks == reference.max_leaf_chunks
        assert decision.target_token_budget == reference.target_token_budget


def test_fadena_so2_pilot_retrieval():
    """Validates that fadena-so2 chapters are indexed in web_state db and retrievable."""
    from pathlib import Path
    db_p = Path("data/web_state/knowledge_store.db")
    if not db_p.exists():
        pytest.skip("data/web_state/knowledge_store.db not present")

    store = KnowledgeStore(str(db_p))
    summaries = store.get_chapter_summaries_by_notebook("fadena-so2")
    assert len(summaries) >= 10, f"Expected >= 10 chapters for fadena-so2, got {len(summaries)}"

    # Search for Virtual Memory in fadena-so2
    res = store.search_chapter_summaries("Virtual Memory paging segmentation", notebook_id="fadena-so2", limit=2)
    assert len(res) > 0
    assert any("Virtual Memory" in s.title or "Memory" in s.title for s in res)
