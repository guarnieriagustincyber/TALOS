"""Integration test suite for KASIU Web API and REST Endpoints (Hito 10 - Fase 1).

Validates all required endpoints:
- GET  /
- GET  /api/health
- GET  /api/curriculum/roadmap
- GET  /api/curriculum/nodes/{node_id}
- GET  /api/student/cognitive-state
- GET  /api/student/spaced-repetition/due
- POST /api/session/start
- POST /api/session/turn/conceptual
"""

from typing import Generator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(scope="module")
def api_client(web_state_test_copy: Path) -> Generator[TestClient, None, None]:
    """Provide a TestClient bound to a deterministic, mock-enabled test container."""
    container = AppContainer(working_dir=web_state_test_copy, use_mock=True)
    set_container(container)
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_index_route(api_client: TestClient) -> None:
    """Verify GET / serves the SPA shell with dark theme and interactive tabs."""
    res = api_client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "KASIU Study Engine" in res.text
    assert "mermaid.min.js" in res.text
    assert "tab-btn-study" in res.text


def test_static_assets_offline_delivery(api_client: TestClient) -> None:
    """Verify that all vendor and app assets are delivered offline from /static/."""
    assets = [
        "/static/css/app.css",
        "/static/js/app.js",
        "/static/js/chat.js",
        "/static/js/followup.js",
        "/static/js/practice.js",
        "/static/js/dag.js",
        "/static/vendor/mermaid.min.js",
        "/static/vendor/marked.min.js",
        "/static/vendor/dompurify.min.js",
    ]
    for asset_path in assets:
        res = api_client.get(asset_path)
        assert res.status_code == 200, f"Asset {asset_path} failed to load: {res.status_code}"
        assert len(res.content) > 0


def test_health_endpoint(api_client: TestClient) -> None:
    """Verify GET /api/health exposes accurate component diagnostics and frozen perimeter status."""
    res = api_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "healthy"
    assert data["frozen_perimeter"] == "INTACT"
    assert data["test_suite"]["total"] >= 1478
    assert data["test_suite"]["passed"] >= 1478

    components = data["components"]
    assert components["curriculum"]["status"] == "ok"
    assert components["curriculum"]["nodes_loaded"] == 6
    assert components["ledger"]["status"] == "ok"
    assert components["ledger"]["integrity"] == "VALID"
    assert components["sandbox"]["tier"] == 0


def test_curriculum_roadmap_endpoint(api_client: TestClient) -> None:
    """Verify GET /api/curriculum/roadmap returns nodes, edges, and valid Mermaid markup."""
    res = api_client.get("/api/curriculum/roadmap")
    assert res.status_code == 200
    data = res.json()

    assert data["roadmap_id"] == "ROADMAP-CYBERSECURITY-V1"
    assert len(data["nodes"]) == 6

    # Verify Mermaid markup generation
    mermaid = data["mermaid_source"]
    assert "graph TD" in mermaid
    assert "classDef assessed_proficient" in mermaid
    assert "classDef available" in mermaid
    assert "classDef locked" in mermaid

    # Verify node structure
    root_nodes = [n for n in data["nodes"] if n["is_root"]]
    assert len(root_nodes) >= 1
    assert any(n["node_id"] == "SEC-01-C-PTR" for n in data["nodes"])


def test_curriculum_roadmap_notebook_scoped(api_client: TestClient) -> None:
    """Verify GET /api/curriculum/roadmap?notebook_id=... returns scoped KCs and graph."""
    res = api_client.get("/api/curriculum/roadmap?notebook_id=fadena-teleco")
    assert res.status_code == 200
    data = res.json()

    assert data["roadmap_id"] == "fadena_teleco_2025"
    assert "Infraestructura de Telecomunicaciones" in data["title"]
    assert len(data["nodes"]) == 12
    assert any(n["node_id"] == "teleco_transmision_datos" for n in data["nodes"])
    assert any(n["node_id"] == "teleco_parametros_senales" for n in data["nodes"])
    
    # Verify Mermaid markup for notebook
    mermaid = data["mermaid_source"]
    assert "graph TD" in mermaid
    assert "teleco_transmision_datos" in mermaid


