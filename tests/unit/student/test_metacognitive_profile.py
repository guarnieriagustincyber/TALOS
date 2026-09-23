"""Tests unitarios para el Perfil Metacognitivo y Directivas de Fading (Slice 6.0.6 / M1-M10)."""

import pytest

from study_engine.pedagogy.student_context import get_scaffolding_directive
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import (
    StudentStorage,
    calculate_autonomy_score,
)


def test_cold_start_returns_neutral_profile():
    """M9: Cold start debe retornar perfil neutral, no None o error."""
    storage = StudentStorage(":memory:")
    profile = storage.calculate_solution_dependency("new_student")

    assert profile["student_id"] == "new_student"
    assert profile["classification"] == "moderada"
    assert profile["ratio"] == 0.0
    assert profile["autonomy_score"] == 0.5
    assert profile["total_attempts"] == 0
    assert profile["successful_attempts"] == 0
    assert profile["total_solutions"] == 0
    assert profile["forced_solutions"] == 0
    assert profile["evasion_kcs"] == []
    assert profile["overconfident_kcs"] == []
    assert profile["is_overconfident"] is False


def test_calculate_autonomy_score_formula():
    """M2: Fórmula explícita de autonomy_score."""
    # Cold start
    assert calculate_autonomy_score(0, 0, 0.0) == 0.5

    # Con intentos y 0 soluciones consultadas -> Autonomía máxima
    assert calculate_autonomy_score(5, 0, float("inf")) == 1.0

    # Escala lineal acotada a 1.0 (ratio / 10.0)
    assert calculate_autonomy_score(10, 2, 5.0) == 0.5
    assert calculate_autonomy_score(15, 1, 15.0) == 1.0
    assert calculate_autonomy_score(2, 2, 1.0) == 0.1
    assert calculate_autonomy_score(8, 1, 8.0) == 0.8


def test_evasion_kcs_detection_threshold():
    """M1: evasion_kcs requiere attempts >= 2 y (solutions / attempts) > 0.5."""
    storage = StudentStorage(":memory:")
    sid = "student_evasion"

    # KC1: attempts=2, solutions=2 -> ratio = 1.0 > 0.5 (EVASION)
    storage.record_exercise_attempt("ex_1", student_id=sid, success=False, metadata={"kc_id": "punteros_dangling"})
    storage.record_exercise_attempt("ex_2", student_id=sid, success=False, metadata={"kc_id": "punteros_dangling"})
    storage.log_solution_access("ex_1", student_id=sid, forced=True, metadata={"kc_id": "punteros_dangling"})
    storage.log_solution_access("ex_2", student_id=sid, forced=True, metadata={"kc_id": "punteros_dangling"})

    # KC2: attempts=3, solutions=1 -> ratio = 0.33 <= 0.5 (NO EVASION)
    for i in range(3):
        storage.record_exercise_attempt(f"ex_kc2_{i}", student_id=sid, success=False, metadata={"kc_id": "malloc_heap"})
    storage.log_solution_access("ex_kc2_0", student_id=sid, forced=False, metadata={"kc_id": "malloc_heap"})

    # KC3: attempts=1, solutions=1 -> attempts < 2 (NO EVASION)
    storage.record_exercise_attempt("ex_kc3_0", student_id=sid, success=False, metadata={"kc_id": "race_cond"})
    storage.log_solution_access("ex_kc3_0", student_id=sid, forced=True, metadata={"kc_id": "race_cond"})

    profile = storage.calculate_solution_dependency(sid)
    assert "punteros_dangling" in profile["evasion_kcs"]
    assert "malloc_heap" not in profile["evasion_kcs"]
    assert "race_cond" not in profile["evasion_kcs"]


