"""Regression tests for honest audit verdicts on generated phases."""

import asyncio
from types import SimpleNamespace

import pytest
from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.dialogue_engine import DialogueEngine, EvidenceResult
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import (
    StreamEvent,
    StructuredResponsePipeline,
    _content_binding_hash,
    _content_binding_matches,
    _pending_content_text,
)
from study_engine.web.routes.chat import _route_content_binding_matches


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


def _report_for_call(kwargs, **overrides) -> ForensicAuditReport:
    fields = {
        "audit_id": "audit-synthetic-current",
        "request_id": kwargs["request_id"],
        "notebook_id": kwargs["notebook_id"],
        "prompt_hash": kwargs["prompt_hash"],
        "overall_verdict": AuditVerdict.APPROVED,
        "audit_latency_ms": 0.0,
        "auditor_backend": "synthetic-auditor",
    }
    fields.update(overrides)
    return ForensicAuditReport(**fields)


def _phase_events(pipeline: StructuredResponsePipeline) -> list[StreamEvent]:
    async def collect() -> list[StreamEvent]:
        return [
            event
            async for event in pipeline.generate_phased_response(
                user_query="Explicá el concepto",
                requested_phase="conceptual",
            )
        ]

    return asyncio.run(collect())


def test_guard_triggered_never_reports_approved():
    assert _audit_verdict(_pipeline(token="<blocked-code>")) == "FLAGGED_BY_GUARD"


def test_auditor_unavailable_never_reports_approved():
    assert _audit_verdict(_pipeline(token="Respuesta sin código")) == "AUDITOR_UNAVAILABLE"


def test_executed_audit_approval_reports_approved(monkeypatch):
    calls = []

    def approve(*args, **kwargs):
        calls.append((args, kwargs))
        return _report_for_call(kwargs)

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        approve,
    )

    verdict = _audit_verdict(
        _pipeline(token="Respuesta fundamentada", auditor=object())
    )

    assert calls
    assert verdict == "APPROVED"


def test_approved_audit_precedes_release_of_generated_tokens(monkeypatch):
    def approve(*args, **kwargs):
        return _report_for_call(kwargs)

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        approve,
    )

    async def collect() -> list:
        return [
            event
            async for event in _pipeline(
                token="Respuesta fundamentada",
                auditor=object(),
            ).generate_phased_response(
                user_query="Explicá el concepto",
                requested_phase="conceptual",
            )
        ]

    events = asyncio.run(collect())
    audit_index = next(
        index for index, event in enumerate(events)
        if event.event_type == "audit_verdict"
    )
    token_indices = [
        index for index, event in enumerate(events)
        if event.event_type == "phase_token"
    ]

    assert token_indices
    assert min(token_indices) > audit_index


@pytest.mark.parametrize(
    ("changed_field", "changed_value"),
    [
        ("request_id", "req_other_execution"),
        ("notebook_id", "other-notebook"),
        ("prompt_hash", "0" * 64),
    ],
)
def test_approved_report_with_incompatible_identity_never_releases_tokens(
    monkeypatch, changed_field, changed_value
):
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **kwargs: _report_for_call(
            kwargs, **{changed_field: changed_value}
        ),
    )

    events = _phase_events(_pipeline(token="Mismo contenido", auditor=object()))

    assert next(e for e in events if e.event_type == "audit_verdict").payload["verdict"] == "REJECTED_INPUT_MISMATCH"
    assert not any(e.event_type == "phase_token" for e in events)
    assert any(e.event_type == "abstention" for e in events)
    assert not any(e.event_type == "phase_complete" for e in events)


def test_report_from_prior_execution_cannot_approve_identical_text(monkeypatch):
    calls = []
    prior_report = None

    def return_prior_report(*_args, **kwargs):
        nonlocal prior_report
        calls.append(kwargs)
        if prior_report is None:
            prior_report = _report_for_call(kwargs)
        return prior_report

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        return_prior_report,
    )

    first = _phase_events(_pipeline(token="Texto idéntico", auditor=object()))
    second = _phase_events(_pipeline(token="Texto idéntico", auditor=object()))

    assert calls[0]["generated_text"] == calls[1]["generated_text"]
    assert calls[0]["request_id"] != calls[1]["request_id"]
    assert any(e.event_type == "phase_token" for e in first)
    assert next(e for e in second if e.event_type == "audit_verdict").payload["verdict"] == "REJECTED_INPUT_MISMATCH"
    assert not any(e.event_type == "phase_token" for e in second)
    assert any(e.event_type == "abstention" for e in second)


