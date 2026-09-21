"""OpenAI-compatible REST and streaming provider adapter without external SDKs (Fase 5.9 / Pilar 1)."""

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx

from study_engine.contracts.generation import TokenUsage
from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import ProviderCompletion
from study_engine.llm.providers.abstract_provider import AbstractLLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(AbstractLLMProvider):
    """Generic adapter for OpenAI-compatible inference APIs using httpx."""

    def __init__(
        self,
        name: str,
        default_model: str,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 15.0,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(name=name, default_model=default_model)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    def is_available(self) -> bool:
        """Check if provider has configured API credentials."""
        return bool(self.api_key and self.api_key.strip())

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    async def complete(
        self,
        prompt_bundle: PromptBundle,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> ProviderCompletion:
        """Execute full non-streaming completion."""
        if not self.is_available():
            raise RuntimeError(f"Provider {self.name} is not available (missing credentials).")

        endpoint = f"{self.base_url}/chat/completions"
        messages: List[Dict[str, str]] = []
        if prompt_bundle.system_prompt:
            messages.append({"role": "system", "content": prompt_bundle.system_prompt})
        for msg in prompt_bundle.messages:
            messages.append({
                "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                "content": msg.content,
            })

        payload = {
            "model": self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        t0 = time.time()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(endpoint, json=payload, headers=self._get_headers())
            elapsed_ms = (time.time() - t0) * 1000.0

            if response.status_code == 429:
                raise RuntimeError(f"Provider {self.name} rate limit exceeded (HTTP 429)")
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Provider {self.name} HTTP error {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            choice = data.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content", "") or " "
            usage_data = data.get("usage", {})

            return ProviderCompletion(
                text=text,
                latency_ms=elapsed_ms,
                model=data.get("model", self.default_model),
                tokens_used=TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                ),
            )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens using Server-Sent Events (SSE)."""
        if not self.is_available():
            raise RuntimeError(f"Provider {self.name} is not available (missing credentials).")

        endpoint = f"{self.base_url}/chat/completions"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        payload = {
            "model": self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                if response.status_code == 429:
                    raise RuntimeError(f"Provider {self.name} rate limit exceeded (HTTP 429)")
                if response.status_code >= 400:
                    body = await response.aread()
                    raise RuntimeError(
                        f"Provider {self.name} HTTP error {response.status_code}: {body.decode('utf-8', errors='ignore')[:200]}"
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data:"):
                        raw_data = line[len("data:"):].strip()
                        if raw_data == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(raw_data)
                            choices = chunk_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.debug(f"Failed to parse SSE JSON chunk from {self.name}: {raw_data}")
                            continue