def test_curriculum_node_detail_endpoint(api_client: TestClient) -> None:
    """Verify GET /api/curriculum/nodes/{node_id} for existing and non-existing nodes."""
    # Existing node
    res = api_client.get("/api/curriculum/nodes/SEC-01-C-PTR")
    assert res.status_code == 200
    node = res.json()
    assert node["node_id"] == "SEC-01-C-PTR"
    assert "Punteros" in node["title"]
    assert node["status"] in ("AVAILABLE", "IN_PROGRESS", "ASSESSED_PROFICIENT")
    assert len(node["authorized_sources"]) >= 1

    # Non-existent node -> 404
    res_404 = api_client.get("/api/curriculum/nodes/NON-EXISTENT-NODE")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()


def test_student_cognitive_state_endpoint(api_client: TestClient) -> None:
    """Verify GET /api/student/cognitive-state returns real BKT state and active alerts (Fix 3.3)."""
    res = api_client.get("/api/student/cognitive-state")
    assert res.status_code == 200
    state = res.json()
    assert "student_id" in state
    assert "kc_mastery" in state
    assert "active_alerts" in state


def test_student_spaced_repetition_endpoint(api_client: TestClient) -> None:
    """Verify GET /api/student/spaced-repetition/due returns SM-2 schedule (Fix 3.3)."""
    res = api_client.get("/api/student/spaced-repetition/due")
    assert res.status_code == 200
    due_data = res.json()
    assert isinstance(due_data, list)


def test_pedagogy_episode_start_endpoint(api_client: TestClient) -> None:
    """Verify POST /api/pedagogy/episode/start sets active episode with validated KC (Equivalente E19)."""
    # Successful start with authorized KC
    res = api_client.post(
        "/api/pedagogy/episode/start",
        json={
            "notebook_id": "fadena-lenguajes",
            "kc_id": "leng_intro_algoritmos",
        },
    )
    assert res.status_code == 200
    episode_data = res.json()

    assert episode_data["notebook_id"] == "fadena-lenguajes"
    assert episode_data["kc_id"] == "leng_intro_algoritmos"
    assert "episode_id" in episode_data
    assert episode_data["phase"] == "EXPLAINING"
    assert episode_data["current_step_id"] == "step_concept"

    # Invalid KC -> 400 Bad Request
    res_invalid = api_client.post(
        "/api/pedagogy/episode/start",
        json={
            "notebook_id": "fadena-lenguajes",
            "kc_id": "NON_EXISTENT_KC",
        },
    )
    assert res_invalid.status_code == 400
    assert "Rechazo formal de episodio" in res_invalid.json()["detail"]


def test_chat_query_conceptual_streaming_endpoint(api_client: TestClient) -> None:
    """Verify POST /api/chat/query executes streaming socratic turn with evidence manifest (Equivalente E19)."""
    turn_res = api_client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Qué es un puntero en lenguaje C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "requested_phase": "conceptual",
            "session_id": "sess-student-study-loop-v1",
        },
    )
    assert turn_res.status_code == 200
    assert "text/event-stream" in turn_res.headers["content-type"]

    import json
    lines = [line.strip() for line in turn_res.text.split("\n") if line.startswith("data: ")]
    assert len(lines) > 0
    events = [json.loads(line[6:]) for line in lines]
    event_types = [e["event_type"] for e in events]

    assert "phase_start" in event_types
    assert "phase_complete" in event_types

    # Invariant: Phase complete reports valid phase and permissible next phases
    complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert complete_ev["payload"]["completed_phase"] == "conceptual"
    assert isinstance(complete_ev["payload"]["next_phases"], list)


