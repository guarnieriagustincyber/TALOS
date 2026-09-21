"""Contracts and domain models for Subsystem S5.2.A (Assessment Policy).

INVARIANTS:
1. EvidenceType describes what occurred, never the outcome (no CODE_FAILURE).
2. EvidenceOutcome (PASS, FAIL, INCONCLUSIVE) describes the result.
3. S4.4 audit is required ONLY if requires_audit_approved=True (LLM tutors).
4. MANUAL_OVERRIDE requires actor_type=HUMAN, rationale, and revision hashes.
5. EXEMPT is strictly human-governed; AI/tools cannot produce EXEMPT.
6. canonical_policy_id is an immutable 64-char SHA-256 digest.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.roadmap.contracts import NodeType


class EvidenceType(str, Enum):
    """Classification of evidence generation mechanism or modality."""

    CONCEPTUAL_EXPLANATION = "CONCEPTUAL_EXPLANATION"
    CODE_EXECUTION = "CODE_EXECUTION"
    LAB_TELEMETRY = "LAB_TELEMETRY"
    DIAGNOSTIC_QUIZ = "DIAGNOSTIC_QUIZ"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class EvidenceOutcome(str, Enum):
    """Result of an evidence-producing evaluation attempt."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class ActorType(str, Enum):
    """Source authority that executed or produced the evidence."""

    HUMAN = "HUMAN"
    AI_TUTOR = "AI_TUTOR"
    TOOL_VERIFIER = "TOOL_VERIFIER"


class CriteriaEvaluationVerdict(str, Enum):
    """Deterministic verdict from evaluating evidence against criteria."""

    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    REGRESSED = "REGRESSED"
    EXEMPT = "EXEMPT"


class PolicyContractError(Exception):
    """Base exception for all assessment policy violations."""


class PolicyHashMismatchError(PolicyContractError):
    """Raised when a policy's declared hash does not match computed hash."""


class SovereignExemptionViolationError(PolicyContractError, ValueError):
    """Raised when unauthorized actor or invalid override attempts EXEMPT."""


class InvalidCriteriaConfigurationError(PolicyContractError):
    """Raised when an assessment criteria configuration is invalid."""


class EvidenceRecord(BaseContract):

    """Atomic record of an observed evaluation or activity."""

    model_config = ConfigDict(frozen=True)

    record_id: str = Field(
        ..., min_length=1, description="Unique evidence record identifier"
    )
    student_id: str = Field(
        default="default-student",
        min_length=1,
        description="Student identifier associated with this evidence",
    )
    node_id: str = Field(
        ..., min_length=1, description="Associated curricular node ID"
    )

    competency_id: Optional[str] = Field(
        default=None, description="Optional associated competency ID"
    )
    evidence_type: EvidenceType = Field(
        ..., description="Taxonomic modality of evidence"
    )
    outcome: EvidenceOutcome = Field(
        ..., description="Result: PASS, FAIL, or INCONCLUSIVE"
    )
    score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Normalized performance metric [0.0, 1.0]",
    )
    timestamp: datetime = Field(
        ..., description="UTC timestamp of evidence creation"
    )
    actor_type: ActorType = Field(
        ..., description="Authority type: HUMAN, AI_TUTOR, or TOOL_VERIFIER"
    )
    actor_id: str = Field(
        ..., min_length=1, description="Specific identifier of actor or module"
    )
    audit_verdict: Optional[str] = Field(
        default=None,
        description="S4.4 Forensic Audit verdict (e.g. APPROVED)",
    )

    tool_backend: Optional[str] = Field(
        default=None,
        description="Tool backend name if produced by S6 (e.g. wireshark)",
    )
    verifier_id: Optional[str] = Field(
        default=None,
        description="Instrumental verifier identifier for tool telemetry",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Human pedagogical reasoning or verifier explanation",
    )
    roadmap_revision_id: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Roadmap canonical revision active at record creation",
    )
    policy_revision_id: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Policy canonical revision active at record creation",
    )
    authority_id: EpistemologicalAuthority = Field(
        ...,
        description="Mandatory sovereign authority responsible for record",
    )
    assessment_digest: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Canonical SHA-256 digest of admitted AssessmentResult",
    )
    spine_id: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Lineage provenance spine identifier",
    )
    overall_level: Optional[PerformanceLevel] = Field(
        default=None,
        description="Evaluative level copied from AssessmentResult",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata for lab metrics or telemetry",
    )

    @model_validator(mode="after")
    def validate_sovereign_override_boundary(self) -> "EvidenceRecord":
        """Enforce strict sovereign rules on MANUAL_OVERRIDE records."""
        if self.evidence_type == EvidenceType.MANUAL_OVERRIDE:
            if self.actor_type != ActorType.HUMAN:
                raise SovereignExemptionViolationError(
                    f"Only HUMAN actors may produce MANUAL_OVERRIDE. "
                    f"Forbidden actor_type: '{self.actor_type.value}'."
                )
            if not self.rationale or not self.rationale.strip():
                raise SovereignExemptionViolationError(
                    "MANUAL_OVERRIDE requires a non-empty rationale."
                )
            if not self.roadmap_revision_id:
                raise SovereignExemptionViolationError(
                    "MANUAL_OVERRIDE requires explicit roadmap_revision_id."
                )
            if not self.policy_revision_id:
                raise SovereignExemptionViolationError(
                    "MANUAL_OVERRIDE requires explicit policy_revision_id."
                )
        return self


