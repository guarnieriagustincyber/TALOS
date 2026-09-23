"""Commit 2 — Verificación de no fuga de 'oracle' en HTTP y persistencia en SQLite.

Contrato:
- /api/student/exercises/generate/multi-kc, /debugging, /trace:
  Retornan HTTP 201 y el cuerpo NO contiene la clave 'oracle'.
- container.generated_registry.get(exercise_id) contiene el 'oracle' en SQLite.
- /api/chat/evaluate: evalúa exitosamente leyendo de SQLite (status=GRADED).
- Post-restart / ID desconocido: evalúa fail-closed (status=UNGRADED) sin mutar BKT.
- Post-restart con la misma BD SQLite: el ejercicio persiste y se evalúa exitosamente.
"""

from fastapi.testclient import TestClient

from study_engine.pedagogy.generated_registry import GeneratedExerciseRegistry
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def test_generation_endpoints_do_not_leak_oracle(tmp_path):
    """Los endpoints de generación devuelven 201 sin la clave 'oracle'."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    # 1. Multi-KC
    r_multi = client.post(
        "/api/student/exercises/generate/multi-kc",
        json={"kc_ids": ["punteros", "memoria"]},
    )
    assert r_multi.status_code == 201, r_multi.text
    multi_data = r_multi.json()
    assert "oracle" not in multi_data
    assert "exercise_id" in multi_data
    multi_ex_id = multi_data["exercise_id"]

    # Verificar que el oracle sí está en SQLite
    persisted_multi = container.generated_registry.get(multi_ex_id)
    assert persisted_multi is not None
    assert "oracle" in persisted_multi
    assert persisted_multi["oracle"]["type"] == "keyword_coverage"

    # 2. Debugging
    r_debug = client.post(
        "/api/student/exercises/generate/debugging",
        json={"kc_id": "punteros", "bug_type": "buffer_overflow"},
    )
    assert r_debug.status_code == 201, r_debug.text
    debug_data = r_debug.json()
    assert "oracle" not in debug_data
    assert "exercise_id" in debug_data
    debug_ex_id = debug_data["exercise_id"]

    persisted_debug = container.generated_registry.get(debug_ex_id)
    assert persisted_debug is not None
    assert "oracle" in persisted_debug
    assert persisted_debug["oracle"]["cwe"] == "CWE-120"

    # 3. Trace
    r_trace = client.post(
        "/api/student/exercises/generate/trace",
        json={"kc_id": "punteros", "n_mutations": 2},
    )
    assert r_trace.status_code == 201, r_trace.text
    trace_data = r_trace.json()
    assert "oracle" not in trace_data
    assert "exercise_id" in trace_data
    trace_ex_id = trace_data["exercise_id"]

    persisted_trace = container.generated_registry.get(trace_ex_id)
    assert persisted_trace is not None
    assert "oracle" in persisted_trace
    assert "final_state" in persisted_trace["oracle"]


def test_evaluate_uses_sqlite_persisted_oracle(tmp_path):
    """POST /api/chat/evaluate lee el oracle desde SQLite y califica."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    # Generar ejercicio de debugging
    r_gen = client.post(
        "/api/student/exercises/generate/debugging",
        json={"kc_id": "punteros", "bug_type": "buffer_overflow"},
    )
    assert r_gen.status_code == 201
    ex_id = r_gen.json()["exercise_id"]

    # Calificar con respuesta correcta
    r_eval_good = client.post(
        "/api/chat/evaluate",
        json={"exercise_id": ex_id, "user_answer": "Es un buffer overflow clásico en strcpy"},
    )
    assert r_eval_good.status_code == 200
    res_good = r_eval_good.json()
    assert res_good["status"] == "GRADED"
    assert res_good["is_correct"] is True
    assert res_good["source"] == "generated"
    assert res_good["p_L"] is not None

    # Calificar con respuesta incorrecta
    r_eval_bad = client.post(
        "/api/chat/evaluate",
        json={"exercise_id": ex_id, "user_answer": "Es un error de compilación de sintaxis"},
    )
    assert r_eval_bad.status_code == 200
    res_bad = r_eval_bad.json()
    assert res_bad["status"] == "GRADED"
    assert res_bad["is_correct"] is False


