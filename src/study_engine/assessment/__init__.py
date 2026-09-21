"""Subsystem S9.1: Deterministic Practical Assessment Engine.

Provides formal evaluation of practical laboratory execution observations
against S5.4 task specifications and rubrics under non-average policies.
"""

from study_engine.assessment.aggregator import aggregate_evaluations
from study_engine.assessment.evaluator_deterministic import (
    evaluate_practical_task,
)
from study_engine.assessment.fact_extractor import extract_instrumental_facts
from study_engine.assessment.service import (
    DeterministicAssessmentEngine,
    SpecificationIntegrityError,
)

__all__ = [
    "DeterministicAssessmentEngine",
    "SpecificationIntegrityError",
    "extract_instrumental_facts",
    "evaluate_practical_task",
    "aggregate_evaluations",
]
