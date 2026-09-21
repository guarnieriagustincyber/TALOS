"""Contract tests for Subsystem S4.4 Forensic Auditor."""

import pytest
from pydantic import ValidationError

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
    CheckSeverity,
    CheckStatus,
    ClaimSupportVerdict,
    ClaimType,
    ClaimVerification,
    DeterministicAuditCheck,
    ForensicAuditInput,
    ForensicAuditReport,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)
from study_engine.audit.nli import (
    BaseNLIJudge,
    MockNLIJudge,
    NLIInferenceResult,
)


def _make_dummy_audit_input() -> ForensicAuditInput:
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-1",
        document_id="doc-1",
        source_id="src-1",
        source_title="Tanenbaum SO",
        content_hash="a" * 64,
    )
    unit = PackagedEvidenceUnit(
        citation=rec,
        content="Los procesos en estado zombie ocupan una entrada en el PCB.",
        retrieval_score=0.9,
        retrieval_rank=1,
        retrieval_method="hybrid",
    )
    manifest = CitationManifest(records={"E1": rec})
    packet = EvidencePacket(
        original_query="¿Qué es un zombie?",
        normalized_query="que es un zombie",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block="[E1] Los procesos en estado zombie...",
        total_characters=100,
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-101",
        notebook_id="fadena-so",
        query="¿Qué es un zombie?",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )

    parsed_cite = ParsedCitation(
        citation_id="E1",
        in_manifest=True,
        chunk_id="chk-1",
        source_id="src-1",
    )
    resp = GenerationResponse(
        response_id="resp-101",
        request_id="req-101",
        notebook_id="fadena-so",
        mode=GenerationMode.EXPLANATION,
        text="Un proceso zombie ocupa entrada en el PCB [E1].",
        raw_content="Un proceso zombie ocupa entrada en el PCB [E1].",
        citations=(parsed_cite,),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="b" * 64,
    )


def test_audit_contracts_immutability():

    """Verify contracts are strictly frozen against in-place mutations."""
    diag = LexicalDiagnostics(
        status=LexicalAnomalyStatus.NO_ANOMALY,
        token_overlap_ratio=0.85,
    )
    with pytest.raises(ValidationError):
        diag.token_overlap_ratio = 0.9  # type: ignore[misc]

    check = DeterministicAuditCheck(
        check_id="CHECK_1",
        status=CheckStatus.PASS,
        severity=CheckSeverity.CRITICAL,
        reason="Success",
    )
    with pytest.raises(ValidationError):
        check.status = CheckStatus.FAIL  # type: ignore[misc]

    cv = ClaimVerification(
        claim_index=0,
        claim_text="Texto",
        claim_type=ClaimType.FACTUAL,
        cited_tags=("E1",),
        lexical_diagnostics=diag,
        nli_verdict=ClaimSupportVerdict.ENTAILED,
    )
    with pytest.raises(ValidationError):
        cv.nli_verdict = ClaimSupportVerdict.CONTRADICTED  # type: ignore[misc]

    audit_input = _make_dummy_audit_input()
    with pytest.raises(ValidationError):
        audit_input.prompt_hash = "c" * 64  # type: ignore[misc]


def test_prompt_hash_validation():
    """Verify prompt_hash must be exactly 64 hex characters or None."""
    audit_input = _make_dummy_audit_input()
    assert audit_input.prompt_hash == "b" * 64

    # Invalid prompt hash length raises ValidationError
    with pytest.raises(ValidationError):
        ForensicAuditInput(
            request=audit_input.request,
            response=audit_input.response,
            prompt_hash="too_short",
        )


def test_mock_nli_conforms_to_protocol():
    """Verify MockNLIJudge conforms to BaseNLIJudge runtime protocol."""
    judge = MockNLIJudge()
    assert isinstance(judge, BaseNLIJudge)
    assert judge.judge_id == "mock-nli-v1"

    res = judge.evaluate_claim(premise="P", hypothesis="H")
    assert isinstance(res, NLIInferenceResult)
    assert res.verdict == ClaimSupportVerdict.ENTAILED


def test_closed_enums():
    """Verify all audit enums define expected closed members."""
    assert set(AuditVerdict) == {
        AuditVerdict.APPROVED,
        AuditVerdict.FLAGGED_UNASSESSED,
        AuditVerdict.UNVERIFIED_SOURCE,
        AuditVerdict.REJECTED_UNSUPPORTED,
        AuditVerdict.REJECTED_CONTRADICTION,
        AuditVerdict.REJECTED_ABSTENTION_VIOLATION,
        AuditVerdict.REJECTED_INJECTION_DETECTED,
        AuditVerdict.REJECTED_POLICY_VIOLATION,
        AuditVerdict.REJECTED_INPUT_MISMATCH,
    }
    assert set(CheckStatus) == {
        CheckStatus.PASS,
        CheckStatus.FAIL,
        CheckStatus.INCONCLUSIVE,
    }
    assert set(CheckSeverity) == {
        CheckSeverity.CRITICAL,
        CheckSeverity.WARNING,
        CheckSeverity.INFORMATIONAL,
    }
    assert set(ClaimType) == {
        ClaimType.FACTUAL,
        ClaimType.PEDAGOGICAL,
        ClaimType.QUESTION,
        ClaimType.CONVERSATIONAL,
        ClaimType.UNCLASSIFIED,
    }
    assert set(ClaimSupportVerdict) == {
        ClaimSupportVerdict.ENTAILED,
        ClaimSupportVerdict.CONTRADICTED,
        ClaimSupportVerdict.NOT_ENTAILED,
        ClaimSupportVerdict.UNASSESSED,
    }


def test_forensic_audit_report_immutability():
    """Verify ForensicAuditReport is frozen and validates constraints."""
    rep = ForensicAuditReport(
        audit_id="audit_123",
        request_id="req_101",
        notebook_id="fadena-so",
        overall_verdict=AuditVerdict.APPROVED,
        audit_latency_ms=12.5,
        auditor_backend="forensic-v1",
    )
    assert rep.overall_verdict == AuditVerdict.APPROVED
    assert rep.nli_executed is False

    with pytest.raises(ValidationError):
        rep.overall_verdict = (  # type: ignore[misc]
            AuditVerdict.REJECTED_UNSUPPORTED
        )
