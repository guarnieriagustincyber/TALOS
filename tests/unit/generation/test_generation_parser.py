"""Unit tests for GenerationOutputParser in Subsystem S4.2."""

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
)
from study_engine.contracts.generation import (
    AbstentionOrigin,
    AbstentionType,
    GenerationMode,
    GenerationRequest,
    RawGenerationResult,
    ResponseValidationStatus,
)
from study_engine.generation.parser import GenerationOutputParser


def _make_context(manifest_records: dict) -> PackagedContext:
    """Helper to build test PackagedContext with specific manifest."""
    packet = EvidencePacket(
        original_query="What is a thread?",
        normalized_query="What is a thread?",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
    )
    manifest = CitationManifest(records=manifest_records)
    return PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        formatted_context_block="Context block",
        total_characters=13,
        epistemic_policy="Mandatory policy",
    )


def test_lexical_citation_extraction_without_normalization():
    """Lexical regex extracts tags in first-seen order (no normalization)."""
    text = (
        "En [E1] se define el hilo. Más tarde [E01] y [E2] complementan [E1]."
    )

    cites = GenerationOutputParser.extract_citations(text)
    # E01 is extracted verbatim, not coerced into E1!
    assert cites == ("E1", "E01", "E2")


def test_lexical_multi_citation_bracket_extraction():
    """Verify comma-separated citations in single brackets are extracted."""
    text = "Memoria dinámica [E1, E2] y referencias cruzadas [E3, E04]."
    cites = GenerationOutputParser.extract_citations(text)
    assert cites == ("E1", "E2", "E3", "E04")


def test_valid_manifest_citations_resolved():
    """Valid citations matching manifest are verified and resolved."""
    parser = GenerationOutputParser()
    r1 = CitationRecord(
        citation_id="E1",
        chunk_id="so:th:1",
        document_id="d1",
        source_id="tanenbaum-so",
        source_title="SO",
        content_hash="b" * 64,
        grade=EvidenceGrade.DIRECT,
    )
    ctx = _make_context({"E1": r1})
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="Explica hilos",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    raw = RawGenerationResult(
        raw_content="Un hilo es una unidad de ejecucion ligera [E1]."
    )

    resp = parser.parse(raw, req, response_id="resp-fixed")

    assert resp.validation_status == ResponseValidationStatus.VALID
    assert resp.phantom_citations == ()
    assert len(resp.citations) == 1
    assert resp.citations[0].citation_id == "E1"
    assert resp.citations[0].in_manifest is True
    assert resp.citations[0].chunk_id == "so:th:1"
    assert resp.citations[0].source_id == "tanenbaum-so"
    assert resp.citations[0].grade == EvidenceGrade.DIRECT


def test_phantom_citation_fail_visible():
    """Verify HG-S4.2-03: Phantom citations are marked fail-visible."""
    parser = GenerationOutputParser()
    ctx = _make_context({})  # Empty manifest
    req = GenerationRequest(
        request_id="req-phantom",
        notebook_id="fadena-so",
        query="Explica hilos",
        packaged_context=ctx,
    )
    raw = RawGenerationResult(
        raw_content="Afirmacion basada en [E99] y en [E01]."
    )

    resp = parser.parse(raw, req)

    assert (
        resp.validation_status
        == ResponseValidationStatus.INVALID_CITATION_DETECTED
    )
    assert resp.phantom_citations == ("E99", "E01")
    assert len(resp.citations) == 2
    assert resp.citations[0].in_manifest is False
    assert resp.citations[1].in_manifest is False


def test_deterministic_parser():
    """Verify HG-S4.2-07: Identical inputs produce identical outputs."""
    parser = GenerationOutputParser()
    ctx = _make_context({})
    req = GenerationRequest(
        request_id="req-det",
        notebook_id="fadena-so",
        query="Consulta determinista",
        packaged_context=ctx,
    )
    raw = RawGenerationResult(raw_content="Respuesta idéntica.")

    r1 = parser.parse(raw, req, response_id="const-id")
    r2 = parser.parse(raw, req, response_id="const-id")

    assert r1 == r2


def test_abstention_origin_evidence_policy():
    """Mandatory context abstention marks AbstentionOrigin.EVIDENCE_POLICY."""
    parser = GenerationOutputParser()
    packet = EvidencePacket(
        original_query="Tema externo",
        normalized_query="Tema externo",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.NO_CANDIDATES,
        abstention_required=True,
        abstention_reason="No se hallaron candidatos.",
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=CitationManifest(records={}),
        formatted_context_block="Aviso abstención",
        total_characters=16,
        epistemic_policy="Mandatory policy",
    )
    req = GenerationRequest(
        request_id="req-ab-pol",
        notebook_id="fadena-so",
        query="Tema externo",
        packaged_context=ctx,
    )
    raw = RawGenerationResult(raw_content="No puedo responder [E1].")

    resp = parser.parse(raw, req)

    assert resp.is_abstention is True
    assert resp.abstention_details is not None
    assert (
        resp.abstention_details.origin == AbstentionOrigin.EVIDENCE_POLICY
    )
    assert (
        resp.abstention_details.abstention_type == AbstentionType.NO_EVIDENCE
    )
    assert "No se hallaron candidatos." in resp.abstention_details.reason


def test_abstention_origin_generator():

    """Generator voluntary abstention marks AbstentionOrigin.GENERATOR."""
    parser = GenerationOutputParser()
    ctx = _make_context({})
    req = GenerationRequest(
        request_id="req-ab-gen",
        notebook_id="fadena-so",
        query="Consulta compleja",
        packaged_context=ctx,
    )
    raw = RawGenerationResult(
        raw_content="No dispongo de evidencia suficiente para responder.",
        generator_abstained=True,
    )

    resp = parser.parse(raw, req)

    assert resp.is_abstention is True
    assert resp.abstention_details is not None
    assert resp.abstention_details.origin == AbstentionOrigin.GENERATOR
    assert (
        resp.abstention_details.abstention_type
        == AbstentionType.INSUFFICIENT_CONTEXT
    )
