"""Synthetic-only qualification tests for A-PRE's Python audit observer."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from scripts.apre_effects import EffectObserver
from scripts.quality_gate import Perimeter, Suite, run_gate


def _observer(tmp_path: Path) -> tuple[EffectObserver, Path, Path]:
    repository = tmp_path / "repository"
    scratch = tmp_path / "scratch"
    repository.mkdir()
    scratch.mkdir()
    return EffectObserver(repository, scratch), repository, scratch


def test_observer_classifies_scratch_repository_and_external_paths(
    tmp_path: Path,
) -> None:
    observer, repository, scratch = _observer(tmp_path)
    observer.set_case("synthetic::paths")

    temporary = observer.observe("open", (str(scratch / "file.txt"), "w", 0))
    repository_read = observer.observe(
        "open", (str(repository / "input.txt"), "r", 0)
    )
    external_read = observer.observe(
        "open", (str(tmp_path / "outside.txt"), "r", 0)
    )

    assert temporary is not None
    assert temporary["classification"] == "TEMPORARY"
    assert temporary["case_id"] == "synthetic::paths"
    assert repository_read is not None
    assert repository_read["classification"] == "NONE"
    assert external_read is not None
    assert external_read["classification"] == "REAL"


def test_observer_marks_uninterpretable_events_unknown_and_never_complete(
    tmp_path: Path,
) -> None:
    observer, _, _ = _observer(tmp_path)
    event = observer.observe("open", (object(), None, None))

    assert event is not None
    assert event["classification"] == "UNKNOWN"
    report = observer.report()
    assert report["coverage"]["python_audit_hooks"] is False
    assert report["coverage"]["native_syscalls"] is False
    assert report["coverage"]["complete"] is False
    assert report["overall_classification"] == "UNKNOWN"


def test_observer_captures_synthetic_python_audit_events_in_child_process(
    tmp_path: Path,
) -> None:
    observer, repository, scratch = _observer(tmp_path)
    output = tmp_path / "observer-report.json"
    synthetic_file = scratch / "fixture.txt"
    source = """
import json
import sqlite3
import socket
import subprocess
import sys
from pathlib import Path
from scripts.apre_effects import EffectObserver

observer = EffectObserver(Path(sys.argv[1]), Path(sys.argv[2]))
observer.install()
observer.set_case("synthetic::audit")
Path(sys.argv[3]).write_text("fixture", encoding="utf-8")
sqlite3.connect(":memory:").close()
connection = socket.socket()
connection.close()
subprocess.run([sys.executable, "-c", "pass"], check=True)
observer.close()
Path(sys.argv[4]).write_text(
    json.dumps(observer.report()), encoding="utf-8"
)
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = (
        str(repository.parent.parent)
        + os.pathsep
        + environment.get("PYTHONPATH", "")
    )
    # The installed source module is available from the project root.
    project_root = Path(__file__).resolve().parents[2]
    environment["PYTHONPATH"] = (
        str(project_root) + os.pathsep + environment.get("PYTHONPATH", "")
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            source,
            str(repository),
            str(scratch),
            str(synthetic_file),
            str(output),
        ],
        check=True,
        env=environment,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    report: dict[str, Any] = json.loads(output.read_text(encoding="utf-8"))
    events = report["events"]
    observed = {(event["event"], event["classification"]) for event in events}
    assert ("open", "TEMPORARY") in observed
    assert ("sqlite3.connect", "TEMPORARY") in observed
    assert ("socket.__new__", "REAL") in observed
    assert ("subprocess.Popen", "REAL") in observed
    assert all(event["case_id"] == "synthetic::audit" for event in events)
    assert report["coverage"]["complete"] is False


def test_observer_output_must_be_outside_repository(tmp_path: Path) -> None:
    observer, repository, _ = _observer(tmp_path)
    try:
        observer.write_report(repository / "effects.json")
    except ValueError as error:
        assert "outside the repository" in str(error)
    else:
        raise AssertionError("observer accepted an in-repository output path")


def test_quality_gate_wires_observer_plugin_and_writes_external_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.quality_gate as quality_gate
    import pytest as pytest_runtime

    repository = tmp_path / "repository"
    scratch = tmp_path / "scratch"
    evidence = tmp_path / "evidence"
    (repository / "tests/unit").mkdir(parents=True)
    scratch.mkdir()
    evidence.mkdir()
    effects_output = evidence / "effects.json"
    collector_output = evidence / "collector.json"
    perimeter = Perimeter(
        suites=(
            Suite(
                path="tests/unit",
                classification="required",
                reason="synthetic collector fixture",
                modules=("tests/unit/test_synthetic.py",),
            ),
        ),
        optional_modules={},
        module_classifications={"tests/unit/test_synthetic.py": "required"},
    )
    monkeypatch.setattr(quality_gate, "REPOSITORY_ROOT", repository)

    def synthetic_pytest_main(
        args: list[str], *, plugins: list[Any]
    ) -> pytest.ExitCode:
        del args
        collector, observer = plugins
        item = type(
            "SyntheticItem", (), {"nodeid": "tests/unit/test_x.py::case"}
        )()
        observer.pytest_runtest_setup(item)
        observer.observe("socket.connect", ("synthetic-address", 1))
        observer.pytest_runtest_teardown(item)
        collector.collected["tests/unit"] = 1
        collector.outcomes["tests/unit"][item.nodeid] = "passed"
        return pytest_runtime.ExitCode.OK

    monkeypatch.setattr(pytest_runtime, "main", synthetic_pytest_main)
    result = run_gate(
        "required",
        perimeter,
        effects_output=effects_output,
        scratch_root=scratch,
        collector_output=collector_output,
    )

    assert result == pytest_runtime.ExitCode.OK
    report = json.loads(effects_output.read_text(encoding="utf-8"))
    assert report["coverage"]["complete"] is False
    assert report["events"] == [
        {
            "case_id": "tests/unit/test_x.py::case",
            "event": "socket.connect",
            "classification": "REAL",
            "path": None,
            "reason": "network or process operation requested",
        }
    ]
    assert report["overall_classification"] == "OBSERVED"
    collector = json.loads(collector_output.read_text(encoding="utf-8"))
    assert collector["pytest_exit_code"] == pytest_runtime.ExitCode.OK
    assert collector["collections"]["collected"] == 1
    assert collector["suites"][0]["status"] == "PASS"


def test_quality_gate_rejects_in_repository_observer_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.quality_gate as quality_gate

    repository = tmp_path / "repository"
    scratch = tmp_path / "scratch"
    (repository / "tests/unit").mkdir(parents=True)
    scratch.mkdir()
    perimeter = Perimeter(
        suites=(
            Suite(
                path="tests/unit",
                classification="required",
                reason="synthetic collector fixture",
                modules=("tests/unit/test_synthetic.py",),
            ),
        ),
        optional_modules={},
        module_classifications={"tests/unit/test_synthetic.py": "required"},
    )
    monkeypatch.setattr(quality_gate, "REPOSITORY_ROOT", repository)

    with pytest.raises(ValueError, match="outside the repository"):
        run_gate(
            "required",
            perimeter,
            effects_output=repository / "effects.json",
            scratch_root=scratch,
        )
