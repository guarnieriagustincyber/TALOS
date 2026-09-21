"""Tests for ExerciseGenerator, S4.4 verification, and coverage criteria."""

import json
from pathlib import Path
import pytest

from study_engine.pedagogy.exercise_generator import ExerciseGenerator
from study_engine.pedagogy.exercise_contracts import ExerciseType, ExerciseVerificationStatus
from study_engine.pedagogy.exercise_store import ExerciseStore


def test_exercise_generator_creates_and_certifies_valid_mc():
    gen = ExerciseGenerator()
    cand = gen.create_candidate(
        exercise_id="ex_test_mc_01",
        source_id="src_tanenbaum_os_modernos",
        source_location="Capítulo 2, p. 85",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Qué estructura mantiene el estado de ejecución de un proceso en el kernel de SO?",
        exercise_type=ExerciseType.MC,
        expected_answer="A",
        options=[
            "A. Process Control Block (PCB)",
            "B. File Allocation Table (FAT)",
            "C. Interrupt Descriptor Table (IDT)",
            "D. Translation Lookaside Buffer (TLB)",
        ],
        solution_explanation="El PCB almacena el contexto de ejecución, registros y estado del proceso.",
    )

    assert cand.verification_status == ExerciseVerificationStatus.UNVERIFIED
    certified = gen.certify_candidate(cand)
    assert certified is not None
    assert certified.verification_status == ExerciseVerificationStatus.QUALIFIABLE
    assert certified.is_presentable() is True
    assert certified.verified_by == "TALOS-S4.4-ForensicVerifier-v2"


def test_exercise_generator_rejects_ambiguous_or_ungrounded():
    gen = ExerciseGenerator()

    # 1. Reject too brief prompt
    cand_short = gen.create_candidate(
        exercise_id="ex_bad_1",
        source_id="src_tanenbaum_os_modernos",
        source_location="p. 1",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Qué es?",
        exercise_type=ExerciseType.EXACT_TEXT,
        expected_answer="PCB",
    )
    assert gen.certify_candidate(cand_short) is None

    # 2. Reject MC with missing expected answer in options
    cand_bad_opt = gen.create_candidate(
        exercise_id="ex_bad_2",
        source_id="src_tanenbaum_os_modernos",
        source_location="p. 1",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Qué estructura mantiene el estado de ejecución en el kernel?",
        exercise_type=ExerciseType.MC,
        expected_answer="Z",
        options=["A. PCB", "B. TCB"],
    )
    assert gen.certify_candidate(cand_bad_opt) is None

    # 3. Reject NUMERIC with non-parseable expected answer
    cand_bad_num = gen.create_candidate(
        exercise_id="ex_bad_3",
        source_id="src_tanenbaum_os_modernos",
        source_location="p. 1",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Cuál es el valor del offset numérico de la estructura en memoria?",
        exercise_type=ExerciseType.NUMERIC,
        expected_answer="muchos_bytes",
    )
    assert gen.certify_candidate(cand_bad_num) is None


def test_exercise_store_coverage_exceeds_50_kcs():
    store = ExerciseStore()
    covered = store.get_covered_kcs()
    all_exercises = store.list_all()

    # Success criteria from FASE V2 directive: >50 KCs covered
    assert len(covered) >= 50, f"Se esperaban >= 50 KCs cubiertos, pero hay {len(covered)}"
    assert len(all_exercises) >= 100, f"Se esperaban >= 100 ejercicios certificados, pero hay {len(all_exercises)}"

    # Distribution criteria: MC >= 40%
    mc_count = sum(1 for e in all_exercises if e.exercise_type == ExerciseType.MC)
    assert mc_count / len(all_exercises) >= 0.40, "La proporción de MC debe ser >= 40%"


