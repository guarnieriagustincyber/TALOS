"""Ollama Local Provider Adapter (Fase 5.9 / Fase 5.5)."""

import os
from typing import Optional

from study_engine.llm.providers.openai_compatible import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    """Local offline inference adapter via Ollama (e.g. Qwen 2.5 2B / Llama 3.2)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        host = base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        host = host.rstrip("/")
        if not host.endswith("/v1"):
            api_base = f"{host}/v1"
        else:
            api_base = host

        model = default_model or os.environ.get("OLLAMA_MODEL", "qwen2.5:2b")
        super().__init__(
            name="ollama",
            default_model=model,
            base_url=api_base,
            api_key="ollama",  # Non-empty placeholder for local daemon
            timeout=timeout,
        )

    def is_available(self) -> bool:
        """Local Ollama is considered available unless explicitly disabled via env."""
        disabled = os.environ.get("TALOS_DISABLE_OLLAMA", "0").lower() in ("1", "true", "yes")
        return not disabled
