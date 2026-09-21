"""Pure deterministic state synthesizer for Subsystem S5.2.C (State Engine).

INVARIANTS:
1. Pure function determinism: same inputs -> bitwise identical StudentState.
2. Topological derivation: parents evaluated strictly before descendants.
3. Hard blocking: if prerequisite is in NEEDS_REVIEW, descendants are LOCKED.
4. Soft non-blocking: soft prerequisites generate advisory warnings only.
5. Intrinsic assessment preservation: LOCKED nodes retain evaluation_result.
6. Historical ledger seal: ledger_cutoff_hash reflects cutoff entries only.
7. Strict student_id isolation: evidence from alien students is excluded.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from study_engine.roadmap.contracts import CurricularRoadmap, DependencyType
from study_engine.roadmap.engine import RoadmapDAG
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import HistoryCutoffMode
from study_engine.state.policy_contracts import (
    AssessmentPolicy,
    CriteriaEvaluationVerdict,

    EvidenceRecord,
    InvalidCriteriaConfigurationError,
)
from study_engine.state.policy_engine import (
    evaluate_node_criteria,
    validate_policy_hash,
)
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    NodeState,
    StudentState,
    compute_canonical_state_id,
)


def derive_student_state(
    roadmap: CurricularRoadmap,
    policy: AssessmentPolicy,
    ledger: EvidenceLedger,
    student_id: str,
    as_of_time: Optional[datetime] = None,
    cutoff_mode: HistoryCutoffMode = HistoryCutoffMode.COMMIT_TIME,
) -> StudentState:
    """Derive complete, immutable StudentState deterministically.

    Args:
        roadmap: Valid CurricularRoadmap graph (S5.1).
        policy: Valid AssessmentPolicy rulebook (S5.2.A).
        ledger: Historical EvidenceLedger (S5.2.B).
        student_id: Target student identifier.
        as_of_time: Temporal cutoff boundary. If None, current UTC is used.
        cutoff_mode: COMMIT_TIME (default) vs EVENT_TIME.

    Returns:
        Immutable StudentState with sealed cryptographic hashes.

    Raises:
        ValueError: If student_id is empty.
        PolicyHashMismatchError: If policy hash is invalid.
        InvalidCriteriaConfigurationError: If node lacks criteria.
    """
    if not student_id or not student_id.strip():
        raise ValueError("student_id must be a non-empty string.")

    # 1. Validate inputs and policies
    validate_policy_hash(policy)
    effective_as_of = as_of_time or datetime.now(timezone.utc)

    # 2. Derive historical ledger cutoff seal (HG-S5.2C-06)
    ledger_cutoff_hash = ledger.get_cutoff_tip_hash(
        as_of_time=effective_as_of,
        cutoff_mode=cutoff_mode,
    )

    # 3. Filter ledger entries strictly by student_id and cutoff (HG-S5.2C-07)
    node_evidence_map: Dict[str, List[EvidenceRecord]] = {}
    node_commit_ts_map: Dict[str, List[datetime]] = {}

    for entry in ledger._entries:
        if cutoff_mode == HistoryCutoffMode.COMMIT_TIME:
            if entry.committed_at > effective_as_of:
                continue
        elif cutoff_mode == HistoryCutoffMode.EVENT_TIME:
            if entry.record.timestamp > effective_as_of:
                continue

        # Strict student isolation
        if entry.record.student_id != student_id:
            continue

        n_id = entry.record.node_id
        node_evidence_map.setdefault(n_id, []).append(entry.record)
        node_commit_ts_map.setdefault(n_id, []).append(entry.committed_at)

    # 4. Construct DAG and extract topological order (HG-S5.2C-02)
    dag = RoadmapDAG.from_roadmap(roadmap)
    topological_node_ids = dag.get_topological_order()

    # Index incoming dependencies per node
    incoming_dependencies: Dict[str, List[Tuple[str, DependencyType]]] = {}
    for dep in roadmap.dependencies:
        incoming_dependencies.setdefault(dep.target_node_id, []).append(
            (dep.source_node_id, dep.dependency_type)
        )

    # 5. Topologically derive each node state
    node_status_map: Dict[str, NodeProgressStatus] = {}
    derived_node_states: List[NodeState] = []

    for node_id in topological_node_ids:
        node = roadmap.nodes[node_id]

        # a) Check prerequisites against already evaluated parent nodes
        unfulfilled_hard: List[str] = []
        unfulfilled_soft: List[str] = []

        for source_id, dep_type in incoming_dependencies.get(node.node_id, []):
            parent_status = node_status_map.get(
                source_id, NodeProgressStatus.LOCKED
            )
            # HARD prereq satisfied ONLY if ASSESSED_PROFICIENT or EXEMPT
            is_satisfied = parent_status in (
                NodeProgressStatus.ASSESSED_PROFICIENT,
                NodeProgressStatus.EXEMPT,
            )
            if not is_satisfied:
                if dep_type == DependencyType.HARD:
                    unfulfilled_hard.append(source_id)
                else:
                    unfulfilled_soft.append(source_id)

        # b) Evaluate intrinsic criteria from policy
        if node.node_id in policy.node_overrides:
            criteria = policy.node_overrides[node.node_id]
        elif node.node_type in policy.default_criteria:
            criteria = policy.default_criteria[node.node_type]
        else:
            raise InvalidCriteriaConfigurationError(
                f"No assessment criteria found for node '{node.node_id}' "
                f"of type '{node.node_type}'."
            )

        node_history = node_evidence_map.get(node.node_id, [])
        eval_result = evaluate_node_criteria(
            criteria=criteria,
            history=node_history,
            as_of_time=effective_as_of,
            node_id=node.node_id,
        )

        # c) Curricular Status Determination (HG-S5.2C-03 & HG-S5.2C-04)

        if unfulfilled_hard:
            # LOCKED due to unsatisfied hard prerequisites
            # Intrinsic evaluation_result is preserved!
            status = NodeProgressStatus.LOCKED
        else:
            if eval_result.verdict == CriteriaEvaluationVerdict.EXEMPT:
                status = NodeProgressStatus.EXEMPT
            elif eval_result.verdict == CriteriaEvaluationVerdict.SATISFIED:
                status = NodeProgressStatus.ASSESSED_PROFICIENT
            elif eval_result.verdict == CriteriaEvaluationVerdict.REGRESSED:
                status = NodeProgressStatus.NEEDS_REVIEW
            else:  # UNSATISFIED
                if not node_history:
                    status = NodeProgressStatus.AVAILABLE
                else:
                    status = NodeProgressStatus.IN_PROGRESS

        # d) Telemetry & Timestamps
        last_ev_ts = (
            max((r.timestamp for r in node_history), default=None)
            if node_history
            else None
        )
        commits = node_commit_ts_map.get(node.node_id, [])
        last_cm_ts = max(commits, default=None) if commits else None

        node_state = NodeState(
            node_id=node.node_id,
            status=status,
            evaluation_result=eval_result,
            unfulfilled_hard_prerequisites=tuple(sorted(unfulfilled_hard)),
            unfulfilled_soft_prerequisites=tuple(sorted(unfulfilled_soft)),
            total_evidence_count=len(node_history),
            last_event_timestamp=last_ev_ts,
            last_commit_timestamp=last_cm_ts,
        )

        node_status_map[node.node_id] = status
        derived_node_states.append(node_state)

    # 6. Sort node_states stably by node_id (HG-S5.2C-01)
    sorted_node_states = tuple(
        sorted(derived_node_states, key=lambda n: n.node_id)
    )

    # 7. Sello criptográfico no-autorreferencial (HG-S5.2C-05)
    canonical_state_id = compute_canonical_state_id(
        student_id=student_id,
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        ledger_cutoff_hash=ledger_cutoff_hash,
        as_of_time=effective_as_of,
        cutoff_mode=cutoff_mode,
        node_states=sorted_node_states,
    )

    return StudentState(
        student_id=student_id,
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        ledger_cutoff_hash=ledger_cutoff_hash,
        as_of_time=effective_as_of,
        cutoff_mode=cutoff_mode,
        node_states=sorted_node_states,
        canonical_state_id=canonical_state_id,
    )
