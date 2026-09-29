"""Folder retrieval may cross notebook boundaries only via folder associations.

Technical folder queries are delegated to retrieval, but their candidate
notebooks remain limited to the selected folder subtree.
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
    store.create_folder(Folder(id="roadmap", name="Roadmap", parent_folder_id="folder_root", created_at=now, updated_at=now))
    store.create_folder(Folder(id="roadmap_fase0", name="Fase 0", parent_folder_id="roadmap", created_at=now, updated_at=now))

    # Each folder has its own notebook-source associations.
    from study_engine.contracts.notebook import Notebook
    store.create_notebook(Notebook(id="nb_prog_1", name="Punteros", folder_id="f_prog"))
    store.create_notebook(Notebook(id="fase0-soc", name="Fase 0", folder_id="roadmap_fase0"))

    for notebook_id, source_id in (
        ("nb_prog_1", "src_prog"),
        ("fase0-soc", "src_soc"),
    ):
        rec = SourceRecord(
            source_id=source_id,
            manifest=SourceManifest(
                source_id=source_id,
                filename=f"{source_id}.pdf",
                byte_size=1,
                sha256="1" * 64 if source_id == "src_soc" else "2" * 64,
            ),
        )
        doc = Document(id=f"doc_{source_id}", source_id=source_id, title=source_id, content="")
        chunks = [
            Chunk(
                id=f"c_{source_id}",
                document_id=f"doc_{source_id}",
                source_id=source_id,
                content="El scheduling SJF selecciona el proceso con menor burst estimado.",
                index=0,
            ),
        ]
        store.store_ingestion_bundle(rec, [doc], chunks, notebook_id=notebook_id)
    return store


def _query_folder(store, folder_id: str):
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
        scope_id=folder_id,
        requested_phase="conceptual",
    )
    return _prepare_chat_context(
        store=store,
        resolver=resolver,
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="folder",
        target_scope_id=folder_id,
    )


def test_folder_technical_query_does_not_retrieve_from_other_folder():
    store = _build_store_with_two_notebooks()
    result = _query_folder(store, "f_prog")
    (resolved_scope, contract, context_pack, raw_chunks, folder_decision,
     _mode, _dir, _style, _conv, _kc, _meta) = result

    # Technical query reaches retrieval but cannot inherit another folder's sources.
    assert folder_decision is None
    assert contract is not None and contract.notebook_id == GLOBAL_SCOPE_ID
    assert context_pack is not None and not getattr(context_pack, "abstained", False)
    assert any(chunk["source_id"] == "src_prog" for chunk in raw_chunks)
    assert all(c["source_id"] == "src_prog" for c in raw_chunks)


def test_roadmap_folder_retrieves_fadena_source_only_after_explicit_association():
    store = _build_store_with_two_notebooks()
    store.link_source_to_notebook("fase0-soc", "src_prog")

    result = _query_folder(store, "roadmap")
    _scope, contract, context_pack, raw_chunks, folder_decision, *_rest = result

    assert folder_decision is None
    assert contract is not None and contract.notebook_id == GLOBAL_SCOPE_ID
    assert context_pack is not None and not getattr(context_pack, "abstained", False)
    assert any(chunk["source_id"] == "src_prog" for chunk in raw_chunks)
    assert all(chunk["source_id"] in {"src_prog", "src_soc"} for chunk in raw_chunks)


def test_folder_organizational_query_still_deflects():
    """Las consultas organizacionales siguen respondiendo a nivel carpeta."""
    store = _build_store_with_two_notebooks()
    result = _prepare_chat_context(
        store=store,
        resolver=ScopeResolver(store),
        container=SimpleNamespace(
            ledger=None,
            pedagogical_orchestrator=SimpleNamespace(_kc_catalog={}),
            bkt_tracker=None,
            mem0_manager=None,
            pedagogical_memory_tracker=None,
        ),
        prompt_text="¿en qué cuadernos tengo material de programación?",
        request=ChatQueryRequest(
            prompt="¿en qué cuadernos tengo material de programación?",
            scope_type="folder",
            scope_id="f_prog",
            requested_phase="conceptual",
        ),
        target_scope_type="folder",
        target_scope_id="f_prog",
    )
    assert result[4] is not None  # folder_decision presente
    assert GLOBAL_SCOPE_ID != "f_prog"  # sanity del sentinel
