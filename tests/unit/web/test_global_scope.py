"""COMMIT 2 fix(scope): scope de carpeta con query técnica = acceso global.

Bug original: "Explicame SJF" con scope Programación/roadmap activo era
deflectado por el FolderOrchestrator ("abrí el cuaderno") aunque el corpus
del roadmap contenía el material.

Contrato: folder + query técnica (action=delegate_to_notebook) NO produce
folder_decision; el pipeline corre con scope global y recupera chunks de
CUALQUIER cuaderno, fundidos por chunk_id.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.hierarchy.folder import Folder
from study_engine.hierarchy.scope_resolver import ScopeResolver
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.routes.chat import (
    GLOBAL_SCOPE_ID,
    _prepare_chat_context,
    ChatQueryRequest,
)


def _build_store_with_two_notebooks():
    store = KnowledgeStore(":memory:")
    store.initialize()
    now = datetime.now(timezone.utc)
    if not store.contains_folder("folder_root"):
        store.create_folder(Folder(id="folder_root", name="Root", parent_folder_id=None, created_at=now, updated_at=now))
    store.create_folder(Folder(id="f_prog", name="Carrera Programación", parent_folder_id="folder_root", created_at=now, updated_at=now))

    # nb_prog_1: cuaderno de Programación SIN material de SO
    from study_engine.contracts.notebook import Notebook
    store.create_notebook(Notebook(id="nb_prog_1", name="Punteros", folder_id="f_prog"))
    # fase0-soc: bóveda con material de SO (SJF)
    store.create_notebook(Notebook(id="fase0-soc", name="Fase 0", folder_id="folder_root"))

    rec = SourceRecord(
        source_id="src_soc",
        manifest=SourceManifest(source_id="src_soc", filename="so.pdf", byte_size=1, sha256="1" * 64),
    )
    doc = Document(id="doc_soc", source_id="src_soc", title="SO", content="")
    chunks = [
        Chunk(id="c_sjf", document_id="doc_soc", source_id="src_soc",
              content="El scheduling SJF selecciona el proceso con menor burst estimado.", index=0),
    ]
    store.store_ingestion_bundle(rec, [doc], chunks, notebook_id="fase0-soc")
    return store


def test_folder_technical_query_goes_global_and_retrieves_cross_notebook():
    store = _build_store_with_two_notebooks()
    resolver = ScopeResolver(store)
    container = SimpleNamespace(
        ledger=None,
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={}),
        bkt_tracker=None,
        mem0_manager=None,
        pedagogical_memory_tracker=None,
    )
    request = ChatQueryRequest(
        prompt="Explicame cómo funciona el scheduling SJF",
        scope_type="folder",
        scope_id="f_prog",
        requested_phase="conceptual",
    )

    result = _prepare_chat_context(
        store=store,
        resolver=resolver,
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="folder",
        target_scope_id="f_prog",
    )
    (resolved_scope, contract, context_pack, raw_chunks, folder_decision,
     _mode, _dir, _style, _conv, _kc, _meta) = result

    # No se deflectó al usuario: el pipeline continuó con scope global
    assert folder_decision is None
    # contrato sintético neutral (el pipeline requiere uno; antes: crash 500)
    assert contract is not None and contract.notebook_id == GLOBAL_SCOPE_ID
    assert context_pack is not None and not getattr(context_pack, "abstained", False)
    # Y el chunk vino del cuaderno BÓVEDA, no del cuaderno del folder
    assert any(c["source_id"] == "src_soc" for c in raw_chunks)


def test_folder_organizational_query_still_deflects():
    """Las consultas organizacionales siguen respondiendo a nivel carpeta."""
    store = _build_store_with_two_notebooks()
    resolver = ScopeResolver(store)
    container = SimpleNamespace(
        ledger=None,
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={}),
        bkt_tracker=None,
        mem0_manager=None,
        pedagogical_memory_tracker=None,
    )
    request = ChatQueryRequest(
        prompt="¿en qué cuadernos tengo material de programación?",
        scope_type="folder",
        scope_id="f_prog",
        requested_phase="conceptual",
    )
    result = _prepare_chat_context(
        store=store,
        resolver=resolver,
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="folder",
        target_scope_id="f_prog",
    )
    assert result[4] is not None  # folder_decision presente
    assert GLOBAL_SCOPE_ID != "f_prog"  # sanity del sentinel
