"""Unit tests for PolicyGuard in Subsystem S4.4."""

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
    ParsedCitation,
    ResponseValidationStatus,
)
from study_engine.audit.contracts import (
    CheckSeverity,
    CheckStatus,
    ForensicAuditInput,
)
from study_engine.audit.policy_guard import PolicyGuard


def _build_policy_input(
    abstention_required: bool = False,
    is_abstention: bool = False,
    citations: tuple = (),
    mode: GenerationMode = GenerationMode.EXPLANATION,
    text: str = "Respuesta ordinaria sin violaciones.",
) -> ForensicAuditInput:
    manifest = CitationManifest(records={})
    decision = (
        GroundingDecision.NO_CANDIDATES
        if abstention_required
        else GroundingDecision.SUPPORTED
    )
    packet = EvidencePacket(
        original_query="query",
        normalized_query="query",
        notebook_id="fadena-so",
        grounding_decision=decision,
        abstention_required=abstention_required,
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
        mode=mode,
    )
    resp = GenerationResponse(
        response_id="resp-1",
        request_id="req-1",
        notebook_id="fadena-so",
        mode=mode,
        text=text,
        raw_content=text,
        citations=citations,
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=is_abstention,
        grounding_decision=packet.grounding_decision,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="a" * 64,
    )


def test_policy_guard_abstention_respected():
    """Verify compliant abstention passes mandatory abstention check."""
    audit_input = _build_policy_input(
        abstention_required=True,
        is_abstention=True,
        text="No puedo responder con la evidencia provista.",
    )
    guard = PolicyGuard()
    checks = guard.verify(audit_input)

    abst_check = next(
        c for c in checks if c.check_id == "CHECK_MANDATORY_ABSTENTION"
    )
    assert abst_check.status == CheckStatus.PASS
    assert abst_check.severity == CheckSeverity.CRITICAL


def test_policy_guard_abstention_violation_with_citations():
    """Verify citations during mandatory abstention trigger FAIL."""
    cite = ParsedCitation(citation_id="E1", in_manifest=False)
    audit_input = _build_policy_input(
        abstention_required=True,
        is_abstention=False,
        citations=(cite,),
        text="Respuesta inventada [E1].",
    )
    guard = PolicyGuard()
    checks = guard.verify(audit_input)

    abst_check = next(
        c for c in checks if c.check_id == "CHECK_MANDATORY_ABSTENTION"
    )
    assert abst_check.status == CheckStatus.FAIL
    assert abst_check.severity == CheckSeverity.CRITICAL
    assert "Response generated 1 citations" in abst_check.reason


def test_policy_guard_p7_mastery_mutation_detected():
    """Verify simulated student promotion or mastery mutation triggers FAIL."""
    audit_input = _build_policy_input(
        mode=GenerationMode.EVALUATION,
        text=(
            "Excelente respuesta. Has aprobado el tema y avanzas "
            "al siguiente módulo."
        ),
    )
    guard = PolicyGuard()
    checks = guard.verify(audit_input)

    p7_check = next(
        c for c in checks if c.check_id == "CHECK_P7_MASTERY_MUTATION"
    )
    assert p7_check.status == CheckStatus.FAIL
    assert p7_check.severity == CheckSeverity.CRITICAL
    assert "Principio P7 violated" in p7_check.reason


def test_policy_guard_socratic_structural_shape():
    """Verify socratic responses without questions trigger WARNING."""
    audit_input = _build_policy_input(
        mode=GenerationMode.SOCRATIC_TUTOR,
        text=(
            "Un proceso es una instancia de un programa en ejecución. "
            "Consta de espacio de direcciones, registros de CPU, "
            "contador de programa y archivos abiertos en el SO."
        ),
    )

    guard = PolicyGuard()
    checks = guard.verify(audit_input)

    soc_check = next(
        c for c in checks if c.check_id == "CHECK_SOCRATIC_STRUCTURAL_SHAPE"
    )
    assert soc_check.status == CheckStatus.FAIL
    assert soc_check.severity == CheckSeverity.WARNING
