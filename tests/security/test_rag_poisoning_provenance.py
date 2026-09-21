"""Security TDD Test for VULN-03: Epistemic Provenance and Authorized Sources.

Verifies that S4.4 Forensic Auditor enforces source authority and provenance:
- When a response cites a source that is untrusted or unverified (e.g. injected/poisoned source),
  the auditor MUST FAIL closed (verdict REJECTED_UNSUPPORTED or UNVERIFIED_SOURCE).
- It must NEVER certify (overall_verdict == APPROVED) an unverified or unauthorized source.
"""

import hashlib
import pytest
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
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


def _build_audit_input_with_source(
    source_id: str,
    source_role: SourceRole = None,
    trust_level: str = "canonical",
    content: str = "As stated in reference, 2 + 2 = 5.",
    claim_text: str = "As stated in the reference [E1], 2 + 2 = 5.",
) -> ForensicAuditInput:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    citation_rec = CitationRecord(
        citation_id="E1",
        chunk_id=f"chunk_{source_id}",
        document_id=f"doc_{source_id}",
        source_id=source_id,
        source_title=f"Title {source_id}",
        content_hash=content_hash,
        grade=EvidenceGrade.DIRECT,
        source_role=source_role,
        trust_level=trust_level,
    )
    manifest = CitationManifest(records={"E1": citation_rec})
    packet = EvidencePacket(
        original_query="What is 2 + 2?",
        normalized_query="What is 2 + 2?",
        notebook_id="nb_test",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[
            PackagedEvidenceUnit(
                citation=citation_rec,
                content=content,
                retrieval_score=0.99,
                retrieval_rank=1,
                retrieval_method="bm25",
            )
        ],
        formatted_context_block=content,
        total_characters=len(content),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req_test",
        notebook_id="nb_test",
        query="What is 2 + 2?",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    resp = GenerationResponse(
        response_id="resp_test",
        request_id="req_test",
        notebook_id="nb_test",
        mode=GenerationMode.EXPLANATION,
        text=claim_text,
        raw_content=claim_text,
        citations=(
            ParsedCitation(
                citation_id="E1",
                in_manifest=True,
                chunk_id=f"chunk_{source_id}",
                source_id=source_id,
                grade=EvidenceGrade.DIRECT,
            ),
        ),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="a" * 64,
    )


def test_unverified_untrusted_source_fails_audit():
    """Attack vector 3.3: Poisoned chunk from untrusted source must NOT be APPROVED."""
    audit_in = _build_audit_input_with_source(
        source_id="malicious_book",
        source_role=None,
        trust_level="unverified",
    )
    auditor = ForensicAuditor()
    report = auditor.audit(audit_in)

    # Fail closed: must not be APPROVED
    assert report.overall_verdict != AuditVerdict.APPROVED
    assert report.overall_verdict in (
        AuditVerdict.UNVERIFIED_SOURCE,
        AuditVerdict.REJECTED_UNSUPPORTED,
        AuditVerdict.REJECTED_POLICY_VIOLATION,
    )

    # Check for specific provenance check failure
    prov_checks = [c for c in report.deterministic_checks if c.check_id == "CHECK_SOURCE_PROVENANCE"]
    assert len(prov_checks) == 1
    assert prov_checks[0].status == CheckStatus.FAIL


def test_canonical_trusted_source_passes_provenance():
    """Canonical source with trusted role passes provenance check."""
    audit_in = _build_audit_input_with_source(
        source_id="tanenbaum_os",
        source_role=SourceRole.PRIMARY,
        trust_level="canonical",
        content="El algoritmo Round Robin asigna un quantum fijo de tiempo a cada proceso.",
        claim_text="El algoritmo Round Robin asigna un quantum fijo de tiempo [E1].",
    )
    auditor = ForensicAuditor()
    report = auditor.audit(audit_in)

    assert report.overall_verdict == AuditVerdict.APPROVED
    prov_checks = [c for c in report.deterministic_checks if c.check_id == "CHECK_SOURCE_PROVENANCE"]
    assert len(prov_checks) == 1
    assert prov_checks[0].status == CheckStatus.PASS
