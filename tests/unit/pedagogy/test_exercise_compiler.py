"""Tipo 1 (Fase 6) — Ejercicios Multi-KC deterministas.

- select_multi_kc_candidates elige KCs con p_L alto, priorizando struggled.
- compose genera id estable, prompt con KCs, oracle keyword-coverage.
- El oráculo es determinista: la misma respuesta da el mismo veredicto; y
  respuestas completas pasan, vacías fallan.
"""

from types import SimpleNamespace

from study_engine.pedagogy.exercise_compiler import (
    compose_multi_kc_exercise,
    select_multi_kc_candidates,
)
from study_engine.pedagogy.generated_registry import GeneratedOracleGrader

KC_CATALOG = {
    "nb1": {
        "kcs": [
            {"kc_id": "aritmetica_punteros", "title": "Aritmética de punteros",
             "subtopics": ["malloc", "free"]},
            {"kc_id": "arrays_direccionamiento", "title": "Arrays y direccionamiento",
             "subtopics": ["offset", "base"]},
            {"kc_id": "kc_bajo", "title": "algo raro"},
        ]
    }
}


class _Bkt:
    def __init__(self, pl):
        self.pl = pl

    def get_state(self, kc_id):
        return SimpleNamespace(p_L=self.pl.get(kc_id, 0.0))


def test_selecciona_kcs_con_p_L_alto_priorizando_struggled():
    bkt = _Bkt({
        "aritmetica_punteros": 0.85,       # alto
        "arrays_direccionamiento": 0.75,   # alto
        "kc_bajo": 0.2,                    # no entra
    })
    digest = {"struggled_kcs": ["aritmetica_punteros"], "mastered_kcs": []}
    out = select_multi_kc_candidates(KC_CATALOG, bkt, digest=digest)
    assert set(out) == {"aritmetica_punteros", "arrays_direccionamiento"}
    assert out[0] == "aritmetica_punteros"  # struggled primero


def test_compose_genera_ejercicio_estable_y_determinista():
    ex1 = compose_multi_kc_exercise(["aritmetica_punteros", "arrays_direccionamiento"],
                                    catalog=KC_CATALOG)
    ex2 = compose_multi_kc_exercise(["aritmetica_punteros", "arrays_direccionamiento"],
                                    catalog=KC_CATALOG)
    assert ex1 is not None
    assert ex1["exercise_id"] == ex2["exercise_id"]  # estable
    assert ex1["kind"] == "multi_kc"
    assert "aritmetica_punteros" in ex1["prompt"]
    assert ex1["oracle"]["type"] == "keyword_coverage"


def test_compose_retorna_none_si_kcs_sin_template():
    assert compose_multi_kc_exercise(["tema_lejano_xyz"], catalog=KC_CATALOG) is None
    assert compose_multi_kc_exercise([], catalog=KC_CATALOG) is None


def test_oraculo_determinista_multikc():
    ex = compose_multi_kc_exercise(["aritmetica_punteros", "arrays_direccionamiento"],
                                   catalog=KC_CATALOG)
    grader = GeneratedOracleGrader()

    completa = (
        "Reservo la copia con malloc en el heap (copia profunda), hago null-check "
        "con fallback, el caller debe liberar con free."
    )
    r1 = grader.grade(completa, ex["oracle"])
    assert r1["is_correct"] is True

    vaga = "La función duplica el string."
    r2 = grader.grade(vaga, ex["oracle"])
    assert r2["is_correct"] is False

    # Determinismo: misma entrada => mismo dict
    assert grader.grade(completa, ex["oracle"]) == r1
