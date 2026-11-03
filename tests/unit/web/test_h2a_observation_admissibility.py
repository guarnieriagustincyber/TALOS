"""H2-A (autorización propietaria 2026-10-21): admisibilidad de observaciones.

Regla aprobada: una observación solo puede modificar el estado académico de
los conocimientos que un instrumento autorizado y verificable haya evaluado
efectivamente.

TEST CONTRACT (por caso):
- Propiedad: los falsos positivos reproducidos (.m1_h2a/repro_before.json)
  dejan de producir efectos académicos; las evaluaciones legítimas
  (certificadas, exactas) conservan sus efectos; "no evaluable" no penaliza.
- Precondiciones: AppContainer(use_mock=True) + working_dir temporal +
  sesión persistida real (patrón test_exercise_loop.py); StudentState
  sintético temporal.
- Oráculo: BKTTracker sintético (p_L/attempts antes vs después) + respuesta
  HTTP (bkt_updates/academic_admission).
- NO demuestra: validez pedagógica general de los instrumentos (H9/EP-04);
  comportamiento con estado real.
"""

import os

import pytest
from fastapi.testclient import TestClient

from study_engine.federation.notebook_registry import Notebook, NotebookRegistry
from study_engine.pedagogy.observation_admissibility import (
    GeneratedAdmission,
    admit_generated_observation,
)
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container

ADMIN_TOKEN = "synthetic-admin-token-for-focused-tests-012345"
NB = "notebook-h2a-admissibility"
KCS = ["punteros", "memoria", "arquitectura_computadores", "kc_eval_h2a"]


@pytest.fixture(autouse=True)
def _admin_token(monkeypatch):
    monkeypatch.setenv("TALOS_ADMIN_TOKEN", ADMIN_TOKEN)


class _H2A:
    """Container sintético + sesión real + cliente (patrón route-level)."""

    def __init__(self, tmp_path):
        self.container = AppContainer(working_dir=tmp_path, use_mock=True)
        registry = NotebookRegistry(initial_notebooks=[Notebook(
            notebook_id=NB,
            name="Notebook sintético H2-A",
            subject="Admisibilidad de observaciones",
            sources=[],
        )])
        self.container.notebook_registry = registry
        self.container.pedagogical_orchestrator.notebook_registry = registry
        self.container.study_session_orchestrator.notebook_registry = registry
        self.container.pedagogical_orchestrator._kc_catalog = {
            NB: {
                "name": "Notebook sintético H2-A",
                "curriculum_id": "curriculum-h2a-admissibility",
                "kcs": [
                    {"kc_id": k, "title": k, "unit": 1, "prerequisites": []}
                    for k in KCS
                ],
            },
        }
        self.session_id = self.container.study_session_orchestrator.open_session(NB).session_id
        set_container(self.container)
        self.client = TestClient(create_app())

    def state(self, kc):
        return self.container.bkt_tracker.get_state(kc)

    def gen(self, kind, payload):
        r = self.client.post(
            f"/api/student/exercises/generate/{kind}?include_oracle=true",
            json=payload,
            headers={"X-Admin-Token": ADMIN_TOKEN},
        )
        assert r.status_code == 201, r.text
        return r.json()

    def evaluate(self, ex_id, answer, attempt):
        r = self.client.post(
            "/api/chat/evaluate",
            json={
                "exercise_id": ex_id,
                "user_answer": answer,
                "session_id": self.session_id,
                "attempt_id": attempt,
            },
        )
        assert r.status_code == 200, r.text
        return r.json()


# ---------------------------------------------------------------------------
# Contención: los defectos reproducidos dejan de producir efectos académicos
# ---------------------------------------------------------------------------

