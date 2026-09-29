import json
from pathlib import Path

import pytest

import scripts.quality_gate as quality_gate
from scripts.quality_gate import PerimeterError, validate_perimeter


def test_repository_test_perimeter_matches_discovered_suites() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    perimeter = validate_perimeter(
        repo_root,
        repo_root / "config" / "test_perimeter.json",
    )

    assert len(perimeter.suites) == 24
    discovered_modules = {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "tests").rglob("test_*.py")
    }
    assert set(perimeter.module_classifications) == discovered_modules
    assert len(perimeter.module_classifications) == len(discovered_modules)
    assert set(perimeter.module_classifications.values()) == {
        "required",
        "qualification-required",
        "optional",
        "support-only",
    }
    assert (
        perimeter.module_classifications[
            "tests/integration/test_llm_latency.py"
        ]
        == "optional"
    )
    assert (
        perimeter.module_classifications[
            "tests/performance/test_budget_ceiling.py"
        ]
        == "qualification-required"
    )
    assert (
        perimeter.module_classifications["tests/utils/test_registry.py"]
        == "support-only"
    )
    assert perimeter.optional_modules == {
        "tests/integration/test_llm_latency.py": (
            "Requires live network access; run separately with a recorded "
            "provider, credentials, and network configuration."
        ),
        "tests/integration/test_study_loop_real_llm.py": (
            "Requires KASIU_LIVE_TESTS=1 and GEMINI_API_KEY; run separately "
            "as a "
            "live-model evaluation."
        ),
    }


def test_unclassified_test_suite_is_rejected(tmp_path: Path) -> None:
    tests_root = tmp_path / "tests"
    (tests_root / "unit").mkdir(parents=True)
    (tests_root / "unit" / "test_known.py").write_text("", encoding="utf-8")
    (tests_root / "new_area").mkdir()
    (tests_root / "new_area" / "test_unclassified.py").write_text(
        "", encoding="utf-8"
    )
    manifest_path = tmp_path / "perimeter.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suites": [
                    {
                        "path": "tests/unit",
                        "classification": "required",
                        "reason": "Known deterministic unit tests.",
                    }
                ],
                "module_overrides": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PerimeterError, match="unclassified test suites: tests/new_area"
    ):
        validate_perimeter(tmp_path, manifest_path)


def test_gate_fails_closed_before_pytest_for_new_suite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tests_root = tmp_path / "tests"
    (tests_root / "unit").mkdir(parents=True)
    (tests_root / "unit" / "test_known.py").write_text("", encoding="utf-8")
    (tests_root / "security_new").mkdir()
    (tests_root / "security_new" / "test_unclassified.py").write_text(
        "", encoding="utf-8"
    )
    manifest_path = tmp_path / "perimeter.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suites": [
                    {
                        "path": "tests/unit",
                        "classification": "required",
                        "reason": "Known deterministic unit tests.",
                    }
                ],
                "module_overrides": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(quality_gate, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(quality_gate, "PERIMETER_PATH", manifest_path)

    assert quality_gate.main(["--profile", "release"]) == 2
    assert (
        "unclassified test suites: tests/security_new"
        in capsys.readouterr().err
    )


def test_optional_module_requires_a_reason(tmp_path: Path) -> None:
    tests_root = tmp_path / "tests" / "integration"
    tests_root.mkdir(parents=True)
    (tests_root / "test_external.py").write_text("", encoding="utf-8")
    manifest_path = tmp_path / "perimeter.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suites": [
                    {
                        "path": "tests/integration",
                        "classification": "required",
                        "reason": "Hermetic integration tests.",
                    }
                ],
                "module_overrides": [
                    {
                        "path": "tests/integration/test_external.py",
                        "classification": "optional",
                        "reason": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PerimeterError, match="optional module requires a reason"
    ):
        validate_perimeter(tmp_path, manifest_path)


def test_optional_override_cannot_conflict_with_suite_classification(
    tmp_path: Path,
) -> None:
    tests_root = tmp_path / "tests" / "performance"
    tests_root.mkdir(parents=True)
    (tests_root / "test_budget.py").write_text("", encoding="utf-8")
    manifest_path = tmp_path / "perimeter.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suites": [
                    {
                        "path": "tests/performance",
                        "classification": "qualification-required",
                        "reason": "Controlled resource qualification.",
                    }
                ],
                "module_overrides": [
                    {
                        "path": "tests/performance/test_budget.py",
                        "classification": "optional",
                        "reason": "External resource is unavailable.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PerimeterError,
        match="optional module override conflicts with suite classification",
    ):
        validate_perimeter(tmp_path, manifest_path)


def test_duplicate_manifest_keys_are_rejected(tmp_path: Path) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    manifest_path = tmp_path / "perimeter.json"
    manifest_path.write_text(
        '{"schema_version": 1, "schema_version": 1, '
        '"suites": [], "module_overrides": []}',
        encoding="utf-8",
    )

    with pytest.raises(PerimeterError, match="Duplicate JSON key"):
        validate_perimeter(tmp_path, manifest_path)
