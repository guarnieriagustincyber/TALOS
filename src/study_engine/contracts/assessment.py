"""Assessment contracts for Subsystem S9.1 (Deterministic Practical Engine).

INVARIANTS:
1. S9.1 AssessmentResult represents evaluative interpretation of empirical
   facts against S5.4 task and rubric specifications.
2. InstrumentalFact (from S6.1) is strictly distinct from EvaluativeFact
   (derived by S9.1 evaluators).
3. AssessmentStatus distinguishes ASSESSED from INSUFFICIENT_OBSERVATION.
   Absence of observation != negative observation; insufficient != N1.
4. All specifications and observations are cryptographically bound by SHA-256.
5. All contracts are strictly frozen and immutable (frozen=True, extra=forbid).
6. Single sovereign authority: EpistemologicalAuthority.ASSESSMENT_ENGINE.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
from typing import Optional, Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.curriculum.performance_contracts import PerformanceLevel

_HEX_64_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def compute_canonical_sha256(contract: BaseContract) -> str:
    """Compute deterministic SHA-256 digest of contract JSON payload."""
    payload = json.dumps(
        contract.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AssessmentStatus(str, Enum):
    """Evaluation status of a rubric dimension."""

    ASSESSED = "ASSESSED"
    INSUFFICIENT_OBSERVATION = "INSUFFICIENT_OBS"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_YET_ASSESSED = "NOT_YET_ASSESSED"


class FactObservability(str, Enum):
    """Epistemological observability degree of an instrumental fact."""

    CONCLUSIVE = "CONCLUSIVE"
    PARTIAL_TRUNCATED = "PARTIAL_TRUNCATED"
    VERIFIED_ABSENCE = "VERIFIED_ABSENCE"


class InstrumentalFactType(str, Enum):
    """Instrumental empirical facts extracted from ExecutionObservation."""

    PROCESS_EXIT_CODE = "process.exit_code"
    PROCESS_TERMINATION_REASON = "process.termination_reason"
    PROCESS_TIMED_OUT = "process.timed_out"
    EXECUTION_DURATION_MS = "process.duration_ms"
    STDOUT_TEXT_SNIPPET = "stdout.text_snippet"
    STDERR_TEXT_SNIPPET = "stderr.text_snippet"
    STREAM_WAS_TRUNCATED = "stream.was_truncated"
    ARTIFACT_PRESENT = "artifact.present"
    ARTIFACT_VERIFIED_ABSENT = "artifact.verified_absent"
    ARTIFACT_OMITTED_BY_LIMIT = "artifact.omitted_by_limit"
    ARTIFACT_SIZE_BYTES = "artifact.size_bytes"
    ARTIFACT_SHA256_DIGEST = "artifact.sha256_digest"


class EvaluativeFactType(str, Enum):
    """Evaluative facts derived by S9.1 against curricular requirements."""

    ARTIFACT_CONFORMS_TO_REQUIREMENT = "eval.artifact_conforms"
    STDOUT_MATCHES_PATTERN = "eval.stdout_matches_pattern"
    STDERR_MATCHES_PATTERN = "eval.stderr_matches_pattern"
    DURATION_WITHIN_SLA = "eval.duration_within_sla"
    EXIT_CODE_EXPECTED = "eval.exit_code_expected"


class InstrumentalFact(BaseContract):
    """Empirical fact extracted strictly from ExecutionObservation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_id: str = Field(..., min_length=1)
    observation_id: str = Field(..., min_length=1)
    fact_type: InstrumentalFactType
    fact_value: str = Field(..., description="Serialized value representation")
    observability: FactObservability = Field(
        default=FactObservability.CONCLUSIVE
    )
    inspected_domain: str = Field(
        default="scratch/workspace/",
        min_length=1,
        description="Physical domain inspected for this fact",
    )
    provenance_detail: str = Field(
        ..., min_length=1, description="Source provenance within observation"
    )


class EvaluativeFact(BaseContract):
    """Fact derived by S9.1 comparing instrumental facts to requirements."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_id: str = Field(..., min_length=1)
    evaluator_id: str = Field(..., min_length=1)
    fact_type: EvaluativeFactType
    fact_value: str = Field(..., description="Evaluation outcome value")
    satisfied: bool = Field(
        ..., description="True if requirement criterion met"
    )
    based_on_instrumental_fact_ids: Tuple[str, ...] = Field(
        ..., min_length=1, description="Auditable empirical foundation"
    )
    requirement_id: str = Field(
        ..., min_length=1, description="Task requirement referenced"
    )
    rationale: str = Field(
        ..., min_length=1, description="Rule-based derivation explanation"
    )


class SpecificationReference(BaseContract):
    """Immutable cryptographic reference to a curriculum specification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    specification_id: str = Field(..., min_length=1)
    revision_id: str = Field(..., min_length=1)
    specification_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")


