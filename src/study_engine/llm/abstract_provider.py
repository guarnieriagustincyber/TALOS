"""Abstract LLM Provider interface (Ola 5, Fase 5.3).

Standardizes synchronous/asynchronous generation, streaming, health checks,
and capabilities across all multi-backend providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Iterator, Optional

from study_engine.contracts.generation import TokenUsage


@dataclass(frozen=True)
class LLMResponse:
    """Standardized completion response from an AbstractLLMProvider."""
    text: str
    latency_ms: float
    tokens_used: Optional[TokenUsage] = None
    model: str = ""
    provider_id: str = ""


@dataclass
class ProviderHealth:
    """Detailed telemetry and health evaluation of a provider backend."""
    provider_id: str
    availability: float          # 0.0 - 1.0
    avg_latency_ms: float
    rate_limit_429_count: int
    context_capacity: int
    multimodal_support: bool
    structured_output: bool
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    is_healthy: bool = True

    @property
    def composite_score(self) -> float:
        """Composite health score: availability * 0.4 + latency_factor * 0.3 + error_penalty * 0.3.

        Higher score = better provider candidate.
        """
        if not self.is_healthy or self.availability <= 0.0:
            return 0.0

        # Normalized latency: 0ms -> 1.0; 2000ms+ -> 0.0
        norm_latency = max(0.0, 1.0 - min(self.avg_latency_ms, 2000.0) / 2000.0)

        # Error penalty: each 429 degrades 429 score
        error_factor = max(0.0, 1.0 - min(self.rate_limit_429_count * 0.2, 1.0))

        score = (self.availability * 0.4) + (norm_latency * 0.3) + (error_factor * 0.3)
        return round(score, 4)


class AbstractLLMProvider(ABC):
    """Abstract interface for all model providers in ModelRegistry."""

    def __init__(self, provider_id: str, default_model: str) -> None:
        self.provider_id = provider_id
        self.default_model = default_model

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> LLMResponse:
        """Synchronously or blocking generate completion."""
        ...

    @abstractmethod
    def generate_stream(self, prompt: str, max_tokens: int = 1000) -> Iterator[str]:
        """Synchronously stream tokens."""
        ...

    @abstractmethod
    def supports_multimodal(self) -> bool:
        """True if provider supports multimodal image/diagram inputs."""
        ...

    @abstractmethod
    def max_context_tokens(self) -> int:
        """Maximum context window capacity in tokens."""
        ...

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Return real-time or cached health evaluation."""
        ...
