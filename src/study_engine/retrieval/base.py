"""Abstract base protocol for retrieval engines in Subsystem S3."""

from typing import Protocol, runtime_checkable
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
)


@runtime_checkable
class BaseRetriever(Protocol):
    """Minimal protocol defining the retrieval boundary."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Execute a retrieval query and return ranked, isolated candidates."""
        ...
