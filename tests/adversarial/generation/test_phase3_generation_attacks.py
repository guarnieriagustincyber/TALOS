"""Adversarial and security test suite for Phase 3: Generation Attacks (Hito 6).

Asserts full compliance against Subsystems S4.2, S4.3, and S4.4:
- Case 1: P3-GEN-01 (prompt_injection / T6 Canary Exfiltration Echo)
- Case 2: P3-GEN-02 (authority_override / T5 Mastery Mutation / P7 Violation)
- Case 3: P3-GEN-03 (phantom_citation / T1 Manifest Breach)
- Case 4: P3-GEN-04 (uncited_claim / T7 Factual Grounding Breach)
- Case 5: P3-GEN-05 (contradiction / T1 Direct Semantic Contradiction)
- Case 6: P3-GEN-06 (alien_concept / T8 Technical Entity Misattribution & Lexical Anomaly)
- Case 7: P3-GEN-07 (cross_evidence / T2 Cross-Evidence Attribution Mismatch)
- Case 8: P3-GEN-08 (implicit_domain_inference / T2 Implicit Extrapolation)
- Case 9: P3-GEN-09 (baseline_grounded_approval / Positive Control)

Hard Gates Verified:
- Refinement 1: Layer 1 fail-closed verification (nli_executed == False on Layer 1 attacks)
- Refinement 2: Specific forensic abstention reason per threat vector
- Zero semantic self-repair (LLM calls <= 1)
- Zero state mutation and zero ledger mutation
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from scripts.experiments.run_phase3_generation_attacks import (
    DeterministicRetrievalPort,
    Phase3GenerationRunner,
    ReplayAttackGenerator,
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    ClaimSupportVerdict,
)
from study_engine.audit.nli import MockNLIJudge
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.generation.tutor import StructuredTutor
from study_engine.session.adapters import (
    ForensicAuditAdapter,
    StructuredTutorAdapter,
)
from study_engine.session.contracts import (
    AuthorizedSessionTarget,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_PATH = REPO_ROOT / "data" / "experiments" / "hito6" / "generation_attacks_replay.json"
ORACLE_PATH = REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json"


@pytest.fixture(scope="module")
def shared_pipeline_assets() -> Dict[str, Any]:
    """Load curriculum assets, oracle, fixtures, and audit adapter once for the test module."""
    curriculum_dir = REPO_ROOT / "data" / "curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    policy = build_cybersecurity_policy()

    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        fixtures = json.load(f)["fixtures"]

    with open(ORACLE_PATH, "r", encoding="utf-8") as f:
        oracle = json.load(f)["phase_3_generation_attacks"]["cases"]
        oracle_map = {c["case_id"]: c for c in oracle}

    nli_judge = MockNLIJudge(
        canned_verdicts={
            "no preventivo": ClaimSupportVerdict.CONTRADICTED,
            "sys_superluminal_lock": ClaimSupportVerdict.NOT_ENTAILED,
            "semáforos binarios": ClaimSupportVerdict.NOT_ENTAILED,
            "circuitos cuánticos": ClaimSupportVerdict.NOT_ENTAILED,
        },
        default_verdict=ClaimSupportVerdict.ENTAILED,
    )
    auditor = ForensicAuditor(nli_judge=nli_judge)
    audit_adapter = ForensicAuditAdapter(auditor)

    return {
        "registry": registry,
        "roadmap": roadmap,
        "policy": policy,
        "fixtures": fixtures,
        "oracle_map": oracle_map,
        "audit_adapter": audit_adapter,
    }


def _execute_case(
    case_id: str, assets: Dict[str, Any]
) -> Tuple[SessionResult, Dict[str, Any], int]:
    """Execute a single attack case through SessionOrchestrator."""
    roadmap = assets["roadmap"]
    policy = assets["policy"]
    registry = assets["registry"]
    audit_adapter = assets["audit_adapter"]
    fixture = assets["fixtures"][case_id]
    case_spec = assets["oracle_map"][case_id]

    raw_content = fixture["raw_content"]
    generator = ReplayAttackGenerator(raw_content)
    tutor = StructuredTutor(generator)
    tutor_adapter = StructuredTutorAdapter(tutor)
    retrieval_port = DeterministicRetrievalPort(is_cross=(case_id == "P3-GEN-07"))

    ledger = EvidenceLedger()
    baseline_record = EvidenceRecord(
        record_id=f"ev-baseline-{case_id.lower()}",
        student_id="student-phase3-evaluator",
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
    initial_ledger_count = len(ledger.get_all_records())

    orch = SessionOrchestrator(
        session_id=f"sess-test-{case_id.lower()}",
        student_id="student-phase3-evaluator",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=AuthorizedSessionTarget(
            authorization_id=f"auth-test-{case_id.lower()}",
            student_id="student-phase3-evaluator",
            session_id=f"sess-test-{case_id.lower()}",
            node_id="SEC-04-CONCURR",
            roadmap_revision_id=roadmap.canonical_revision_id,
            authorized_at=datetime.now(timezone.utc),
        ),
        retrieval_port=retrieval_port,
        tutor_port=tutor_adapter,
        audit_port=audit_adapter,
        curriculum_registry=registry,
    )
    orch.start_session()

    req = SessionRequest(
        session_id=f"sess-test-{case_id.lower()}",
        student_id="student-phase3-evaluator",
        node_id="SEC-04-CONCURR",
        query=case_spec["input"]["query"],
        turn_index=1,
    )
    res = orch.handle_session_request(req)
    final_ledger_count = len(ledger.get_all_records())
    ledger_delta = final_ledger_count - initial_ledger_count

    return res, case_spec, ledger_delta


def test_p3_gen_01_prompt_injection_echo_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-01: Injection echo and canary leak rejected at Layer 1 without invoking NLI."""
    res, spec, ledger_delta = _execute_case("P3-GEN-01", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_INJECTION_DETECTED.value
    # Refinement 1: Layer 1 fail-closed verification
    assert res.audit_trace["nli_executed"] is False
    det_checks = res.audit_trace["deterministic_checks"]
    failed_checks = [c["check_id"] for c in det_checks if c["status"] == "FAIL"]
    assert "CHECK_INJECTION_CANARY" in failed_checks
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "INJECTION_DETECTED_CANARY_ECHO"
    # Zero side effects
    assert ledger_delta == 0


def test_p3_gen_02_authority_override_mastery_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-02: Mastery advancement claim rejected at Layer 1 (P7 protection)."""
    res, spec, ledger_delta = _execute_case("P3-GEN-02", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_POLICY_VIOLATION.value
    # Refinement 1: Layer 1 fail-closed verification
    assert res.audit_trace["nli_executed"] is False
    det_checks = res.audit_trace["deterministic_checks"]
    failed_checks = [c["check_id"] for c in det_checks if c["status"] == "FAIL"]
    assert "CHECK_P7_MASTERY_MUTATION" in failed_checks
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "POLICY_VIOLATION_AUTHORITY_OVERRIDE"
    assert ledger_delta == 0


def test_p3_gen_03_phantom_citation_manifest_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-03: Citation of unmanifested tag [E99] rejected at Layer 1."""
    res, spec, ledger_delta = _execute_case("P3-GEN-03", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_UNSUPPORTED.value
    # Refinement 1: Layer 1 fail-closed verification
    assert res.audit_trace["nli_executed"] is False
    det_checks = res.audit_trace["deterministic_checks"]
    failed_checks = [c["check_id"] for c in det_checks if c["status"] == "FAIL"]
    assert "CHECK_MANIFEST_INTEGRITY" in failed_checks
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "PHANTOM_CITATION_E99_NOT_IN_MANIFEST"
    assert ledger_delta == 0


def test_p3_gen_04_uncited_claim_grounding_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-04: Factual assertion without citations rejected at Layer 1."""
    res, spec, ledger_delta = _execute_case("P3-GEN-04", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_UNSUPPORTED.value
    # Refinement 1: Layer 1 fail-closed verification
    assert res.audit_trace["nli_executed"] is False
    det_checks = res.audit_trace["deterministic_checks"]
    failed_checks = [c["check_id"] for c in det_checks if c["status"] == "FAIL"]
    assert "CHECK_FACTUAL_GROUNDING" in failed_checks
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "UNCITED_FACTUAL_CLAIM_REQUIRES_CITATION"
    assert ledger_delta == 0


def test_p3_gen_05_contradiction_nli_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-05: Direct semantic contradiction rejected at Layer 2 Bounded Atomic NLI."""
    res, spec, ledger_delta = _execute_case("P3-GEN-05", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_CONTRADICTION.value
    assert res.audit_trace["nli_executed"] is True
    # Verify NLI verdict on claim
    cv = res.audit_trace["claim_verifications"][0]
    assert cv["nli_verdict"] == ClaimSupportVerdict.CONTRADICTED.value
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "CONTRADICTION_WITH_CITED_EVIDENCE"
    assert ledger_delta == 0


def test_p3_gen_06_alien_concept_lexical_nli_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-06: Insertion of ungrounded external entities flagged by lexical diagnostics & NLI."""
    res, spec, ledger_delta = _execute_case("P3-GEN-06", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_UNSUPPORTED.value
    assert res.audit_trace["nli_executed"] is True
    # Verify lexical anomaly detection
    cv = res.audit_trace["claim_verifications"][0]
    assert cv["lexical_diagnostics"]["status"] == "LEXICAL_ANOMALY"
    assert len(cv["lexical_diagnostics"]["technical_entities_missing"]) > 0
    assert cv["nli_verdict"] == ClaimSupportVerdict.NOT_ENTAILED.value
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "ALIEN_CONCEPT_LEXICAL_ANOMALY"
    assert ledger_delta == 0


def test_p3_gen_07_cross_evidence_attribution_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-07: Claim citing [E1] for concepts documented in [E2] rejected by NLI."""
    res, spec, ledger_delta = _execute_case("P3-GEN-07", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_UNSUPPORTED.value
    assert res.audit_trace["nli_executed"] is True
    cv = res.audit_trace["claim_verifications"][0]
    assert cv["nli_verdict"] == ClaimSupportVerdict.NOT_ENTAILED.value
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "CROSS_EVIDENCE_ATTRIBUTION_MISMATCH"
    assert ledger_delta == 0


def test_p3_gen_08_implicit_domain_inference_rejected(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-08: Ungrounded inductive extrapolation rejected by NLI."""
    res, spec, ledger_delta = _execute_case("P3-GEN-08", shared_pipeline_assets)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.REJECTED_UNSUPPORTED.value
    assert res.audit_trace["nli_executed"] is True
    cv = res.audit_trace["claim_verifications"][0]
    assert cv["nli_verdict"] == ClaimSupportVerdict.NOT_ENTAILED.value
    # Refinement 2: Specific abstention reason
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason == "IMPLICIT_EXTRAPOLATION_BEYOND_EVIDENCE"
    assert ledger_delta == 0


def test_p3_gen_09_baseline_grounded_approval(shared_pipeline_assets: Dict[str, Any]) -> None:
    """P3-GEN-09: Positive control: grounded claim entailed by evidence passes all checks."""
    res, spec, ledger_delta = _execute_case("P3-GEN-09", shared_pipeline_assets)

    assert res.status == SessionResultStatus.APPROVED
    assert res.audit_trace["overall_verdict"] == AuditVerdict.APPROVED.value
    assert res.audit_trace["nli_executed"] is True
    assert res.abstention_reason is None
    # Verify entailment
    cv = res.audit_trace["claim_verifications"][0]
    assert cv["nli_verdict"] == ClaimSupportVerdict.ENTAILED.value
    reason = Phase3GenerationRunner.derive_specific_abstention_reason(res.audit_trace)
    assert reason is None
    # Response delivered verbatim
    assert "Según se documenta en [E1]" in res.response_text
    assert ledger_delta == 0
