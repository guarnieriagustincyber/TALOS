"""Security regression tests for programming-submission execution."""

import multiprocessing
import os
from pathlib import Path
import time
from typing import Any

import pytest

from study_engine.pedagogy.auditors.programming_auditor import (
    ProgrammingExerciseAuditor,
    _acquire_audit_slot,
)
from study_engine.pedagogy.submission_reader import StudentSubmission


def _probe_audit_slot(
    directory: str,
    result_queue: Any,
    release_event: Any,
    audit_request: bool = False,
) -> None:
    import study_engine.pedagogy.auditors.programming_auditor as auditor_module

    auditor_module._AUDIT_SLOT_DIRECTORY = Path(directory)
    if audit_request:
        def unexpected_sandbox_start(**kwargs: Any) -> None:
            raise AssertionError("rejected audit attempted to create a sandbox")

        auditor_module.run_managed_process_group = unexpected_sandbox_start
        result = ProgrammingExerciseAuditor()._execute_tests_safe(
            "answer = 42\n",
            "assert answer == 42\n",
        )
        result_queue.put(result["execution_status"])
        return

    descriptor = _acquire_audit_slot()
    result_queue.put("acquired" if descriptor is not None else "rejected")
    if descriptor is not None:
        try:
            release_event.wait(timeout=5)
        finally:
            os.close(descriptor)


def test_valid_submission_executes_in_isolated_process() -> None:
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "def is_valid(value: int) -> bool:\n    return 0 <= value <= 255\n",
        "assert is_valid(0)\nassert is_valid(255)\nassert not is_valid(256)\n",
    )

    assert result["execution_status"] == "pass"
    assert result["success"] is True
    assert result["assertions_count"] == 3


def test_assertion_failure_is_distinguished() -> None:
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "def answer() -> int:\n    return 41\n",
        "assert answer() == 42\n",
    )

    assert result["execution_status"] == "assertion_failure"
    assert result["success"] is False
    assert "AssertionError" in result["error"]


def test_runtime_exception_is_distinguished() -> None:
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "raise ValueError('controlled runtime failure')\n",
        "assert True\n",
    )

    assert result["execution_status"] == "runtime_error"
    assert "controlled runtime failure" in result["error"]


