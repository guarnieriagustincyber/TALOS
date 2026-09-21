"""Base protocol for execution adapters in S6 Execution Plane."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionRequest,
    ExecutionResult,
)


@runtime_checkable
class BaseExecutionAdapter(Protocol):
    """Authoritative protocol for execution sandboxes and adapters."""

    @property
    def adapter_id(self) -> str:
        """Unique identifier of the execution adapter implementation."""
        ...

    @property
    def adapter_version(self) -> str:
        """Semantic version of the adapter."""
        ...

    def execute(
        self, request: ExecutionRequest, workspace_root: Path
    ) -> ExecutionResult:
        """Execute request within the bounded sandbox environment."""
        ...

    def observe(
        self, result: ExecutionResult, tool_name: str
    ) -> ExecutionObservation:
        """Convert low-level ExecutionResult into an Observation."""
        ...
