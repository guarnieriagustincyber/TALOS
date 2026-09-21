"""Subsystem S5.4 — Curriculum Assessment & Competency Contracts.

Exported contracts and domain specifications:
- PerformanceLevel (IntEnum: N1..N4)
- RubricDimension, CompensationScope, CompensationRule, AssessmentRubric
- Precondition, Postcondition, Invariant, TerminationVariant,
  HoareContractSpecification
- PerturbationType, ExpectedBehavior, PerturbationTemplate
- ArtifactType, ArtifactProvenance, ArtifactRecord, ArtifactRequirement
- TaskDifficulty, LabEnvironmentRequirements, PracticalTaskSpecification
- MilestoneStatus, ProjectMilestone, ProjectSpecification
- DefenseCategory, DefenseQuestionTemplate, OralDefenseSpecification
- GatewayFormat, GatewayVerdictCriteria, GatewayDefinition,
  GatewayAttemptRecord
"""

from study_engine.curriculum.artifact_contracts import (
    ArtifactProvenance,
    ArtifactRecord,
    ArtifactRequirement,
    ArtifactType,
)
from study_engine.curriculum.gateway_contracts import (
    GatewayAttemptRecord,
    GatewayDefinition,
    GatewayFormat,
    GatewayVerdictCriteria,
)
from study_engine.curriculum.hoare_contracts import (
    HoareContractSpecification,
    Invariant,
    Postcondition,
    Precondition,
    TerminationVariant,
)
from study_engine.curriculum.milestone_contracts import (
    MilestoneStatus,
    ProjectMilestone,
    ProjectSpecification,
)
from study_engine.curriculum.oral_defense_contracts import (
    DefenseCategory,
    DefenseQuestionTemplate,
    OralDefenseSpecification,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.perturbation_contracts import (
    ExpectedBehavior,
    PerturbationTemplate,
    PerturbationType,
)
from study_engine.curriculum.rubric_contracts import (
    CANONICAL_DIMENSIONS,
    DIMENSION_COMMUNICATION,
    DIMENSION_FOUNDATIONS,
    DIMENSION_INVARIANT_JUSTIFICATION,
    DIMENSION_LIVE_DEMO,
    DIMENSION_QUESTIONS_PERTURBATIONS,
    AssessmentRubric,
    CompensationRule,
    CompensationScope,
    RubricDimension,
)
from study_engine.curriculum.task_contracts import (
    LabEnvironmentRequirements,
    PracticalTaskSpecification,
    TaskDifficulty,
)

__all__ = [
    # Performance
    "PerformanceLevel",
    # Rubric
    "CANONICAL_DIMENSIONS",
    "DIMENSION_LIVE_DEMO",
    "DIMENSION_INVARIANT_JUSTIFICATION",
    "DIMENSION_FOUNDATIONS",
    "DIMENSION_QUESTIONS_PERTURBATIONS",
    "DIMENSION_COMMUNICATION",
    "CompensationScope",
    "CompensationRule",
    "RubricDimension",
    "AssessmentRubric",
    # Hoare
    "Precondition",
    "Postcondition",
    "Invariant",
    "TerminationVariant",
    "HoareContractSpecification",
    # Perturbation
    "PerturbationType",
    "ExpectedBehavior",
    "PerturbationTemplate",
    # Artifact
    "ArtifactType",
    "ArtifactProvenance",
    "ArtifactRecord",
    "ArtifactRequirement",
    # Task
    "TaskDifficulty",
    "LabEnvironmentRequirements",
    "PracticalTaskSpecification",
    # Milestone
    "MilestoneStatus",
    "ProjectMilestone",
    "ProjectSpecification",
    # Oral defense
    "DefenseCategory",
    "DefenseQuestionTemplate",
    "OralDefenseSpecification",
    # Gateway
    "GatewayFormat",
    "GatewayVerdictCriteria",
    "GatewayDefinition",
    "GatewayAttemptRecord",
]
