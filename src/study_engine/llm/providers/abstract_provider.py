"""Abstract LLM Provider interface (Fase 5.9 / Pilar 1).

Decouples TALOS from vendor-specific SDKs. Standardizes asynchronous
completion and token streaming across all local and cloud backends.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import ProviderCompletion


class AbstractLLMProvider(ABC):
    """Abstract base class for all LLM providers in TalosLLMPool."""

    def __init__(self, name: str, default_model: str) -> None:
        self.name: str = name
        self.default_model: str = default_model

    @abstractmethod
    async def complete(
        self,
        prompt_bundle: PromptBundle,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> ProviderCompletion:
        """Execute a full non-streaming completion."""
        ...

    @abstractmethod
    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens asynchronously."""
        ...

    def is_available(self) -> bool:
        """Check if provider has requisite configuration (e.g. API key or endpoint)."""
        return True
