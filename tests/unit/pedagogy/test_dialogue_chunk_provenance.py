"""Unit tests M1-02: provenance del diálogo Socrático en S4.4.

Hallazgo live (2026-10-20): el Nivel 1 de `_retrieve_evidence` entregaba
strings de citation_id como chunks; `generation_adapter` exige provenance
completa (chunk_id, document_id, source_id, source_title) y contenido con
hash verificable → ValueError previo a la generación → REJECTED_AUDIT_ERROR
en TODOS los turnos de diálogo (post d1/d2: ABSTAINED en <1s).

Contrato del fix:
- El contenido del chunk citado se materializa por chunk_id del store
  autorizado y se verifica sha256(content) == citation.content_hash.
- Cita sin contenido, inexistente o con hash mismatch → excluida
  (fail-closed); con cero citas verificables el Nivel 1 no admite evidencia.
- El chunk dict construido satisface la validación de provenance completa
  del adapter (contract real, no shape nominal).
- Sin loader (wiring de tests/legacy) se preserva el comportamiento anterior.
"""

import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace

import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.dialogue_engine import DialogueEngine, EvidenceResult
from study_engine.pedagogy.dialogue_policy import ValidatedIntent


CHUNK_CONTENT = (
    "Un puntero es una variable que contiene la dirección de memoria de otro objeto. "
    "La aritmética de punteros escala el desplazamiento por el tamaño del tipo apuntado."
)
CONTENT_HASH = hashlib.sha256(CHUNK_CONTENT.encode("utf-8")).hexdigest()


def make_citation(cid: str = "E1") -> CitationRecord:
    return CitationRecord(
        citation_id=cid,
        chunk_id=f"chk_{cid}",
        document_id=f"doc_{cid}",
        source_id="src_joyanes_fundamentos",
        source_title="Joyanes - Fundamentos de Programación",
        content_hash=CONTENT_HASH,
    )


def make_packet(citations) -> ConceptPacket:
    return ConceptPacket(
        kc_id="aritmetica_punteros",
        notebook_id="fase0-soc",
        objective="Comprender aritmética de punteros",
        evidence_by_role={"PRIMARY": list(citations)},
        core_concept="Direccionamiento contiguo",
        mental_model="Memoria lineal por offset",
        reasoning_guidance="Base más offset por sizeof(T).",
        formalization=None,
        implementation_guidance=None,
        pitfalls=(),
        citations=tuple(citations),
        s44_report=None,
        audit_verdict=AuditVerdict.APPROVED,
        assembly_hash="c" * 64,
    )


def make_store_chunk(chunk_id: str = "chk_E1", content: str = CHUNK_CONTENT) -> SimpleNamespace:
    return SimpleNamespace(
        chunk_id=chunk_id,
        id=chunk_id,
        document_id="doc_E1",
        source_id="src_joyanes_fundamentos",
        content=content,
    )


def make_intent() -> ValidatedIntent:
    return ValidatedIntent(
        action="PROCEED_DIALOGUE",
        query_text="¿cómo funciona?",
        proposed_intent="CLARIFICATION",
    )


def build_engine(store_chunks: dict, **kwargs) -> DialogueEngine:
    loader = (lambda chunk_id: store_chunks.get(chunk_id)) if store_chunks is not None else None
    return DialogueEngine(chunk_content_loader=loader, **kwargs)


