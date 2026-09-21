"""Unit tests for StudyPlan contract."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.study_plan import StudyPlan


def test_study_plan_valid_minimal():
    plan = StudyPlan(
        id="plan-001",
        module="Estructuras de Control",
        objective="Dominar condicionales y bucles en pseudocódigo y C",
    )
    assert plan.id == "plan-001"
    assert plan.module == "Estructuras de Control"
    assert plan.depth == "standard"
    assert plan.prerequisites == []
    assert plan.concepts == []


def test_study_plan_valid_full():
    now = datetime.now(timezone.utc)
    plan = StudyPlan(
        id="plan-fase-0-mod-1",
        student_id="student-01",
        module="Fundamentos de Algoritmos",
        objective="Construcción y análisis de algoritmos básicos",
        prerequisites=["Lógica proposicional"],
        concepts=["Variables", "Tipos de datos", "Asignación", "Condicionales"],
        sources=["joyanes-fp-4e", "spraul-think-like-a-programmer"],
        order=["1. Variables", "2. Expresiones", "3. Condicionales"],
        depth="rigorous",
        exercises=["ejercicio-01", "ejercicio-02"],
        mastery_criteria="Superar evaluación conceptual y 2 ejercicios prácticos sin errores de frontera.",
        metadata={"estimated_hours": 10},
        created_at=now,
    )
    assert len(plan.sources) == 2
    assert plan.depth == "rigorous"
    assert len(plan.exercises) == 2


def test_study_plan_missing_required():
    with pytest.raises(ValidationError):
        StudyPlan(module="Mod", objective="Obj")

    with pytest.raises(ValidationError):
        StudyPlan(id="plan-1", objective="Obj")

    with pytest.raises(ValidationError):
        StudyPlan(id="plan-1", module="Mod")
