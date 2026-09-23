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


def test_selector_fallback_a_generado_cuando_catalogo_vacio(tmp_path):
    """Integración Fase 6: catálogo estático vacío -> registry -> genera on-the-fly."""
    from study_engine.pedagogy.exercise_service import select_or_generate
    from study_engine.pedagogy.exercise_store import ExerciseStore
    from study_engine.pedagogy.generated_registry import GeneratedExerciseRegistry
    from study_engine.student.storage import StudentStorage

    empty_store = ExerciseStore(storage_path=tmp_path / "vacio.json")  # sin ejercicios
    registry = GeneratedExerciseRegistry(StudentStorage(str(tmp_path / "s.db")))

    # KC sin cobertura certificada pero matcheable a la plantilla multi-KC
    out = select_or_generate(
        empty_store,
        registry,
        "aritmetica_punteros",
        catalog={"fase0-soc": {"kcs": [
            {"kc_id": "aritmetica_punteros", "title": "Aritmética de punteros",
             "subtopics": ["malloc", "free"]},
        ]}},
    )
    assert out is not None and out["source"] == "generated"

    # Segunda llamada: NO regenera — usa lo persistido en el registro
    out2 = select_or_generate(empty_store, registry, "aritmetica_punteros",
                              catalog={"fase0-soc": {"kcs": [
                                  {"kc_id": "aritmetica_punteros", "title": "x"}]}})
    assert out2["exercise_id"] == out["exercise_id"]


def test_select_multi_kc_threshold_0_6():
    """Verifica que el umbral HIGH_MASTERY_THRESHOLD = 0.6 funciona exactamente."""
    bkt = _Bkt({
        "kc_alto": 0.61,
        "kc_borde_bajo": 0.59,
        "kc_muy_bajo": 0.1,
    })
    catalog = {
        "nb": {
            "kcs": [
                {"kc_id": "kc_alto", "title": "Alto"},
                {"kc_borde_bajo": "kc_borde_bajo", "title": "Borde Bajo"},
                {"kc_muy_bajo": "kc_muy_bajo", "title": "Muy Bajo"},
            ]
        }
    }
    out = select_multi_kc_candidates(catalog, bkt)
    assert "kc_alto" in out
    assert "kc_borde_bajo" not in out
    assert "kc_muy_bajo" not in out


def test_compose_multi_kc_3_kcs_y_4_familias():
    """Valida 3 KCs combinados y la cobertura de las 4 familias añadidas en Fase B."""
    catalog = {
        "nb_multi": {
            "kcs": [
                {"kc_id": "punteros_shared", "title": "Punteros y memoria compartida",
                 "subtopics": ["shared", "concurrencia", "mutex", "thread"]},
                {"kc_id": "concurrencia_mutex", "title": "Concurrencia con mutex",
                 "subtopics": ["mutex", "thread", "race"]},
                {"kc_id": "race_conditions", "title": "Condiciones de carrera",
                 "subtopics": ["race", "shared"]},
                {"kc_id": "pila_underflow", "title": "Pila y LIFO",
                 "subtopics": ["pila", "underflow", "push", "pop"]},
                {"kc_id": "memoria_stack", "title": "Memoria de stack",
                 "subtopics": ["stack", "lifo"]},
                {"kc_id": "x86_abi", "title": "ABI x86-64",
                 "subtopics": ["x86", "abi", "calling_convention"]},
                {"kc_id": "stack_frame", "title": "Marco de pila x86",
                 "subtopics": ["rbp", "rsp", "ret"]},
                {"kc_id": "arrays_subindice", "title": "Arrays y subíndices",
                 "subtopics": ["subindice", "corchetes"]},
                {"kc_id": "bounds_oob", "title": "Límites y OOB",
                 "subtopics": ["bounds", "fuera_de_rango", "oob"]},
            ]
        }
    }
    grader = GeneratedOracleGrader()

    # 1. 3-KC combinación en Familia 1 (Concurrencia)
    ex1 = compose_multi_kc_exercise(
        ["punteros_shared", "concurrencia_mutex", "race_conditions"],
        catalog=catalog
    )
    assert ex1 is not None
    assert "Buffer compartido dinámico con sincronización mutex" in ex1["prompt"]
    assert len(ex1["kc_ids"]) == 3
    # Solución de referencia pasa
    res1 = grader.grade(
        "Adquirir pthread_mutex_lock(&lock) antes de invocar malloc(), verificar null, luego asignar a *shared_ptr, "
        "y liberar con pthread_mutex_unlock(&lock) para evitar la data race. Luego liberar con free.",
        ex1["oracle"]
    )
    assert res1["is_correct"] is True
    # Mutación incompleta falla
    res1_bad = grader.grade("Asignar el puntero en el heap con malloc.", ex1["oracle"])
    assert res1_bad["is_correct"] is False

    # 2. Familia 2: Pila / Recursión / Underflow
    ex2 = compose_multi_kc_exercise(["pila_underflow", "memoria_stack"], catalog=catalog)
    assert ex2 is not None
    assert "Operación pop segura en pila dinámica enlazada" in ex2["prompt"]
    res2 = grader.grade(
        "Validar si es null antes de pop para prevenir underflow, extraer valor en out_val, avanzar al siguiente next y liberar con free.",
        ex2["oracle"]
    )
    assert res2["is_correct"] is True

    # 3. Familia 3: x86 ABI / Stack Frame
    ex3 = compose_multi_kc_exercise(["x86_abi", "stack_frame"], catalog=catalog)
    assert ex3 is not None
    assert "Prólogo de función y convención ABI System V x86-64" in ex3["prompt"]
    res3 = grader.grade(
        "Prólogo push %rbp; mov %rsp, %rbp; argumentos en %edi y %esi, resultado en %eax; epílogo pop %rbp y ret.",
        ex3["oracle"]
    )
    assert res3["is_correct"] is True

    # 4. Familia 4: Arrays / Indexing / Bounds
    ex4 = compose_multi_kc_exercise(["arrays_subindice", "bounds_oob"], catalog=catalog)
    assert ex4 is not None
    assert "Búsqueda en rango con aritmética de punteros y guardas de frontera" in ex4["prompt"]
    res4 = grader.grade(
        "Avanzar start++ comparando *start == target mientras start < end con guarda de frontera, retornar null si no encontrado.",
        ex4["oracle"]
    )
    assert res4["is_correct"] is True

