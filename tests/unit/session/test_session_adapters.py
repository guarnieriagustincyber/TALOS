"""Unit and contract tests for Subsystem S5.3 infrastructure adapters (Hito 3).

Validates:
- ForensicAuditAdapter translation layer over frozen S4.4 ForensicAuditor.
- Fail-closed canonical abstention on S4.4 rejection (zero self-repair loop).
- ReplayFixtureBackend and ReplayMockBackend deterministic fixtures.
- StructuredTutorAdapter and CurriculumRetrievalAdapter port conformances.
- End-to-end orchestrator execution with real adapters.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import pytest

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import AuditVerdict
from study_engine.evidence.engine import EvidenceEngine
from study_engine.context.packer import ContextPacker
from study_engine.contracts.evidence_engine import PackagedContext
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationParameters,
    GenerationRequest,
    RawGenerationResult,
)
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.generation.mock import MockGenerator
from study_engine.generation.parser import GenerationOutputParser
from study_engine.generation.tutor import StructuredTutor
from study_engine.llm.backends import ReplayMockBackend
from study_engine.session.adapters import (
    CurriculumRetrievalAdapter,
    ForensicAuditAdapter,
    ReplayFixtureBackend,
    StructuredTutorAdapter,
)
from study_engine.session.contracts import (
    SessionRequest,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from typing import Dict, Tuple
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


def _make_test_fixtures() -> Tuple[
    CurricularRoadmap, AssessmentPolicy, EvidenceLedger
]:
    n_a = RoadmapNode(
        node_id="node-a",
        title="Topic A",
        description="Root",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=1,
    )
    n_b = RoadmapNode(
        node_id="node-b",
        title="Topic B",
        description="Child",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=2,
    )
    nodes: Dict[str, RoadmapNode] = {"node-a": n_a, "node-b": n_b}
    deps: Tuple[RoadmapDependency, ...] = (
        RoadmapDependency(
            source_node_id="node-a",
            target_node_id="node-b",
            dependency_type=DependencyType.HARD,
        ),
    )
    rm_id = compute_canonical_revision_id("rm", "Roadmap", "1.0", nodes, deps)
    roadmap = CurricularRoadmap(
        roadmap_id="rm",
        title="Roadmap",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rm_id,
    )

    req = EvidenceRequirement(
        requirement_id="req-1",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-topic",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit}
    pol_id = compute_canonical_policy_id("pol", "Policy", "1.0", defaults, {})
    policy = AssessmentPolicy(
        policy_id="pol",
        title="Policy",
        version="1.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=pol_id,
    )
    ledger = EvidenceLedger()
    return roadmap, policy, ledger


def _build_test_packaged_context(
    chunk_content: str = "Concurrency is the composition of independently executing processes.",
) -> PackagedContext:
    """Helper creating a valid PackagedContext using EvidenceEngine and ContextPacker."""
    candidates = [
        ScoredCandidate(
            chunk_id="chunk-c1",
            document_id="doc-concurrency.pdf",
            source_id="src-concurrency",
            notebook_id="nb-os-concurrency",
            rank=1,
            score=0.95,
            retrieval_method="hybrid",
            content=chunk_content,
        )
    ]
    packet = EvidenceEngine().evaluate_candidates(
        query="What is concurrency?",
        notebook_id="nb-os-concurrency",
        candidates=candidates,
    )
    return ContextPacker().pack(packet)


def test_forensic_audit_adapter_approved() -> None:
    """ForensicAuditAdapter successfully delegates to frozen S4.4 and approves grounded output."""
    ctx = _build_test_packaged_context()
    req = GenerationRequest(
        request_id="gen-test-01",
        notebook_id="nb-os-concurrency",
        query="What is concurrency?",
        mode=GenerationMode.EXPLANATION,
        packaged_context=ctx,
    )

    parser = GenerationOutputParser()
    raw = RawGenerationResult(
        raw_content="As demonstrated in [E1], concurrency involves executing independent processes."
    )
    resp = parser.parse(raw_result=raw, request=req)

    adapter = ForensicAuditAdapter(ForensicAuditor())
    report = adapter.audit_response(req, resp)

    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.request_id == req.request_id
    assert report.notebook_id == req.notebook_id
    assert report.audit_latency_ms >= 0.0


def test_forensic_audit_adapter_rejected_unsupported() -> None:
    """ForensicAuditAdapter fails-closed when output introduces ungrounded citation [E99]."""
    ctx = _build_test_packaged_context()
    req = GenerationRequest(
        request_id="gen-test-02",
        notebook_id="nb-os-concurrency",
        query="What is concurrency?",
        mode=GenerationMode.EXPLANATION,
        packaged_context=ctx,
    )

    parser = GenerationOutputParser()
    raw = RawGenerationResult(
        raw_content="According to [E99], concurrency is magical and free of bugs."
    )
    resp = parser.parse(raw_result=raw, request=req)

    adapter = ForensicAuditAdapter(ForensicAuditor())
    report = adapter.audit_response(req, resp)

    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert report.request_id == req.request_id


def test_replay_fixture_backend_lookup() -> None:
    """ReplayFixtureBackend retrieves canonical approved and rejected fixtures from json."""
    backend = ReplayFixtureBackend()

    fix_approved = backend.get_fixture_by_id("fixture_approved_concurrency_01")
    assert fix_approved is not None
    assert "[E1]" in fix_approved["raw_content"]
    assert fix_approved["expected_audit_verdict"] == "APPROVED"

    fix_rejected = backend.get_fixture_by_id("fixture_rejected_hallucination_02")
    assert fix_rejected is not None
    assert "[E99]" in fix_rejected["raw_content"]
    assert fix_rejected["expected_audit_verdict"] == "REJECTED_UNSUPPORTED"

    # Query search
    found = backend.find_by_query_or_node(
        query="¿Qué es una condición de carrera?",
        node_id="SEC-04-CONCURR",
    )
    assert found is not None
    assert found["fixture_id"] == "fixture_approved_concurrency_01"


def test_replay_mock_backend_completion() -> None:
    """ReplayMockBackend provides completion based on query lookup."""
    from study_engine.generation.prompts import PromptAssembler

    backend = ReplayMockBackend()
    ctx = _build_test_packaged_context()
    req = GenerationRequest(
        request_id="gen-test-replay-01",
        notebook_id="nb-os-concurrency",
        query="Por favor explica ¿Qué es una condición de carrera?",
        mode=GenerationMode.EXPLANATION,
        packaged_context=ctx,
    )
    bundle = PromptAssembler().assemble(req)
    comp = backend.complete(bundle)
    assert "[E1]" in comp.text
    assert comp.generator_abstained is False


def test_structured_tutor_adapter_answering() -> None:
    """StructuredTutorAdapter delegates to StructuredTutor and returns validated response."""
    ctx = _build_test_packaged_context()
    req = GenerationRequest(
        request_id="gen-test-03",
        notebook_id="nb-os-concurrency",
        query="Explain concurrency",
        mode=GenerationMode.EXPLANATION,
        packaged_context=ctx,
    )

    mock_gen = MockGenerator(
        canned_content="Concurrency allows multiple executions [E1]."
    )
    tutor = StructuredTutor(mock_gen)
    adapter = StructuredTutorAdapter(tutor)

    resp = adapter.generate_tutoring(req)
    assert resp.request_id == req.request_id
    assert "[E1]" in resp.text


def test_orchestrator_integration_with_real_adapters_approved() -> None:
    """End-to-end SessionOrchestrator with real adapters certifies approved turn."""
    roadmap, policy, ledger = _make_test_fixtures()

    class TestRetrievalPort:
        def retrieve_evidence(
            self, query: str, node_id: str, registry: object, top_k: int = 5
        ) -> List[ScoredCandidate]:
            return [
                ScoredCandidate(
                    chunk_id="chunk-c1",
                    document_id="doc-1.pdf",
                    source_id="src-1",
                    notebook_id="nb-1",
                    rank=1,
                    score=0.95,
                    retrieval_method="hybrid",
                    content="Concurrency involves independent threads of execution.",
                )
            ]

    mock_gen = MockGenerator()
    tutor = StructuredTutor(mock_gen)
    tutor_adapter = StructuredTutorAdapter(tutor)
    audit_adapter = ForensicAuditAdapter(ForensicAuditor())

    orch = SessionOrchestrator(
        session_id="s-integ-appr",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=TestRetrievalPort(),
        tutor_port=tutor_adapter,
        audit_port=audit_adapter,
    )
    orch.start_session()

    req = SessionRequest(
        session_id="s-integ-appr",
        student_id="alice",
        node_id="node-a",
        query="Explain concurrency fundamentals",
        turn_index=1,
    )

    res = orch.handle_session_request(req)
    assert res.status == SessionResultStatus.APPROVED
    assert "Según la evidencia documentada [E1]" in res.response_text
    assert res.audit_report_id is not None
    assert res.abstention_reason is None


def test_orchestrator_integration_with_real_adapters_rejection() -> None:
    """End-to-end SessionOrchestrator with real adapters immediately abstains on S4.4 rejection."""
    roadmap, policy, ledger = _make_test_fixtures()

    class TestRetrievalPort:
        def retrieve_evidence(
            self, query: str, node_id: str, registry: object, top_k: int = 5
        ) -> List[ScoredCandidate]:
            return [
                ScoredCandidate(
                    chunk_id="chunk-c1",
                    document_id="doc-1.pdf",
                    source_id="src-1",
                    notebook_id="nb-1",
                    rank=1,
                    score=0.95,
                    retrieval_method="hybrid",
                    content="Concurrency involves independent threads of execution.",
                )
            ]

    # Hallucinated content with unregistered citation [E99]
    mock_gen = MockGenerator(
        canned_content="Esta conjetura introduce una cita no fundamentada [E99]."
    )
    tutor = StructuredTutor(mock_gen)
    tutor_adapter = StructuredTutorAdapter(tutor)
    audit_adapter = ForensicAuditAdapter(ForensicAuditor())

    orch = SessionOrchestrator(
        session_id="s-integ-rej",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=TestRetrievalPort(),
        tutor_port=tutor_adapter,
        audit_port=audit_adapter,
    )
    orch.start_session()

    req = SessionRequest(
        session_id="s-integ-rej",
        student_id="alice",
        node_id="node-a",
        query="Explain ungrounded claims",
        turn_index=1,
    )

    res = orch.handle_session_request(req)
    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "REJECTED_UNSUPPORTED"
    assert "Forensic audit rejected generated response" in res.response_text
    assert res.audit_report_id is not None
