"""Validate and run the repository's declared test perimeter."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
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
            for part in path.relative_to(tests_root).parts
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
        self.durations: dict[str, float] = defaultdict(float)
        self.skip_reasons: dict[str, list[str]] = defaultdict(list)
        self.errors: dict[str, list[str]] = defaultdict(list)
        self.warnings: dict[str, list[str]] = defaultdict(list)
        self.global_warnings: list[str] = []

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
        self.durations[suite_path] += float(report.duration)
        if report.when == "call":
            self.outcomes[suite_path][report.nodeid] = report.outcome
        elif report.failed:
            self.outcomes[suite_path][report.nodeid] = "failed"
        elif report.skipped and report.nodeid not in self.outcomes[suite_path]:
            self.outcomes[suite_path][report.nodeid] = "skipped"
        if report.skipped:
            reason = str(report.longrepr)
            if reason not in self.skip_reasons[suite_path]:
                self.skip_reasons[suite_path].append(reason)
        elif report.failed:
            error = str(report.longrepr)
            if error not in self.errors[suite_path]:
                self.errors[suite_path].append(error)

    def pytest_collectreport(self, report: Any) -> None:
        if report.failed:
            suite_path = self.suite_for_nodeid(report.nodeid)
            self.collection_failures[suite_path] += 1
            self.errors[suite_path].append(str(report.longrepr))

    def pytest_warning_recorded(
        self,
        warning_message: Warning,
        when: str,
        nodeid: str,
        location: tuple[str, int, str] | None,
    ) -> None:
        del when, location
        message = str(warning_message.message)
        if nodeid:
            suite_path = self.suite_for_nodeid(nodeid)
            if message not in self.warnings[suite_path]:
                self.warnings[suite_path].append(message)
        elif message not in self.global_warnings:
            self.global_warnings.append(message)

    def counts(self, suite_path: str) -> dict[str, int]:
        outcomes = self.outcomes[suite_path].values()
        return {
            "collected": self.collected[suite_path],
            "passed": sum(outcome == "passed" for outcome in outcomes),
            "failed": sum(outcome == "failed" for outcome in outcomes),
            "skipped": sum(outcome == "skipped" for outcome in outcomes),
            "collection_errors": self.collection_failures[suite_path],
        }

    def collector_payload(
        self,
        perimeter: Perimeter,
        profile: str,
        exit_code: int,
    ) -> dict[str, Any]:
        suite_rows = []
        totals = {
            "collected": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "collection_errors": 0,
        }
        for suite in perimeter.suites:
            if suite.classification == "support-only":
                suite_rows.append(
                    {
                        "path": suite.path,
                        "classification": suite.classification,
                        "status": "SKIP",
                        "collected": 0,
                        "passed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "collection_errors": 0,
                        "skip_reasons": [suite.reason],
                        "duration_seconds": 0.0,
                        "warnings": [],
                        "errors": [],
                    }
                )
                continue

            counts = self.counts(suite.path)
            active = suite.classification == "required" or (
                profile == "release"
                and suite.classification == "qualification-required"
            )
            if not active:
                status = "SKIP"
                skip_reasons = ["excluded by selected profile"]
                errors = []
            elif counts["collection_errors"]:
                status = "ERROR"
                skip_reasons = self.skip_reasons[suite.path]
                errors = self.errors[suite.path]
            elif counts["failed"]:
                status = "FAIL"
                skip_reasons = self.skip_reasons[suite.path]
                errors = self.errors[suite.path]
            elif counts["collected"] == 0:
                status = "ERROR"
                skip_reasons = self.skip_reasons[suite.path]
                errors = ["active suite collected no tests"]
            elif counts["skipped"]:
                status = "FAIL"
                skip_reasons = self.skip_reasons[suite.path]
                errors = ["active suite contains skipped tests"]
            else:
                status = "PASS"
                skip_reasons = self.skip_reasons[suite.path]
                errors = []

            suite_rows.append(
                {
                    "path": suite.path,
                    "classification": suite.classification,
                    "status": status,
                    **counts,
                    "skip_reasons": skip_reasons,
                    "duration_seconds": self.durations[suite.path],
                    "warnings": self.warnings[suite.path],
                    "errors": errors,
                }
            )
            if active:
                for field, count in counts.items():
                    totals[field] += count

        return {
            "schema_version": 1,
            "profile": profile,
            "pytest_exit_code": int(exit_code),
            "collections": totals,
            "suites": suite_rows,
            "optional_modules": [
                {
                    "path": path,
                    "status": "SKIP",
                    "reason": reason,
                }
                for path, reason in sorted(perimeter.optional_modules.items())
            ],
            "warnings": self.global_warnings
            + [
                warning
                for suite_warnings in self.warnings.values()
                for warning in suite_warnings
                if warning not in self.global_warnings
            ],
        }

    def write_collector(
        self, output_path: Path, payload: dict[str, Any]
    ) -> None:
        output = output_path.resolve()
        if output.is_relative_to(REPOSITORY_ROOT.resolve()):
            raise ValueError("collector output must be outside the repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(encoded + "\n")
            stream.flush()
        try:
            temporary_path.replace(output)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def run_gate(
    profile: str,
    perimeter: Perimeter,
    *,
    effects_output: Path | None = None,
    scratch_root: Path | None = None,
    collector_output: Path | None = None,
) -> int:
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
    plugins: list[Any] = [results]
    observer = None
    if (
        collector_output is not None
        and collector_output.resolve().is_relative_to(
            REPOSITORY_ROOT.resolve()
        )
    ):
        raise ValueError("collector output must be outside the repository")
    if effects_output is not None:
        if scratch_root is None:
            raise ValueError(
                "an explicit external scratch root is required for "
                "effects observation"
            )
        if effects_output.resolve().is_relative_to(REPOSITORY_ROOT.resolve()):
            raise ValueError("effects output must be outside the repository")
        from scripts.apre_effects import EffectObserver

        observer = EffectObserver(REPOSITORY_ROOT, scratch_root)
        observer.install()
        plugins.append(observer)

    previous_directory = Path.cwd()
    os.chdir(REPOSITORY_ROOT)
    exit_code = pytest.ExitCode.INTERNAL_ERROR
    try:
        exit_code = pytest.main(pytest_args, plugins=plugins)
    finally:
        os.chdir(previous_directory)
        if observer is not None:
            observer.close()
            observer.write_report(effects_output)
        if collector_output is not None:
            results.write_collector(
                collector_output,
                results.collector_payload(perimeter, profile, int(exit_code)),
            )

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
            if counts["failed"] == 0
            and counts["collection_errors"] == 0
            and counts["skipped"] == 0
            and counts["collected"] > 0
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
    parser.add_argument(
        "--apre-effects-output",
        type=Path,
        help=(
            "write Python audit-hook events to an external JSON artifact; "
            "this is not complete syscall or sterility proof"
        ),
    )
    parser.add_argument(
        "--apre-scratch-root",
        type=Path,
        help="existing writable temporary directory outside the repository",
    )
    parser.add_argument(
        "--apre-collector-output",
        type=Path,
        help="write collected per-suite results to an external JSON artifact",
    )
    args = parser.parse_args(argv)
    environment_options = {
        "apre_effects_output": "TALOS_APRE_EFFECTS_OUTPUT",
        "apre_scratch_root": "TALOS_APRE_SCRATCH_ROOT",
        "apre_collector_output": "TALOS_APRE_COLLECTOR_OUTPUT",
    }
    for argument, variable in environment_options.items():
        environment_value = os.environ.get(variable)
        if environment_value is None:
            continue
        if not environment_value.strip():
            parser.error(f"{variable} must not be empty")
        environment_path = Path(environment_value)
        argument_path = getattr(args, argument)
        if argument_path is not None and argument_path.resolve() != (
            environment_path.resolve()
        ):
            parser.error(
                f"--{argument.replace('_', '-')} conflicts with {variable}"
            )
        setattr(args, argument, argument_path or environment_path)

    if (args.apre_effects_output is None) != (args.apre_scratch_root is None):
        parser.error(
            "--apre-effects-output and --apre-scratch-root must be "
            "used together"
        )
    if args.apre_collector_output is not None and (
        args.apre_effects_output is None
    ):
        parser.error("--apre-collector-output requires effects observation")
    if args.apre_effects_output is not None and args.profile != "release":
        parser.error(
            "A-PRE observation is defined only for the release profile"
        )

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
    return run_gate(
        args.profile,
        perimeter,
        effects_output=args.apre_effects_output,
        scratch_root=args.apre_scratch_root,
        collector_output=args.apre_collector_output,
    )


if __name__ == "__main__":
    sys.exit(main())
