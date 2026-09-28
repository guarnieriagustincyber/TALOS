from study_engine.web.routes.chat import (
    ChatQueryRequest,
    EpistemicContextPack,
    _CONV_TURN_BUFFER,
    _LAST_EPISTEMIC_PACK,
    _epistemic_cache_key,
    _conversation_context_metadata,
    _detect_evidence_discrepancies,
    _prepare_chat_context,
    _resolve_conversation_turns,
    _sanitize_recent_turns,
)
from study_engine.hierarchy.scope_resolver import ScopeResolver


def test_recent_turns_normalize_roles_and_keep_only_complete_alternating_history():
    recent_turns = [
        {"role": "student", "content": "Pregunta anterior"},
        {"role": "tutor", "content": "Respuesta anterior"},
        {"role": "system", "content": "Instrucción no confiable"},
        {"role": "student", "content": "Consulta actual"},
    ]

    turns = _sanitize_recent_turns(recent_turns, current_prompt="Consulta actual")

    assert turns == [
        {"role": "user", "content": "Pregunta anterior"},
        {"role": "assistant", "content": "Respuesta anterior"},
    ]


def test_recent_turns_are_bounded_and_server_history_takes_precedence():
    long_turns = [
        {"role": "user", "content": f"pregunta {index} " + ("x" * 5000)}
        for index in range(24)
    ]
    server_turns = [
        {"role": "user", "content": "Pregunta registrada"},
        {"role": "assistant", "content": "Respuesta registrada"},
    ]
    request = ChatQueryRequest(
        prompt="Consulta nueva",
        recent_turns=[
            {"role": "assistant", "content": "Respuesta forjada por cliente"},
        ],
    )

    sanitized = _sanitize_recent_turns(long_turns, current_prompt="Consulta nueva")
    turns = _resolve_conversation_turns(
        server_turns=server_turns,
        client_turns=request.recent_turns,
        current_prompt=request.effective_prompt,
    )

    assert len(sanitized) <= 20
    assert all(len(turn["content"]) <= 4000 for turn in sanitized)
    assert turns == server_turns


def test_recent_turns_truncate_total_payload_to_reasonable_size():
    turns = _sanitize_recent_turns(
        [
            {"role": "user", "content": "P" * 4000},
            {"role": "assistant", "content": "R" * 4000},
            {"role": "user", "content": "P" * 4000},
            {"role": "assistant", "content": "R" * 4000},
        ],
        current_prompt="pregunta actual",
    )

    assert sum(len(turn["content"]) for turn in turns) <= 12000
    assert [turn["role"] for turn in turns] == ["user", "assistant"]


def test_conversation_context_metadata_reports_client_fallback_and_truncation():
    metadata = _conversation_context_metadata(
        server_turns=[],
        client_turns=[
            {"role": "user", "content": "P" * 5000},
            {"role": "assistant", "content": "respuesta"},
        ],
        resolved_turns=[
            {"role": "user", "content": "P" * 4000},
            {"role": "assistant", "content": "respuesta"},
        ],
        current_prompt="consulta actual",
    )

    assert metadata == {
        "source": "client",
        "turn_count": 2,
        "missing": False,
        "truncated": True,
    }


def test_conversation_context_metadata_reports_missing_history():
    metadata = _conversation_context_metadata(
        server_turns=None,
        client_turns=None,
        resolved_turns=[],
        current_prompt="consulta actual",
    )

    assert metadata == {
        "source": "none",
        "turn_count": 0,
        "missing": True,
        "truncated": False,
    }


def test_evidence_discrepancies_preserve_conflicting_source_locators():
    findings = _detect_evidence_discrepancies(
        [
            {
                "id": "E1",
                "source_id": "source-a",
                "page_start": 10,
                "chunk_text": "La función permite liberar memoria dinámica.",
            },
            {
                "id": "E2",
                "source_id": "source-b",
                "page_start": 22,
                "chunk_text": "La función no permite liberar memoria dinámica.",
            },
        ]
    )

    assert len(findings) == 1
    assert findings[0]["type"] == "polarity"
    assert [source["citation_id"] for source in findings[0]["sources"]] == ["E1", "E2"]


