import pytest
from study_engine.pedagogy.command_parser import parse_student_command, CommandType
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader, check_synonym_match, load_synonyms
from study_engine.web.routes.dialogue import validate_hints_socratic
from study_engine.student.storage import StudentStorage
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler

def test_c5_validate_hints_socratic_filtering():
    # E11: Pista con > 70% o que contenga solución literal debe ser rechazada
    expected = "puntero a entero"
    hints = [
        "La respuesta es un puntero a entero", # subcadena directa
        "puntero a enteros", # similitud > 70%
        "Revisá cómo se declaran las direcciones en el stack frame", # válida
    ]
    validated, all_rejected = validate_hints_socratic(hints, expected)
    assert len(validated) == 1
    assert "stack frame" in validated[0]
    assert all_rejected is False

def test_c10_validate_hints_all_rejected_fallback():
    # E16: Si todas las pistas son rechazadas, all_rejected es True y validated es vacio
    expected = "puntero a entero"
    hints = [
        "La respuesta es un puntero a entero",
        "puntero a enteros",
    ]
    validated, all_rejected = validate_hints_socratic(hints, expected)
    assert len(validated) == 0
    assert all_rejected is True

def test_c6_c11_exact_text_synonyms_and_fuzzy():
    # E12, E17: Evaluación de 3 capas
    grader = ExactMatchGrader()
    
    # Capa 1: normalización exacta
    r1 = grader.grade("   PUNTERO   ", "puntero")
    assert r1.is_correct is True
    assert r1.normalization_policy == "exact_text_strip_collapse_preserve_operators"

    # Capa 2: Sinónimos técnicos
    r2 = grader.grade("arreglo", "array")
    assert r2.is_correct is True
    assert r2.normalization_policy == "synonym_match"

    # Capa 2 bidireccional
    r3 = grader.grade("array", "arreglo")
    assert r3.is_correct is True
    assert r3.normalization_policy == "synonym_match"

    # Capa 3: Fuzzy match (>= 0.85)
    r4 = grader.grade("punteross", "punteros")
    assert r4.is_correct is True
    assert r4.normalization_policy == "fuzzy_match"

    # Disparidad mayor (< 0.85 y no sinónimo)
    r5 = grader.grade("memoria cache", "puntero")
    assert r5.is_correct is False

def test_c12_student_hints_storage_and_indexes():
    # E15, E18: Trazabilidad de pistas en SQLite
    storage = StudentStorage(":memory:")
    
    # Verificar schema e índices
    conn = storage._get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(student_hints)")
    cols = {row[1] for row in cursor.fetchall()}
    assert {"id", "episode_id", "exercise_id", "kc_id", "hint_level", "hint_text", "timestamp"}.issubset(cols)

    cursor.execute("PRAGMA index_list(student_hints)")
    indexes = {row[1] for row in cursor.fetchall()}
    assert "idx_hints_episode" in indexes
    assert "idx_hints_exercise" in indexes
    assert "idx_hints_kc" in indexes

    # Registrar pista
    hint_id = storage.record_hint(
        episode_id="ep_test_01",
        exercise_id="ex_ptr_01",
        kc_id="kc_ptrs",
        hint_level=1,
        hint_text="Pensá en la dirección física de la variable.",
    )
    assert hint_id > 0
    assert storage.count_hints("ep_test_01") == 1
    hints = storage.get_hints_for_exercise("ex_ptr_01")
    assert len(hints) == 1
    assert hints[0]["hint_text"] == "Pensá en la dirección física de la variable."

def test_c8_spaced_repetition_record_review():
    # E14: SpacedRepetitionScheduler record_review actualiza estado
    storage = StudentStorage(":memory:")
    scheduler = SpacedRepetitionScheduler(storage)
    
    state_init = scheduler.get_anchor_state("kc_ptrs")
    assert state_init.repetitions == 0
    
    next_review = scheduler.record_review(anchor_id="kc_ptrs", correct=True)
    state_after = scheduler.get_anchor_state("kc_ptrs")
    assert state_after.repetitions == 1
    assert state_after.interval == 1
    assert state_after.next_review == next_review

def test_command_parser_practicar_syntax():
    # Fix 3.1: /practicar, /ejercicio, :practice
    c1 = parse_student_command("/practicar punteros")
    assert c1 is not None
    assert c1.command_type == CommandType.DAME_UN_EJERCICIO
    assert c1.target_arg == "punteros"

    c2 = parse_student_command(":practice arrays")
    assert c2 is not None
    assert c2.command_type == CommandType.DAME_UN_EJERCICIO
    assert c2.target_arg == "arrays"

    c3 = parse_student_command("DAME UN EJERCICIO DE MEMORIA")
    assert c3 is not None
    assert c3.command_type == CommandType.DAME_UN_EJERCICIO
    assert c3.target_arg == "MEMORIA"
