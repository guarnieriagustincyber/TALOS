"""Unit tests for MockGenerator in Subsystem S4.2."""

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
)
from study_engine.contracts.generation import GenerationRequest
from study_engine.generation.mock import MockGenerator


def _build_context(
    manifest_records: dict, abstention: bool = False
) -> PackagedContext:
    """Helper to build PackagedContext."""

    packet = EvidencePacket(
        original_query="What is a thread?",
        normalized_query="What is a thread?",
        notebook_id="fadena-so",
        grounding_decision=(
            GroundingDecision.NO_CANDIDATES
            if abstention
            else GroundingDecision.UNASSESSED_EVIDENCE
        ),
        abstention_required=abstention,
    )
    manifest = CitationManifest(records=manifest_records)
    return PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        formatted_context_block="Context block",
        total_characters=13,
        epistemic_policy="Mandatory policy",
    )


def test_mock_generator_abstention_auto_generation():
    """MockGenerator auto-generates abstention message when required."""
    gen = MockGenerator()
    ctx = _build_context({}, abstention=True)
    req = GenerationRequest(
        request_id="req-ab",
        notebook_id="fadena-so",
        query="Tema inexistente",
        packaged_context=ctx,
    )
    res = gen.generate(req)
    assert "No puedo responder" in res.raw_content
    assert res.tokens_used is not None
    assert res.tokens_used.prompt_tokens == 120


def test_mock_generator_manifest_citation_auto_generation():
    """MockGenerator cites first manifest entry when available."""
    gen = MockGenerator()
    r1 = CitationRecord(
        citation_id="E1",
        chunk_id="so:1",
        document_id="d1",
        source_id="tanenbaum-so",
        source_title="SO",
        content_hash="c" * 64,
    )
    ctx = _build_context({"E1": r1}, abstention=False)
    req = GenerationRequest(
        request_id="req-cite",
        notebook_id="fadena-so",
        query="Tema con cita",
        packaged_context=ctx,
    )
    res = gen.generate(req)
    assert "[E1]" in res.raw_content


def test_mock_generator_empty_manifest_auto_generation():
    """MockGenerator handles empty manifest gracefully."""
    gen = MockGenerator()
    ctx = _build_context({}, abstention=False)
    req = GenerationRequest(
        request_id="req-empty",
        notebook_id="fadena-so",
        query="Tema sin cita",
        packaged_context=ctx,
    )
    res = gen.generate(req)
    assert "Explicación general" in res.raw_content