def test_overconfident_kcs_detection_threshold():
    """M1: overconfident_kcs requiere attempts >= 3, successful == 0 y solutions == 0."""
    storage = StudentStorage(":memory:")
    sid = "student_overconfident"

    # KC1: 3 fallos, 0 aciertos, 0 soluciones -> OVERCONFIDENT
    for i in range(3):
        storage.record_exercise_attempt(f"ex_over_{i}", student_id=sid, success=False, metadata={"kc_id": "deadlock_mutex"})

    # KC2: 2 fallos, 0 aciertos, 0 soluciones -> attempts < 3 (NO OVERCONFIDENT)
    for i in range(2):
        storage.record_exercise_attempt(f"ex_norm_{i}", student_id=sid, success=False, metadata={"kc_id": "fork_exec"})

    # KC3: 3 fallos, 1 solución consultada -> solutions > 0 (NO OVERCONFIDENT)
    for i in range(3):
        storage.record_exercise_attempt(f"ex_sol_{i}", student_id=sid, success=False, metadata={"kc_id": "virtual_mem"})
    storage.log_solution_access("ex_sol_0", student_id=sid, forced=False, metadata={"kc_id": "virtual_mem"})

    profile = storage.calculate_solution_dependency(sid)
    assert "deadlock_mutex" in profile["overconfident_kcs"]
    assert "fork_exec" not in profile["overconfident_kcs"]
    assert "virtual_mem" not in profile["overconfident_kcs"]
    assert profile["is_overconfident"] is True


def test_scaffolding_directives_per_profile():
    """Verifica generación de directivas pedagógicas según clasificación y KCs marcados."""
    # 1. Alta dependencia
    p_alta = {
        "classification": "alta",
        "ratio": 1.2,
        "autonomy_score": 0.12,
        "evasion_kcs": ["punteros_dangling"],
        "overconfident_kcs": [],
    }
    dir_alta = get_scaffolding_directive(p_alta, target_kc_id="punteros_dangling")
    assert "ANDAMIAJE REFORZADO" in dir_alta
    assert "hints progresivos" in dir_alta
    assert "ALERTA DE EVASIÓN en 'punteros_dangling'" in dir_alta

    # 2. Baja dependencia / alta autonomía
    p_baja = {
        "classification": "baja",
        "ratio": 8.5,
        "autonomy_score": 0.85,
        "evasion_kcs": [],
        "overconfident_kcs": ["x86_stack"],
    }
    dir_baja = get_scaffolding_directive(p_baja, target_kc_id="x86_stack")
    assert "DESAFÍO DIRECTO / ALTA AUTONOMÍA" in dir_baja
    assert "ALERTA DE SOBRECONFIANZA en 'x86_stack'" in dir_baja

    # 3. Moderada
    p_mod = {
        "classification": "moderada",
        "ratio": 3.0,
        "autonomy_score": 0.5,
        "evasion_kcs": [],
        "overconfident_kcs": [],
    }
    dir_mod = get_scaffolding_directive(p_mod, target_kc_id="arrays")
    assert "ANDAMIAJE MODERADO" in dir_mod


def test_bkt_invariance_untouched_parameters():
    """M10: El cálculo del perfil metacognitivo NO altera parámetros ni estados de BKT."""
    storage = StudentStorage(":memory:")
    bkt = BKTTracker(storage)

    # Estado previo en BKT
    s0 = bkt.get_state("test_kc")
    p_L_prior = s0.p_L
    attempts_prior = s0.attempts

    # Operaciones metacognitivas
    storage.record_exercise_attempt("ex_1", success=False, metadata={"kc_id": "test_kc"})
    storage.log_solution_access("ex_1", metadata={"kc_id": "test_kc"})
    profile = storage.calculate_solution_dependency()
    directive = get_scaffolding_directive(profile, target_kc_id="test_kc")

    # BKT no debe haber mutado por el profiling
    s1 = bkt.get_state("test_kc")
    assert s1.p_L == p_L_prior
    assert s1.attempts == attempts_prior
    assert s1.p_T == s0.p_T
    assert s1.p_G == s0.p_G
    assert s1.p_S == s0.p_S
