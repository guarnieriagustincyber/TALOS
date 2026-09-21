"""Unit tests for StudentState contract."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.student_state import StudentState


def test_student_state_valid_minimal():
    state = StudentState(student_id="student-01")
    assert state.student_id == "student-01"
    assert state.status == "developing"
    assert state.understanding == {}
    assert state.strengths == []
    assert state.weaknesses == []
    assert state.recurring_errors == []


def test_student_state_valid_full():
    now = datetime.now(timezone.utc)
    state = StudentState(
        student_id="student-agustin",
        topic="Recursión",
        status="developing",
        understanding={
            "conceptual": True,
            "application": True,
            "transfer": False,
        },
        strengths=["Caso base", "Pila de llamadas"],
        weaknesses=["Recursión de cola"],
        recurring_errors=["Condición de parada invertida"],
        last_evaluation={"score": 8.5, "passed": True},
        next_action={"type": "targeted_exercise", "topic": "Recursión de cola"},
        metadata={"session_count": 5},
        updated_at=now,
    )
    assert state.understanding["conceptual"] is True
    assert state.understanding["transfer"] is False
    assert len(state.strengths) == 2
    assert state.last_evaluation["score"] == 8.5


def test_student_state_missing_student_id():
    with pytest.raises(ValidationError):
        StudentState()

    with pytest.raises(ValidationError):
        StudentState(student_id="")
