"""Model Registry with dynamic health-scoring and circuit breaker management (Ola 5, Fase 5.3).

INVARIANTS:
1. INV-W5-3: ModelRegistry NUNCA decide KCs, transiciones pedagógicas ni maestría de BKT.
2. Dynamic Selection: Providers are selected dynamically based on health scores (composite_score),
   NOT blind hardcoded fallbacks.
3. Configurable Hierarchy: Default priority rankings are external configuration, not hardcoded logic.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple

from study_engine.llm.abstract_provider import AbstractLLMProvider, ProviderHealth
from study_engine.llm.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


DEFAULT_PROVIDER_HIERARCHY: Dict[str, List[str]] = {
    "NORMAL": ["groq", "cerebras", "gemini"],
    "DEEP": ["gemini", "groq", "xkiro", "nvidia"],
    "GLOBAL": ["xkiro", "gemini", "nvidia", "openrouter"],
    "MULTIMODAL": ["openrouter", "gemini"],
}


class ModelRegistry:
    """Registry coordinating provider instances, capability discovery, circuit breakers, and health scores."""

    def __init__(
        self,
        hierarchy_config: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        self.hierarchy_config = hierarchy_config or DEFAULT_PROVIDER_HIERARCHY
        self._providers: Dict[str, AbstractLLMProvider] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._health_cache: Dict[str, ProviderHealth] = {}

    def register_provider(
        self,
        provider: AbstractLLMProvider,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        """Register a provider instance and associate its dedicated CircuitBreaker."""
        pid = provider.provider_id
        self._providers[pid] = provider
        self._circuit_breakers[pid] = circuit_breaker or CircuitBreaker()
        self._health_cache[pid] = provider.health_check()
        logger.info("Registered provider in ModelRegistry: %s", pid)

    def get_provider(self, provider_id: str) -> Optional[AbstractLLMProvider]:
        return self._providers.get(provider_id)

    def get_circuit_breaker(self, provider_id: str) -> Optional[CircuitBreaker]:
        return self._circuit_breakers.get(provider_id)

    def get_provider_health(self, provider_id: str) -> Optional[ProviderHealth]:
        return self._health_cache.get(provider_id)

    def record_call_result(
        self,
        provider_id: str,
        success: bool,
        latency_ms: float = 0.0,
        is_429: bool = False,
    ) -> None:
        """Update provider health score and circuit breaker following an invocation."""
        cb = self._circuit_breakers.get(provider_id)
        health = self._health_cache.get(provider_id)

        now = datetime.now(timezone.utc)
        if success:
            if cb:
                cb.record_success()
            if health:
                health.last_success = now
                health.rate_limit_429_count = max(0, health.rate_limit_429_count - 1)
                # Exponential moving average for latency
                health.avg_latency_ms = (health.avg_latency_ms * 0.7) + (latency_ms * 0.3)
                health.availability = min(1.0, health.availability + 0.05)
                health.is_healthy = True
        else:
            if cb:
                cb.record_failure()
            if health:
                health.last_failure = now
                if is_429:
                    health.rate_limit_429_count += 1
                health.availability = max(0.0, health.availability - 0.2)
                if cb and cb.is_circuit_open():
                    health.is_healthy = False

    def select_best_provider(
        self,
        *,
        depth: str = "NORMAL",
        requires_multimodal: bool = False,
        min_context_tokens: int = 4000,
    ) -> Tuple[AbstractLLMProvider, ProviderHealth]:
        """Select highest composite scoring eligible provider.

        Eligibility filters:
        1. Context capacity >= min_context_tokens
        2. Multimodal support if requires_multimodal is True
        3. Circuit breaker must NOT be OPEN
        4. Healthy availability > 0.0
        """
        # Determine candidate list based on hierarchy config
        configured_candidates = self.hierarchy_config.get("MULTIMODAL" if requires_multimodal else depth, [])
        all_registered = list(self._providers.keys())
        configured_set = set(configured_candidates)
        fallback_ids = [k for k in all_registered if k not in configured_set]

        def _evaluate_candidates(ids: List[str]) -> List[Tuple[float, AbstractLLMProvider, ProviderHealth]]:
            results: List[Tuple[float, AbstractLLMProvider, ProviderHealth]] = []
            for pid in ids:
                prov = self._providers.get(pid)
                if not prov:
                    continue

                # 1. Check multimodal requirement
                if requires_multimodal and not prov.supports_multimodal():
                    continue

                # 2. Check context tokens
                if prov.max_context_tokens() < min_context_tokens:
                    continue

                # 3. Check circuit breaker state
                cb = self._circuit_breakers.get(pid)
                if cb and cb.is_circuit_open():
                    continue

                # 4. Check health score
                health = self._health_cache.get(pid) or prov.health_check()
                if not health.is_healthy or health.availability <= 0.0:
                    continue

                # Compute composite score
                score = health.composite_score
                results.append((score, prov, health))
            return results

        eligible = _evaluate_candidates(configured_candidates)
        if not eligible:
            eligible = _evaluate_candidates(fallback_ids)

        if not eligible:
            raise RuntimeError(
                f"No healthy provider available matching requirements: "
                f"depth={depth}, multimodal={requires_multimodal}, min_tokens={min_context_tokens}."
            )

        # Sort descending by composite score
        eligible.sort(key=lambda x: x[0], reverse=True)
        best_score, best_provider, best_health = eligible[0]

        logger.debug(
            "ModelRegistry selected %s with composite score %.4f",
            best_provider.provider_id,
            best_score,
        )
        return best_provider, best_health
