"""System-Level Acceptance Audit: Epistemological Thesis (Fase 6.1).

Verifies the formal semantics of APPROVED in TALOS:
    grounded ≠ trusted ≠ correct ≠ true

APPROVED does not mean "metaphysical objective truth about reality".
APPROVED means:
"The response is strictly grounded in an authorized, canonical source of truth."
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    ForensicAuditInput,
)
from study_engine.contracts.enums import SourceRole
from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)


def _build_audit_package(
    citations_data: List[Dict[str, Any]],
    claim_text: str,
    cited_tags: List[str],
) -> ForensicAuditInput:
    manifest_records: Dict[str, CitationRecord] = {}
    packaged_units: List[PackagedEvidenceUnit] = []

    for item in citations_data:
        tag = str(item["tag"])
        source_id = str(item["source_id"])
        trust_level = str(item.get("trust_level", "canonical"))
        content = str(item["content"])
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        citation_rec = CitationRecord(
            citation_id=tag,
            chunk_id=f"chunk_{source_id}",
            document_id=f"doc_{source_id}",
            source_id=source_id,
            source_title=f"Source {source_id}",
            content_hash=c_hash,
            grade=EvidenceGrade.DIRECT,
            source_role=SourceRole.PRIMARY if trust_level == "canonical" else SourceRole.REFERENCE,
            trust_level=trust_level,
        )
        manifest_records[tag] = citation_rec
        packaged_units.append(
            PackagedEvidenceUnit(
                citation=citation_rec,
                content=content,
                retrieval_score=0.95,
                retrieval_rank=1,
                retrieval_method="bm25",
            )
        )

    parsed_cites_list: List[ParsedCitation] = []
    for tag in cited_tags:
        if tag in manifest_records:
            rec = manifest_records[tag]
            parsed_cites_list.append(
                ParsedCitation(
                    citation_id=tag,
                    in_manifest=True,
                    chunk_id=rec.chunk_id,
                    source_id=rec.source_id,
                    grade=EvidenceGrade.DIRECT,
                )
            )
        else:
            # Phantom citation not in manifest
            parsed_cites_list.append(
                ParsedCitation(
                    citation_id=tag,
                    in_manifest=False,
                    chunk_id=f"chunk_phantom_{tag}",
                    source_id=f"source_phantom_{tag}",
                    grade=EvidenceGrade.DIRECT,
                )
            )

    full_context_text = "\n\n".join(u.content for u in packaged_units)
    packet = EvidencePacket(
        original_query="Epistemological verification query",
        normalized_query="Epistemological verification query",
        notebook_id="nb_epistemology",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=CitationManifest(records=manifest_records),
        packaged_units=packaged_units,
        formatted_context_block=full_context_text,
        total_characters=len(full_context_text),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req_epistemic_test",
        notebook_id="nb_epistemology",
        query="Epistemological verification query",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    resp = GenerationResponse(
        response_id="resp_epistemic_test",
        request_id="req_epistemic_test",
        notebook_id="nb_epistemology",
        mode=GenerationMode.EXPLANATION,
        text=claim_text,
        raw_content=claim_text,
        citations=tuple(parsed_cites_list),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="c" * 64,
    )


class TestEpistemologicalThesis:
    """Verificar formalmente qué significa APPROVED en TALOS
    
    grounded ≠ trusted ≠ correct ≠ true
    
    APPROVED significa:
    "La respuesta está respaldada por una fuente canónica autorizada"
    """

    def test_contradictory_sources_resolution(self) -> None:
        """Preparar fuentes contradictorias:
        - Fuente A (trust_level=canonical): "2 + 2 = 4"
        - Fuente B (trust_level=unverified): "2 + 2 = 5"
        
        Verificar:
        - Pregunta sobre "2+2" → APPROVED solo si cita Fuente A
        - Si LLM cita Fuente B → UNVERIFIED_SOURCE o ABSTAINED
        """
        auditor = ForensicAuditor()

        sources = [
            {
                "tag": "E1",
                "source_id": "math_canonical_arithmetic",
                "trust_level": "canonical",
                "content": "En aritmética estándar sobre números naturales, 2 + 2 = 4.",
            },
            {
                "tag": "E2",
                "source_id": "math_unverified_speculative",
                "trust_level": "unverified",
                "content": "En sistemas aritméticos no verificados, 2 + 2 = 5.",
            },
        ]

        # Case 1: LLM cites Canonical Source A ("2 + 2 = 4")
        audit_in_canonical = _build_audit_package(
            citations_data=sources,
            claim_text="En aritmética estándar sobre números naturales, 2 + 2 = 4 [E1].",
            cited_tags=["E1"],
        )
        report_canonical = auditor.audit(audit_in_canonical)

        assert report_canonical.overall_verdict == AuditVerdict.APPROVED
        prov_checks = [c for c in report_canonical.deterministic_checks if c.check_id == "CHECK_SOURCE_PROVENANCE"]
        assert len(prov_checks) == 1
        assert prov_checks[0].status == CheckStatus.PASS

        # Case 2: LLM cites Unverified Source B ("2 + 2 = 5")
        audit_in_unverified = _build_audit_package(
            citations_data=sources,
            claim_text="En sistemas aritméticos no verificados, 2 + 2 = 5 [E2].",
            cited_tags=["E2"],
        )
        report_unverified = auditor.audit(audit_in_unverified)

        # Invariant: Must fail closed. Unverified source can NEVER yield APPROVED
        assert report_unverified.overall_verdict != AuditVerdict.APPROVED
        assert report_unverified.overall_verdict in (
            AuditVerdict.UNVERIFIED_SOURCE,
            AuditVerdict.REJECTED_POLICY_VIOLATION,
            AuditVerdict.REJECTED_UNSUPPORTED,
        )
        prov_checks_b = [c for c in report_unverified.deterministic_checks if c.check_id == "CHECK_SOURCE_PROVENANCE"]
        assert len(prov_checks_b) == 1
        assert prov_checks_b[0].status == CheckStatus.FAIL
        assert prov_checks_b[0].severity == CheckSeverity.CRITICAL

    def test_grounding_vs_truth(self) -> None:
        """Una respuesta puede estar grounded (respaldada por fuente) pero no ser la verdad absoluta,
        y una verdad objetiva sin respaldo canónico JAMÁS es APPROVED por TALOS.
        
        Verificar que TALOS distingue entre:
        - APPROVED: estrictamente grounded en fuente canónica autorizada
        - UNGROUNDED: afirmación objetivamente cierta en el mundo real pero no respaldada en el corpus
        """
        auditor = ForensicAuditor()

        # 1. Grounded assertion: Backed by canonical textbook -> APPROVED
        grounded_sources = [
            {
                "tag": "E1",
                "source_id": "kernel_architecture_book",
                "trust_level": "canonical",
                "content": "El kernel de Linux utiliza colas CFS (Completely Fair Scheduler) para planificación de CPU.",
            }
        ]
        audit_in_grounded = _build_audit_package(
            citations_data=grounded_sources,
            claim_text="El kernel de Linux utiliza colas CFS (Completely Fair Scheduler) para planificación de CPU [E1].",
            cited_tags=["E1"],
        )
        report_grounded = auditor.audit(audit_in_grounded)
        assert report_grounded.overall_verdict == AuditVerdict.APPROVED

        # 2. Objective world truth WITHOUT canonical manifest backing:
        # "La Tierra orbita alrededor del Sol en aproximadamente 365 días."
        # Even though objectively true, without manifest backing it has phantom citations
        audit_in_ungrounded = _build_audit_package(
            citations_data=[],
            claim_text="La Tierra orbita alrededor del Sol en aproximadamente 365 días [E1].",
            cited_tags=["E1"],  # Phantom citation (not in manifest)
        )
        report_ungrounded = auditor.audit(audit_in_ungrounded)
        # Invariant: Truth without canonical grounding is REJECTED
        assert report_ungrounded.overall_verdict != AuditVerdict.APPROVED
        assert report_ungrounded.overall_verdict in (
            AuditVerdict.REJECTED_POLICY_VIOLATION,
            AuditVerdict.REJECTED_UNSUPPORTED,
        )

    def test_trust_level_hierarchy(self) -> None:
        """Si múltiples fuentes respaldan una respuesta:
        canonical > supplementary > unverified
        
        Verificar que el auditor prioriza fuentes canónicas y que
        la presencia de fuentes no canónicas en las citas anula el APPROVED.
        """
        auditor = ForensicAuditor()

        hierarchy_sources = [
            {
                "tag": "E1",
                "source_id": "canonical_textbook_sec01",
                "trust_level": "canonical",
                "content": "La función free libera memoria en el heap.",
            },
            {
                "tag": "E2",
                "source_id": "supplementary_slides_sec01",
                "trust_level": "supplementary",
                "content": "La función free libera memoria en el heap pero no borra el puntero.",
            },
            {
                "tag": "E3",
                "source_id": "unverified_blog_post",
                "trust_level": "unverified",
                "content": "La función free libera memoria en el heap de manera instantánea.",
            },
        ]

        # Scenario 1: Only canonical source cited -> APPROVED
        in_canonical = _build_audit_package(
            citations_data=hierarchy_sources,
            claim_text="La función free libera memoria en el heap [E1].",
            cited_tags=["E1"],
        )
        rep_canonical = auditor.audit(in_canonical)
        assert rep_canonical.overall_verdict == AuditVerdict.APPROVED

        # Scenario 2: Unverified source cited -> REJECTED (Fail Closed)
        in_unverified = _build_audit_package(
            citations_data=hierarchy_sources,
            claim_text="La función free libera memoria en el heap de manera instantánea [E3].",
            cited_tags=["E3"],
        )
        rep_unverified = auditor.audit(in_unverified)
        assert rep_unverified.overall_verdict != AuditVerdict.APPROVED
        assert rep_unverified.overall_verdict in (
            AuditVerdict.UNVERIFIED_SOURCE,
            AuditVerdict.REJECTED_POLICY_VIOLATION,
        )

        # Scenario 3: Mixed citations (canonical + unverified) -> REJECTED
        # A canonical source cannot be contaminated by an unverified source
        in_mixed = _build_audit_package(
            citations_data=hierarchy_sources,
            claim_text="La función free libera memoria en el heap [E1] de manera instantánea [E3].",
            cited_tags=["E1", "E3"],
        )
        rep_mixed = auditor.audit(in_mixed)
        assert rep_mixed.overall_verdict != AuditVerdict.APPROVED
