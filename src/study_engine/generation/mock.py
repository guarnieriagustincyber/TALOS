"""Deterministic Mock Generator for Subsystem S4.2 testing.

Provides configurable RawGenerationResult outputs without external network
or GPU requirements, strictly satisfying the BaseGenerator protocol.
"""

from typing import Optional

from study_engine.contracts.generation import (
    GenerationRequest,
    RawGenerationResult,
    TokenUsage,
)
from study_engine.generation.base import BaseGenerator


class MockGenerator(BaseGenerator):
    """Deterministic, configurable generator for testing."""

    def __init__(
        self,
        canned_content: Optional[str] = None,
        canned_abstained: bool = False,
        canned_latency_ms: Optional[float] = 12.5,
        canned_tokens: Optional[TokenUsage] = None,
        canned_model: Optional[str] = "mock-tutor-v1",
    ) -> None:
        """Initialize MockGenerator with canned behaviors."""
        self._content = canned_content
        self._abstained = canned_abstained
        self._latency_ms = canned_latency_ms
        self._tokens = (
            canned_tokens
            if canned_tokens is not None
            else TokenUsage(
                prompt_tokens=120, completion_tokens=45, total_tokens=165
            )
        )
        self._model = canned_model

    def generate(self, request: GenerationRequest) -> RawGenerationResult:

        """Produce RawGenerationResult according to configuration."""
        if self._content is not None:
            content = self._content
        elif request.packaged_context.packet.abstention_required:
            content = (
                "No puedo responder a esta consulta ya que no dispongo de "
                "evidencias en los documentos del cuaderno curricular."
            )
        else:
            manifest_keys = list(
                request.packaged_context.citation_manifest.records.keys()
            )
            if manifest_keys:
                cite = f"[{manifest_keys[0]}]"
                content = (
                    f"Según la evidencia documentada {cite}, el concepto "
                    f"solicitado se define conforme a las fuentes del curso."
                )
            else:
                content = "Explicación general sin referencias documentadas."

        return RawGenerationResult(
            raw_content=content,
            generator_abstained=self._abstained,
            latency_ms=self._latency_ms,
            tokens_used=self._tokens,
            model=self._model,
        )
