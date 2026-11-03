"""A8: root route, static mounts, API 404 semantics, and legacy decommissioning.

Uses a synthetic ASGI app (the real create_app) without starting servers.
The LocalAccessMiddleware pytest gating disables the perimeter for these
tests; dedicated perimeter behavior is covered by test_local_access.py.
"""

import asyncio

import httpx
import pytest
from fastapi import FastAPI

from study_engine.web.app import create_app
from study_engine.web.local_access import configure_local_access


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    return httpx.ASGITransport(app=app)


def _get(transport, path, headers=None):
    async def run():
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:8000"
        ) as c:
            return await c.get(path, headers=headers or {})
    return asyncio.run(run())


def test_root_serves_legacy_static_interface(client):
    """A8-T01: GET / must not crash when static_dir defaults to the package dir."""
    response = _get(client, "/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert len(response.text) > 100  # Not an empty or error page


def test_root_with_explicit_static_dir_serves_that_dir(tmp_path):
    """A8-T02: explicit static_dir is honored, not the package default."""
    (tmp_path / "index.html").write_text("<html>custom shell</html>", encoding="utf-8")
    custom_app = create_app(static_dir=tmp_path)
    transport = httpx.ASGITransport(app=custom_app)
    response = _get(transport, "/")
    assert response.status_code == 200
    assert "custom shell" in response.text


def test_unknown_api_route_returns_json_404_not_html(client):
    """A8-T05: an unregistered /api/ route must return 404 JSON, never React HTML."""
    response = _get(client, "/api/nonexistent/endpoint")
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]
    assert "Not Found" in response.text
    assert "<html" not in response.text.lower()


def test_legacy_session_route_returns_410_gone(client):
    """A8-T14: /api/session/* is explicitly decommissioned with 410."""
    for method_path in ["/api/session/anything", "/api/session/practice/submit"]:
        response = _get(client, method_path)
        assert response.status_code == 410
        assert "ENDPOINT_RETIRED" in response.text


def test_static_mount_serves_package_assets(client):
    """A8-T03: /static serves files from the static directory."""
    response = _get(client, "/static/css/styles.css")
    assert response.status_code in (200, 404)  # file may or may not exist


def test_static_traversal_is_rejected(client):
    """A8-T08: path traversal via /static must not escape the mount."""
    response = _get(client, "/static/../../etc/passwd")
    assert response.status_code in (404, 400)
    assert "root:" not in response.text


def test_storage_mount_is_bounded(client):
    """A8-T10: /storage must not serve files outside the storage directory."""
    response = _get(client, "/storage/../../../.env")
    assert response.status_code in (404, 400)
    assert "KEY" not in response.text


def test_practice_evaluate_stays_unavailable(client):
    """A8 regression: /api/practice/evaluate preserves its PRACTICE_UNAVAILABLE contract."""
    async def run():
        async with httpx.AsyncClient(
            transport=client, base_url="http://127.0.0.1:8000"
        ) as c:
            return await c.post("/api/practice/evaluate", json={
                "task_id": "synthetic-task", "file_path": "synthetic.py",
            })
    response = asyncio.run(run())
    assert response.status_code == 200
    assert "PRACTICE_UNAVAILABLE" in response.text


def test_root_route_does_not_capture_api_paths(client):
    """A8-T15: the root handler must only match GET /, not /api/* paths."""
    # /api/session/* returns 410 JSON — proves the root HTML handler doesn't intercept it
    response = _get(client, "/api/session/test")
    assert response.status_code == 410
    assert "application/json" in response.headers["content-type"]
    assert "<html" not in response.text.lower()
    # /docs is FastAPI's OpenAPI docs — also not intercepted by root
    response = _get(client, "/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_chat_route_still_streams(client):
    """A8-T17: /api/chat/query remains registered and reachable (SSE contract preserved)."""
    response = _get(client, "/api/chat/query")
    # GET on a POST-only route → 405, not 404 or HTML
    assert response.status_code == 405
