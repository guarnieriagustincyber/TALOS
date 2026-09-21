"""Contract tests for Oral Defense specifications (S5.4)."""

import pytest
from pydantic import ValidationError

from study_engine.curriculum.oral_defense_contracts import (
    DefenseCategory,
    DefenseQuestionTemplate,
    OralDefenseSpecification,
)


def test_oral_defense_question_count_validation() -> None:
    """required_questions_count cannot exceed pool size."""
    q1 = DefenseQuestionTemplate(
        question_id="q1",
        category=DefenseCategory.ARCHITECTURE_JUSTIFICATION,
        prompt_text="Explain why you chose deque over list",
        target_concepts=("data_structures", "time_complexity"),
        expected_points_n3=("O(1) append/pop vs O(n)",),
    )

    with pytest.raises(
        ValidationError, match="required_questions_count .* exceeds"
    ):
        OralDefenseSpecification(
            defense_id="def-invalid",
            duration_minutes=15,
            panel_size=1,
            question_pool=(q1,),
            required_questions_count=3,  # Exceeds pool size of 1
            rubric_id="rubric-oral",
        )


def test_g1_2_oral_defense_fixture() -> None:
    """Demonstrate representation of G1.2 Oral Defense (10 min, 1 eval)."""
    q_endian = DefenseQuestionTemplate(
        question_id="q-g12-endianness",
        category=DefenseCategory.ARCHITECTURE_JUSTIFICATION,
        prompt_text="Explicá el impacto de endianness en red",
        target_concepts=("network_byte_order", "big_endian"),
        expected_points_n3=(
            "Red usa big-endian (RFC 791)",
            "x86 usa little-endian",
            "struct.unpack usa '!'",
        ),
        expected_points_n4=(
            "Predice inversión de campos multi-byte",
            "Explica registros de CPU y memoria",
        ),
    )
    q_checksum = DefenseQuestionTemplate(
        question_id="q-g12-checksum",
        category=DefenseCategory.INVARIANT_DEFENSE,
        prompt_text="¿Cómo calculás y verificás el checksum de IPv4?",
        target_concepts=("ones_complement", "checksum"),
        expected_points_n3=(
            "Suma complemento a uno de 16 bits",
            "Zero en el campo al calcular",
        ),
        expected_points_n4=(
            "Explica por qué resultado es 0xFFFF",
            "Distingue suma 0 de checksum incorrecto",
        ),
    )

    oral = OralDefenseSpecification(
        defense_id="def-g12-oral",
        duration_minutes=10,
        panel_size=1,
        question_pool=(q_endian, q_checksum),
        required_questions_count=2,
        rubric_id="rubric-g12-oral",
    )

    assert oral.duration_minutes == 10
    assert oral.panel_size == 1
    assert len(oral.question_pool) == 2
    assert oral.required_questions_count == 2


def test_g6a_panel_defense_fixture() -> None:
    """Demonstrate representation of G6A Track A Defense (30 min, 3 eval)."""
    q_exec = DefenseQuestionTemplate(
        question_id="q-g6a-exec",
        category=DefenseCategory.EXECUTIVE_SYNTHESIS,
        prompt_text="Explicá al CTO por qué fallaría con least privilege",
        target_concepts=("least_privilege", "iam_policies"),
        expected_points_n3=(
            "Token comprometido sin s3:GetObject",
            "El rol estaba restringido",
        ),
        expected_points_n4=(
            "Traduce impacto a negocio",
            "Propone mitigación arquitectónica",
        ),
    )

    oral = OralDefenseSpecification(
        defense_id="def-g6a-final-panel",
        duration_minutes=30,
        panel_size=3,
        question_pool=(q_exec,),
        required_questions_count=1,
        rubric_id="rubric-g6a",
    )

    assert oral.panel_size == 3
    assert oral.duration_minutes == 30