@pytest.mark.parametrize("invalid_report", [None, SimpleNamespace(overall_verdict="APPROVED")])
def test_missing_or_untyped_audit_report_cannot_approve(monkeypatch, invalid_report):
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **_kwargs: invalid_report,
    )

    events = _phase_events(_pipeline(token="Texto retenido", auditor=object()))

    assert next(e for e in events if e.event_type == "audit_verdict").payload["verdict"] == "AUDIT_RESULT_MISSING"
    assert not any(e.event_type == "phase_token" for e in events)
    assert any(e.event_type == "abstention" for e in events)


def test_report_without_valid_audit_id_cannot_approve(monkeypatch):
    def report_without_audit_id(*_args, **kwargs):
        report = _report_for_call(kwargs)
        return report.model_copy(update={"audit_id": ""})

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        report_without_audit_id,
    )

    events = _phase_events(_pipeline(token="Texto retenido", auditor=object()))

    assert next(e for e in events if e.event_type == "audit_verdict").payload["verdict"] == "REJECTED_INPUT_MISMATCH"
    assert not any(e.event_type == "phase_token" for e in events)


@pytest.mark.parametrize("error", [TimeoutError, ConnectionError, RuntimeError])
def test_audit_failure_never_releases_tokens(monkeypatch, error):
    def fail(*_args, **_kwargs):
        raise error("synthetic audit failure")

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        fail,
    )

    events = _phase_events(_pipeline(token="Texto retenido", auditor=object()))

    assert not any(e.event_type == "phase_token" for e in events)
    assert any(e.event_type == "abstention" for e in events)


def test_failed_content_binding_cannot_release_after_valid_report(monkeypatch):
    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **kwargs: _report_for_call(kwargs),
    )
    monkeypatch.setattr(
        "study_engine.pedagogy.structured_pipeline._content_binding_matches",
        lambda *_args: False,
    )

    events = _phase_events(_pipeline(token="Texto retenido", auditor=object()))

    assert next(e for e in events if e.event_type == "audit_verdict").payload["verdict"] == "REJECTED_INPUT_MISMATCH"
    assert not any(e.event_type == "phase_token" for e in events)
    assert any(e.event_type == "abstention" for e in events)


def test_non_approved_audit_does_not_release_generated_tokens(monkeypatch):
    def reject(*args, **kwargs):
        return _report_for_call(
            kwargs, overall_verdict=AuditVerdict.REJECTED_UNSUPPORTED
        )

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        reject,
    )

    async def collect() -> list:
        return [
            event
            async for event in _pipeline(
                token="Contenido no aprobado",
                auditor=object(),
            ).generate_phased_response(
                user_query="Explicá el concepto",
                requested_phase="conceptual",
            )
        ]

    events = asyncio.run(collect())

    assert next(event for event in events if event.event_type == "audit_verdict").payload["verdict"] == "REJECTED_UNSUPPORTED"
    assert not any(event.event_type == "phase_token" for event in events)
    assert any(event.event_type == "abstention" for event in events)


def test_content_binding_hash_is_stable_for_exact_audited_text():
    text = "Respuesta fundamentada."
    assert _content_binding_hash(text) == _content_binding_hash(text)
    assert _content_binding_hash(text) != _content_binding_hash(text + " alterada")


def test_pending_sse_fragments_reconstruct_exact_audited_text():
    events = [
        StreamEvent(event_type="phase_token", payload={"token": "Res"}),
        StreamEvent(event_type="phase_token", payload={"token": "puesta"}),
        StreamEvent(event_type="phase_token", payload={"token": "."}),
    ]
    assert _pending_content_text(events) == "Respuesta."


