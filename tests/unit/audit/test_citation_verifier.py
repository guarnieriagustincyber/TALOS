"""Unit tests for CitationVerifier in Subsystem S4.4."""

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
    CheckSeverity,
    CheckStatus,
    ForensicAuditInput,
)
from study_engine.audit.citation_verifier import CitationVerifier


def _build_audit_input(
    resp_request_id: str = "req-1",
    resp_notebook_id: str = "fadena-so",
    resp_mode: GenerationMode = GenerationMode.EXPLANATION,
    resp_decision: GroundingDecision = GroundingDecision.SUPPORTED,
    citation_tags: tuple = ("E1",),
    unit_content: str = "Contenido canónico del chunk.",
) -> ForensicAuditInput:
    import hashlib

    canonical_hash = hashlib.sha256(unit_content.encode("utf-8")).hexdigest()
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-1",
        document_id="doc-1",
        source_id="src-1",
        source_title="Tanenbaum",
        content_hash=canonical_hash,
    )
    unit = PackagedEvidenceUnit(
        citation=rec,
        content=unit_content,
        retrieval_score=0.88,
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
        formatted_context_block="[E1] Contenido canónico del chunk.",
        total_characters=30,
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="query",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )

    parsed_cites = tuple(
        ParsedCitation(
            citation_id=t,
            in_manifest=(t in manifest.records),
        )
        for t in citation_tags
    )
    resp = GenerationResponse(
        response_id="resp-1",
        request_id=resp_request_id,
        notebook_id=resp_notebook_id,
        mode=resp_mode,
        text="Respuesta [E1].",
        raw_content="Respuesta [E1].",
        citations=parsed_cites,
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=resp_decision,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="f" * 64,
    )


def test_citation_verifier_identity_success():
    """Verify strictly aligned request/response passes identity check."""
    audit_input = _build_audit_input()
    verifier = CitationVerifier()
    checks = verifier.verify(audit_input)

    identity_check = next(
        c for c in checks if c.check_id == "CHECK_INPUT_IDENTITY"
    )
    assert identity_check.status == CheckStatus.PASS
    assert identity_check.severity == CheckSeverity.CRITICAL


def test_citation_verifier_identity_mismatches():
    """Verify request_id, notebook_id, or mode mismatch triggers FAIL."""
    audit_input = _build_audit_input(
        resp_request_id="mismatched-req",
        resp_notebook_id="other-notebook",
        resp_mode=GenerationMode.SOCRATIC_TUTOR,
    )
    verifier = CitationVerifier()
    checks = verifier.verify(audit_input)

    identity_check = next(
        c for c in checks if c.check_id == "CHECK_INPUT_IDENTITY"
    )
    assert identity_check.status == CheckStatus.FAIL
    assert identity_check.severity == CheckSeverity.CRITICAL
    assert "request_id mismatch" in identity_check.reason
    assert "notebook mismatch" in identity_check.reason
    assert "mode mismatch" in identity_check.reason


def test_citation_verifier_phantom_citations():
    """Verify citation tags absent from manifest trigger FAIL."""
    audit_input = _build_audit_input(citation_tags=("E1", "E99"))
    verifier = CitationVerifier()
    checks = verifier.verify(audit_input)

    manifest_check = next(
        c for c in checks if c.check_id == "CHECK_MANIFEST_INTEGRITY"
    )
    assert manifest_check.status == CheckStatus.FAIL
    assert manifest_check.severity == CheckSeverity.CRITICAL
    assert "Phantom citations" in manifest_check.reason
    assert "E99" in manifest_check.reason


def test_citation_verifier_hash_tampering():
    """Verify hash mismatch between manifest record and chunk content."""
    audit_input = _build_audit_input(unit_content="Texto adulterado")
    verifier = CitationVerifier()

    unit = audit_input.request.packaged_context.packaged_units[0]
    tampered_unit = PackagedEvidenceUnit(
        citation=unit.citation,
        content="Texto completamente modificado después del hashing.",
        retrieval_score=unit.retrieval_score,
        retrieval_rank=unit.retrieval_rank,
        retrieval_method=unit.retrieval_method,
    )
    audit_input.request.packaged_context.packaged_units[0] = tampered_unit

    tampered_checks = verifier.verify(audit_input)
    tampered_manifest = next(
        c for c in tampered_checks if c.check_id == "CHECK_MANIFEST_INTEGRITY"
    )
    assert tampered_manifest.status == CheckStatus.FAIL
    assert "hash mismatch" in tampered_manifest.reason
