"""Bounded, streaming I/O capture for student subprocess execution.

INVARIANTS:
1. Hard Output Limit: Total stdout + stderr captured never exceeds
   max_output_bytes in RAM.
2. Discard Accounting: Any output beyond max_output_bytes is discarded;
   output_bytes_discarded is counted accurately.
3. Binary Safety: UTF-8 decoding uses errors='replace' to prevent crashes
   on arbitrary binary or null-byte outputs.
4. Non-Blocking Concurrency: stdout and stderr pipes are read concurrently
   via background worker threads to prevent OS pipe buffer deadlock.
"""

from dataclasses import dataclass
import subprocess
import threading
from typing import BinaryIO, Optional


@dataclass(frozen=True)
class CapturedStreams:
    """Immutable result of bounded stream capture."""

    stdout: str
    stderr: str
    bytes_captured: int
    bytes_discarded: int
    truncated: bool


def capture_subprocess_streams(
    process: subprocess.Popen[bytes],
    max_output_bytes: int,
    stdin_payload: Optional[str] = None,
) -> CapturedStreams:
    """Capture process stdout and stderr with global hard output bounding.

    Args:
        process: Subprocess instance with stdout=PIPE, stderr=PIPE, stdin=PIPE.
        max_output_bytes: Global ceiling for captured bytes (stdout + stderr).
        stdin_payload: Optional string to write to child stdin before closing.

    Returns:
        CapturedStreams containing bounded decoded text and telemetry.
    """
    # 1. Write stdin payload if provided and close pipe
    if process.stdin is not None:
        try:
            if stdin_payload is not None:
                process.stdin.write(stdin_payload.encode("utf-8"))
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    captured_count = 0
    discarded_count = 0
    lock = threading.Lock()

    def _reader(pipe: Optional[BinaryIO], is_stdout: bool) -> None:
        nonlocal captured_count, discarded_count
        if pipe is None:
            return

        chunk_size = 4096
        try:
            while True:
                chunk = pipe.read(chunk_size)
                if not chunk:
                    break

                with lock:
                    remaining_capacity = max_output_bytes - captured_count
                    if remaining_capacity > 0:
                        accepted_len = min(len(chunk), remaining_capacity)
                        accepted_bytes = chunk[:accepted_len]
                        if is_stdout:
                            stdout_chunks.append(accepted_bytes)
                        else:
                            stderr_chunks.append(accepted_bytes)
                        captured_count += accepted_len

                        # Any remainder of this chunk is discarded
                        excess = len(chunk) - accepted_len
                        discarded_count += excess
                    else:
                        discarded_count += len(chunk)
        finally:
            pipe.close()

    stdout_thread = threading.Thread(
        target=_reader, args=(process.stdout, True), daemon=True
    )
    stderr_thread = threading.Thread(
        target=_reader, args=(process.stderr, False), daemon=True
    )

    stdout_thread.start()
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()

    stdout_bytes = b"".join(stdout_chunks)
    stderr_bytes = b"".join(stderr_chunks)

    stdout_text = stdout_bytes.decode("utf-8", errors="replace")
    stderr_text = stderr_bytes.decode("utf-8", errors="replace")

    return CapturedStreams(
        stdout=stdout_text,
        stderr=stderr_text,
        bytes_captured=captured_count,
        bytes_discarded=discarded_count,
        truncated=discarded_count > 0,
    )
