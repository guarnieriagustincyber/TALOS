"""Real local perimeter on a synthetic ASGI app; no product startup or storage."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI

from study_engine.web.local_access import configure_local_access


def request(*, host="127.0.0.1:8000", headers=None, method="POST", peer="127.0.0.1"):
    app = FastAPI()
    called = []

    @app.api_route("/api/synthetic", methods=["GET", "POST"])
    async def endpoint():
        called.append(True)
        return {"synthetic": True}

    # Explicit opt-in: the pytest-process default disables the perimeter.
    configure_local_access(app, perimeter_enabled=True)

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, client=(peer, 12345)),
            base_url="http://127.0.0.1:8000",
        ) as client:
            return await client.request(method, "/api/synthetic", headers={"host": host, **(headers or {})})

    return asyncio.run(run()), called


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_legitimate_browser_can_reach_local_handler(origin):
    response, called = request(headers={"origin": origin, "sec-fetch-site": "same-site"})
    assert response.status_code == 200 and called
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize("headers", [
    {"origin": "https://evil.invalid"}, {"origin": "null"},
    {"origin": "http://localhost:9999"}, {"sec-fetch-site": "cross-site"},
    {"origin": "https://evil.invalid", "content-type": "application/x-www-form-urlencoded"},
])
@pytest.mark.parametrize("method", ["GET", "POST", "OPTIONS"])
def test_cross_site_requests_are_blocked_before_dispatch(headers, method):
    response, called = request(headers=headers, method=method)
    assert response.status_code == 403 and not called


@pytest.mark.parametrize("host", ["evil.invalid:8000", "127.0.0.1.evil.invalid", "user@localhost:8000", "localhost:9999", "0.0.0.0:8000"])
def test_dns_rebinding_or_remote_hosts_rejected(host):
    response, called = request(host=host)
    assert response.status_code == 403 and not called


def test_remote_peer_is_denied_even_with_a_local_host_and_origin():
    response, called = request(peer="192.0.2.1", headers={"origin": "http://localhost:5173", "x-forwarded-for": "127.0.0.1"})
    assert response.status_code == 403 and not called


def test_local_cli_is_inside_single_user_boundary_not_a_user_identity():
    response, called = request()
    assert response.status_code == 200 and called


def test_preflight_from_legitimate_frontend():
    response, called = request(method="OPTIONS", headers={
        "origin": "http://localhost:5173", "access-control-request-method": "POST",
        "access-control-request-headers": "content-type",
    })
    assert response.status_code == 200 and not called


def test_websocket_with_foreign_origin_is_rejected():
    from study_engine.web.local_access import LocalAccessMiddleware
    sent = []

    async def forbidden(*args):
        raise AssertionError("must not dispatch")

    async def send(event):
        sent.append(event)

    asyncio.run(LocalAccessMiddleware(forbidden)({
        "type": "websocket", "client": ("127.0.0.1", 1234),
        "headers": [(b"host", b"localhost:8000"), (b"origin", b"https://evil.invalid")],
    }, None, send))
    assert sent == [{"type": "websocket.close", "code": 1008}]


def test_foreign_page_cannot_read_diagnostics_by_changing_session_id(monkeypatch):
    from types import SimpleNamespace
    from study_engine.utils.cache import TTLCache
    from study_engine.web.routes import evidence
    app = FastAPI()
    app.include_router(evidence.router)
    configure_local_access(app, perimeter_enabled=True)
    cache = TTLCache()
    cache["session-A"] = evidence.ClaimsVerificationResponse(
        session_id="session-A", verdict="REJECTED_UNSUPPORTED", claims=[]
    ).model_dump()
    monkeypatch.setattr(evidence, "_claims_cache", cache)

    async def provide():
        return SimpleNamespace()

    async def inline(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    app.dependency_overrides[evidence.get_container] = provide
    monkeypatch.setattr("fastapi.routing.run_in_threadpool", inline)
    monkeypatch.setattr("fastapi.dependencies.utils.run_in_threadpool", inline)

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000") as client:
            for session in ("session-A", "session-B"):
                result = await client.get(f"/api/evidence/claims/{session}", headers={"origin": "https://evil.invalid"})
                assert result.status_code == 403 and "verdict" not in result.json()
            # Local single-user access is not represented as per-user authorization.
            assert (await client.get("/api/evidence/claims/session-A")).status_code == 200
            assert (await client.get("/api/evidence/claims/session-B")).status_code == 404

    asyncio.run(run())
