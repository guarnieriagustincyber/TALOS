"""Real HTTP/SSE route, pipeline and generation adapter with synthetic inputs.

Only retrieval preparation and generation/auditor ports are controlled. The
auditor emits typed reports, never NLI calls; no application/container startup.
"""
import asyncio
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from study_engine.audit.contracts import (
    AuditVerdict, ClaimSupportVerdict, ClaimType, ClaimVerification,
    ForensicAuditReport, LexicalAnomalyStatus, LexicalDiagnostics,
)
from study_engine.hierarchy.scope_resolver import ResolvedScope, ScopeType
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.utils.cache import TTLCache
from study_engine.web.local_access import configure_local_access
from study_engine.web.routes import chat, evidence

TEXT = "Una tabla de rutas selecciona el siguiente salto. [E1]"


class InstrumentedAuditor:
    def __init__(self):
        self.verdict = AuditVerdict.APPROVED
        self.failures = 0
        self.inputs = []
        self.reports = []
        self.empty_claims = False
        self.missing = False
        self.error = None
        self.reuse = False

    def audit(self, payload):
        self.inputs.append(payload)
        if self.error:
            raise self.error("synthetic operational failure")
        if self.missing:
            return None
        if self.reuse and self.reports:
            return self.reports[0]
        claims = () if self.empty_claims else (ClaimVerification(
            claim_index=0, claim_text=TEXT, claim_type=ClaimType.FACTUAL,
            cited_tags=("E1",), lexical_diagnostics=LexicalDiagnostics(status=LexicalAnomalyStatus.NO_ANOMALY),
            nli_verdict=ClaimSupportVerdict.ENTAILED if self.verdict == AuditVerdict.APPROVED else ClaimSupportVerdict.UNASSESSED,
            nli_rationale="PRIVATE OPERATOR RATIONALE",
        ),)
        report = ForensicAuditReport(
            audit_id="audit-" + payload.request.request_id, request_id=payload.request.request_id,
            notebook_id=payload.request.notebook_id, prompt_hash=payload.prompt_hash,
            overall_verdict=self.verdict, claim_verifications=claims,
            nli_executed=False, nli_technical_failures=self.failures,
            evidence_hashes=tuple(u.citation.content_hash for u in payload.request.packaged_context.packaged_units),
            audit_latency_ms=0.0, auditor_backend="synthetic-instrumented-no-NLI",
        )
        self.reports.append(report)
        return report


class FixedBackend:
    name = "synthetic-fixed-text"
    gate = None

    async def stream(self, **kwargs):
        if self.gate is not None:
            if "slow-fixture" in kwargs.get("user_prompt", ""):
                await self.gate.wait()
            else:
                self.gate.set()
        yield TEXT