class EvidenceRequirement(BaseContract):
    """Specification of what evidence is required to prove a competency."""

    model_config = ConfigDict(frozen=True)

    requirement_id: str = Field(
        ..., min_length=1, description="Unique requirement identifier slug"
    )
    evidence_type: EvidenceType = Field(
        ..., description="Required evidence type"
    )
    min_count: int = Field(
        default=1,
        ge=1,
        description="Minimum number of qualifying PASS evidences required",
    )
    min_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum normalized score for evidence to qualify",
    )
    max_age_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Max validity window in days (None = non-expiring)",
    )
    requires_audit_approved: bool = Field(
        default=False,
        description="True if evidence requires S4.4 APPROVED verdict (LLMs)",
    )
    required_tool_backend: Optional[str] = Field(
        default=None,
        description="Required tool backend for instrumental telemetry (S6)",
    )


class NodeAssessmentCriteria(BaseContract):
    """Evaluation rulebook governing satisfaction and regression for a node."""

    model_config = ConfigDict(frozen=True)

    criteria_id: str = Field(
        ..., min_length=1, description="Unique criteria identifier"
    )
    target_node_type: Optional[NodeType] = Field(
        default=None,
        description="Target NodeType if this serves as default for a type",
    )
    target_node_id: Optional[str] = Field(
        default=None,
        description="Target node_id if this is a node-specific override",
    )
    requirements: Tuple[EvidenceRequirement, ...] = Field(
        ...,
        min_length=1,
        description="Set of requirements that must be satisfied",
    )
    regression_threshold_failures: int = Field(
        default=2,
        ge=1,
        description="Consecutive FAILs after last PASS causing regression",
    )
    allow_exempt: bool = Field(
        default=True,
        description="Whether human sovereign may mark this node EXEMPT",
    )


class AssessmentPolicy(BaseContract):
    """Complete, sovereign curricular assessment policy."""

    model_config = ConfigDict(frozen=True)

    policy_id: str = Field(
        ..., min_length=1, description="Unique policy identifier"
    )
    title: str = Field(
        ..., min_length=1, description="Human-readable policy title"
    )
    version: str = Field(
        ..., min_length=1, description="Semantic version string (e.g. 1.0.0)"
    )
    default_criteria: Dict[NodeType, NodeAssessmentCriteria] = Field(
        ..., description="Default criteria indexed by NodeType"
    )
    node_overrides: Dict[str, NodeAssessmentCriteria] = Field(
        default_factory=dict,
        description="Specific criteria overrides indexed by node_id",
    )
    canonical_policy_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 digest derived from canonical policy structure",
    )


class CriteriaEvaluationResult(BaseContract):
    """Deterministic evaluation outcome for a node against evidence."""

    model_config = ConfigDict(frozen=True)

    criteria_id: str = Field(

        ..., min_length=1, description="Evaluated criteria identifier"
    )
    verdict: CriteriaEvaluationVerdict = Field(
        ..., description="Evaluation verdict"
    )
    satisfied_requirements: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="List of requirement_ids successfully met",
    )
    missing_requirements: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="List of requirement_ids not yet satisfied",
    )
    subsequent_failures_count: int = Field(
        default=0,
        ge=0,
        description="Count of consecutive FAILs strictly after last PASS",
    )
    evaluation_timestamp: datetime = Field(
        ..., description="Timestamp representing as_of evaluation point"
    )
    rationale: str = Field(
        ..., min_length=1, description="Deterministic pedagogical explanation"
    )
