"""Unit tests for ForensicAuditor in Subsystem S4.4."""

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
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
from study_engine.audit.contracts import (
    AuditVerdict,
    ClaimSupportVerdict,
    ForensicAuditInput,
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.nli import MockNLIJudge


def _make_auditor_test_input(
    text: str = "Round Robin asigna quantum fijo [E1].",
    response_mode: GenerationMode = GenerationMode.EXPLANATION,
    request_mode: GenerationMode = GenerationMode.EXPLANATION,
) -> ForensicAuditInput:
    import hashlib

    content = "Round Robin asigna quantum fijo a los procesos."
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-1",
        document_id="doc-1",
        source_id="src-1",
        source_title="Tanenbaum",
        content_hash=content_hash,
    )
    unit = PackagedEvidenceUnit(
        citation=rec,
        content=content,
        retrieval_score=0.9,
        retrieval_rank=1,
        retrieval_method="hybrid",
    )
    manifest = CitationManifest(records={"E1": rec})
    packet = EvidencePacket(
        original_query="query",
        normalized_query="query",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block="[E1] Round Robin asigna quantum fijo...",
        total_characters=50,
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="query",
        packaged_context=ctx,
        mode=request_mode,
    )
    parsed_cites = (
        ParsedCitation(citation_id="E1", in_manifest=True),
    )
    resp = GenerationResponse(
        response_id="resp-1",
        request_id="req-1",
        notebook_id="fadena-so",
        mode=response_mode,
        text=text,
        raw_content=text,
        citations=parsed_cites,
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=packet.grounding_decision,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="1" * 64,
    )


def test_forensic_auditor_end_to_end_approval():
    """Verify compliant response is APPROVED with nli_executed=True."""
    audit_input = _make_auditor_test_input()
    auditor = ForensicAuditor()
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.nli_executed is True
    assert report.nli_judge_id == "mock-nli-v1"
    assert len(report.claim_verifications) == 1
    cv0 = report.claim_verifications[0]
    assert cv0.nli_verdict == ClaimSupportVerdict.ENTAILED


def test_forensic_auditor_fail_closed_bypasses_nli():
    """Verify Layer 1 critical failure rejects without executing NLI."""
    # Mismatched mode causes CHECK_INPUT_IDENTITY critical failure
    audit_input = _make_auditor_test_input(
        response_mode=GenerationMode.SOCRATIC_TUTOR,
        request_mode=GenerationMode.EXPLANATION,
    )
    judge = MockNLIJudge(
        inject_error=RuntimeError("This should NEVER be called")
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_INPUT_MISMATCH
    assert report.nli_executed is False
    assert report.nli_judge_id is None


def test_forensic_auditor_nli_contradiction_rejected():
    """Verify NLI contradiction results in REJECTED_CONTRADICTION."""
    audit_input = _make_auditor_test_input()
    judge = MockNLIJudge(
        default_verdict=ClaimSupportVerdict.CONTRADICTED
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_CONTRADICTION
    assert report.nli_executed is True


def test_forensic_auditor_nli_unsupported_rejected():
    """Verify NLI finding of not entailed results in REJECTED_UNSUPPORTED."""
    audit_input = _make_auditor_test_input()
    judge = MockNLIJudge(
        default_verdict=ClaimSupportVerdict.NOT_ENTAILED
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert report.nli_executed is True


def test_forensic_auditor_judge_error_fails_safe():
    """Verify judge exception results in FLAGGED_UNASSESSED, not APPROVED."""
    audit_input = _make_auditor_test_input()
    judge = MockNLIJudge(
        inject_error=RuntimeError("Provider 500 error")
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.nli_executed is True
    cv0 = report.claim_verifications[0]
    assert cv0.nli_verdict == ClaimSupportVerdict.UNASSESSED
