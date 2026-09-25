"""Provider backends and protocols for Subsystem S4.3.

Provides modular, swappable execution backends conforming strictly to the
ProviderBackend protocol: MockBackend, RuleBasedBackend, and HttpOpenAIBackend.
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, Optional, Protocol, runtime_checkable
import httpx
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.contracts.generation import TokenUsage
from study_engine.generation.prompts import PromptBundle
from study_engine.llm.exceptions import (
    LLMBackendError,
    LLMConnectionError,
    LLMTimeoutError,
)


class ProviderCompletion(BaseContract):
    """Immutable completion payload returned by a ProviderBackend."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(
        ..., min_length=1, description="Generated completion text"
    )
    latency_ms: float = Field(
        ..., ge=0.0, description="Backend roundtrip latency in milliseconds"
    )
    tokens_used: Optional[TokenUsage] = Field(
        default=None,
        description="Reported token telemetry (None if unprovided)",
    )

    model: str = Field(
        ..., min_length=1, description="Authoritative model identifier"
    )
    generator_abstained: bool = Field(
        default=False,
        description="True if generator explicitly signaled abstention",
    )


@runtime_checkable
class ProviderBackend(Protocol):
    """Authoritative protocol for low-level generation backends."""

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        """Execute completion over an assembled PromptBundle."""
        ...


class MockBackend(ProviderBackend):
    """Deterministic, configurable backend for hermetic testing."""

    def __init__(
        self,
        canned_text: Optional[str] = None,
        canned_abstained: bool = False,
        canned_tokens: Optional[TokenUsage] = None,
        canned_latency_ms: float = 10.0,
        canned_model: str = "mock-llm-v1",
        raise_error: Optional[Exception] = None,
    ) -> None:
        """Initialize MockBackend with canned outputs or exceptions."""
        self._text = canned_text
        self._abstained = canned_abstained
        self._tokens = canned_tokens
        self._latency_ms = canned_latency_ms
        self._model = canned_model
        self._raise_error = raise_error

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        """Produce canned response or raise configured error."""
        if self._raise_error is not None:
            raise self._raise_error

        if self._text is not None:
            text = self._text
        else:
            text = (
                "Según la evidencia [E1], el concepto solicitado se "
                "explica conforme a las fuentes autorizadas del curso."
            )

        return ProviderCompletion(
            text=text,
            latency_ms=self._latency_ms,
            tokens_used=self._tokens,
            model=self._model,
            generator_abstained=self._abstained,
        )


class ReplayMockBackend(ProviderBackend):
    """Deterministic ProviderBackend replaying from generation_replay.json."""

    def __init__(
        self,
        replay_file: Optional[Path] = None,
        default_model: str = "mock-replay-v1",
    ) -> None:
        self._replay_file = replay_file or (
            Path(__file__).resolve().parents[3]
            / "data"
            / "experiments"
            / "hito3"
            / "generation_replay.json"
        )
        self._default_model = default_model
        self._fixtures: Dict[str, Any] = {}
        if self._replay_file.exists():
            with open(self._replay_file, "r", encoding="utf-8") as f:
                self._fixtures = json.load(f).get("fixtures", {})

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        """Complete by looking up query match in loaded fixtures."""
        user_queries = [
            m.content for m in prompt_bundle.messages if m.role.value == "user"
        ]
        query = user_queries[-1] if user_queries else ""

        for fix in self._fixtures.values():
            fix_query = fix.get("query", "")
            if fix_query and (fix_query in query or query in fix_query):
                return ProviderCompletion(
                    text=fix["raw_content"],
                    latency_ms=10.0,
                    tokens_used=TokenUsage(
                        prompt_tokens=100, completion_tokens=50, total_tokens=150
                    ),
                    model=self._default_model,
                    generator_abstained=False,
                )

        # Fallback to standard grounded mock response if not in replay table
        return ProviderCompletion(
            text="Según la evidencia [E1], el concepto solicitado se explica conforme a las fuentes autorizadas del curso.",
            latency_ms=10.0,
            tokens_used=TokenUsage(
                prompt_tokens=100, completion_tokens=50, total_tokens=150
            ),
            model=self._default_model,
            generator_abstained=False,
        )