def test_multi_turn_conversational_flow(api_client: TestClient) -> None:
    """Verify multi-turn conversational progression on /api/chat/query preserving active history (Equivalente E19)."""
    import json
    session_id = "sess-multi-turn-test-123"

    # Turn 1: Basic conceptual question
    turn1_res = api_client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Qué es un puntero en lenguaje C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "requested_phase": "conceptual",
            "session_id": session_id,
        },
    )
    assert turn1_res.status_code == 200
    lines1 = [l.strip() for l in turn1_res.text.split("\n") if l.startswith("data: ")]
    events1 = [json.loads(l[6:]) for l in lines1]
    tokens1 = "".join([e["payload"]["token"] for e in events1 if e["event_type"] == "phase_token"])
    assert len(tokens1) > 10

    # Turn 2: Follow-up deepening question
    turn2_res = api_client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cómo funciona la aritmética de punteros?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "requested_phase": "pseudocode",
            "session_id": session_id,
        },
    )
    assert turn2_res.status_code == 200
    lines2 = [l.strip() for l in turn2_res.text.split("\n") if l.startswith("data: ")]
    events2 = [json.loads(l[6:]) for l in lines2]
    event_types2 = [e["event_type"] for e in events2]
    assert "phase_start" in event_types2
    assert "phase_complete" in event_types2


def test_socratic_practice_request_abstains_without_evidence(api_client: TestClient) -> None:
    """Verify unsupported practice requests terminate as pedagogical abstentions."""
    import json
    res = api_client.post(
        "/api/chat/query",
        json={
            "prompt": "/practicar punteros",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": "sess-test-practice-dispatch",
        },
    )
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]
    assert [event["event_type"] for event in events] == [
        "evidence_manifest",
        "abstention",
    ]
    assert events[0]["payload"]["abstained"] is True
    assert events[1]["payload"]["abstained"] is True
    assert events[1]["payload"]["abstention_code"] == "QUERY_OUT_OF_SCOPE"


def test_practice_evaluate_endpoint(api_client: TestClient) -> None:
    """Verify POST /api/practice/evaluate handles code submission in sandbox (Equivalente E19)."""
    res = api_client.post(
        "/api/practice/evaluate",
        json={
            "task_id": "task-punteros-swap-01",
            "file_path": "src/exercises/swap.py",
            "command": ":eval",
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["task_id"] == "task-punteros-swap-01"
    assert "status" in data
    assert "assertions" in data
    assert "stdout" in data
    assert "execution_time_ms" in data


def test_session_endpoints_decommissioned_return_410_gone(api_client: TestClient) -> None:
    """Verify all legacy /api/session/* endpoints return HTTP 410 Gone (Fase 4.2 & E20)."""
    # 1. POST /api/session/start
    start_res = api_client.post("/api/session/start", json={"node_id": "c-basics"})
    assert start_res.status_code == 410
    start_data = start_res.json()
    assert start_data["error"] == "ENDPOINT_RETIRED"
    assert "docs/api_migration_session_to_chat.md" in start_data["migration_guide"]

    # 2. POST /api/session/turn/conceptual
    turn_res = api_client.post(
        "/api/session/turn/conceptual",
        json={"session_id": "sess-123", "student_message": "Hola"},
    )
    assert turn_res.status_code == 410
    turn_data = turn_res.json()
    assert turn_data["error"] == "ENDPOINT_RETIRED"

    # 3. GET /api/session/practice/task
    task_res = api_client.get("/api/session/practice/task?node_id=c-basics")
    assert task_res.status_code == 410
    assert task_res.json()["error"] == "ENDPOINT_RETIRED"

    # 4. POST /api/session/practice/submit
    submit_res = api_client.post(
        "/api/session/practice/submit",
        json={"session_id": "sess-123", "node_id": "c-basics", "code": "int main(){}"},
    )
    assert submit_res.status_code == 410
    assert submit_res.json()["error"] == "ENDPOINT_RETIRED"
