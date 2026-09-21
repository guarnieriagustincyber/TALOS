"""Project milestone contracts for Subsystem S5.4.

INVARIANTS:
1. S5.4 defines declarative project and milestone specifications;
   it NEVER tracks or mutates milestone states.
2. MilestoneStatus is a vocabulary enum; no methods in S5.4
   transition or modify it (HG-S5.4-06).
3. Milestones within a project must form a strict DAG.
4. All models are strictly immutable (frozen=True, extra="forbid").
"""

from enum import Enum
from typing import Optional, Set, Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract


class MilestoneStatus(str, Enum):
    """Declarative vocabulary for project milestone states.

    INVARIANT: S5.4 does not own state transitions for milestones.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    SATISFIED = "satisfied"
    FAILED = "failed"


class ProjectMilestone(BaseContract):
    """Declarative specification of an incremental stage in a project."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    milestone_id: str = Field(
        ..., min_length=1, description="Unique milestone identifier"
    )
    project_id: str = Field(
        ..., min_length=1, description="Parent project identifier"
    )
    sequence_order: int = Field(
        ..., ge=0, description="Ordinal position in progression"
    )
    title: str = Field(..., min_length=1, description="Milestone title")
    description: str = Field(
        ..., min_length=1, description="Completion criteria"
    )
    task_ids: Tuple[str, ...] = Field(
        default_factory=tuple, description="Tasks in milestone"
    )
    prerequisite_milestone_ids: Tuple[str, ...] = Field(
        default_factory=tuple, description="Prerequisite milestones"
    )
    required_evidence_criteria: Tuple[str, ...] = Field(
        default_factory=tuple, description="Assessment criteria"
    )


class ProjectSpecification(BaseContract):
    """Declarative specification of a practical project (P-00 to P21).

    INVARIANTS:
    - Milestones must form a valid DAG without cycles.
    - All prerequisite_milestone_ids must reference valid milestones.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: str = Field(
        ..., min_length=1, description="Project ID (e.g. 'P-00', 'P21-A')"
    )
    title: str = Field(..., min_length=1, description="Project title")
    curriculum_node_id: str = Field(
        ..., min_length=1, description="Curricular node (S5.1)"
    )
    milestones: Tuple[ProjectMilestone, ...] = Field(
        ..., min_length=1, description="Milestones forming a DAG"
    )
    capstone_gateway_id: Optional[str] = Field(
        default=None, description="Optional Gateway certifying this project"
    )

    @model_validator(mode="after")
    def validate_milestone_dag(self) -> "ProjectSpecification":
        """Verify milestone uniqueness, prerequisite validity, no cycles."""
        m_map = {m.milestone_id: m for m in self.milestones}
        if len(m_map) != len(self.milestones):
            raise ValueError(
                f"Duplicate milestone IDs in project '{self.project_id}'"
            )

        for m in self.milestones:
            for prereq_id in m.prerequisite_milestone_ids:
                if prereq_id not in m_map:
                    raise ValueError(
                        f"Milestone '{m.milestone_id}' references unknown "
                        f"prerequisite '{prereq_id}' in project "
                        f"'{self.project_id}'"
                    )
                if prereq_id == m.milestone_id:
                    raise ValueError(
                        f"Milestone '{m.milestone_id}' cannot depend on itself"
                    )

        visited: Set[str] = set()
        recursion_stack: Set[str] = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            recursion_stack.add(node_id)
            for prereq in m_map[node_id].prerequisite_milestone_ids:
                if prereq not in visited:
                    if has_cycle(prereq):
                        return True
                elif prereq in recursion_stack:
                    return True
            recursion_stack.remove(node_id)
            return False

        for mid in m_map:
            if mid not in visited:
                if has_cycle(mid):
                    raise ValueError(
                        f"Cyclic milestone dependency in project "
                        f"'{self.project_id}'"
                    )

        return self
