"""Focal F3 tests: exact-input cache, bounded concurrency and audit budget.

These tests verify that latency optimisations never turn an unassessed claim
into an approval.  The fake judge is synchronous and intentionally slow so the
concurrency and budget behaviour can be observed without a provider.
"""

import hashlib
import time

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


class _SlowJudge:
    judge_id = "slow-fake-nli-v1"

    def __init__(self, delay: float = 0.2, verdict=ClaimSupportVerdict.ENTAILED):
        self.delay = delay
        self.verdict = verdict
        self.calls = []

    def evaluate_claim(self, premise: str, hypothesis: str) -> NLIInferenceResult:
        self.calls.append((premise, hypothesis))
        time.sleep(self.delay)
        return NLIInferenceResult(
            verdict=self.verdict, confidence=0.9, rationale="fake"
        )


class _RaisingJudge:
    judge_id = "raising-fake-nli-v1"

    def __init__(self, error: Exception):
        self.error = error

    def evaluate_claim(self, premise: str, hypothesis: str) -> NLIInferenceResult:
        raise self.error


def _make_input(text: str, tags=("E1",), declared_tags=None):
    declared_tags = tuple(tags) if declared_tags is None else tuple(declared_tags)

    records = {}
    units = []
    for tag in tags:
        content = f"Evidencia exacta y verificable para {tag}."
        rec = CitationRecord(
            citation_id=tag,
            chunk_id=f"chk-{tag}",
            document_id=f"doc-{tag}",
            source_id=f"src-{tag}",
            source_title=f"Fuente {tag}",
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )
        records[tag] = rec
        units.append(
            PackagedEvidenceUnit(
                citation=rec,
                content=content,
                retrieval_score=0.9,
                retrieval_rank=1,
                retrieval_method="hybrid",
            )
        )

    packet = EvidencePacket(
        original_query="query",
        normalized_query="query",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=CitationManifest(records=records),
        packaged_units=units,
        formatted_context_block="contexto",
        total_characters=8,
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
        citations=tuple(
            ParsedCitation(citation_id=tag, in_manifest=tag in records)
            for tag in declared_tags
        ),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=packet.grounding_decision,
    )
    return ForensicAuditInput(request=req, response=resp, prompt_hash="1" * 64)


def test_identical_evidence_and_claim_uses_one_provider_call():
    text = (
        "El scheduler desaloja el proceso [E1].\n"
        "El scheduler desaloja el proceso [E1].\n"
    )
    judge = _SlowJudge(delay=0.0)
    report = ForensicAuditor(nli_judge=judge).audit(_make_input(text))

    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.nli_calls == 1
    assert report.nli_cache_hits == 1
    assert len(judge.calls) == 1


def test_bounded_concurrency_reduces_wall_clock_without_merging_evidence():
    text = (
        "El scheduler desaloja el proceso [E1].\n"
        "El kernel libera la página [E1].\n"
        "La memoria se asigna al proceso [E1].\n"
    )
    judge = _SlowJudge(delay=0.2)
    started = time.perf_counter()
    report = ForensicAuditor(
        nli_judge=judge, nli_max_concurrency=3, nli_budget_seconds=5.0
    ).audit(_make_input(text))
    elapsed = time.perf_counter() - started

    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.nli_calls == 3
    # Sequential would be ~0.6s; three workers finish in roughly one delay.
    assert elapsed < 0.45
    assert len({hypothesis for _, hypothesis in judge.calls}) == 3


def test_audit_budget_marks_remaining_claims_unassessed_never_approved():
    text = "\n".join(
        f"El recurso {i} se libera de forma verificable [E1]." for i in range(6)
    )
    judge = _SlowJudge(delay=0.2)
    report = ForensicAuditor(
        nli_judge=judge, nli_max_concurrency=2, nli_budget_seconds=0.05
    ).audit(_make_input(text))

    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.nli_calls <= 2
    assert len(judge.calls) <= 2
    unassessed = [
        v
        for v in report.claim_verifications
        if v.nli_verdict == ClaimSupportVerdict.UNASSESSED
    ]
    assert unassessed
    assert all(
        "budget exhausted" in (v.nli_rationale or "").lower()
        for v in unassessed
    )


def test_unresolved_citation_is_unassessed_without_calling_the_judge():
    # A crafted response can cite a tag that is not declared in ``citations``
    # and therefore does not trip manifest integrity.  The auditor must still
    # refuse to ask the judge with an empty premise.
    text = "El scheduler desaloja el proceso [E99].\n"
    judge = _SlowJudge(delay=0.0)
    report = ForensicAuditor(nli_judge=judge).audit(
        _make_input(text, tags=("E1",), declared_tags=())
    )

    assert report.overall_verdict != AuditVerdict.APPROVED
    assert judge.calls == []
    assert report.nli_calls == 0
    assert any(
        "not present in packaged context" in (v.nli_rationale or "")
        for v in report.claim_verifications
    )


def test_citation_markers_are_not_sent_to_the_semantic_judge():
    text = "- En ejecución [E1].\n"
    judge = _SlowJudge(delay=0.0)
    report = ForensicAuditor(nli_judge=judge).audit(_make_input(text))

    assert report.overall_verdict == AuditVerdict.APPROVED
    assert judge.calls
    hypothesis = judge.calls[0][1]
    assert "[E1]" not in hypothesis
    assert hypothesis == "En ejecución."
    # The report still preserves the original cited claim text.
    assert report.claim_verifications[0].claim_text == "En ejecución [E1]."


def test_provider_failure_is_counted_as_technical_not_academic():
    report = ForensicAuditor(
        nli_judge=_RaisingJudge(TimeoutError("provider timed out"))
    ).audit(_make_input("El scheduler desaloja el proceso [E1]."))

    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.nli_calls == 1
    assert report.nli_technical_failures == 1
    assert report.nli_budget_exhausted is False
    assert report.claim_verifications[0].nli_verdict == ClaimSupportVerdict.UNASSESSED
