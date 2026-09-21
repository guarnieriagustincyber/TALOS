"""Contract tests for Gateway specifications and attempts (S5.4)."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.curriculum.gateway_contracts import (
    GatewayAttemptRecord,
    GatewayDefinition,
    GatewayFormat,
    GatewayVerdictCriteria,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel


def test_gateway_definition_zero_verdict_authority() -> None:
    """HG-S5.4-03: GatewayDefinition specifies criteria; never emits."""
    criteria = GatewayVerdictCriteria(
        criteria_id="crit-g01",
        minimum_overall_level=PerformanceLevel.N3_COMPETENT,
        require_all_dimensions_pass=True,
    )

    gateway = GatewayDefinition(
        gateway_id="G0.1",
        curriculum_node_id="node-f0-g01",
        title="Gateway G0.1: Parser de Log Desconocido",
        format=GatewayFormat.INDIVIDUAL_PRACTICAL,
        rubric_id="rubric-g01",
        verdict_criteria=criteria,
    )

    # Assert absence of verdict emission methods
    assert not hasattr(gateway, "emit_verdict")
    assert not hasattr(gateway, "grant_mastery")
    assert not hasattr(gateway, "set_verdict")
    assert not hasattr(gateway, "update_student_state")
    assert not hasattr(gateway, "write_to_ledger")


def test_gateway_attempt_record_zero_evaluation_attributes() -> None:
    """R1.2: GatewayAttemptRecord contains operational facts, not verdicts."""
    now = datetime.now(timezone.utc)
    attempt = GatewayAttemptRecord(
        attempt_id="att-uuid-001",
        gateway_id="G0.1",
        student_id="student-42",
        session_id="sess-99",
        started_at=now,
        completed_at=now,
        submitted_artifact_ids=("art-01", "art-02"),
        observation_refs=("obs-trace-01",),
        perturbation_response_refs=("resp-pert-01",),
    )

    # Immutability check
    with pytest.raises(ValidationError):
        attempt.completed_at = now

    # No scoring/verdict attributes
    assert not hasattr(attempt, "verdict")
    assert not hasattr(attempt, "score")
    assert not hasattr(attempt, "is_passing")
    assert not hasattr(attempt, "rubric_evaluation")


def test_g0_1_unknown_log_parser_gateway_representation() -> None:
    """Demonstrate representation of Gateway G0.1 from real curriculum."""
    crit = GatewayVerdictCriteria(
        criteria_id="crit-g01",
        minimum_overall_level=PerformanceLevel.N3_COMPETENT,
        max_attempt_duration_minutes=30,
    )

    g01 = GatewayDefinition(
        gateway_id="G0.1",
        curriculum_node_id="node-t01-log-parsing",
        title="Gateway G0.1: Parser Funcional de Log Desconocido",
        format=GatewayFormat.INDIVIDUAL_PRACTICAL,
        rubric_id="rubric-g01-log-parser",
        verdict_criteria=crit,
        practical_task_ids=("task-g01-parse-unknown-log",),
        required_evidence_outcomes=(
            "outcome-t01-dataclasses",
            "outcome-t01-complexity-analysis",
        ),
    )

    assert g01.gateway_id == "G0.1"
    assert g01.verdict_criteria.max_attempt_duration_minutes == 30
    assert len(g01.required_evidence_outcomes) == 2


def test_g6a_capstone_gateway_representation() -> None:
    """Demonstrate representation of Gateway G6A (Track A Capstone)."""
    crit = GatewayVerdictCriteria(
        criteria_id="crit-g6a",
        minimum_overall_level=PerformanceLevel.N3_COMPETENT,
        require_all_dimensions_pass=True,
        allow_compensation=True,
        max_attempt_duration_minutes=75,
    )

    g6a = GatewayDefinition(
        gateway_id="G6A",
        curriculum_node_id="node-track-a-capstone",
        title="Gateway G6A: Cloud-Native SOC & Threat Hunting Defense",
        format=GatewayFormat.CAPSTONE_DEFENSE,
        rubric_id="rubric-g6a-5dimensions",
        verdict_criteria=crit,
        practical_task_ids=("task-p21a-cloud-soc",),
        perturbation_ids=(
            "pert-g6a-cloudtrail-disabled",
            "pert-g6a-k8s-api-attack",
            "pert-g6a-hostpid",
        ),
        oral_defense_id="defense-g6a-panel",
        associated_project_id="P21-A",
        required_evidence_outcomes=(
            "outcome-cloud-security",
            "outcome-devsecops",
            "outcome-k8s-soc",
        ),
    )

    assert g6a.gateway_id == "G6A"
    assert g6a.format == GatewayFormat.CAPSTONE_DEFENSE
    assert g6a.associated_project_id == "P21-A"
    assert len(g6a.perturbation_ids) == 3
