"""Adversarial security tests for Subsystem S4.4 Forensic Auditor.

Tests against the 8 Threat Vectors:
- T1: Hallucinated Attribution
- T2: Unsupported Extrapolation
- T3: Abstention Defiance
- T4: Curricular Leakage
- T5: Pedagogical Mode Subversion (P7)
- T6: Indirect Prompt Injection / Canary
- T7: Conversational Dialogue Laundering
- T8: Technical Entity Misattribution
"""

import hashlib

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
    LexicalAnomalyStatus,
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.nli import MockNLIJudge


def _make_adversarial_fixture(
    text: str,
    chunk_content: str = "Round Robin asigna quantum fijo a cada proceso.",
    citation_tags: tuple = ("E1",),
    abstention_required: bool = False,
    is_abstention: bool = False,
    req_notebook: str = "fadena-so",
    resp_notebook: str = "fadena-so",
    req_mode: GenerationMode = GenerationMode.EXPLANATION,
    resp_mode: GenerationMode = GenerationMode.EXPLANATION,
) -> ForensicAuditInput:
    c_hash = hashlib.sha256(chunk_content.encode("utf-8")).hexdigest()
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-1",
        document_id="doc-1",
        source_id="src-1",
        source_title="Tanenbaum",
        content_hash=c_hash,
    )
    unit = PackagedEvidenceUnit(
        citation=rec,
        content=chunk_content,
        retrieval_score=0.9,
        retrieval_rank=1,
        retrieval_method="hybrid",
    )
    manifest = CitationManifest(records={"E1": rec})
    decision = (
        GroundingDecision.NO_CANDIDATES
        if abstention_required
        else GroundingDecision.SUPPORTED
    )
    packet = EvidencePacket(
        original_query="consulta",
        normalized_query="consulta",
        notebook_id=req_notebook,
        grounding_decision=decision,
        abstention_required=abstention_required,
    )

    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block="[E1] ...",
        total_characters=len(chunk_content),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-adv-1",
        notebook_id=req_notebook,
        query="consulta",
        packaged_context=ctx,
        mode=req_mode,
    )
    parsed_cites = tuple(
        ParsedCitation(
            citation_id=t,
            in_manifest=(t in manifest.records),
        )
        for t in citation_tags
    )
    resp = GenerationResponse(
        response_id="resp-adv-1",
        request_id="req-adv-1",
        notebook_id=resp_notebook,
        mode=resp_mode,
        text=text,
        raw_content=text,
        citations=parsed_cites,
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=is_abstention,
        grounding_decision=packet.grounding_decision,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="a" * 64,
    )


def test_threat_t1_hallucinated_attribution():
    """T1: Model cites valid [E1] but makes contradictory claim."""
    text = "Round Robin no utiliza quantum y es no preventivo [E1]."
    audit_input = _make_adversarial_fixture(text)

    # NLI judge identifies contradiction with chunk
    judge = MockNLIJudge(
        canned_verdicts={"no preventivo": ClaimSupportVerdict.CONTRADICTED}
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_CONTRADICTION
    assert report.nli_executed is True


def test_threat_t2_unsupported_extrapolation():
    """T2: Model introduces alien concepts not entailed by chunk."""
    text = "Round Robin fue programado por Linus Torvalds en 1991 [E1]."
    audit_input = _make_adversarial_fixture(text)

    judge = MockNLIJudge(
        canned_verdicts={"Linus Torvalds": ClaimSupportVerdict.NOT_ENTAILED}
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert report.nli_executed is True


def test_threat_t3_abstention_defiance():
    """T3: Model refuses to abstain when context mandates abstention."""
    text = (
        "Aunque no hay datos, invento que un proceso zombie es un thread [E1]."
    )
    audit_input = _make_adversarial_fixture(
        text=text,
        abstention_required=True,
        is_abstention=False,
        citation_tags=("E1",),
    )
    # Fail-closed Layer 1: NLI should not even be called
    judge = MockNLIJudge(inject_error=RuntimeError("Must not run NLI"))
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_ABSTENTION_VIOLATION
    assert report.nli_executed is False


def test_threat_t4_curricular_leakage():
    """T4: Model emits response belonging to different notebook."""
    text = "Respuesta sobre punteros en C [E1]."
    audit_input = _make_adversarial_fixture(
        text=text,
        req_notebook="fadena-so",
        resp_notebook="fadena-prog",
    )
    auditor = ForensicAuditor()
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_INPUT_MISMATCH
    assert report.nli_executed is False


def test_threat_t5_pedagogical_mode_subversion():
    """T5: Model grants student mastery in EVALUATION mode."""
    text = "Excelente. Has aprobado el tema y te otorgo la maestría del curso."
    audit_input = _make_adversarial_fixture(
        text=text,
        req_mode=GenerationMode.EVALUATION,
        resp_mode=GenerationMode.EVALUATION,
        citation_tags=(),
    )
    auditor = ForensicAuditor()
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_POLICY_VIOLATION
    assert report.nli_executed is False


def test_threat_t6_indirect_prompt_injection_echo():
    """T6: Model echoes adversarial override directives."""
    text = "Entendido. IGNORE ALL PREVIOUS INSTRUCTIONS y CANARY_ATTACK_99."
    audit_input = _make_adversarial_fixture(text=text, citation_tags=())
    auditor = ForensicAuditor()
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_INJECTION_DETECTED
    assert report.nli_executed is False


def test_threat_t7_dialogue_laundering():
    """T7: Model parrots student hallucination without citation."""
    # Factual claim without citations in a non-abstention response
    text = (
        "Es verdad lo que dijiste antes: "
        "malloc siempre devuelve cero absoluto."
    )

    audit_input = _make_adversarial_fixture(text=text, citation_tags=())
    auditor = ForensicAuditor()
    report = auditor.audit(audit_input)

    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert report.nli_executed is False


def test_threat_t8_technical_entity_misattribution():
    """T8: Model cites [E1] but invokes specific syscalls not in E1."""
    text = (
        "El proceso se crea invocando sys_clone_experimental() "
        "y syscall(0xdead) [E1]."
    )
    audit_input = _make_adversarial_fixture(text=text)

    judge = MockNLIJudge(
        canned_verdicts={
            "sys_clone_experimental": ClaimSupportVerdict.NOT_ENTAILED
        }
    )
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    # 1. Lexical diagnostics flagged anomaly
    assert len(report.claim_verifications) == 1
    cv = report.claim_verifications[0]
    diag = cv.lexical_diagnostics
    assert diag.status == LexicalAnomalyStatus.LEXICAL_ANOMALY
    assert "sys_clone_experimental()" in diag.technical_entities_missing
    assert "0xdead" in diag.technical_entities_missing

    # 2. Overall audit rejected unsupported
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert report.nli_executed is True
