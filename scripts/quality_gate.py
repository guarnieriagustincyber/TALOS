"""Validate and run the repository's declared test perimeter."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PERIMETER_PATH = REPOSITORY_ROOT / "config" / "test_perimeter.json"
TESTS_ROOT = REPOSITORY_ROOT / "tests"
CLASSIFICATIONS = {"required", "qualification-required", "support-only"}


class PerimeterError(ValueError):
    """Raised when the discovered tests do not match the declared perimeter."""


@dataclass(frozen=True)
class Suite:
    path: str
    classification: str
    reason: str
    modules: tuple[str, ...]


@dataclass(frozen=True)
class Perimeter:
    suites: tuple[Suite, ...]
    optional_modules: dict[str, str]
    module_classifications: dict[str, str]


def _repo_test_path(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise PerimeterError(f"{field} must be a repository-relative path.")
    path = Path(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.parts[0] != "tests"
    ):
        raise PerimeterError(f"Invalid {field} path: {value!r}.")
    return path.as_posix()


def validate_perimeter(repo_root: Path, manifest_path: Path) -> Perimeter:
    """Load the perimeter and reject unclassified discovered tests."""

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}.")
            result[key] = value
        return result

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
        )
    except (OSError, ValueError) as error:
        raise PerimeterError(
            f"Cannot read test perimeter {manifest_path}: {error}"
        ) from error

    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise PerimeterError(
            "Test perimeter must be an object with schema_version 1."
        )

    suite_entries = manifest.get("suites")
    override_entries = manifest.get("module_overrides")
    if not isinstance(suite_entries, list) or not isinstance(
        override_entries, list
    ):
        raise PerimeterError(
            "Test perimeter requires 'suites' and 'module_overrides' lists."
        )

    tests_root = repo_root / "tests"
    discovered_files = sorted(
        path
        for path in tests_root.rglob("test_*.py")
        if not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.parts
        )
    )
    if not discovered_files:
        raise PerimeterError(
            "No test_*.py modules were discovered under tests/."
        )

    discovered_suites: dict[str, list[str]] = defaultdict(list)
    for path in discovered_files:
        relative = path.relative_to(repo_root).as_posix()
        parts = path.relative_to(tests_root).parts
        suite_path = "tests" if len(parts) == 1 else f"tests/{parts[0]}"
        discovered_suites[suite_path].append(relative)

    registered: dict[str, tuple[str, str]] = {}
    for entry in suite_entries:
        if not isinstance(entry, dict):
            raise PerimeterError("Every suite entry must be an object.")
        suite_path = _repo_test_path(entry.get("path"), "suite")
        classification = entry.get("classification")
        reason = entry.get("reason")
        if (
            not isinstance(classification, str)
            or classification not in CLASSIFICATIONS
        ):
            raise PerimeterError(
                f"{suite_path}: classification must be one of "
                f"{', '.join(sorted(CLASSIFICATIONS))}."
            )
        if not isinstance(reason, str) or not reason.strip():
            raise PerimeterError(
                f"{suite_path}: a non-empty classification reason is required."
            )
        if suite_path in registered:
            raise PerimeterError(
                f"Duplicate suite classification: {suite_path}."
            )
        registered[suite_path] = (classification, reason.strip())

    discovered_paths = set(discovered_suites)
    registered_paths = set(registered)
    unknown = sorted(discovered_paths - registered_paths)
    stale = sorted(registered_paths - discovered_paths)
    if unknown or stale:
        details = []
        if unknown:
            details.append(f"unclassified test suites: {', '.join(unknown)}")
        if stale:
            details.append(
                f"registered suites with no test modules: {', '.join(stale)}"
            )
        raise PerimeterError("; ".join(details))

    discovered_module_paths = discovered_files_as_strings(discovered_suites)
    optional_modules: dict[str, str] = {}
    module_classifications = {
        module: registered[suite_path][0]
        for suite_path, modules in discovered_suites.items()
        for module in modules
    }
    for entry in override_entries:
        if not isinstance(entry, dict):
            raise PerimeterError("Every module override must be an object.")
        module_path = _repo_test_path(entry.get("path"), "module override")
        reason = entry.get("reason")
        if entry.get("classification") != "optional":
            raise PerimeterError(
                f"{module_path}: module overrides must be optional."
            )
        if not isinstance(reason, str) or not reason.strip():
            raise PerimeterError(
                f"{module_path}: an optional module requires a reason."
            )
        if module_path not in discovered_module_paths:
            raise PerimeterError(
                f"Optional module is not a discovered test module: "
                f"{module_path}."
            )
        if module_classifications[module_path] != "required":
            raise PerimeterError(
                f"{module_path}: optional module override conflicts with "
                "suite classification "
                f"{module_classifications[module_path]!r}."
            )
        if module_path in optional_modules:
            raise PerimeterError(f"Duplicate module override: {module_path}.")
        optional_modules[module_path] = reason.strip()
        module_classifications[module_path] = "optional"

    if set(module_classifications) != discovered_module_paths:
        raise PerimeterError(
            "Every discovered test module must resolve to exactly one "
            "classification."
        )

    suites = tuple(
        Suite(
            path=path,
            classification=registered[path][0],
            reason=registered[path][1],
            modules=tuple(discovered_suites[path]),
        )
        for path in sorted(registered)
    )
    return Perimeter(
        suites=suites,
        optional_modules=optional_modules,
        module_classifications=module_classifications,
    )


def discovered_files_as_strings(
    discovered_suites: dict[str, list[str]],
) -> set[str]:
    return {
        module for modules in discovered_suites.values() for module in modules
    }


class SuiteResults:
    """Collect pytest outcomes once per item, grouped by registered suite."""

    def __init__(self, suite_paths: list[str]) -> None:
        self.suite_paths = suite_paths
        self.collected: dict[str, int] = defaultdict(int)
        self.outcomes: dict[str, dict[str, str]] = defaultdict(dict)
        self.collection_failures: dict[str, int] = defaultdict(int)

    def suite_for_nodeid(self, nodeid: str) -> str:
        module_path = nodeid.split("::", 1)[0]
        if not module_path.startswith("tests/"):
            module_path = f"tests/{module_path}"
        for suite_path in self.suite_paths:
            if module_path == suite_path or module_path.startswith(
                f"{suite_path}/"
            ):
                return suite_path
        return "unclassified"

    def pytest_collection_finish(self, session: Any) -> None:
        for item in session.items:
            self.collected[self.suite_for_nodeid(item.nodeid)] += 1

    def pytest_runtest_logreport(self, report: Any) -> None:
        suite_path = self.suite_for_nodeid(report.nodeid)
        if report.when == "call":
            self.outcomes[suite_path][report.nodeid] = report.outcome
        elif report.failed:
            self.outcomes[suite_path][report.nodeid] = "failed"
        elif report.skipped and report.nodeid not in self.outcomes[suite_path]:
            self.outcomes[suite_path][report.nodeid] = "skipped"

    def pytest_collectreport(self, report: Any) -> None:
        if report.failed:
            suite_path = self.suite_for_nodeid(report.nodeid)
            self.collection_failures[suite_path] += 1

    def counts(self, suite_path: str) -> dict[str, int]:
        outcomes = self.outcomes[suite_path].values()
        return {
            "collected": self.collected[suite_path],
            "passed": sum(outcome == "passed" for outcome in outcomes),
            "failed": sum(outcome == "failed" for outcome in outcomes)
            + self.collection_failures[suite_path],
            "skipped": sum(outcome == "skipped" for outcome in outcomes),
        }


def run_gate(profile: str, perimeter: Perimeter) -> int:
    import pytest

    active_suites = [
        suite
        for suite in perimeter.suites
        if suite.classification == "required"
        or (
            profile == "release"
            and suite.classification == "qualification-required"
        )
    ]
    suite_paths = [suite.path for suite in active_suites]
    selected_paths = [
        (
            f"{suite.path}/"
            if (REPOSITORY_ROOT / suite.path).is_dir()
            else suite.path
        )
        for suite in active_suites
    ]
    pytest_args = ["-q", *selected_paths]
    for module_path in sorted(perimeter.optional_modules):
        pytest_args.extend(["--ignore", module_path])

    results = SuiteResults(suite_paths)
    previous_directory = Path.cwd()
    os.chdir(REPOSITORY_ROOT)
    try:
        exit_code = pytest.main(pytest_args, plugins=[results])
    finally:
        os.chdir(previous_directory)

    print("\n" + "=" * 72)
    print(f"TEST PERIMETER REPORT — PROFILE: {profile.upper()}")
    print("=" * 72)
    all_passed = exit_code == pytest.ExitCode.OK
    for suite in perimeter.suites:
        if suite not in active_suites:
            if suite.classification == "support-only":
                print(f"{suite.path:<28} SUPPORT ONLY: {suite.reason}")
            else:
                print(
                    f"{suite.path:<28} NOT RUN "
                    "(qualification-required; run release profile)"
                )
            continue
        counts = results.counts(suite.path)
        status = (
            "PASS"
            if counts["failed"] == 0 and counts["collected"] > 0
            else "FAIL"
        )
        print(
            f"{suite.path:<28} {status:<4} "
            f"tests={counts['collected']} passed={counts['passed']} "
            f"skipped={counts['skipped']} failed={counts['failed']}"
        )
        all_passed = all_passed and status == "PASS"

    for module_path, reason in sorted(perimeter.optional_modules.items()):
        print(f"{module_path:<52} NOT RUN (optional): {reason}")

    print("=" * 72)
    if all_passed:
        print(
            "RESULT: TEST GATE PASS — this is test evidence, not by itself "
            "a release certification."
        )
        return 0
    print("RESULT: TEST GATE FAIL — release qualification is not established.")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("required", "release"),
        default="required",
        help=(
            "required runs deterministic suites; release also runs "
            "controlled qualification suites"
        ),
    )
    args = parser.parse_args(argv)

    sys.path[:0] = [
        str(REPOSITORY_ROOT),
        str(REPOSITORY_ROOT / "src"),
    ]
    try:
        perimeter = validate_perimeter(REPOSITORY_ROOT, PERIMETER_PATH)
    except PerimeterError as error:
        print(f"TEST PERIMETER ERROR: {error}", file=sys.stderr)
        return 2

    from study_engine.contracts.trust_root import verify_manifest_trust_root

    try:
        verify_manifest_trust_root(TESTS_ROOT / "protected" / "manifest.json")
    except Exception as error:
        print(
            "CRITICAL SECURITY BREACH: trust root verification failed: "
            f"{error}",
            file=sys.stderr,
        )
        return 1

    module_count = sum(len(suite.modules) for suite in perimeter.suites)
    print(
        f"Validated {module_count} test_*.py files across "
        f"{len(perimeter.suites)} suites, including "
        "support-only helpers."
    )
    print("Protected manifest trust root: OK.")
    return run_gate(args.profile, perimeter)


if __name__ == "__main__":
    sys.exit(main())