def test_pending_sse_fragments_detect_content_mismatch():
    events = [
        StreamEvent(event_type="phase_token", payload={"token": "Texto"}),
    ]
    assert _pending_content_text(events) != "Texto alterado"
    assert not _content_binding_matches(
        "Texto alterado",
        events,
        _content_binding_hash("Texto alterado"),
    )


def test_route_releases_only_exactly_audited_text():
    audited = "Respuesta fundamentada."
    binding_id = "current-run"
    assert _route_content_binding_matches(
        _content_binding_hash(audited), audited, binding_id, binding_id
    )


def test_route_blocks_post_audit_transformation():
    audited = "Respuesta fundamentada."
    transformed = "Respuesta fundamentada.\n\n[ref. no verificada]"
    binding_id = "current-run"
    assert not _route_content_binding_matches(
        _content_binding_hash(audited), transformed, binding_id, binding_id
    )


def test_route_rejects_verdict_hash_from_another_response():
    audited = "Respuesta A."
    current = "Respuesta B."
    assert not _route_content_binding_matches(
        _content_binding_hash(audited), current, "old-run", "current-run"
    )


def test_route_rejects_missing_binding_metadata():
    assert not _route_content_binding_matches(
        None, "Respuesta fundamentada.", None, "current-run"
    )


def _dialogue_audit_verdict(auditor) -> str:
    engine = DialogueEngine(forensic_auditor=auditor)
    evidence = EvidenceResult(chunks=[], citations=[], level="NONE")
    return engine._execute_s44_audit("Respuesta de prueba", evidence)


def test_dialogue_auditor_unavailable_is_not_approved():
    assert _dialogue_audit_verdict(None) == "REJECTED_AUDIT_ERROR"


def test_dialogue_auditor_without_supported_interface_is_not_approved():
    assert _dialogue_audit_verdict(object()) == "REJECTED_AUDIT_ERROR"


@pytest.mark.parametrize(
    "result",
    [SimpleNamespace(), SimpleNamespace(overall_verdict="NOT_A_VERDICT")],
)
def test_dialogue_audit_without_valid_verdict_is_not_approved(monkeypatch, result):
    class Auditor:
        def audit(self):
            pass

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **_kwargs: result,
    )

    assert _dialogue_audit_verdict(Auditor()) == "REJECTED_AUDIT_ERROR"


def test_dialogue_audit_legacy_result_without_verdict_is_not_approved():
    class Auditor:
        def audit_claims(self, _claims, _evidence):
            return SimpleNamespace()

    assert _dialogue_audit_verdict(Auditor()) == "REJECTED_AUDIT_ERROR"


def test_dialogue_legacy_rejection_verdict_is_preserved():
    class Auditor:
        def audit_claims(self, _claims, _evidence):
            return SimpleNamespace(verdict="REJECTED")

    assert _dialogue_audit_verdict(Auditor()) == "REJECTED"


@pytest.mark.parametrize("error", [TimeoutError, ConnectionError])
def test_dialogue_legacy_transient_audit_errors_are_deferred(error):
    class Auditor:
        def audit_claims(self, _claims, _evidence):
            raise error("temporary audit failure")

    assert _dialogue_audit_verdict(Auditor()) == "DEFERRED_RETRY"


def test_dialogue_audit_exception_is_not_approved(monkeypatch):
    class Auditor:
        def audit(self):
            pass

    def fail(*_args, **_kwargs):
        raise RuntimeError("audit failed")

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        fail,
    )

    assert _dialogue_audit_verdict(Auditor()) == "REJECTED_AUDIT_ERROR"


@pytest.mark.parametrize(
    ("verdict", "expected"),
    [
        (AuditVerdict.APPROVED, "APPROVED"),
        (AuditVerdict.REJECTED_UNSUPPORTED, "REJECTED_UNSUPPORTED"),
    ],
)
def test_dialogue_valid_audit_verdict_is_preserved(monkeypatch, verdict, expected):
    class Auditor:
        def audit(self):
            pass

    monkeypatch.setattr(
        "study_engine.audit.generation_adapter.audit_generation_payload",
        lambda *_args, **_kwargs: SimpleNamespace(overall_verdict=verdict),
    )

    assert _dialogue_audit_verdict(Auditor()) == expected
