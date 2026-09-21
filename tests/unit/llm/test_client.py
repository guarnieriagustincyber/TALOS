"""Unit tests for LLMClient and StructuredTutor in Subsystem S4.3."""

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    RawGenerationResult,
    ResponseValidationStatus,
)
from study_engine.generation.parser import GenerationOutputParser
from study_engine.generation.tutor import StructuredTutor
from study_engine.llm.backends import MockBackend, RuleBasedBackend
from study_engine.llm.client import LLMClient


def _make_context() -> PackagedContext:
    """Helper to build minimal valid PackagedContext."""
    packet = EvidencePacket(
        original_query="Explica procesos",
        normalized_query="Explica procesos",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
    )
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="so:proc:1",
        document_id="d1",
        source_id="tanenbaum-so",
        source_title="SO",
        content_hash="a" * 64,
        grade=EvidenceGrade.DIRECT,
    )
    manifest = CitationManifest(records={"E1": rec})
    return PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        formatted_context_block="[E1] Fuente: SO",
        total_characters=15,
        epistemic_policy="Mandatory policy",
    )


def test_llm_client_delegates_to_mock_backend():
    """Verify LLMClient returns valid RawGenerationResult from MockBackend."""
    ctx = _make_context()
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="¿Qué es un proceso?",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    backend = MockBackend(canned_text="Un proceso es memoria activa [E1].")
    client = LLMClient(backend=backend)

    res = client.generate(req)

    assert isinstance(res, RawGenerationResult)
    assert res.raw_content == "Un proceso es memoria activa [E1]."
    assert res.model == "mock-llm-v1"
    assert res.latency_ms >= 0.0


def test_llm_client_with_rule_based_backend():
    """Verify LLMClient works deterministically with RuleBasedBackend."""
    ctx = _make_context()
    req = GenerationRequest(
        request_id="req-2",
        notebook_id="fadena-so",
        query="Explica hilos",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    backend = RuleBasedBackend()
    client = LLMClient(backend=backend)

    res = client.generate(req)

    assert isinstance(res, RawGenerationResult)
    assert "[E1]" in res.raw_content
    assert res.model == "rule-based-v1"


def test_structured_tutor_answer_delegation():
    """Verify HG-S4.3-06: Tutor produces validated GenerationResponse."""
    ctx = _make_context()
    req = GenerationRequest(
        request_id="req-3",
        notebook_id="fadena-so",
        query="Explica procesos",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    backend = MockBackend(
        canned_text="Un proceso es un programa en ejecucion [E1]."
    )
    client = LLMClient(backend=backend)
    tutor = StructuredTutor(generator=client)

    resp = tutor.answer(req, response_id="resp-cert")

    assert isinstance(resp, GenerationResponse)

    assert resp.response_id == "resp-cert"
    assert resp.request_id == "req-3"
    assert resp.notebook_id == "fadena-so"
    assert resp.validation_status == ResponseValidationStatus.VALID
    assert len(resp.citations) == 1
    assert resp.citations[0].citation_id == "E1"
    assert resp.citations[0].in_manifest is True


def test_structured_tutor_properties():
    """Verify generator and parser properties on StructuredTutor."""
    backend = MockBackend()
    client = LLMClient(backend=backend)
    parser = GenerationOutputParser()
    tutor = StructuredTutor(generator=client, parser=parser)

    assert tutor.generator is client
    assert tutor.parser is parser


def test_llm_client_properties():
    """Verify backend and assembler properties on LLMClient."""
    backend = MockBackend()
    client = LLMClient(backend=backend)
    assert client.backend is backend
    assert client.assembler is not None
