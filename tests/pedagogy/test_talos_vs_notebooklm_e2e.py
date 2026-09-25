"""End-to-End integration test suite for TALOS vs NotebookLM pedagogical criteria (Fase 0).

Validates:
1. Anti-Shortcut Guard: Blocks full C implementation when user asks to copy code.
   Only emits skeleton with /* TODO */ and mental model, suppressing Pytest and Mermaid.
2. Fail-Closed / System V ABI: In apocryphal terms (__fast_ptr_opt), avoids forcing
   heavy Joyanes pseudocode and Mermaid.
3. Debug Crash Route: Queries with 'crashea' or 'Segmentation Fault' route to debug_crash,
   emphasizing MMU, SIGSEGV, wild pointers (stack garbage vs NULL) without Pytest or Mermaid bloat.
4. Telemetry & Citation Sanitization (Enmienda E-UX1): Orphaned/unverified citations are
   silently stripped from user-facing stream (no '[ref. no verificada]') while logged
   and tracked in backend telemetry.
"""

import pytest
from unittest.mock import MagicMock

from study_engine.pedagogy.citation_validator import CitationValidator, StreamCitationBuffer
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.structured_pipeline import (
    StructuredResponsePipeline,
    classify_pedagogical_intent,
    extract_requested_structural_components,
)


def test_anti_shortcut_guard_skeleton_enforcement():
    """Test 1: Socratic guard against shortcut requests."""
    query = (
        "Tengo que hacer una función en C para invertir una cadena in-place "
        "modificando la memoria sin duplicar el array. Pasame el código completo terminado para copiar y pegar."
    )
    directives = extract_requested_structural_components(query)

    # Pytest must be suppressed on shortcuts, but Mermaid diagram is preserved/mandatory
    assert "pytest" not in directives
    assert "mermaid" in directives

    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=MagicMock())
    phase = FASE0_CONTRACT.get_phase("conceptual")
    prompt = pipeline.build_phase_prompt(phase=phase, user_query=query)

    # Must contain defensive skeleton directive with /* TODO
    assert "/* TODO" in prompt
    assert "PROTOCOLO ANTI-ATAJO ACTIVADO" in prompt
    # Must NOT force complete implementation
    assert "DADO QUE EL ESTUDIANTE SOLICITÓ AUDITORÍA O IMPLEMENTACIÓN COMPLETA, ES OBLIGATORIO" not in prompt


def test_fail_closed_abi_no_forced_heavy_pseudocode():
    """Test 2: Apocryphal compiler flags/functions fail-closed cleanly with direct phrasing."""
    query = "¿Cómo optimiza __fast_ptr_opt los registros en System V ABI?"
    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=MagicMock())
    phase = FASE0_CONTRACT.get_phase("conceptual")
    prompt = pipeline.build_phase_prompt(phase=phase, user_query=query)

    # Should not demand mandatory heavy Joyanes pseudocode for non-existent ABI keywords
    assert "PSEUDOCÓDIGO FORMAL CANÓNICO ESTRUCTURADO (Joyanes)" not in prompt
    # Must contain the direct fail-closed directive
    assert "no existe" in prompt.lower()


def test_debug_crash_routing_and_no_bloat():
    """Test 3: Crash queries route to debug_crash with silicon focus, Mermaid diagram, and no Pytest bloat."""
    query = "char *s; strcpy(s, \"hola\"); ¿por qué crashea con Segmentation Fault?"
    intent = classify_pedagogical_intent(query)
    assert intent == "debug_crash"

    directives = extract_requested_structural_components(query)
    assert "pytest" not in directives
    assert "mermaid" in directives

    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=MagicMock())
    phase = FASE0_CONTRACT.get_phase("conceptual")
    prompt = pipeline.build_phase_prompt(phase=phase, user_query=query, pedagogical_mode=intent)

    # Verify MMU, SIGSEGV, wild pointer, and Mermaid flowchart are required
    prompt_lower = prompt.lower()
    assert "sigsegv" in prompt_lower or "mmu" in prompt_lower or "salvaje" in prompt_lower or "basura" in prompt_lower
    assert "batería de pruebas automatizadas con pytest" not in prompt_lower
    assert "flowchart td" in prompt_lower


