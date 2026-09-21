"""Contract tests for Perturbation templates (S5.4)."""

import pytest
from pydantic import ValidationError

from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.perturbation_contracts import (
    ExpectedBehavior,
    PerturbationTemplate,
    PerturbationType,
)


def test_perturbation_template_requires_n3() -> None:
    """Perturbation must declare at least an N3 expectation."""
    n4_only = {
        PerformanceLevel.N4_EXCELLENT: ExpectedBehavior(
            performance_level=PerformanceLevel.N4_EXCELLENT,
            expected_reasoning="Predicts exact breakage",
            expected_action="Patches unpack logic",
        )
    }
    with pytest.raises(
        ValidationError,
        match="must define expectations for PerformanceLevel.N3_COMPETENT",
    ):
        PerturbationTemplate(
            perturbation_id="pert-bad",
            type=PerturbationType.PARAMETER_MUTATION,
            name="Bad Perturbation",
            description="Missing N3",
            baseline_condition="default",
            mutated_condition="mutated",
            level_expectations=n4_only,
        )


def test_g1_2_endianness_perturbation_representation() -> None:
    """Demonstrate representation of G1.2 #1 (Endianness Swap)."""
    n3_exp = ExpectedBehavior(
        performance_level=PerformanceLevel.N3_COMPETENT,
        expected_reasoning="Campos de 16+ bits se invierten por little-endian",
        expected_action="Diagnostica usar '!' para red (RFC 791 big-endian)",
    )
    n4_exp = ExpectedBehavior(
        performance_level=PerformanceLevel.N4_EXCELLENT,
        expected_reasoning="Predice Version/IHL y TTL/Protocol no sufren swap",
        expected_action="Escribe test con struct.pack('!H') vs '<H'",
    )

    template = PerturbationTemplate(
        perturbation_id="pert-g12-endianness-swap",
        type=PerturbationType.PARAMETER_MUTATION,
        name="Endianness Format Swap ('!' to '<')",
        description="Mutación de endianness en parser IPv4",
        baseline_condition="struct.unpack('!BBHHHBBH4s4s', raw_ip_header)",
        mutated_condition="struct.unpack('<BBHHHBBH4s4s', raw_ip_header)",
        level_expectations={
            PerformanceLevel.N3_COMPETENT: n3_exp,
            PerformanceLevel.N4_EXCELLENT: n4_exp,
        },
    )

    assert template.perturbation_id == "pert-g12-endianness-swap"
    assert template.type == PerturbationType.PARAMETER_MUTATION
    assert PerformanceLevel.N3_COMPETENT in template.level_expectations
    assert PerformanceLevel.N4_EXCELLENT in template.level_expectations


def test_perturbation_taxonomy_complete() -> None:
    """Ensure all 6 canonical perturbation types exist."""
    assert len(PerturbationType) == 6
    assert set(PerturbationType) == {
        PerturbationType.PARAMETER_MUTATION,
        PerturbationType.FAULT_INJECTION,
        PerturbationType.BOUNDARY_CONDITION,
        PerturbationType.ADVERSARIAL_INPUT,
        PerturbationType.ENVIRONMENT_DEGRADATION,
        PerturbationType.PROTOCOL_VIOLATION,
    }
