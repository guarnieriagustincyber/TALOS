"""Instrumental fact extractor for Subsystem S9.1.

INVARIANTS:
1. Derives purely instrumental facts from ExecutionObservation.
2. Never evaluates conformance, scores, or grades (S9 evaluator duty).
3. Distinguishes VERIFIED_ABSENCE (exhaustive scan completed without limits)
   from ARTIFACT_OMITTED_BY_LIMIT (collection truncated or files dropped).
4. Strictly frozen and deterministic output.
"""

from typing import List, Tuple

from study_engine.contracts.assessment import (
    FactObservability,
    InstrumentalFact,
    InstrumentalFactType,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    TerminationReason,
)


def extract_instrumental_facts(
    observation: ExecutionObservation,
    expected_paths: Tuple[str, ...] = (),
) -> Tuple[InstrumentalFact, ...]:
    """Extract formalized InstrumentalFacts from an ExecutionObservation."""
    obs_id = observation.observation_id
    facts: List[InstrumentalFact] = []

    # 1. Process termination and exit facts
    exit_code = (
        observation.exit_code
        if observation.exit_code is not None
        else observation.raw_telemetry.get("exit_code", -1)
    )
    facts.append(
        InstrumentalFact(
            fact_id=f"fact-exit-{obs_id}",
            observation_id=obs_id,
            fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
            fact_value=str(exit_code),
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="process",
            provenance_detail=f"Process exited with code {exit_code}",
        )
    )

    term_reason = TerminationReason.NORMAL_EXIT
    if observation.telemetry is not None:
        term_reason = observation.telemetry.termination_reason
    elif "termination_reason" in observation.raw_telemetry:
        term_reason = TerminationReason(
            observation.raw_telemetry["termination_reason"]
        )

    facts.append(
        InstrumentalFact(
            fact_id=f"fact-term-{obs_id}",
            observation_id=obs_id,
            fact_type=InstrumentalFactType.PROCESS_TERMINATION_REASON,
            fact_value=term_reason.value,
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="process",
            provenance_detail=f"Termination reason {term_reason.value}",
        )
    )

    is_timeout = term_reason == TerminationReason.TIMEOUT
    facts.append(
        InstrumentalFact(
            fact_id=f"fact-timeout-{obs_id}",
            observation_id=obs_id,
            fact_type=InstrumentalFactType.PROCESS_TIMED_OUT,
            fact_value=str(is_timeout).lower(),
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="process",
            provenance_detail=f"Process timed out: {is_timeout}",
        )
    )

    # 2. Execution timing SLA
    duration_ms = 0.0
    if observation.telemetry is not None:
        duration_ms = observation.telemetry.duration_ms
    elif "duration_ms" in observation.raw_telemetry:
        duration_ms = float(observation.raw_telemetry["duration_ms"])

    facts.append(
        InstrumentalFact(
            fact_id=f"fact-dur-{obs_id}",
            observation_id=obs_id,
            fact_type=InstrumentalFactType.EXECUTION_DURATION_MS,
            fact_value=str(duration_ms),
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="process",
            provenance_detail=f"Wall-clock duration: {duration_ms:.2f} ms",
        )
    )

    # 3. Stream bounds and text snippets
    is_truncated = False
    if observation.telemetry is not None:
        is_truncated = observation.telemetry.output_truncated

    stream_obs = (
        FactObservability.PARTIAL_TRUNCATED
        if is_truncated
        else FactObservability.CONCLUSIVE
    )

    facts.append(
        InstrumentalFact(
            fact_id=f"fact-trunc-{obs_id}",
            observation_id=obs_id,
            fact_type=InstrumentalFactType.STREAM_WAS_TRUNCATED,
            fact_value=str(is_truncated).lower(),
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="streams",
            provenance_detail=f"Output streams truncated: {is_truncated}",
        )
    )

    stdout_text = observation.raw_telemetry.get("stdout", "")
    if stdout_text:
        facts.append(
            InstrumentalFact(
                fact_id=f"fact-stdout-{obs_id}",
                observation_id=obs_id,
                fact_type=InstrumentalFactType.STDOUT_TEXT_SNIPPET,
                fact_value=stdout_text,
                observability=stream_obs,
                inspected_domain="stdout",
                provenance_detail=(
                    f"Captured stdout ({len(stdout_text)} chars, "
                    f"observability={stream_obs.value})"
                ),
            )
        )

    stderr_text = observation.raw_telemetry.get("stderr", "")
    if stderr_text:
        facts.append(
            InstrumentalFact(
                fact_id=f"fact-stderr-{obs_id}",
                observation_id=obs_id,
                fact_type=InstrumentalFactType.STDERR_TEXT_SNIPPET,
                fact_value=stderr_text,
                observability=stream_obs,
                inspected_domain="stderr",
                provenance_detail=(
                    f"Captured stderr ({len(stderr_text)} chars, "
                    f"observability={stream_obs.value})"
                ),
            )
        )

    # 4. Artifact facts
    observed_paths = {
        a.relative_path: a for a in observation.produced_artifacts
    }

    for idx, (path, art) in enumerate(observed_paths.items()):
        facts.append(
            InstrumentalFact(
                fact_id=f"fact-art-pres-{obs_id}-{idx}",
                observation_id=obs_id,
                fact_type=InstrumentalFactType.ARTIFACT_PRESENT,
                fact_value=path,
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="scratch/workspace/",
                provenance_detail=f"Artifact present in workspace: '{path}'",
            )
        )
        facts.append(
            InstrumentalFact(
                fact_id=f"fact-art-size-{obs_id}-{idx}",
                observation_id=obs_id,
                fact_type=InstrumentalFactType.ARTIFACT_SIZE_BYTES,
                fact_value=f"{path}:{art.file_size_bytes}",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="scratch/workspace/",
                provenance_detail=(
                    f"Artifact '{path}' size {art.file_size_bytes} bytes"
                ),
            )
        )
        facts.append(
            InstrumentalFact(
                fact_id=f"fact-art-hash-{obs_id}-{idx}",
                observation_id=obs_id,
                fact_type=InstrumentalFactType.ARTIFACT_SHA256_DIGEST,
                fact_value=f"{path}:{art.sha256_digest}",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="scratch/workspace/",
                provenance_detail=(
                    f"Artifact '{path}' sha256 {art.sha256_digest}"
                ),
            )
        )

    # 5. Cross-reference expected artifact paths
    collection_truncated = False
    omitted_count = 0
    if observation.artifact_summary is not None:
        summary = observation.artifact_summary
        collection_truncated = summary.collection_truncated
        omitted_count = summary.artifacts_omitted

    for req_idx, expected in enumerate(expected_paths):
        if expected not in observed_paths:
            if collection_truncated or omitted_count > 0:
                # Observer limit reached: cannot verify absence
                facts.append(
                    InstrumentalFact(
                        fact_id=f"fact-art-omit-{obs_id}-{req_idx}",
                        observation_id=obs_id,
                        fact_type=(
                            InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT
                        ),
                        fact_value=expected,
                        observability=FactObservability.PARTIAL_TRUNCATED,
                        inspected_domain="scratch/workspace/",
                        provenance_detail=(
                            f"Required artifact '{expected}' was not "
                            f"observed; collection truncated/omitted "
                            f"(omitted={omitted_count})"
                        ),
                    )
                )
            else:
                # Exhaustive scan completed cleanly: verified absence
                facts.append(
                    InstrumentalFact(
                        fact_id=f"fact-art-abs-{obs_id}-{req_idx}",
                        observation_id=obs_id,
                        fact_type=(
                            InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
                        ),
                        fact_value=expected,
                        observability=FactObservability.VERIFIED_ABSENCE,
                        inspected_domain="scratch/workspace/",
                        provenance_detail=(
                            f"Artifact '{expected}' verified absent in "
                            f"scratch/workspace/ after exhaustive scan"
                        ),
                    )
                )

    return tuple(facts)
