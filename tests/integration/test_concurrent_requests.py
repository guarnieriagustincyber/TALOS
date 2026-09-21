"""Integration test for concurrent requests to verify non-blocking execution (Ola 4)."""

import asyncio
import json
from typing import Any, List
import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.mark.integration
def test_concurrent_llm_calls() -> None:
    """Verificar que múltiples requests concurrentes a /api/chat/query no bloquean el servidor ni el event loop."""
    container = AppContainer(use_mock=True)
    set_container(container)
    app = create_app()

    with TestClient(app) as client:
        # Simular 5 requests conceptuales concurrentes sobre el endpoint canónico de chat SSE
        async def make_requests() -> List[Any]:
            tasks = [
                asyncio.to_thread(
                    client.post,
                    "/api/chat/query",
                    json={
                        "prompt": "¿Qué es un puntero en lenguaje C?",
                        "scope_type": "notebook",
                        "scope_id": "fadena-lenguajes",
                        "requested_phase": "conceptual",
                        "session_id": f"sess-test-concurrent-{i}",
                    },
                )
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks)
            return responses

        responses = asyncio.run(make_requests())
        assert len(responses) == 5
        assert all(r.status_code == 200 for r in responses)
        assert all("text/event-stream" in r.headers["content-type"] for r in responses)

        for r in responses:
            lines = [line.strip() for line in r.text.split("\n") if line.startswith("data: ")]
            assert len(lines) > 0
            events = [json.loads(line[6:]) for line in lines]
            event_types = [e["event_type"] for e in events]
            assert "phase_start" in event_types
            assert "phase_complete" in event_types
