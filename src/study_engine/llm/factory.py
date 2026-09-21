"""Authoritative LLM Provider Factory and Externalized Pricing for Hito 7.2.

This module provides:
1. LLMProviderFactory: Modular factory for instantiating live ProviderBackend instances
   (Groq, Gemini, OpenRouter) or hermetic test backends (Mock, Replay).
2. LLMPricingTable: Externalized pricing table loader and cost calculator
   (Refinement 1 from Tech Lead dictamen).
3. Explicit CI Fallback: When external API keys are unavailable, the factory
   transparently falls back to ReplayMockBackend, ensuring 100% offline reproducibility
   and zero network flakiness in automated testing and CI pipelines
   (Refinement 3 from Tech Lead dictamen).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional, Tuple, cast
import httpx
from pydantic import BaseModel, ConfigDict, Field

from study_engine.config import settings
from study_engine.contracts.generation import TokenUsage
from study_engine.llm.backends import (
    HttpOpenAIBackend,
    MockBackend,
    ProviderBackend,
    ReplayMockBackend,
)
from study_engine.llm.client import LLMClient
from study_engine.llm.exceptions import LLMConnectionError

logger = logging.getLogger(__name__)

ProviderType = Literal["groq", "gemini", "nvidia", "openrouter", "ollama", "xkiro", "mock", "replay"]


class ProviderSpec(BaseModel):
    """Immutable registry entry describing an external LLM provider.

    A declarative row in the provider registry table. No provider-specific
    branching lives in the factory; the registry fully drives instantiation
    and rotation priority.
    """

    model_config = ConfigDict(frozen=True)

    provider_type: str = Field(..., description="Provider key (groq, nvidia, ...).")
    base_url: str = Field(..., description="OpenAI-compatible endpoint base URL.")
    default_model: str = Field(..., description="Default model identifier.")
    api_key_env: str = Field(..., description="Environment variable holding the API key.")
    priority: int = Field(..., ge=0, description="Rotation priority (lower = preferred first).")


# Standard authoritative endpoints and default models.
# Single source of truth: PROVIDER_DEFAULTS below is a derived view kept for
# backward compatibility with resolve_api_key and existing callers.
PROVIDER_REGISTRY: Dict[str, ProviderSpec] = {
    "groq": ProviderSpec(
        provider_type="groq",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        api_key_env="GROQ_API_KEY",
        priority=1,
    ),
    "gemini": ProviderSpec(
        provider_type="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-3.1-flash-lite",
        api_key_env="GEMINI_API_KEY",
        priority=2,
    ),
    "nvidia": ProviderSpec(
        provider_type="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        default_model="deepseek-ai/deepseek-v4-flash",
        api_key_env="NVIDIA_API_KEY",
        priority=3,
    ),
    "openrouter": ProviderSpec(
        provider_type="openrouter",
        base_url="https://openrouter.ai/api/v1",
        default_model="google/gemini-2.5-flash-lite",
        api_key_env="OPENROUTER_API_KEY",
        priority=4,
    ),
    "ollama": ProviderSpec(
        provider_type="ollama",
        base_url="http://localhost:11434/v1",
        default_model="qwen3.5:2b",
        api_key_env="",  # local: no API key required
        priority=5,
    ),
    "xkiro": ProviderSpec(
        provider_type="xkiro",
        base_url="https://api.xkiro.com/v1",
        default_model="qwen/qwen3.8-max:free",
        api_key_env="XKIRO_API_KEY",
        priority=6,
    ),
}

# Legacy view: {provider: {base_url, default_model, env_var}} for callers that
# still read PROVIDER_DEFAULTS directly. Derived from the registry.
PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    name: {
        "base_url": spec.base_url,
        "default_model": spec.default_model,
        "env_var": spec.api_key_env,
    }
    for name, spec in PROVIDER_REGISTRY.items()
}


class ProviderConfig(BaseModel):
    """Configuration contract for LLM provider instantiations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider_type: ProviderType = Field(
        default="groq", description="Authoritative provider type"
    )
    model_name: Optional[str] = Field(
        default=None, description="Model identifier override"
    )
    api_key: Optional[str] = Field(
        default=None, description="Explicit API key override"
    )
    base_url: Optional[str] = Field(
        default=None, description="Endpoint base URL override"
    )
    timeout_seconds: float = Field(
        default=10.0, ge=1.0, description="Read/execution timeout SLA"
    )
    connect_timeout_seconds: float = Field(
        default=5.0, ge=1.0, description="Connection timeout SLA"
    )
    max_retries: int = Field(
        default=1, ge=0, le=5, description="Maximum retry attempts on 429/503"
    )
    fallback_to_mock_if_missing_key: bool = Field(
        default=True,
        description="Whether to switch to ReplayMockBackend in CI/offline mode",
    )
    fixture_path: Optional[Path] = Field(
        default=None, description="Optional path to replay fixtures JSON"
    )
    pricing_path: Optional[Path] = Field(
        default=None, description="Optional path to llm_pricing.json"
    )
    custom_client: Optional[httpx.Client] = Field(
        default=None, description="Optional injected httpx Client (e.g. MockTransport)"
    )


