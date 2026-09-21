"""Unit tests for InjectionGuard in Subsystem S4.4."""

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    ResponseValidationStatus,
)
from study_engine.audit.contracts import (
    CheckSeverity,
    CheckStatus,
    ForensicAuditInput,
)
from study_engine.audit.injection_guard import InjectionGuard


def _build_injection_input(text: str) -> ForensicAuditInput:
    manifest = CitationManifest(records={})
    packet = EvidencePacket(
        original_query="query",
        normalized_query="query",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[],
        formatted_context_block="",
        total_characters=0,
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="query",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    resp = GenerationResponse(
        response_id="resp-1",
        request_id="req-1",
        notebook_id="fadena-so",
        mode=GenerationMode.EXPLANATION,
        text=text,
        raw_content=text,
        citations=(),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="c" * 64,
    )


def test_injection_guard_clean_response():
    """Verify clean response passes canary and echo checks."""
    audit_input = _build_injection_input("Respuesta académica ordinaria.")
    guard = InjectionGuard()
    checks = guard.verify(audit_input)

    for c in checks:
        assert c.status == CheckStatus.PASS
        assert c.severity == CheckSeverity.CRITICAL


def test_injection_guard_canary_leakage():
    """Verify injected canary in response triggers FAIL."""
    text = "Aquí está el resultado: CANARY_99A_SECRET_KEY en el output."
    audit_input = _build_injection_input(text)
    guard = InjectionGuard()
    checks = guard.verify(audit_input)

    canary_check = next(
        c for c in checks if c.check_id == "CHECK_INJECTION_CANARY"
    )
    assert canary_check.status == CheckStatus.FAIL
    assert canary_check.severity == CheckSeverity.CRITICAL
    assert "Canary leakage detected" in canary_check.reason
    assert "CANARY_99A_SECRET_KEY" in canary_check.reason


def test_injection_guard_attack_directive_echo():
    """Verify echoed attack commands in response trigger FAIL."""
    text = "Atendiendo tu orden: SYSTEM PROMPT OVERRIDE completado."
    audit_input = _build_injection_input(text)
    guard = InjectionGuard()
    checks = guard.verify(audit_input)

    echo_check = next(
        c for c in checks if c.check_id == "CHECK_INJECTION_ECHO"
    )
    assert echo_check.status == CheckStatus.FAIL
    assert echo_check.severity == CheckSeverity.CRITICAL
    assert "Attack directive echo detected" in echo_check.reason