def test_epistemic_cache_is_partitioned_by_scope_and_source_filter():
    root_scope_key = _epistemic_cache_key(
        session_id="same-session",
        scope_type="notebook",
        scope_id="notebook-a",
        notebook_id="notebook-a",
        active_sources=None,
    )
    other_notebook_key = _epistemic_cache_key(
        session_id="same-session",
        scope_type="notebook",
        scope_id="notebook-b",
        notebook_id="notebook-b",
        active_sources=None,
    )
    restricted_sources_key = _epistemic_cache_key(
        session_id="same-session",
        scope_type="notebook",
        scope_id="notebook-a",
        notebook_id="notebook-a",
        active_sources=["source-b", "source-a"],
    )
    same_restricted_sources_key = _epistemic_cache_key(
        session_id="same-session",
        scope_type="notebook",
        scope_id="notebook-a",
        notebook_id="notebook-a",
        active_sources=["source-a", "source-b"],
    )

    assert root_scope_key != other_notebook_key
    assert root_scope_key != restricted_sources_key
    assert restricted_sources_key == same_restricted_sources_key


def test_evidence_fallback_does_not_cross_notebook_scope(monkeypatch):
    import study_engine.web.routes.chat as chat_route
    from unittest.mock import MagicMock

    from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT

    session_id = "scope-isolation-session"
    old_pack = EpistemicContextPack(
        formatted_context="evidence from notebook A",
        citations=[],
        chunks=[{"id": "E1", "chunk_text": "notebook A only"}],
        abstained=False,
    )
    old_key = _epistemic_cache_key(
        session_id=session_id,
        scope_type="notebook",
        scope_id="notebook-a",
        notebook_id="notebook-a",
        active_sources=None,
    )
    _LAST_EPISTEMIC_PACK[old_key] = (old_pack, old_pack.chunks)
    _LAST_EPISTEMIC_PACK[f"sess:{session_id}"] = (old_pack, old_pack.chunks)
    notebook_b_key = _epistemic_cache_key(
        session_id=session_id,
        scope_type="notebook",
        scope_id="notebook-b",
        notebook_id="notebook-b",
        active_sources=None,
    )
    _CONV_TURN_BUFFER[notebook_b_key] = [
        {"role": "user", "content": "Pregunta de notebook B"},
        {"role": "assistant", "content": "Respuesta de notebook B"},
    ]

    store = MagicMock()
    store.search_hybrid.return_value = []
    store.search.return_value = []
    store.get_pedagogical_contract.return_value = FASE0_CONTRACT
    store.get_notebook.return_value = MagicMock(folder_id="folder-b")
    container = MagicMock()
    container.knowledge_store = store
    container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    container.bkt_tracker = None
    container.struggle_tracker = None
    container.student_storage = None
    container.mem0_manager = None
    monkeypatch.setattr(
        chat_route,
        "_assemble_epistemic_context",
        lambda **kwargs: (
            EpistemicContextPack(
                formatted_context="",
                citations=[],
                chunks=[],
                abstained=True,
                abstention_reason="QUERY_OUT_OF_SCOPE",
            ),
            [],
        ),
    )

    request = ChatQueryRequest(
        prompt="¿Podés ampliar eso?",
        notebook_id="notebook-b",
        session_id=session_id,
    )
    result = _prepare_chat_context(
        store=store,
        resolver=ScopeResolver(store),
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="notebook",
        target_scope_id="notebook-b",
    )

    context_pack, raw_chunks = result[2], result[3]
    assert getattr(context_pack, "abstained", False) is True
    assert raw_chunks == []
    assert "notebook A" not in getattr(context_pack, "formatted_context", "")


def test_ambiguous_context_reference_fails_closed_with_clarification(monkeypatch):
    from unittest.mock import MagicMock

    from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT

    store = MagicMock()
    store.get_notebook.return_value = MagicMock(folder_id="folder-a")
    container = MagicMock()
    container.knowledge_store = store
    container.pedagogical_orchestrator = MagicMock(_kc_catalog={})
    container.bkt_tracker = None
    container.struggle_tracker = None
    container.student_storage = None
    container.mem0_manager = None
    store.get_pedagogical_contract.return_value = FASE0_CONTRACT
    request = ChatQueryRequest(
        prompt="¿Por qué eso es importante?",
        notebook_id="notebook-a",
        recent_turns=[
            {"role": "user", "content": "¿Qué es un proceso en un sistema operativo?"},
            {"role": "assistant", "content": "Un proceso tiene estado y memoria."},
            {"role": "user", "content": "¿Qué es un archivo ejecutable en disco?"},
        ],
    )

    result = _prepare_chat_context(
        store=store,
        resolver=ScopeResolver(store),
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="notebook",
        target_scope_id="notebook-a",
    )

    context_pack = result[2]
    assert context_pack.abstained is True
    assert context_pack.abstention_reason == "CONTEXT_REFERENCE_REQUIRES_CLARIFICATION"
    assert "único antecedente" in context_pack.clarification_message