def test_exercise_generator_rejects_banned_mad_libs_patterns():
    gen = ExerciseGenerator()

    # Reject candidate with banned mad-libs prompt
    cand_mad_prompt = gen.create_candidate(
        exercise_id="ex_bad_mad_1",
        source_id="src_tanenbaum_os_modernos",
        source_location="Capítulo 2",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿cuál es el principio conceptual y la garantía formal fundamental que asegura la integridad?",
        exercise_type=ExerciseType.MC,
        expected_answer="A",
        options=["A. Opcion uno valida", "B. Opcion dos valida", "C. Opcion tres valida"],
    )
    is_valid, viols = gen.verify_candidate_integrity(cand_mad_prompt)
    assert not is_valid
    assert any("banned mad-libs boilerplate" in v for v in viols)

    # Reject candidate with banned mad-libs option
    cand_mad_opt = gen.create_candidate(
        exercise_id="ex_bad_mad_2",
        source_id="src_tanenbaum_os_modernos",
        source_location="Capítulo 2",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Cómo maneja el kernel los desbordamientos de buffer en la pila de llamadas?",
        exercise_type=ExerciseType.MC,
        expected_answer="A",
        options=[
            "A. Con canarios de pila y páginas no ejecutables",
            "B. Omitir la validación de límites para maximizar la velocidad",
            "C. Desactivar las interrupciones del hardware permanentemente",
        ],
    )
    is_valid, viols = gen.verify_candidate_integrity(cand_mad_opt)
    assert not is_valid
    assert any("banned boilerplate pattern" in v for v in viols)


def test_exercise_generator_rejects_distractor_jaccard_overlap():
    gen = ExerciseGenerator()

    # Reject options that are near-duplicates (high Jaccard overlap)
    cand_overlap = gen.create_candidate(
        exercise_id="ex_bad_overlap",
        source_id="src_tanenbaum_os_modernos",
        source_location="Capítulo 2",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Cuál es la función del registro program counter durante la ejecución del proceso?",
        exercise_type=ExerciseType.MC,
        expected_answer="A",
        options=[
            "A. Almacenar la dirección de memoria de la siguiente instrucción a ejecutar",
            "B. Guardar la dirección de memoria de la siguiente instrucción a ejecutar",
            "C. Tabla de páginas virtuales del espacio de memoria",
        ],
    )
    is_valid, viols = gen.verify_candidate_integrity(cand_overlap)
    assert not is_valid
    assert any("too similar" in v for v in viols)

    # Reject duplicate options
    cand_dup = gen.create_candidate(
        exercise_id="ex_bad_dup",
        source_id="src_tanenbaum_os_modernos",
        source_location="Capítulo 2",
        source_hash="0" * 64,
        kc_id="so2_gestion_procesos_pcb",
        prompt="¿Cuál es la función principal del despachador de procesos en el sistema operativo?",
        exercise_type=ExerciseType.MC,
        expected_answer="A",
        options=[
            "A. Asignar la CPU al proceso seleccionado",
            "B. Asignar la CPU al proceso seleccionado",
            "C. Crear nuevos hilos de kernel",
        ],
    )
    is_valid, viols = gen.verify_candidate_integrity(cand_dup)
    assert not is_valid
    assert any("duplicate text" in v for v in viols)


def test_certified_exercises_zero_mad_libs_and_full_integrity():
    store = ExerciseStore()
    gen = ExerciseGenerator()

    exercises = store.list_all()
    assert len(exercises) >= 100, f"Expected >= 100 certified exercises, got {len(exercises)}"

    covered_kcs = store.get_covered_kcs()
    assert len(covered_kcs) >= 50, f"Expected >= 50 KCs covered, got {len(covered_kcs)}"

    for ex in exercises:
        is_valid, viols = gen.verify_candidate_integrity(ex)
        assert is_valid, f"Exercise {ex.exercise_id} failed integrity verification: {viols}"

        for pat in gen.BANNED_MAD_LIBS_PATTERNS:
            assert not pat.search(ex.prompt), f"Exercise {ex.exercise_id} prompt has banned pattern: {pat.pattern}"
            if ex.options:
                for opt in ex.options:
                    assert not pat.search(opt), f"Exercise {ex.exercise_id} option has banned pattern: {opt}"