def test_post_restart_unknown_evaluates_ungraded_fail_closed(tmp_path):
    """Ejercicio desconocido o tras reinicio sin persistencia da UNGRADED y no muta BKT."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    kc = "punteros"
    prior_p_l = container.bkt_tracker.get_state(kc).p_L

    r_unknown = client.post(
        "/api/chat/evaluate",
        json={"exercise_id": "gen_inexistente_9999", "user_answer": "buffer overflow"},
    )
    assert r_unknown.status_code == 200
    data = r_unknown.json()
    assert data["status"] == "UNGRADED"
    assert data["is_correct"] is None
    assert container.bkt_tracker.get_state(kc).p_L == prior_p_l


def test_post_restart_with_persisted_sqlite_db(tmp_path):
    """Simular reinicio del servidor: un nuevo container con el mismo student_state.db evalúa con éxito."""
    db_file = tmp_path / "student_state.db"

    # Primer ciclo de vida
    app1 = create_app()
    container1 = AppContainer(working_dir=tmp_path, use_mock=True)
    container1.student_storage = StudentStorage(db_file)
    container1.generated_registry = GeneratedExerciseRegistry(container1.student_storage)
    container1.bkt_tracker = BKTTracker(container1.student_storage)
    set_container(container1)
    client1 = TestClient(app1)

    r_gen = client1.post(
        "/api/student/exercises/generate/debugging",
        json={"kc_id": "punteros", "bug_type": "use_after_free"},
    )
    assert r_gen.status_code == 201
    ex_id = r_gen.json()["exercise_id"]

    # Simular reinicio del proceso cargando un container nuevo sobre el mismo archivo SQLite
    app2 = create_app()
    container2 = AppContainer(working_dir=tmp_path, use_mock=True)
    container2.student_storage = StudentStorage(db_file)
    container2.generated_registry = GeneratedExerciseRegistry(container2.student_storage)
    container2.bkt_tracker = BKTTracker(container2.student_storage)
    set_container(container2)
    client2 = TestClient(app2)

    # El registro generado debe poder leerlo de la base SQLite persistida
    persisted = container2.generated_registry.get(ex_id)
    assert persisted is not None
    assert persisted["oracle"]["cwe"] == "CWE-416"

    # Y la evaluación funciona sin problemas
    r_eval = client2.post(
        "/api/chat/evaluate",
        json={"exercise_id": ex_id, "user_answer": "Es un use after free (CWE-416)"},
    )
    assert r_eval.status_code == 200
    res = r_eval.json()
    assert res["status"] == "GRADED"
    assert res["is_correct"] is True


def test_generation_endpoints_authenticated_oracle_inspection_a4(tmp_path):
    """Requerimiento A4: include_oracle=true requiere header X-Admin-Token (403 sin él, 201 con él)."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    endpoints = [
        ("/api/student/exercises/generate/multi-kc", {"kc_ids": ["punteros", "memoria"]}),
        ("/api/student/exercises/generate/debugging", {"kc_id": "punteros", "bug_type": "buffer_overflow"}),
        ("/api/student/exercises/generate/trace", {"kc_id": "punteros", "n_mutations": 2}),
    ]

    for url, body in endpoints:
        # 1. Sin query param: 201 y 0 leakage
        r_def = client.post(url, json=body)
        assert r_def.status_code == 201
        assert "oracle" not in r_def.json()

        # 2. Con include_oracle=true pero SIN token: 403 Forbidden
        r_unauth = client.post(f"{url}?include_oracle=true", json=body)
        assert r_unauth.status_code == 403, f"{url} debió responder 403 sin token"
        assert "X-Admin-Token" in r_unauth.json()["detail"]

        # 3. Con include_oracle=true y token erróneo: 403 Forbidden
        r_bad = client.post(
            f"{url}?include_oracle=true",
            json=body,
            headers={"X-Admin-Token": "token-invalido-xyz"},
        )
        assert r_bad.status_code == 403

        # 4. Con include_oracle=true y token válido: 201 Created CON oracle
        r_auth = client.post(
            f"{url}?include_oracle=true",
            json=body,
            headers={"X-Admin-Token": "talos-admin-secret-dev"},
        )
        assert r_auth.status_code == 201
        data = r_auth.json()
        assert "oracle" in data
        assert isinstance(data["oracle"], dict)


