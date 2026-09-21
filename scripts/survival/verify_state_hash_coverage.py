#!/usr/bin/env python3
"""Empirical test script for StudentState Canonical Hash Coverage (SSA-0).

Audits every authority-bearing and operational field of StudentState and NodeState
to prove that modifying ANY field alters canonical_state_id and is detected by
validate_student_state_hash().
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.contracts import CurricularRoadmap, NodeType, RoadmapNode
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import (
    CriteriaEvaluationResult,
    HistoryCutoffMode,
    NodeProgressStatus,
    NodeState,
    StateHashMismatchError,
    StudentState,
    validate_student_state_hash,
)
from study_engine.state.state_engine import derive_student_state


def build_baseline_state() -> StudentState:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    node = RoadmapNode(
        node_id="node-cov-01",
        title="Coverage Node",
        description="Node for hash coverage test",
        node_type=NodeType.TOPIC,
        notebook_id="nb-cov",
    )
    nodes = {"node-cov-01": node}
    rev_id = compute_canonical_revision_id(
        roadmap_id="rm-cov",
        title="Roadmap Cov",
        version="1.0",
        nodes=nodes,
        dependencies=(),
    )
    roadmap = CurricularRoadmap(
        roadmap_id="rm-cov",
        title="Roadmap Cov",
        version="1.0",
        nodes=nodes,
        dependencies=(),
        canonical_revision_id=rev_id,
    )

    criteria = NodeAssessmentCriteria(
        criteria_id="crit-cov-01",
        target_node_id="node-cov-01",
        requirements=(
            EvidenceRequirement(
                requirement_id="req-cov-01",
                evidence_type=EvidenceType.CODE_EXECUTION,
                min_count=1,
            ),
        ),
    )
    pol_id = compute_canonical_policy_id(
        policy_id="pol-cov",
        title="Policy Cov",
        version="1.0",
        default_criteria={},
        node_overrides={"node-cov-01": criteria},
    )
    policy = AssessmentPolicy(
        policy_id="pol-cov",
        title="Policy Cov",
        version="1.0",
        default_criteria={},
        node_overrides={"node-cov-01": criteria},
        canonical_policy_id=pol_id,
    )

    ledger = EvidenceLedger()
    rec = EvidenceRecord(
        record_id="REC-COV-001",
        student_id="student-cov-01",
        node_id="node-cov-01",
        competency_id="comp-cov",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.AI_TUTOR,
        actor_id="test-cov-tutor",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
    )
    ledger.append_record(rec, override_committed_at=now)

    state = derive_student_state(
        student_id="student-cov-01",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        as_of_time=now + timedelta(hours=1),
    )
    validate_student_state_hash(state)
    return state


def run_field_coverage_audit() -> dict:
    base_state = build_baseline_state()
    field_checks = []

    # Helper to test mutation detection
    def check_mutation(description: str, mutated_state: StudentState) -> dict:
        caught = False
        error_msg = ""
        try:
            validate_student_state_hash(mutated_state)
        except StateHashMismatchError as e:
            caught = True
            error_msg = str(e)
        return {
            "field_or_subfield": description,
            "hash_diverged_and_caught": caught,
            "error_sample": error_msg[:80] + "..." if len(error_msg) > 80 else error_msg,
        }

    # Top-level StudentState fields
    field_checks.append(
        check_mutation(
            "student_id",
            base_state.model_copy(update={"student_id": "forged-student"}),
        )
    )
    field_checks.append(
        check_mutation(
            "roadmap_revision_id",
            base_state.model_copy(update={"roadmap_revision_id": "0" * 64}),
        )
    )
    field_checks.append(
        check_mutation(
            "policy_revision_id",
            base_state.model_copy(update={"policy_revision_id": "1" * 64}),
        )
    )
    field_checks.append(
        check_mutation(
            "ledger_cutoff_hash",
            base_state.model_copy(update={"ledger_cutoff_hash": "2" * 64}),
        )
    )
    field_checks.append(
        check_mutation(
            "as_of_time",
            base_state.model_copy(
                update={"as_of_time": base_state.as_of_time + timedelta(seconds=1)}
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "cutoff_mode",
            base_state.model_copy(
                update={"cutoff_mode": HistoryCutoffMode.EVENT_TIME}
            ),
        )
    )

    # NodeState fields
    orig_ns = base_state.node_states[0]

    def copy_with_node(mutated_node: NodeState) -> StudentState:
        return base_state.model_copy(update={"node_states": (mutated_node,)})

    field_checks.append(
        check_mutation(
            "node_states[0].node_id",
            copy_with_node(orig_ns.model_copy(update={"node_id": "forged-node"})),
        )
    )
    field_checks.append(
        check_mutation(
            "node_states[0].status",
            copy_with_node(
                orig_ns.model_copy(update={"status": NodeProgressStatus.LOCKED})
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "node_states[0].unfulfilled_hard_prerequisites",
            copy_with_node(
                orig_ns.model_copy(
                    update={"unfulfilled_hard_prerequisites": ("injected-prereq",)}
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "node_states[0].unfulfilled_soft_prerequisites",
            copy_with_node(
                orig_ns.model_copy(
                    update={"unfulfilled_soft_prerequisites": ("injected-soft",)}
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "node_states[0].total_evidence_count",
            copy_with_node(
                orig_ns.model_copy(
                    update={"total_evidence_count": orig_ns.total_evidence_count + 1}
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "node_states[0].last_event_timestamp",
            copy_with_node(
                orig_ns.model_copy(
                    update={
                        "last_event_timestamp": orig_ns.last_event_timestamp
                        + timedelta(minutes=1)
                    }
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "node_states[0].last_commit_timestamp",
            copy_with_node(
                orig_ns.model_copy(
                    update={
                        "last_commit_timestamp": orig_ns.last_commit_timestamp
                        + timedelta(minutes=1)
                    }
                )
            ),
        )
    )

    # CriteriaEvaluationResult subfields
    orig_ev = orig_ns.evaluation_result
    assert orig_ev is not None

    def copy_with_eval(mutated_ev: CriteriaEvaluationResult) -> StudentState:
        return copy_with_node(orig_ns.model_copy(update={"evaluation_result": mutated_ev}))

    field_checks.append(
        check_mutation(
            "evaluation_result.criteria_id",
            copy_with_eval(orig_ev.model_copy(update={"criteria_id": "forged-crit"})),
        )
    )
    field_checks.append(
        check_mutation(
            "evaluation_result.verdict",
            copy_with_eval(
                orig_ev.model_copy(
                    update={"verdict": CriteriaEvaluationVerdict.REGRESSED}
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "evaluation_result.satisfied_requirements",
            copy_with_eval(
                orig_ev.model_copy(
                    update={"satisfied_requirements": ("injected-req",)}
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "evaluation_result.missing_requirements",
            copy_with_eval(
                orig_ev.model_copy(
                    update={"missing_requirements": ("missing-req-99",)}
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "evaluation_result.subsequent_failures_count",
            copy_with_eval(
                orig_ev.model_copy(
                    update={
                        "subsequent_failures_count": orig_ev.subsequent_failures_count
                        + 1
                    }
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "evaluation_result.evaluation_timestamp",
            copy_with_eval(
                orig_ev.model_copy(
                    update={
                        "evaluation_timestamp": orig_ev.evaluation_timestamp
                        + timedelta(seconds=1)
                    }
                )
            ),
        )
    )
    field_checks.append(
        check_mutation(
            "evaluation_result.rationale",
            copy_with_eval(
                orig_ev.model_copy(update={"rationale": "Tampered rationale text"})
            ),
        )
    )

    total_tested = len(field_checks)
    total_caught = sum(1 for c in field_checks if c["hash_diverged_and_caught"])

    summary = {
        "title": "StudentState Canonical Hash Coverage Audit",
        "total_authority_fields_tested": total_tested,
        "total_fields_tamper_detected": total_caught,
        "tamper_detection_coverage_ratio": total_caught / total_tested,
        "all_fields_sealed": total_caught == total_tested,
        "detailed_results": field_checks,
    }

    out_path = Path("data/experiments/survival/state_hash_coverage_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run_field_coverage_audit()