class RuleBasedBackend(ProviderBackend):
    """Offline template backend with zero complex pedagogical logic."""

    def __init__(self, model_name: str = "rule-based-v1") -> None:
        """Initialize RuleBasedBackend."""
        self._model_name = model_name

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        """Produce simple deterministic template completion."""
        start = time.perf_counter()
        # Simple extraction of user query
        user_queries = [
            m.content for m in prompt_bundle.messages if m.role.value == "user"
        ]
        last_query = user_queries[-1] if user_queries else "consulta general"

        text = (
            f"Respuesta determinista para '{last_query}'. "
            "Conforme a la evidencia documental [E1], el concepto "
            "queda definido."
        )
        latency = (time.perf_counter() - start) * 1000.0

        return ProviderCompletion(

            text=text,
            latency_ms=latency,
            tokens_used=None,
            model=self._model_name,
            generator_abstained=False,
        )


class HttpOpenAIBackend(ProviderBackend):
    """OpenAI-compatible HTTP backend using httpx.

    Communicates with any standard /v1/chat/completions endpoint
    (Ollama, vLLM, LM Studio, LocalAI, OpenAI, etc.).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        default_model: str = "llama3",
        timeout_seconds: float = 30.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        """Initialize HttpOpenAIBackend.

        Parameters
        ----------
        base_url : str
            Base URL of the provider endpoint.
        api_key : Optional[str]
            Optional authorization bearer token.
        default_model : str
            Default model identifier to request if not specified in parameters.
        timeout_seconds : float
            Request timeout duration.
        client : Optional[httpx.Client]
            Optional injected httpx client (e.g. for MockTransport testing).
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._timeout_seconds = timeout_seconds

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx.Client(timeout=self._timeout_seconds)
            self._owns_client = True

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        if (
            self._base_url.endswith("/openai")
            or self._base_url.endswith("/v1")
        ):
            url = f"{self._base_url}/chat/completions"
        else:
            url = f"{self._base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # 1. Format payload: system_prompt first, then sequential dialog
        payload_messages = [
            {"role": "system", "content": prompt_bundle.system_prompt}
        ]
        for m in prompt_bundle.messages:
            payload_messages.append(
                {"role": m.role.value, "content": m.content}
            )

        target_model = (
            prompt_bundle.parameters.suggested_model or self._default_model
        )

        payload = {
            "model": target_model,
            "messages": payload_messages,
            "temperature": prompt_bundle.parameters.temperature,
            "max_tokens": prompt_bundle.parameters.max_output_tokens,
        }
        if prompt_bundle.parameters.stop_sequences:
            payload["stop"] = list(prompt_bundle.parameters.stop_sequences)
        if prompt_bundle.parameters.seed is not None:
            payload["seed"] = prompt_bundle.parameters.seed

        start_time = time.perf_counter()
        response = None
        # Fail-fast: sin reintentos con sleep. El CircuitBreakerBackend del nivel
        # superior maneja el fallback al siguiente proveedor. Los sleep() síncronos
        # bloquean el threadpool de FastAPI y congelan la PC.
        max_attempts = 1
        for attempt in range(max_attempts):
            try:
                response = self._client.post(
                    url, headers=headers, json=payload
                )
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"HTTP request to {url} timed out after "
                    f"{self._timeout_seconds}s: {exc}"
                ) from exc
            except httpx.ConnectError as exc:
                raise LLMConnectionError(
                    f"Failed to connect to backend at {url}: {exc}"
                ) from exc
            except httpx.RequestError as exc:
                raise LLMBackendError(
                    f"HTTP transport error contacting {url}: {exc}"
                ) from exc

            # 429/503: fail-fast al circuit breaker en lugar de sleep+retry
            if response.status_code in (503, 429):
                raise LLMBackendError(
                    f"Backend rate-limited (HTTP {response.status_code}). "
                    f"Circuit breaker enrutará al fallback."
                )
            break

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if response is None or response.status_code != 200:
            err_text = response.text if response is not None else "No response"
            status_code = response.status_code if response is not None else 500
            raise LLMBackendError(
                f"Backend HTTP {status_code}: {err_text}"
            )

        # 2. Strict validation of response payload structure (Hardening #4)

        try:
            data = response.json()
        except Exception as exc:
            raise LLMBackendError(
                f"Backend returned invalid JSON payload: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise LLMBackendError(
                f"Backend response must be a JSON object, got {type(data)}."
            )

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise LLMBackendError(
                "Backend response missing non-empty 'choices' list."
            )

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMBackendError("First choice in response is not an object.")

        message = first_choice.get("message")
        if not message or not isinstance(message, dict):
            raise LLMBackendError(
                "Choice missing 'message' object in completion."
            )

        content = message.get("content")
        if content is None or not isinstance(content, str):
            raise LLMBackendError(
                "Message missing valid string 'content' field."
            )

        if not content.strip():
            raise LLMBackendError(
                "Backend produced blank or whitespace-only content string."
            )

        # 3. Extract reported token usage if present (no heuristic estimation)
        tokens_used: Optional[TokenUsage] = None
        raw_usage = data.get("usage")
        if isinstance(raw_usage, dict):
            tokens_used = TokenUsage(
                prompt_tokens=raw_usage.get("prompt_tokens"),
                completion_tokens=raw_usage.get("completion_tokens"),
                total_tokens=raw_usage.get("total_tokens"),
            )

        reported_model = data.get("model") or target_model

        return ProviderCompletion(
            text=content,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            model=reported_model,
            generator_abstained=False,
        )

    def close(self) -> None:
        """Close internal HTTP client if owned."""
        if self._owns_client:
            self._client.close()


