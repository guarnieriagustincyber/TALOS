"""TalosLLMRouter & ProviderCircuitBreaker (Fase 5.9 / Pilar 2 / Ajustes 1, 3, 4).

Features:
- Thread-safe ProviderCircuitBreaker with asyncio.Lock() (CLOSED, OPEN, HALF_OPEN).
- Semantic Routing per pedagogical phase.
- Mid-stream fallback with clean buffer discarding and retry on next provider.
- DataSanitizer enforcement (fail-closed, local-only routing for sensitive data).
- QuotaManager integration with proactive 90% cutoff.
- Diagnostic Health Status reporting.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import logging
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from study_engine.contracts.generation import TokenUsage
from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import ProviderCompletion
from study_engine.llm.providers.abstract_provider import AbstractLLMProvider
from study_engine.llm.quota_manager import QuotaManager
from study_engine.llm.sanitizer import DataSanitizer, SensitiveDataLeakError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class PoolExhaustedError(RuntimeError):
    """Raised when all candidate LLM providers in the pool fail or are saturated."""
    pass


class ProviderCircuitBreaker:
    """Thread-safe circuit breaker with asyncio.Lock() protecting state transitions."""

    def __init__(
        self,
        provider_name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
    ) -> None:
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self._state: CircuitState = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._opened_at: Optional[float] = None
        self._last_failure: Optional[str] = None
        self._half_open_in_flight: bool = False
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def last_failure(self) -> Optional[str]:
        return self._last_failure

    async def can_proceed(self) -> bool:
        """Evaluate if provider can accept a request under lock protection."""
        async with self._lock:
            now = time.time()
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                if self._opened_at is not None and (now - self._opened_at) >= self.cooldown_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_in_flight = True
                    logger.info(
                        f"[CIRCUIT BREAKER] Provider {self.provider_name} transitioned from OPEN to HALF_OPEN."
                    )
                    return True
                return False

            if self._state == CircuitState.HALF_OPEN:
                if not self._half_open_in_flight:
                    self._half_open_in_flight = True
                    return True
                return False

            return False

    async def record_success(self) -> None:
        """Record successful execution and reset failure counters."""
        async with self._lock:
            self._consecutive_failures = 0
            self._half_open_in_flight = False
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._opened_at = None
                logger.info(
                    f"[CIRCUIT BREAKER] Provider {self.provider_name} recovered to CLOSED."
                )

    async def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record provider failure and conditionally open circuit."""
        async with self._lock:
            self._consecutive_failures += 1
            self._last_failure = datetime.now(timezone.utc).isoformat()
            self._half_open_in_flight = False

            is_429 = error is not None and "429" in str(error)
            should_open = (
                self._state == CircuitState.HALF_OPEN
                or is_429
                or self._consecutive_failures >= self.failure_threshold
            )

            if should_open:
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                logger.warning(
                    f"[CIRCUIT BREAKER] Provider {self.provider_name} circuit OPENED: "
                    f"failures={self._consecutive_failures}, is_429={is_429}, err={error}"
                )


DEFAULT_PHASE_ROUTING: Dict[str, List[str]] = {
    "conceptual": ["nvidia", "cerebras", "sambanova", "ollama"],
    "verification": ["nvidia", "cerebras", "sambanova", "ollama"],
    "pseudocode": ["cerebras", "sambanova", "nvidia", "ollama"],
    "python_code": ["nvidia", "cerebras", "sambanova", "ollama"],
    "greeting": ["ollama", "cloudflare"],
    "navigation": ["ollama", "cloudflare"],
    "*": ["nvidia", "cerebras", "sambanova", "ollama"],
}