def make_app(monkeypatch):
    auditor, backend = InstrumentedAuditor(), FixedBackend()
    container = SimpleNamespace(knowledge_store=SimpleNamespace(), controller=SimpleNamespace(), auditor=auditor)
    for name in ("_ACTIVE_TURN_HISTORIES", "_CONV_TURN_BUFFER", "_ACTIVE_PROTECTED_ASSESSMENTS", "_KC_TURN_STREAKS"):
        monkeypatch.setattr(chat, name, TTLCache())
    monkeypatch.setattr(evidence, "_claims_cache", TTLCache())

    async def inline(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", inline)
    monkeypatch.setattr(chat, "_resolve_chat_backend", lambda *a, **kw: backend)

    def prepare(**kwargs):
        nb = kwargs["target_scope_id"]
        contract = PedagogicalContract(
            notebook_id=nb, base_system_prompt="Synthetic fixture only", forbidden_patterns=[], safe_words=[],
            response_phases=[ResponsePhase(phase_id="conceptual", phase_prompt_template="Explicá {concept}.", max_tokens=120)],
        )
        chunk = {"citation_id": "E1", "chunk_id": "chunk-synthetic", "document_id": "doc-synthetic",
                 "source_id": "source-synthetic", "source_title": "Synthetic routes", "chunk_text": TEXT,
                 "doc_hash": hashlib.sha256(TEXT.encode()).hexdigest(), "page_start": 1, "page_end": 1}
        pack = chat.EpistemicContextPack("[E1] " + TEXT, [], [chunk], is_sufficient=True)
        scope = ResolvedScope(scope_type=ScopeType.NOTEBOOK, scope_id=nb, notebook_id=nb)
        return scope, contract, pack, [chunk], None, "basic", None, None, None, None, None

    monkeypatch.setattr(chat, "_prepare_chat_context", prepare)
    app = FastAPI()
    app.include_router(chat.router)
    configure_local_access(app, perimeter_enabled=True)

    async def provide():
        return container

    app.dependency_overrides[chat.get_container] = provide
    return app, auditor, backend


async def exchange(app, session="session-A", query="tabla de rutas", notebook="nb-synthetic"):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
        response = await client.post("/api/chat/query", headers={"origin": "http://localhost:5173"}, json={
            "prompt": query, "session_id": session, "scope_type": "notebook", "scope_id": notebook,
        })
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    return events


def projection(events):
    return next(e["payload"]["audit_projection"] for e in events if e["event_type"] == "audit_verdict" and "audit_projection" in e["payload"])


def test_approved_projection_comes_from_actual_adapter_and_validated_report(monkeypatch):
    app, auditor, _ = make_app(monkeypatch)
    events = asyncio.run(exchange(app))
    p = projection(events)
    assert len(auditor.inputs) == 1
    assert p["audit_id"] == auditor.reports[0].audit_id and p["request_id"] == auditor.inputs[0].request.request_id
    assert p["session_id"] == "session-A" and p["notebook_id"] == p["scope_id"] == "nb-synthetic"
    emitted = "".join(e["payload"]["token"] for e in events if e["event_type"] == "phase_token")
    assert emitted and p["content_sha256"] == hashlib.sha256(emitted.encode()).hexdigest()
    assert p["auditor_verdict"] == p["decision"] == "APPROVED" and p["emission"] == "authorized"
    assert events[-1]["event_type"] == "phase_complete"
    assert "PRIVATE OPERATOR RATIONALE" not in json.dumps(events)
    assert "claim_text" not in p["claims"][0] and p["claims"][0]["cited_tags"] == ["E1"]
    assert len(evidence._claims_cache) == 0


@pytest.mark.parametrize("verdict,failures,decision", [
    (AuditVerdict.REJECTED_UNSUPPORTED, 0, "REJECTED_UNSUPPORTED"),
    (AuditVerdict.FLAGGED_UNASSESSED, 0, "FLAGGED_UNASSESSED"),
    (AuditVerdict.FLAGGED_UNASSESSED, 1, "DEFERRED_RETRY"),
])
def test_rejected_and_inconclusive_preserve_original_without_leaking_text(monkeypatch, verdict, failures, decision):
    app, auditor, _ = make_app(monkeypatch)
    auditor.verdict, auditor.failures = verdict, failures
    events = asyncio.run(exchange(app))
    p = projection(events)
    assert p["auditor_verdict"] == verdict.value and p["decision"] == decision and p["emission"] == "blocked"
    assert not any(e["event_type"] == "phase_token" for e in events)
    assert TEXT not in json.dumps(events, ensure_ascii=False)
    assert events[-1]["event_type"] == "abstention"


@pytest.mark.parametrize("error,missing", [(None, True), (TimeoutError, False), (RuntimeError, False)])
def test_absent_or_failed_auditor_never_fabricates_projection(monkeypatch, error, missing):
    app, auditor, _ = make_app(monkeypatch)
    auditor.error, auditor.missing = error, missing
    events = asyncio.run(exchange(app))
    assert not any("audit_projection" in e["payload"] for e in events)
    assert not any(e["event_type"] == "phase_token" for e in events)


def test_reused_report_cannot_approve_a_new_response(monkeypatch):
    app, auditor, _ = make_app(monkeypatch)
    first = asyncio.run(exchange(app))
    auditor.reuse = True
    second = asyncio.run(exchange(app))
    assert projection(first)["decision"] == "APPROVED"
    assert not any("audit_projection" in e["payload"] for e in second)
    assert any(e["payload"].get("verdict") == "REJECTED_INPUT_MISMATCH" for e in second)


def test_final_route_rewrite_cannot_keep_an_approval_projection(monkeypatch):
    app, _, _ = make_app(monkeypatch)
    from study_engine.pedagogy.citation_validator import CitationValidator
    monkeypatch.setattr(CitationValidator, "validate_and_rewrite", lambda self, text, chunks: (text + " ALTERED", []))
    events = asyncio.run(exchange(app))
    assert not any("audit_projection" in e["payload"] for e in events)
    assert not any(e["event_type"] == "phase_token" for e in events)


@pytest.mark.parametrize("same_session", [True, False])
def test_concurrent_invocations_keep_their_own_reports(monkeypatch, same_session):
    app, auditor, backend = make_app(monkeypatch)

    async def run():
        backend.gate = asyncio.Event()
        return await asyncio.gather(exchange(app, "A", "slow-fixture"), exchange(app, "A" if same_session else "B", "fast-fixture"))

    first, second = asyncio.run(run())
    a, b = projection(first), projection(second)
    assert a["request_id"] != b["request_id"] and a["content_binding_id"] != b["content_binding_id"]
    assert a["audit_id"] != b["audit_id"] and a["session_id"] == "A" and b["session_id"] == ("A" if same_session else "B")
    assert auditor.inputs[0].request.query == "fast-fixture"


def test_report_with_zero_claims_is_not_missing(monkeypatch):
    app, auditor, _ = make_app(monkeypatch)
    auditor.empty_claims = True
    p = projection(asyncio.run(exchange(app)))
    assert p["claims"] == [] and p["audit_id"] and p["decision"] == "APPROVED"


@pytest.mark.parametrize("first_verdict,last_verdict", [
    (AuditVerdict.APPROVED, AuditVerdict.REJECTED_UNSUPPORTED),
    (AuditVerdict.REJECTED_UNSUPPORTED, AuditVerdict.APPROVED),
])
def test_later_verdict_does_not_rewrite_prior_projection(monkeypatch, first_verdict, last_verdict):
    app, auditor, _ = make_app(monkeypatch)
    auditor.verdict = first_verdict
    first = projection(asyncio.run(exchange(app)))
    auditor.verdict = last_verdict
    last = projection(asyncio.run(exchange(app)))
    assert first["auditor_verdict"] == first_verdict.value and last["auditor_verdict"] == last_verdict.value
    assert first["request_id"] != last["request_id"]
