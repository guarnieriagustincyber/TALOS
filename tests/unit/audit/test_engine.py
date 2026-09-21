"""Unit tests for DeterministicAuditEngine in Subsystem S4.4."""

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
    CheckStatus,
    ForensicAuditInput,
    LexicalAnomalyStatus,
)
from study_engine.audit.engine import DeterministicAuditEngine


def _make_engine_input(
    text: str = "Round Robin asigna quantum de CPU [E1].",
    citation_tags: tuple = ("E1",),
    abstention_required: bool = False,
    is_abstention: bool = False,
) -> ForensicAuditInput:
    import hashlib

    content = "Round Robin asigna quantum fijo de CPU a cada proceso."
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
        abstention_required=abstention_required,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block="[E1] Round Robin asigna quantum...",
        total_characters=50,
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
        request_id="req-1",
        notebook_id="fadena-so",
        mode=GenerationMode.EXPLANATION,
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
        prompt_hash="e" * 64,
    )


def test_deterministic_engine_clean_pass():
    """Verify fully compliant input passes all Layer 1 checks."""
    audit_input = _make_engine_input()
    engine = DeterministicAuditEngine()
    result = engine.evaluate(audit_input)

    assert not result.has_critical_failure
    assert result.early_verdict is None
    assert len(result.claims) == 1
    assert result.claims[0].cited_tags == ("E1",)
    diag = result.lexical_diagnostics[0]
    assert diag.status == LexicalAnomalyStatus.NO_ANOMALY


def test_deterministic_engine_factual_without_citation_fails():
    """Verify factual claims lacking citations trigger rejection."""
    # Sentence has factual content but 0 citations in non-abstention response

    audit_input = _make_engine_input(
        text="Round Robin es un algoritmo de planificación de procesos.",
        citation_tags=(),
    )
    engine = DeterministicAuditEngine()
    result = engine.evaluate(audit_input)

    assert result.has_critical_failure
    assert result.early_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    grounding_check = next(
        c for c in result.checks if c.check_id == "CHECK_FACTUAL_GROUNDING"
    )
    assert grounding_check.status == CheckStatus.FAIL
