"""Unit tests for Provider Adapters (Fase 5.9 / Pilar 1)."""

import asyncio
import json
import httpx
import pytest

from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.providers.cerebras_provider import CerebrasProvider
from study_engine.llm.providers.cloudflare_provider import CloudflareProvider
from study_engine.llm.providers.mock_provider import MockProvider
from study_engine.llm.providers.nvidia_provider import NvidiaProvider
from study_engine.llm.providers.ollama_provider import OllamaProvider
from study_engine.llm.providers.openai_compatible import OpenAICompatibleProvider
from study_engine.llm.providers.sambanova_provider import SambaNovaProvider


def _build_test_prompt_bundle(user_text: str = "Explain pointers") -> PromptBundle:
    params = GenerationParameters(max_output_tokens=150, temperature=0.3)
    messages = (PromptMessage(role=PromptRole.USER, content=user_text),)
    p_hash = compute_canonical_prompt_hash("System prompt", messages, params)
    return PromptBundle(
        system_prompt="System prompt",
        messages=messages,
        parameters=params,
        prompt_hash=p_hash,
    )


def test_mock_provider_complete_and_stream():
    """MockProvider should complete and stream deterministically."""
    async def _run():
        provider = MockProvider(
            name="test-mock",
            canned_response="Pointers hold memory addresses in C.",
        )
        assert provider.is_available() is True
        assert provider.name == "test-mock"

        bundle = _build_test_prompt_bundle()
        completion = await provider.complete(bundle)
        assert completion.text == "Pointers hold memory addresses in C."
        assert completion.tokens_used is not None
        assert completion.tokens_used.total_tokens > 0

        # Stream test
        streamed = []
        async for token in provider.stream("Sys", "User"):
            streamed.append(token)
        full_streamed = "".join(streamed)
        assert full_streamed == "Pointers hold memory addresses in C."
        assert provider.call_count == 2

    asyncio.run(_run())


def test_openai_compatible_complete_mock_transport(monkeypatch):
    """OpenAICompatibleProvider should parse HTTP response using httpx."""
    async def _run():
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/chat/completions"
            body = json.loads(request.content)
            assert body["model"] == "test-model"
            return httpx.Response(
                200,
                json={
                    "model": "test-model",
                    "choices": [{"message": {"content": "Simulated OpenAI response"}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
                },
            )

        mock_transport = httpx.MockTransport(handler)

        provider = OpenAICompatibleProvider(
            name="test-compat",
            default_model="test-model",
            base_url="https://api.test.com/v1",
            api_key="test-key",
        )

        # Monkeypatch httpx.AsyncClient to use mock_transport
        orig_async_client = httpx.AsyncClient

        def mock_client_factory(*args, **kwargs):
            kwargs["transport"] = mock_transport
            return orig_async_client(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", mock_client_factory)

        bundle = _build_test_prompt_bundle()
        comp = await provider.complete(bundle)
        assert comp.text == "Simulated OpenAI response"
        assert comp.tokens_used.total_tokens == 20

    asyncio.run(_run())


def test_openai_compatible_stream_mock_transport(monkeypatch):
    """OpenAICompatibleProvider should stream SSE tokens correctly."""
    async def _run():
        sse_lines = (
            'data: {"choices": [{"delta": {"content": "Hello"}}]}\n\n'
            'data: {"choices": [{"delta": {"content": " World"}}]}\n\n'
            "data: [DONE]\n\n"
        )

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/chat/completions"
            return httpx.Response(
                200,
                content=sse_lines.encode("utf-8"),
                headers={"Content-Type": "text/event-stream"},
            )

        mock_transport = httpx.MockTransport(handler)
        orig_async_client = httpx.AsyncClient

        def mock_client_factory(*args, **kwargs):
            kwargs["transport"] = mock_transport
            return orig_async_client(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", mock_client_factory)

        provider = OpenAICompatibleProvider(
            name="test-compat",
            default_model="test-model",
            base_url="https://api.test.com/v1",
            api_key="test-key",
        )

        tokens = []
        async for token in provider.stream("System", "User"):
            tokens.append(token)

        assert "".join(tokens) == "Hello World"

    asyncio.run(_run())


def test_openai_compatible_http_errors(monkeypatch):
    """OpenAICompatibleProvider should raise on HTTP 429 and 500."""
    async def _run():
        def handler_429(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": "Rate limit exceeded"})

        mock_transport = httpx.MockTransport(handler_429)
        orig_async_client = httpx.AsyncClient

        def mock_client_factory(*args, **kwargs):
            kwargs["transport"] = mock_transport
            return orig_async_client(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", mock_client_factory)

        provider = OpenAICompatibleProvider(
            name="test-compat",
            default_model="test-model",
            base_url="https://api.test.com/v1",
            api_key="test-key",
        )

        bundle = _build_test_prompt_bundle()
        with pytest.raises(RuntimeError) as exc_info:
            await provider.complete(bundle)
        assert "429" in str(exc_info.value)

    asyncio.run(_run())


def test_provider_instantiations_and_availability(monkeypatch):
    """Concrete provider classes should configure credentials and default models."""
    monkeypatch.setenv("CEREBRAS_API_KEY", "c-key")
    monkeypatch.setenv("SAMBANOVA_API_KEY", "s-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-key")
    monkeypatch.setenv("CLOUDFLARE_API_KEY", "cf-key")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "cf-acc")

    cerebras = CerebrasProvider()
    assert cerebras.is_available() is True
    assert cerebras.default_model == "llama3.3-70b"

    sambanova = SambaNovaProvider()
    assert sambanova.is_available() is True
    assert sambanova.default_model == "Meta-Llama-3.3-70B-Instruct"

    nvidia = NvidiaProvider()
    assert nvidia.is_available() is True
    assert nvidia.default_model == "deepseek-ai/deepseek-r1"

    cloudflare = CloudflareProvider()
    assert cloudflare.is_available() is True
    assert "@cf" in cloudflare.default_model

    ollama = OllamaProvider()
    assert ollama.is_available() is True
    assert "qwen" in ollama.default_model

    # Check unconfigured behavior
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    unconfigured_cerebras = CerebrasProvider(api_key="")
    assert unconfigured_cerebras.is_available() is False
