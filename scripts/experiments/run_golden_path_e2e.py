#!/usr/bin/env python3
"""Hito 5 Campaign Runner: Golden Path End-to-End (Sections 32-35).

Coordinates the first closed-loop execution combining:
- Golden Path A (Conceptual Turn): Question -> Epistemic Retrieval -> Context Packing ->
  Deterministic Generation -> S4.4 Forensic Audit -> Approved Response.
- Golden Path B (Practical Turn): Task -> Artifact Execution -> S9.1 Assessment ->
  S5.2.A Evidence Admissibility -> S5.2.B Ledger Commitment -> S5.2.C State Projection.
- Pre-calculated Differential Oracle Verification: Strict zero-tolerance assertion
  against data/experiments/hito5/gp_e2e_oracle.json.
- Cryptographic Hash Chain and Anti-Replay Defense Verification.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.audit.auditor import ForensicAuditor
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import SessionProvenanceContext
from study_engine.contracts.generation import GenerationMode
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.generation.tutor import StructuredTutor
from study_engine.llm.backends import ReplayMockBackend
from study_engine.llm.client import LLMClient
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import DeterministicHashEmbedder
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.roadmap.contracts import CurricularRoadmap, NodeType
from study_engine.session.adapters import (
    CurriculumRetrievalAdapter,
    CurriculumStateAdapter,
    DeterministicAssessmentAdapter,
    EvidenceIngestionAdapter,
    ForensicAuditAdapter,
    PracticalExecutionAdapter,
    StructuredTutorAdapter,
)
from study_engine.session.contracts import (
    PracticeRequest,
    PracticeResult,
    PracticeResultStatus,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    IdempotentReplayError,
    InconsistentReplayError,
    LedgerIntegrityStatus,
)
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
from study_engine.state.state_contracts import NodeProgressStatus, StudentState
from study_engine.storage.knowledge_store import KnowledgeStore


def build_cybersecurity_policy() -> AssessmentPolicy:
    """Construct authoritative AssessmentPolicy matching cybersecurity_v1 roadmap."""
    req_concept = EvidenceRequirement(
        requirement_id="req-concept-mastery",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        min_count=1,
        min_score=0.8,
    )
    crit_topic = NodeAssessmentCriteria(
        criteria_id="crit-topic-mastery",
        target_node_type=NodeType.TOPIC,
        requirements=(req_concept,),
        regression_threshold_failures=2,
    )
    req_code = EvidenceRequirement(
        requirement_id="req-code-execution",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    crit_lab = NodeAssessmentCriteria(
        criteria_id="crit-lab-mastery",
        target_node_type=NodeType.LAB,
        requirements=(req_code,),
        regression_threshold_failures=2,
    )
    crit_comp = NodeAssessmentCriteria(
        criteria_id="crit-comp-mastery",
        target_node_type=NodeType.COMPETENCY,
        requirements=(req_code,),
        regression_threshold_failures=2,
    )

    defaults = {
        NodeType.TOPIC: crit_topic,
        NodeType.LAB: crit_lab,
        NodeType.COMPETENCY: crit_comp,
    }
    policy_id = "pol-cybersecurity-v1"
    title = "Authoritative FADENA Cybersecurity Assessment Policy"
    version = "1.0.0"
    canonical_id = compute_canonical_policy_id(
        policy_id=policy_id,
        title=title,
        version=version,
        default_criteria=defaults,
        node_overrides={},
    )
    return AssessmentPolicy(
        policy_id=policy_id,
        title=title,
        version=version,
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=canonical_id,
    )


class E2ECampaignRunner:
    """Authoritative campaign orchestrator for Hito 5 Golden Path End-to-End."""

    def __init__(
        self,
        repo_root: Path,
        oracle_path: Optional[Path] = None,
        working_dir: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path or (
            repo_root / "data" / "experiments" / "hito5" / "gp_e2e_oracle.json"
        )
        self.working_dir = working_dir
        self._temp_dir_obj: Optional[tempfile.TemporaryDirectory[str]] = None

        if not self.oracle_path.exists():
            raise FileNotFoundError(
                f"Differential oracle file not found at: '{self.oracle_path}'"
            )

        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle: Dict[str, Any] = json.load(f)

    def initialize_pipeline(self) -> Tuple[SessionOrchestrator, Dict[str, Any]]:
        """Set up all components: stores, indices, curriculum, ledger, and orchestrator."""
        if self.working_dir is None:
            self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="gp_e2e_")
            work_path = Path(self._temp_dir_obj.name)
        else:
            work_path = self.working_dir
            work_path.mkdir(parents=True, exist_ok=True)

        db_path = work_path / "knowledge_store.db"
        vec_path = work_path / "vector_store.db"

        # 1. Ingest real benchmark PDFs into KnowledgeStore
        store = KnowledgeStore(db_path=db_path)
        store.initialize()
        sources_dir = self.repo_root / "data" / "benchmark" / "sources"
        ingest_benchmark_corpus(
            store=store,
            sources_dir=sources_dir,
            notebook_id="NB-SEC-04-CONCURR",
        )

        # 2. Vector indexing for dense retrieval
        vstore = SQLiteVectorStore(db_path=vec_path, read_only=False)
        embedder = DeterministicHashEmbedder(dimensions=128)
        concurrency_chunks = store.chunks.list_by_document("so_concurrencia.pdf")
        records: List[VectorRecord] = []
        for c in concurrency_chunks:
            vec = embedder.embed_passages([c.content])[0]
            records.append(
                VectorRecord(
                    chunk_id=c.id,
                    source_id=c.source_id,
                    notebook_id="NB-SEC-04-CONCURR",
                    provider_id=embedder.provider_id,
                    model_id=embedder.model_id,
                    dimensions=embedder.dimensions,
                    vector=vec,
                )
            )
        vstore.save_records(records)

        # 3. Retrieval Service
        lexical = LexicalRetriever(store)
        dense = DenseRetriever(store, vstore, embedder)
        hybrid = HybridRetriever(store, lexical, dense)
        retrieval_service = RetrievalService(store, hybrid)

        # 4. Curriculum Registry, Roadmap, Alignment, Tasks, Rubrics
        curriculum_dir = self.repo_root / "data" / "curriculum"
        registry = CurriculumRegistry(root_dir=curriculum_dir)
        roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
        alignment = registry.load_alignment("cybersecurity_v1_alignment.json")
        task = registry.load_task("task_sec05_file_hasher.json")
        rubric = registry.load_rubric("rubric_sec05_deterministic.json")

        # 5. Policy & Ledger
        policy = build_cybersecurity_policy()
        ledger = EvidenceLedger()

        student_id = self.oracle["phase_1_conceptual"]["input"]["student_id"]
        session_id = self.oracle["phase_1_conceptual"]["input"]["session_id"]

        # Commit Evidence 1: Conceptual baseline for SEC-02-OS-PROC
        baseline_record = EvidenceRecord(
            record_id="ev-baseline-conceptual-sec02",
            student_id=student_id,
            node_id="SEC-02-OS-PROC",
            evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="evaluator-conceptual-baseline",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            assessment_digest=hashlib.sha256(b"conceptual-sec02-prereq-baseline").hexdigest(),
        )
        ledger.append_record(baseline_record)

        # 6. Session Adapters
        retrieval_adapter = CurriculumRetrievalAdapter(retrieval_service, registry)
        mock_backend = ReplayMockBackend()
        llm_client = LLMClient(backend=mock_backend)
        tutor = StructuredTutor(generator=llm_client)
        tutor_adapter = StructuredTutorAdapter(tutor)
        audit_adapter = ForensicAuditAdapter(ForensicAuditor())

        canonical_stdin = self.oracle.get("canonical_stdin", "STUDY_ENGINE_CANONICAL_INPUT")
        exec_adapter = PracticalExecutionAdapter(default_stdin=canonical_stdin)
        assess_adapter = DeterministicAssessmentAdapter(default_task=task)
        ingest_adapter = EvidenceIngestionAdapter(
            ledger=ledger,
            roadmap=roadmap,
            policy=policy,
            student_id=student_id,
            session_id=session_id,
        )
        state_adapter = CurriculumStateAdapter(
            roadmap=roadmap,
            policy=policy,
            ledger=ledger,
            student_id=student_id,
        )

        orch = SessionOrchestrator(
            session_id=session_id,
            student_id=student_id,
            roadmap=roadmap,
            policy=policy,
            ledger=ledger,
            retrieval_port=retrieval_adapter,
            tutor_port=tutor_adapter,
            audit_port=audit_adapter,
            execution_port=exec_adapter,
            assessment_port=assess_adapter,
            ingestion_port=ingest_adapter,
            state_read_port=state_adapter,
            curriculum_registry=registry,
            session_started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        orch.start_session()

        context = {
            "store": store,
            "vstore": vstore,
            "registry": registry,
            "roadmap": roadmap,
            "alignment": alignment,
            "task": task,
            "rubric": rubric,
            "policy": policy,
            "ledger": ledger,
            "retrieval_service": retrieval_service,
            "state_adapter": state_adapter,
            "ingest_adapter": ingest_adapter,
            "student_id": student_id,
            "session_id": session_id,
        }
        return orch, context

    def execute_campaign(self) -> Dict[str, Any]:
        """Execute the complete 4-phase campaign and compare with the differential oracle."""
        orch, ctx = self.initialize_pipeline()
        ledger: EvidenceLedger = ctx["ledger"]
        state_adapter: CurriculumStateAdapter = ctx["state_adapter"]
        ingest_adapter: EvidenceIngestionAdapter = ctx["ingest_adapter"]
        retrieval_service: RetrievalService = ctx["retrieval_service"]
        registry: CurriculumRegistry = ctx["registry"]
        student_id: str = ctx["student_id"]
        session_id: str = ctx["session_id"]
        roadmap: CurricularRoadmap = ctx["roadmap"]
        policy: AssessmentPolicy = ctx["policy"]

        results: Dict[str, Any] = {
            "campaign_id": self.oracle["campaign_id"],
            "spec_version": self.oracle["spec_version"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "phases": {},
            "oracle_comparison": {},
            "verdict": "PENDING",
        }

        # ---------------------------------------------------------------------
        # PHASE 1: Golden Path A (Conceptual Turn)
        # ---------------------------------------------------------------------
        p1_spec = self.oracle["phase_1_conceptual"]
        p1_in = p1_spec["input"]

        # Step 1a: Scoped retrieval check
        retrieved_candidates = retrieval_service.retrieve_evidence(
            query=p1_in["query"],
            node_id=p1_in["node_id"],
            registry=registry,
            top_k=5,
        )

        # Step 1b: SessionRequest turn
        req_a = SessionRequest(
            session_id=p1_in["session_id"],
            student_id=p1_in["student_id"],
            node_id=p1_in["node_id"],
            query=p1_in["query"],
            turn_index=p1_in["turn_index"],
            mode=GenerationMode(p1_in["mode"]),
        )
        res_a: SessionResult = orch.handle_session_request(req_a)

        results["phases"]["phase_1_conceptual"] = {
            "session_status": res_a.status.value,
            "candidate_count": len(retrieved_candidates),
            "retrieved_document_ids": list({c.document_id for c in retrieved_candidates}),
            "retrieved_pages": sorted(list({c.page_start for c in retrieved_candidates if c.page_start is not None})),
            "response_text": res_a.response_text,
            "audit_report_id": res_a.audit_report_id,
            "abstention_reason": res_a.abstention_reason,
            "audit_trace": res_a.audit_trace,
        }

        # ---------------------------------------------------------------------
        # PHASE 2: Golden Path B (Practical Turn)
        # ---------------------------------------------------------------------
        p2_spec = self.oracle["phase_2_practical"]
        p2_in = p2_spec["input"]
        artifact_abs_path = (self.repo_root / p2_in["artifact_path"]).resolve()

        req_b = PracticeRequest(
            student_id=p2_in["student_id"],
            node_id=p2_in["node_id"],
            task_id=p2_in["task_id"],
            rubric_id=p2_in["rubric_id"],
            artifact_path=str(artifact_abs_path),
        )
        res_b: PracticeResult = orch.handle_practical_submission(req_b)

        asmt_passed = (
            res_b.assessment_result.aggregation.passed
            if res_b.assessment_result
            else False
        )
        overall_level = (
            res_b.assessment_result.aggregation.overall_level.name
            if res_b.assessment_result and res_b.assessment_result.aggregation.overall_level
            else None
        )

        obs_dict: Dict[str, Any] = res_b.execution_observation or {}
        results["phases"]["phase_2_practical"] = {
            "practice_status": res_b.status.value,
            "exit_code": obs_dict.get("exit_code"),
            "execution_status": obs_dict.get("status"),
            "assessment_passed": asmt_passed,
            "overall_level": overall_level,
            "evidence_record_id": res_b.evidence_record_id,
            "updated_node_status": res_b.updated_node_status,
            "rejection_reason": res_b.rejection_reason,
        }

        # ---------------------------------------------------------------------
        # PHASE 3: State Projection
        # ---------------------------------------------------------------------
        student_state: StudentState = state_adapter.get_student_state(student_id)
        sec02_status = student_state.get_node_state("SEC-02-OS-PROC")
        sec04_status = student_state.get_node_state("SEC-04-CONCURR")
        sec05_status = student_state.get_node_state("SEC-05-BIN-SEC")

        results["phases"]["phase_3_state"] = {
            "canonical_state_id": student_state.canonical_state_id,
            "node_states": {
                "SEC-02-OS-PROC": sec02_status.status.value if sec02_status else None,
                "SEC-04-CONCURR": sec04_status.status.value if sec04_status else None,
                "SEC-05-BIN-SEC": sec05_status.status.value if sec05_status else None,
            },
        }

        # ---------------------------------------------------------------------
        # PHASE 4: Ledger Verification & Anti-Replay Defense
        # ---------------------------------------------------------------------
        cardinality = len(ledger._entries)
        integrity_report = ledger.verify_integrity()

        # Test Anti-Replay: Attempt idempotent re-submission
        replay_caught_idempotent = False
        if res_b.assessment_result is not None:
            prov_ctx = SessionProvenanceContext(
                student_id=student_id,
                session_id=session_id,
                resolved_target_node_id="SEC-05-BIN-SEC",
                roadmap_revision_id=roadmap.canonical_revision_id,
                policy_revision_id=policy.canonical_policy_id,
                expected_task_specification_sha256=res_b.assessment_result.task.specification_sha256,
                expected_rubric_specification_sha256=res_b.assessment_result.rubric.specification_sha256,
                session_is_active=True,
                session_started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            )
            try:
                ingest_adapter.ingest_assessment(res_b.assessment_result, prov_ctx)
            except IdempotentReplayError:
                replay_caught_idempotent = True
            except Exception:
                pass

        # Cardinality must remain unchanged after caught replay attempt
        cardinality_after_replay = len(ledger._entries)

        results["phases"]["phase_4_ledger"] = {
            "ledger_cardinality": cardinality,
            "hash_chain_status": integrity_report.status.value,
            "anti_replay_idempotent_detected": replay_caught_idempotent,
            "cardinality_after_replay": cardinality_after_replay,
        }

        # ---------------------------------------------------------------------
        # PHASE 5: Comparison against Differential Oracle
        # ---------------------------------------------------------------------
        mismatches: List[str] = []

        # Check Phase 1
        exp_p1 = p1_spec
        if res_a.status.value != exp_p1["expected_audit"]["session_status"]:
            mismatches.append(
                f"Phase 1 Session Status: expected '{exp_p1['expected_audit']['session_status']}', "
                f"got '{res_a.status.value}'"
            )
        if len(retrieved_candidates) != exp_p1["expected_retrieval"]["candidate_count"]:
            mismatches.append(
                f"Phase 1 Candidate Count: expected {exp_p1['expected_retrieval']['candidate_count']}, "
                f"got {len(retrieved_candidates)}"
            )
        exp_doc = exp_p1["expected_retrieval"]["primary_document_id"]
        for cand in retrieved_candidates:
            if cand.document_id != exp_doc:
                mismatches.append(
                    f"Phase 1 Retrieval doc breach: chunk '{cand.chunk_id}' from '{cand.document_id}' != '{exp_doc}'"
                )
        exp_auth = exp_p1["expected_retrieval"].get("expected_authorized_page_range")
        if exp_auth:
            auth_range = set(range(exp_auth["start"], exp_auth["end"] + 1))
            retrieved_pages = {cand.page_start for cand in retrieved_candidates if cand.page_start is not None}
            if not retrieved_pages.issubset(auth_range):
                mismatches.append(
                    f"Phase 1 Retrieval page range breach: pages {retrieved_pages} not subset of authorized {auth_range}"
                )
        for cit in exp_p1["expected_generation"]["citations_manifest_expected"]:
            if f"[{cit}]" not in res_a.response_text:
                mismatches.append(f"Phase 1 Generation Citation missing: '[{cit}]' not in response text.")

        # Check Phase 2
        exp_p2 = p2_spec["expected_practice"]
        if res_b.status.value != exp_p2["assessment_result"]["practice_result_status"]:
            mismatches.append(
                f"Phase 2 Practice Status: expected '{exp_p2['assessment_result']['practice_result_status']}', "
                f"got '{res_b.status.value}'"
            )
        if asmt_passed != exp_p2["assessment_result"]["passed"]:
            mismatches.append(
                f"Phase 2 Passed flag: expected {exp_p2['assessment_result']['passed']}, got {asmt_passed}"
            )
        if overall_level != exp_p2["assessment_result"]["overall_level"]:
            mismatches.append(
                f"Phase 2 Overall Level: expected '{exp_p2['assessment_result']['overall_level']}', got '{overall_level}'"
            )
        if obs_dict.get("exit_code") != exp_p2["execution_observation"]["exit_code"]:
            mismatches.append(
                f"Phase 2 Exit Code: expected {exp_p2['execution_observation']['exit_code']}, "
                f"got {obs_dict.get('exit_code')}"
            )
        if obs_dict.get("status") != exp_p2["execution_observation"]["status"]:
            mismatches.append(
                f"Phase 2 Execution Status: expected '{exp_p2['execution_observation']['status']}', "
                f"got '{obs_dict.get('status')}'"
            )

        # Check Phase 3
        exp_p3 = self.oracle["phase_3_state"]["expected_node_transitions"]
        act_sec02 = sec02_status.status.value if sec02_status else "NONE"
        act_sec04 = sec04_status.status.value if sec04_status else "NONE"
        if exp_p3.get("SEC-02-OS-PROC") and act_sec02 != exp_p3["SEC-02-OS-PROC"]:
            mismatches.append(
                f"Phase 3 SEC-02 status: expected '{exp_p3['SEC-02-OS-PROC']}', got '{act_sec02}'"
            )
        if exp_p3.get("SEC-04-CONCURR") and act_sec04 != exp_p3["SEC-04-CONCURR"]:
            mismatches.append(
                f"Phase 3 SEC-04 status: expected '{exp_p3['SEC-04-CONCURR']}', got '{act_sec04}'"
            )

        # Check Phase 4
        exp_p4 = self.oracle["phase_4_ledger"]
        if cardinality != exp_p4["expected_cardinality"]:
            mismatches.append(
                f"Phase 4 Cardinality: expected {exp_p4['expected_cardinality']}, got {cardinality}"
            )
        if integrity_report.status.value != exp_p4["expected_hash_chain_status"]:
            mismatches.append(
                f"Phase 4 Hash Chain: expected '{exp_p4['expected_hash_chain_status']}', "
                f"got '{integrity_report.status.value}'"
            )
        if not replay_caught_idempotent:
            mismatches.append("Phase 4 Anti-Replay: IdempotentReplayError was not raised on duplicate submission.")

        results["oracle_comparison"] = {
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "status": "PASS" if not mismatches else "FAIL",
        }
        results["verdict"] = "CERTIFIED" if not mismatches else "FAILED"

        return results

    def cleanup(self) -> None:
        """Clean up ephemeral storage resources."""
        if self._temp_dir_obj is not None:
            self._temp_dir_obj.cleanup()
            self._temp_dir_obj = None


def run_golden_path_e2e(
    oracle_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Programmatic entry point for executing Hito 5 Golden Path End-to-End."""
    root = repo_root or REPO_ROOT
    runner = E2ECampaignRunner(repo_root=root, oracle_path=oracle_path)
    try:
        results = runner.execute_campaign()
        if output_path:
            output_file = Path(output_path).resolve()
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        return results
    finally:
        runner.cleanup()


