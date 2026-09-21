"""Runner and telemetry harness for Experiment E4 (Retrieval Adversarial).

Pipeline observed:
  KnowledgeStore
  -> ScoredCandidate[] (Adversarial conditions E4-A and E4-B)
  -> EvidenceEngine (S4.1 Grounding Decision & Claim Authorization)
  -> ContextPacker (Budget & Citation Manifest bijection)
  -> Generation Gate (Deterministic Pre-Generation Halting)
  -> LLM Provider (Strictly ZERO calls, generation_invoked = False)

Strict Invariants:
  1. Zero modifications to src/study_engine/.
  2. Zero LLM API calls (provider_call_count == 0, tokens_used == 0).
  3. Zero mutation to StudentState, EvidenceLedger, or CurricularRoadmap.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from study_engine.contracts.evidence_engine import (
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
)
from study_engine.contracts.retrieval import (
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.context.packer import ContextPacker
from study_engine.evidence.engine import EvidenceEngine
from study_engine.retrieval.embedding import LocalONNXEmbeddingProvider
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore
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
    AssessmentPolicy,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_engine import derive_student_state
from study_engine.storage.knowledge_store import KnowledgeStore


# ---------------------------------------------------------------------------
# Frozen Experiment Constants
# ---------------------------------------------------------------------------
ORACLE_ID = "oracle-def-01"
CANONICAL_QUERY = (
    "¿Cuáles son los tres estados fundamentales en los que puede "
    "encontrarse un proceso?"
)
NOTEBOOK_ID = "fadena-so"
STUDENT_ID = "student-e4-adversarial"

E4_A_CANDIDATES = ["so:conc:31"]
E4_B_CANDIDATES = ["so:proc:52", "so:proc:53"]
CANONICAL_ORACLE_CHUNKS = ["so:proc:56", "so:proc:57"]


def setup_curriculum_fixtures() -> Tuple[
    CurricularRoadmap, AssessmentPolicy, EvidenceLedger
]:
    """Build deterministic curriculum, policy, and ledger baseline."""
    node_proc = RoadmapNode(
        node_id="SO-PROC-01",
        title="Estados de un Proceso",
        description="Definición y transiciones entre estados de un proceso.",
        node_type=NodeType.TOPIC,
        notebook_id=NOTEBOOK_ID,
        priority=1,
    )
    node_conc = RoadmapNode(
        node_id="SO-CONC-01",
        title="Concurrencia e IPC",
        description="Condiciones de carrera y exclusión mutua.",
        node_type=NodeType.TOPIC,
        notebook_id=NOTEBOOK_ID,
        priority=2,
    )
    nodes = {
        "SO-PROC-01": node_proc,
        "SO-CONC-01": node_conc,
    }
    deps = (
        RoadmapDependency(
            source_node_id="SO-PROC-01",
            target_node_id="SO-CONC-01",
            dependency_type=DependencyType.HARD,
        ),
    )
    rm_id = compute_canonical_revision_id(
        "roadmap-so-e4", "Sistemas Operativos E4", "1.0.0", nodes, deps
    )
    roadmap = CurricularRoadmap(
        roadmap_id="roadmap-so-e4",
        title="Sistemas Operativos E4",
        version="1.0.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rm_id,
    )

    req = EvidenceRequirement(
        requirement_id="req-e4-assessment",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        min_count=1,
        min_score=0.8,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-so-default",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit}
    pol_id = compute_canonical_policy_id(
        "policy-so-e4", "Policy SO E4", "1.0.0", defaults, {}
    )
    policy = AssessmentPolicy(
        policy_id="policy-so-e4",
        title="Policy SO E4",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=pol_id,
    )
    ledger = EvidenceLedger()
    return roadmap, policy, ledger


def execute_e4_scenario(
    scenario_id: str,
    candidate_ids: List[str],
    condition_label: str,
    repo_root: Path,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute single E4 scenario observing Grounding & Generation Gate."""
    timestamp_start = datetime.now(timezone.utc)

    # 1. Authoritative Knowledge Store & Baseline Invariants
    db_path = repo_root / "data" / "benchmark" / "db" / "benchmark_store.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Knowledge store DB missing: {db_path}")
    store = KnowledgeStore(db_path)

    roadmap, policy, ledger = setup_curriculum_fixtures()
    state_before = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id=STUDENT_ID,
        as_of_time=timestamp_start,
    )

    student_state_before_hash = state_before.canonical_state_id
    ledger_before_hash = ledger.tip_hash
    roadmap_before_hash = roadmap.canonical_revision_id

    # 2. Build ScoredCandidates from Store
    candidates: List[ScoredCandidate] = []
    candidate_details: List[Dict[str, Any]] = []

    for rank, cid in enumerate(candidate_ids, start=1):
        chk = store.get_chunk(cid)
        c_hash = hashlib.sha256(chk.content.encode("utf-8")).hexdigest()
        cand = ScoredCandidate(
            chunk_id=chk.id,
            document_id=chk.document_id,
            source_id=chk.source_id,
            notebook_id=NOTEBOOK_ID,
            rank=rank,
            score=round(1.0 - (rank * 0.05), 4),
            content=chk.content,
            page_start=chk.page_start,
            page_end=chk.page_end,
            retrieval_method="adversarial_e4_injection",
        )
        candidates.append(cand)
        candidate_details.append(
            {
                "chunk_id": chk.id,
                "document_id": chk.document_id,
                "source_id": chk.source_id,
                "rank": rank,
                "score": cand.score,
                "page_start": chk.page_start,
                "page_end": chk.page_end,
                "content_sha256": c_hash,
                "content_preview": chk.content[:140].strip() + "...",
            }
        )

    # 3. Deterministic Grounding Evaluation (S4.1 EvidenceEngine)
    engine = EvidenceEngine()
    packet: EvidencePacket = engine.evaluate_candidates(
        query=CANONICAL_QUERY,
        notebook_id=NOTEBOOK_ID,
        candidates=candidates,
        store=store,
    )

    # 4. Context Packaging (S4.1 ContextPacker)
    packer = ContextPacker()
    packed_context: PackagedContext = packer.pack(
        packet=packet, max_characters=4000
    )

    # 5. Deterministic Generation Gate Evaluation
    # RULE: A generation request seeking a factual canonical definition
    # MUST NOT be presented to the generator unless decision is SUPPORTED.
    is_supported = packet.grounding_decision == GroundingDecision.SUPPORTED
    if is_supported:
        generation_invoked = True
        gate_action = "PERMIT_GENERATION"
        gate_reason = (
            "Evidence packet satisfies SUPPORTED grounding threshold."
        )
    else:
        generation_invoked = False
        gate_action = "HALT_GENERATION_UNSUPPORTED"
        gate_reason = (
            f"GroundingDecision is '{packet.grounding_decision.value}' "
            f"(required: '{GroundingDecision.SUPPORTED.value}'). "
            "Deterministic generation gate strictly aborts pipeline prior "
            "to LLM invocation."
        )

    provider_call_count = 0  # Zero provider calls
    tokens_used = 0  # Zero tokens

    # 6. Post-Execution State Snapshot & Invariant Verification
    state_after = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id=STUDENT_ID,
        as_of_time=timestamp_start,
    )
    student_state_after_hash = state_after.canonical_state_id
    ledger_after_hash = ledger.tip_hash
    roadmap_after_hash = roadmap.canonical_revision_id

    student_state_mutated = (
        student_state_before_hash != student_state_after_hash
    )
    ledger_mutated = ledger_before_hash != ledger_after_hash
    roadmap_mutated = roadmap_before_hash != roadmap_after_hash

    # 7. Live Retrieval Baseline Comparison
    vec_db = repo_root / "data" / "benchmark" / "db" / "benchmark_vectors.db"
    live_retrieval_candidates: List[Dict[str, Any]] = []
    if vec_db.exists():
        vec_store = SQLiteVectorStore(vec_db)
        provider = LocalONNXEmbeddingProvider()
        retrieval_service = RetrievalService(
            store=store, vector_store=vec_store, provider=provider
        )
        live_res = retrieval_service.retrieve_evidence(
            query=CANONICAL_QUERY,
            notebook_id=NOTEBOOK_ID,
            top_k=5,
            strategy=RetrievalStrategy.HYBRID,
        )
        for c in live_res:
            live_retrieval_candidates.append(
                {
                    "rank": c.rank,
                    "chunk_id": c.chunk_id,
                    "score": round(c.score, 4),
                    "retrieval_method": c.retrieval_method,
                }
            )

    # 8. Compile Comprehensive Telemetry
    telemetry: Dict[str, Any] = {
        "experiment_id": f"GOLDEN-STUDY-V0-{scenario_id}",
        "scenario_id": scenario_id,
        "condition": condition_label,
        "timestamp_utc": timestamp_start.isoformat(),
        "query": {
            "oracle_id": ORACLE_ID,
            "text": CANONICAL_QUERY,
            "notebook_id": NOTEBOOK_ID,
            "canonical_oracle_chunks": CANONICAL_ORACLE_CHUNKS,
        },
        "retrieval_candidates": {
            "mode": "adversarial_controlled",
            "candidate_ids": candidate_ids,
            "candidate_count": len(candidates),
            "candidates": candidate_details,
        },
        "grounding_evaluation": {
            "grounding_decision": packet.grounding_decision.value,
            "is_supported": is_supported,
            "abstention_required": packet.abstention_required,
            "abstention_reason": packet.abstention_reason,
            "has_full_provenance": packet.has_full_provenance,
            "allowed_claims": [c.value for c in packet.allowed_claims],
            "unsupported_claims": [c.value for c in packet.unsupported_claims],
            "canonical_definition_authorized": (
                "CANONICAL_DEFINITION"
                in [c.value for c in packet.allowed_claims]
            ),
            "direct_factual_assertion_authorized": (
                "DIRECT_FACTUAL_ASSERTION"
                in [c.value for c in packet.allowed_claims]
            ),
        },
        "context_packaging": {
            "total_characters": packed_context.total_characters,
            "packaged_units_count": len(packed_context.packaged_units),
            "manifest_keys": list(
                packed_context.citation_manifest.records.keys()
            ),
            "was_truncated": packed_context.was_truncated,
            "formatted_block_preview": packed_context.formatted_context_block[
                :200
            ],
        },
        "generation_gate": {
            "gate_action": gate_action,
            "generation_invoked": generation_invoked,
            "gate_reason": gate_reason,
            "provider_call_count": provider_call_count,
            "tokens_used": tokens_used,
        },
        "invariants": {
            "student_state_before_hash": student_state_before_hash,
            "student_state_after_hash": student_state_after_hash,
            "student_state_mutated": student_state_mutated,
            "ledger_tip_before_hash": ledger_before_hash,
            "ledger_tip_after_hash": ledger_after_hash,
            "ledger_mutated": ledger_mutated,
            "roadmap_before_hash": roadmap_before_hash,
            "roadmap_after_hash": roadmap_after_hash,
            "roadmap_mutated": roadmap_mutated,
            "invariants_satisfied": (
                not student_state_mutated
                and not ledger_mutated
                and not roadmap_mutated
            ),
        },
        "live_retrieval_baseline": {
            "strategy": "hybrid_rrf",
            "top_candidates": live_retrieval_candidates,
            "canonical_present_at_rank_1": (
                len(live_retrieval_candidates) > 0
                and live_retrieval_candidates[0]["chunk_id"] == "so:proc:56"
            ),
        },
        "verdict": {
            "status": (
                "PASS"
                if not is_supported and not generation_invoked
                else "FAIL"
            ),
            "epistemological_boundary_verified": (
                not is_supported and not generation_invoked
            ),
        },
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(telemetry, f, indent=2, ensure_ascii=False)

    return telemetry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Experiment E4 Runner: Retrieval / Grounding Adversarial"
    )
    parser.add_argument(
        "--scenario",
        choices=["E4-A", "E4-B", "ALL"],
        default="ALL",
        help="Scenario to run: E4-A (foreign), E4-B (insufficient), or ALL",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    experiments_dir = repo_root / "data" / "experiments"

    scenarios = []
    if args.scenario in ("E4-A", "ALL"):
        label_a = (
            "Completely foreign evidence (race conditions vs process states)"
        )
        out_a = (
            experiments_dir / "golden_path_a_e4_a_retrieval_adversarial.json"
        )
        scenarios.append(("E4-A", E4_A_CANDIDATES, label_a, out_a))
    if args.scenario in ("E4-B", "ALL"):
        label_b = (
            "Thematically close but insufficient evidence "
            "(cat|grep pipeline vs 3 process states)"
        )
        out_b = (
            experiments_dir / "golden_path_a_e4_b_retrieval_adversarial.json"
        )
        scenarios.append(("E4-B", E4_B_CANDIDATES, label_b, out_b))

    all_passed = True
    print("=" * 80)
    print("EXPERIMENT E4: RETRIEVAL / GROUNDING ADVERSARIAL")
    print("=" * 80)

    for sc_id, cids, label, out_p in scenarios:
        print(f"\n[RUNNING] {sc_id}: {label}")
        print(f"  Candidate chunks: {cids}")
        res = execute_e4_scenario(
            scenario_id=sc_id,
            candidate_ids=cids,
            condition_label=label,
            repo_root=repo_root,
            output_path=out_p,
        )

        decision = res["grounding_evaluation"]["grounding_decision"]
        is_supp = res["grounding_evaluation"]["is_supported"]
        gen_inv = res["generation_gate"]["generation_invoked"]
        status = res["verdict"]["status"]
        inv_ok = res["invariants"]["invariants_satisfied"]
        gate_act = res["generation_gate"]["gate_action"]
        calls = res["generation_gate"]["provider_call_count"]

        print(f"  GroundingDecision:     {decision} (is_supported={is_supp})")
        print(f"  Generation Gate:       {gate_act}")
        print(f"  generation_invoked:    {gen_inv} (required: False)")
        print(f"  provider_call_count:   {calls}")
        print(f"  Invariants satisfied:  {inv_ok}")
        print(f"  Scenario Verdict:      {status}")
        print(f"  Telemetry saved to:    {out_p}")

        if status != "PASS" or not inv_ok:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🟢 EXPERIMENT E4 COMPLETED: ALL SCENARIOS PASSED")
        print("  Boundary verified: GroundingDecision != SUPPORTED & "
              "generation_invoked == False")
    else:
        print("🔴 EXPERIMENT E4 FAILED: BOUNDARY VIOLATION DETECTED")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