def test_d1_state_match_subcadena_no_genera_progreso(tmp_path):
    """Esperado x=1 acepta "x=10" como FEEDBACK, pero sin mutación académica."""
    h = _H2A(tmp_path)
    ex = h.gen("trace", {"kc_id": "arquitectura_computadores", "arch": "x86", "n_mutations": 2})
    kc = h.container.generated_registry.get(ex["exercise_id"])["kc_ids"][0]
    fs = ex["oracle"]["final_state"]
    poisoned = ", ".join(f"{k}={v}0" for k, v in fs.items())
    before = h.state(kc)

    res = h.evaluate(ex["exercise_id"], poisoned, "h2a-t-d1")

    # Feedback conservado (el grader no se modificó); efectos contenidos.
    assert res["status"] == "GRADED"
    assert res["is_correct"] is True
    assert res["bkt_updates"] == {}
    assert res["delta_p_L"] == 0.0
    assert res["academic_admission"]["admissible"] is False
    assert "subcadena" in res["academic_admission"]["reason"]
    assert h.state(kc).p_L == before.p_L
    assert h.state(kc).attempts == before.attempts


def test_d2_state_match_all_symbolic_vacuo_no_genera_progreso(tmp_path):
    """Todos los campos simbólicos → cero criterios evaluables: sin efectos."""
    h = _H2A(tmp_path)
    h.container.generated_registry.save({
        "exercise_id": "gen_h2a_test_all_symbolic",
        "kind": "trace",
        "kc_ids": ["arquitectura_computadores"],
        "prompt": "Predecí el estado final (sintético H2-A).",
        "oracle": {
            "type": "state_match",
            "final_state": {"ptr": "0xdeadbeef", "dst": "0xcafe0000"},
            "symbolic_fields": ["ptr", "dst"],
        },
    })
    kc = "arquitectura_computadores"
    before = h.state(kc)

    res = h.evaluate("gen_h2a_test_all_symbolic", "no tengo idea", "h2a-t-d2")

    assert res["status"] == "GRADED"
    assert res["is_correct"] is True  # el oráculo vacuo sigue diciendo true (feedback)
    assert res["bkt_updates"] == {}
    assert h.state(kc).p_L == before.p_L
    assert h.state(kc).attempts == before.attempts


def test_d3_d6_keyword_falso_multikc_sin_distribucion_ni_espiral(tmp_path):
    """Explicación FALSA con todos los alias: feedback sí; ni BKT multi-KC ni espiral."""
    h = _H2A(tmp_path)
    ex = h.gen("multi-kc", {"kc_ids": ["punteros", "memoria"]})
    kc1, kc2 = "punteros", "memoria"
    accepts = [a for req in ex["oracle"]["required"] for a in req.get("accept", [])]
    false_answer = " ".join(f"Es FALSO que {a} importe; ignoralo." for a in accepts)
    b1, b2 = h.state(kc1), h.state(kc2)

    res = h.evaluate(ex["exercise_id"], false_answer, "h2a-t-d3d6")

    assert res["status"] == "GRADED"
    assert res["is_correct"] is True
    assert res["bkt_updates"] == {}
    assert res["spiral_opportunities"] == []
    assert "sin atribución discriminante" in res["academic_admission"]["reason"]
    assert h.state(kc1).p_L == b1.p_L and h.state(kc1).attempts == b1.attempts
    assert h.state(kc2).p_L == b2.p_L and h.state(kc2).attempts == b2.attempts
    # Registro neutro del intento conservado (H2-A §7)
    assert h.container.student_storage.has_exercise_attempt(ex["exercise_id"])


def test_d4_bug_alias_en_negacion_no_genera_progreso(tmp_path):
    """"NO es un buffer overflow" contiene el alias: feedback sí, progreso no."""
    h = _H2A(tmp_path)
    ex = h.gen("debugging", {"kc_id": "punteros", "bug_type": "buffer_overflow"})
    kc = h.container.generated_registry.get(ex["exercise_id"])["kc_ids"][0]
    before = h.state(kc)
    neg = (
        "Definitivamente NO es un buffer overflow: la función es segura, "
        "no hay vector de explotación ni hace falta parche."
    )

    res = h.evaluate(ex["exercise_id"], neg, "h2a-t-d4")

    assert res["status"] == "GRADED"
    assert res["is_correct"] is True  # defecto del grader documentado (feedback intacto)
    assert res["bkt_updates"] == {}
    assert h.state(kc).p_L == before.p_L
    assert h.state(kc).attempts == before.attempts


