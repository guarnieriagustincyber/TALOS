"""Authoritative generation protocol for Subsystem S4.2 / S4.3.

Establishes the strict boundary between external generation engines
(S4.3) and deterministic output parsing, manifest resolution, and
citation auditing (S4.2 / S4.4).
"""

from typing import Protocol, runtime_checkable

from study_engine.contracts.generation import (
    GenerationRequest,
    RawGenerationResult,
)


@runtime_checkable
class BaseGenerator(Protocol):
    """Protocol for model adapters and generation engines.

    RULE: A BaseGenerator returns RawGenerationResult, NEVER
    GenerationResponse. Certified GenerationResponse instances are produced
    exclusively by the S4.2 GenerationOutputParser.
    """

    def generate(self, request: GenerationRequest) -> RawGenerationResult:
        """Execute generation for the given request and return raw output."""
        ...
