"""S4.4 in study episodes must receive exact, hash-bound retrieved text."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.pedagogy.evidence_assembler import (
    AssembledEvidenceBundle,
    MultiSourceEvidenceAssembler,
)
from study_engine.pedagogy.orchestrator import _package_citation_evidence


def _citation(citation_id: str, content: str) -> CitationRecord:
    return CitationRecord(
        citation_id=citation_id,
        chunk_id=f"chunk-{citation_id}",
        document_id="synthetic-document",
        source_id="synthetic-source",
        source_title="Synthetic academic page",
        page_start=2,
        page_end=2,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def test_s44_packaging_uses_exact_retrieved_chunk_not_placeholder() -> None:
    source_text = "El primer paso es la recopilación de requisitos y el análisis."
    citation = _citation("E1", source_text)

    units = _package_citation_evidence([citation], {"E1": source_text})

    assert units is not None
    assert units[0].content == source_text
    assert hashlib.sha256(units[0].content.encode("utf-8")).hexdigest() == citation.content_hash
    assert "Contenido verificado para cita" not in units[0].content


def test_s44_packaging_rejects_missing_or_hash_mismatched_source_text() -> None:
    source_text = "Fuente exacta."
    citation = _citation("E1", source_text)

    assert _package_citation_evidence([citation], {}) is None
    assert _package_citation_evidence([citation], {"E1": "Texto distinto."}) is None


def test_assembler_uses_knowledge_store_chunk_repository_and_keeps_text(tmp_path: Path) -> None:
    roles_path = tmp_path / "roles.json"
    roles_path.write_text(json.dumps({
        "synthetic-notebook": {
            "synthetic-source": {"roles": ["PRIMARY"], "title": "Synthetic source"},
        },
    }), encoding="utf-8")
    chunk_texts = [
        "El primer paso del proceso es la recopilación de requisitos y el análisis.",
        "El diseño conceptual traduce los requisitos a un esquema de alto nivel.",
    ]
    chunks = [
        SimpleNamespace(
            id=f"chunk-{index}", document_id="synthetic-document",
            content=content, page_start=index + 2, page_end=index + 2,
        )
        for index, content in enumerate(chunk_texts)
    ]

    def get_notebook(notebook_id):
        assert notebook_id == "synthetic-notebook"
        return SimpleNamespace(sources=["synthetic-source"])

    def list_by_source(source_id):
        assert source_id == "synthetic-source"
        return chunks

    store = SimpleNamespace(
        chunks=SimpleNamespace(list_by_source=list_by_source),
        get_notebook=get_notebook,
    )

    assembler = MultiSourceEvidenceAssembler(
        knowledge_store=store, roles_config_path=roles_path,
    )
    bundle = assembler.assemble_evidence_bundle_for_kc(
        notebook_id="synthetic-notebook",
        kc_id="synthetic-kc",
        query="el",
    )

    assert len(bundle.citations) == 2
    for citation in bundle.citations:
        exact_text = bundle.content_by_citation[citation.citation_id]
        assert exact_text in chunk_texts
        assert hashlib.sha256(exact_text.encode("utf-8")).hexdigest() == citation.content_hash


def test_concept_orchestrator_reads_overall_verdict_and_abstains(monkeypatch) -> None:
    from study_engine.pedagogy import orchestrator as orchestrator_module

    content = "Una fuente de evidencia textual exacta."
    citation = _citation("E1", content)
    episode = SimpleNamespace(
        episode_id="synthetic-episode",
        notebook_id="synthetic-notebook",
        kc_id="synthetic-kc",
        objective="synthetic objective",
    )
    bundle = AssembledEvidenceBundle(
        evidence_by_role={"PRIMARY": [citation]},
        citations=[citation],
        content_by_citation={"E1": content},
    )
    report = ForensicAuditReport(
        audit_id="audit-synthetic-rejected",
        request_id="req_synthetic-episode",
        notebook_id="synthetic-notebook",
        overall_verdict=AuditVerdict.REJECTED_UNSUPPORTED,
        audit_latency_ms=1.0,
        auditor_backend="synthetic-auditor",
    )
    orchestrator = orchestrator_module.PedagogicalOrchestrator.__new__(
        orchestrator_module.PedagogicalOrchestrator
    )
    orchestrator.get_episode = lambda _episode_id: episode
    orchestrator.evidence_assembler = SimpleNamespace(
        assemble_evidence_bundle_for_kc=lambda **_kwargs: bundle
    )
    orchestrator.concept_builder = SimpleNamespace(build_proposal=lambda **_kwargs: SimpleNamespace(
        core_concept="A synthetic proposal [E1].",
        mental_model="A second synthetic proposal [E1].",
    ))
    orchestrator.forensic_auditor = SimpleNamespace(audit=lambda _audit_input: report)
    monkeypatch.setattr(orchestrator_module, "get_student_context", lambda _notebook_id: None)

    result = orchestrator.explain_concept("synthetic-episode")

    assert result.status == "ABSTAINED"
    assert result.audit_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert "REJECTED_UNSUPPORTED" in (result.abstention_reason or "")


def test_concept_orchestrator_reads_overall_verdict_on_approval(monkeypatch) -> None:
    """M1-02 regresión: el branch PRESENTABLE/APROVVED debe leer
    `overall_verdict` (no `.verdict`, atributo inexistente en
    ForensicAuditReport). Este branch no era alcanzable en live hasta que la
    reutilización de veredictos NLI M1-02 permitió un APPROVED real
    (POST /dialogue + GET /concept devolvieron 500 AttributeError)."""
    from study_engine.pedagogy import orchestrator as orchestrator_module

    content = "Una fuente de evidencia textual exacta."
    citation = _citation("E1", content)
    episode = SimpleNamespace(
        episode_id="synthetic-episode",
        notebook_id="synthetic-notebook",
        kc_id="synthetic-kc",
        objective="synthetic objective",
    )
    bundle = AssembledEvidenceBundle(
        evidence_by_role={"PRIMARY": [citation]},
        citations=[citation],
        content_by_citation={"E1": content},
    )
    report = ForensicAuditReport(
        audit_id="audit-synthetic-approved",
        request_id="req_synthetic-episode",
        notebook_id="synthetic-notebook",
        overall_verdict=AuditVerdict.APPROVED,
        audit_latency_ms=1.0,
        auditor_backend="synthetic-auditor",
    )
    proposal = SimpleNamespace(
        kc_id="synthetic-kc",
        notebook_id="synthetic-notebook",
        objective="synthetic objective",
        evidence_by_role={"PRIMARY": [citation]},
        core_concept="[E1] Una fuente de evidencia textual exacta.",
        mental_model="[E1] Una fuente de evidencia textual exacta.",
        reasoning_guidance="Pasos deterministas de razonamiento.",
        formalization=None,
        implementation_guidance=None,
        pitfalls=(),
        citations=(citation,),
        assembly_hash="hash-synthetic",
    )
    orchestrator = orchestrator_module.PedagogicalOrchestrator.__new__(
        orchestrator_module.PedagogicalOrchestrator
    )
    orchestrator.get_episode = lambda _episode_id: episode
    orchestrator.evidence_assembler = SimpleNamespace(
        assemble_evidence_bundle_for_kc=lambda **_kwargs: bundle
    )
    orchestrator.concept_builder = SimpleNamespace(build_proposal=lambda **_kwargs: proposal)
    orchestrator.forensic_auditor = SimpleNamespace(audit=lambda _audit_input: report)
    monkeypatch.setattr(orchestrator_module, "get_student_context", lambda _notebook_id: None)

    result = orchestrator.explain_concept("synthetic-episode")

    assert result.status == "PRESENTABLE"
    assert result.audit_verdict == AuditVerdict.APPROVED
    assert result.packet is not None
    assert result.packet.audit_verdict == AuditVerdict.APPROVED
    assert result.packet.s44_report is report
    assert result.packet.core_concept.startswith("[E1]")
    assert result.abstention_reason is None
