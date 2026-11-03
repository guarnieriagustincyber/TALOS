"""Focal F2 tests: SSE progress during the S4.4 audit gate.

Progress events must:
* be emitted while the audit is still running (so a long NLI evaluation does
  not look like a dead connection), and
* never release generated academic content before the approval verdict.
"""

import asyncio
import time

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


class _FakeLLM:
    def __init__(self, token: str) -> None:
        self.token = token

    async def stream(self, **kwargs):
        yield self.token


def _pipeline(token: str) -> StructuredResponsePipeline:
    contract = PedagogicalContract(
        notebook_id="test-notebook",
        base_system_prompt="Tutor de prueba con reglas pedagógicas.",
        forbidden_patterns=["<blocked-code>"],
        safe_words=[],
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                phase_prompt_template="Explicá {concept}.",
                max_tokens=100,
            )
        ],
    )
    return StructuredResponsePipeline(
        contract=contract, llm_backend=_FakeLLM(token), auditor=object()
    )


def _collect(pipeline: StructuredResponsePipeline) -> list:
    async def run():
        return [
            event
            async for event in pipeline.generate_phased_response(
                user_query="Explicá el concepto",
                requested_phase="conceptual",
            )
        ]

    return asyncio.run(run())


def _report(kwargs, **overrides) -> ForensicAuditReport:
    fields = {
        "audit_id": "audit-progress-current",
        "request_id": kwargs["request_id"],
        "notebook_id": kwargs["notebook_id"],
        "prompt_hash": kwargs["prompt_hash"],
        "overall_verdict": AuditVerdict.APPROVED,
        "audit_latency_ms": 50.0,
        "auditor_backend": "synthetic-auditor",
    }
    fields.update(overrides)
    return ForensicAuditReport(**fields)


def test_audit_emits_progress_without_releasing_unverified_content(monkeypatch):
    import study_engine.pedagogy.structured_pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "_AUDIT_PROGRESS_INTERVAL_S", 0.01)

    def slow_approve(*_args, **kwargs):
        time.sleep(0.05)
        return _report(kwargs)

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        slow_approve,
    )

    events = _collect(_pipeline("Respuesta fundamentada [E1]."))

    progress_indices = [
        index for index, event in enumerate(events)
        if event.event_type == "progress"
    ]
    audit_index = next(
        index for index, event in enumerate(events)
        if event.event_type == "audit_verdict"
    )
    token_indices = [
        index for index, event in enumerate(events)
        if event.event_type == "phase_token"
    ]

    assert progress_indices, "expected at least one progress event"
    assert max(progress_indices) < audit_index
    assert token_indices and min(token_indices) > audit_index

    stages = {events[index].payload.get("stage") for index in progress_indices}
    assert "audit_started" in stages
    assert "auditing" in stages

    # Progress payloads contain stage bookkeeping only, never academic text.
    for index in progress_indices:
        payload = events[index].payload
        assert "token" not in payload
        assert set(payload).issubset(
            {"phase", "stage", "message", "generation_ms", "elapsed_ms"}
        )


def test_audit_verdict_carries_latency_metrics(monkeypatch):
    import study_engine.pedagogy.structured_pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "_AUDIT_PROGRESS_INTERVAL_S", 10.0)
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **kwargs: _report(
            kwargs, nli_calls=2, nli_cache_hits=1
        ),
    )

    events = _collect(_pipeline("Respuesta fundamentada [E1]."))
    verdict = next(event for event in events if event.event_type == "audit_verdict")

    assert verdict.payload["verdict"] == "APPROVED"
    metrics = verdict.payload["metrics"]
    assert "generation_ms" in metrics
    assert metrics["audit_ms"] == 50.0
    assert metrics["nli_executed"] is False
    # Per-audit provider calls, not a cumulative judge counter.
    assert metrics["nli_calls"] == 2
    assert metrics["nli_cache_hits"] == 1


def test_technical_audit_failure_is_not_labelled_as_academic_abstention(monkeypatch):
    def fail(*_args, **_kwargs):
        raise TimeoutError("provider timed out")

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        fail,
    )

    events = _collect(_pipeline("Texto retenido [E1]."))
    abstention = next(event for event in events if event.event_type == "abstention")

    assert abstention.payload["abstention_code"] == "DEFERRED_RETRY"
    assert abstention.payload["failure_class"] == "TECHNICAL"
    assert "fallo operativo" in abstention.payload["reason"]
    assert not any(event.event_type == "phase_token" for event in events)


def test_nli_provider_failure_is_reported_as_technical_not_academic(monkeypatch):
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **kwargs: _report(
            kwargs,
            overall_verdict=AuditVerdict.FLAGGED_UNASSESSED,
            nli_technical_failures=1,
        ),
    )

    events = _collect(_pipeline("Texto retenido [E1]."))
    verdict = next(event for event in events if event.event_type == "audit_verdict")
    abstention = next(event for event in events if event.event_type == "abstention")

    assert verdict.payload["verdict"] == "DEFERRED_RETRY"
    assert abstention.payload["abstention_code"] == "DEFERRED_RETRY"
    assert abstention.payload["failure_class"] == "TECHNICAL"
    assert not any(event.event_type == "phase_token" for event in events)


def test_semantic_unassessed_without_provider_failure_stays_academic(monkeypatch):
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **kwargs: _report(
            kwargs,
            overall_verdict=AuditVerdict.FLAGGED_UNASSESSED,
            nli_technical_failures=0,
            nli_budget_exhausted=True,
        ),
    )

    events = _collect(_pipeline("Texto retenido [E1]."))
    verdict = next(event for event in events if event.event_type == "audit_verdict")
    abstention = next(event for event in events if event.event_type == "abstention")

    assert verdict.payload["verdict"] == "FLAGGED_UNASSESSED"
    assert abstention.payload["failure_class"] == "ACADEMIC_OR_UNVERIFIED"
    assert not any(event.event_type == "phase_token" for event in events)


def test_academic_rejection_is_labelled_as_academic(monkeypatch):
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **kwargs: _report(
            kwargs, overall_verdict=AuditVerdict.REJECTED_UNSUPPORTED
        ),
    )

    events = _collect(_pipeline("Contenido no respaldado [E1]."))
    abstention = next(event for event in events if event.event_type == "abstention")

    assert abstention.payload["abstention_code"] == "REJECTED_UNSUPPORTED"
    assert abstention.payload["failure_class"] == "ACADEMIC_OR_UNVERIFIED"
    assert not any(event.event_type == "phase_token" for event in events)
