"""Sensitivity tests for the independent B1-R artifact verifier."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from scripts.verify_b1r_artifact import main, verify_artifact

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads(
    (Path(__file__).parent / "b1r_contract.json").read_text(encoding="utf-8")
)
EXECUTION_COUNT = (
    len(CONTRACT["expected_cases"]) * CONTRACT["repetitions_per_case"]
)


def _valid_report() -> dict[str, Any]:
    cases = {}
    for case_id, expected in CONTRACT["expected_cases"].items():
        observation = {
            "case_id": case_id,
            "http_status": expected["http_status"],
            "content_type": (
                f'{expected["content_type_prefix"]}; charset=utf-8'
            ),
            "events": expected["events"],
            "last_event": expected["events"][-1],
            "phase_complete_present": expected["phase_complete_present"],
            "stream_closed": expected["stream_closed"],
            "observed_exceptions": expected["observed_exceptions"],
            "forbidden_accesses": [],
        }
        cases[case_id] = [
            deepcopy(observation)
            for _ in range(CONTRACT["repetitions_per_case"])
        ]
    return {
        "schema_version": 1,
        "contract_id": CONTRACT["contract_id"],
        "contract_sha256": hashlib.sha256(
            (Path(__file__).parent / "b1r_contract.json").read_bytes()
        ).hexdigest(),
        "case_count": len(cases),
        "repetitions_per_case": CONTRACT["repetitions_per_case"],
        "cases": cases,
        "guard_probes": {
            probe_id: {
                "rejected": True,
                "category": category,
                "observed_violations": 1,
            }
            for probe_id, category in CONTRACT["required_guard_probes"].items()
        },
        "forbidden_accesses": [],
        "external_calls": [],
        "real_provider_calls": 0,
        "synthetic_backend_resolutions": EXECUTION_COUNT,
        "synthetic_pipeline_constructions": EXECUTION_COUNT,
        "synthetic_context_calls": EXECUTION_COUNT,
        "real_container_constructions": 0,
        "protected_data_accesses": 0,
        "normal_lifespan_runs": 0,
        "thread_starts": 0,
        "route_requests": EXECUTION_COUNT,
        "functional_changes": 0,
        "consumer_observation": CONTRACT["consumer_observation"],
    }


def _write_contract(path: Path) -> None:
    path.write_bytes(
        (Path(__file__).parent / "b1r_contract.json").read_bytes()
    )


def _mutate_case(case_id: str, field: str, value: Any) -> Callable:
    def mutate(report: dict[str, Any]) -> None:
        report["cases"][case_id][0][field] = value

    return mutate


MUTATIONS = [
    pytest.param(
        lambda report: report.update(case_count=report["case_count"] - 1),
        "case_count",
        id="case-count",
    ),
    pytest.param(
        lambda report: report.update(repetitions_per_case=2),
        "repetitions_per_case",
        id="repetitions",
    ),
    pytest.param(
        lambda report: report["cases"]["success"].pop(),
        "exactly 3 runs",
        id="missing-run",
    ),
    pytest.param(
        _mutate_case("success", "events", ["phase_start", "phase_complete"]),
        "event sequence",
        id="missing-event",
    ),
    pytest.param(
        _mutate_case("success", "http_status", 500),
        "http_status",
        id="wrong-status",
    ),
    pytest.param(
        _mutate_case("success", "stream_closed", False),
        "stream_closed",
        id="stream-not-closed",
    ),
    pytest.param(
        _mutate_case("error", "observed_exceptions", []),
        "observed_exceptions",
        id="missing-exception",
    ),
    pytest.param(
        lambda report: report.update(real_container_constructions=1),
        "real_container_constructions",
        id="container-built",
    ),
    pytest.param(
        lambda report: report.update(real_provider_calls=1),
        "real_provider_calls",
        id="provider-called",
    ),
    pytest.param(
        lambda report: report.update(normal_lifespan_runs=1),
        "normal_lifespan_runs",
        id="lifespan-ran",
    ),
    pytest.param(
        lambda report: report.update(forbidden_accesses=["sqlite"]),
        "forbidden_accesses",
        id="forbidden-access",
    ),
    pytest.param(
        lambda report: report["guard_probes"]["sqlite_connection"].update(
            rejected=False
        ),
        "not rejected",
        id="sqlite-guard-ineffective",
    ),
    pytest.param(
        lambda report: report["guard_probes"]["subprocess_creation"].update(
            category="external-call"
        ),
        "category differs",
        id="wrong-guard-category",
    ),
    pytest.param(
        lambda report: report["guard_probes"].pop("project_write"),
        "exactly match",
        id="missing-guard-probe",
    ),
    pytest.param(
        lambda report: report.update(route_requests=EXECUTION_COUNT - 1),
        "route_requests",
        id="route-not-reached",
    ),
    pytest.param(
        lambda report: report.update(functional_changes=1),
        "functional_changes",
        id="functional-change",
    ),
]


def test_contract_accepts_a_complete_synthetic_artifact() -> None:
    assert verify_artifact(CONTRACT, _valid_report()) == []


@pytest.mark.parametrize(("mutation", "finding"), MUTATIONS)
def test_contract_rejects_each_mutated_acceptance_property(
    mutation: Callable[[dict[str, Any]], None],
    finding: str,
) -> None:
    report = _valid_report()
    mutation(report)

    findings = verify_artifact(CONTRACT, report)

    assert any(finding in result for result in findings), findings


def test_verifier_has_no_import_dependency_on_talos_application() -> None:
    verifier_source = (REPO_ROOT / "scripts/verify_b1r_artifact.py").read_text(
        encoding="utf-8"
    )

    assert "study_engine" not in verifier_source
    assert "fastapi" not in verifier_source.lower()


def test_unsupported_evidence_envelope_requires_review(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    contract_path = tmp_path / "contract.json"
    report_path = tmp_path / "report.json"
    report = _valid_report()
    report["schema_version"] = 99
    _write_contract(contract_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(
        ["--contract", str(contract_path), "--report", str(report_path)]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out) == {
        "status": "REVIEW REQUIRED",
        "findings": ["contract or report schema is unsupported or ambiguous"],
    }


def test_contract_hash_mismatch_requires_review(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    contract_path = tmp_path / "contract.json"
    report_path = tmp_path / "report.json"
    report = _valid_report()
    report["contract_sha256"] = "0" * 64
    _write_contract(contract_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(
        ["--contract", str(contract_path), "--report", str(report_path)]
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out) == {
        "status": "REVIEW REQUIRED",
        "findings": ["contract or report schema is unsupported or ambiguous"],
    }


def test_supported_but_failing_evidence_returns_technical_fail(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    contract_path = tmp_path / "contract.json"
    report_path = tmp_path / "report.json"
    report = _valid_report()
    report["cases"]["success"][0]["http_status"] = 500
    _write_contract(contract_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")

    exit_code = main(
        ["--contract", str(contract_path), "--report", str(report_path)]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert result["status"] == "TECHNICAL FAIL"
    assert any("http_status" in finding for finding in result["findings"])
