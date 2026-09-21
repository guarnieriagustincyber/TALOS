"""Integration tests for TalosLLMRouter & Resilient Multi-Cloud Orchestration (Fase 5.9)."""

import asyncio
from typing import List
import pytest

from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.providers.mock_provider import MockProvider
from study_engine.llm.quota_manager import QuotaManager
from study_engine.llm.router import PoolExhaustedError, TalosLLMRouter
from study_engine.llm.sanitizer import DataSanitizer, SensitiveDataLeakError


def _make_prompt(text: str = "Explain quicksort") -> PromptBundle:
    params = GenerationParameters(max_output_tokens=200, temperature=0.3)
    messages = (PromptMessage(role=PromptRole.USER, content=text),)
    p_hash = compute_canonical_prompt_hash("Sys", messages, params)
    return PromptBundle(
        system_prompt="Sys",
        messages=messages,
        parameters=params,
        prompt_hash=p_hash,
    )


def test_semantic_routing_phase_priority():
    """Router should prioritize providers according to updated pedagogical phase matrix."""
    p_nvidia = MockProvider(name="nvidia", canned_response="NVIDIA DeepSeek R1 answer")
    p_cerebras = MockProvider(name="cerebras", canned_response="Cerebras conceptual answer")
    p_sambanova = MockProvider(name="sambanova", canned_response="SambaNova answer")
    p_ollama = MockProvider(name="ollama", canned_response="Ollama local answer")

    router = TalosLLMRouter(
        providers={
            "nvidia": p_nvidia,
            "cerebras": p_cerebras,
            "sambanova": p_sambanova,
            "ollama": p_ollama,
        }
    )

    # Conceptual phase prioritizes NVIDIA (DeepSeek R1)
    chain_concept = router.resolve_chain("conceptual")
    assert chain_concept[0] == "nvidia"

    # Python code phase prioritizes NVIDIA (DeepSeek R1)
    chain_code = router.resolve_chain("python_code")
    assert chain_code[0] == "nvidia"

    # Pseudocode phase prioritizes Cerebras
    chain_pseudo = router.resolve_chain("pseudocode")
    assert chain_pseudo[0] == "cerebras"


def test_fallback_on_primary_failure():
    """Router should fallback to secondary provider when primary fails."""
    async def _run():
        p_cerebras = MockProvider(
            name="cerebras",
            should_fail=True,
            failure_exception=RuntimeError("HTTP 429 Too Many Requests"),
        )
        p_sambanova = MockProvider(
            name="sambanova",
            canned_response="SambaNova successfully rescued the turn.",
        )

        router = TalosLLMRouter(
            providers={"cerebras": p_cerebras, "sambanova": p_sambanova},
            phase_routing={"conceptual": ["cerebras", "sambanova"]},
        )

        bundle = _make_prompt("Explain hash tables")
        res = await router.complete(bundle, phase_id="conceptual")

        assert res.text == "SambaNova successfully rescued the turn."
        assert p_cerebras.call_count == 1
        assert p_sambanova.call_count == 1
        assert router._total_fallbacks_today == 1

    asyncio.run(_run())


def test_mid_stream_fallback_clean_recovery():
    """Ajuste 3: If provider fails mid-stream, discard buffer and cleanly restart from next."""
    async def _run():
        # Provider 1 yields 2 tokens then throws connection dropped
        p_primary = MockProvider(
            name="cerebras",
            canned_response="Token1 Token2 Token3 Token4",
            fail_after_tokens=2,
            failure_exception=RuntimeError("Connection broken mid-stream"),
        )
        # Provider 2 yields clean full response
        p_secondary = MockProvider(
            name="sambanova",
            canned_response="Clean recovered response from SambaNova.",
        )

        router = TalosLLMRouter(
            providers={"cerebras": p_primary, "sambanova": p_secondary},
            phase_routing={"conceptual": ["cerebras", "sambanova"]},
        )

        received_tokens: List[str] = []
        reset_called = False

        def on_reset():
            nonlocal reset_called
            reset_called = True
            received_tokens.clear()  # Caller discards partial tokens on mid-stream fallback

        async for token in router.stream(
            system_prompt="System",
            user_prompt="Explain pointers",
            phase_id="conceptual",
            on_fallback_reset=on_reset,
        ):
            received_tokens.append(token)

        assert reset_called is True
        full_text = "".join(received_tokens)
        assert full_text == "Clean recovered response from SambaNova."
        assert router._total_fallbacks_today == 1

    asyncio.run(_run())


def test_border_control_sensitive_data_local_isolation():
    """Router must prohibit outbound cloud providers when sensitive data is present."""
    async def _run():
        p_cerebras = MockProvider(name="cerebras", canned_response="Cloud response")
        p_ollama = MockProvider(name="ollama", canned_response="Local safe response")

        router = TalosLLMRouter(
            providers={"cerebras": p_cerebras, "ollama": p_ollama},
            phase_routing={"conceptual": ["cerebras", "ollama"]},
        )

        # Prompt with sensitive IP and private path
        sensitive_prompt = _make_prompt("Inspect /etc/shadow on 192.168.1.50")
        res = await router.complete(sensitive_prompt, phase_id="conceptual")

        assert res.text == "Local safe response"
        # Cerebras was NEVER called
        assert p_cerebras.call_count == 0
        assert p_ollama.call_count == 1

    asyncio.run(_run())


def test_border_control_fail_closed_when_local_unavailable():
    """Router must raise SensitiveDataLeakError if sensitive data is found and local provider is offline."""
    async def _run():
        p_cerebras = MockProvider(name="cerebras", canned_response="Cloud response")
        p_ollama = MockProvider(name="ollama", available=False)

        router = TalosLLMRouter(
            providers={"cerebras": p_cerebras, "ollama": p_ollama},
            phase_routing={"conceptual": ["cerebras", "ollama"]},
        )

        sensitive_prompt = _make_prompt("Password AKIAIOSFODNN7EXAMPLE")
        with pytest.raises(SensitiveDataLeakError):
            await router.complete(sensitive_prompt, phase_id="conceptual")

        assert p_cerebras.call_count == 0

    asyncio.run(_run())


def test_pool_exhausted_error_when_all_fail():
    """Router must raise PoolExhaustedError when all providers fail."""
    async def _run():
        p1 = MockProvider(name="p1", should_fail=True)
        p2 = MockProvider(name="p2", should_fail=True)

        router = TalosLLMRouter(
            providers={"p1": p1, "p2": p2},
            phase_routing={"*": ["p1", "p2"]},
        )

        bundle = _make_prompt("Hello")
        with pytest.raises(PoolExhaustedError):
            await router.complete(bundle)

    asyncio.run(_run())
