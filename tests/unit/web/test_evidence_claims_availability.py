"""FIX-1: synthetic session projections never turn missing data into approval.

Exercises the real router without application startup, threads, or persistence.
Does not establish S4.4 provenance for injected presentation-cache fixtures.
"""

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from study_engine.session.study_session_contracts import (
    AuthoritativeSessionState,
    CurriculumPosition,
    OpeningBriefFacts,
)
from study_engine.utils import cache as cache_module
from study_engine.utils.cache import TTLCache
from study_engine.web.routes import evidence


@pytest.fixture
def endpoint(monkeypatch):
    cache = TTLCache(maxsize=1000, ttl=3600)
    monkeypatch.setattr(evidence, "_claims_cache", cache)
    container = SimpleNamespace(study_session_orchestrator=SimpleNamespace(_sessions={}))
    app = FastAPI()
    app.include_router(evidence.router)

    async def provide_container():
        return container

    async def inline(function, *args, **kwargs):
        return function(*args, **kwargs)

    app.dependency_overrides[evidence.get_container] = provide_container
    monkeypatch.setattr("fastapi.routing.run_in_threadpool", inline)
    monkeypatch.setattr("fastapi.dependencies.utils.run_in_threadpool", inline)

    def get(session_id):
        async def request():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                base_url="http://synthetic",
            ) as client:
                return await client.get(f"/api/evidence/claims/{session_id}")

        return asyncio.run(request())

    return get, cache, container


def projection(session_id="session-A", verdict="APPROVED", claims=None):
    return evidence.ClaimsVerificationResponse(
        session_id=session_id, verdict=verdict, claims=claims or []
    ).model_dump()


def test_session_without_history_has_no_report(endpoint):
    get, cache, container = endpoint
    position = CurriculumPosition("unit", "Synthetic", ("kc",), (), (), ("kc",))
    facts = OpeningBriefFacts(
        "nb", "Synthetic", "fixture", position, ("kc",), "kc", "fixture",
        0.1, "SYNTHETIC", None, "not real", "NONE", "fixture",
    )
    state = AuthoritativeSessionState(
        "session-A", "nb", "synthetic-student", datetime.now(timezone.utc),
        "curriculum", "kc", None, "IDLE", (), "", None, facts, None, "synthetic",
    )
    assert not hasattr(state, "history")
    container.study_session_orchestrator._sessions[state.session_id] = state
    response = get(state.session_id)
    assert response.status_code == 404
    assert "verdict" not in response.json()
    assert len(cache) == 0


def test_unknown_session_does_not_create_a_projection(endpoint):
    get, cache, _ = endpoint
    response = get("unknown")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No hay un reporte de auditoría disponible para esta consulta."
    }
    assert len(cache) == 0


def test_expired_rejection_is_unavailable_not_approved(endpoint, monkeypatch):
    get, cache, _ = endpoint
    now = [100.0]
    monkeypatch.setattr(cache_module, "time", SimpleNamespace(time=lambda: now[0]))
    cache["session-A"] = projection(verdict="REJECTED_UNSUPPORTED")
    assert get("session-A").json()["verdict"] == "REJECTED_UNSUPPORTED"
    now[0] += 3601
    assert get("session-A").status_code == 404
    assert len(cache) == 0


@pytest.mark.parametrize("verdict", [
    "APPROVED", "REJECTED_UNSUPPORTED", "FLAGGED_UNASSESSED", "DEFERRED_RETRY",
])
def test_explicit_projection_preserves_verdict_and_empty_claims(endpoint, verdict):
    get, cache, _ = endpoint
    cached = projection(verdict=verdict)
    cache["session-A"] = cached
    response = get("session-A")
    assert response.status_code == 200
    assert response.json() == cached


def test_claim_and_contradiction_dtos_remain_compatible(endpoint):
    get, cache, _ = endpoint
    data = projection(verdict="PARTIAL_ABSTENTION", claims=[{
        "claim_id": "C1", "claim_text": "Synthetic claim", "claim_type": "FACTUAL_TEXTUAL",
        "criticality": "CRITICAL", "status": "UNSUPPORTED", "grounding_ratio": 0.0,
        "cited_evidence_indices": ["E1"], "has_redaction": True,
    }])
    data["contradictions"] = [{
        "claim_id": "C1", "claim_text": "Synthetic claim", "source_a": "E1",
        "assertion_a": "A", "source_b": "E2", "assertion_b": "B",
        "conflict_type": "SYNTHETIC", "status": "UNRESOLVED_CONTRADICTION",
    }]
    cache["session-A"] = data
    assert get("session-A").json() == data


def test_cache_identity_mismatch_is_an_internal_error(endpoint):
    get, cache, _ = endpoint
    cache["session-B"] = projection("session-A")
    response = get("session-B")
    assert response.status_code == 500
    assert "session-A" not in response.text
    assert "verdict" not in response.json()


def test_internal_cache_failure_does_not_become_absence_or_approval(endpoint, monkeypatch):
    get, _, _ = endpoint

    class BrokenCache:
        def __getitem__(self, key):
            raise RuntimeError("synthetic cache failure")

    monkeypatch.setattr(evidence, "_claims_cache", BrokenCache())
    response = get("session-A")
    assert response.status_code == 500
    assert "APPROVED" not in response.text


def test_blank_identifier_remains_bad_request(endpoint):
    get, _, _ = endpoint
    assert get("%20").status_code == 400
