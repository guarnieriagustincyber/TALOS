"""Gateway Decision Authority contracts and evaluation logic (S5.5).

INVARIANTS:
1. Single Sovereign Authority: GatewayDecisionAuthority is the sole component
   authorized to evaluate whether a GatewayDefinition is satisfied.
2. Pure Composition: GDA does NOT re-score rubrics, execute sandbox code,
   or conduct oral defenses. It composes authorized results from S9/S10,
   S7, and S5.2.A against declarative GatewayDefinition criteria.
3. Cryptographic Tamper-Evidence: GatewayVerdictRecord contains a canonical
   SHA-256 digest of the verdict payload.
4. Non-Mutating: GDA does not mutate StudentState or append to EvidenceLedger.
   The resulting GatewayVerdictRecord must be submitted to S5.2.A -> S5.2.B.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalStage,
    validate_epistemological_authority,
)
from study_engine.curriculum.gateway_contracts import GatewayDefinition


def compute_gateway_revision_id(gateway_def: GatewayDefinition) -> str:
    """Compute canonical 64-character SHA-256 digest of GatewayDefinition."""
    canonical_json = gateway_def.model_dump_json()
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_verdict_digest(
    verdict_id: str,
    gateway_id: str,
    gateway_revision_id: str,
    student_id: str,
    passed: bool,
    evaluated_at: datetime,
    component_evaluations: Dict[str, Any],
) -> str:
    """Compute canonical SHA-256 tamper-evident digest of a gateway verdict."""
    payload = {
        "verdict_id": verdict_id,
        "gateway_id": gateway_id,
        "gateway_revision_id": gateway_revision_id,
        "student_id": student_id,
        "passed": passed,
        "evaluated_at": evaluated_at.isoformat(),
        "component_evaluations": component_evaluations,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class GatewayVerdictRecord(BaseContract):
    """Tamper-evident, cryptographically anchored verdict for a gateway."""

    verdict_id: str = Field(..., min_length=1)
    gateway_id: str = Field(..., min_length=1)
    gateway_revision_id: str = Field(..., min_length=64, max_length=64)
    student_id: str = Field(..., min_length=1)
    passed: bool
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    authority_id: str = Field(
        default=EpistemologicalAuthority.GATEWAY_DECISION_AUTHORITY.value,
        min_length=1,
    )
    component_evaluations: Dict[str, Any] = Field(default_factory=dict)
    verdict_digest: str = Field(..., min_length=64, max_length=64)

    @field_validator("verdict_digest", "gateway_revision_id")
    @classmethod
    def validate_digest_format(cls, v: str) -> str:
        """Verify 64-character lowercase hex SHA-256 format."""
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("Digest must be a 64-char lowercase hex.")
        return v.lower()


class GatewayDecisionAuthority:
    """Sole sovereign component for composing gateway evaluation verdicts."""

    AUTHORITY_ID: str = (
        EpistemologicalAuthority.GATEWAY_DECISION_AUTHORITY.value
    )

    def __init__(self) -> None:
        # Validate sovereign authority to emit GATEWAY_VERDICT
        validate_epistemological_authority(
            stage=EpistemologicalStage.GATEWAY_VERDICT,
            authority=EpistemologicalAuthority.GATEWAY_DECISION_AUTHORITY,
        )

    def evaluate_gateway(
        self,
        verdict_id: str,
        student_id: str,
        gateway_def: GatewayDefinition,
        assessment_results: List[Dict[str, Any]],
        gateway_revision_id: Optional[str] = None,
        oral_defense_result: Optional[Dict[str, Any]] = None,
        perturbation_results: Optional[List[Dict[str, Any]]] = None,
        evidence_eligibility: Optional[Dict[str, Any]] = None,
    ) -> GatewayVerdictRecord:
        """Compose independent assessment outcomes against criteria.

        Args:
            verdict_id: Unique identifier for the emitted verdict.
            student_id: The candidate student.
            gateway_def: Declarative criteria from S5.4.
            assessment_results: Scored rubric outcomes from S9/S10.
            gateway_revision_id: Explicit revision hash; computed if None.
            oral_defense_result: Scored oral defense outcome from S7.
            perturbation_results: Evaluated perturbation robustness outcomes.
            evidence_eligibility: Historical evidence eligibility report.

        Returns:
            GatewayVerdictRecord: Tamper-evident verdict.
        """
        rev_id = (
            gateway_revision_id or compute_gateway_revision_id(gateway_def)
        )
        perturbations = perturbation_results or []
        components: Dict[str, Any] = {
            "assessments": assessment_results,
            "oral_defense": oral_defense_result,
            "perturbations": perturbations,
            "evidence_eligibility": evidence_eligibility,
        }

        passed = True
        reasons: List[str] = []

        # 1. Practical laboratory tasks
        if gateway_def.practical_task_ids:
            if not assessment_results:
                passed = False
                reasons.append("Missing required practical assessments.")
            else:
                for idx, res in enumerate(assessment_results):
                    if not res.get("passed", False):
                        passed = False
                        det = res.get('details', '')
                        msg = f"Assessment {idx} failed: {det}"
                        reasons.append(msg)

        # 2. Oral Defense requirement
        if gateway_def.oral_defense_id is not None:
            if oral_defense_result is None:
                passed = False
                reasons.append("Missing required oral defense result.")
            elif not oral_defense_result.get("passed", False):
                passed = False
                det = oral_defense_result.get('details', '')
                msg = f"Oral defense failed: {det}"
                reasons.append(msg)

        # 3. Perturbation requirements
        if gateway_def.perturbation_ids:
            if not perturbations:
                passed = False
                reasons.append("Missing required perturbation evaluations.")
            else:
                for p_res in perturbations:
                    if not p_res.get("passed", False):
                        passed = False
                        msg = (
                            f"Perturbation failed: {p_res.get('details', '')}"
                        )
                        reasons.append(msg)

        # 4. Check historical evidence prerequisites
        if gateway_def.required_evidence_outcomes:
            if evidence_eligibility is None:
                passed = False
                reasons.append("Missing required evidence eligibility report.")
            elif not evidence_eligibility.get("eligible", False):
                passed = False
                reasons.append(
                    f"Historical evidence ineligible: "
                    f"{evidence_eligibility.get('reason', '')}"
                )

        now = datetime.now(timezone.utc)
        components["evaluation_reasons"] = reasons

        digest = compute_verdict_digest(
            verdict_id=verdict_id,
            gateway_id=gateway_def.gateway_id,
            gateway_revision_id=rev_id,
            student_id=student_id,
            passed=passed,
            evaluated_at=now,
            component_evaluations=components,
        )

        return GatewayVerdictRecord(
            verdict_id=verdict_id,
            gateway_id=gateway_def.gateway_id,
            gateway_revision_id=rev_id,
            student_id=student_id,
            passed=passed,
            evaluated_at=now,
            authority_id=self.AUTHORITY_ID,
            component_evaluations=components,
            verdict_digest=digest,
        )
