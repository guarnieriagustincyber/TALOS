"""Cloudflare Workers AI Provider Adapter (Fase 5.9)."""

import os
from typing import Optional

from study_engine.llm.providers.openai_compatible import OpenAICompatibleProvider


class CloudflareProvider(OpenAICompatibleProvider):
    """Cloudflare Workers AI adapter (e.g. @cf/meta/llama-3.2-3b-instruct)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        account_id: Optional[str] = None,
        default_model: str = "@cf/meta/llama-3.2-3b-instruct",
        base_url: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        key = api_key or os.environ.get("CLOUDFLARE_API_KEY", "")
        acc_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        self.account_id = acc_id

        if not base_url:
            if acc_id:
                url = f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/v1"
            else:
                url = "https://api.cloudflare.com/client/v4/accounts/unknown/ai/v1"
        else:
            url = base_url

        super().__init__(
            name="cloudflare",
            default_model=default_model,
            base_url=url,
            api_key=key,
            timeout=timeout,
        )

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.account_id and self.account_id.strip())