def test_filesystem_escape_is_inaccessible(tmp_path: Path) -> None:
    sentinel = tmp_path / "host-only-sentinel.txt"
    sentinel.write_text("synthetic filesystem sentinel", encoding="utf-8")
    code = (
        f"try:\n    open({str(sentinel)!r}, encoding='utf-8').read()\n"
        "except Exception:\n    pass\n"
        "else:\n    raise AssertionError('host file was visible')\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"
    assert sentinel.read_text(encoding="utf-8") == "synthetic filesystem sentinel"


def test_system_filesystem_is_read_only() -> None:
    code = (
        "os_module = __builtins__['__import__'].__globals__['sys'].modules['os']\n"
        "with open('/usr/bin/python3.12', 'rb') as system_binary:\n"
        "    assert system_binary.read(1)\n"
        "try:\n"
        "    fd = os_module.open('/usr/bin/python3.12', os_module.O_WRONLY)\n"
        "except OSError:\n"
        "    pass\n"
        "else:\n"
        "    os_module.close(fd)\n"
        "    raise AssertionError('system filesystem was writable')\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"


def test_path_traversal_and_host_symlink_are_inaccessible(tmp_path: Path) -> None:
    sentinel = tmp_path / "host-only-symlink-sentinel.txt"
    sentinel.write_text("synthetic traversal sentinel", encoding="utf-8")
    symlink = tmp_path / "host-only-symlink"
    symlink.symlink_to(sentinel)
    code = (
        f"for path in ({str(sentinel)!r}, {str(symlink)!r}, "
        f"{('/workspace/../../' + str(sentinel).lstrip('/'))!r}):\n"
        "    try:\n"
        "        open(path, encoding='utf-8').read()\n"
        "    except OSError:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('host path escaped the sandbox')\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"
    assert sentinel.read_text(encoding="utf-8") == "synthetic traversal sentinel"


def test_parent_environment_is_not_inherited(monkeypatch) -> None:
    monkeypatch.setenv("TALOS_P0_SYNTHETIC_SECRET", "synthetic-parent-value")
    code = (
        "with open('/proc/self/environ', 'rb') as child_environment:\n"
        "    assert b'TALOS_P0_SYNTHETIC_SECRET=synthetic-parent-value' "
        "not in child_environment.read()\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"


def test_network_namespace_blocks_external_route() -> None:
    code = (
        "import socket\n"
        "connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
        "try:\n"
        "    try:\n"
        "        connection.connect(('198.51.100.1', 9))\n"
        "    except OSError:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('network route was available')\n"
        "finally:\n"
        "    connection.close()\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"


def test_subprocess_import_is_rejected() -> None:
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "import subprocess\n",
        "assert True\n",
    )

    assert result["execution_status"] == "runtime_error"
    assert "Import not allowed: subprocess" in result["error"]


def test_process_creation_is_limited() -> None:
    code = (
        "os_module = __builtins__['__import__'].__globals__['sys'].modules['os']\n"
        "children = []\n"
        "limit_reached = False\n"
        "for _ in range(32):\n"
        "    try:\n"
        "        child_pid = os_module.fork()\n"
        "    except OSError:\n"
        "        limit_reached = True\n"
        "        break\n"
        "    if child_pid == 0:\n"
        "        os_module._exit(0)\n"
        "    children.append(child_pid)\n"
        "for child_pid in children:\n"
        "    os_module.waitpid(child_pid, 0)\n"
        "assert not children, 'a child process was created'\n"
        "assert limit_reached, 'process creation was not limited'\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"


def test_infinite_loop_times_out() -> None:
    started = time.monotonic()
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "while True:\n    pass\n",
        "assert True\n",
    )

    assert result["execution_status"] == "timeout"
    assert result["success"] is False
    assert time.monotonic() - started < 8
    followup = ProgrammingExerciseAuditor()._execute_tests_safe(
        "answer = 42\n",
        "assert answer == 42\n",
    )
    assert followup["execution_status"] == "pass"


def test_output_flood_is_captured_with_a_hard_cap() -> None:
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "print('x' * 2_000_000)\n",
        "assert True\n",
    )

    assert result["execution_status"] == "pass"
    assert result["output_truncated"] is True
    assert result["output_bytes_captured"] == 16_384
    assert result["output_bytes_discarded"] > 0


def test_address_space_limit_rejects_oversized_allocation() -> None:
    code = (
        "try:\n"
        "    allocation = [0] * 100_000_000\n"
        "except MemoryError:\n"
        "    pass\n"
        "else:\n"
        "    raise AssertionError('address-space limit was not enforced')\n"
    )

    result = ProgrammingExerciseAuditor()._execute_tests_safe(code, "assert True\n")

    assert result["execution_status"] == "pass"


def test_audit_slot_rejects_concurrent_execution_and_releases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import study_engine.pedagogy.auditors.programming_auditor as auditor_module

    monkeypatch.setattr(auditor_module, "_AUDIT_SLOT_DIRECTORY", tmp_path / "slots")
    descriptor = _acquire_audit_slot()
    assert descriptor is not None
    try:
        result = ProgrammingExerciseAuditor()._execute_tests_safe(
            "answer = 42\n",
            "assert answer == 42\n",
        )
        assert result["execution_status"] == "concurrency_limit"
        assert result["success"] is False
    finally:
        os.close(descriptor)

    result_after_release = ProgrammingExerciseAuditor()._execute_tests_safe(
        "answer = 42\n",
        "assert answer == 42\n",
    )
    assert result_after_release["execution_status"] == "pass"


def test_audit_slot_serializes_across_processes_and_releases_on_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import study_engine.pedagogy.auditors.programming_auditor as auditor_module

    context = multiprocessing.get_context("fork")
    directory = tmp_path / "slots"
    directory.mkdir(mode=0o700)
    monkeypatch.setattr(auditor_module, "_AUDIT_SLOT_DIRECTORY", directory)
    results = context.Queue()
    release = context.Event()
    owner = context.Process(
        target=_probe_audit_slot,
        args=(str(directory), results, release),
    )
    owner.start()
    try:
        assert results.get(timeout=5) == "acquired"
        rejected = context.Process(
            target=_probe_audit_slot,
            args=(str(directory), results, release, True),
        )
        rejected.start()
        assert results.get(timeout=5) == "concurrency_limit"
        rejected.join(timeout=5)
        assert rejected.exitcode == 0
    finally:
        release.set()
        owner.join(timeout=5)
    assert owner.exitcode == 0

    occupied = context.Process(
        target=_probe_audit_slot,
        args=(str(directory), results, release),
    )
    occupied.start()
    assert results.get(timeout=5) == "acquired"
    occupied.terminate()
    occupied.join(timeout=5)
    assert occupied.exitcode is not None

    recovered = context.Process(
        target=_probe_audit_slot,
        args=(str(directory), results, release),
    )
    recovered.start()
    assert results.get(timeout=5) == "acquired"
    release.set()
    recovered.join(timeout=5)
    assert recovered.exitcode == 0


def test_audit_slot_releases_after_process_manager_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import study_engine.pedagogy.auditors.programming_auditor as auditor_module

    monkeypatch.setattr(auditor_module, "_AUDIT_SLOT_DIRECTORY", tmp_path / "slots")

    def raise_launch_error(**kwargs: Any) -> None:
        raise OSError("synthetic launch error")

    with monkeypatch.context() as patch:
        patch.setattr(
            auditor_module,
            "run_managed_process_group",
            raise_launch_error,
        )
        failed = ProgrammingExerciseAuditor()._execute_tests_safe(
            "answer = 42\n",
            "assert answer == 42\n",
        )
        assert failed["execution_status"] == "infrastructure_error"

    result_after_exception = ProgrammingExerciseAuditor()._execute_tests_safe(
        "answer = 42\n",
        "assert answer == 42\n",
    )
    assert result_after_exception["execution_status"] == "pass"


def test_concurrency_rejection_does_not_update_bkt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import study_engine.pedagogy.auditors.programming_auditor as auditor_module

    class UnexpectedBKTUpdate:
        def get_state(self, kc_id: str) -> None:
            raise AssertionError("BKT state must not be read for a rejected audit")

        def update(self, **kwargs: Any) -> None:
            raise AssertionError("BKT must not be updated for a rejected audit")

    submission = StudentSubmission(
        exercise_id="isolated_audit",
        title="isolated audit",
        file_path=str(tmp_path / "submission.md"),
        code_blocks={
            "python": [
                "def answer() -> int:\n    return 42\n",
                "assert answer() == 42\n",
            ]
        },
        raw_content="synthetic rejected audit",
    )
    monkeypatch.setattr(
        ProgrammingExerciseAuditor,
        "_execute_tests_safe",
        lambda self, code, tests: {
            "success": False,
            "execution_status": "concurrency_limit",
            "error": "slot occupied",
        },
    )
    report = ProgrammingExerciseAuditor(bkt_tracker=UnexpectedBKTUpdate()).audit(
        submission
    )

    test_check = next(check for check in report.checks if check.name == "tests")
    assert not test_check.passed
    assert "reintentá" in test_check.feedback
    assert report.passed is False
    assert report.bkt_updated is False


@pytest.mark.parametrize("missing_tool", ["bwrap", "prlimit"])
def test_missing_sandbox_fails_closed(monkeypatch, missing_tool: str) -> None:
    import study_engine.pedagogy.auditors.programming_auditor as programming_auditor

    original_which = programming_auditor.shutil.which

    def without_bubblewrap(command: str) -> str | None:
        if command == missing_tool:
            return None
        return original_which(command)

    monkeypatch.setattr(programming_auditor.shutil, "which", without_bubblewrap)
    result = ProgrammingExerciseAuditor()._execute_tests_safe(
        "answer = 42\n",
        "assert answer == 42\n",
    )

    assert result["execution_status"] == "infrastructure_error"
    assert result["success"] is False
