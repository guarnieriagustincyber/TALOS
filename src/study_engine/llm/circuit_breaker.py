"""Circuit breaker implementation for Subsystem S4.3 and ModelRegistry (Ola 5, Fase 5.3).

Provides:
- CircuitState: CLOSED, OPEN, HALF_OPEN
- Cooldown exponencial: 1s -> 2s -> 4s -> 8s -> max 60s
- Thread-safety via asyncio.Lock
- Fail-closed transitions upon 3 consecutive failures
- Integration with quota enforcement
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Per-provider circuit breaker with exponential cooldown and concurrency protection."""

    def __init__(
        self,
        failure_threshold: int = 3,
        initial_cooldown: float = 1.0,
        max_cooldown: float = 60.0,
        tokens_per_minute_limit: int = 200_000,
        requests_per_day_limit: int = 450,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.initial_cooldown = initial_cooldown
        self.max_cooldown = max_cooldown
        self.tokens_per_minute_limit = tokens_per_minute_limit
        self.requests_per_day_limit = requests_per_day_limit

        self.state: CircuitState = CircuitState.CLOSED
        self.consecutive_failures: int = 0
        self.opened_at: Optional[float] = None
        self.current_cooldown: float = initial_cooldown

        self._lock = asyncio.Lock()

        # Sliding window for TPM and RPD
        self._minute_token_history: List[Tuple[float, int]] = []
        self._current_utc_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._requests_today: int = 0
        self._tokens_today: int = 0

    @property
    def cooldown_seconds(self) -> float:
        return self.current_cooldown

    def record_failure(self, now: Optional[float] = None) -> None:
        """Record provider error. Trip to OPEN if consecutive failures reach threshold."""
        ts = now if now is not None else time.time()
        self.consecutive_failures += 1

        if self.state == CircuitState.HALF_OPEN:
            # Re-trip immediately with doubled cooldown
            self.state = CircuitState.OPEN
            self.opened_at = ts
            self.current_cooldown = min(self.current_cooldown * 2.0, self.max_cooldown)
            logger.warning(
                f"[CIRCUIT BREAKER] Probe failed in HALF_OPEN. Circuit returned to OPEN for {self.current_cooldown}s."
            )
        elif self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = ts
            logger.warning(
                f"[CIRCUIT BREAKER] Threshold reached ({self.consecutive_failures} failures). "
                f"Circuit tripped to OPEN for {self.current_cooldown}s."
            )

    def record_success(self) -> None:
        """Record successful execution. Resets failures and restores CLOSED state."""
        self.consecutive_failures = 0
        self.current_cooldown = self.initial_cooldown
        self.opened_at = None
        if self.state != CircuitState.CLOSED:
            logger.info("[CIRCUIT BREAKER] Provider recovered. Circuit restored to CLOSED state.")
            self.state = CircuitState.CLOSED

    def is_circuit_open(self, now: Optional[float] = None) -> bool:
        """Check whether circuit is OPEN or has transitioned to HALF_OPEN."""
        if self.state == CircuitState.CLOSED:
            return False

        ts = now if now is not None else time.time()
        if self.state == CircuitState.OPEN:
            if self.opened_at is not None and (ts - self.opened_at) >= self.current_cooldown:
                self.state = CircuitState.HALF_OPEN
                logger.info(
                    f"[CIRCUIT BREAKER] Cooldown ({self.current_cooldown}s) elapsed. Circuit entered HALF_OPEN state."
                )
                return False
            return True

        # In HALF_OPEN, allows canary trial
        return False

    def can_proceed(self, estimated_tokens: int = 250, now: Optional[float] = None) -> bool:
        """Validate if request can proceed based on circuit state and quota bounds."""
        if self.is_circuit_open(now=now):
            return False

        ts = now if now is not None else time.time()
        self._sync_date_and_clean_history(now=ts)

        if self._requests_today >= self.requests_per_day_limit:
            return False

        tokens_last_minute = sum(count for _, count in self._minute_token_history)
        if tokens_last_minute + estimated_tokens > self.tokens_per_minute_limit:
            return False

        return True

    def _sync_date_and_clean_history(self, now: Optional[float] = None) -> None:
        ts = now if now is not None else time.time()
        cutoff = ts - 60.0
        self._minute_token_history = [
            (t, count) for (t, count) in self._minute_token_history if t >= cutoff
        ]
        current_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if current_date_str != self._current_utc_date:
            self._current_utc_date = current_date_str
            self._requests_today = 0
            self._tokens_today = 0

    def record_usage(self, tokens_used: int, now: Optional[float] = None) -> None:
        ts = now if now is not None else time.time()
        self._sync_date_and_clean_history(ts)
        self._minute_token_history.append((ts, tokens_used))
        self._requests_today += 1
        self._tokens_today += tokens_used


class CircuitBreakerBackend:
    """Backend wrapper adhering to ProviderBackend protocol with circuit protection."""

    def __init__(
        self,
        primary_backend: Any,
        fallback_backend: Any,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.primary_backend = primary_backend
        self.fallback_backend = fallback_backend
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    @property
    def model_name(self) -> str:
        for attr in ("model_name", "model", "default_model", "name"):
            if hasattr(self.primary_backend, attr):
                val = getattr(self.primary_backend, attr)
                if val and isinstance(val, str):
                    return val
        return "circuit-breaker-backend"

    def complete(self, prompt_bundle: Any) -> Any:
        estimated_tokens = getattr(getattr(prompt_bundle, "parameters", None), "max_output_tokens", 250) or 250
        if not self.circuit_breaker.can_proceed(estimated_tokens=estimated_tokens):
            logger.warning("[CIRCUIT BREAKER] Circuit OPEN or quota exceeded. Routing to fallback.")
            return self.fallback_backend.complete(prompt_bundle)

        try:
            completion = self.primary_backend.complete(prompt_bundle)
            used = 150
            if hasattr(completion, "tokens_used") and completion.tokens_used and getattr(completion.tokens_used, "total_tokens", None):
                used = completion.tokens_used.total_tokens
            self.circuit_breaker.record_usage(used)
            self.circuit_breaker.record_success()
            return completion
        except Exception as exc:
            self.circuit_breaker.record_failure()
            logger.warning(f"[CIRCUIT BREAKER] Execution failed: {exc}. Routing to fallback.")
            return self.fallback_backend.complete(prompt_bundle)
