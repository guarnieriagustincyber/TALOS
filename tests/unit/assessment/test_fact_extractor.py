"""Unit tests for Instrumental Fact Extractor (S9.1.2).

Verifies:
1. Proper extraction of process exit, duration, and termination facts.
2. Conclusive vs truncated observability tagging on output streams.
3. Proper artifact extraction (present, size, sha256).
4. Strict VERIFIED_ABSENCE vs ARTIFACT_OMITTED_BY_LIMIT distinction.
"""

from study_engine.assessment.fact_extractor import extract_instrumental_facts
from study_engine.contracts.assessment import (
    FactObservability,
    InstrumentalFactType,
)
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ExecutionObservation,
    ExecutionStatus,
    ObservedArtifact,
    ProcessTelemetry,
    TerminationReason,
)


def _sample_observation(
    exit_code: int = 0,
    term_reason: TerminationReason = TerminationReason.NORMAL_EXIT,
    truncated: bool = False,
    stdout: str = "hello\n",
    stderr: str = "",
    produced_artifacts: tuple[ObservedArtifact, ...] = (),
    collection_truncated: bool = False,
    artifacts_omitted: int = 0,
) -> ExecutionObservation:
    telemetry = ProcessTelemetry(
        duration_ms=125.5,
        output_truncated=truncated,
        termination_reason=term_reason,
    )
    summary = ArtifactCollectionSummary(
        artifacts_discovered=len(produced_artifacts),
        artifacts_collected=len(produced_artifacts),
        artifacts_omitted=artifacts_omitted,
        collection_truncated=collection_truncated,
    )
    return ExecutionObservation(
        observation_id="obs-unit-001",
        execution_id="exec-unit-001",
        tool_name="python.run_script",
        status=ExecutionStatus.COMPLETED,
        exit_code=exit_code,
        telemetry=telemetry,
        raw_telemetry={
            "exit_code": exit_code,
            "duration_ms": 125.5,
            "termination_reason": term_reason.value,
            "stdout": stdout,
            "stderr": stderr,
        },
        produced_artifacts=produced_artifacts,
        artifact_summary=summary,
    )


class TestFactExtractor:
    """Test suite for extract_instrumental_facts."""

    def test_extract_process_facts(self) -> None:
        """Extracts exit code, duration, termination reason, and timeout."""
        obs = _sample_observation(
            exit_code=0, term_reason=TerminationReason.NORMAL_EXIT
        )
        facts = extract_instrumental_facts(obs)
        fact_types = {f.fact_type for f in facts}
        assert InstrumentalFactType.PROCESS_EXIT_CODE in fact_types
        assert InstrumentalFactType.PROCESS_TERMINATION_REASON in fact_types
        assert InstrumentalFactType.PROCESS_TIMED_OUT in fact_types
        assert InstrumentalFactType.EXECUTION_DURATION_MS in fact_types

        exit_fact = next(
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.PROCESS_EXIT_CODE
        )
        assert exit_fact.fact_value == "0"
        assert exit_fact.observability == FactObservability.CONCLUSIVE

    def test_stream_truncation_observability(self) -> None:
        """Tag stream facts as PARTIAL_TRUNCATED when truncated."""
        obs_clean = _sample_observation(truncated=False, stdout="all good")
        facts_clean = extract_instrumental_facts(obs_clean)
        stdout_clean = next(
            f
            for f in facts_clean
            if f.fact_type == InstrumentalFactType.STDOUT_TEXT_SNIPPET
        )
        assert stdout_clean.observability == FactObservability.CONCLUSIVE

        obs_trunc = _sample_observation(truncated=True, stdout="cut off...")
        facts_trunc = extract_instrumental_facts(obs_trunc)
        stdout_trunc = next(
            f
            for f in facts_trunc
            if f.fact_type == InstrumentalFactType.STDOUT_TEXT_SNIPPET
        )
        assert stdout_trunc.observability == (
            FactObservability.PARTIAL_TRUNCATED
        )

    def test_artifact_presence_and_metadata(self) -> None:
        """Artifact present in workspace produces presence, size, and hash."""
        art = ObservedArtifact(
            artifact_id="art-01",
            relative_path="result.json",
            file_size_bytes=42,
            sha256_digest="c" * 64,
        )
        obs = _sample_observation(produced_artifacts=(art,))
        facts = extract_instrumental_facts(
            obs, expected_paths=("result.json",)
        )

        pres_fact = next(
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.ARTIFACT_PRESENT
        )
        assert pres_fact.fact_value == "result.json"

        # No absence fact emitted for present artifact
        abs_facts = [
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
        ]
        assert len(abs_facts) == 0

    def test_artifact_verified_absence(self) -> None:
        """Clean scan with missing artifact produces VERIFIED_ABSENCE."""
        obs = _sample_observation(
            produced_artifacts=(),
            collection_truncated=False,
            artifacts_omitted=0,
        )
        facts = extract_instrumental_facts(obs, expected_paths=("report.pdf",))

        abs_fact = next(
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
        )
        assert abs_fact.fact_value == "report.pdf"
        assert abs_fact.observability == FactObservability.VERIFIED_ABSENCE
        assert abs_fact.inspected_domain == "scratch/workspace/"

    def test_artifact_omitted_by_limit_not_absence(self) -> None:
        """When collection is truncated, artifact is OMITTED_BY_LIMIT."""
        obs = _sample_observation(
            produced_artifacts=(),
            collection_truncated=True,
            artifacts_omitted=2,
        )
        facts = extract_instrumental_facts(obs, expected_paths=("dump.bin",))

        # Must NOT emit ARTIFACT_VERIFIED_ABSENT
        abs_facts = [
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
        ]
        assert len(abs_facts) == 0

        # Must emit ARTIFACT_OMITTED_BY_LIMIT
        omit_fact = next(
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT
        )
        assert omit_fact.fact_value == "dump.bin"
        assert omit_fact.observability == FactObservability.PARTIAL_TRUNCATED