class TalosLLMRouter:
    """Multi-cloud resilient router with phase awareness, sanitization, and fallback."""

    def __init__(
        self,
        providers: Dict[str, AbstractLLMProvider],
        sanitizer: Optional[DataSanitizer] = None,
        quota_manager: Optional[QuotaManager] = None,
        phase_routing: Optional[Dict[str, List[str]]] = None,
        cooldown_seconds: float = 300.0,
        failure_threshold: int = 3,
    ) -> None:
        self.providers: Dict[str, AbstractLLMProvider] = dict(providers)
        self.sanitizer: DataSanitizer = sanitizer or DataSanitizer()
        self.quota_manager: QuotaManager = quota_manager or QuotaManager()
        self.phase_routing: Dict[str, List[str]] = (
            dict(phase_routing) if phase_routing is not None else dict(DEFAULT_PHASE_ROUTING)
        )

        self.circuit_breakers: Dict[str, ProviderCircuitBreaker] = {
            name: ProviderCircuitBreaker(
                provider_name=name,
                failure_threshold=failure_threshold,
                cooldown_seconds=cooldown_seconds,
            )
            for name in self.providers
        }

        self._total_requests_today: int = 0
        self._total_fallbacks_today: int = 0

    def register_provider(
        self,
        provider: AbstractLLMProvider,
        cooldown_seconds: float = 300.0,
        failure_threshold: int = 3,
    ) -> None:
        """Dynamically add or override a provider."""
        self.providers[provider.name] = provider
        self.circuit_breakers[provider.name] = ProviderCircuitBreaker(
            provider_name=provider.name,
            failure_threshold=failure_threshold,
            cooldown_seconds=cooldown_seconds,
        )

    def resolve_chain(self, phase_id: Optional[str] = None, is_sensitive: bool = False) -> List[str]:
        """Resolve ordered provider candidates for a given phase and sensitivity status."""
        if is_sensitive:
            # Sensitive data must never leave local perimeter
            candidates = [p for p in ["ollama", "mock"] if p in self.providers]
            return candidates

        target_phase = phase_id or "*"
        chain = self.phase_routing.get(target_phase, self.phase_routing.get("*", []))

        # Filter to registered providers
        resolved = [p for p in chain if p in self.providers]

        # If mock provider exists and is not in chain, append as safety net
        if "mock" in self.providers and "mock" not in resolved:
            resolved.append("mock")

        return resolved

    async def complete(
        self,
        prompt_bundle: PromptBundle,
        phase_id: Optional[str] = None,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> ProviderCompletion:
        """Execute non-streaming completion with automatic fallback and border control."""
        # Check sensitivity
        combined_text = f"{prompt_bundle.system_prompt or ''}\n" + "\n".join(
            m.content for m in prompt_bundle.messages
        )
        if context:
            combined_text += f"\n{context}"

        is_sensitive = self.sanitizer.is_sensitive(combined_text)
        chain = self.resolve_chain(phase_id=phase_id, is_sensitive=is_sensitive)

        if is_sensitive and not chain:
            raise SensitiveDataLeakError(
                "Sensitive data detected in prompt/context; outbound cloud inference "
                "prohibited and no local provider (Ollama/Mock) is configured."
            )

        last_error: Optional[Exception] = None

        for provider_name in chain:
            provider = self.providers[provider_name]
            cb = self.circuit_breakers[provider_name]

            if not provider.is_available():
                continue

            if not await cb.can_proceed():
                continue

            if not self.quota_manager.check_quota(provider_name, estimated_tokens=max_tokens):
                continue

            try:
                completion = await provider.complete(
                    prompt_bundle=prompt_bundle,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                await cb.record_success()
                tokens_count = (
                    completion.tokens_used.total_tokens
                    if completion.tokens_used and completion.tokens_used.total_tokens
                    else 100
                )
                self.quota_manager.record_usage(provider_name, tokens_count)
                self._total_requests_today += 1
                return completion
            except Exception as exc:
                last_error = exc
                await cb.record_failure(exc)
                self._total_fallbacks_today += 1
                logger.warning(
                    f"[TALOS ROUTER] Provider {provider_name} failed during complete: {exc}. "
                    f"Falling back to next provider."
                )
                continue

        if is_sensitive:
            raise SensitiveDataLeakError(
                f"Sensitive data detected and local provider failed: {last_error}"
            )
        raise PoolExhaustedError(
            f"All available LLM providers in pool failed or exhausted. Last error: {last_error}"
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        phase_id: Optional[str] = None,
        context: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        on_fallback_reset: Optional[Callable[[], Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens with border control and mid-stream fallback (Ajuste 3)."""
        combined_text = f"{system_prompt}\n{user_prompt}"
        if context:
            combined_text += f"\n{context}"

        is_sensitive = self.sanitizer.is_sensitive(combined_text)
        chain = self.resolve_chain(phase_id=phase_id, is_sensitive=is_sensitive)

        if is_sensitive and not chain:
            raise SensitiveDataLeakError(
                "Sensitive data detected in prompt/context; outbound cloud inference "
                "prohibited and no local provider (Ollama/Mock) is configured."
            )

        last_error: Optional[Exception] = None

        for provider_name in chain:
            provider = self.providers[provider_name]
            cb = self.circuit_breakers[provider_name]

            if not provider.is_available():
                continue

            if not await cb.can_proceed():
                continue

            if not self.quota_manager.check_quota(provider_name, estimated_tokens=max_tokens):
                continue

            # Attempt stream with mid-stream error recovery
            buffer = ""
            tokens_emitted = 0
            try:
                gen = provider.stream(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                async for token in gen:
                    buffer += token
                    tokens_emitted += 1
                    yield token

                # If loop finishes cleanly without exception:
                await cb.record_success()
                self.quota_manager.record_usage(provider_name, tokens_emitted)
                self._total_requests_today += 1
                return
            except Exception as exc:
                last_error = exc
                await cb.record_failure(exc)
                self._total_fallbacks_today += 1
                logger.warning(
                    f"[TALOS ROUTER] Provider {provider_name} failed mid-stream after {tokens_emitted} tokens: {exc}. "
                    f"Discarding partial buffer and falling back to next provider."
                )
                buffer = ""  # Discard buffer cleanly
                if tokens_emitted > 0 and on_fallback_reset:
                    on_fallback_reset()
                continue

        if is_sensitive:
            raise SensitiveDataLeakError(
                f"Sensitive data detected and local provider failed: {last_error}"
            )
        raise PoolExhaustedError(
            f"All available LLM providers in pool failed or exhausted. Last error: {last_error}"
        )

    def get_health(self) -> Dict[str, Any]:
        """Return diagnostic health status for all providers and quotas (Ajuste 4)."""
        providers_status: Dict[str, Any] = {}
        for name, provider in self.providers.items():
            cb = self.circuit_breakers[name]
            quota_status = self.quota_manager.get_status(name)
            providers_status[name] = {
                "available": provider.is_available(),
                "state": cb.state.value,
                "daily_tokens_used": quota_status.get("tokens_used", 0),
                "daily_requests": quota_status.get("requests_count", 0),
                "daily_quota": quota_status.get("daily_limit"),
                "quota_remaining": quota_status.get("remaining_quota"),
                "saturated": quota_status.get("saturated", False),
                "last_failure": cb.last_failure,
            }

        # Overall health determination
        any_open = any(p["state"] == CircuitState.OPEN.value for p in providers_status.values())
        all_unavailable_or_open = all(
            (not p["available"]) or p["state"] == CircuitState.OPEN.value
            for p in providers_status.values()
        )

        if all_unavailable_or_open:
            status = "exhausted"
        elif any_open:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "providers": providers_status,
            "total_requests_today": self._total_requests_today,
            "total_fallbacks_today": self._total_fallbacks_today,
            "routing_matrix": self.phase_routing,
        }
