"""Acceptance tests for structured A-PRE result emission and verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.apre_result import EMPTY_SHA256, sha256_file, write_result
from scripts.verify_apre_result import (
    main as verify_main,
    verify_artifact,
)


def _fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    repository = tmp_path / "repository"
    evidence = tmp_path / "evidence"
    repository.mkdir()
    evidence.mkdir()
    suite_paths = (
        ("tests/unit", "required"),
        ("tests/performance", "qualification-required"),
        ("tests/utils", "support-only"),
    )
    manifest = {
        "schema_version": 1,
        "suites": [
            {"path": path, "classification": classification}
            for path, classification in suite_paths
        ],
        "module_overrides": [
            {
                "path": "tests/unit/test_live.py",
                "reason": "fixture-only optional case",
            }
        ],
    }
    input_paths = {
        "pyproject.toml": "project manifest fixture",
        "requirements.lock": "lock fixture",
        "config/test_perimeter.json": json.dumps(manifest),
        "scripts/quality_gate.py": "quality gate fixture",
        "scripts/apre_effects.py": "effects observer fixture",
        "scripts/apre_harness.py": "harness fixture",
        "scripts/apre_result.py": "result code fixture",
        "scripts/verify_apre_result.py": "verifier code fixture",
    }
    for relative, content in input_paths.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    output = evidence / "stdout.txt"
    output.write_text("synthetic pytest transcript\n", encoding="utf-8")
    errors_output = evidence / "stderr.txt"
    errors_output.write_text("", encoding="utf-8")
    report = {
        "schema_version": 1,
        "run_id": "preflight-fixture-001",
        "global_status": "PASS",
        "started_at": "2026-09-30T15:00:00Z",
        "duration_seconds": 1.25,
        "identity": {
            "repository": "example/TALOS",
            "branch": "fixture",
            "commit": "a" * 40,
            "working_tree_clean": True,
            "working_tree_diff_sha256": EMPTY_SHA256,
            "platform": "Linux/x86_64/test",
        },
        "runtime": {
            "python_executable": "/tmp/pre-venv/bin/python",
            "python_version": "3.10.21",
            "uv_version": "0.12.20",
            "input_hashes": {
                relative: hashlib.sha256(content.encode("utf-8")).hexdigest()
                for relative, content in input_paths.items()
            },
        },
        "command": [
            "/tmp/pre-venv/bin/python",
            "scripts/quality_gate.py",
            "--profile",
            "release",
        ],
        "profile": "release",
        "exit_code": 0,
        "collections": {
            "collected": 2,
            "passed": 1,
            "failed": 0,
            "skipped": 1,
            "collection_errors": 0,
        },
        "suites": [
            {
                "path": "tests/unit",
                "classification": "required",
                "status": "PASS",
                "collected": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
                "collection_errors": 0,
                "skip_reasons": [],
                "duration_seconds": 0.5,
                "warnings": [],
                "errors": [],
            },
            {
                "path": "tests/performance",
                "classification": "qualification-required",
                "status": "WARNING",
                "collected": 1,
                "passed": 0,
                "failed": 0,
                "skipped": 1,
                "collection_errors": 0,
                "skip_reasons": ["fixture skips a hardware qualification"],
                "duration_seconds": 0.5,
                "warnings": ["one justified skip"],
                "errors": [],
            },
            {
                "path": "tests/utils",
                "classification": "support-only",
                "status": "SKIP",
                "collected": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "collection_errors": 0,
                "skip_reasons": ["support-only helper directory"],
                "duration_seconds": 0,
                "warnings": [],
                "errors": [],
            },
        ],
        "optional_modules": [
            {
                "path": "tests/unit/test_live.py",
                "status": "SKIP",
                "reason": "fixture-only optional case",
            }
        ],
        "artifacts": [
            {
                "path": "stdout.txt",
                "sha256": sha256_file(output),
            },
            {
                "path": "stderr.txt",
                "sha256": sha256_file(errors_output),
            },
        ],
        "sterility": {
            "before_state_sha256": "b" * 64,
            "after_state_sha256": "b" * 64,
            "unexpected_changes": [],
        },
        "warnings": ["one justified skip"],
        "errors": [],
    }
    return report, manifest, repository, evidence


def _mark_warning_failed(report: dict[str, Any]) -> None:
    report["suites"][1]["failed"] = 1
    report["collections"].update(passed=0, failed=1)


def test_writer_emits_validated_artifact_inside_evidence_root(
    tmp_path: Path,
) -> None:
    report, manifest, repository, evidence = _fixture(tmp_path)
    output = evidence / "result.json"

    write_result(
        report,
        manifest,
        repository_root=repository,
        evidence_root=evidence,
        output_path=output,
    )

    assert json.loads(output.read_text(encoding="utf-8")) == report


@pytest.mark.parametrize(
    ("mutation", "finding"),
    [
        (
            lambda report: report["identity"].update(working_tree_clean=False),
            "working_tree_clean must be true",
        ),
        (
            lambda report: report["collections"].update(passed=2),
            "collections.passed does not match suite totals",
        ),
        (
            lambda report: report["suites"][0].update(status="SKIP"),
            "executable suite cannot be wholly SKIP",
        ),
        (
            lambda report: report["suites"][2].update(skip_reasons=[]),
            "support-only suite must be SKIP",
        ),
        (
            _mark_warning_failed,
            "WARNING requires no failures",
        ),
        (
            lambda report: report["artifacts"][0].update(sha256="0" * 64),
            "artifact hash mismatch",
        ),
        (
            lambda report: report["artifacts"][0].update(
                path="../outside.txt"
            ),
            "artifact path must be unique and relative",
        ),
        (
            lambda report: report["runtime"]["input_hashes"].update(
                **{"requirements.lock": "0" * 64}
            ),
            "input hash mismatch: requirements.lock",
        ),
    ],
)
def test_writer_rejects_inconsistent_or_modified_evidence(
    tmp_path: Path,
    mutation: Any,
    finding: str,
) -> None:
    report, manifest, repository, evidence = _fixture(tmp_path)
    mutation(report)

    with pytest.raises(ValueError, match=finding):
        write_result(
            report,
            manifest,
            repository_root=repository,
            evidence_root=evidence,
            output_path=evidence / "invalid.json",
        )
    assert verify_artifact(
        report,
        manifest,
        repository_root=repository,
        evidence_root=evidence,
    )


def test_writer_refuses_output_outside_evidence_directory(
    tmp_path: Path,
) -> None:
    report, manifest, repository, evidence = _fixture(tmp_path)

    with pytest.raises(ValueError, match="inside the evidence directory"):
        write_result(
            report,
            manifest,
            repository_root=repository,
            evidence_root=evidence,
            output_path=tmp_path / "outside.json",
        )


def test_independent_verifier_cli_accepts_fixture_and_detects_tampering(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report, manifest, repository, evidence = _fixture(tmp_path)
    report_path = evidence / "result.json"
    manifest_path = repository / "config/test_perimeter.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    write_result(
        report,
        manifest,
        repository_root=repository,
        evidence_root=evidence,
        output_path=report_path,
    )
    args = [
        "--report",
        str(report_path),
        "--manifest",
        str(manifest_path),
        "--repository-root",
        str(repository),
        "--evidence-root",
        str(evidence),
    ]

    assert verify_main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"

    report["identity"]["working_tree_clean"] = False
    report_path.write_text(json.dumps(report), encoding="utf-8")
    assert verify_main(args) == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["status"] == "FAIL"
    assert any(
        "working_tree_clean" in finding for finding in failed["findings"]
    )


@pytest.mark.parametrize(
    ("content", "expected_code", "expected_status"),
    [
        ("{", 2, "REVIEW REQUIRED"),
        ("{}", 1, "FAIL"),
    ],
)
def test_verifier_cli_rejects_corrupt_or_incomplete_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    content: str,
    expected_code: int,
    expected_status: str,
) -> None:
    _, manifest, repository, evidence = _fixture(tmp_path)
    report_path = evidence / "result.json"
    report_path.write_text(content, encoding="utf-8")
    manifest_path = repository / "config/test_perimeter.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    args = [
        "--report",
        str(report_path),
        "--manifest",
        str(manifest_path),
        "--repository-root",
        str(repository),
        "--evidence-root",
        str(evidence),
    ]

    assert verify_main(args) == expected_code
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == expected_status
    assert result["findings"]


def test_dirty_checkout_can_only_be_recorded_as_error(
    tmp_path: Path,
) -> None:
    report, manifest, repository, evidence = _fixture(tmp_path)
    report["global_status"] = "ERROR"
    report["exit_code"] = 2
    report["identity"]["working_tree_clean"] = False
    report["errors"] = ["working tree was not clean before execution"]

    write_result(
        report,
        manifest,
        repository_root=repository,
        evidence_root=evidence,
        output_path=evidence / "error.json",
    )
