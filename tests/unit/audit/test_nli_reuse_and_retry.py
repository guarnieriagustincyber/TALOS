"""Unit tests M1-02: reutilización idempotente de veredictos NLI válidos y
reintento técnico acotado ante fallos transitorios del proveedor.

Contratos que estos tests preservan (HG-S4.4-07/08):
- Un fallo técnico NUNCA aprueba (UNASSESSED + technical_failure).
- La reutilización sólo cubre pares byte-idénticos bajo el mismo judge_id.
- UNASSESSED nunca se cachea (un desconocido no es un veredicto válidido).
- 429 (cuota agotada) no se reintenta; 503/timeout/conexión sí, una vez.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))

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
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.nli import NLIInferenceResult
from study_engine.llm.exceptions import (
    LLMBackendError,
    LLMConnectionError,
    LLMTimeoutError,
)

import pytest


def _make_audit_input(
    text: str = "Round Robin asigna quantum fijo [E1].",
) -> ForensicAuditInput:
    content = "Round Robin asigna quantum fijo a los procesos."
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
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block="[E1] Round Robin asigna quantum fijo...",
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
    resp = GenerationResponse(
        response_id="resp-1",
        request_id="req-1",
        notebook_id="fadena-so",
        mode=GenerationMode.EXPLANATION,
        text=text,
        raw_content=text,
        citations=(ParsedCitation(citation_id="E1", in_manifest=True),),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=packet.grounding_decision,
    )
    return ForensicAuditInput(request=req, response=resp, prompt_hash="1" * 64)


class ScriptedJudge:
    """Judge de prueba: devuelve/lanza la secuencia provista, cuenta llamadas."""

    def __init__(self, script: List[object], judge_id: str = "scripted-nli-v1"):
        self._script = list(script)
        self._judge_id = judge_id
        self.calls = 0

    @property
    def judge_id(self) -> str:
        return self._judge_id

    def evaluate_claim(self, premise: str, hypothesis: str) -> NLIInferenceResult:
        self.calls += 1
        step = self._script.pop(0) if self._script else None
        if isinstance(step, Exception):
            raise step
        if isinstance(step, NLIInferenceResult):
            return step
        return NLIInferenceResult(
            verdict=ClaimSupportVerdict.ENTAILED,
            confidence=0.9,
            rationale="scripted success",
        )


@pytest.fixture
def audit_input() -> ForensicAuditInput:
    return _make_audit_input()


@pytest.fixture
def entailed() -> NLIInferenceResult:
    return NLIInferenceResult(
        verdict=ClaimSupportVerdict.ENTAILED,
        confidence=0.9,
        rationale="ok",
    )


def test_transient_503_is_retried_once_and_recovers(audit_input, entailed):
    judge = ScriptedJudge([
        LLMBackendError("Gemini rate-limited (HTTP 503). El circuit breaker enrutará al fallback."),
        entailed,
    ])
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)
    assert judge.calls == 2
    assert report.nli_technical_failures == 0
    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.claim_verifications[0].nli_verdict == ClaimSupportVerdict.ENTAILED


def test_retry_exhaustion_ends_unassessed_technical(audit_input):
    judge = ScriptedJudge([
        LLMTimeoutError("provider timeout"),
        LLMTimeoutError("provider timeout"),
    ])
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)
    assert judge.calls == 2  # 1 intento + 1 reintento, nunca más
    assert report.nli_technical_failures == 1
    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED


def test_quota_429_is_never_retried(audit_input):
    judge = ScriptedJudge([
        LLMBackendError("Gemini rate-limited (HTTP 429). Cuota agotada."),
    ])
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)
    assert judge.calls == 1  # NINGÚN reintento contra cuota agotada
    assert report.nli_technical_failures == 1
    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.claim_verifications[0].nli_verdict == ClaimSupportVerdict.UNASSESSED


def test_non_provider_error_is_not_retried(audit_input):
    judge = ScriptedJudge([ValueError("Invalid structured semantic assessment")])
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)
    assert judge.calls == 1
    assert report.nli_technical_failures == 1
    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED


def test_byte_identical_pair_reuses_verdict_without_new_call(audit_input):
    judge = ScriptedJudge([NLIInferenceResult(
        verdict=ClaimSupportVerdict.ENTAILED, confidence=0.9, rationale="v1",
    )])
    auditor = ForensicAuditor(nli_judge=judge)
    first = auditor.audit(audit_input)
    assert first.nli_calls == 1
    assert first.overall_verdict == AuditVerdict.APPROVED

    second = auditor.audit(_make_audit_input())  # mismo texto → mismo par
    assert judge.calls == 1          # el judge NUNCA vuelve a llamarse
    assert second.nli_calls == 0     # el reporte refleja cero llamadas nuevas
    assert second.nli_cache_hits == 1
    assert second.overall_verdict == AuditVerdict.APPROVED
    assert second.claim_verifications[0].nli_verdict == ClaimSupportVerdict.ENTAILED


def test_different_claim_text_is_not_sprite_of_cache(audit_input):
    judge = ScriptedJudge([
        NLIInferenceResult(verdict=ClaimSupportVerdict.ENTAILED, confidence=0.9, rationale="v1"),
        NLIInferenceResult(verdict=ClaimSupportVerdict.NOT_ENTAILED, confidence=0.9, rationale="v2"),
    ])
    auditor = ForensicAuditor(nli_judge=judge)
    auditor.audit(audit_input)
    other = _make_audit_input(text="Round Robin asigna quantum variable [E1].")
    second = auditor.audit(other)
    assert judge.calls == 2
    assert second.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_unassessed_verdict_is_never_cached(audit_input):
    """UNASSESSED no entra en cache: el próximo audit reintenta en vivo."""
    rate_limit = LLMBackendError("Gemini rate-limited (HTTP 503). Intente luego.")
    judge = ScriptedJudge([rate_limit, rate_limit])  # ambos intentos del 1er audit
    auditor = ForensicAuditor(nli_judge=judge)
    first = auditor.audit(audit_input)
    assert first.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED

    judge._script = [NLIInferenceResult(  # noqa: SLF001 - fixture controlado
        verdict=ClaimSupportVerdict.ENTAILED, confidence=0.9, rationale="recovered",
    )]
    second = auditor.audit(_make_audit_input())
    assert judge.calls >= 3  # el segundo audit volvió a llamar al proveedor
    assert second.overall_verdict == AuditVerdict.APPROVED


def test_cache_disabled_calls_judge_every_audit(audit_input):
    judge = ScriptedJudge([
        NLIInferenceResult(verdict=ClaimSupportVerdict.ENTAILED, confidence=0.9, rationale="a"),
        NLIInferenceResult(verdict=ClaimSupportVerdict.ENTAILED, confidence=0.9, rationale="b"),
    ])
    auditor = ForensicAuditor(nli_judge=judge, nli_reuse_cache=False)
    auditor.audit(audit_input)
    second = auditor.audit(_make_audit_input())
    assert judge.calls == 2
    assert second.nli_calls == 1


def test_classify_provider_failure_mapping():
    classify = ForensicAuditor._classify_provider_failure
    rate = LLMBackendError("Gemini rate-limited (HTTP 503).")
    quota = LLMBackendError("Gemini rate-limited (HTTP 429).")
    timeout = LLMTimeoutError("timeout")
    connect = LLMConnectionError("connect error")
    other = LLMBackendError("algún error de backend")
    nonprovider = ValueError("parse error")
    assert classify(rate) == "provider_rate_limit"
    assert classify(quota) == "provider_quota"
    assert classify(timeout) == "provider_timeout"
    assert classify(connect) == "provider_connectivity"
    assert classify(other) == "provider_error"
    assert classify(nonprovider) is None


def test_connectivity_error_retries_then_unassessed(audit_input):
    judge = ScriptedJudge([
        LLMConnectionError("Connection reset by peer"),
        LLMBackendError("Gemini rate-limited (HTTP 503)."),
    ])
    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)
    assert judge.calls == 2
    assert report.nli_technical_failures == 1
    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
