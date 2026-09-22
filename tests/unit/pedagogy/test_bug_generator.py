"""Tipo 2 (Fase 6) — BugSpotter: mutación controlada + grader de clase de bug."""

from study_engine.pedagogy.bug_generator import _BUG_BANK, generate_debugging_exercise
from study_engine.pedagogy.generated_registry import GeneratedOracleGrader


def test_cada_plantilla_mutacion_aplica_de_verdad():
    """La mutación debe transformar el código correcto en el buggy (no manual)."""
    for tpl in _BUG_BANK:
        buggy = tpl["correct"].replace(tpl["mutation_find"], tpl["mutation_replace"])
        assert tpl["probe"] in buggy, f"{tpl['cwe']}: probe no aparece en buggy"
        assert tpl["probe"] not in tpl["correct"], f"{tpl['cwe']}: correcto ya contenía el bug"


def test_cwe120_genera_codigo_con_strcpy_sin_limite():
    ex = generate_debugging_exercise("punteros", bug_type="buffer_overflow")
    assert ex is not None
    assert "strcpy(buffer, input);" in ex["prompt"]
    assert ex["oracle"]["cwe"] == "CWE-120"
    assert ex["kc_ids"] == ["punteros"]


def test_match_por_familia_si_no_hay_bug_type():
    ex = generate_debugging_exercise("so2_concurrencia_procesos")
    assert ex is not None  # cae a CWE-362 race_condition por familia
    assert ex["oracle"]["cwe"] == "CWE-362"


def test_grader_acepta_sinonimos_de_la_clase():
    ex = generate_debugging_exercise("punteros", bug_type="buffer_overflow")
    grader = GeneratedOracleGrader()
    for phrasing in [
        "Es un buffer overflow clásico: strcpy sin bound",
        "CWE-120. Desborda el stack.",
        "Stack smashing: el input pisa el buffer de 64 bytes",
    ]:
        r = grader.grade(phrasing, ex["oracle"])
        assert r["is_correct"] is True, phrasing

    bad = grader.grade("es un problema de punteros", ex["oracle"])
    assert bad["is_correct"] is False
    assert bad["expected_class"] == "CWE-120"


def test_generacion_determinista_mismo_id():
    a = generate_debugging_exercise("punteros", bug_type="use_after_free")
    b = generate_debugging_exercise("punteros", bug_type="use_after_free")
    assert a["exercise_id"] == b["exercise_id"]
    assert a["prompt"] == b["prompt"]
