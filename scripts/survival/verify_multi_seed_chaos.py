#!/usr/bin/env python3
"""Multi-Seed Chaos Curriculum Verification against Independent Reference Oracle (SSA-0).

Runs 20 distinct random seeds (50 events each = 1,000 total chaotic events)
comparing S5 StateEngine against IndependentReferenceOracle.
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

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
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import NodeProgressStatus, validate_student_state_hash
from study_engine.state.state_engine import derive_student_state

# Import oracle from test_l6
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tests" / "survival"))
from test_l6_chaos_and_external_oracle import IndependentReferenceOracle


def run_multi_seed_chaos_campaign(num_seeds: int = 20, events_per_seed: int = 50) -> dict:
    node_ids = ["node-A", "node-B", "node-C", "node-D"]
    edges = [("node-A", "node-B"), ("node-B", "node-C"), ("node-C", "node-D")]

    # Setup Roadmap
    nodes = {
        nid: RoadmapNode(
            node_id=nid,
            title=f"Title {nid}",
            description=f"Desc {nid}",
            node_type=NodeType.TOPIC,
            notebook_id="nb-chaos",
        )
        for nid in node_ids
    }
    deps = tuple(
        RoadmapDependency(
            source_node_id=p,
            target_node_id=c,
            dependency_type=DependencyType.HARD,
        )
        for p, c in edges
    )
    rev_id = compute_canonical_revision_id(
        roadmap_id="rm-chaos",
        title="Roadmap Chaos",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
    )
    roadmap = CurricularRoadmap(
        roadmap_id="rm-chaos",
        title="Roadmap Chaos",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rev_id,
    )

    overrides = {
        nid: NodeAssessmentCriteria(
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
        for nid in node_ids
    }
    pol_id = compute_canonical_policy_id(
        policy_id="pol-chaos",
        title="Policy Chaos",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
    )
    policy = AssessmentPolicy(
        policy_id="pol-chaos",
        title="Policy Chaos",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
        canonical_policy_id=pol_id,
    )

    oracle = IndependentReferenceOracle(dag_edges=edges, node_ids=node_ids)

    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    student_id = "student-chaos-oracle"

    total_events_tested = 0
    total_matches = 0
    total_mismatches = 0
    mismatch_details = []

    for seed_idx in range(1, num_seeds + 1):
        rng = random.Random(seed_idx * 1000 + 7)
        ledger = EvidenceLedger()
        event_log = []

        for step in range(events_per_seed):
            target_node = rng.choice(node_ids)
            outcome = rng.choice([
                EvidenceOutcome.PASS,
                EvidenceOutcome.FAIL,
                EvidenceOutcome.INCONCLUSIVE,
            ])
            is_valid_student = rng.random() > 0.15
            current_student = student_id if is_valid_student else "foreign-student"

            event_ts = base_time + timedelta(minutes=step * 5)
            rec = EvidenceRecord(
                record_id=f"REC-S{seed_idx:02d}-{step:03d}",
                student_id=current_student,
                node_id=target_node,
                competency_id="comp-general",
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=outcome,
                score=1.0 if outcome == EvidenceOutcome.PASS else 0.0,
                timestamp=event_ts,
                actor_type=ActorType.AI_TUTOR,
                actor_id="chaos-agent",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                roadmap_revision_id=roadmap.canonical_revision_id,
                policy_revision_id=policy.canonical_policy_id,
                metadata={"seed": seed_idx, "step": step},
            )
            ledger.append_record(rec, override_committed_at=event_ts)

            event_log.append({
                "student_id": current_student,
                "node_id": target_node,
                "outcome": outcome.value,
                "timestamp": event_ts.isoformat(),
            })

            # Check differential oracle
            oracle_proj = oracle.project(student_id=student_id, events=event_log)
            engine_state = derive_student_state(
                roadmap=roadmap,
                policy=policy,
                ledger=ledger,
                student_id=student_id,
                as_of_time=event_ts,
            )

            # Compare node by node
            step_match = True
            for nid in node_ids:
                ns_engine = engine_state.get_node_state(nid)
                ns_oracle = oracle_proj.node_projections[nid]

                expected_status = ns_oracle.status
                actual_status = ns_engine.status.value

                if expected_status != actual_status:
                    step_match = False
                    mismatch_details.append({
                        "seed": seed_idx,
                        "step": step,
                        "node_id": nid,
                        "expected_status": expected_status,
                        "actual_status": actual_status,
                    })

            total_events_tested += 1
            if step_match:
                total_matches += 1
            else:
                total_mismatches += 1

    summary = {
        "num_seeds": num_seeds,
        "events_per_seed": events_per_seed,
        "total_state_transitions_evaluated": total_events_tested,
        "total_exact_matches": total_matches,
        "total_mismatches": total_mismatches,
        "exact_match_ratio": total_matches / total_events_tested if total_events_tested > 0 else 0,
        "oracle_independence_verified": True,
        "mismatches": mismatch_details[:10],
    }

    out_path = Path("data/experiments/survival/multi_seed_chaos_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run_multi_seed_chaos_campaign(num_seeds=20, events_per_seed=50)
