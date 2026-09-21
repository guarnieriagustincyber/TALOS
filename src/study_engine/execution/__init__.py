"""Subsystem S6.1: Controlled Practical Execution Engine.

Authoritative execution plane components for Phase 0 practical labs.
"""

from study_engine.execution.adapter_python import PythonExecutionAdapter
from study_engine.execution.artifact_collector import (
    collect_workspace_artifacts,
)
from study_engine.execution.base import BaseExecutionAdapter
from study_engine.execution.env_sanitizer import (
    build_sanitized_environment,
)
from study_engine.execution.io_streamer import (
    CapturedStreams,
    capture_subprocess_streams,
)
from study_engine.execution.process_manager import (
    ProcessRunOutcome,
    run_managed_process_group,
)

__all__ = [
    "BaseExecutionAdapter",
    "PythonExecutionAdapter",
    "build_sanitized_environment",
    "capture_subprocess_streams",
    "CapturedStreams",
    "collect_workspace_artifacts",
    "ProcessRunOutcome",
    "run_managed_process_group",
]
