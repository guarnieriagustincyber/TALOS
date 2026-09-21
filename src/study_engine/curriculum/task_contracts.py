"""Practical laboratory task contracts for Subsystem S5.4.

INVARIANTS:
1. S5.4 defines practical task specifications;
   it NEVER executes commands or provisions labs (S6 responsibility).
2. References external resources via explicit string IDs.
3. All models are strictly immutable (frozen=True, extra="forbid").
"""

from enum import Enum
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.curriculum.artifact_contracts import ArtifactRequirement


class TaskDifficulty(str, Enum):
    """Categorization of pedagogical difficulty."""

    FUNDAMENTAL = "fundamental"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    CAPSTONE = "capstone"


class LabEnvironmentRequirements(BaseContract):
    """Declarative specification of required sandbox and environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    environment_id: str = Field(
        ..., min_length=1, description="Environment template identifier"
    )
    os_family: str = Field(
        default="linux", min_length=1, description="Target OS family"
    )
    required_packages: Tuple[str, ...] = Field(
        default_factory=tuple, description="Required software packages"
    )
    required_ports: Tuple[int, ...] = Field(
        default_factory=tuple, description="Ports required open in lab"
    )
    network_isolation_level: str = Field(
        default="internal_only",
        description="Isolation mode ('airgapped', 'internal_only')",
    )
    resource_limits: Dict[str, Any] = Field(
        default_factory=dict, description="Constraints on memory, CPU, timeout"
    )


class PracticalTaskSpecification(BaseContract):
    """Declarative specification of a hands-on cybersecurity task.

    INVARIANTS:
    - Purely declarative; possesses no execution or grading methods.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str = Field(
        ..., min_length=1, description="Unique practical task identifier"
    )
    curriculum_node_id: str = Field(
        ..., min_length=1, description="Roadmap node ID (S5.1) this supports"
    )
    title: str = Field(..., min_length=1, description="Task title")
    difficulty: TaskDifficulty = Field(
        default=TaskDifficulty.FUNDAMENTAL, description="Task complexity"
    )
    description: str = Field(
        ..., min_length=1, description="Task instructions"
    )
    hoare_contract_id: Optional[str] = Field(
        default=None, description="Optional reference to Hoare specification"
    )
    lab_environment: Optional[LabEnvironmentRequirements] = Field(
        default=None, description="Container and tool requirements"
    )
    required_artifacts: Tuple[ArtifactRequirement, ...] = Field(
        default_factory=tuple, description="Required observable artifacts"
    )
    perturbation_ids: Tuple[str, ...] = Field(
        default_factory=tuple, description="Pool of perturbation templates"
    )
    time_limit_minutes: Optional[int] = Field(
        default=None, gt=0, description="Optional practical time limit"
    )
