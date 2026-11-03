"""COMMIT 5 feat(stream): finish_reason observable al cierre.

- Gemini captura finish_reason de cada chunk SSE.
- CircuitBreakerBackend.stream lo propaga del backend usado.
- El pipeline loguea el finish_reason y emite evento "truncated" si es
  "length" (corte por max_tokens), sin cambiar timeouts ni max_tokens.
"""

import asyncio
from unittest.mock import MagicMock

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.audit.auditor import ForensicAuditor
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.web.routes.chat import EpistemicContextPack
from study_engine.llm.circuit_breaker import CircuitBreakerBackend
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


class _MockAuditor:
    """Mock auditor that returns APPROVED for testing."""

    def __init__(self):
        self.reports = []
        self.inputs = []

    def audit(self, audit_input):
        from uuid import uuid4
        from study_engine.audit.contracts import ForensicAuditReport, DeterministicAuditCheck, CheckStatus, CheckSeverity
        from study_engine.contracts.generation import GenerationMode, GenerationRequest, GenerationResponse, ResponseValidationStatus, ParsedCitation
        from study_engine.contracts.evidence_engine import GroundingDecision, EvidencePacket, CitationManifest, PackagedContext, PackagedEvidenceUnit
        
        # Create a minimal APPROVED report
        report = ForensicAuditReport(
            audit_id=f"audit_test_{uuid4().hex[:8]}",
            request_id=audit_input.request.request_id,
            notebook_id=audit_input.request.notebook_id,
            overall_verdict=AuditVerdict.APPROVED,
            deterministic_checks=(),
            claim_verifications=(),
            nli_executed=False,
            nli_judge_id="mock",
            prompt_hash=audit_input.prompt_hash,
            audit_latency_ms=1.0,
            auditor_backend="mock",
        )
        self.reports.append(report)
        self.inputs.append(audit_input)
        return report


from study_engine.audit.contracts import AuditVerdict
from study_engine.audit.auditor import ForensicAuditor
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.web.routes.chat import EpistemicContextPack
from study_engine.llm.circuit_breaker import CircuitBreakerBackend
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


class _StreamingBackendWithFinish:
    """Backend fake que streamea 2 tokens y fija finish_reason al cerrar (como Gemini)."""

    def __init__(self, finish_reason):
        self._finish = finish_reason
        self._last_finish_reason = None

    async def stream(self, **kwargs):
        yield "palabra-uno "
        yield "palabra-dos"
        self._last_finish_reason = self._finish


def _mk_backend(finish):
    return _StreamingBackendWithFinish(finish)


def _collect_events(pipeline, **kwargs):
    async def _run():
        return [ev async for ev in pipeline.generate_phased_response(**kwargs)]
    return asyncio.run(_run())


def _pipeline_with(backend):
    contract = PedagogicalContract(
        contract_id="c1",
        notebook_id="nb1",
        version="1",
        authoritative_sources=(),
        domain_scope=(),
        base_system_prompt="Sistema tutelar TALOS para pruebas de streaming.",
        response_phases=[
            ResponsePhase(phase_id="conceptual", max_tokens=50, phase_prompt_template="Q: {concept}"),
        ],
    )
    return StructuredResponsePipeline(contract=contract, llm_backend=backend, auditor=_MockAuditor())


def _context_pack():
    """Create a minimal valid EpistemicContextPack with evidence for testing."""
    import hashlib
    content = "Test content for streaming."
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    chunk = {
        "citation_id": "E1",
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "source_id": "src-1",
        "source_title": "Test Source",
        "chunk_text": "Test content for streaming.",
        "content_hash": content_hash,
        "trust_level": "canonical",
        "page_start": 1,
        "page_end": 1,
    }
    citation = {
        "citation_id": "E1",
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "source_id": "src-1",
        "source_title": "Test Source",
        "content_hash": content_hash,
        "trust_level": "canonical",
        "page_start": 1,
        "page_end": 1,
    }
    citations = [citation]
    return EpistemicContextPack(
        formatted_context="[E1] Test content for streaming.",
        citations=citations,
        chunks=[{
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "source_id": "src-1",
            "source_title": "Test Source",
            "chunk_text": "Test content for streaming.",
            "content_hash": content_hash,
        }],
        abstained=False,
        is_sufficient=True,
        trust_status="SUPPORTED",
    )


def test_cb_stream_propaga_finish_reason_del_backend():
    primary = _mk_backend("length")
    cb = CircuitBreakerBackend(primary, _mk_backend("stop"))
    asyncio.run(_collect_tokens(cb))
    assert cb._last_finish_reason == "length"


def _collect_tokens(cb):
    async def _run():
        return [t async for t in cb.stream(system_prompt="s", user_prompt="u", max_tokens=10)]
    return _run()


def test_pipeline_emite_truncated_cuando_finish_reason_es_length():
    backend = _mk_backend("length")
    pipeline = _pipeline_with(backend)
    events = _collect_events(
        pipeline,
        user_query="describí listas",
        context_pack=_context_pack(),
        requested_phase="conceptual",
    )
    kinds = [e.event_type for e in events]
    assert "truncated" in kinds


def test_pipeline_no_emite_truncated_con_stop():
    backend = _mk_backend("stop")
    pipeline = _pipeline_with(backend)
    events = _collect_events(
        pipeline,
        user_query="describí listas",
        context_pack=_context_pack(),
        requested_phase="conceptual",
    )
    kinds = [e.event_type for e in events]
    assert "truncated" not in kinds
    assert "phase_complete" in kinds
