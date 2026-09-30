import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Literal

import pytest
from playwright.sync_api import Page, Route, expect, sync_playwright


UI_ROOT = Path(__file__).resolve().parents[1]


def _wait_for_server(process: subprocess.Popen[str], url: str) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Vite exited before becoming ready")
        try:
            with socket.create_connection(("127.0.0.1", 4173), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError(f"Vite did not become ready at {url}")


@pytest.fixture(scope="module")
def ui_server():
    env = {**os.environ, "CI": "1"}
    process = subprocess.Popen(
        ["./node_modules/.bin/vite", "--host", "127.0.0.1", "--port", "4173", "--strictPort"],
        cwd=UI_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    url = "http://127.0.0.1:4173"
    try:
        _wait_for_server(process, url)
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def browser_page(ui_server: str):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.url.startswith("https://")
                else route.continue_(),
            )
            page.goto(ui_server, wait_until="domcontentloaded", timeout=15_000)
            expect(page).to_have_title("KASIU Core v0.3.0")
            expect(page.locator("#root > *")).to_have_count(1, timeout=15_000)
            yield page, page_errors
        finally:
            browser.close()


def _sse_event(event_type: str, payload: dict[str, object]) -> str:
    import json

    return f"data: {json.dumps({'event_type': event_type, 'payload': payload})}\n\n"


@pytest.mark.parametrize(
    ("outcome", "expected_text"),
    [
        ("success", "La consulta E2E llegó al endpoint simulado"),
        ("error", "Fallo simulado"),
        ("truncated", "La respuesta quedó truncada por límite de tokens"),
        ("aborted", "La generación se interrumpió antes de completarse"),
        ("incomplete", "La respuesta SSE terminó antes de completarse"),
    ],
)
def test_react_chat_consumes_mocked_sse(
    browser_page: tuple[Page, list[str]],
    outcome: Literal["success", "error", "truncated", "aborted", "incomplete"],
    expected_text: str,
) -> None:
    page, page_errors = browser_page
    chat_requests: list[dict[str, object]] = []

    def route_api(route: Route) -> None:
        request = route.request
        if request.url.endswith("/api/chat/query"):
            import json

            chat_requests.append(json.loads(request.post_data or "{}"))
            if outcome == "error":
                body = _sse_event("error", {"message": "Fallo simulado"})
            elif outcome == "truncated":
                body = "".join(
                    (
                        _sse_event("phase_token", {"token": "Respuesta parcial"}),
                        _sse_event(
                            "truncated",
                            {
                                "message": (
                                    "La respuesta quedó truncada por límite de tokens "
                                    "del proveedor."
                                )
                            },
                        ),
                    )
                )
            elif outcome == "aborted":
                body = "".join(
                    (
                        _sse_event("phase_token", {"token": "Respuesta parcial"}),
                        _sse_event(
                            "stream_aborted",
                            {"reason": "USER_ABORTED_OR_DISCONNECTED"},
                        ),
                    )
                )
            elif outcome == "incomplete":
                body = _sse_event("phase_token", {"token": "Respuesta parcial"})
            else:
                body = "".join(
                    (
                        _sse_event(
                            "phase_token",
                            {"token": "La consulta E2E llegó al endpoint simulado [E1]."},
                        ),
                        _sse_event(
                            "evidence_manifest",
                            {
                                "citations": [
                                    {
                                        "citation_id": "E1",
                                        "source_id": "fixture-source",
                                        "source_title": "Fuente de prueba E2E",
                                        "page": 7,
                                        "chunk_text": "Fragmento sintético de evidencia.",
                                        "doc_hash": "a" * 64,
                                    }
                                ]
                            },
                        ),
                        _sse_event("phase_complete", {}),
                    )
                )
            route.fulfill(
                status=200,
                content_type="text/event-stream",
                headers={"cache-control": "no-cache"},
                body=body,
            )
            return
        if request.url.endswith("/api/study/session/open"):
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"session_id":"e2e-session","episode_phase":"IDLE"}',
            )
            return
        route.fulfill(status=200, content_type="application/json", body="[]")

    page.route("**/api/**", route_api)
    page.get_by_text("Sistemas Operativos II", exact=False).click()
    query = "consulta de integración E2E"
    prompt = page.get_by_placeholder("Pregunta a TALOS o ingresa un comando socrático...")
    prompt.fill(query)
    prompt.press("Enter")

    expect(page.get_by_text(expected_text, exact=False)).to_be_visible(timeout=15_000)
    expect(page.get_by_text("En vivo", exact=True)).to_have_count(0)
    expect(page.get_by_label("Cargando respuesta...")).to_have_count(0)
    expect(page.get_by_placeholder("Pregunta a TALOS o ingresa un comando socrático...")).to_be_enabled()
    expect(page.get_by_text("Error de Comunicación Epistémica", exact=True)).to_have_count(
        0 if outcome == "success" else 1
    )
    if outcome in ("truncated", "aborted", "incomplete"):
        expect(page.get_by_text("Respuesta parcial", exact=False)).to_have_count(0)
    assert len(chat_requests) == 1
    assert chat_requests[0]["query"] == query
    assert chat_requests[0]["notebook_id"] == "fadena-so2"
    assert not page_errors, f"Uncaught browser errors: {page_errors}"

    if outcome == "success":
        expect(page.get_by_text("1 fuente consultada", exact=True)).to_be_visible()
        citation = page.get_by_role("button", name="[E1] p.7")
        expect(citation).to_be_visible()
        citation.click()
        citation_dialog = page.get_by_role("dialog")
        expect(citation_dialog).to_contain_text("Fuente de prueba E2E")
        expect(citation_dialog).to_contain_text("Fragmento sintético de evidencia.")