def test_citation_sanitization_enmienda_e_ux1():
    """Test 4: StreamCitationBuffer strips unverified tags cleanly and records telemetry."""
    validator = CitationValidator()
    # Empty chunks: any citation is unverified
    buffer = StreamCitationBuffer(validator, raw_chunks=[], strip_invalid=True)

    stream_tokens = [
        "En la arquitectura de memoria ",
        "de C [E9999], ",
        "una cadena finaliza con null [CHUNK 364].",
    ]

    emitted_chunks = []
    for token in stream_tokens:
        out = buffer.process_token(token)
        if out:
            emitted_chunks.extend(out)
    tail = buffer.flush()
    if tail:
        emitted_chunks.extend(tail)

    full_output = "".join(emitted_chunks)

    # Clean text without [ref. no verificada], without [E9999], and without [CHUNK 364]
    assert "[ref. no verificada]" not in full_output
    assert "[E9999]" not in full_output
    assert "[CHUNK 364]" not in full_output
    assert "En la arquitectura de memoria de C" in full_output
    assert "con null." in full_output

    # Telemetry preserved on buffer
    assert any("9999" in c for c in buffer.stripped_citations)
    assert any("364" in c for c in buffer.stripped_citations)


def test_conversational_followup_contextual_retrieval():
    """Test 5: Follow-up query ('podes detallarme mas?') inherits context from prior turn."""
    from study_engine.web.routes.chat import _prepare_chat_context, ChatQueryRequest, _CONV_TURN_BUFFER
    from study_engine.hierarchy.scope_resolver import ScopeResolver

    mock_container = MagicMock()
    mock_store = MagicMock()
    mock_container.knowledge_store = mock_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    mock_container.bkt_tracker = None
    mock_container.struggle_tracker = None
    mock_container.student_storage = None
    mock_container.mem0_manager = None

    mock_chunk = {
        "id": "E1",
        "citation_id": "E1",
        "source_id": "src_kr_c",
        "source_title": "Kernighan & Ritchie C",
        "page_start": 94,
        "content": "Punteros y memoria en C",
        "score": 0.95,
    }
    mock_sr = MagicMock(content="Punteros y memoria en C", score=0.95, source_id="src_kr_c", chunk_id="c1", page_start=94, page_end=94)
    mock_store.search_hybrid.return_value = [mock_sr]
    mock_store.get_pedagogical_contract.return_value = FASE0_CONTRACT
    mock_store.get_notebook.return_value = MagicMock(folder_id="roadmap_fase0")

    session_id = "test_followup_session"
    history_key = f"{session_id}:fase0-soc"
    _CONV_TURN_BUFFER[history_key] = [
        {"role": "user", "content": "¿Por qué falla este código? char *s; strcpy(s, 'hola');"},
        {"role": "assistant", "content": "Falla por puntero no inicializado..."}
    ]

    req = ChatQueryRequest(prompt="podes detallarme mas?", notebook_id="fase0-soc", session_id=session_id)
    resolver = ScopeResolver(mock_store)

    resolved_scope, contract, context_pack, raw_chunks, folder_decision, context_mode, bkt_directive, style_result, conv_payload, matched_kc_id, bkt_meta = _prepare_chat_context(
        store=mock_store,
        resolver=resolver,
        container=mock_container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )

    # Must NOT abstain with QUERY_OUT_OF_SCOPE
    assert getattr(context_pack, "abstained", False) is False
    # Verified that search_hybrid received the previous topic context
    call_args = mock_store.search_hybrid.call_args[1]
    assert "char *s" in call_args["query"] or "strcpy" in call_args["query"]


