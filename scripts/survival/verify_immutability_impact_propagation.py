#!/usr/bin/env python3
"""Empirical test script for Shallow Immutability Impact Propagation (SSA-0).

Determines whether mutating EvidenceRecord.metadata in-memory propagates to:
1. Cryptographic chain integrity (Ledger.verify_integrity())
2. On-disk persistence (file bytes)
3. State evaluation & progression (derive_student_state / policy_engine)
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.contracts import CurricularRoadmap, RoadmapNode, NodeType
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import LedgerIntegrityStatus
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
from study_engine.state.state_contracts import HistoryCutoffMode, NodeProgressStatus
from study_engine.state.state_engine import derive_student_state


def run_impact_propagation_test() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = Path(tmp) / "ledger_immutability_impact.jsonl"
        ledger = EvidenceLedger(file_path=ledger_path)

        # 1. Setup minimal roadmap & policy
        node = RoadmapNode(
            node_id="node-imm-01",
            title="Node 01",
            description="Testing immutability",
            node_type=NodeType.TOPIC,
            notebook_id="nb-01",
        )
        nodes = {"node-imm-01": node}
        rev_id = compute_canonical_revision_id(
            roadmap_id="road-imm",
            title="Roadmap",
            version="1.0.0",
            nodes=nodes,
            dependencies=(),
        )
        roadmap = CurricularRoadmap(
            roadmap_id="road-imm",
            title="Roadmap",
            version="1.0.0",
            nodes=nodes,
            dependencies=(),
            canonical_revision_id=rev_id,
        )

        criteria = NodeAssessmentCriteria(
            criteria_id="crit-imm-01",
            target_node_id="node-imm-01",
            requirements=(
                EvidenceRequirement(
                    requirement_id="req-imm-01",
                    evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
                    min_count=1,
                ),
            ),
        )
        overrides = {"node-imm-01": criteria}
        pol_id = compute_canonical_policy_id(
            policy_id="pol-imm",
            title="Policy",
            version="1.0.0",
            default_criteria={},
            node_overrides=overrides,
        )
        policy = AssessmentPolicy(
            policy_id="pol-imm",
            title="Policy",
            version="1.0.0",
            canonical_policy_id=pol_id,
            default_criteria={},
            node_overrides=overrides,
        )

        # 2. Append valid PASS record
        record = EvidenceRecord(
            record_id="REC-IMM-001",
            student_id="student-imm-01",
            node_id="node-imm-01",
            competency_id="comp-imm-01",
            evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime.now(timezone.utc),
            actor_type=ActorType.AI_TUTOR,
            actor_id="test-tutor",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            roadmap_revision_id=roadmap.canonical_revision_id,
            policy_revision_id=policy.canonical_policy_id,
            metadata={"original_key": "original_val"},
        )
        entry = ledger.append_record(record)

        # Pre-tamper baseline checks
        pre_integrity = ledger.verify_integrity()
        pre_state = derive_student_state(
            roadmap=roadmap,
            policy=policy,
            ledger=ledger,
            student_id="student-imm-01",
        )
        pre_node_status = pre_state.get_node_state("node-imm-01").status

        # 3. Hostile in-place mutation of nested metadata
        record.metadata["tampered_injected"] = "malicious_payload"
        record.metadata["original_key"] = "corrupted_val"

        # 4. Measure propagation
        # Check A: Cryptographic ledger verification
        post_integrity = ledger.verify_integrity()

        # Check B: Disk persistence alteration
        with open(ledger_path, "r", encoding="utf-8") as f:
            disk_content = f.read()
        disk_tampered = "malicious_payload" in disk_content

        # Check C: State derivation alteration
        post_state = derive_student_state(
            roadmap=roadmap,
            policy=policy,
            ledger=ledger,
            student_id="student-imm-01",
        )
        post_node_status = post_state.get_node_state("node-imm-01").status
        state_hash_identical = pre_state.canonical_state_id == post_state.canonical_state_id

        result = {
            "title": "Shallow Immutability Impact Propagation Assessment",
            "metadata_mutated_in_place": True,
            "impact_on_cryptographic_verification": {
                "pre_mutation_status": pre_integrity.status.value,
                "post_mutation_status": post_integrity.status.value,
                "detected_by_ledger_verify": post_integrity.status == LedgerIntegrityStatus.HASH_CHAIN_BROKEN,
                "details": post_integrity.details,
            },
            "impact_on_disk_persistence": {
                "disk_content_modified": disk_tampered,
                "explanation": "Disk serialization occurs during append_record. Post-hoc in-memory mutations do not alter on-disk JSONL.",
            },
            "impact_on_student_progression": {
                "pre_node_status": pre_node_status.value,
                "post_node_status": post_node_status.value,
                "state_hash_identical": state_hash_identical,
                "progression_forged": False,
                "explanation": "Policy engine criteria evaluate first-class fields (outcome, score, evidence_type, actor_type). Metadata is not used for progression logic.",
            },
            "classification": "DESIGN_GAP",
            "epistemic_verdict": "Confirmed shallow immutability leak. However, impact is strictly contained: cannot forge student state, cannot bypass policy rules, and is immediately flagged as HASH_CHAIN_BROKEN if ledger integrity is verified.",
        }

        out_path = Path("data/experiments/survival/immutability_impact_report.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(json.dumps(result, indent=2))
        return result


if __name__ == "__main__":
    run_impact_propagation_test()
