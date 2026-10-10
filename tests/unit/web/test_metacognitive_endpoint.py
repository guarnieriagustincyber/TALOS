"""Tests de integración web para el endpoint y contexto metacognitivo (M3, M4, M6, M8)."""

import json
import logging
from fastapi.testclient import TestClient
import pytest

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.student.storage import StudentStorage
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(autouse=True)
def synthetic_admin_token(monkeypatch):
    monkeypatch.setenv("TALOS_ADMIN_TOKEN", "synthetic-admin-token-for-focused-tests-012345")


def test_endpoint_requires_admin_token_403_and_200(tmp_path):
    """M4: GET /api/student/metacognitive-profile requiere header X-Admin-Token."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    url = "/api/student/metacognitive-profile"

    # 1. Sin header: 403 Forbidden
    r_no_auth = client.get(url)
    assert r_no_auth.status_code == 403
    assert "X-Admin-Token" in r_no_auth.json()["detail"]

    # 2. Con token inválido: 403 Forbidden
    r_bad_auth = client.get(url, headers={"X-Admin-Token": "bad-secret-token"})
    assert r_bad_auth.status_code == 403

    # 3. Con token válido: 200 OK
    r_auth = client.get(
        url,
        headers={"X-Admin-Token": "synthetic-admin-token-for-focused-tests-012345"},
    )
    assert r_auth.status_code == 200
    data = r_auth.json()
    assert data["student_id"] == CANONICAL_STUDENT_ID
    assert "classification" in data
    assert "autonomy_score" in data
    assert "evasion_kcs" in data
    assert "overconfident_kcs" in data
    assert "scaffolding_directive_preview" in data


def test_metacognitive_endpoint_fails_closed_without_secure_configuration(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    monkeypatch.delenv("TALOS_ADMIN_TOKEN", raising=False)

    response = TestClient(app).get("/api/student/metacognitive-profile")

    assert response.status_code == 503


def test_chat_priority_struggle_over_metacognitive(tmp_path):
    """M8: Si el Protocolo de Lucha está activo (3+ fallos consecutivos), tiene prioridad absoluta y NO se inyecta metacognitiva."""
    from study_engine.web.routes.chat import _prepare_chat_context
    from study_engine.web.routes.chat import ChatQueryRequest

    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    db_file = tmp_path / "student_state.db"
    container.student_storage = StudentStorage(db_file)
    set_container(container)

    kc = "aritmetica_punteros"

    # Simular 3 fallos consecutivos en struggle_tracker
    struggle = container.struggle_tracker
    for _ in range(3):
        struggle.record(kc, False)
    assert struggle.is_struggling(kc) is True

    # Generar contexto de chat
    from study_engine.hierarchy.scope_resolver import ScopeResolver
    req = ChatQueryRequest(prompt=f"ayuda con {kc}", notebook_id="fase0-soc")
    store = container.knowledge_store
    resolver = ScopeResolver(store)
    result = _prepare_chat_context(
        store=store,
        resolver=resolver,
        container=container,
        prompt_text=req.prompt,
        request=req,
        target_scope_type="notebook",
        target_scope_id="fase0-soc",
    )

    # El paquete de contexto debe tener la directiva de struggle
    # y NO debe tener la directiva metacognitiva estándar
    bkt_dir = result[6]
    assert "PROTOCOLO DE LUCHA (STRUGGLE MODE)" in bkt_dir
    assert "DIRECTIVA METACOGNITIVA" not in bkt_dir


def test_chat_scaffolding_directive_injected_at_end_with_json_log(tmp_path, caplog):
    """M3 & M6: Cuando no hay struggle, se concatena directiva metacognitiva al final y emite log JSON."""
    from study_engine.hierarchy.scope_resolver import ScopeResolver
    from study_engine.web.routes.chat import _prepare_chat_context
    from study_engine.web.routes.chat import ChatQueryRequest

    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    db_file = tmp_path / "student_state.db"
    container.student_storage = StudentStorage(db_file)
    set_container(container)

    # Registrar datos de alta dependencia
    container.student_storage.record_exercise_attempt("ex_1", success=False, metadata={"kc_id": "punteros"})
    container.student_storage.log_solution_access("ex_1", forced=True, metadata={"kc_id": "punteros"})

    kc = "aritmetica_punteros"
    req = ChatQueryRequest(prompt=f"explica {kc}", notebook_id="fase0-soc")
    store = container.knowledge_store
    resolver = ScopeResolver(store)

    with caplog.at_level(logging.INFO):
        result = _prepare_chat_context(
            store=store,
            resolver=resolver,
            container=container,
            prompt_text=req.prompt,
            request=req,
            target_scope_type="notebook",
            target_scope_id="fase0-soc",
        )

    bkt_dir = result[6]
    # M3: Concatena al final
    assert "=== DIRECTIVA METACOGNITIVA:" in bkt_dir

    # M6: Log estructurado JSON emitido
    json_logs = []
    for record in caplog.records:
        try:
            parsed = json.loads(record.getMessage())
            if parsed.get("event") == "METACOGNITIVE_SCAFFOLDING":
                json_logs.append(parsed)
        except Exception:
            pass

    assert len(json_logs) >= 1
    ev = json_logs[0]
    assert ev["event"] == "METACOGNITIVE_SCAFFOLDING"
    assert ev["student_id"] == CANONICAL_STUDENT_ID
    assert "classification" in ev
    assert "ratio" in ev
    assert "autonomy_score" in ev
    assert ev["directive_injected"] is True
