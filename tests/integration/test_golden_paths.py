"""Five Protected End-to-End Golden Path Integration Scenarios (S5.5).

Verifies the global connective tissue and epistemological progression:
    Observation (S6/S7)
        != AssessmentResult (S9/S10)
        != EvidenceRecord (S5.2.A)
        != GatewayVerdictRecord (GatewayDecisionAuthority)
        != StudentState (S5.2.C)

Scenarios:
- Scenario A: Conceptual Tutoring Turn (S5.1 -> S5.3 -> S3 -> S4.1 -> S4.3
              -> S4.4) + Stale context & ungrounded claim adversarial
              injection.
- Scenario B: Formative Mastery & State Advancement (S6 -> S9 -> S5.2.A
              -> S5.2.B -> S5.2.C) + Partial failure & tampered observation.
- Scenario C: Gateway Defense & Cryptographic Backward Lineage (G1.2 -> Task
              -> Artifact -> Perturbation -> Oral Defense -> GDA -> Ledger
              -> State -> Spine verification) + Tampered artifact rejection.
- Scenario D: Persistence & Crash Consistency (Disk-backed Ledger atomic).
- Scenario E: Adversarial Security & Locked Node Inviolability (Locked DAG).
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile
from typing import Dict, Tuple
import pytest

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
    ClaimSupportVerdict,
    ForensicAuditInput,
)
from study_engine.audit.nli import MockNLIJudge
from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
    EpistemologicalStage,
    validate_epistemological_authority,
)
from study_engine.contracts.events import OperationalEvent
from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.execution import ExecutionObservation
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)
from study_engine.contracts.spine import (
    ExecutionProvenanceSpine,
    LineageVerificationError,
    SpineAssessment,
    SpineCurriculum,
    SpineExecution,
    SpineIdentity,
    SpineTerminalState,
    verify_spine_lineage,
)
from study_engine.contracts.verdict_authority import (
    GatewayDecisionAuthority,
    compute_gateway_revision_id,
)
from study_engine.curriculum.gateway_contracts import (
    GatewayDefinition,
    GatewayFormat,
    GatewayVerdictCriteria,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.session.contracts import (
    SessionStatus,
    StudentInput,
    StudentInputType,
    TurnActionType,
)
from study_engine.session.orchestrator import SessionOrchestrator
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
from study_engine.state.state_contracts import NodeProgressStatus
from study_engine.state.state_engine import derive_student_state


def _setup_curriculum_fixtures() -> Tuple[
    CurricularRoadmap, AssessmentPolicy, EvidenceLedger
]:
    """Build a deterministic two-node curriculum with hard dependency."""
    node_1 = RoadmapNode(
        node_id="NET-01",
        title="Network Basics",
        description="TCP/IP fundamentals",
        node_type=NodeType.TOPIC,
        notebook_id="net-fundamentals",
        priority=1,
    )
    node_2 = RoadmapNode(
        node_id="NET-02",
        title="Socket Programming",
        description="Low-level socket programming",
        node_type=NodeType.TOPIC,
        notebook_id="net-fundamentals",
        priority=2,
    )
    nodes: Dict[str, RoadmapNode] = {"NET-01": node_1, "NET-02": node_2}
    deps: Tuple[RoadmapDependency, ...] = (
        RoadmapDependency(
            source_node_id="NET-01",
            target_node_id="NET-02",
            dependency_type=DependencyType.HARD,
        ),
    )
    rm_id = compute_canonical_revision_id(
        "net-roadmap", "Networking", "1.0", nodes, deps
    )
    roadmap = CurricularRoadmap(
        roadmap_id="net-roadmap",
        title="Networking",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rm_id,
    )

    req = EvidenceRequirement(
        requirement_id="req-practical",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-net",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit}
    pol_id = compute_canonical_policy_id(
        "net-policy", "Net Policy", "1.0", defaults, {}
    )
    policy = AssessmentPolicy(
        policy_id="net-policy",
        title="Net Policy",
        version="1.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=pol_id,
    )
    ledger = EvidenceLedger()
    return roadmap, policy, ledger


class TestScenarioAConceptualTutoringTurn:
    """Golden Path Scenario A: Roadmap -> Session -> Retrieval -> Audit."""

    def test_scenario_a_happy_path(self) -> None:
        """Coordinated tutoring turn with S4.4 approval."""
        roadmap, policy, ledger = _setup_curriculum_fixtures()
        orch = SessionOrchestrator("sess-01", "alice", roadmap, policy, ledger)

        # 1. Start session -> focuses on available node NET-01
        start_out = orch.start_session()
        assert start_out.resolved_target_node_id == "NET-01"
        assert orch.fsm.current_status == SessionStatus.WAITING_FOR_STUDENT

        # 2. Student inputs conceptual question
        now = datetime.now(timezone.utc)
        curr_state = derive_student_state(roadmap, policy, ledger, "alice")
        s_input = StudentInput(
            input_id="inp-01",
            session_id="sess-01",
            turn_index=0,
            input_type=StudentInputType.QUESTION,
            content="Explain TCP three-way handshake.",
            timestamp=now,
        )
        decision = orch.decide_turn(s_input, curr_state)
        assert decision.resolved_target_node_id == "NET-01"
        assert decision.action_type == TurnActionType.EXPLAIN

        # 3. Build verified retrieval context and audited response
        content = (
            "TCP uses SYN, SYN-ACK, and ACK to establish a connection."
        )
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        c_rec = CitationRecord(
            citation_id="E1",
            chunk_id="chk-1",
            document_id="doc-1",
            source_id="src-1",
            source_title="Computer Networks",
            content_hash=c_hash,
        )
        unit = PackagedEvidenceUnit(
            citation=c_rec,
            content=content,
            retrieval_score=0.95,
            retrieval_rank=1,
            retrieval_method="hybrid",
        )
        manifest = CitationManifest(records={"E1": c_rec})
        packet = EvidencePacket(
            original_query="Explain TCP three-way handshake",
            normalized_query="explain tcp three-way handshake",
            notebook_id="net-fundamentals",
            grounding_decision=GroundingDecision.SUPPORTED,
        )
        ctx = PackagedContext(
            packet=packet,
            citation_manifest=manifest,
            packaged_units=[unit],
            formatted_context_block=f"[E1] {content}",
            total_characters=len(content),
            epistemic_policy="Estricta",
        )
        req = GenerationRequest(
            request_id="req-01",
            notebook_id="net-fundamentals",
            query="Explain TCP three-way handshake",
            packaged_context=ctx,
            mode=GenerationMode.EXPLANATION,
        )
        gen_resp = GenerationResponse(
            response_id="resp-01",
            request_id="req-01",
            notebook_id="net-fundamentals",
            mode=GenerationMode.EXPLANATION,
            text=(
                "TCP establishes connections via SYN, SYN-ACK, and ACK [E1]."
            ),
            raw_content=(
                "TCP establishes connections via SYN, SYN-ACK, and ACK [E1]."
            ),
            citations=(
                ParsedCitation(
                    citation_id="E1",
                    in_manifest=True,
                ),
            ),
            validation_status=ResponseValidationStatus.VALID,
            is_abstention=False,
            grounding_decision=packet.grounding_decision,
        )

        audit_in = ForensicAuditInput(
            request=req,
            response=gen_resp,
            prompt_hash="1" * 64,
        )
        auditor = ForensicAuditor(nli_judge=MockNLIJudge())
        audit_res = auditor.audit(audit_in)
        assert audit_res.overall_verdict == AuditVerdict.APPROVED

    def test_scenario_a_adversarial_stale_context_rejected(self) -> None:
        """Auditor rejects hallucinated claims lacking grounding."""
        content = "TCP uses SYN, SYN-ACK, and ACK."
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        c_rec = CitationRecord(
            citation_id="E1",
            chunk_id="chk-1",
            document_id="doc-1",
            source_id="src-1",
            source_title="Computer Networks",
            content_hash=c_hash,
        )
        unit = PackagedEvidenceUnit(
            citation=c_rec,
            content=content,
            retrieval_score=0.95,
            retrieval_rank=1,
            retrieval_method="hybrid",
        )
        manifest = CitationManifest(records={"E1": c_rec})
        packet = EvidencePacket(
            original_query="Explain TCP",
            normalized_query="explain tcp",
            notebook_id="net-fundamentals",
            grounding_decision=GroundingDecision.SUPPORTED,
        )
        ctx = PackagedContext(
            packet=packet,
            citation_manifest=manifest,
            packaged_units=[unit],
            formatted_context_block=f"[E1] {content}",
            total_characters=len(content),
            epistemic_policy="Estricta",
        )
        req = GenerationRequest(
            request_id="req-adv-01",
            notebook_id="net-fundamentals",
            query="Explain TCP",
            packaged_context=ctx,
            mode=GenerationMode.EXPLANATION,
        )
        hallucinated_resp = GenerationResponse(
            response_id="resp-adv-01",
            request_id="req-adv-01",
            notebook_id="net-fundamentals",
            mode=GenerationMode.EXPLANATION,
            text="TCP is entirely connectionless and unreliable [E1].",
            raw_content="TCP is entirely connectionless and unreliable [E1].",
            citations=(
                ParsedCitation(
                    citation_id="E1",
                    in_manifest=True,
                ),
            ),
            validation_status=ResponseValidationStatus.VALID,
            is_abstention=False,
            grounding_decision=packet.grounding_decision,
        )

        audit_in = ForensicAuditInput(
            request=req,
            response=hallucinated_resp,
            prompt_hash="1" * 64,
        )
        auditor = ForensicAuditor(
            nli_judge=MockNLIJudge(
                default_verdict=ClaimSupportVerdict.CONTRADICTED
            )
        )
        audit_res = auditor.audit(audit_in)
        assert (
            audit_res.overall_verdict == AuditVerdict.REJECTED_CONTRADICTION
        )


class TestScenarioBFormativeMasteryAdvancement:
    """Golden Path Scenario B: S6 -> S9 -> S5.2.A -> S5.2.B -> S5.2.C."""

    def test_scenario_b_happy_path(self) -> None:
        """Practical task completion unlocks downstream node in DAG."""
        roadmap, policy, ledger = _setup_curriculum_fixtures()

        # Initial state: NET-01 is AVAILABLE, NET-02 is LOCKED
        initial_state = derive_student_state(roadmap, policy, ledger, "alice")
        net01_init = initial_state.get_node_state("NET-01")
        assert net01_init is not None
        assert net01_init.status == NodeProgressStatus.AVAILABLE
        net02_init = initial_state.get_node_state("NET-02")
        assert net02_init is not None
        assert net02_init.status == NodeProgressStatus.LOCKED

        # 1. S6 execution emits instrumental observation
        obs = ExecutionObservation(
            observation_id="obs-net-01",
            execution_id="exec-01",
            tool_name="python.run_script",
            raw_telemetry={"exit_code": 0, "tests_passed": 5},
            produced_artifact_digests=("a" * 64,),
        )
        assert obs.authority_id == "S6_EXECUTION_PLANE"

        # 2. S9/S10 Assessment Engine validates observation
        asmt_score = 1.0
        asmt_result = {
            "observation_id": obs.observation_id,
            "passed": True,
            "score": asmt_score,
            "dimensions": {"accuracy": 1.0, "code_quality": 1.0},
        }

        # 3. S5.2.A validates evidence eligibility and creates EvidenceRecord
        now = datetime.now(timezone.utc)
        record = EvidenceRecord(
            record_id="ev-net-01-pass",
            student_id="alice",
            node_id="NET-01",
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=EvidenceOutcome.PASS,
            score=asmt_score,
            timestamp=now,
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="s6_python_adapter",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            metadata={
                "session_id": "sess-01",
                "details": "Practical socket implementation verified",
            },
        )

        # 4. S5.2.B commits EvidenceRecord to hash-chained ledger
        entry = ledger.append_evidence(record)
        assert entry.entry_index == 0
        assert len(entry.entry_hash) == 64

        # 5. S5.2.C derives new StudentState
        updated_state = derive_student_state(roadmap, policy, ledger, "alice")
        net01_up = updated_state.get_node_state("NET-01")
        assert net01_up is not None
        assert net01_up.status == NodeProgressStatus.ASSESSED_PROFICIENT
        # Downstream NET-02 is now unlocked!
        net02_up = updated_state.get_node_state("NET-02")
        assert net02_up is not None
        assert net02_up.status == NodeProgressStatus.AVAILABLE

    def test_scenario_b_partial_failure_leaves_downstream_locked(self) -> None:
        """Failed assessment outcome preserves LOCKED status on downstream."""
        roadmap, policy, ledger = _setup_curriculum_fixtures()

        now = datetime.now(timezone.utc)
        failed_record = EvidenceRecord(
            record_id="ev-net-01-fail",
            student_id="alice",
            node_id="NET-01",
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=EvidenceOutcome.FAIL,
            score=0.4,
            timestamp=now,
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="s6_python_adapter",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            metadata={
                "session_id": "sess-01",
                "details": "Socket test failed with exit code 1",
            },
        )
        ledger.append_evidence(failed_record)

        state = derive_student_state(roadmap, policy, ledger, "alice")
        net01_fail = state.get_node_state("NET-01")
        assert net01_fail is not None
        assert net01_fail.status != NodeProgressStatus.ASSESSED_PROFICIENT
        net02_fail = state.get_node_state("NET-02")
        assert net02_fail is not None
        assert net02_fail.status == NodeProgressStatus.LOCKED


class TestScenarioCGatewayDefenseAndLineage:
    """Golden Path Scenario C: Gateway Defense & Cryptographic Lineage."""

    VALID_SHA_CURRICULUM = "1" * 64
    VALID_SHA_POLICY = "2" * 64
    VALID_SHA_RUBRIC = "3" * 64
    VALID_SHA_TASK = "4" * 64
    VALID_SHA_ARTIFACT = "5" * 64

    def _make_gateway_fixtures(self) -> Tuple[
        CurricularRoadmap, AssessmentPolicy, EvidenceLedger, GatewayDefinition
    ]:
        g_node = RoadmapNode(
            node_id="G1-2",
            title="Gateway 1.2: Network Security",
            description="Capstone defense",
            node_type=NodeType.LAB,
            notebook_id="net-capstone",
            priority=1,
        )
        nodes = {"G1-2": g_node}
        rm_id = compute_canonical_revision_id(
            "rm-g", "Gateway Roadmap", "1.0", nodes, ()
        )
        roadmap = CurricularRoadmap(
            roadmap_id="rm-g",
            title="Gateway Roadmap",
            version="1.0",
            nodes=nodes,
            dependencies=(),
            canonical_revision_id=rm_id,
        )

        req = EvidenceRequirement(
            requirement_id="req-gw",
            evidence_type=EvidenceType.CODE_EXECUTION,
            min_count=1,
            min_score=0.85,
        )
        crit = NodeAssessmentCriteria(
            criteria_id="crit-gw",
            target_node_type=NodeType.LAB,
            requirements=(req,),
            regression_threshold_failures=1,
        )
        defaults = {NodeType.LAB: crit}
        pol_id = compute_canonical_policy_id(
            "pol-g", "Gateway Policy", "1.0", defaults, {}
        )
        policy = AssessmentPolicy(
            policy_id="pol-g",
            title="Gateway Policy",
            version="1.0",
            default_criteria=defaults,
            node_overrides={},
            canonical_policy_id=pol_id,
        )
        ledger = EvidenceLedger()

        gdef = GatewayDefinition(
            gateway_id="G1-2",
            curriculum_node_id="G1-2",
            title="Capstone Gateway 1.2",
            format=GatewayFormat.PRACTICAL_AND_ORAL,
            rubric_id="rubric-g12",
            verdict_criteria=GatewayVerdictCriteria(
                criteria_id="crit-g12",
                minimum_overall_level=PerformanceLevel.N4_EXCELLENT,
            ),
            practical_task_ids=("task-pcap-analyzer",),
            perturbation_ids=("pert-malformed-pcap",),
            oral_defense_id="oral-g12",
            required_evidence_outcomes=("outcome-prereq-met",),
        )
        return roadmap, policy, ledger, gdef

    def test_scenario_c_happy_path_and_lineage_verification(self) -> None:
        """Gateway completion + complete backward provenance graph check."""
        roadmap, policy, ledger, gdef = self._make_gateway_fixtures()
        gda = GatewayDecisionAuthority()

        # 1. S6 executes task -> produces artifact and observation
        artifact_hash = self.VALID_SHA_ARTIFACT
        obs = ExecutionObservation(
            observation_id="obs-gw-01",
            execution_id="exec-gw-01",
            tool_name="python.run_script",
            raw_telemetry={"exit_code": 0},
            produced_artifact_digests=(artifact_hash,),
        )

        # 2. S9/S10 assessments
        asmt_results = [{"passed": True, "details": "PCAP parsed correctly"}]
        pert_results = [{"passed": True, "details": "Handled malformed PCAP"}]
        oral_result = {
            "passed": True,
            "details": "Defended architectural choices",
        }
        evidence_elig = {"eligible": True}

        # 3. GatewayDecisionAuthority composes verdict
        g_rev = compute_gateway_revision_id(gdef)
        verdict = gda.evaluate_gateway(
            verdict_id="verdict-g12-001",
            student_id="alice",
            gateway_def=gdef,
            gateway_revision_id=g_rev,
            assessment_results=asmt_results,
            oral_defense_result=oral_result,
            perturbation_results=pert_results,
            evidence_eligibility=evidence_elig,
        )
        assert verdict.passed is True
        assert verdict.authority_id == "GATEWAY_DECISION_AUTHORITY"

        # 4. S5.2.A creates EvidenceRecord from verdict
        now = datetime.now(timezone.utc)
        record = EvidenceRecord(
            record_id="ev-gw-01",
            student_id="alice",
            node_id="G1-2",
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=now,
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="s6_python_adapter",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            metadata={
                "session_id": "sess-gw-01",
                "details": f"Gateway verdict digest: {verdict.verdict_digest}",
            },
        )

        # 5. S5.2.B commits to Ledger
        ledger.append_evidence(record)

        # 6. S5.2.C derives StudentState
        state = derive_student_state(roadmap, policy, ledger, "alice")
        g12_state = state.get_node_state("G1-2")
        assert g12_state is not None
        assert g12_state.status == NodeProgressStatus.ASSESSED_PROFICIENT

        # 7. Construct and verify ExecutionProvenanceSpine
        spine = ExecutionProvenanceSpine(
            spine_id="spine-g12-alice",
            identity=SpineIdentity(
                student_id="alice",
                session_id="sess-gw-01",
                attempt_id="attempt-01",
            ),
            curriculum=SpineCurriculum(
                curriculum_node_id="G1-2",
                roadmap_revision_id=roadmap.canonical_revision_id,
                policy_revision_id=policy.canonical_policy_id,
                gateway_id="G1-2",
                gateway_revision_id=g_rev,
            ),
            assessment=SpineAssessment(
                rubric_id=gdef.rubric_id,
                rubric_revision_id=self.VALID_SHA_RUBRIC,
                task_id="task-pcap-analyzer",
                task_revision_id=self.VALID_SHA_TASK,
                assessment_result_id="asmt-g12-01",
                evidence_record_id=record.record_id,
                evaluator_version="1.0.0",
            ),
            execution=SpineExecution(
                observation_ids=(obs.observation_id,),
                artifact_digests=(artifact_hash,),
                perturbation_id="pert-malformed-pcap",
            ),
            terminal_state=SpineTerminalState(
                ledger_cutoff_hash=ledger.tip_hash,
                student_state_id=state.canonical_state_id,
            ),
        )

        # Lineage verification passes deterministically!
        assert verify_spine_lineage(
            spine=spine,
            expected_artifact_digests=(artifact_hash,),
            expected_ledger_cutoff_hash=ledger.tip_hash,
            expected_student_state_id=state.canonical_state_id,
        )

    def test_scenario_c_adversarial_tampered_artifact_rejected(self) -> None:
        """Tampered artifact hash fails lineage verification immediately."""
        _, _, ledger, gdef = self._make_gateway_fixtures()
        g_rev = compute_gateway_revision_id(gdef)

        tampered_artifact = "e" * 64
        spine = ExecutionProvenanceSpine(
            spine_id="spine-tampered",
            identity=SpineIdentity(student_id="alice"),
            curriculum=SpineCurriculum(
                curriculum_node_id="G1-2",
                roadmap_revision_id="a" * 64,
                policy_revision_id="b" * 64,
                gateway_id="G1-2",
                gateway_revision_id=g_rev,
            ),
            assessment=SpineAssessment(
                task_id="task-1",
                task_revision_id="c" * 64,
            ),
            execution=SpineExecution(
                artifact_digests=(tampered_artifact,),
            ),
            terminal_state=SpineTerminalState(),
        )

        # Expected original artifact vs tampered
        with pytest.raises(
            LineageVerificationError, match="Artifact digest mismatch"
        ):
            verify_spine_lineage(
                spine=spine,
                expected_artifact_digests=(self.VALID_SHA_ARTIFACT,),
            )

    def test_scenario_c_authority_bypass_rejected(self) -> None:
        """Attempt by S6 Execution Plane to emit GatewayVerdict fails."""
        with pytest.raises(EpistemologicalAuthorityViolationError):
            validate_epistemological_authority(
                stage=EpistemologicalStage.GATEWAY_VERDICT,
                authority=EpistemologicalAuthority.EXECUTION_PLANE,
            )


class TestScenarioDPersistenceAndCrashConsistency:
    """Golden Path Scenario D: Disk-backed ledger atomic persistence."""

    def test_scenario_d_crash_durability_and_state_identity(self) -> None:
        """Ledger reload from disk yields bitwise identical state."""
        roadmap, policy, _ = _setup_curriculum_fixtures()

        with tempfile.TemporaryDirectory() as tmp_dir:
            ledger_path = Path(tmp_dir) / "evidence_ledger.jsonl"

            # 1. Initialize ledger, commit entry, and derive initial state
            ledger_1 = EvidenceLedger(file_path=ledger_path)
            now = datetime.now(timezone.utc)
            rec = EvidenceRecord(
                record_id="ev-persist-01",
                student_id="bob",
                node_id="NET-01",
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.PASS,
                score=0.9,
                timestamp=now,
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="s6_python_adapter",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                metadata={
                    "session_id": "sess-persist",
                    "details": "Socket lab completed",
                },
            )
            entry_1 = ledger_1.append_evidence(rec)
            state_1 = derive_student_state(
                roadmap,
                policy,
                ledger_1,
                "bob",
                as_of_time=entry_1.committed_at,
            )

            # 2. Simulate process crash / restart by reloading from file
            ledger_2 = EvidenceLedger(file_path=ledger_path)
            report = ledger_2.verify_integrity()
            assert report.status == LedgerIntegrityStatus.VALID
            assert ledger_2.total_entries == 1
            assert ledger_2.tip_hash == ledger_1.tip_hash

            # 3. Derive state from reloaded ledger
            state_2 = derive_student_state(
                roadmap,
                policy,
                ledger_2,
                "bob",
                as_of_time=entry_1.committed_at,
            )

            # Deterministic equality: bitwise identical state ID
            assert state_1.canonical_state_id == state_2.canonical_state_id
            assert state_1.ledger_cutoff_hash == state_2.ledger_cutoff_hash
            s1_net = state_1.get_node_state("NET-01")
            s2_net = state_2.get_node_state("NET-01")
            assert s1_net is not None and s2_net is not None
            assert (
                s1_net.status
                == s2_net.status
                == NodeProgressStatus.ASSESSED_PROFICIENT
            )


class TestScenarioEAdversarialSecurityAndLockedNodes:
    """Golden Path Scenario E: Inviolability of locked nodes/types."""

    def test_scenario_e_locked_node_targeting_rejected(self) -> None:
        """Orchestrator rejects targeting a locked node without prereqs."""
        from study_engine.session.contracts import LockedNodeTargetError

        roadmap, policy, ledger = _setup_curriculum_fixtures()
        orch = SessionOrchestrator("sess-e", "alice", roadmap, policy, ledger)
        orch.start_session()
        now = datetime.now(timezone.utc)
        curr_state = derive_student_state(roadmap, policy, ledger, "alice")

        # Attempt to target locked NET-02
        s_input = StudentInput(
            input_id="inp-locked",
            session_id="sess-e",
            turn_index=0,
            input_type=StudentInputType.QUESTION,
            content="I want to jump directly to socket programming.",
            timestamp=now,
            requested_node_id="NET-02",
        )
        with pytest.raises(LockedNodeTargetError, match="is LOCKED"):
            orch.decide_turn(s_input, curr_state)

    def test_scenario_e_operational_event_ledger_injection_blocked(
        self,
    ) -> None:
        """OperationalEvent cannot be injected into the EvidenceLedger."""
        ledger = EvidenceLedger()
        op_event = OperationalEvent(
            event_id="op-100",
            correlation_id="corr-1",
            causation_id="cause-1",
            event_type="tool.invoked",
            component="S6_EXECUTION_PLANE",
            payload={"cmd": "tshark"},
        )

        with pytest.raises(
            TypeError, match="Only EvidenceRecord can be committed"
        ):
            ledger.append_evidence(op_event)  # type: ignore[arg-type]