def test_multikc_bkt_updates_all_kcs_and_records_attempt_a5(tmp_path):
    """Requerimiento A5: actualización de BKT a través de TODOS los kc_ids y persistencia de intento."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    db_file = tmp_path / "student_state.db"
    container.student_storage = StudentStorage(db_file)
    container.generated_registry = GeneratedExerciseRegistry(container.student_storage)
    container.bkt_tracker = BKTTracker(container.student_storage)
    set_container(container)
    client = TestClient(app)

    kc1 = "punteros"
    kc2 = "memoria"

    # Generar multi-kc exercise
    r_gen = client.post(
        "/api/student/exercises/generate/multi-kc?include_oracle=true",
        json={"kc_ids": [kc1, kc2]},
        headers={"X-Admin-Token": "talos-admin-secret-dev"},
    )
    assert r_gen.status_code == 201
    ex = r_gen.json()
    ex_id = ex["exercise_id"]

    # Verificar que inicialmente no hay intentos
    assert not container.student_storage.has_exercise_attempt(ex_id)
    assert container.bkt_tracker.get_state(kc1).attempts == 0
    assert container.bkt_tracker.get_state(kc2).attempts == 0

    # Calificar respuesta correcta
    sol = "Reservo la copia con malloc en el heap, verifico null y el caller debe liberar con free"
    r_eval = client.post(
        "/api/chat/evaluate",
        json={"exercise_id": ex_id, "user_answer": sol},
    )
    assert r_eval.status_code == 200
    res = r_eval.json()
    assert res["status"] == "GRADED"
    assert res["is_correct"] is True

    # A5: Ambos KCs deben haberse actualizado en BKT
    assert kc1 in res["bkt_updates"]
    assert kc2 in res["bkt_updates"]
    assert container.bkt_tracker.get_state(kc1).attempts == 1
    assert container.bkt_tracker.get_state(kc2).attempts == 1

    # A5: Intento forense persistido en SQLite student_exercise_attempts
    assert container.student_storage.has_exercise_attempt(ex_id)


def test_trace_x86_generation_and_evaluation(tmp_path):
    """Verifica generación de Trace Table x86 y su evaluación determinista."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    client = TestClient(app)

    # Generación con arch='x86'
    r_gen = client.post(
        "/api/student/exercises/generate/trace?include_oracle=true",
        json={"kc_id": "arquitectura_computadores", "arch": "x86"},
        headers={"X-Admin-Token": "talos-admin-secret-dev"},
    )
    assert r_gen.status_code == 201
    ex = r_gen.json()
    assert "x86-64" in ex["prompt"]
    assert ex["oracle"]["architecture"] == "x86-64"

    # Preparar respuesta canónica leyendo el oracle admin
    final_state = ex["oracle"]["final_state"]
    ans = ", ".join(f"{k}={v}" for k, v in final_state.items())

    # Evaluar vía endpoint
    r_eval = client.post(
        "/api/chat/evaluate",
        json={"exercise_id": ex["exercise_id"], "user_answer": ans},
    )
    assert r_eval.status_code == 200
    res = r_eval.json()
    assert res["status"] == "GRADED"
    assert res["is_correct"] is True

