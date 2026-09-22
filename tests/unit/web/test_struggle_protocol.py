"""Protocolo de Lucha (Fase 5.3b) — 3 fallos consecutivos activan la directiva.

Contrato:
- record(kc, False) x3 -> is_struggling(kc) True -> se emite STRUGGLE_DIRECTIVE.
- Un acierto o cambio de KC resetea la racha.
- En el chat, el bkt_directive del siguiente turno contiene la directiva
  ("PROHIBIDO repetir la explicación teórica" + cambio de modalidad + predicción).
"""

from types import SimpleNamespace

from study_engine.pedagogy.exercise_service import STRUGGLE_DIRECTIVE, StruggleTracker


def test_tres_fallos_activan_lucha():
    t = StruggleTracker()
    for _ in range(2):
        t.record("kc_z", correct=False)
    assert not t.is_struggling("kc_z")
    t.record("kc_z", correct=False)
    assert t.is_struggling("kc_z")
    assert "PROHIBIDO repetir" in t.directive("kc_z")


def test_acierto_resetea():
    t = StruggleTracker()
    for _ in range(3):
        t.record("kc_z", correct=False)
    assert t.is_struggling("kc_z")
    t.record("kc_z", correct=True)
    assert not t.is_struggling("kc_z")


def test_cambio_de_kc_resetea_foco():
    t = StruggleTracker()
    for _ in range(3):
        t.record("kc_z", correct=False)
    assert t.is_struggling("kc_z")
    t.record("kc_otro", correct=False)  # cambio de KC
    assert not t.is_struggling("kc_z")
    assert not t.is_struggling("kc_otro")


def test_el_prompt_del_chat_lleva_la_directiva():
    """_prepare_chat_context inyecta la directiva en bkt_directive si hay lucha."""
    from datetime import datetime, timezone

    from study_engine.contracts.catalog import SourceRecord
    from study_engine.contracts.chunk import Chunk
    from study_engine.contracts.document import Document
    from study_engine.contracts.ingestion import SourceManifest
    from study_engine.hierarchy.scope_resolver import ScopeResolver
    from study_engine.storage.knowledge_store import KnowledgeStore
    from study_engine.web.routes.chat import ChatQueryRequest, _prepare_chat_context
    from study_engine.contracts.notebook import Notebook

    store = KnowledgeStore(":memory:")
    store.initialize()
    store.create_notebook(Notebook(id="nb1", name="NB1"))
    rec = SourceRecord(
        source_id="src1",
        manifest=SourceManifest(source_id="src1", filename="a.pdf", byte_size=1, sha256="1" * 64),
    )
    doc = Document(id="d1", source_id="src1", title="Doc", content="")
    chunks = [Chunk(id="c1", document_id="d1", source_id="src1",
                    content="La búsqueda binaria divide el espacio a la mitad.", index=0)]
    store.store_ingestion_bundle(rec, [doc], chunks, notebook_id="nb1")

    kcs = [{"kc_id": "kc_busq", "title": "Búsqueda binaria",
            "subtopics": ["búsqueda binaria en arreglos"]}]
    struggle = StruggleTracker()
    for _ in range(3):
        struggle.record("kc_busq", correct=False)

    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={"nb1": {"kcs": kcs}}),
        bkt_tracker=None,
        mem0_manager=None,
        pedagogical_memory_tracker=None,
        struggle_tracker=struggle,
    )
    req = ChatQueryRequest(
        prompt="¿cómo funciona la búsqueda binaria en arreglos?",
        notebook_id="nb1",
        requested_phase="conceptual",
    )
    result = _prepare_chat_context(
        store=store,
        resolver=ScopeResolver(store),
        container=container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="nb1",
    )
    bkt_directive = result[6]
    assert bkt_directive and STRUGGLE_DIRECTIVE in bkt_directive
