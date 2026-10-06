#!/usr/bin/env python3
"""Hito 7 Campaign Runner: Real Study Loop (Learning Loop V1).

Coordinates and verifies the complete 10-stage Study Loop:
- Turn 1: Conceptual Grounding (Epistemic Retrieval -> Context -> Generation -> S4.4 Audit)
- Turn 2: Comprehension Probing (Conversational gate with calibrated NLI threshold >= 0.6)
- Turn 3: Practice Presentation & Dispatch (CurriculumRegistry task resolution)
- Turn 4: Instrumental Execution & Deterministic Evaluation (S6 Sandbox -> S9.1 Assessment -> S5.2.A Ingestion)
- Turn 5: Pure State Derivation, Advancement, and Templated Feedback (S7 Policy + S5.2.C State)
- Anti-Replay Defense Verification (D(K, R) -> IdempotentReplayError -> Delta Ledger = 0)
- Differential Oracle Verification against study_loop_oracle.json
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
from study_engine.contracts.tutor import PedagogicalAction, ResponseBudgetPolicy
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
from study_engine.session.study_loop import StudyLoopController
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import IdempotentReplayError, LedgerIntegrityStatus
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
from study_engine.tutor.policy import DeterministicTutorPolicy, TutorPolicyConfig


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


class StudyLoopExperimentRunner:
    """Authoritative experiment orchestrator for Hito 7 Real Study Loop V1."""

    def __init__(
        self,
        repo_root: Path,
        oracle_path: Optional[Path] = None,
        working_dir: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path or (
            repo_root / "data" / "experiments" / "study_loop_v1" / "study_loop_oracle.json"
        )
        self.working_dir = working_dir
        self._temp_dir_obj: Optional[tempfile.TemporaryDirectory[str]] = None

        if not self.oracle_path.exists():
            raise FileNotFoundError(f"Differential oracle not found at: '{self.oracle_path}'")

        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle: Dict[str, Any] = json.load(f)

    def initialize_pipeline(self) -> Tuple[StudyLoopController, Dict[str, Any]]:
        """Set up all components, stores, indices, curriculum, ledger, and controller."""
        if self.working_dir is None:
            self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="study_loop_v1_")
            work_path = Path(self._temp_dir_obj.name)
        else:
            work_path = self.working_dir
            work_path.mkdir(parents=True, exist_ok=True)

        db_path = work_path / "knowledge_store.db"
        vec_path = work_path / "vector_store.db"

        # 1. Ingest benchmark PDFs into KnowledgeStore (idempotent: skip if already ingested)
        store = KnowledgeStore(db_path=db_path)
        store.initialize()
        if not store.sources.list_all():
            sources_dir = self.repo_root / "data" / "benchmark" / "sources"
            ingest_benchmark_corpus(
                store=store,
                sources_dir=sources_dir,
                notebook_id="NB-SEC-01-C-PTR",
            )


        # 2. Vector indexing for dense retrieval
        vstore = SQLiteVectorStore(db_path=vec_path, read_only=False)
        embedder = DeterministicHashEmbedder(dimensions=128)
        pointer_chunks = store.chunks.list_by_document("prog_punteros.pdf")
        records: List[VectorRecord] = []
        for c in pointer_chunks:
            vec = embedder.embed_passages([c.content])[0]
            records.append(
                VectorRecord(
                    chunk_id=c.id,
                    source_id=c.source_id,
                    notebook_id="NB-SEC-01-C-PTR",
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
        retrieval_service = RetrievalService(store, hybrid, dense_threshold=0.20)

        # 4. Curriculum Registry, Roadmap, Tasks, Rubrics
        curriculum_dir = self.repo_root / "data" / "curriculum"
        registry = CurriculumRegistry(root_dir=curriculum_dir)
        roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
        task = registry.load_task("task_sec05_file_hasher.json")
        rubric = registry.load_rubric("rubric_sec05_deterministic.json")

        # 5. Policy & Ledger
        policy = build_cybersecurity_policy()
        ledger = EvidenceLedger()

        student_id = self.oracle["student_id"]
        session_id = f"sess-{student_id}"

        # 6. Session Adapters & Tutor Policy
        retrieval_adapter = CurriculumRetrievalAdapter(retrieval_service, registry)
        replay_file = self.repo_root / "data" / "experiments" / "study_loop_v1" / "study_loop_replay.json"
        mock_backend = ReplayMockBackend(replay_file=replay_file)
        llm_client = LLMClient(backend=mock_backend)
        tutor = StructuredTutor(generator=llm_client)
        tutor_adapter = StructuredTutorAdapter(tutor)
        audit_adapter = ForensicAuditAdapter(ForensicAuditor())

        canonical_stdin = "STUDY_ENGINE_CANONICAL_INPUT"
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
            session_started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        )
        orch.start_session()

        tutor_policy = DeterministicTutorPolicy(
            config=TutorPolicyConfig(
                max_conceptual_turns=5,
                understanding_threshold=0.6,
                node_to_task_mapping={"SEC-05-BIN-SEC": "task_sec05_file_hasher.json"},
            )
        )

        controller = StudyLoopController(
            orchestrator=orch,
            tutor_policy=tutor_policy,
            curriculum_registry=registry,
            active_node_id="SEC-01-C-PTR",
        )

        context = {
            "store": store,
            "vstore": vstore,
            "registry": registry,
            "roadmap": roadmap,
            "task": task,
            "rubric": rubric,
            "policy": policy,
            "ledger": ledger,
            "retrieval_service": retrieval_service,
            "state_adapter": state_adapter,
            "ingest_adapter": ingest_adapter,
            "student_id": student_id,
            "session_id": session_id,
            "work_path": work_path,
        }
        return controller, context

    def execute_campaign(self) -> Dict[str, Any]:
        """Execute the canonical 5-turn study loop and compare against study_loop_oracle.json."""
        controller, ctx = self.initialize_pipeline()
        ledger: EvidenceLedger = ctx["ledger"]
        state_adapter: CurriculumStateAdapter = ctx["state_adapter"]
        retrieval_service: RetrievalService = ctx["retrieval_service"]
        registry: CurriculumRegistry = ctx["registry"]
        work_path: Path = ctx["work_path"]

        results: Dict[str, Any] = {
            "campaign_id": "HITO-7-STUDY-LOOP-V1",
            "oracle_id": self.oracle["oracle_id"],
            "spec_version": self.oracle["spec_version"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "turns": {},
            "oracle_comparison": {},
            "verdict": "PENDING",
        }

        # ---------------------------------------------------------------------
        # TURN 1: Conceptual Grounding (SEC-01-C-PTR)
        # ---------------------------------------------------------------------
        t1_spec = self.oracle["turns"][0]
        t1_in = t1_spec["input"]
        controller.set_active_node(t1_in["node_id"])

        # Decide action
        t1_decision = controller.decide_next_action(t1_in["student_query"])

        # Retrieval check
        retrieved_candidates = retrieval_service.retrieve_evidence(
            query=t1_in["student_query"],
            node_id=t1_in["node_id"],
            registry=registry,
            top_k=5,
        )

        # Conceptual turn execution
        t1_res: SessionResult = controller.handle_conceptual_turn(
            query=t1_in["student_query"],
            target_node_id=t1_in["node_id"],
        )

        results["turns"]["turn_1"] = {
            "turn_id": t1_spec["turn_id"],
            "action": t1_decision.action.value,
            "budget": t1_decision.budget.value,
            "target_node_id": t1_decision.target_node_id,
            "pedagogical_intent": t1_decision.pedagogical_intent,
            "allow_code_snippets": t1_decision.allow_code_snippets,
            "session_status": t1_res.status.value,
            "retrieved_doc_ids": list({c.document_id for c in retrieved_candidates}),
            "retrieved_pages": sorted(list({c.page_start for c in retrieved_candidates if c.page_start is not None})),
            "audit_report_id": t1_res.audit_report_id,
            "response_text": t1_res.response_text,
        }

        # ---------------------------------------------------------------------
        # TURN 2: Check Understanding (SEC-01-C-PTR)
        # ---------------------------------------------------------------------
        t2_spec = self.oracle["turns"][1]
        t2_in = t2_spec["input"]

        t2_decision = controller.decide_next_action(t2_in["student_message"])
        t2_eval = controller.check_understanding(
            student_message=t2_in["student_message"],
            target_node_id=t2_in["node_id"],
            calibrated_nli_score=0.90,
        )

        results["turns"]["turn_2"] = {
            "turn_id": t2_spec["turn_id"],
            "action": t2_decision.action.value,
            "budget": t2_decision.budget.value,
            "target_node_id": t2_decision.target_node_id,
            "pedagogical_intent": t2_decision.pedagogical_intent,
            "conceptually_sound": t2_eval["conceptually_sound"],
            "ready_for_practice": t2_eval["ready_for_practice"],
            "ledger_delta": t2_eval["ledger_delta"],
        }

        # ---------------------------------------------------------------------
        # PREREQUISITE ADVANCEMENT (Student has completed SEC-01..SEC-04)
        # ---------------------------------------------------------------------
        base_t = datetime.now(timezone.utc) - timedelta(minutes=15)
        student_id = controller.orchestrator.student_id
        for i, (nid, etype) in enumerate([
            ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
            ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
            ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
            ("SEC-04-CONCURR", EvidenceType.CODE_EXECUTION),
        ]):
            r = EvidenceRecord(
                record_id=f"ev-prereq-{nid.lower().replace('-', '_')}",
                student_id=student_id,
                node_id=nid,
                evidence_type=etype,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=base_t + timedelta(minutes=i),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="evaluator-prereq",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                assessment_digest=hashlib.sha256(f"prereq-{nid}".encode()).hexdigest(),
            )
            ledger.append_record(r)

        # ---------------------------------------------------------------------
        # TURN 3: Practice Dispatch (SEC-05-BIN-SEC)
        # ---------------------------------------------------------------------
        t3_spec = self.oracle["turns"][2]
        t3_in = t3_spec["input"]
        controller.set_active_node(t3_in["node_id"])
        controller.conceptual_turns_completed = 2  # student has 2 completed conceptual turns

        t3_decision = controller.decide_next_action(t3_in["student_message"])
        t3_dispatch = controller.dispatch_practice(target_node_id=t3_in["node_id"])

        results["turns"]["turn_3"] = {
            "turn_id": t3_spec["turn_id"],
            "action": t3_decision.action.value,
            "budget": t3_decision.budget.value,
            "target_node_id": t3_decision.target_node_id,
            "suggested_task_id": t3_decision.suggested_task_id,
            "pedagogical_intent": t3_decision.pedagogical_intent,
            "dispatched_task_id": t3_dispatch["task_id"],
        }

        # ---------------------------------------------------------------------
        # TURN 4: Instrumental Execution & Evaluation (SEC-05-BIN-SEC)
        # ---------------------------------------------------------------------
        t4_spec = self.oracle["turns"][3]
        t4_in = t4_spec["input"]
        artifact_code = t4_in["artifact_code"]
        script_file = work_path / "hasher_submission.py"
        script_file.write_text(artifact_code, encoding="utf-8")

        cardinality_before_practice = len(ledger._entries)

        p_req = PracticeRequest(
            student_id=controller.orchestrator.student_id,
            node_id=t4_in["node_id"],
            task_id=t4_in["task_id"],
            rubric_id=t4_in["rubric_id"],
            artifact_path=str(script_file),
        )
        t4_res: PracticeResult = controller.submit_practice(p_req)

        cardinality_after_practice = len(ledger._entries)
        ledger_delta = cardinality_after_practice - cardinality_before_practice

        obs_dict: Dict[str, Any] = t4_res.execution_observation or {}
        asmt_passed = bool(
            t4_res.assessment_result.aggregation.passed
            if t4_res.assessment_result
            else False
        )
        overall_lvl = (
            t4_res.assessment_result.aggregation.overall_level.name
            if t4_res.assessment_result and t4_res.assessment_result.aggregation.overall_level
            else None
        )

        results["turns"]["turn_4"] = {
            "turn_id": t4_spec["turn_id"],
            "status": t4_res.status.value,
            "exit_code": obs_dict.get("exit_code"),
            "execution_status": obs_dict.get("status"),
            "assessment_passed": asmt_passed,
            "score": 1.0 if asmt_passed else 0.0,
            "overall_level": overall_lvl,
            "evidence_record_id": t4_res.evidence_record_id,
            "ledger_delta": ledger_delta,
            "rejection_reason": t4_res.rejection_reason,
        }

        # ---------------------------------------------------------------------
        # TURN 5: State Derivation, Unlock, and Feedback
        # ---------------------------------------------------------------------
        t5_spec = self.oracle["turns"][4]
        student_state: StudentState = controller.derive_state()
        sec05_ns = student_state.get_node_state("SEC-05-BIN-SEC")
        sec06_ns = student_state.get_node_state("SEC-06-CAPSTONE")

        t5_decision = controller.decide_next_action()
        feedback_text = controller.render_feedback(t4_res)
        # Anti-replay check: Attempt to re-ingest the exact same assessment result (K, R)
        replay_caught = False
        if t4_res.assessment_result is not None:
            prov = SessionProvenanceContext(
                student_id=controller.orchestrator.student_id,
                session_id=controller.orchestrator.session_id,
                resolved_target_node_id="SEC-05-BIN-SEC",
                roadmap_revision_id=controller.orchestrator.roadmap.canonical_revision_id,
                policy_revision_id=controller.orchestrator.policy.canonical_policy_id,
                expected_task_specification_sha256=t4_res.assessment_result.task.specification_sha256,
                expected_rubric_specification_sha256=t4_res.assessment_result.rubric.specification_sha256,
                session_is_active=True,
                session_started_at=controller.orchestrator.session_started_at,
            )
            if controller.orchestrator.ingestion_port is not None:
                try:
                    controller.orchestrator.ingestion_port.ingest_assessment(t4_res.assessment_result, prov)
                except IdempotentReplayError:
                    replay_caught = True
                except Exception:
                    pass

        cardinality_final = len(ledger._entries)
        integrity = ledger.verify_integrity()

        results["turns"]["turn_5"] = {
            "turn_id": t5_spec["turn_id"],
            "sec05_status": sec05_ns.status.value if sec05_ns else None,
            "sec06_status": sec06_ns.status.value if sec06_ns else None,
            "sec06_unlocked": (sec06_ns.status.value == "AVAILABLE") if sec06_ns else False,
            "action": t5_decision.action.value,
            "budget": t5_decision.budget.value,
            "target_node_id": t5_decision.target_node_id,
            "pedagogical_intent": t5_decision.pedagogical_intent,
            "feedback_rendered": bool(feedback_text),
            "ledger_cardinality": cardinality_final,
            "hash_chain_status": integrity.status.value,
            "anti_replay_idempotent_detected": replay_caught,
        }

        # ---------------------------------------------------------------------
        # Differential Oracle Comparison
        # ---------------------------------------------------------------------
        mismatches: List[str] = []

        # Compare Turn 1
        exp_t1 = t1_spec
        if results["turns"]["turn_1"]["action"] != exp_t1["expected_tutor_decision"]["action"]:
            mismatches.append(f"Turn 1 Action: expected {exp_t1['expected_tutor_decision']['action']}, got {results['turns']['turn_1']['action']}")
        if results["turns"]["turn_1"]["session_status"] != exp_t1["expected_audit"]["status"]:
            mismatches.append(f"Turn 1 Status: expected {exp_t1['expected_audit']['status']}, got {results['turns']['turn_1']['session_status']}")
        for doc in exp_t1["expected_retrieval"]["authorized_document_ids"]:
            if doc not in results["turns"]["turn_1"]["retrieved_doc_ids"]:
                mismatches.append(f"Turn 1 Doc: '{doc}' missing from retrieved doc IDs")
        exp_pr = exp_t1["expected_retrieval"]["authorized_page_range"]
        auth_pages = set(range(exp_pr["start"], exp_pr["end"] + 1))
        ret_pages = set(results["turns"]["turn_1"]["retrieved_pages"])
        if not ret_pages.issubset(auth_pages):
            mismatches.append(f"Turn 1 Pages: {ret_pages} not subset of {auth_pages}")

        # Compare Turn 2
        exp_t2 = t2_spec
        if results["turns"]["turn_2"]["action"] != exp_t2["expected_tutor_decision"]["action"]:
            mismatches.append(f"Turn 2 Action: expected {exp_t2['expected_tutor_decision']['action']}, got {results['turns']['turn_2']['action']}")
        if results["turns"]["turn_2"]["conceptually_sound"] != exp_t2["expected_evaluation"]["conceptually_sound"]:
            mismatches.append(f"Turn 2 Concept Sound: expected {exp_t2['expected_evaluation']['conceptually_sound']}, got {results['turns']['turn_2']['conceptually_sound']}")
        if results["turns"]["turn_2"]["ready_for_practice"] != exp_t2["expected_evaluation"]["ready_for_practice"]:
            mismatches.append(f"Turn 2 Ready Practice: expected {exp_t2['expected_evaluation']['ready_for_practice']}, got {results['turns']['turn_2']['ready_for_practice']}")

        # Compare Turn 3
        exp_t3 = t3_spec
        if results["turns"]["turn_3"]["action"] != exp_t3["expected_tutor_decision"]["action"]:
            mismatches.append(f"Turn 3 Action: expected {exp_t3['expected_tutor_decision']['action']}, got {results['turns']['turn_3']['action']}")
        if results["turns"]["turn_3"]["suggested_task_id"] != exp_t3["expected_tutor_decision"]["suggested_task_id"]:
            mismatches.append(f"Turn 3 Task ID: expected {exp_t3['expected_tutor_decision']['suggested_task_id']}, got {results['turns']['turn_3']['suggested_task_id']}")

        # Compare Turn 4
        exp_t4 = t4_spec
        if results["turns"]["turn_4"]["status"] != exp_t4["expected_assessment"]["status"]:
            mismatches.append(f"Turn 4 Status: expected {exp_t4['expected_assessment']['status']}, got {results['turns']['turn_4']['status']}")
        if results["turns"]["turn_4"]["exit_code"] != exp_t4["expected_execution"]["exit_code"]:
            mismatches.append(f"Turn 4 Exit Code: expected {exp_t4['expected_execution']['exit_code']}, got {results['turns']['turn_4']['exit_code']}")
        if results["turns"]["turn_4"]["overall_level"] != exp_t4["expected_assessment"]["overall_level"]:
            mismatches.append(f"Turn 4 Overall Level: expected {exp_t4['expected_assessment']['overall_level']}, got {results['turns']['turn_4']['overall_level']}")
        if results["turns"]["turn_4"]["ledger_delta"] != exp_t4["expected_ingestion"]["ledger_delta"]:
            mismatches.append(f"Turn 4 Ledger Delta: expected {exp_t4['expected_ingestion']['ledger_delta']}, got {results['turns']['turn_4']['ledger_delta']}")

        # Compare Turn 5
        exp_t5 = t5_spec
        if results["turns"]["turn_5"]["sec05_status"] != exp_t5["expected_state_projection"]["sec05_status"]:
            mismatches.append(f"Turn 5 SEC-05: expected {exp_t5['expected_state_projection']['sec05_status']}, got {results['turns']['turn_5']['sec05_status']}")
        if results["turns"]["turn_5"]["sec06_status"] != exp_t5["expected_state_projection"]["sec06_status"]:
            mismatches.append(f"Turn 5 SEC-06: expected {exp_t5['expected_state_projection']['sec06_status']}, got {results['turns']['turn_5']['sec06_status']}")
        if results["turns"]["turn_5"]["sec06_unlocked"] != exp_t5["expected_state_projection"]["sec06_unlocked"]:
            mismatches.append(f"Turn 5 SEC-06 Unlocked: expected {exp_t5['expected_state_projection']['sec06_unlocked']}, got {results['turns']['turn_5']['sec06_unlocked']}")
        if results["turns"]["turn_5"]["action"] != exp_t5["expected_tutor_decision"]["action"]:
            mismatches.append(f"Turn 5 Action: expected {exp_t5['expected_tutor_decision']['action']}, got {results['turns']['turn_5']['action']}")
        if results["turns"]["turn_5"]["ledger_cardinality"] != exp_t5["expected_persistence_guarantees"]["ledger_cardinality"]:
            mismatches.append(f"Turn 5 Cardinality: expected {exp_t5['expected_persistence_guarantees']['ledger_cardinality']}, got {results['turns']['turn_5']['ledger_cardinality']}")
        if results["turns"]["turn_5"]["hash_chain_status"] != exp_t5["expected_persistence_guarantees"]["hash_chain_status"]:
            mismatches.append(f"Turn 5 Hash Chain: expected {exp_t5['expected_persistence_guarantees']['hash_chain_status']}, got {results['turns']['turn_5']['hash_chain_status']}")
        if not results["turns"]["turn_5"]["anti_replay_idempotent_detected"]:
            mismatches.append("Turn 5 Anti-Replay: IdempotentReplayError was not detected on duplicate submission")

        verdict = "CERTIFIED" if not mismatches else "FAILED"
        results["verdict"] = verdict
        results["oracle_comparison"] = {
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "status": "PASS" if not mismatches else "FAIL",
        }
        return results


def run_study_loop_v1(
    repo_root: Optional[Path] = None,
    oracle_path: Optional[Path] = None,
    working_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run authoritative Study Loop V1 campaign and return telemetry dictionary."""
    root = repo_root or REPO_ROOT
    runner = StudyLoopExperimentRunner(repo_root=root, oracle_path=oracle_path, working_dir=working_dir)
    return runner.execute_campaign()


def main() -> int:
    parser = argparse.ArgumentParser(description="Hito 7: Real Study Loop V1 Campaign Runner")
    parser.add_argument("--oracle", type=str, default=None, help="Path to differential oracle JSON")
    parser.add_argument("--output", type=str, default=None, help="Path to output telemetry JSON")
    parser.add_argument("--working-dir", type=str, default=None, help="Working directory for databases")
    args = parser.parse_args()

    oracle_p = Path(args.oracle).resolve() if args.oracle else None
    working_d = Path(args.working_dir).resolve() if args.working_dir else None

    results = run_study_loop_v1(oracle_path=oracle_p, working_dir=working_d)

    output_path = (
        Path(args.output).resolve()
        if args.output
        else REPO_ROOT / "data" / "experiments" / "study_loop_v1" / "study_loop_telemetry.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Study Loop V1 Campaign completed with verdict: {results['verdict']}")
    print(f"Telemetry saved to: {output_path}")
    if results["oracle_comparison"]["mismatches"]:
        print(f"Mismatches ({results['oracle_comparison']['mismatch_count']}):")
        for m in results["oracle_comparison"]["mismatches"]:
            print(f"  - {m}")
        return 1

    print("All 5 canonical turns MATCHED differential oracle with ZERO mismatches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
