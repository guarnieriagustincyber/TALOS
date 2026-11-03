import json
from types import SimpleNamespace

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.source import Source
from study_engine.storage.knowledge_store import KnowledgeStore

from study_engine.web.routes.chat import (
    _assemble_epistemic_context,
    _style_directive_for_task,
    _trust_level_from_manifest,
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import AuditVerdict, CheckStatus
from study_engine.audit.generation_adapter import audit_generation_payload
from study_engine.pedagogy.style_contracts import ConversationStyle


def test_chat_trust_uses_source_manifest_policy_and_fails_closed_on_unknown_values():
    assert _trust_level_from_manifest(json.dumps({"metadata": {"trust_level": "canonical"}})) == "canonical"
    assert _trust_level_from_manifest(json.dumps({"metadata": {"trust_level": "unverified"}})) == "unverified"
    assert _trust_level_from_manifest(json.dumps({"metadata": {"trust_level": "verified"}})) == "unverified"
    assert _trust_level_from_manifest("not-json") == "unverified"
    assert _trust_level_from_manifest(None) == "unverified"


def test_chat_trust_matches_the_existing_evidence_engine_default_for_registered_sources():
    # Existing EvidenceEngine treats a persisted source manifest without an
    # override as canonical; chat now carries that same policy into S4.4.
    assert _trust_level_from_manifest(json.dumps({"metadata": {}})) == "canonical"


def test_prompt_uses_exact_evidence_ids_from_the_audit_manifest(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path / "knowledge.db")
    store.initialize()
    store.create_notebook(Notebook(id="synthetic-rag-a", name="Synthetic RAG A"))
    source_id = "synthetic-buffer-source"
    store.store_ingestion_bundle(
        SourceRecord(
            source_id=source_id,
            manifest=SourceManifest(
                source_id=source_id, filename="synthetic-buffer.txt",
                byte_size=40, sha256="a" * 64,
                metadata={"trust_level": "canonical"},
            ),
            source=Source(source_id=source_id, title="Synthetic Buffer"),
        ),
        [Document(id="synthetic-buffer-document", source_id=source_id, title="Synthetic Buffer")],
        [Chunk(
            id="synthetic-buffer-chunk", document_id="synthetic-buffer-document",
            source_id=source_id,
            content="El búfer compartido permite al productor escribir datos y al consumidor leerlos.",
            page_start=7, page_end=7,
        )],
        notebook_id="synthetic-rag-a",
    )
    manifest_path = tmp_path / "l3-synthetic.json"
    manifest_path.write_text(json.dumps({"grants": [{
        "notebook_id": "synthetic-rag-a", "source_id": source_id, "status": "AUTHORIZED",
    }]}), encoding="utf-8")
    store.l3_manifest_path = manifest_path
    monkeypatch.setattr(store, "vector_search", lambda **_kwargs: [])

    from study_engine.retrieval.expansion import SectionExpander

    monkeypatch.setattr(
        SectionExpander,
        "expand_results",
        lambda _self, **_kwargs: ([], "[CHUNK 0 | Pág 1 | Unbound]\\nUnsupported neighbor"),
    )
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={}),
    )
    pack, chunks = _assemble_epistemic_context(
        store=store,
        container=container,
        prompt_text="¿Qué hace el búfer compartido?",
        target_notebook_id="synthetic-rag-a",
    )

    assert pack is not None and not pack.abstained
    assert len(chunks) == 1
    assert chunks[0]["citation_id"] == "E1"
    assert chunks[0]["chunk_id"] == "synthetic-buffer-chunk"
    assert chunks[0]["trust_level"] == "canonical"
    assert "[E1] Fuente: Synthetic Buffer (Pág: 7)" in pack.formatted_context
    assert "[1] [E1]" not in pack.formatted_context
    assert "Unsupported neighbor" not in pack.formatted_context

    auditor = ForensicAuditor()
    bad = audit_generation_payload(
        auditor, generated_text="El búfer compartido permite escribir y leer datos [1].",
        context_chunks=chunks, query="¿Qué hace el búfer?", notebook_id="synthetic-rag-a",
    )
    assert bad.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert any(check.check_id == "CHECK_FACTUAL_GROUNDING" and check.status == CheckStatus.FAIL
               for check in bad.deterministic_checks)

    good = audit_generation_payload(
        auditor, generated_text="El búfer compartido permite escribir y leer datos [E1].",
        context_chunks=chunks, query="¿Qué hace el búfer?", notebook_id="synthetic-rag-a",
    )
    assert good.overall_verdict == AuditVerdict.APPROVED

    uncited_example = audit_generation_payload(
        auditor,
        generated_text=(
            "El búfer compartido permite escribir y leer datos [E1]. "
            "Una CPU de 128 bits siempre escribe ahí."
        ),
        context_chunks=chunks, query="¿Qué hace el búfer?", notebook_id="synthetic-rag-a",
    )
    assert uncited_example.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_basic_direct_answer_does_not_force_unsupported_machine_layer():
    formal = SimpleNamespace(style=ConversationStyle.FORMAL_EXPLANATION,
                             instruction_directive="TRI-CAPA MANDATORIA")
    basic = _style_directive_for_task(formal, "responder la consulta")
    assert "Cada oración declarativa" in basic
    assert "Una cita de la oración anterior no se hereda" in basic
    assert "no amplíes una definición" in basic
    assert "conservá ese alcance" in basic
    assert "nivel de máquina obligatorio" in basic
    assert "TRI-CAPA MANDATORIA" not in basic
    assert _style_directive_for_task(formal, "explicar en profundidad") == "TRI-CAPA MANDATORIA"


def test_comparative_style_requires_cell_level_grounding_and_avoids_inferred_tradeoffs():
    formal = SimpleNamespace(style=ConversationStyle.FORMAL_EXPLANATION,
                             instruction_directive="TRI-CAPA MANDATORIA")
    directive = _style_directive_for_task(formal, "comparar")
    assert directive is not None
    assert "Cada celda factual" in directive
    assert "no agregues pros" in directive
