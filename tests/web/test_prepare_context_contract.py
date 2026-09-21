"""P0: prepare-context always returns 11 values on notebook, folder and fast-path."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from study_engine.hierarchy.scope_resolver import ResolvedScope, ScopeType
from study_engine.memory.mem0_manager import Mem0Manager
from study_engine.student.storage import StudentStorage
from study_engine.tutor.policy_validator import RouteKind
from study_engine.web.routes.chat import (
    PREPARE_CONTEXT_ARITY,
    ChatQueryRequest,
    _pack_prepare_context,
    _prepare_chat_context,
    _trigger_background_memory_extraction,
)


def test_prepare_context_contract_all_paths():
    notebook_scope = ResolvedScope(
        scope_type=ScopeType.NOTEBOOK, scope_id="nb1", notebook_id="nb1"
    )
    folder_scope = ResolvedScope(
        scope_type=ScopeType.FOLDER, scope_id="f_prog", folder_id="f_prog"
    )
    paths = {
        "notebook": _pack_prepare_context(
            notebook_scope,
            contract=object(),
            context_pack=object(),
            raw_chunks=[],
            context_mode="intermediate",
            bkt_directive="dir",
            style_result=object(),
            matched_kc_id="kc_loops",
            bkt_meta={"p_L": 0.4, "unmet_prerequisites": []},
        ),
        "folder": _pack_prepare_context(folder_scope, folder_decision=object()),
        "fast_path": _pack_prepare_context(
            notebook_scope,
            conv_payload=(object(), RouteKind.GREETING, {}),
        ),
    }
    for path, result in paths.items():
        assert len(result) == PREPARE_CONTEXT_ARITY, f"{path} devuelve {len(result)} valores"
    assert paths["folder"][9] is None and paths["folder"][10] is None
    assert paths["fast_path"][9] is None and paths["fast_path"][10] is None
    assert paths["notebook"][10]["p_L"] == 0.4


def test_prepare_chat_context_folder_arity():
    store = MagicMock()
    store.contains_folder.return_value = True
    resolver = MagicMock()
    resolver.resolve.return_value = ResolvedScope(
        scope_type=ScopeType.FOLDER, scope_id="f_prog", folder_id="f_prog"
    )
    container = MagicMock()
    container.ledger = None
    request = ChatQueryRequest(
        prompt="¿Cuál es mi progreso en esta carpeta?",
        scope_type="folder",
        scope_id="f_prog",
    )
    with patch(
        "study_engine.hierarchy.folder_orchestrator.FolderOrchestrator"
    ) as orch_cls:
        orch_cls.return_value.route_query.return_value = {"kind": "organizational"}
        result = _prepare_chat_context(
            store=store,
            resolver=resolver,
            container=container,
            prompt_text=request.prompt or "",
            request=request,
            target_scope_type="folder",
            target_scope_id="f_prog",
        )
    assert len(result) == PREPARE_CONTEXT_ARITY
    assert result[4] == {"kind": "organizational"}
    assert result[9] is None
    assert result[10] is None


def test_prepare_chat_context_fast_path_arity():
    store = MagicMock()
    resolver = MagicMock()
    resolver.resolve.return_value = ResolvedScope(
        scope_type=ScopeType.NOTEBOOK,
        scope_id="fase0-soc",
        notebook_id="fase0-soc",
    )
    container = MagicMock()
    request = ChatQueryRequest(
        prompt="hola",
        notebook_id="fase0-soc",
        requested_phase="conceptual",
    )
    with patch(
        "study_engine.tutor.fastpath_service.FastPathConversationalService.detect_conversational_route",
        return_value=(True, RouteKind.GREETING),
    ), patch(
        "study_engine.tutor.fastpath_service.FastPathConversationalService.extract_student_context",
        return_value={"student": "agustin"},
    ):
        result = _prepare_chat_context(
            store=store,
            resolver=resolver,
            container=container,
            prompt_text="hola",
            request=request,
            target_scope_type="notebook",
            target_scope_id="fase0-soc",
        )
    assert len(result) == PREPARE_CONTEXT_ARITY
    assert result[8] is not None
    assert result[9] is None
    assert result[10] is None


def test_prepare_chat_context_notebook_arity():
    store = MagicMock()
    store.get_pedagogical_contract.return_value = SimpleNamespace(id="contract")
    resolver = MagicMock()
    resolver.resolve.return_value = ResolvedScope(
        scope_type=ScopeType.NOTEBOOK,
        scope_id="fase0-soc",
        notebook_id="fase0-soc",
    )
    container = MagicMock()
    container.pedagogical_orchestrator = SimpleNamespace(
        _kc_catalog={"fase0-soc": {"kcs": [{"kc_id": "kc_while", "title": "Bucle MIENTRAS"}]}}
    )
    container.bkt_tracker = None
    container.mem0_manager = None
    container.pedagogical_memory_tracker = None
    request = ChatQueryRequest(
        prompt="¿Por qué un bucle MIENTRAS puede convertirse en infinito?",
        notebook_id="fase0-soc",
        requested_phase="conceptual",
    )
    pack = SimpleNamespace(abstained=False)
    with patch(
        "study_engine.tutor.fastpath_service.FastPathConversationalService.detect_conversational_route",
        return_value=(False, None),
    ), patch(
        "study_engine.web.routes.chat._assemble_epistemic_context",
        return_value=(pack, []),
    ):
        result = _prepare_chat_context(
            store=store,
            resolver=resolver,
            container=container,
            prompt_text=request.prompt or "",
            request=request,
            target_scope_type="notebook",
            target_scope_id="fase0-soc",
        )
    assert len(result) == PREPARE_CONTEXT_ARITY
    assert result[9] == "kc_while"
    assert isinstance(result[10], dict)
    assert "p_L" in result[10]


def test_trigger_background_memory_uses_real_notebook_id(tmp_path):
    db_path = tmp_path / "student_state.db"
    storage = StudentStorage(str(db_path))
    mem0 = Mem0Manager(student_storage=storage)
    captured = {}

    def _capture_process(**kwargs):
        captured.update(kwargs)
        return Mem0Manager.process_turn_memories(mem0, **kwargs)

    mem0.process_turn_memories = _capture_process  # type: ignore[method-assign]

    container = SimpleNamespace(
        pedagogical_memory_extractor=None,
        student_storage=None,
        mem0_manager=mem0,
    )
    _trigger_background_memory_extraction(
        container=container,
        student_id="agustin",
        prompt_text="Mostrame un diagrama mermaid del bucle y que no tenga off-by-one",
        response_text="Acá va el diagrama...",
        active_kc="kc_while",
        pedagogical_mode="conceptual",
        llm_backend=None,
        notebook_id="fase0-soc",
    )
    assert captured.get("notebook_id") == "fase0-soc"
    stats = mem0.get_memory_stats("agustin")
    assert stats.get("preference", 0) >= 1
    assert db_path.exists()
    assert db_path.stat().st_size > 0