def test_d5_verify_estructural_es_feedback_sin_bkt(tmp_path, monkeypatch):
    """/verify de un ensayo estructuralmente prolijo y vacío: sin mutación BKT."""
    from study_engine.web.routes import student_exercises

    h = _H2A(tmp_path)
    subs = tmp_path / "student_submissions"
    (subs / "fase0-sye" / "tramo1").mkdir(parents=True, exist_ok=True)
    essay = (
        '<!-- metadata: {"notebook_id": "fase0-sye", "kc_id": "estado_nacion_h2a"} -->\n\n'
        "## Tesis Central\n"
        "Esta investigacion sostiene con absoluta conviccion y sin ningun contenido "
        "disciplinar verificable que basta escribir palabras suficientes aqui.\n\n"
        "## Argumentos\n"
        "1. Primer argumento vacio pero numerado correctamente para el contador.\n"
        "2. Segundo argumento igualmente vacio con palabras suficientes.\n"
        "3. Tercer argumento irrelevante sin ninguna doctrina real.\n\n"
        "## Citas\n"
        "- Bobbio imaginado para el test sintetico (sin pagina).\n"
        "- Constitucion totalmente apocrifa del test H2-A (s/n).\n\n"
        "## Contrapunto\n"
        "El contrapunto dialéctico de este test también es deliberadamente vacío: "
        "no contrasta ninguna tradición doctrinal ni tensión institucional real y "
        "existe únicamente para superar el conteo mínimo de palabras exigido.\n"
    )
    (subs / "fase0-sye" / "tramo1" / "ej_h2a_essay.md").write_text(essay, encoding="utf-8")
    monkeypatch.setattr(student_exercises, "BASE_SUBMISSIONS_DIR", subs)
    monkeypatch.setattr(student_exercises, "REPORTS_DIR", subs / ".reports")

    kc = "estado_nacion_h2a"
    before = h.state(kc)
    r = h.client.post("/api/student/exercises/ej_h2a_essay/verify")
    assert r.status_code == 200
    report = r.json()

    # Feedback estructural conservado íntegro...
    assert report["passed"] is True
    assert report["score"] >= 70.0
    # ...sin efecto académico (H2-A)
    assert report["bkt_updated"] is False
    assert h.state(kc).p_L == before.p_L
    assert h.state(kc).attempts == before.attempts


def test_no_evaluable_no_penaliza_bkt(tmp_path):
    """Un fallo de observación no admisible NO cuenta como conocimiento incorrecto."""
    h = _H2A(tmp_path)
    ex = h.gen("debugging", {"kc_id": "punteros", "bug_type": "buffer_overflow"})
    kc = h.container.generated_registry.get(ex["exercise_id"])["kc_ids"][0]
    before = h.state(kc)

    res = h.evaluate(ex["exercise_id"], "no se nada del tema", "h2a-t-noeval")

    assert res["status"] == "GRADED"
    assert res["is_correct"] is False  # feedback de fallo
    assert res["remediation"] is not None  # la remediación (feedback) se conserva
    # "No evaluable ≠ incorrecto": BKT no registra el fallo como observación
    assert res["bkt_updates"] == {}
    assert h.state(kc).attempts == before.attempts
    assert h.state(kc).p_L == before.p_L
    assert res["struggle_consecutive_failures"] == 0


# ---------------------------------------------------------------------------
# Positivos: las evaluaciones legítimas conservan sus efectos autorizados
# ---------------------------------------------------------------------------

def _store_with(tmp_path, exercises):
    import json

    from study_engine.pedagogy.exercise_store import ExerciseStore

    p = tmp_path / "exercises.json"
    p.write_text(json.dumps(exercises), encoding="utf-8")
    return ExerciseStore(storage_path=p)