class CloudflareWorkerBackend(ProviderBackend):
    """Backend for Cloudflare Workers AI proxy.

    The Worker at ``talos2.guarnieriagustincyber.workers.dev`` returns a
    non-standard envelope::

        {"success": true, "result": {"choices": [{"text": "..."}}], "model": "..."}}

    The ``text`` field in each choice is the generated content (not
    ``message.content`` as in OpenAI chat format).  This backend unwraps that
    envelope and normalises the response into a ``ProviderCompletion``.
    """

    def __init__(
        self,
        worker_url: str,
        api_key: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._url = worker_url.rstrip("/") + "/v1/chat/completions"
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds)
        self.model_name = "cloudflare-worker"

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": prompt_bundle.system_prompt}]
        for m in prompt_bundle.messages:
            messages.append({"role": m.role.value, "content": m.content})

        payload: Dict[str, Any] = {
            "messages": messages,
            "max_tokens": prompt_bundle.parameters.max_output_tokens or 500,
        }

        start = time.perf_counter()
        try:
            response = self._client.post(self._url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Cloudflare Worker timed out: {exc}") from exc
        except httpx.RequestError as exc:
            raise LLMConnectionError(f"Cloudflare Worker connection error: {exc}") from exc

        latency_ms = (time.perf_counter() - start) * 1000.0

        if response.status_code != 200:
            raise LLMBackendError(
                f"Cloudflare Worker HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception as exc:
            raise LLMBackendError(f"Cloudflare Worker invalid JSON: {exc}") from exc

        # Unwrap {"success": true, "result": {...}} envelope
        result = data.get("result", data)
        choices = result.get("choices") or data.get("choices") or []
        if not choices:
            raise LLMBackendError("Cloudflare Worker: no choices in response")

        first = choices[0]
        # Prefer message.content (chat format), fall back to text (completion format)
        content: Optional[str] = None
        if isinstance(first.get("message"), dict):
            content = first["message"].get("content")
        if not content:
            content = first.get("text") or first.get("content")

        if not content or not content.strip():
            raise LLMBackendError("Cloudflare Worker: blank content in response")

        reported_model = result.get("model") or data.get("model") or "cloudflare-worker"
        self.model_name = reported_model

        return ProviderCompletion(
            text=content.strip(),
            latency_ms=latency_ms,
            tokens_used=None,
            model=reported_model,
            generator_abstained=False,
        )

    def close(self) -> None:
        self._client.close()


class CloudflareDirectBackend(ProviderBackend):
    """Backend for Cloudflare Workers AI via the direct REST API.

    Uses the official endpoint::

        POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}

    with a real Cloudflare API Token (created at dash.cloudflare.com/profile/api-tokens).
    Response envelope: ``{"result": {"response": "..."}, "success": true}``.

    Confirmed working models (2026-09-25):
        @cf/meta/llama-3.3-70b-instruct-fp8-fast  — ~1.5s
        @cf/qwen/qwen3.8-27b                       — ~1.1s  (uses chat format in result.choices)
        @cf/openai/gpt-oss-120b
        @cf/google/gemma-4-26b-a4b-it
        @cf/deepseek-ai/deepseek-v4-flash-0731
    """

    def __init__(
        self,
        account_id: str,
        api_token: str,
        model: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        timeout_seconds: float = 12.0,
    ) -> None:
        self._account_id = account_id
        self._api_token = api_token
        self._model = model
        self._timeout = timeout_seconds
        self._base = "https://api.cloudflare.com/client/v4/accounts"
        self._client = httpx.Client(timeout=timeout_seconds)
        self.model_name = model

    @property
    def _url(self) -> str:
        return f"{self._base}/{self._account_id}/ai/run/{self._model}"

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": prompt_bundle.system_prompt}]
        for m in prompt_bundle.messages:
            messages.append({"role": m.role.value, "content": m.content})

        payload: Dict[str, Any] = {
            "messages": messages,
            "max_tokens": prompt_bundle.parameters.max_output_tokens or 500,
        }

        start = time.perf_counter()
        try:
            response = self._client.post(self._url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Cloudflare Direct timed out ({self._model}): {exc}") from exc
        except httpx.RequestError as exc:
            raise LLMConnectionError(f"Cloudflare Direct connection error: {exc}") from exc

        latency_ms = (time.perf_counter() - start) * 1000.0

        if response.status_code != 200:
            raise LLMBackendError(
                f"Cloudflare Direct HTTP {response.status_code} ({self._model}): {response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception as exc:
            raise LLMBackendError(f"Cloudflare Direct invalid JSON: {exc}") from exc

        if not data.get("success"):
            errs = data.get("errors") or data.get("messages") or []
            raise LLMBackendError(f"Cloudflare Direct API error: {errs}")

        result = data.get("result") or {}

        # Workers AI returns content in different keys per model family:
        # - "response"              → simple text models (llama-3.1-8b-fast, etc.)
        # - "choices[].message.content" → OpenAI-format models (qwen3.8-27b, etc.)
        # - "choices[].text"        → completion-format models
        content: Optional[str] = None

        # Try "response" key first (most common in Workers AI)
        content = result.get("response")

        if not content:
            choices = result.get("choices") or []
            if choices:
                first = choices[0]
                msg = first.get("message") or {}
                content = (
                    msg.get("content")
                    or msg.get("reasoning")
                    or first.get("text")
                )

        if not content or not str(content).strip():
            raise LLMBackendError(
                f"Cloudflare Direct: blank or missing content in response. "
                f"result keys: {list(result.keys())}"
            )

        return ProviderCompletion(
            text=str(content).strip(),
            latency_ms=latency_ms,
            tokens_used=None,
            model=self._model,
            generator_abstained=False,
        )

    def close(self) -> None:
        self._client.close()