class LLMPricingTable:
    """Authoritative externalized pricing calculator (Refinement 1).

    Loads pricing rates per 1,000 tokens from data/config/llm_pricing.json.
    Guarantees no hardcoded pricing figures in application code.
    """

    DEFAULT_CONFIG_PATH = (
        Path(__file__).resolve().parents[3] / "data" / "config" / "llm_pricing.json"
    )

    def __init__(self, pricing_path: Optional[Path] = None) -> None:
        self.pricing_path = pricing_path or self.DEFAULT_CONFIG_PATH
        self.rates: Dict[str, Dict[str, Dict[str, float]]] = {}
        self._load_pricing()

    def _load_pricing(self) -> None:
        if self.pricing_path.exists():
            try:
                with open(self.pricing_path, "r", encoding="utf-8") as f:
                    self.rates = json.load(f)
            except Exception as exc:
                logger.warning(
                    f"Failed to read pricing table at {self.pricing_path}: {exc}. Using fallback zero rates."
                )
                self.rates = {}
        else:
            logger.warning(
                f"Pricing table file {self.pricing_path} does not exist. Using fallback zero rates."
            )
            self.rates = {}

    def get_rate(self, provider: str, model: str) -> Tuple[float, float]:
        """Return (input_rate_per_1k, output_rate_per_1k) for provider and model."""
        prov_rates = self.rates.get(provider.lower(), {})
        if model in prov_rates:
            model_info = prov_rates[model]
            return (
                float(model_info.get("input_per_1k_tokens", 0.0)),
                float(model_info.get("output_per_1k_tokens", 0.0)),
            )
        # Check default entry
        if "default" in prov_rates:
            def_info = prov_rates["default"]
            return (
                float(def_info.get("input_per_1k_tokens", 0.0)),
                float(def_info.get("output_per_1k_tokens", 0.0)),
            )
        return (0.0, 0.0)

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Compute estimated USD cost based on token counts."""
        input_rate, output_rate = self.get_rate(provider, model)
        cost_input = (prompt_tokens / 1000.0) * input_rate
        cost_output = (completion_tokens / 1000.0) * output_rate
        return round(cost_input + cost_output, 7)


class LLMProviderFactory:
    """Authoritative factory for constructing modular LLM generation backends.

    ARCHITECTURAL BEHAVIOR & CI GUARANTEE (Refinement 3):
    - Production: Inspects environment variables for GROQ_API_KEY, GEMINI_API_KEY,
      or STUDY_ENGINE_LLM_API_KEY (and optional local .env).
    - CI / Automated Testing: If no API key is detected and fallback_to_mock_if_missing_key
      is True (default), it logs an informational warning and instantiates ReplayMockBackend.
    - Determinism Invariant: The Study Loop is fully operational and deterministic
      regardless of external network connectivity or cloud provider availability.
    """

    def __init__(self, pricing_table: Optional[LLMPricingTable] = None) -> None:
        self.pricing_table = pricing_table or LLMPricingTable()

    @staticmethod
    def _read_env_file(env_file_path: Path) -> Dict[str, str]:
        """Simple, zero-dependency parser for key=value .env files."""
        env_vars: Dict[str, str] = {}
        if not env_file_path.exists():
            return env_vars
        try:
            with open(env_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    if "=" in stripped:
                        key, val = stripped.split("=", 1)
                        clean_key = key.strip()
                        clean_val = val.strip().strip("'\"")
                        env_vars[clean_key] = clean_val
        except Exception as exc:
            logger.debug(f"Could not read .env at {env_file_path}: {exc}")
        return env_vars

    def resolve_api_key(
        self,
        provider_type: ProviderType,
        explicit_key: Optional[str] = None,
    ) -> Optional[str]:
        """Resolve API key following strict precedence: explicit -> settings -> env."""
        if explicit_key and explicit_key.strip():
            return explicit_key.strip()

        # Check global generic environment variable
        global_key = os.environ.get("STUDY_ENGINE_LLM_API_KEY")
        if global_key and global_key.strip():
            return global_key.strip()

        # Check central Settings instance
        provider_key_map = {
            "gemini": settings.gemini_api_key,
            "groq": settings.groq_api_key,
            "nvidia": settings.nvidia_api_key,
            "openrouter": settings.openrouter_api_key,
        }
        mapped_key = provider_key_map.get(provider_type)
        if mapped_key and mapped_key.strip():
            return mapped_key.strip()

        # Check provider-specific environment variable as fallback
        target_var = PROVIDER_DEFAULTS.get(provider_type, {}).get("env_var")
        if target_var:
            prov_key = os.environ.get(target_var)
            if prov_key and prov_key.strip():
                return prov_key.strip()

        return None

    def create_provider(
        self, config: Optional[ProviderConfig] = None
    ) -> ProviderBackend:
        """Create and return a configured ProviderBackend instance.

        Dispatches via the strategy table ``_BACKEND_BUILDERS`` keyed by
        provider type. External HTTP providers are resolved through the
        registry table. For priority-based rotation across providers use
        ``create_rotating_provider`` instead.
        """
        cfg = self._resolve_config(config)

        builder = _BACKEND_BUILDERS.get(cfg.provider_type)
        if builder is None:
            raise ValueError(f"Unsupported provider type: {cfg.provider_type}")
        return builder(self, cfg)

    def _resolve_config(self, config: Optional[ProviderConfig]) -> ProviderConfig:
        """Normalize the effective ProviderConfig (env overrides + auto-detect)."""
        cfg = config or ProviderConfig()

        env_provider = os.getenv("STUDY_ENGINE_LLM_PROVIDER")
        if env_provider and config is None:
            clean_p = env_provider.strip().lower()
            if clean_p in _BACKEND_BUILDERS:
                cfg = cfg.model_copy(update={"provider_type": clean_p})

        # Auto-detect: default groq -> gemini if only GEMINI_API_KEY present
        if config is None and cfg.provider_type == "groq" and not env_provider:
            if not self.resolve_api_key("groq") and self.resolve_api_key("gemini"):
                cfg = cfg.model_copy(update={"provider_type": "gemini"})

        return cfg

    @staticmethod
    def _build_http_backend(
        factory: "LLMProviderFactory", cfg: ProviderConfig, spec: ProviderSpec
    ) -> ProviderBackend:
        """Instantiate a live external HTTP backend from a registry spec."""
        resolved_key = factory.resolve_api_key(
            cfg.provider_type, explicit_key=cfg.api_key
        )

        if not resolved_key:
            if not spec.api_key_env:
                # Local providers (e.g. Ollama) need no key; use a sentinel
                # that is never transmitted as a bearer token.
                resolved_key = "local"
            elif cfg.fallback_to_mock_if_missing_key:
                factory._warn_missing_key(cfg.provider_type)
                return ReplayMockBackend(replay_file=cfg.fixture_path)
            else:
                raise LLMConnectionError(
                    f"Missing API key for provider '{cfg.provider_type}'. "
                    f"Set {spec.api_key_env} or STUDY_ENGINE_LLM_API_KEY."
                )

        base_url = cfg.base_url or spec.base_url
        model = cfg.model_name or spec.default_model
        model = os.getenv("STUDY_ENGINE_LLM_MODEL") or model
        timeout, connect_timeout = factory._resolve_timeouts(cfg)

        if cfg.provider_type == "gemini":
            from study_engine.llm.gemini_backend import GeminiBackend

            return GeminiBackend(
                base_url=base_url,
                api_key=resolved_key,
                model_name=model,
                timeout_seconds=timeout,
                connect_timeout_seconds=connect_timeout,
                client=factory._build_client(cfg, timeout, connect_timeout),
            )

        return HttpOpenAIBackend(
            base_url=base_url,
            api_key=resolved_key,
            default_model=model,
            timeout_seconds=cfg.timeout_seconds,
            client=factory._build_client(cfg, timeout, connect_timeout),
        )

    @staticmethod
    def _resolve_timeouts(cfg: ProviderConfig) -> Tuple[float, float]:
        """Compute effective timeouts, honoring provider-specific overrides."""
        timeout = cfg.timeout_seconds
        if cfg.provider_type == "gemini":
            env_timeout = os.getenv("STUDY_ENGINE_GEMINI_TIMEOUT")
            if env_timeout:
                try:
                    timeout = float(env_timeout)
                except ValueError:
                    logger.warning(
                        f"Invalid STUDY_ENGINE_GEMINI_TIMEOUT='{env_timeout}' "
                        f"– using default {cfg.timeout_seconds}s"
                    )
            if timeout <= 15.0:
                timeout = 35.0
        return timeout, cfg.connect_timeout_seconds

    @staticmethod
    def _build_client(
        cfg: ProviderConfig, timeout: float, connect_timeout: float
    ) -> httpx.Client:
        """Return injected or newly-built httpx client with effective timeouts."""
        if cfg.custom_client is not None:
            return cfg.custom_client
        return httpx.Client(timeout=httpx.Timeout(timeout, connect=connect_timeout))

    @staticmethod
    def _warn_missing_key(provider_type: str) -> None:
        logger.warning(
            f"[CI/OFFLINE FALLBACK] No API key detected for provider '{provider_type}'. "
            "Conmuting to hermetic ReplayMockBackend to preserve test reproducibility."
        )

    def _build_rotation(self, cfg: ProviderConfig) -> ProviderBackend:
        """Compose a priority-ordered rotation chain of live providers.

        Reuses the existing CircuitBreakerBackend: each provider is wrapped,
        and its fallback is the next provider in priority order, terminating
        at a hermetic ReplayMockBackend. No bespoke fallback logic.
        """
        from study_engine.llm.circuit_breaker import CircuitBreakerBackend

        ordered = sorted(
            PROVIDER_REGISTRY.values(), key=lambda s: s.priority
        )
        ordered = [
            spec for spec in ordered
            if self.resolve_api_key(cast(ProviderType, spec.provider_type))
            or not spec.api_key_env
        ]

        tail: ProviderBackend = ReplayMockBackend(replay_file=cfg.fixture_path)
        for spec in reversed(ordered):
            primary = self._build_http_backend(self, cfg, spec)
            tail = CircuitBreakerBackend(primary_backend=primary, fallback_backend=tail)
        return tail

    def create_rotating_provider(
        self, config: Optional[ProviderConfig] = None
    ) -> ProviderBackend:
        """Create a priority-ordered rotating provider chain.

        Returns a CircuitBreakerBackend chain covering every provider with a
        resolvable key (or a local provider such as Ollama), ordered by the
        registry ``priority``. If a provider's circuit opens, the existing
        CircuitBreakerBackend falls through to the next in priority order,
        terminating at a hermetic ReplayMockBackend.
        """
        return self._build_rotation(config or ProviderConfig())

    def create_client(self, config: Optional[ProviderConfig] = None) -> LLMClient:
        """Create LLMClient generator adapter around configured provider."""
        backend = self.create_provider(config)
        return LLMClient(backend=backend)


# ---------------------------------------------------------------------------
# Strategy dispatch table for create_provider.
# Declarative: adding a provider only requires a PROVIDER_REGISTRY row; the
# HTTP builders are shared. No if/elif chain in the factory itself.
# ---------------------------------------------------------------------------
def _build_mock_backend(factory: LLMProviderFactory, cfg: ProviderConfig) -> ProviderBackend:
    """Construct a hermetic MockBackend (deterministic test backend)."""
    return MockBackend()


def _build_replay_backend(factory: LLMProviderFactory, cfg: ProviderConfig) -> ProviderBackend:
    """Construct a ReplayMockBackend from fixtures (offline/CI)."""
    return ReplayMockBackend(replay_file=cfg.fixture_path)


def _build_http_registry_backend(factory: LLMProviderFactory, cfg: ProviderConfig) -> ProviderBackend:
    """Construct an external HTTP backend from its registry spec."""
    spec = PROVIDER_REGISTRY[cfg.provider_type]
    return factory._build_http_backend(factory, cfg, spec)


# Typed strategy builder: (factory, config) -> ProviderBackend
ProviderBuilder = Callable[[LLMProviderFactory, ProviderConfig], ProviderBackend]

_BACKEND_BUILDERS: Dict[str, ProviderBuilder] = {
    "mock": _build_mock_backend,
    "replay": _build_replay_backend,
    "groq": _build_http_registry_backend,
    "gemini": _build_http_registry_backend,
    "nvidia": _build_http_registry_backend,
    "openrouter": _build_http_registry_backend,
    "ollama": _build_http_registry_backend,
}
