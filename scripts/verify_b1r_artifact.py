"""Independent verifier for a B1-R synthetic route evidence artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def verify_artifact(
    contract: dict[str, Any],
    report: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    expected_cases = contract.get("expected_cases")
    if not isinstance(expected_cases, dict) or not expected_cases:
        return ["contract.expected_cases must be a non-empty object"]

    case_ids = set(expected_cases)
    expected_repetitions = contract.get("repetitions_per_case")
    expected_contract_id = contract.get("contract_id")

    if report.get("schema_version") != 1:
        findings.append("report.schema_version must equal 1")
    if report.get("contract_id") != expected_contract_id:
        findings.append("report.contract_id does not match the contract")
    if report.get("case_count") != len(case_ids):
        findings.append("report.case_count does not match expected cases")
    if report.get("repetitions_per_case") != expected_repetitions:
        findings.append("report.repetitions_per_case does not match contract")
    if report.get("consumer_observation") != contract.get(
        "consumer_observation"
    ):
        findings.append("consumer observation is not the declared boundary")

    cases = report.get("cases")
    if not isinstance(cases, dict):
        findings.append("report.cases must be an object")
        cases = {}
    if set(cases) != case_ids:
        findings.append("report case IDs do not exactly match the contract")

    if isinstance(expected_repetitions, int):
        for case_id, expected in expected_cases.items():
            observations = cases.get(case_id)
            if not isinstance(observations, list):
                findings.append(f"{case_id}: observations must be a list")
                continue
            if len(observations) != expected_repetitions:
                findings.append(
                    f"{case_id}: expected exactly {expected_repetitions} runs"
                )
                continue
            normalized_runs = []
            for index, observation in enumerate(observations):
                if not isinstance(observation, dict):
                    findings.append(
                        f"{case_id}[{index}]: observation must be an object"
                    )
                    continue
                normalized = {
                    "case_id": observation.get("case_id"),
                    "http_status": observation.get("http_status"),
                    "content_type": observation.get("content_type"),
                    "events": observation.get("events"),
                    "last_event": observation.get("last_event"),
                    "phase_complete_present": observation.get(
                        "phase_complete_present"
                    ),
                    "stream_closed": observation.get("stream_closed"),
                    "observed_exceptions": observation.get(
                        "observed_exceptions"
                    ),
                }
                normalized_runs.append(normalized)
                for field in (
                    "http_status",
                    "stream_closed",
                    "phase_complete_present",
                    "observed_exceptions",
                ):
                    if observation.get(field) != expected.get(field):
                        findings.append(
                            f"{case_id}[{index}]: {field} "
                            "differs from contract"
                        )
                content_type = observation.get("content_type")
                if not (
                    isinstance(content_type, str)
                    and content_type.startswith(
                        expected.get("content_type_prefix", "")
                    )
                ):
                    findings.append(
                        f"{case_id}[{index}]: content_type "
                        "differs from contract"
                    )
                if observation.get("events") != expected.get("events"):
                    findings.append(
                        f"{case_id}[{index}]: event sequence "
                        "differs from contract"
                    )
                events = observation.get("events")
                expected_last = (
                    events[-1] if isinstance(events, list) and events else None
                )
                if observation.get("last_event") != expected_last:
                    findings.append(
                        f"{case_id}[{index}]: last_event differs from events"
                    )
                if observation.get("case_id") != case_id:
                    findings.append(
                        f"{case_id}[{index}]: case_id does not match case key"
                    )
                if observation.get("forbidden_accesses") != []:
                    findings.append(
                        f"{case_id}[{index}]: forbidden accesses were recorded"
                    )
            if normalized_runs and any(
                run != normalized_runs[0] for run in normalized_runs[1:]
            ):
                findings.append(
                    f"{case_id}: normalized observations are not repeatable"
                )

    required_probes = contract.get("required_guard_probes", {})
    probes = report.get("guard_probes")
    if not isinstance(probes, dict):
        findings.append("report.guard_probes must be an object")
        probes = {}
    if set(probes) != set(required_probes):
        findings.append("guard probe IDs do not exactly match the contract")
    for probe_id, expected_category in required_probes.items():
        actual = probes.get(probe_id)
        if not isinstance(actual, dict):
            findings.append(f"{probe_id}: guard probe result is missing")
            continue
        if actual.get("rejected") is not True:
            findings.append(
                f"{probe_id}: prohibited operation was not rejected"
            )
        if actual.get("category") != expected_category:
            findings.append(f"{probe_id}: rejection category differs")
        if actual.get("observed_violations") != 1:
            findings.append(
                f"{probe_id}: expected exactly one rejected operation"
            )

    for field in ("forbidden_accesses", "external_calls"):
        if report.get(field) != []:
            findings.append(f"{field} must be empty")
    for field in contract.get("required_zero_counters", []):
        if report.get(field) != 0:
            findings.append(f"{field} must equal 0")

    execution_count = len(case_ids) * expected_repetitions
    expected_counts = contract.get("expected_counts_per_execution", [])
    for field in expected_counts:
        expected_value = execution_count
        if report.get(field) != expected_value:
            findings.append(f"{field} must equal {expected_value}")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        contract_bytes = args.contract.read_bytes()
        contract = json.loads(contract_bytes)
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"status": "REVIEW REQUIRED", "findings": [str(exc)]},
                sort_keys=True,
            )
        )
        return 2

    if not isinstance(contract, dict) or not isinstance(report, dict):
        findings = ["contract and report roots must be JSON objects"]
        status = "REVIEW REQUIRED"
        exit_code = 2
    elif not _supported_envelope(
        contract,
        report,
        hashlib.sha256(contract_bytes).hexdigest(),
    ):
        findings = ["contract or report schema is unsupported or ambiguous"]
        status = "REVIEW REQUIRED"
        exit_code = 2
    else:
        findings = verify_artifact(contract, report)
        status = "TECHNICAL PASS" if not findings else "TECHNICAL FAIL"
        exit_code = 0 if not findings else 1
    print(json.dumps({"status": status, "findings": findings}, sort_keys=True))
    return exit_code


def _supported_envelope(
    contract: dict[str, Any],
    report: dict[str, Any],
    contract_sha256: str,
) -> bool:
    expected_cases = contract.get("expected_cases")
    required_probes = contract.get("required_guard_probes")
    repetitions = contract.get("repetitions_per_case")
    return (
        contract.get("schema_version") == 1
        and contract.get("contract_id") == report.get("contract_id")
        and report.get("contract_sha256") == contract_sha256
        and isinstance(contract.get("contract_id"), str)
        and isinstance(repetitions, int)
        and not isinstance(repetitions, bool)
        and repetitions > 0
        and isinstance(expected_cases, dict)
        and bool(expected_cases)
        and all(
            isinstance(case_id, str) and _supported_case_contract(expected)
            for case_id, expected in expected_cases.items()
        )
        and isinstance(required_probes, dict)
        and bool(required_probes)
        and all(
            isinstance(probe_id, str) and isinstance(category, str)
            for probe_id, category in required_probes.items()
        )
        and isinstance(contract.get("consumer_observation"), str)
        and isinstance(contract.get("required_zero_counters"), list)
        and all(
            isinstance(field, str)
            for field in contract["required_zero_counters"]
        )
        and isinstance(contract.get("expected_counts_per_execution"), list)
        and all(
            isinstance(field, str)
            for field in contract["expected_counts_per_execution"]
        )
        and report.get("schema_version") == 1
    )


def _supported_case_contract(expected: Any) -> bool:
    if not isinstance(expected, dict):
        return False
    events = expected.get("events")
    exceptions = expected.get("observed_exceptions")
    status = expected.get("http_status")
    return (
        isinstance(events, list)
        and bool(events)
        and all(isinstance(event, str) for event in events)
        and isinstance(status, int)
        and not isinstance(status, bool)
        and isinstance(expected.get("content_type_prefix"), str)
        and bool(expected["content_type_prefix"])
        and isinstance(expected.get("stream_closed"), bool)
        and isinstance(expected.get("phase_complete_present"), bool)
        and isinstance(exceptions, list)
        and all(isinstance(exception, str) for exception in exceptions)
    )


if __name__ == "__main__":
    sys.exit(main())
