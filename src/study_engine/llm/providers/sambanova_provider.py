"""SambaNova Cloud Provider Adapter (Fase 5.9)."""

import os
from typing import Optional

from study_engine.llm.providers.openai_compatible import OpenAICompatibleProvider


class SambaNovaProvider(OpenAICompatibleProvider):
    """SambaNova Systems inference adapter (e.g. Llama 3.3 70B / DeepSeek v3)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "Meta-Llama-3.3-70B-Instruct",
        base_url: str = "https://api.sambanova.ai/v1",
        timeout: float = 15.0,
    ) -> None:
        key = api_key or os.environ.get("SAMBANOVA_API_KEY", "")
        super().__init__(
            name="sambanova",
            default_model=default_model,
            base_url=base_url,
            api_key=key,
            timeout=timeout,
        )
