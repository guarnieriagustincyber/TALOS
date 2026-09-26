"""Regression tests for honest audit verdicts on generated phases."""

import asyncio
from types import SimpleNamespace

from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


class _FakeLLM:
    def __init__(self, token: str) -> None:
        self.token = token

    async def stream(self, **kwargs):
        yield self.token


def _pipeline(*, token: str, auditor=None) -> StructuredResponsePipeline:
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
        contract=contract,
        llm_backend=_FakeLLM(token),
        auditor=auditor,
    )


def _audit_verdict(pipeline: StructuredResponsePipeline) -> str:
    async def collect() -> list:
        return [
            event
            async for event in pipeline.generate_phased_response(
                user_query="Explicá el concepto",
                requested_phase="conceptual",
            )
        ]

    events = asyncio.run(collect())
    audit_event = next(event for event in events if event.event_type == "audit_verdict")
    return audit_event.payload["verdict"]


def test_guard_triggered_never_reports_approved():
    assert _audit_verdict(_pipeline(token="<blocked-code>")) == "FLAGGED_BY_GUARD"


def test_auditor_unavailable_never_reports_approved():
    assert _audit_verdict(_pipeline(token="Respuesta sin código")) == "AUDITOR_UNAVAILABLE"


def test_executed_audit_approval_reports_approved(monkeypatch):
    calls = []

    def approve(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(overall_verdict="APPROVED")

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        approve,
    )

    verdict = _audit_verdict(
        _pipeline(token="Respuesta fundamentada", auditor=object())
    )

    assert calls
    assert verdict == "APPROVED"
