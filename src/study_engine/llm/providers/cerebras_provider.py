"""Cerebras Cloud Provider Adapter (Fase 5.9)."""

import os
from typing import Optional

from study_engine.llm.providers.openai_compatible import OpenAICompatibleProvider


class CerebrasProvider(OpenAICompatibleProvider):
    """Cerebras ultra-fast inference adapter (e.g. Qwen 2.5 72B / Llama 3.3 70B)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "llama3.3-70b",
        base_url: str = "https://api.cerebras.ai/v1",
        timeout: float = 15.0,
    ) -> None:
        key = api_key or os.environ.get("CEREBRAS_API_KEY", "")
        super().__init__(
            name="cerebras",
            default_model=default_model,
            base_url=base_url,
            api_key=key,
            timeout=timeout,
        )
