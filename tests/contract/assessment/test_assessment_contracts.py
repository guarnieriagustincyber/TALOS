"""Contract tests for Subsystem S9.1 assessment contracts.

Verifies:
1. Immutability and frozen config enforcement.
2. Complete round-trip JSON serialization.
3. DimensionEvaluation consistency rules (status vs assigned_level).
4. Deterministic canonical SHA-256 calculation.
5. Separation of InstrumentalFact vs EvaluativeFact contracts.
6. EpistemologicalAuthority.ASSESSMENT_ENGINE sovereign authority stamp.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.assessment import (
    AggregationResult,
    AssessmentResult,
    AssessmentStatus,
    DimensionEvaluation,
    EvaluativeFact,
    EvaluativeFactType,
    FactObservability,
    InstrumentalFact,
    InstrumentalFactType,
    ObservationReference,
    SpecificationReference,
    compute_canonical_sha256,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.curriculum.performance_contracts import PerformanceLevel


class TestAssessmentContracts:
    """Contract verification for S9.1 assessment data models."""

    VALID_SHA = "a" * 64

    def _sample_spec_ref(self, spec_id: str) -> SpecificationReference:
        return SpecificationReference(
            specification_id=spec_id,
            revision_id="rev-001",
            specification_sha256=self.VALID_SHA,
        )

    def _sample_obs_ref(self) -> ObservationReference:
        return ObservationReference(
            observation_id="obs-001",
            execution_id="exec-001",
            effective_script_sha256=self.VALID_SHA,
            observation_sha256=self.VALID_SHA,
        )

    def _sample_instrumental_fact(self) -> InstrumentalFact:
        return InstrumentalFact(
            fact_id="fact-inst-01",
            observation_id="obs-001",
            fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
            fact_value="0",
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="scratch/workspace/",
            provenance_detail="Process exit code from telemetry",
        )

    def _sample_evaluative_fact(self) -> EvaluativeFact:
        return EvaluativeFact(
            fact_id="fact-eval-01",
            evaluator_id="S9_DETERMINISTIC_EVALUATOR",
            fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
            fact_value="0",
            satisfied=True,
            based_on_instrumental_fact_ids=("fact-inst-01",),
            requirement_id="req-clean-exit",
            rationale="Process exited with expected code 0",
        )

    def _sample_dimension_eval(self) -> DimensionEvaluation:
        return DimensionEvaluation(
            dimension_id="dim-execution",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N3_COMPETENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-eval-01",),
            evaluator_rule_ids=("rule-clean-exit-n3",),
            evaluation_rationale="Exit code satisfied requirement",
        )

    def _sample_assessment_result(self) -> AssessmentResult:
        return AssessmentResult(
            assessment_id="asmt-001",
            task=self._sample_spec_ref("task-net-01"),
            rubric=self._sample_spec_ref("rubric-net-01"),
            observations=(self._sample_obs_ref(),),
            instrumental_facts=(self._sample_instrumental_fact(),),
            evaluative_facts=(self._sample_evaluative_fact(),),
            dimension_evaluations=(self._sample_dimension_eval(),),
            aggregation=AggregationResult(
                overall_level=PerformanceLevel.N3_COMPETENT,
                passed=True,
            ),
            evaluator_id="S9_DETERMINISTIC_EVALUATOR",
            evaluator_version="1.0.0",
            assessed_at=datetime.now(timezone.utc),
        )

    def test_assessment_result_roundtrip_serialization(self) -> None:
        """Complete AssessmentResult serializes and deserializes cleanly."""
        res = self._sample_assessment_result()
        data = res.model_dump()
        restored = AssessmentResult.model_validate(data)
        assert restored.assessment_id == res.assessment_id
        assert restored.authority_id == (
            EpistemologicalAuthority.ASSESSMENT_ENGINE.value
        )
        assert len(restored.instrumental_facts) == 1
        assert len(restored.evaluative_facts) == 1
        assert len(restored.dimension_evaluations) == 1
        assert restored.aggregation.passed is True

    def test_assessment_result_immutability(self) -> None:
        """Models reject mutation and extra fields fail-closed."""
        res = self._sample_assessment_result()
        with pytest.raises(ValidationError):
            setattr(res, "assessment_id", "mutated")

    def test_dimension_evaluation_consistency_validator(self) -> None:
        """DimensionEvaluation strictly validates status vs assigned levels."""
        # Valid ASSESSED
        dim = DimensionEvaluation(
            dimension_id="dim-01",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N3_COMPETENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-01",),
            evaluation_rationale="Passed",
        )
        assert dim.assigned_level == PerformanceLevel.N3_COMPETENT

        # Invalid: ASSESSED without assigned_level
        with pytest.raises(
            ValidationError, match="must have an assigned_level"
        ):
            DimensionEvaluation(
                dimension_id="dim-01",
                status=AssessmentStatus.ASSESSED,
                assigned_level=None,
                passed_minimum=True,
                is_critical=True,
                evidence_evaluative_fact_ids=("fact-01",),
                evaluation_rationale="Invalid",
            )

        # Invalid: INSUFFICIENT_OBSERVATION with assigned_level
        with pytest.raises(
            ValidationError, match="cannot have assigned_level"
        ):
            DimensionEvaluation(
                dimension_id="dim-01",
                status=AssessmentStatus.INSUFFICIENT_OBSERVATION,
                assigned_level=PerformanceLevel.N1_INSUFFICIENT,
                passed_minimum=False,
                is_critical=True,
                evidence_evaluative_fact_ids=(),
                evaluation_rationale="Invalid",
            )

        # Valid INSUFFICIENT_OBSERVATION
        dim_insufficient = DimensionEvaluation(
            dimension_id="dim-01",
            status=AssessmentStatus.INSUFFICIENT_OBSERVATION,
            assigned_level=None,
            passed_minimum=None,
            is_critical=True,
            evidence_evaluative_fact_ids=(),
            evaluation_rationale="Output was truncated before evaluation",
        )
        assert dim_insufficient.assigned_level is None
        assert dim_insufficient.passed_minimum is None

    def test_deterministic_canonical_sha256(self) -> None:
        """compute_canonical_sha256 produces deterministic hash."""
        fact = self._sample_instrumental_fact()
        hash1 = compute_canonical_sha256(fact)
        hash2 = compute_canonical_sha256(fact)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_instrumental_vs_evaluative_fact_separation(self) -> None:
        """InstrumentalFact rejects evaluative types and vice versa."""
        # InstrumentalFact rejects EvaluativeFactType
        bad_eval_type: object = (
            EvaluativeFactType.ARTIFACT_CONFORMS_TO_REQUIREMENT
        )
        with pytest.raises(ValidationError):
            InstrumentalFact(
                fact_id="fact-bad-01",
                observation_id="obs-001",
                fact_type=bad_eval_type,  # type: ignore[arg-type]
                fact_value="true",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="scratch/workspace/",
                provenance_detail="Detail",
            )

        # EvaluativeFact rejects InstrumentalFactType
        bad_inst_type: object = InstrumentalFactType.PROCESS_EXIT_CODE
        with pytest.raises(ValidationError):
            EvaluativeFact(
                fact_id="fact-bad-02",
                evaluator_id="S9_EVALUATOR",
                fact_type=bad_inst_type,  # type: ignore[arg-type]
                fact_value="0",
                satisfied=True,
                based_on_instrumental_fact_ids=("fact-01",),
                requirement_id="req-01",
                rationale="Rationale",
            )
