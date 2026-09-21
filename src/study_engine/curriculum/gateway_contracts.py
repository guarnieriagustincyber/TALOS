"""Gateway definition and attempt contracts for Subsystem S5.4.

INVARIANTS:
1. Zero Verdict Emission Authority (HG-S5.4-03):
   GatewayDefinition defines criteria; it NEVER emits the verdict.
2. GatewayAttemptRecord captures operational facts;
   it contains ZERO evaluation verdicts or scores (R1.2).
3. All models are strictly immutable (frozen=True, extra="forbid").
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.curriculum.performance_contracts import PerformanceLevel


class GatewayFormat(str, Enum):
    """Execution modality of a curriculum gateway."""

    INDIVIDUAL_PRACTICAL = "individual_practical"
    PANEL_DEFENSE = "panel_defense"
    PRACTICAL_AND_ORAL = "practical_and_oral"
    CAPSTONE_DEFENSE = "capstone_defense"


class GatewayVerdictCriteria(BaseContract):
    """Declarative criteria and thresholds required for approval."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    criteria_id: str = Field(
        ..., min_length=1, description="Unique criteria specification ID"
    )
    minimum_overall_level: PerformanceLevel = Field(
        default=PerformanceLevel.N3_COMPETENT,
        description="Minimum non-average level required",
    )
    critical_dimensions_required: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Dimensions that must strictly satisfy minimum level",
    )
    require_all_dimensions_pass: bool = Field(
        default=True,
        description="Whether every declared dimension must pass independently",
    )
    allow_compensation: bool = Field(
        default=False,
        description="Whether rubric compensation rules may be consulted",
    )
    max_attempt_duration_minutes: int = Field(
        default=60, gt=0, description="Max allowable duration in minutes"
    )


class GatewayDefinition(BaseContract):
    """Declarative definition of a curriculum gateway.

    INVARIANTS:
    - Sovereign specification of gateway approval criteria.
    - Possesses ZERO methods to emit verdicts or mutate StudentState.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    gateway_id: str = Field(
        ..., min_length=1, description="Gateway ID (e.g. 'G0.1', 'G6A')"
    )
    curriculum_node_id: str = Field(
        ..., min_length=1, description="Roadmap node ID (S5.1)"
    )
    title: str = Field(..., min_length=1, description="Gateway title")
    format: GatewayFormat = Field(
        ..., description="Gateway examination format"
    )
    rubric_id: str = Field(
        ..., min_length=1, description="Reference to AssessmentRubric"
    )
    verdict_criteria: GatewayVerdictCriteria = Field(
        ..., description="Declarative threshold conditions for approval"
    )
    practical_task_ids: Tuple[str, ...] = Field(
        default_factory=tuple, description="Practical laboratory tasks"
    )
    perturbation_ids: Tuple[str, ...] = Field(
        default_factory=tuple, description="Tested perturbations"
    )
    oral_defense_id: Optional[str] = Field(
        default=None, description="Reference to OralDefenseSpecification"
    )
    associated_project_id: Optional[str] = Field(
        default=None, description="Reference to capstone ProjectSpecification"
    )
    required_evidence_outcomes: Tuple[str, ...] = Field(
        default_factory=tuple, description="Required certified outcomes"
    )


class GatewayAttemptRecord(BaseContract):
    """Operational record of a student's attempt at a gateway.

    INVARIANTS:
    - Records WHAT was attempted and WHAT artifacts were generated.
    - Does NOT contain the verdict or evaluate competence (R1.2).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    attempt_id: str = Field(
        ..., min_length=1, description="Unique attempt identifier"
    )
    gateway_id: str = Field(..., min_length=1, description="Gateway attempted")
    student_id: str = Field(..., min_length=1, description="Student ID")
    session_id: Optional[str] = Field(
        default=None, description="Session ID (S5.3)"
    )
    started_at: datetime = Field(..., description="Attempt start timestamp")
    completed_at: Optional[datetime] = Field(
        default=None, description="Attempt completion timestamp"
    )
    submitted_artifact_ids: Tuple[str, ...] = Field(
        default_factory=tuple, description="IDs of artifacts generated"
    )
    observation_refs: Tuple[str, ...] = Field(
        default_factory=tuple, description="References to execution traces"
    )
    perturbation_response_refs: Tuple[str, ...] = Field(
        default_factory=tuple, description="References to responses given"
    )
