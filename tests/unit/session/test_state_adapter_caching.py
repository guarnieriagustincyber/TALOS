"""Unit tests for CurriculumStateAdapter deterministic cutoff-based caching (H4-DESIGN-03)."""

from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.gp_b_contracts import (
    NODE_DOWNSTREAM,
    NODE_ROOT,
    STUDENT_ID,
    build_assessment_policy,
    build_roadmap,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.session.adapters import CurriculumStateAdapter
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus


def _create_dummy_record(student_id: str, node_id: str, outcome: EvidenceOutcome = EvidenceOutcome.PASS) -> EvidenceRecord:
    rec_id = f"rec-test-{uuid.uuid4().hex[:8]}"
    return EvidenceRecord(
        record_id=rec_id,
        student_id=student_id,
        node_id=node_id,
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=outcome,
        score=1.0 if outcome == EvidenceOutcome.PASS else 0.0,
        timestamp=datetime.now(timezone.utc),
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="tool-verifier",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        overall_level=PerformanceLevel.N3_COMPETENT if outcome == EvidenceOutcome.PASS else PerformanceLevel.N1_INSUFFICIENT,
        tool_backend="python.adapter",
        metadata={"evaluation_attempt_id": f"att-{uuid.uuid4().hex[:8]}"},
    )


def test_state_adapter_caching_lifecycle():
    """Verify O(1) cache hit and deterministic invalidation upon new ledger commits."""
    roadmap = build_roadmap()
    policy = build_assessment_policy()
    ledger = EvidenceLedger()

    adapter = CurriculumStateAdapter(
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        student_id=STUDENT_ID,
    )

    assert adapter.projection_count == 0
    assert adapter.cache_hit_count == 0

    # 1. Initial lookup -> Cache miss (first derivation)
    s1 = adapter.get_node_state(NODE_ROOT)
    assert s1 is not None
    assert s1.status == NodeProgressStatus.AVAILABLE
    assert adapter.projection_count == 1
    assert adapter.cache_hit_count == 0

    # 2. Subsequent lookups -> Cache hits
    for _ in range(5):
        s = adapter.get_node_state(NODE_ROOT)
        assert s is not None
        assert s.status == NodeProgressStatus.AVAILABLE

    assert adapter.projection_count == 1
    assert adapter.cache_hit_count == 5

    # Also lookup downstream node -> should hit cached student state
    s_down = adapter.get_node_state(NODE_DOWNSTREAM)
    assert s_down is not None
    assert s_down.status == NodeProgressStatus.LOCKED
    assert adapter.projection_count == 1
    assert adapter.cache_hit_count == 6

    # 3. Append new evidence to ledger -> Invalidation triggered by tip hash mutation
    rec = _create_dummy_record(STUDENT_ID, NODE_ROOT, EvidenceOutcome.PASS)
    ledger.append_record(rec)

    # Next lookup must detect cutoff hash change, re-project, and update cache
    s_after = adapter.get_node_state(NODE_ROOT)
    assert s_after is not None
    assert s_after.status == NodeProgressStatus.ASSESSED_PROFICIENT
    assert adapter.projection_count == 2
    assert adapter.cache_hit_count == 6

    # Subsequent lookup hits new cache
    s_after_2 = adapter.get_node_state(NODE_DOWNSTREAM)
    assert s_after_2 is not None
    assert s_after_2.status == NodeProgressStatus.AVAILABLE
    assert adapter.projection_count == 2
    assert adapter.cache_hit_count == 7

    # 4. Explicit invalidation
    adapter.invalidate_cache()
    _ = adapter.get_node_state(NODE_ROOT)
    assert adapter.projection_count == 3
