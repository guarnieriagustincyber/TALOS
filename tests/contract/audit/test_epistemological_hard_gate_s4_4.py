"""Epistemological Hard Gate contract tests for S4.4 (Forensic Auditor).

Enforces the Sovereign NLI Decision Machine:
1. CONTRADICTION -> REJECTED_CONTRADICTION
2. UNKNOWN       -> FLAGGED_UNASSESSED
3. ERROR         -> FLAGGED_UNASSESSED (Fail-Closed: Failure is NOT approval)
4. NOT_ENTAILED  -> REJECTED_UNSUPPORTED
5. ENTAILMENT    -> Continues audit (Layer 1 must also pass)
"""

import hashlib
from typing import cast

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
    DeterministicAuditCheck,
    ForensicAuditInput,
)
from study_engine.audit.engine import (
    DeterministicAuditEngine,
    DeterministicEngineResult,
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.nli import MockNLIJudge


def _make_audit_input(
    response_text: str = "Round Robin asigna quantum fijo [E1].",
    evidence_content: str = "Round Robin asigna quantum fijo a los procesos.",
) -> ForensicAuditInput:
    content_hash = hashlib.sha256(evidence_content.encode("utf-8")).hexdigest()

    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-punteros-01",
        document_id="doc-punteros",
        source_id="src-punteros",
        source_title="Introducción a C",
        content_hash=content_hash,
    )
    unit = PackagedEvidenceUnit(
        citation=rec,
        content=evidence_content,
        retrieval_score=0.95,
        retrieval_rank=1,
        retrieval_method="hybrid_rrf",
    )
    manifest = CitationManifest(records={"E1": rec})
    packet = EvidencePacket(
        original_query="¿Cómo funciona?",
        normalized_query="¿Cómo funciona?",
        notebook_id="fadena-prog",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block=f"[E1] {evidence_content}",
        total_characters=len(evidence_content),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-gate-44",
        notebook_id="fadena-prog",
        query="¿Cómo funciona?",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    parsed_cites = (
        ParsedCitation(citation_id="E1", in_manifest=True),
    )
    resp = GenerationResponse(
        response_id="resp-gate-44",
        request_id="req-gate-44",
        notebook_id="fadena-prog",
        mode=GenerationMode.EXPLANATION,
        text=response_text,
        raw_content=response_text,
        citations=parsed_cites,
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="a" * 64,
    )


# ---------------------------------------------------------------------------
# Branch 1: CONTRADICTION -> REJECTED_CONTRADICTION
# ---------------------------------------------------------------------------


def test_hard_gate_s4_4_contradiction_yields_rejected_contradiction() -> None:
    """HG-S4.4: Contradiction MUST yield REJECTED_CONTRADICTION."""
    audit_input = _make_audit_input()
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.CONTRADICTED)
    auditor = ForensicAuditor(nli_judge=judge)

    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_CONTRADICTION
    assert report.nli_executed is True
    assert any(
        cv.nli_verdict == ClaimSupportVerdict.CONTRADICTED
        for cv in report.claim_verifications
    )


# ---------------------------------------------------------------------------
# Branch 2: UNKNOWN -> FLAGGED_UNASSESSED
# ---------------------------------------------------------------------------


def test_hard_gate_s4_4_unknown_yields_flagged_unassessed() -> None:
    """HG-S4.4: Unknown claim MUST yield FLAGGED_UNASSESSED."""
    audit_input = _make_audit_input()
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.UNASSESSED)
    auditor = ForensicAuditor(nli_judge=judge)

    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.nli_executed is True


# ---------------------------------------------------------------------------
# Branch 3: ERROR -> FLAGGED_UNASSESSED (Fail-Closed)
# ---------------------------------------------------------------------------


def test_hard_gate_s4_4_judge_error_yields_flagged_unassessed() -> None:
    """HG-S4.4-08: NLI Failure Is Not Approval. Judge exception -> FLAGGED."""
    audit_input = _make_audit_input()
    err = RuntimeError("LLM API Timeout")
    judge = MockNLIJudge(inject_error=err)
    auditor = ForensicAuditor(nli_judge=judge)

    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.nli_executed is True
    assert any(
        "Judge error: LLM API Timeout" in (cv.nli_rationale or "")
        for cv in report.claim_verifications
    )


# ---------------------------------------------------------------------------
# Branch 4: NOT_ENTAILED (Neutral / Unsupported) -> REJECTED_UNSUPPORTED
# ---------------------------------------------------------------------------


def test_hard_gate_s4_4_not_entailed_yields_rejected_unsupported() -> None:
    """HG-S4.4: Unentailed/neutral claim MUST yield REJECTED_UNSUPPORTED."""
    audit_input = _make_audit_input()
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.NOT_ENTAILED)
    auditor = ForensicAuditor(nli_judge=judge)

    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert report.nli_executed is True


# ---------------------------------------------------------------------------
# Branch 5: ENTAILMENT != Automatic Approval (Layer 1 Precedence)
# ---------------------------------------------------------------------------


class _MockEngineWithNonCriticalFailure:
    """Mock deterministic engine injecting a non-critical Layer 1 failure."""

    def evaluate(
        self, audit_input: ForensicAuditInput
    ) -> DeterministicEngineResult:
        from study_engine.audit.claim_extractor import ExtractedClaim
        from study_engine.audit.contracts import ClaimType

        return DeterministicEngineResult(
            has_critical_failure=False,
            early_verdict=AuditVerdict.REJECTED_POLICY_VIOLATION,
            checks=(
                DeterministicAuditCheck(
                    check_id="CHECK_POLICY_COMPLIANCE",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.WARNING,
                    reason="Non-critical policy violation detected in Layer 1",
                ),
            ),
            claims=(
                ExtractedClaim(
                    claim_index=0,
                    claim_text="Claim text.",
                    claim_type=ClaimType.FACTUAL,
                    cited_tags=("E1",),
                ),
            ),
            lexical_diagnostics={},
        )


def test_hard_gate_s4_4_entailment_blocked_by_layer1_failure() -> None:
    """INVARIANT: ENTAILMENT alone never yields APPROVED on Layer 1 fail."""
    audit_input = _make_audit_input()
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.ENTAILED)
    mock_engine = _MockEngineWithNonCriticalFailure()
    engine = cast(DeterministicAuditEngine, mock_engine)
    auditor = ForensicAuditor(engine=engine, nli_judge=judge)

    report = auditor.audit(audit_input)

    # Even though all claims were ENTAILED, Layer 1 failure blocks APPROVED
    assert report.overall_verdict != AuditVerdict.APPROVED
    assert report.overall_verdict == AuditVerdict.REJECTED_POLICY_VIOLATION


def test_hard_gate_s4_4_clean_entailment_and_layer1_pass_approved() -> None:
    """INVARIANT: APPROVED requires Layer 1 pass AND NLI entailment."""
    audit_input = _make_audit_input()
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.ENTAILED)
    auditor = ForensicAuditor(nli_judge=judge)

    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.nli_executed is True
