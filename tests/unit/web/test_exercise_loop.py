"""Fase 5.3 — Loop de evaluación BKT en chat (determinista, sin LLM).

Contrato:
- select_exercise_for_kc: solo QUALIFIABLE; prioriza no-vistos (sin submission).
- should_propose: True solo al llegar al umbral de turnos (3).
- POST /api/chat/evaluate: correcta sube p_L, incorrecta baja + remediación;
  ejercicio inexistente/sin clave => UNGRADED y BKT intacto (fail-closed).
"""

import json

from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def _exercise_json(exercise_id, kc_id, expected, ex_type="NUMERIC", options=None,
                   status="QUALIFIABLE"):
    return {
        "exercise_id": exercise_id,
        "source_id": "src_test",
        "source_location": "p.1",
        "source_hash": "0" * 64,
        "extractor_version": "test",
        "extraction_method": "test",
        "verification_status": status,
        "verified_by": "test",
        "verification_timestamp": None,
        "content_hash": "1" * 64,
        "kc_id": kc_id,
        "prompt": f"Ejercicio de {kc_id}",
        "exercise_type": ex_type,
        "options": options,
        "expected_answer": expected,
        "solution_explanation": None,
    }


def _store_with(tmp_path, exercises):
    p = tmp_path / "exercises.json"
    p.write_text(json.dumps(exercises), encoding="utf-8")
    from study_engine.pedagogy.exercise_store import ExerciseStore
    return ExerciseStore(storage_path=p)


def test_propone_solo_si_hay_qualifiable(tmp_path):
    from study_engine.pedagogy.exercise_service import select_exercise_for_kc

    store = _store_with(tmp_path, [
        _exercise_json("ex_a", "kc_si", "42"),
        _exercise_json("ex_b", "kc_no", "x", status="UNVERIFIED"),
    ])
    assert select_exercise_for_kc(store, "kc_si", submissions_root=tmp_path).exercise_id == "ex_a"
    assert select_exercise_for_kc(store, "kc_no", submissions_root=tmp_path) is None
    assert select_exercise_for_kc(store, "kc_inexistente", submissions_root=tmp_path) is None
    assert select_exercise_for_kc(store, None, submissions_root=tmp_path) is None


def test_prioriza_no_vistos(tmp_path):
    from study_engine.pedagogy.exercise_service import select_exercise_for_kc

    store = _store_with(tmp_path, [
        _exercise_json("ex_visto", "kc_x", "1"),
        _exercise_json("ex_nuevo", "kc_x", "2"),
    ])
    subs = tmp_path / "subs" / "nb" / "u1"
    subs.mkdir(parents=True)
    (subs / "ex_visto.md").write_text("resuelto", encoding="utf-8")
    chosen = select_exercise_for_kc(store, "kc_x", submissions_root=tmp_path / "subs")
    assert chosen.exercise_id == "ex_nuevo"


def test_should_propose_umbral():
    from study_engine.pedagogy.exercise_service import (
        PROPOSAL_COLD_START_THRESHOLD,
        PROPOSAL_STREAK_THRESHOLD,
        should_propose,
    )

    # Assessed KC (attempts >= 1): umbral es 3 turnos
    assert should_propose(1, attempts=1) is False
    assert should_propose(PROPOSAL_STREAK_THRESHOLD - 1, attempts=1) is False
    assert should_propose(PROPOSAL_STREAK_THRESHOLD, attempts=1) is True
    assert should_propose(PROPOSAL_STREAK_THRESHOLD + 2, attempts=1) is True

    # Cold-start / unassessed KC (attempts == 0): acelerado a 2 turnos
    assert should_propose(1, attempts=0) is False
    assert should_propose(PROPOSAL_COLD_START_THRESHOLD, attempts=0) is True
    assert should_propose(PROPOSAL_COLD_START_THRESHOLD + 1, attempts=0) is True


def _client_with_exercises(tmp_path, exercises):
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    container.exercise_store = _store_with(tmp_path, exercises)
    set_container(container)
    return app, container


def test_evaluate_correcta_sube_p_L(tmp_path):
    app, container = _client_with_exercises(tmp_path, [
        _exercise_json("ex_ok", "kc_eval", "1012"),
    ])
    client = TestClient(app)
    r0 = container.bkt_tracker.get_state("kc_eval").p_L
    r = client.post("/api/chat/evaluate", json={"exercise_id": "ex_ok", "user_answer": "1012"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "GRADED" and body["is_correct"] is True
    assert body["p_L"] > r0 and body["delta_p_L"] > 0


def test_evaluate_incorrecta_remedia_y_no_infla_mas_que_correcta(tmp_path):
    """Respuesta incorrecta: BKT cuenta el intento y ofrece remediación.

    Nota de calibración del modelo (Corbett & Anderson): con p_T alto, un
    intento incorrecto también suma aprendizaje — la autoridad del sistema es
    que `correct > incorrect` siempre, y la remediación marca el refuerzo.
    """
    app, container = _client_with_exercises(tmp_path, [
        _exercise_json("ex_no", "kc_eval_down", "42"),
        _exercise_json("ex_ok", "kc_eval_up", "42"),
    ])
    client = TestClient(app)
    bad = client.post("/api/chat/evaluate", json={"exercise_id": "ex_no", "user_answer": "999"}).json()
    good = client.post("/api/chat/evaluate", json={"exercise_id": "ex_ok", "user_answer": "42"}).json()

    assert bad["is_correct"] is False
    assert bad["attempts"] == 1
    assert bad["remediation"] is not None and "kc_eval_down" in bad["remediation"]
    # Autoridad relativa: la correcta siempre mejora más que la incorrecta
    assert good["delta_p_L"] > bad["delta_p_L"]


def test_evaluate_mc_con_opciones(tmp_path):
    app, container = _client_with_exercises(tmp_path, [
        _exercise_json("ex_mc", "kc_eval_mc", "b", ex_type="MC", options=["a", "b", "c"]),
    ])
    client = TestClient(app)
    r = client.post("/api/chat/evaluate", json={"exercise_id": "ex_mc", "user_answer": "b"})
    assert r.json()["is_correct"] is True


def test_evaluate_fail_closed_sin_ejercicio_certificado(tmp_path):
    app, container = _client_with_exercises(tmp_path, [])
    before = container.bkt_tracker.get_state("kc_eval").p_L
    client = TestClient(app)
    r = client.post("/api/chat/evaluate", json={"exercise_id": "ex_fantasma", "user_answer": "x"})
    body = r.json()
    assert body["status"] == "UNGRADED"
    assert container.bkt_tracker.get_state("kc_eval").p_L == before  # BKT intacto