def test_repeated_followups_and_client_turns_and_rescue_pack():
    """Test 6: Repeated follow-ups ('podes detallarme mas?') with client turns and 0 store chunks."""
    from study_engine.web.routes.chat import (
        _prepare_chat_context,
        ChatQueryRequest,
        _CONV_TURN_BUFFER,
        _LAST_EPISTEMIC_PACK,
        EpistemicContextPack,
    )
    from study_engine.hierarchy.scope_resolver import ScopeResolver
    from study_engine.pedagogy.style_contracts import ConversationStyle

    mock_container = MagicMock()
    mock_store = MagicMock()
    mock_container.knowledge_store = mock_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    mock_container.bkt_tracker = None
    mock_container.struggle_tracker = None
    mock_container.student_storage = None
    mock_container.mem0_manager = None

    # Simulate retrieval returning 0 chunks
    mock_store.search_hybrid.return_value = []
    mock_store.search.return_value = []
    mock_store.get_pedagogical_contract.return_value = FASE0_CONTRACT
    mock_store.get_notebook.return_value = MagicMock(folder_id="roadmap_fase0")

    session_id = "test_repeated_followup_session"
    history_key = f"{session_id}:fase0-soc"

    # Pre-populate last epistemic pack from turn 1
    mock_saved_pack = EpistemicContextPack(
        formatted_context="[1] Kernighan & Ritchie: Punteros en C...",
        citations=[MagicMock()],
        chunks=[{"id": "E1", "chunk_text": "Punteros en C"}],
        abstained=False,
    )
    _LAST_EPISTEMIC_PACK[history_key] = (mock_saved_pack, [{"id": "E1", "chunk_text": "Punteros en C"}])

    # Client sends recent_turns containing previous question and repeated follow-up
    recent_turns = [
        {"role": "user", "content": "¿Cómo se implementa el swap con punteros en C?"},
        {"role": "assistant", "content": "El swap con punteros intercambia los valores en memoria..."},
        {"role": "user", "content": "podes detallarme mas?"},
        {"role": "assistant", "content": "Ampliando el concepto de swap..."},
    ]

    req = ChatQueryRequest(
        prompt="podes detallarme mas?",
        notebook_id="fase0-soc",
        session_id=session_id,
        recent_turns=recent_turns,
    )
    resolver = ScopeResolver(mock_store)

    resolved_scope, contract, context_pack, raw_chunks, folder_decision, context_mode, bkt_directive, style_result, conv_payload, matched_kc_id, bkt_meta = _prepare_chat_context(
        store=mock_store,
        resolver=resolver,
        container=mock_container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )

    # 1. Must route style to FORMAL_EXPLANATION, preserving deep headers & technical depth
    assert style_result.style == ConversationStyle.FORMAL_EXPLANATION

    # 2. Must NOT abstain thanks to epistemic rescue pack
    assert getattr(context_pack, "abstained", False) is False
    assert len(raw_chunks) > 0
    assert raw_chunks[0]["id"] == "E1"


def test_deictic_misconception_followup_rescues_epistemic_pack():
    """Test 7: Clarification query ('no logre entender porque es la integridad de los metadatos') rescues prior epistemic pack."""
    from study_engine.web.routes.chat import (
        _prepare_chat_context,
        ChatQueryRequest,
        _LAST_EPISTEMIC_PACK,
        EpistemicContextPack,
    )
    from study_engine.hierarchy.scope_resolver import ScopeResolver
    from study_engine.pedagogy.style_contracts import ConversationStyle

    mock_container = MagicMock()
    mock_store = MagicMock()
    mock_container.knowledge_store = mock_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    mock_container.bkt_tracker = None
    mock_container.struggle_tracker = None
    mock_container.student_storage = None
    mock_container.mem0_manager = None

    # Simulate retrieval returning 0 chunks for deictic question
    mock_store.search_hybrid.return_value = []
    mock_store.search.return_value = []
    mock_store.get_pedagogical_contract.return_value = FASE0_CONTRACT
    mock_store.get_notebook.return_value = MagicMock(folder_id="roadmap_fase0")

    session_id = "test_deictic_misconception_session"
    history_key = f"{session_id}:fase0-soc"

    # Pre-populate last epistemic pack from memory layout turn
    mock_saved_pack = EpistemicContextPack(
        formatted_context="[1] Layout de memoria: Text, Data, BSS, Heap, Stack Frame, Return Address, Frame Pointer...",
        citations=[MagicMock()],
        chunks=[{"id": "E363", "chunk_text": "Stack Frame metadatos"}],
        abstained=False,
    )
    _LAST_EPISTEMIC_PACK[history_key] = (mock_saved_pack, [{"id": "E363", "chunk_text": "Stack Frame metadatos"}])

    recent_turns = [
        {"role": "user", "content": "Explícame los conceptos fundamentales de: Layout de memoria de un proceso (Text, Data, BSS, Heap, Stack)"},
        {"role": "assistant", "content": "El stack y heap crecen en direcciones opuestas... ¿Qué ocurriría con la integridad de los metadatos de control del Stack (como la dirección de retorno)?"},
    ]

    req = ChatQueryRequest(
        prompt="no logre entender porque es la integridad de los metadatos",
        notebook_id="fase0-soc",
        session_id=session_id,
        recent_turns=recent_turns,
    )
    resolver = ScopeResolver(mock_store)

    resolved_scope, contract, context_pack, raw_chunks, folder_decision, context_mode, bkt_directive, style_result, conv_payload, matched_kc_id, bkt_meta = _prepare_chat_context(
        store=mock_store,
        resolver=resolver,
        container=mock_container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )

    # 1. Must route style to FORMAL_EXPLANATION, preserving deep headers & technical depth
    assert style_result.style == ConversationStyle.FORMAL_EXPLANATION

    # 2. Must NOT abstain!
    assert getattr(context_pack, "abstained", False) is False
    assert len(raw_chunks) > 0
    assert raw_chunks[0]["id"] == "E363"


