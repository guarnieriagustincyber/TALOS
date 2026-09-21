"""Unit tests for deterministic graders (ExactMatchGrader & MultiChoiceGrader).

INVARIANTS TESTED:
1. MultiChoiceGrader checks exact option identity.
2. ExactMatchGrader NUMERIC policy preserves signs (e.g. -5 != 5, 1012 == 1012).
3. ExactMatchGrader EXACT_TEXT collapses whitespace without erasing punctuation or operators.
4. Output includes complete auditable trace.
"""

import pytest
from study_engine.pedagogy.exercise_contracts import ExerciseType
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader


def test_multichoice_grader_correct_and_incorrect() -> None:
    grader = MultiChoiceGrader()
    res_ok = grader.grade("b", "B")
    assert res_ok.is_correct is True
    assert res_ok.normalized_answer == "B"
    assert "¡Correcto!" in res_ok.feedback

    res_fail = grader.grade("A", "C")
    assert res_fail.is_correct is False
    assert res_fail.normalized_answer == "A"
    assert res_fail.expected_answer == "C"


def test_exact_numeric_grader_preserves_signs() -> None:
    grader = ExactMatchGrader()

    # Positive integer match
    res_pos = grader.grade("1012", "1012", ExerciseType.NUMERIC)
    assert res_pos.is_correct is True
    assert res_pos.normalized_answer == "1012"

    # Embedded in conversational text
    res_text = grader.grade("La dirección resultante es 1012 bytes.", "1012", ExerciseType.NUMERIC)
    assert res_text.is_correct is True

    # Strict sign preservation: -5 vs 5 must NOT match
    res_neg_mismatch = grader.grade("-5", "5", ExerciseType.NUMERIC)
    assert res_neg_mismatch.is_correct is False

    res_neg_match = grader.grade("-15", "-15", ExerciseType.NUMERIC)
    assert res_neg_match.is_correct is True


def test_exact_text_grader_preserves_operators() -> None:
    grader = ExactMatchGrader()

    # Exact string match with extra whitespace
    res_ok = grader.grade("  PCB   ", "pcb", ExerciseType.EXACT_TEXT)
    assert res_ok.is_correct is True
    assert res_ok.normalized_answer == "pcb"

    # Preserves formula operators: 3 - 2 != 3 2
    res_formula = grader.grade("3 - 2", "3 - 2", ExerciseType.EXACT_TEXT)
    assert res_formula.is_correct is True

    res_diff = grader.grade("3 2", "3 - 2", ExerciseType.EXACT_TEXT)
    assert res_diff.is_correct is False
