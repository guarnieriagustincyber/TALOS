"""Test-only CurriculumRegistry for test fixtures.

INVARIANTS:
1. NEVER used in production code.
2. Isolates in-memory dynamic registrations strictly to test suites.
"""

from typing import Optional
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification


class TestCurriculumRegistry(CurriculumRegistry):
    """Test-only CurriculumRegistry providing dynamic in-memory fixture registration."""

    __test__ = False

    def register_task(self, task: PracticalTaskSpecification) -> None:
        """Register an in-memory task fixture for tests."""
        self._tasks_cache[task.task_id] = task

    def register_rubric(
        self, rubric: AssessmentRubric, task_id: Optional[str] = None
    ) -> None:
        """Register an in-memory rubric fixture for tests."""
        self._rubrics_cache[rubric.rubric_id] = rubric
        if task_id:
            self._rubrics_cache[task_id] = rubric
