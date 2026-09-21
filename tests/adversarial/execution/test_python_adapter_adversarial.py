"""Sixteen-vector adversarial verification suite for S6.1 Execution Adapter.

Verifies that S6.1 enforces all security boundaries, resource bounds,
and failure modes under hostile or pathological student code.
"""

import os
from pathlib import Path
import pytest

from study_engine.contracts.execution import (
    ArtifactOmissionReason,
    ExecutionPlaneTier,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    TerminationReason,
    ToolCapability,
)
from study_engine.execution.adapter_python import PythonExecutionAdapter


class TestS61AdversarialSuite:
    """16 adversarial vectors targeting S6.1 PythonExecutionAdapter."""

    def test_adv_01_process_tree_timeout_kill(self, tmp_path: Path) -> None:
        """Vector 1: Process tree escape killed via process group SIGKILL."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "tree.py"
        script.write_text(
            "import subprocess, time, sys\n"
            "p = subprocess.Popen([sys.executable, '-c', "
            "'import time; time.sleep(100)'])\n"
            "time.sleep(100)\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-01",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="tree.py",
            policy=ExecutionPolicy(timeout_seconds=1),
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.TIMED_OUT
        assert result.telemetry.termination_reason == TerminationReason.TIMEOUT

    def test_adv_02_sigterm_defiance(self, tmp_path: Path) -> None:
        """Vector 2: Script ignoring SIGTERM is liquidated via SIGKILL."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "trap_term.py"
        script.write_text(
            "import signal, time\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            "while True:\n"
            "    time.sleep(0.1)\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-02",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="trap_term.py",
            policy=ExecutionPolicy(timeout_seconds=1),
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.TIMED_OUT
        assert result.telemetry.termination_reason == TerminationReason.TIMEOUT

    def test_adv_03_output_flooding_bounded(self, tmp_path: Path) -> None:
        """Vector 3: Print flooding is bounded without memory bloat."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "flood.py"
        # Prints 50,000 lines of 100 bytes (~5MB)
        script.write_text(
            "import sys\n"
            "for _ in range(50000):\n"
            "    sys.stdout.write('A' * 100 + '\\n')\n"
        )
        adapter = PythonExecutionAdapter()
        policy = ExecutionPolicy(max_output_bytes=10000)  # 10KB cap
        req = ExecutionRequest(
            request_id="adv-03",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="flood.py",
            policy=policy,
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.stdout.encode("utf-8")) <= 10000
        assert result.telemetry.output_truncated is True
        assert result.telemetry.output_bytes_discarded > 0

    def test_adv_04_stdin_flooding_rejected(self, tmp_path: Path) -> None:
        """Vector 4: Massive stdin payload is rejected by request policy."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "cat.py"
        script.write_text("print('test')\n")

        adapter = PythonExecutionAdapter()
        # Stdin is 100KB, max allowed is 64KB
        policy = ExecutionPolicy(max_stdin_bytes=1024)
        req = ExecutionRequest(
            request_id="adv-04",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="cat.py",
            stdin_payload="X" * 2048,
            policy=policy,
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.POLICY_REJECTED
        assert "max_stdin_bytes" in (result.sanitized_engine_error or "")

    def test_adv_05_binary_and_null_bytes(self, tmp_path: Path) -> None:
        """Vector 5: Arbitrary binary bytes do not crash UTF-8 decoding."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "binary_out.py"
        script.write_text(
            "import sys\n"
            "sys.stdout.buffer.write(b'\\x00\\xff\\xfe\\x01\\x80\\x7f')\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-05",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="binary_out.py",
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        # Must decode safely with replacement characters without raising
        assert len(result.stdout) > 0

    def test_adv_06_host_secret_exfiltration_prevented(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Vector 6: Script attempting to read host API keys fails closed."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-token-12345")
        monkeypatch.setenv("GEMINI_API_KEY", "gem-secret-key-67890")

        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "exfil.py"
        script.write_text(
            "import os\n"
            "k = os.environ['OPENAI_API_KEY']\n"
            "print(f'Exfiltrated: {k}')\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-06",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="exfil.py",
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.FAILED_PROCESS
        assert "KeyError" in result.stderr
        assert "sk-secret-token-12345" not in result.stdout
        assert "sk-secret-token-12345" not in result.stderr

    def test_adv_07_symlink_file_escape_rejected(
        self, tmp_path: Path
    ) -> None:
        """Vector 7: Script creating symlink to host file is rejected."""
        ws = tmp_path / "ws"
        ws.mkdir()
        secret_host_file = tmp_path / "host_secrets.txt"
        secret_host_file.write_text("HOST_SECRETS_DATA")

        script = ws / "symlink_attack.py"
        script.write_text(
            f"import os\n"
            f"os.symlink('{secret_host_file}', 'loot.txt')\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-07",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="symlink_attack.py",
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        # Symlink must NOT be collected as produced artifact
        assert len(result.produced_artifacts) == 0
        assert len(result.omitted_artifacts) == 1
        assert (
            result.omitted_artifacts[0].reason
            == ArtifactOmissionReason.SYMLINK_REJECTED
        )

    def test_adv_08_symlink_directory_escape_rejected(
        self, tmp_path: Path
    ) -> None:
        """Vector 8: Script creating symlink to host directory is rejected."""
        ws = tmp_path / "ws"
        ws.mkdir()
        host_dir = tmp_path / "sensitive_dir"
        host_dir.mkdir()
        (host_dir / "key.pem").write_text("PRIVATE_KEY")

        script = ws / "symlink_dir_attack.py"
        script.write_text(
            f"import os\n"
            f"os.symlink('{host_dir}', 'loot_dir')\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-08",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="symlink_dir_attack.py",
        )
        result = adapter.execute(req, ws)
        assert len(result.produced_artifacts) == 0
        assert len(result.omitted_artifacts) == 1
        assert (
            result.omitted_artifacts[0].reason
            == ArtifactOmissionReason.SYMLINK_REJECTED
        )

    def test_adv_09_workspace_traversal_rejected(
        self, tmp_path: Path
    ) -> None:
        """Vector 9: Request attempting path traversal is rejected."""
        ws = tmp_path / "ws"
        ws.mkdir()

        # Try to pass outside path via relative traversal
        with pytest.raises(Exception):
            ExecutionRequest(
                request_id="adv-09",
                capability=ToolCapability(capability_name="python.run_script"),
                workspace_id="ws-01",
                relative_script_path="../../outside.py",
            )

    def test_adv_10_environment_mutation_isolated(
        self, tmp_path: Path
    ) -> None:
        """Vector 10: Child mutating its environment cannot alter host."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "mutate_env.py"
        script.write_text(
            "import os\n"
            "os.environ['MUTATED_SECRET'] = 'poisoned'\n"
            "print('Mutated inside child')\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-10",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="mutate_env.py",
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        assert "MUTATED_SECRET" not in os.environ

    def test_adv_11_single_huge_artifact_omitted(
        self, tmp_path: Path
    ) -> None:
        """Vector 11: Oversized file is omitted with EXCEEDS_SIZE_LIMIT."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "huge_file.py"
        # Write 20KB file when limit is 10KB
        script.write_text(
            "with open('huge.dat', 'wb') as f:\n"
            "    f.write(b'0' * 20000)\n"
        )
        policy = ExecutionPolicy(max_artifact_bytes=10000)
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-11",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="huge_file.py",
            policy=policy,
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.produced_artifacts) == 0
        assert len(result.omitted_artifacts) == 1
        assert (
            result.omitted_artifacts[0].reason
            == ArtifactOmissionReason.EXCEEDS_SIZE_LIMIT
        )

    def test_adv_12_artifact_count_explosion_truncated(
        self, tmp_path: Path
    ) -> None:
        """Vector 12: File count explosion is capped at max_artifact_count."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "many_files.py"
        script.write_text(
            "for i in range(10):\n"
            "    with open(f'file_{i}.txt', 'w') as f:\n"
            "        f.write(f'{i}')\n"
        )
        policy = ExecutionPolicy(max_artifact_count=4)
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-12",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="many_files.py",
            policy=policy,
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.produced_artifacts) == 4
        assert len(result.omitted_artifacts) == 6
        assert result.artifact_summary.collection_truncated is True
        assert (
            result.omitted_artifacts[0].reason
            == ArtifactOmissionReason.EXCEEDS_COUNT_LIMIT
        )

    def test_adv_13_fork_bomb_timeout_mitigation(
        self, tmp_path: Path
    ) -> None:
        """Vector 13: Fork explosion is caught and liquidated by timeout."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "fork_loop.py"
        script.write_text(
            "import os, time\n"
            "try:\n"
            "    for _ in range(5):\n"
            "        os.fork()\n"
            "except Exception:\n"
            "    pass\n"
            "time.sleep(100)\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-13",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="fork_loop.py",
            policy=ExecutionPolicy(timeout_seconds=1),
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.TIMED_OUT

    def test_adv_14_process_tree_after_parent_exit(
        self, tmp_path: Path
    ) -> None:
        """Vector 14: Parent exits leaving running child; child reaped."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "spawn_daemon.py"
        script.write_text(
            "import subprocess, sys\n"
            "p = subprocess.Popen([sys.executable, '-c', "
            "'import time; time.sleep(0.5)'])\n"
            "# Parent exits immediately\n"
            "sys.exit(0)\n"
        )
        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-14",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="spawn_daemon.py",
            policy=ExecutionPolicy(timeout_seconds=2),
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.COMPLETED
        assert result.exit_code == 0

    def test_adv_15_engine_error_sanitization(
        self, tmp_path: Path
    ) -> None:
        """Vector 15: Engine error message does not leak host file paths."""
        ws = tmp_path / "ws"
        ws.mkdir()
        adapter = PythonExecutionAdapter()

        # Non-existent script
        req = ExecutionRequest(
            request_id="adv-15",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="non_existent.py",
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.POLICY_REJECTED
        error_msg = result.sanitized_engine_error or ""
        assert "/media/agustin" not in error_msg
        assert "/home/agustin" not in error_msg
        assert "Script file does not exist" in error_msg

    def test_adv_16_unsupported_tier_zero_execution(
        self, tmp_path: Path
    ) -> None:
        """Vector 16: TIER_1 request produces POLICY_REJECTED without run."""
        ws = tmp_path / "ws"
        ws.mkdir()
        script = ws / "harmful.py"
        # If this runs, it creates a file
        script.write_text("open('should_not_exist.txt', 'w').write('bad')\n")

        adapter = PythonExecutionAdapter()
        req = ExecutionRequest(
            request_id="adv-16",
            capability=ToolCapability(capability_name="python.run_script"),
            workspace_id="ws-01",
            relative_script_path="harmful.py",
            tier=ExecutionPlaneTier.TIER_1,
        )
        result = adapter.execute(req, ws)
        assert result.status == ExecutionStatus.POLICY_REJECTED
        assert result.exit_code == -1
        assert not (ws / "should_not_exist.txt").exists()
