"""Tipo 3 (Fase 6) — Trace-Tables: simulación determinista y grading de estado."""

from study_engine.pedagogy.state_predictor import generate_trace_exercise, _simulate
from study_engine.pedagogy.generated_registry import GeneratedOracleGrader


def test_simulacion_directa_es_right():
    # int x=7; int *p=&x; *p = *p + 3; x = x - 2;
    ops = [("x", ":=", 7), ("p", ":@", "x"), ("*p", "+", 3), ("x", "-", 2)]
    out = _simulate(ops, ["x", "p"])
    assert out["x"] == 8
    assert out["*p"] == 8  # p sigue apuntando a x
    assert out["p_apunta_a"] == "x"


def test_generacion_seed_determinista():
    ex1 = generate_trace_exercise("punteros", seed=42)
    ex2 = generate_trace_exercise("punteros", seed=42)
    assert ex1["exercise_id"] == ex2["exercise_id"]
    assert ex1["oracle"]["final_state"] == ex2["oracle"]["final_state"]
    for k in ("x", "*p"):
        assert k in ex1["oracle"]["final_state"]


def test_grader_state_match():
    ex = generate_trace_exercise("punteros", seed=7)
    oracle = ex["oracle"]
    x_val = oracle["final_state"]["x"]
    p_val = oracle["final_state"]["*p"]

    grader = GeneratedOracleGrader()

    # Formato canónico var=valor (separación por coma o espacio)
    correct = f"x={x_val}, *p={p_val}, p apunta a x"
    assert grader.grade(correct, oracle)["is_correct"] is True

    # Incidencia: valor errado para *p
    wrong = f"x={x_val}, *p={p_val + 1}"
    r = grader.grade(wrong, oracle)
    assert r["is_correct"] is False
    assert r["wrong_fields"] == ["*p"]

    # Con dos puntos también vale
    alt = f"x:{x_val}; *p:{p_val}"
    assert grader.grade(alt, oracle)["is_correct"] is True

    # Valor suelto sin variable asociada NO alcanza (evita falsos positivos)
    suelto = f"el resultado es {x_val} y {p_val}"
    assert grader.grade(suelto, oracle)["is_correct"] is False


def test_endpoint_integration(tmp_path):
    from study_engine.student.storage import StudentStorage
    from study_engine.pedagogy.generated_registry import GeneratedExerciseRegistry

    storage = StudentStorage(str(tmp_path / "s.db"))
    registry = GeneratedExerciseRegistry(storage)
    ex = generate_trace_exercise("punteros", seed=9)
    registry.save(ex)
    loaded = registry.get(ex["exercise_id"])
    assert loaded is not None and loaded["source"] == "generated"
    assert loaded["oracle"]["final_state"] == ex["oracle"]["final_state"]
