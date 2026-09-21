"""Process group lifecycle and timeout enforcement for S6.1.

INVARIANTS:
1. Process Group Isolation: Processes are spawned with start_new_session=True.
2. Group Termination: Timeouts kill the entire process group via os.killpg.
3. Graceful Escalation: SIGTERM followed by 2.0s grace period before SIGKILL.
4. Clean I/O Separation: DEVNULL used when no stdin payload is provided.
"""

from dataclasses import dataclass
import os
import signal
import subprocess
import time
from typing import Dict, List, Optional

from study_engine.contracts.execution import TerminationReason
from study_engine.execution.io_streamer import (
    CapturedStreams,
    capture_subprocess_streams,
)


@dataclass(frozen=True)
class ProcessRunOutcome:
    """Outcome of managed process execution."""

    exit_code: int
    duration_ms: float
    streams: CapturedStreams
    timed_out: bool
    termination_reason: TerminationReason


def run_managed_process_group(
    cmd: List[str],
    cwd: str,
    env: Dict[str, str],
    timeout_seconds: int,
    max_output_bytes: int,
    stdin_payload: Optional[str] = None,
) -> ProcessRunOutcome:
    """Execute command in new process group with bounded I/O and timeout.

    Args:
        cmd: Argument vector (e.g. [sys.executable, "-u", script_path]).
        cwd: Working directory (scratch workspace).
        env: Sanitized environment dictionary.
        timeout_seconds: Wall-clock timeout limit in seconds.
        max_output_bytes: Combined output cap for stdout and stderr.
        stdin_payload: Optional stdin string payload.

    Returns:
        ProcessRunOutcome with returncode, timing, streams, and reason.
    """
    if stdin_payload is not None:
        stdin_mode = subprocess.PIPE
    else:
        stdin_mode = subprocess.DEVNULL

    t_start = time.perf_counter()

    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=stdin_mode,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    pgid = os.getpgid(p.pid)
    timed_out = False

    # Start I/O streaming in background thread
    streams_holder: list[CapturedStreams] = []

    def _stream_worker() -> None:
        captured = capture_subprocess_streams(
            process=p,
            max_output_bytes=max_output_bytes,
            stdin_payload=stdin_payload,
        )
        streams_holder.append(captured)

    import threading

    io_thread = threading.Thread(target=_stream_worker, daemon=True)
    io_thread.start()

    # Monitor timeout
    deadline = t_start + timeout_seconds
    while True:
        ret = p.poll()
        if ret is not None:
            break
        now = time.perf_counter()
        if now >= deadline:
            timed_out = True
            break
        # Fine-grained sleep
        time.sleep(0.05)

    if timed_out:
        # 1. Send SIGTERM to entire process group
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

        # 2. Wait grace period (up to 2.0s)
        grace_deadline = time.perf_counter() + 2.0
        while time.perf_counter() < grace_deadline:
            if p.poll() is not None:
                break
            time.sleep(0.05)

        # 3. If still alive, escalate to SIGKILL
        if p.poll() is None:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            p.wait()

    t_end = time.perf_counter()
    duration_ms = (t_end - t_start) * 1000.0

    io_thread.join(timeout=3.0)

    if streams_holder:
        streams = streams_holder[0]
    else:
        streams = CapturedStreams(
            stdout="",
            stderr="[I/O Capture Error]",
            bytes_captured=0,
            bytes_discarded=0,
            truncated=False,
        )

    exit_code = p.returncode if p.returncode is not None else -1

    if timed_out:
        term_reason = TerminationReason.TIMEOUT
    elif exit_code == 0:
        term_reason = TerminationReason.NORMAL_EXIT
    else:
        term_reason = TerminationReason.NONZERO_EXIT

    return ProcessRunOutcome(
        exit_code=exit_code,
        duration_ms=duration_ms,
        streams=streams,
        timed_out=timed_out,
        termination_reason=term_reason,
    )
