"""Deterministic Mock Provider for hermetic testing of TalosLLMPool (Fase 5.9)."""

import asyncio
import time
from typing import AsyncGenerator, Optional

from study_engine.contracts.generation import TokenUsage
from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import ProviderCompletion
from study_engine.llm.providers.abstract_provider import AbstractLLMProvider


class MockProvider(AbstractLLMProvider):
    """Controllable mock provider for testing fallbacks, quotas, and mid-stream errors."""

    def __init__(
        self,
        name: str = "mock",
        default_model: str = "mock-model-v1",
        canned_response: str = "Respuesta simulada determinista de MockProvider.",
        available: bool = True,
        should_fail: bool = False,
        failure_exception: Optional[Exception] = None,
        fail_after_tokens: int = -1,
        latency_seconds: float = 0.0,
    ) -> None:
        super().__init__(name=name, default_model=default_model)
        self.canned_response = canned_response or "Ok"
        self._available = available
        self.should_fail = should_fail
        self.failure_exception = failure_exception or RuntimeError(f"Simulated failure in {name}")
        self.fail_after_tokens = fail_after_tokens
        self.latency_seconds = latency_seconds
        self.call_count: int = 0

    def is_available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        self._available = available

    async def complete(
        self,
        prompt_bundle: PromptBundle,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> ProviderCompletion:
        t0 = time.time()
        self.call_count += 1
        if self.latency_seconds > 0:
            await asyncio.sleep(self.latency_seconds)

        if self.should_fail:
            raise self.failure_exception

        tokens_count = len(self.canned_response.split())
        elapsed_ms = (time.time() - t0) * 1000.0
        return ProviderCompletion(
            text=self.canned_response,
            latency_ms=elapsed_ms,
            model=self.default_model,
            tokens_used=TokenUsage(
                prompt_tokens=10,
                completion_tokens=tokens_count,
                total_tokens=tokens_count + 10,
            ),
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        self.call_count += 1
        if self.latency_seconds > 0:
            await asyncio.sleep(self.latency_seconds)

        if self.should_fail:
            raise self.failure_exception

        words = self.canned_response.split(" ")
        emitted = 0
        for i, word in enumerate(words):
            if self.fail_after_tokens >= 0 and emitted >= self.fail_after_tokens:
                raise self.failure_exception

            chunk = word if i == len(words) - 1 else word + " "
            emitted += 1
            yield chunk
            await asyncio.sleep(0.001)