def _exercise_json(exercise_id, kc_id, expected, ex_type="NUMERIC", options=None):
    return {
        "exercise_id": exercise_id,
        "source_id": "src_test",
        "source_location": "p.1",
        "source_hash": "0" * 64,
        "extractor_version": "test",
        "extraction_method": "test",
        "verification_status": "QUALIFIABLE",
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


def test_certificado_exacto_sube_p_l(tmp_path):
    """Positivo H2-A §6: ejercicio certificado con clave válida conserva su efecto."""
    h = _H2A(tmp_path)
    h.container.exercise_store = _store_with(
        tmp_path, [_exercise_json("ex_h2a_ok", "kc_eval_h2a", "1012")]
    )
    before = h.state("kc_eval_h2a")

    res = h.evaluate("ex_h2a_ok", "1012", "h2a-t-cert-1")

    assert res["status"] == "GRADED"
    assert res["is_correct"] is True
    assert res["delta_p_L"] > 0
    assert h.state("kc_eval_h2a").p_L > before.p_L
    assert h.state("kc_eval_h2a").attempts == before.attempts + 1


def test_certificado_incorrecto_cuenta_intento(tmp_path):
    """Positivo: fallo en instrumento exacto certificado SÍ es observación."""
    h = _H2A(tmp_path)
    h.container.exercise_store = _store_with(
        tmp_path, [_exercise_json("ex_h2a_no", "kc_eval_h2a", "42")]
    )
    before = h.state("kc_eval_h2a")

    res = h.evaluate("ex_h2a_no", "999", "h2a-t-cert-2")

    assert res["is_correct"] is False
    assert res["attempts"] == before.attempts + 1
    assert res["remediation"] is not None


def test_reenvio_identico_no_duplica_efectos(tmp_path):
    """Positivo §6: el recibo durable de /evaluate se reutiliza (replay idempotente)."""
    h = _H2A(tmp_path)
    ex = h.gen("debugging", {"kc_id": "punteros", "bug_type": "buffer_overflow"})
    payload = {
        "exercise_id": ex["exercise_id"],
        "user_answer": "Es un buffer overflow del stack por strcpy",
        "session_id": h.session_id,
        "attempt_id": "h2a-t-replay-1",
    }
    r1 = h.client.post("/api/chat/evaluate", json=payload)
    r2 = h.client.post("/api/chat/evaluate", json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json().get("was_idempotent_replay") is True

    # Con certificado: tampoco duplica la mutación admitida
    h.container.exercise_store = _store_with(
        tmp_path, [_exercise_json("ex_h2a_rep", "kc_eval_h2a", "7")]
    )
    p2 = {
        "exercise_id": "ex_h2a_rep",
        "user_answer": "7",
        "session_id": h.session_id,
        "attempt_id": "h2a-t-replay-2",
    }
    h.client.post("/api/chat/evaluate", json=p2)
    after_first = h.state("kc_eval_h2a").attempts
    r2b = h.client.post("/api/chat/evaluate", json=p2)
    assert r2b.json().get("was_idempotent_replay") is True
    assert h.state("kc_eval_h2a").attempts == after_first


# ---------------------------------------------------------------------------
# Módulo de política: clasificación por contrato real
# ---------------------------------------------------------------------------

def test_admision_por_contrato_real_no_por_nombre():
    for kind in ("multi_kc", "debugging", "trace"):
        d = admit_generated_observation(kind=kind, kc_ids=["k1"])
        assert isinstance(d, GeneratedAdmission)
        assert d.academic_effects is False
        assert d.reason  # motivo documentado por contrato


def test_admision_fail_closed_casos_desconocidos():
    assert admit_generated_observation(kind=None, kc_ids=["k1"]).academic_effects is False
    assert admit_generated_observation(kind="exacto_futuro", kc_ids=["k1"]).academic_effects is False
    d = admit_generated_observation(kind="exacto_futuro", kc_ids=["k1"])
    assert "desconocido" in d.reason


def test_admision_multikc_exige_atribucion_discriminante():
    d1 = admit_generated_observation(kind="trace", kc_ids=["k1"])
    d2 = admit_generated_observation(kind="trace", kc_ids=["k1", "k2", "k3"])
    assert "sin atribución discriminante" in d2.reason
    assert "sin atribución discriminante" not in d1.reason
    d0 = admit_generated_observation(kind="trace", kc_ids=[])
    assert "sin KC atribuible" in d0.reason
