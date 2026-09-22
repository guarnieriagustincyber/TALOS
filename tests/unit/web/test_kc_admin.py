"""Fase 5.1 — Gestión manual de KCs: endpoints + persistencia + match BKT.

Contratos:
- GET /api/notebooks/{id}/curriculum: lista vacía si no hay KCs (no error).
- POST .../knowledge-components: crea, persiste en notebook_kcs, 409 si dupe.
- El KC manual entra al catálogo efectivo -> el matcher de chat lo resuelve
  ("el BKT ahora puede matchear el KC nuevo").
- GET /api/student/exercises/available responde con esquema esperado.
"""

import json

from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container
from study_engine.web.routes.chat import _match_kc_id


def _fresh_container(tmp_path):
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    return app, container


def test_curriculum_endpoint_lista_vacia_si_no_hay_kcs(tmp_path):
    app, _ = _fresh_container(tmp_path)
    client = TestClient(app)
    r = client.get("/api/notebooks/nb-vacio/curriculum")
    assert r.status_code == 200
    body = r.json()
    assert body["notebook_id"] == "nb-vacio"
    assert body["total"] == 0 and body["kcs"] == []


def test_creacion_manual_y_lectura_posterior(tmp_path):
    app, container = _fresh_container(tmp_path)
    client = TestClient(app)

    # El cuaderno fase0-soc existe (seed canónico del container)
    r = client.get("/api/notebooks/fase0-soc/curriculum")
    assert r.status_code == 200
    base_total = r.json()["total"]

    r = client.post(
        "/api/notebooks/fase0-soc/knowledge-components",
        json={
            "kc_id": "so_planificacion_cpu",
            "title": "Planificación de CPU: SJF, Round Robin y prioridades",
            "prerequisites": ["fase0_tramo2_logica_control"],
            "subtopics": ["SJF apropiativo y no apropiativo", "quantum y context switch"],
            "estimated_time": 90,
            "difficulty": "intermedio",
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["kc_id"] == "so_planificacion_cpu"

    # Lectura posterior: aparece en el curriculum con status BKT
    r = client.get("/api/notebooks/fase0-soc/curriculum")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == base_total + 1
    mine = [k for k in body["kcs"] if k["kc_id"] == "so_planificacion_cpu"]
    assert mine and mine[0]["difficulty"] == "intermedio"
    assert mine[0]["status"] in ("not_started", "in_progress", "mastered")

    # Persistencia real en la DB (relectura cruda)
    conn = container.knowledge_store.engine.connect()
    row = conn.execute(
        "SELECT title, difficulty FROM notebook_kcs WHERE kc_id = ? AND notebook_id = ?",
        ("so_planificacion_cpu", "fase0-soc"),
    ).fetchone()
    conn.close()
    assert row and "Planificación de CPU" in row[0]


def test_idempotencia_duplicado_da_409_sin_duplicar(tmp_path):
    app, container = _fresh_container(tmp_path)
    client = TestClient(app)

    payload = {"kc_id": "so_deadlocks", "title": "Deadlocks y condiciones de Coffman"}
    r1 = client.post("/api/notebooks/fase0-soc/knowledge-components", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/notebooks/fase0-soc/knowledge-components", json=payload)
    assert r2.status_code == 409

    conn = container.knowledge_store.engine.connect()
    n = conn.execute(
        "SELECT COUNT(*) FROM notebook_kcs WHERE kc_id = 'so_deadlocks'"
    ).fetchone()[0]
    conn.close()
    assert n == 1


def test_bkt_matcher_matchea_kc_manual_recien_creado(tmp_path):
    app, container = _fresh_container(tmp_path)
    client = TestClient(app)
    r = client.post(
        "/api/notebooks/fase0-soc/knowledge-components",
        json={
            "kc_id": "so_memoria_virtual",
            "title": "Memoria Virtual y paginación",
            "subtopics": ["page fault", "working set"],
        },
    )
    assert r.status_code == 201

    # El catálogo en memoria quedó refrescado; el matcher del chat lo resuelve.
    kcs = container.pedagogical_orchestrator._kc_catalog["fase0-soc"]["kcs"]
    assert _match_kc_id(kcs, "¿cómo funciona la paginación con memoria virtual?") == "so_memoria_virtual"


def test_exercises_available_esquema_y_failclosed(tmp_path):
    app, _ = _fresh_container(tmp_path)
    client = TestClient(app)
    r = client.get("/api/student/exercises/available", params={"notebook_id": "fase0-soc"})
    assert r.status_code == 200
    body = r.json()
    assert body["notebook_id"] == "fase0-soc"
    assert isinstance(body["exercises"], list)
    for item in body["exercises"]:
        assert set(item) == {"exercise_id", "kc_id", "title", "type", "difficulty"}


def test_kc_validaciones_de_formato(tmp_path):
    app, _ = _fresh_container(tmp_path)
    client = TestClient(app)
    r = client.post(
        "/api/notebooks/fase0-soc/knowledge-components",
        json={"kc_id": "KC Invalido!!", "title": "mal"},
    )
    assert r.status_code == 422
    r = client.post(
        "/api/notebooks/fase0-soc/knowledge-components",
        json={"kc_id": "ok_kc", "title": "difficulty invalida", "difficulty": "easy"},
    )
    assert r.status_code == 422


def test_404_si_notebook_no_existe(tmp_path):
    app, _ = _fresh_container(tmp_path)
    client = TestClient(app)
    r = client.post(
        "/api/notebooks/nb_inexistente/knowledge-components",
        json={"kc_id": "x_ok", "title": "algo válido"},
    )
    assert r.status_code == 404