class ObservationReference(BaseContract):
    """Immutable cryptographic reference to an execution observation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: str = Field(..., min_length=1)
    execution_id: str = Field(..., min_length=1)
    effective_script_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    observation_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")


class DimensionEvaluation(BaseContract):
    """Formal evaluation of a single rubric dimension."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension_id: str = Field(..., min_length=1)
    status: AssessmentStatus
    assigned_level: Optional[PerformanceLevel] = Field(
        default=None, description="Required when status == ASSESSED"
    )
    passed_minimum: Optional[bool] = Field(
        default=None, description="Required when status == ASSESSED"
    )
    is_critical: bool = Field(
        ..., description="Inherited from formal rubric specification"
    )
    evidence_evaluative_fact_ids: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Evaluative fact IDs supporting this evaluation",
    )
    evaluator_rule_ids: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Deterministic rule IDs executed for this dimension",
    )
    evaluation_rationale: str = Field(
        ...,
        min_length=1,
        description="Structured explanation: rules matched + facts observed",
    )

    @model_validator(mode="after")
    def validate_dimension_consistency(self) -> "DimensionEvaluation":
        """Enforce strict consistency between status and assigned levels."""
        if self.status == AssessmentStatus.ASSESSED:
            if self.assigned_level is None:
                raise ValueError(
                    f"Dimension '{self.dimension_id}' with status ASSESSED "
                    f"must have an assigned_level."
                )
            if self.passed_minimum is None:
                raise ValueError(
                    f"Dimension '{self.dimension_id}' with status ASSESSED "
                    f"must specify passed_minimum."
                )
            if len(self.evidence_evaluative_fact_ids) == 0:
                raise ValueError(
                    f"Dimension '{self.dimension_id}' with status ASSESSED "
                    f"must reference at least one evaluative fact ID."
                )
        else:
            if self.assigned_level is not None:
                raise ValueError(
                    f"Dimension '{self.dimension_id}' with status "
                    f"'{self.status.value}' cannot have assigned_level."
                )
            if self.passed_minimum is not None:
                raise ValueError(
                    f"Dimension '{self.dimension_id}' with status "
                    f"'{self.status.value}' cannot have passed_minimum."
                )
        return self


class AggregationResult(BaseContract):
    """Aggregated outcome of dimension evaluations under non-average policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    aggregation_policy: str = Field(
        default="S5.4_NON_AVERAGE_CRITICAL_DIMENSIONS", min_length=1
    )
    overall_level: Optional[PerformanceLevel] = Field(
        default=None,
        description="Overall level; None if any critical dimension unassessed",
    )
    passed: bool = Field(
        ...,
        description=(
            "True strictly if available evidence satisfies the applied "
            "evaluation policy. Never represents student mastery."
        ),
    )
    critical_dimension_failures: Tuple[str, ...] = Field(default_factory=tuple)
    compensation_rules_applied: Tuple[str, ...] = Field(default_factory=tuple)
    insufficient_dimensions: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Dimensions with INSUFFICIENT_OBSERVATION status",
    )


class AssessmentResult(BaseContract):
    """Sovereign assessment result emitted by Assessment Engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assessment_id: str = Field(..., min_length=1)
    task: SpecificationReference
    rubric: SpecificationReference
    observations: Tuple[ObservationReference, ...] = Field(..., min_length=1)
    instrumental_facts: Tuple[InstrumentalFact, ...] = Field(..., min_length=1)
    evaluative_facts: Tuple[EvaluativeFact, ...] = Field(..., min_length=1)
    dimension_evaluations: Tuple[DimensionEvaluation, ...] = Field(
        ..., min_length=1
    )
    aggregation: AggregationResult
    evaluator_id: str = Field(..., min_length=1)
    evaluator_version: str = Field(..., min_length=1)
    assessed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    authority_id: str = Field(
        default=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        frozen=True,
    )
    assessment_digest: str = Field(
        default="",
        description="Deterministic SHA-256 digest computed over result core",
    )