def test_level1_materializes_citations_with_full_provenance():
    """Chunks del Nivel 1 = dicts con provenance completa + hash verificado."""
    cit = make_citation()
    engine = build_engine({"chk_E1": make_store_chunk()})
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([cit]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    assert evidence.level == "CONCEPT_PACKET"
    assert len(evidence.chunks) == 1
    chunk = evidence.chunks[0]
    assert chunk["chunk_id"] == "chk_E1"
    assert chunk["document_id"] == "doc_E1"
    assert chunk["source_id"] == "src_joyanes_fundamentos"
    assert chunk["source_title"] == "Joyanes - Fundamentos de Programación"
    assert chunk["citation_id"] == "E1"
    # Provenance de fuente: trust_level canónico (CHECK_SOURCE_PROVENANCE).
    assert chunk["trust_level"] == "canonical"
    # Hash del contenido EXACTO entregado (cadena adapter consistente).
    assert chunk["content_hash"] == hashlib.sha256(chunk["content"].encode()).hexdigest()
    # Identidad con el packet: el contenido materializado es el verificado.
    assert hashlib.sha256(chunk["content"].rstrip().encode()).hexdigest() == CONTENT_HASH or (
        chunk["content"] == CHUNK_CONTENT
    )


def test_level1_excludes_citation_with_hash_mismatch():
    """Mismatch de hash → cita excluida; Nivel 1 sin admisión (fail-closed)."""
    bad = make_citation("E1")
    forged = make_citation("E2")
    store = {
        "chk_E1": make_store_chunk(),  # contenido íntegro
        "chk_E2": make_store_chunk(content="contenido alterado que no verifica el hash"),
    }
    engine = build_engine(store)
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([bad, forged]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    # Sólo sobrevive la cita con identidad verificable.
    assert [c["citation_id"] for c in evidence.chunks] == ["E1"]


def test_level1_missing_chunk_excludes_citation():
    """Chunk inexistente en el store → cita excluida (fail-closed)."""
    cit = make_citation()
    engine = build_engine({})  # store vacío
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([cit]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    assert evidence.level == "NONE"
    assert len(evidence.chunks) == 0


def test_level1_loader_error_excludes_citation():
    """Fallo del loader → cita excluida, jamás propagación de excepción."""
    def failing_loader(_chunk_id):
        raise RuntimeError("store caído")

    engine = DialogueEngine(chunk_content_loader=failing_loader)
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([make_citation()]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    assert evidence.level == "NONE"
    assert len(evidence.chunks) == 0


def test_level1_without_loader_preserves_legacy_shape():
    """Sin loader (wiring de tests): strings nominales como antes del fix."""
    cit = make_citation()
    engine = DialogueEngine()  # chunk_content_loader=None
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([cit]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    assert evidence.level == "CONCEPT_PACKET"
    assert evidence.chunks == ("E1",)


def test_s44_audit_accepts_materialized_chunks_via_real_adapter():
    """Extremo a extremo: `_execute_s44_audit` con el generation_adapter REAL
    sobre chunks materializados → veredicto del auditor (sin ValueError de
    provenance)."""
    cit = make_citation()
    engine = build_engine(
        {"chk_E1": make_store_chunk()},
        forensic_auditor=SimpleNamespace(
            audit=lambda _input: ForensicAuditReport(
                audit_id="audit-dialogue-synthetic",
                request_id="req_dialogue_synthetic",
                notebook_id="fase0-soc",
                overall_verdict=AuditVerdict.APPROVED,
                audit_latency_ms=1.0,
                auditor_backend="synthetic-auditor",
            )
        ),
    )
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([cit]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    verdict = engine._execute_s44_audit(
        "La estructura contigua permite direccionar por offset [E1].", evidence
    )
    # El adapter construyó el reporte (sin ValueError de provenance) y el
    # auditor sintético devolvió APPROVED.
    assert verdict == "APPROVED"


def test_s44_audit_rejects_on_legacy_string_chunks():
    """Comportamiento previo (chunks-string): el adapter REAL rechaza con
    REJECTED_AUDIT_ERROR — documenta el bug corregido."""
    cit = make_citation()
    engine = build_engine({"chk_E1": make_store_chunk()})
    # EvidenceResult manual con chunks-string (shape pre-fix).
    evidence = EvidenceResult(chunks=["E1"], citations=[cit], level="CONCEPT_PACKET")
    verdict = engine._execute_s44_audit("Respuesta [E1].", evidence)
    assert verdict == "REJECTED_AUDIT_ERROR"


def test_evidence_result_carries_audit_context():
    """query/notebook_id quedan disponibles para generation_adapter."""
    cit = make_citation()
    engine = build_engine({"chk_E1": make_store_chunk()})
    evidence = asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet([cit]),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )
    assert getattr(evidence, "notebook_id", None) == "fase0-soc"
    assert getattr(evidence, "query", None) == "dialogue_turn"
