"""NVIDIA NIM Provider Adapter (DeepSeek R1 / Fase 5.9)."""

import os
from typing import Optional

from study_engine.llm.providers.openai_compatible import OpenAICompatibleProvider


class NvidiaProvider(OpenAICompatibleProvider):
    """NVIDIA NIM inference adapter (e.g. DeepSeek R1 for reasoning and code)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "deepseek-ai/deepseek-r1",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        timeout: float = 30.0,
    ) -> None:
        key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        super().__init__(
            name="nvidia",
            default_model=default_model,
            base_url=base_url,
            api_key=key,
            timeout=timeout,
        )