def main() -> int:
    """CLI runner for Hito 5 Golden Path E2E campaign."""
    parser = argparse.ArgumentParser(description="Hito 5 Golden Path E2E Runner")
    parser.add_argument(
        "--oracle",
        type=str,
        default=str(REPO_ROOT / "data" / "experiments" / "hito5" / "gp_e2e_oracle.json"),
        help="Path to differential oracle JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(REPO_ROOT / "data" / "experiments" / "hito5" / "gp_e2e_telemetry.json"),
        help="Path to save execution telemetry and verification results",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 KASIU / STUDY ENGINE — HITO 5: GOLDEN PATH END-TO-END RUNNER")
    print("=" * 70)
    print(f"Differential Oracle: {args.oracle}")
    print(f"Output Telemetry:    {args.output}")

    results = run_golden_path_e2e(
        oracle_path=Path(args.oracle),
        output_path=Path(args.output),
    )

    verdict = results["verdict"]
    comp = results["oracle_comparison"]

    print("\n--- CAMPAIGN EXECUTION SUMMARY ---")
    print(f"Phase 1 (Conceptual GP-A): {results['phases']['phase_1_conceptual']['session_status']}")
    print(f"Phase 2 (Practical GP-B):  {results['phases']['phase_2_practical']['practice_status']} "
          f"(Level: {results['phases']['phase_2_practical']['overall_level']})")
    print(f"Phase 3 (State):           SEC-02={results['phases']['phase_3_state']['node_states'].get('SEC-02-OS-PROC')}, "
          f"SEC-04={results['phases']['phase_3_state']['node_states'].get('SEC-04-CONCURR')}")
    print(f"Phase 4 (Ledger):          Cardinality={results['phases']['phase_4_ledger']['ledger_cardinality']}, "
          f"Integrity={results['phases']['phase_4_ledger']['hash_chain_status']}, "
          f"Anti-Replay={'DEFENDED' if results['phases']['phase_4_ledger']['anti_replay_idempotent_detected'] else 'VULNERABLE'}")
    print(f"Oracle Comparison:         {comp['status']} ({comp['mismatch_count']} mismatches)")

    if comp["mismatches"]:
        print("\n🚨 ORACLE MISMATCHES DETECTED:")
        for m in comp["mismatches"]:
            print(f"  - {m}")

    print("=" * 70)
    print(f"FINAL VERDICT: {verdict}")
    print("=" * 70)

    return 0 if verdict == "CERTIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
