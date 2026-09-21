"""LLM integration package for Subsystem S4.3 and TalosLLMPool (Fase 5.9)."""

from study_engine.llm.backends import (
    HttpOpenAIBackend,
    MockBackend,
    ProviderBackend,
    ProviderCompletion,
    RuleBasedBackend,
)
from study_engine.llm.client import LLMClient
from study_engine.llm.exceptions import (
    LLMBackendError,
    LLMConnectionError,
    LLMError,
    LLMTimeoutError,
)
from study_engine.llm.quota_manager import QuotaManager
from study_engine.llm.router import (
    CircuitState,
    PoolExhaustedError,
    ProviderCircuitBreaker,
    TalosLLMRouter,
)
from study_engine.llm.sanitizer import DataSanitizer, SensitiveDataLeakError

__all__ = [
    "HttpOpenAIBackend",
    "LLMBackendError",
    "LLMClient",
    "LLMConnectionError",
    "LLMError",
    "LLMTimeoutError",
    "MockBackend",
    "ProviderBackend",
    "ProviderCompletion",
    "RuleBasedBackend",
    "TalosLLMRouter",
    "ProviderCircuitBreaker",
    "CircuitState",
    "PoolExhaustedError",
    "DataSanitizer",
    "SensitiveDataLeakError",
    "QuotaManager",
]