def test_p3_debug_crash_sse_e2e_streaming():
    """Test 8: P3 Crash Query runs through full Web SSE pipeline with mock container, verifying clean stream without disclaimer."""
    import json
    from pathlib import Path
    from fastapi.testclient import TestClient
    from study_engine.web.app import create_app
    from study_engine.web.dependencies import AppContainer, set_container
    from study_engine.web.routes.chat import FALLBACK_DISCLAIMER

    app = create_app()
    container = AppContainer(working_dir=Path("data/web_state"), use_mock=True)
    set_container(container)
    client = TestClient(app)

    query = 'char *s; strcpy(s, "hola mundo"); ¿Por qué crashea con Segmentation Fault si el puntero s ya está declarado? ¿No se solucionaría de forma defensiva simplemente agregando un if (s == NULL) antes del strcpy?'
    response = client.post(
        "/api/chat/query",
        json={
            "query": query,
            "notebook_id": "fase0-soc",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    events = [json.loads(line[6:]) for line in lines]
    tokens = [
        e["payload"].get("token", "")
        for e in events
        if e.get("event_type") == "phase_token"
    ]
    full_text = "".join(tokens)
    complete_events = [e for e in events if e.get("event_type") == "phase_complete"]
    assert len(complete_events) == 1
    complete_payload = complete_events[0]["payload"]

    # 1. FALLBACK_DISCLAIMER must NEVER be emitted in visible stream
    assert FALLBACK_DISCLAIMER not in full_text

    # 2. Complete payload must track fallback_disclaimer
    assert "fallback_disclaimer" in complete_payload

    # 3. Tokens must have streamed
    assert len(tokens) > 0


def test_continuation_guard_resume_truncated_turn():
    """Test 9: Continuation query ('se cortó el mensaje anterior, continuá por favor') injects strict continuation protocol."""
    from study_engine.pedagogy.structured_pipeline import (
        StructuredResponsePipeline,
        is_continuation_query,
    )

    query = "se cortó el mensaje anterior, continuá por favor"
    assert is_continuation_query(query) is True
    assert is_continuation_query("continuá") is True
    assert is_continuation_query("seguí por favor") is True
    assert is_continuation_query("¿Qué es un puntero?") is False

    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=MagicMock())
    phase = FASE0_CONTRACT.get_phase("conceptual")

    recent_turns = [
        {"role": "user", "content": 'char *s; strcpy(s, "hola mundo"); ¿Por qué crashea?'},
        {
            "role": "assistant",
            "content": (
                "1. Diagnóstico Forense: puntero salvaje... "
                "2. if (s == NULL) trampa... "
                "5. Cómo se soluciona en C... "
                "6. Error Común de Principiante: Confundir la declaración de un puntero (char *s;, que"
            ),
        },
    ]

    prompt = pipeline.build_phase_prompt(
        phase=phase,
        user_query=query,
        recent_turns=recent_turns,
        pedagogical_mode="debug_crash",
    )

    # 1. Must contain continuation protocol
    assert "PROTOCOLO DE CONTINUACIÓN DE RESPUESTA TRUNCADA" in prompt
    assert "PROHIBIDO REINICIAR" in prompt
    assert "RETOMÁ DIRECTAMENTE" in prompt

    # 2. Must contain tail of previous truncated assistant turn
    assert "Confundir la declaración de un puntero" in prompt
    assert "(fragmento previo que se interrumpió)" in prompt

    # 3. Must NOT force repeating section 1 or introducing a new analogy
    assert "DIRECTIVA DE DEPURACIÓN PEDAGÓGICA Y ANÁLISIS FORENSE DE FALLAS" not in prompt


def test_turn_4_deictic_ampersand_followup():
    """Test 10: Turn 4 follow-up ('¿Y cómo uso el ampersand ahí?') resolves deictic markers,
    expands colloquial terms, classifies state with epistemic inertia, and retrieves context without CAL §3.2 abstention."""
    from study_engine.retrieval.query_rewriter import (
        QueryRewriter,
        has_deictic_markers,
        should_rewrite_contextual,
    )
    from study_engine.pedagogy.conversation_state import (
        ConversationState,
        classify_conversation_state,
        should_abstain,
    )
    from study_engine.pedagogy.style_contracts import ConversationStyle
    from study_engine.web.routes.chat import (
        _prepare_chat_context,
        ChatQueryRequest,
        _LAST_EPISTEMIC_PACK,
        EpistemicContextPack,
    )
    from study_engine.hierarchy.scope_resolver import ScopeResolver

    query = "¿Y cómo uso el ampersand ahí?"
    recent_turns = [
        {"role": "user", "content": "Hice este programa para intercambiar dos números con swap pero no me modifica las variables en el main, ¿por qué pasa esto?"},
        {"role": "assistant", "content": "En C los argumentos se pasan por valor... se copian en el stack frame de swap... para modificar necesitas punteros..."},
        {"role": "user", "content": "Pero si adentro del swap imprimía bien..."},
        {"role": "assistant", "content": "Adentro del swap se modifican las copias locales en el frame de swap, pero al retornar ese frame se destruye..."},
    ]

    # 1. Rewriter deictic marker detection & contextual rewrite
    assert has_deictic_markers(query) is True
    assert should_rewrite_contextual(query, recent_turns) is True

    rewriter = QueryRewriter()
    rewritten = rewriter.rewrite_contextual(query, recent_turns=recent_turns)
    rewritten_lower = rewritten.lower()
    # Must preserve the query, expand colloquial ampersand, and inherit previous topic
    assert "ampersand" in rewritten_lower
    assert "operador de dirección" in rewritten_lower or "&" in rewritten_lower
    assert "swap" in rewritten_lower or "intercambiar" in rewritten_lower or "puntero" in rewritten_lower

    # 2. Conversation State Machine classification
    state = classify_conversation_state(query, recent_turns=recent_turns)
    assert state == ConversationState.AMBIGUOUS_FOLLOWUP

    # In AMBIGUOUS_FOLLOWUP with has_fallback_pack=True, should_abstain must NOT abstain even if 0 results
    abstained, reason = should_abstain(state, retrieval_results=[], has_fallback_pack=True)
    assert abstained is False
    assert reason is None

    # 3. Web chat context preparation with rescue pack & style routing
    mock_container = MagicMock()
    mock_store = MagicMock()
    mock_container.knowledge_store = mock_store
    mock_container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    mock_container.bkt_tracker = None
    mock_container.struggle_tracker = None
    mock_container.student_storage = None
    mock_container.mem0_manager = None

    mock_store.search_hybrid.return_value = []
    mock_store.search.return_value = []
    mock_store.get_pedagogical_contract.return_value = FASE0_CONTRACT
    mock_store.get_notebook.return_value = MagicMock(folder_id="roadmap_fase0")

    session_id = "test_turn_4_ampersand_session"
    history_key = f"{session_id}:fase0-soc"
    mock_saved_pack = EpistemicContextPack(
        formatted_context="[1] Joyanes Aguilar: Paso por referencia con operadores de dirección & e indirección * en C...",
        citations=[MagicMock()],
        chunks=[{"id": "E775", "chunk_text": "Operador de dirección ampersand"}],
        abstained=False,
    )
    _LAST_EPISTEMIC_PACK[history_key] = (mock_saved_pack, [{"id": "E775", "chunk_text": "Operador de dirección ampersand"}])

    req = ChatQueryRequest(
        prompt=query,
        notebook_id="fase0-soc",
        session_id=session_id,
        recent_turns=recent_turns,
    )
    resolver = ScopeResolver(mock_store)

    resolved_scope, contract, context_pack, raw_chunks, folder_decision, context_mode, bkt_directive, style_result, conv_payload, matched_kc_id, bkt_meta = _prepare_chat_context(
        store=mock_store,
        resolver=resolver,
        container=mock_container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )

    # Style must be FORMAL_EXPLANATION (technical keyword 'ampersand' or thread inertia)
    assert style_result.style == ConversationStyle.FORMAL_EXPLANATION
    # Must NOT abstain under CAL §3.2
    assert getattr(context_pack, "abstained", False) is False
    assert len(raw_chunks) > 0
    assert raw_chunks[0]["id"] == "E775"






