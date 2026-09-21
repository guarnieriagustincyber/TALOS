"""Layer L6 Hostile Survival Audit: Independent Reference Oracle & Chaos Curriculum.

Part of SYSTEM SURVIVAL AUDIT — SSA-0.
Modalidad: Read-Only / Red Team / No Patch.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import random
from typing import Dict, List, Optional, Set, Tuple
import pytest

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
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
    HistoryCutoffMode,
    NodeProgressStatus,
    StudentState,
    validate_student_state_hash,
)
from study_engine.state.state_engine import derive_student_state


# =============================================================================
# INDEPENDENT REFERENCE ORACLE (BUILT COMPLETELY OUTSIDE S5)
# =============================================================================

@dataclass(frozen=True)
class CanonicalNodeProjection:
    node_id: str
    status: str
    verdict: str
    qualifying_pass_count: int
    unfulfilled_hard_prereqs: Tuple[str, ...]


@dataclass(frozen=True)
class CanonicalStateProjection:
    student_id: str
    node_projections: Dict[str, CanonicalNodeProjection]


class IndependentReferenceOracle:
    """Minimalist, independent formal state machine model.

    Implements pure topological projection without using S5 codebase internals.
    """

    def __init__(self, dag_edges: List[Tuple[str, str]], node_ids: List[str]):
        self.node_ids = sorted(node_ids)
        self.hard_prereqs: Dict[str, List[str]] = {nid: [] for nid in self.node_ids}
        for parent, child in dag_edges:
            self.hard_prereqs[child].append(parent)

    def project(
        self, student_id: str, events: List[Dict[str, str]]
    ) -> CanonicalStateProjection:
        # Separate events per node for student
        node_events: Dict[str, List[Dict[str, str]]] = {
            nid: [] for nid in self.node_ids
        }
        for ev in events:
            if ev["student_id"] == student_id and ev["node_id"] in node_events:
                node_events[ev["node_id"]].append(ev)

        projections: Dict[str, CanonicalNodeProjection] = {}
        resolved_status: Dict[str, str] = {}

        # Topological pass A -> B -> C -> D
        for node_id in self.node_ids:
            history = node_events[node_id]

            # 1. Evaluate intrinsic criteria
            pass_count = sum(1 for e in history if e["outcome"] == "PASS")
            has_pass = pass_count >= 1

            # Check regression
            last_pass_idx = -1
            for idx, e in enumerate(history):
                if e["outcome"] == "PASS":
                    last_pass_idx = idx

            fails_after_pass = 0
            if last_pass_idx >= 0:
                fails_after_pass = sum(
                    1
                    for e in history[last_pass_idx + 1 :]
                    if e["outcome"] == "FAIL"
                )

            if not has_pass:
                verdict = "UNSATISFIED"
            elif fails_after_pass >= 1:
                verdict = "REGRESSED"
            else:
                verdict = "SATISFIED"

            # 2. Check hard prerequisites
            unfulfilled = []
            for parent_id in self.hard_prereqs[node_id]:
                parent_st = resolved_status.get(parent_id, "LOCKED")
                if parent_st not in ("ASSESSED_PROFICIENT", "EXEMPT"):
                    unfulfilled.append(parent_id)

            unfulfilled_tuple = tuple(sorted(unfulfilled))

            # 3. Determine status
            if unfulfilled_tuple:
                status = "LOCKED"
            else:
                if verdict == "SATISFIED":
                    status = "ASSESSED_PROFICIENT"
                elif verdict == "REGRESSED":
                    status = "NEEDS_REVIEW"
                else:
                    status = (
                        "IN_PROGRESS" if len(history) > 0 else "AVAILABLE"
                    )

            resolved_status[node_id] = status
            projections[node_id] = CanonicalNodeProjection(
                node_id=node_id,
                status=status,
                verdict=verdict,
                qualifying_pass_count=pass_count,
                unfulfilled_hard_prereqs=unfulfilled_tuple,
            )

        return CanonicalStateProjection(
            student_id=student_id, node_projections=projections
        )


def extract_s5_canonical_projection(
    state: StudentState,
) -> CanonicalStateProjection:
    """Extract canonical projection from real S5.2.C StudentState."""
    projections = {}
    for ns in state.node_states:
        verdict_str = (
            ns.evaluation_result.verdict.value
            if ns.evaluation_result
            else "UNSATISFIED"
        )
        projections[ns.node_id] = CanonicalNodeProjection(
            node_id=ns.node_id,
            status=ns.status.value,
            verdict=verdict_str,
            qualifying_pass_count=(
                len(ns.evaluation_result.satisfied_requirements)
                if (ns.evaluation_result and ns.evaluation_result.satisfied_requirements)
                else (1 if verdict_str == "SATISFIED" else 0)
            ),
            unfulfilled_hard_prereqs=ns.unfulfilled_hard_prerequisites,
        )
    return CanonicalStateProjection(
        student_id=state.student_id, node_projections=projections
    )


# =============================================================================
# L6: CHAOS CURRICULUM MODEL CHECKING (50 PSEUDORANDOM EVENTS)
# =============================================================================

def test_l6_chaos_curriculum_differential_oracle_validation():
    """Execute a 50-event chaotic curriculum against S5 and verify bitwise semantic parity with oracle."""
    rng = random.Random(42)  # Deterministic seed for audit reproducibility
    student_id = "student-chaos-01"
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    # 1. Define Pipeline DAG: node-A -> node-B -> node-C -> node-D
    pipeline_nodes = ["node-A", "node-B", "node-C", "node-D"]
    pipeline_edges = [
        ("node-A", "node-B"),
        ("node-B", "node-C"),
        ("node-C", "node-D"),
    ]

    nodes_dict = {}
    for nid in pipeline_nodes:
        nodes_dict[nid] = RoadmapNode(
            node_id=nid,
            title=f"Title {nid}",
            description=f"Desc {nid}",
            node_type=NodeType.TOPIC,
            notebook_id="nb-01",
        )

    deps = []
    for parent, child in pipeline_edges:
        deps.append(
            RoadmapDependency(
                source_node_id=parent,
                target_node_id=child,
                dependency_type=DependencyType.HARD,
            )
        )

    rev_id = compute_canonical_revision_id(
        roadmap_id="rm-chaos",
        title="Chaos Roadmap",
        version="1.0",
        nodes=nodes_dict,
        dependencies=tuple(deps),
    )
    roadmap = CurricularRoadmap(
        roadmap_id="rm-chaos",
        title="Chaos Roadmap",
        version="1.0",
        nodes=nodes_dict,
        dependencies=tuple(deps),
        canonical_revision_id=rev_id,
    )

    overrides = {}
    for nid in pipeline_nodes:
        overrides[nid] = NodeAssessmentCriteria(
            criteria_id=f"crit-{nid}",
            target_node_id=nid,
            requirements=(
                EvidenceRequirement(
                    requirement_id=f"req-{nid}",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    min_count=1,
                ),
            ),
            regression_threshold_failures=1,
        )

    pol_id = compute_canonical_policy_id(
        policy_id="pol-chaos",
        title="Chaos Policy",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
    )
    policy = AssessmentPolicy(
        policy_id="pol-chaos",
        title="Chaos Policy",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
        canonical_policy_id=pol_id,
    )

    # 2. Generate 50 chaotic events
    oracle = IndependentReferenceOracle(
        dag_edges=pipeline_edges, node_ids=pipeline_nodes
    )
    oracle_events: List[Dict[str, str]] = []
    ledger = EvidenceLedger()

    outcomes = [
        EvidenceOutcome.PASS,
        EvidenceOutcome.FAIL,
        EvidenceOutcome.INCONCLUSIVE,
    ]

    for i in range(50):
        target_node = rng.choice(pipeline_nodes)
        outcome = rng.choice(outcomes)
        ev_time = base_time + timedelta(minutes=i * 10)

        oracle_events.append(
            {
                "student_id": student_id,
                "node_id": target_node,
                "outcome": outcome.value,
                "timestamp": ev_time.isoformat(),
            }
        )

        score = 1.0 if outcome == EvidenceOutcome.PASS else 0.0
        rec = EvidenceRecord(
            record_id=f"ev-chaos-{i:03d}",
            student_id=student_id,
            node_id=target_node,
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=outcome,
            score=score,
            timestamp=ev_time,
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="gcc",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            roadmap_revision_id=roadmap.canonical_revision_id,
            policy_revision_id=policy.canonical_policy_id,
        )
        ledger.append_record(rec, override_committed_at=ev_time)

    # 3. Derive State via S5.2.C StateEngine
    as_of = base_time + timedelta(hours=24)
    s5_state = derive_student_state(
        student_id=student_id,
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )

    validate_student_state_hash(s5_state)

    # 4. Compute Oracle Projection
    oracle_proj = oracle.project(student_id=student_id, events=oracle_events)
    s5_proj = extract_s5_canonical_projection(s5_state)

    # 5. Differential Comparison between S5 and Independent Oracle
    print("\n--- CHAOS CURRICULUM DIFFERENTIAL COMPARISON (50 EVENTS) ---")
    for nid in pipeline_nodes:
        s5_n = s5_proj.node_projections[nid]
        ora_n = oracle_proj.node_projections[nid]
        print(f"Node {nid}:")
        print(f"  S5 State    : status={s5_n.status}, verdict={s5_n.verdict}, prereqs={s5_n.unfulfilled_hard_prereqs}")
        print(f"  Oracle State: status={ora_n.status}, verdict={ora_n.verdict}, prereqs={ora_n.unfulfilled_hard_prereqs}")

        assert s5_n.status == ora_n.status, (
            f"DIFFERENTIAL DIVERGENCE on {nid} status: S5={s5_n.status} vs Oracle={ora_n.status}"
        )
        assert s5_n.verdict == ora_n.verdict, (
            f"DIFFERENTIAL DIVERGENCE on {nid} verdict: S5={s5_n.verdict} vs Oracle={ora_n.verdict}"
        )
        assert s5_n.unfulfilled_hard_prereqs == ora_n.unfulfilled_hard_prereqs, (
            f"DIFFERENTIAL DIVERGENCE on {nid} prereqs: S5={s5_n.unfulfilled_hard_prereqs} vs Oracle={ora_n.unfulfilled_hard_prereqs}"
        )

    print("--> DIFFERENTIAL ORACLE VALIDATION: 100% CANONICAL STATE PROJECTION PARITY CONFIRMED!")
