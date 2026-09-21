"""Deterministic evaluation engine for Subsystem S5.2.A (Assessment Policy).

INVARIANTS:
1. Pure determinism: same (criteria, history, as_of_time) -> identical result.
2. Regression counts exclusively FAILs strictly after the last qualifying PASS.
3. EXEMPT is strictly human sovereign; AI/tools cannot produce EXEMPT.
4. Canonical policy hash is derived; declared hash mismatch raises error.
5. S4.4 audit required only when requires_audit_approved=True (LLM tutors).
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from study_engine.roadmap.contracts import NodeType
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationResult,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
    NodeAssessmentCriteria,
    PolicyHashMismatchError,
    SovereignExemptionViolationError,
)


def compute_canonical_policy_id(

    policy_id: str,
    title: str,
    version: str,
    default_criteria: Dict[NodeType, NodeAssessmentCriteria],
    node_overrides: Dict[str, NodeAssessmentCriteria],
) -> str:
    """Compute deterministic SHA-256 digest from canonical policy structure."""
    canonical_defaults: List[Dict[str, Any]] = []
    for node_type in sorted(default_criteria.keys(), key=lambda nt: nt.value):
        crit = default_criteria[node_type]
        canonical_defaults.append(_serialize_criteria(crit))

    canonical_overrides: List[Dict[str, Any]] = []
    for node_id in sorted(node_overrides.keys()):
        crit = node_overrides[node_id]
        canonical_overrides.append(_serialize_criteria(crit))

    payload = {
        "policy_id": policy_id,
        "title": title,
        "version": version,
        "default_criteria": canonical_defaults,
        "node_overrides": canonical_overrides,
    }

    raw_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()


def _serialize_criteria(crit: NodeAssessmentCriteria) -> Dict[str, Any]:
    """Serialize a NodeAssessmentCriteria deterministically."""
    sorted_reqs = sorted(crit.requirements, key=lambda r: r.requirement_id)
    serialized_reqs = []
    for req in sorted_reqs:
        serialized_reqs.append(
            {
                "requirement_id": req.requirement_id,
                "evidence_type": req.evidence_type.value,
                "min_count": req.min_count,
                "min_score": req.min_score,
                "max_age_days": req.max_age_days,
                "requires_audit_approved": req.requires_audit_approved,
                "required_tool_backend": req.required_tool_backend,
            }
        )

    return {
        "criteria_id": crit.criteria_id,
        "target_node_type": (
            crit.target_node_type.value if crit.target_node_type else None
        ),
        "target_node_id": crit.target_node_id,
        "requirements": serialized_reqs,
        "regression_threshold_failures": crit.regression_threshold_failures,
        "allow_exempt": crit.allow_exempt,
    }


def validate_policy_hash(policy: AssessmentPolicy) -> None:
    """Validate that declared policy hash matches computed canonical hash.

    Raises PolicyHashMismatchError if hashes diverge (strict rejection).
    """
    computed = compute_canonical_policy_id(
        policy_id=policy.policy_id,
        title=policy.title,
        version=policy.version,
        default_criteria=policy.default_criteria,
        node_overrides=policy.node_overrides,
    )
    if policy.canonical_policy_id != computed:
        raise PolicyHashMismatchError(
            f"Declared canonical_policy_id '{policy.canonical_policy_id}' "
            f"does not match computed canonical hash '{computed}'."
        )


def evaluate_node_criteria(
    criteria: NodeAssessmentCriteria,
    history: Sequence[EvidenceRecord],
    as_of_time: datetime,
    node_id: Optional[str] = None,
) -> CriteriaEvaluationResult:
    """Evaluate an evidence history against a node assessment criteria.

    Pure function: deterministic, zero side-effects, zero network/LLM calls.
    """
    effective_node_id = node_id or criteria.target_node_id

    # 1. Filter history: must be <= as_of_time, matching node_id if specified
    relevant_records: List[EvidenceRecord] = []
    for rec in history:
        if rec.timestamp > as_of_time:
            continue
        if effective_node_id and rec.node_id != effective_node_id:
            continue
        relevant_records.append(rec)

    # Sort chronologically ascending
    relevant_records.sort(key=lambda r: r.timestamp)

    # 2. Check Sovereign Exemption (MANUAL_OVERRIDE)
    for rec in relevant_records:
        if rec.evidence_type == EvidenceType.MANUAL_OVERRIDE:
            if not criteria.allow_exempt:
                raise SovereignExemptionViolationError(
                    f"Criteria '{criteria.criteria_id}' explicitly forbids "
                    f"EXEMPT status (allow_exempt=False)."
                )
            if rec.actor_type != ActorType.HUMAN:
                raise SovereignExemptionViolationError(
                    f"MANUAL_OVERRIDE produced by forbidden actor "
                    f"'{rec.actor_type.value}'. Only HUMAN allowed."
                )
            if not rec.rationale or not rec.rationale.strip():
                raise SovereignExemptionViolationError(
                    "MANUAL_OVERRIDE requires a non-empty rationale."
                )
            if not rec.roadmap_revision_id or not rec.policy_revision_id:
                raise SovereignExemptionViolationError(
                    "MANUAL_OVERRIDE requires explicit revision identifiers."
                )

            return CriteriaEvaluationResult(
                criteria_id=criteria.criteria_id,
                verdict=CriteriaEvaluationVerdict.EXEMPT,
                satisfied_requirements=(),
                missing_requirements=(),
                subsequent_failures_count=0,
                evaluation_timestamp=as_of_time,
                rationale=(
                    f"Exempt by sovereign authority: {rec.rationale}"
                ),
            )

    # 3. Evaluate Requirements for Satisfaction

    satisfied_reqs: List[str] = []
    missing_reqs: List[str] = []
    qualifying_pass_records: List[EvidenceRecord] = []

    for req in criteria.requirements:
        qualifying_for_req: List[EvidenceRecord] = []
        for rec in relevant_records:
            if rec.evidence_type != req.evidence_type:
                continue
            if rec.outcome != EvidenceOutcome.PASS:
                continue
            if rec.score < req.min_score:
                continue
            if req.requires_audit_approved and rec.audit_verdict != "APPROVED":
                continue
            if (
                req.required_tool_backend
                and rec.tool_backend != req.required_tool_backend
            ):
                continue
            if req.max_age_days is not None:
                age_days = (
                    as_of_time - rec.timestamp
                ).total_seconds() / 86400.0
                if age_days > req.max_age_days:
                    # Stale evidence does not count towards satisfaction
                    continue

            qualifying_for_req.append(rec)

        if len(qualifying_for_req) >= req.min_count:
            satisfied_reqs.append(req.requirement_id)
            qualifying_pass_records.extend(qualifying_for_req)
        else:
            missing_reqs.append(req.requirement_id)

    # If any requirement is missing, node is UNSATISFIED
    if missing_reqs:
        return CriteriaEvaluationResult(
            criteria_id=criteria.criteria_id,
            verdict=CriteriaEvaluationVerdict.UNSATISFIED,
            satisfied_requirements=tuple(satisfied_reqs),
            missing_requirements=tuple(missing_reqs),
            subsequent_failures_count=0,
            evaluation_timestamp=as_of_time,
            rationale=(
                f"Missing {len(missing_reqs)} requirement(s): {missing_reqs}."
            ),
        )

    # 4. Check for Regression strictly AFTER the latest qualifying PASS
    t_last_pass = max(r.timestamp for r in qualifying_pass_records)

    # Count FAIL records occurring strictly after t_last_pass
    subsequent_failures = [
        rec
        for rec in relevant_records
        if rec.timestamp > t_last_pass
        and rec.outcome == EvidenceOutcome.FAIL
    ]
    fail_count = len(subsequent_failures)

    if fail_count >= criteria.regression_threshold_failures:
        return CriteriaEvaluationResult(
            criteria_id=criteria.criteria_id,
            verdict=CriteriaEvaluationVerdict.REGRESSED,
            satisfied_requirements=tuple(satisfied_reqs),
            missing_requirements=(),
            subsequent_failures_count=fail_count,
            evaluation_timestamp=as_of_time,
            rationale=(
                f"Regression triggered: observed {fail_count} failure(s) "
                f"after last success "
                f"(threshold={criteria.regression_threshold_failures})."
            ),

        )

    return CriteriaEvaluationResult(
        criteria_id=criteria.criteria_id,
        verdict=CriteriaEvaluationVerdict.SATISFIED,
        satisfied_requirements=tuple(satisfied_reqs),
        missing_requirements=(),
        subsequent_failures_count=fail_count,
        evaluation_timestamp=as_of_time,
        rationale=(
            f"All {len(satisfied_reqs)} requirement(s) satisfied with "
            f"{fail_count} subsequent failure(s)."
        ),
    )
