"""Google Gemini Backend for Subsystem S4.3.

Provides a robust, sovereign provider backend communicating with Google's
OpenAI-compatible Generative Language API endpoint:
https://generativelanguage.googleapis.com/v1beta/openai/chat/completions

Features:
- Native resolution of GEMINI_API_KEY from environment or .env.
- Exponential backoff with jitter on HTTP 429 (rate-limiting) and 503 errors.
- Automatic graceful fallback/alias resolution for deprecated models
  (e.g., gemini-2.0-flash-lite -> gemini-3.5-flash-lite per Google Generative AI deprecation notice).
- Full compliance with ProviderBackend protocol and BaseContract guarantees.
"""

import json
import logging
import os
from pathlib import Path
import random
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from study_engine.config import settings
from study_engine.contracts.generation import TokenUsage
from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import (
    HttpOpenAIBackend,
    ProviderBackend,
    ProviderCompletion,
)
from study_engine.llm.exceptions import (
    LLMBackendError,
    LLMConnectionError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
ACTIVE_FALLBACK_MODEL = "gemini-3.5-flash-lite"

# Map deprecated/retired Google models directly to active equivalents
MODEL_ALIAS_MAP = {
    "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",
    "gemini-3.6-flash": "gemini-3.6-flash",
    "gemini-2.0-flash-lite": "gemini-3.5-flash-lite",
    "gemini-2.0-flash": "gemini-3.5-flash-lite",
    "gemini-1.5-flash": "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite": "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
    "gemini-2.5-flash": "gemini-3.5-flash-lite",
}


class GeminiBackend(ProviderBackend):
    """Authoritative Google Gemini execution backend via OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_GEMINI_MODEL,
        base_url: str = GEMINI_OPENAI_BASE_URL,
        timeout_seconds: float = 45.0,
        connect_timeout_seconds: float = 5.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._connect_timeout_seconds = connect_timeout_seconds
        self._api_key = self._resolve_api_key(api_key)

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            timeout = httpx.Timeout(
                timeout=self._timeout_seconds,
                connect=self._connect_timeout_seconds,
            )
            self._client = httpx.Client(timeout=timeout)
            self._owns_client = True

    @staticmethod
    def _resolve_api_key(explicit_key: Optional[str]) -> str:
        """Resolve GEMINI_API_KEY from explicit arg, global env, or settings."""
        if explicit_key and explicit_key.strip():
            return explicit_key.strip()

        if settings.gemini_api_key:
            return settings.gemini_api_key.strip()

        global_key = os.environ.get("STUDY_ENGINE_LLM_API_KEY")
        if global_key and global_key.strip():
            return global_key.strip()

        return ""

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def model_name(self) -> str:
        return self._model_name

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        """Execute chat completion against Gemini's OpenAI-compatible endpoint."""
        if not self._api_key:
            raise LLMConnectionError(
                "No GEMINI_API_KEY available. Set GEMINI_API_KEY or configure .env."
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        # 1. Assemble messages
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": prompt_bundle.system_prompt}
        ]
        for m in prompt_bundle.messages:
            messages.append({"role": m.role.value, "content": m.content})

        raw_model = prompt_bundle.parameters.suggested_model or self._model_name
        target_model = MODEL_ALIAS_MAP.get(raw_model, raw_model)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": prompt_bundle.parameters.temperature,
            "max_tokens": prompt_bundle.parameters.max_output_tokens,
        }
        if prompt_bundle.parameters.stop_sequences:
            payload["stop"] = list(prompt_bundle.parameters.stop_sequences)

        start_time = time.perf_counter()
        response: Optional[httpx.Response] = None
        max_attempts = 1  # Sin reintentos: el pipeline tiene timeout externo de 18s

        for attempt in range(max_attempts):
            try:
                response = self._client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                # Fail-fast: el timeout externo en el pipeline corta en 18s.
                # No retries aquí para evitar bloquear el threadpool.
                raise LLMTimeoutError(
                    f"HTTP request to Gemini endpoint {url} timed out after "
                    f"{self._timeout_seconds}s: {exc}"
                ) from exc
            except httpx.ConnectError as exc:
                logger.warning(
                    f"[Gemini ConnectError] Failed to connect to {url}: {exc}. "
                    "Failing fast to circuit breaker."
                )
                raise LLMConnectionError(
                    f"Failed to connect to Gemini backend at {url}: {exc}"
                ) from exc
            except httpx.RequestError as exc:
                raise LLMBackendError(
                    f"HTTP transport error contacting Gemini backend {url}: {exc}"
                ) from exc

            # Handle 404 model deprecation: auto-fallback to ACTIVE_FALLBACK_MODEL
            if response.status_code == 404:
                resp_text = response.text
                if (
                    "is no longer available" in resp_text
                    or "not found" in resp_text.lower()
                ) and payload["model"] != ACTIVE_FALLBACK_MODEL:
                    logger.warning(
                        f"[Gemini Deprecation Fallback] Model '{payload['model']}' returned 404. "
                        f"Auto-switching payload to active replacement '{ACTIVE_FALLBACK_MODEL}'."
                    )
                    payload["model"] = ACTIVE_FALLBACK_MODEL
                    max_attempts = 2  # permitir un intento extra solo para el fallback de modelo
                    continue

            # 429/503: no reintentar, fail-fast al circuit breaker
            if response.status_code in (429, 503):
                raise LLMBackendError(
                    f"Gemini rate-limited (HTTP {response.status_code}). El circuit breaker enrutará al fallback."
                )

            break

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if response is None:
            raise LLMBackendError("No HTTP response received from Gemini backend")

        if response.status_code != 200:
            raise LLMBackendError(
                f"Gemini API returned error HTTP {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            choice = data["choices"][0]
            text = choice["message"]["content"]
            usage_dict = data.get("usage")
            tokens_used = None
            if usage_dict:
                tokens_used = TokenUsage(
                    prompt_tokens=usage_dict.get("prompt_tokens", 0),
                    completion_tokens=usage_dict.get("completion_tokens", 0),
                    total_tokens=usage_dict.get("total_tokens", 0),
                )
            returned_model = data.get("model", payload["model"])
        except Exception as exc:
            raise LLMBackendError(
                f"Failed to parse Gemini response payload: {exc}. Response text: {response.text}"
            ) from exc

        return ProviderCompletion(
            text=text,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            model=returned_model,
            generator_abstained=False,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        phase_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream completion tokens in real-time using OpenAI-compatible SSE."""
        if not self._api_key:
            raise LLMConnectionError(
                "No GEMINI_API_KEY available for streaming. Configure .env."
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        target_model = MODEL_ALIAS_MAP.get(self._model_name, self._model_name)
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "stream": True,
        }

        timeout = httpx.Timeout(
            timeout=self._timeout_seconds,
            connect=self._connect_timeout_seconds,
        )

        async with httpx.AsyncClient(timeout=timeout) as async_client:
            async with async_client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise LLMBackendError(
                        f"Gemini streaming error HTTP {response.status_code}: {error_text.decode('utf-8', errors='replace')}"
                    )

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_str)
                        choices = chunk_data.get("choices", [])
                        if not choices:
                            continue
                        # COMMIT 5: capturar finish_reason (stop/length/error)
                        # para observabilidad del stream; el pipeline lo lee al
                        # cerrar y emite evento "truncated" si fue por límite.
                        fr = choices[0].get("finish_reason")
                        if fr:
                            self._last_finish_reason = fr
                        delta = choices[0].get("delta", {})
                        content_piece = delta.get("content", "")
                        if content_piece:
                            yield content_piece
                    except json.JSONDecodeError:
                        continue

