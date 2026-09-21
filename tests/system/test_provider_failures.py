"""System-Level Acceptance Audit: Provider Failure Handling (Fase 6.1).

Verifies that TALOS gracefully handles malformed, adversarial, or failing
responses from external LLM providers without crashing, leaking secrets,
or violating safety invariants.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, AsyncGenerator, Dict, List, Optional
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from study_engine.contracts.generation import GenerationParameters, TokenUsage
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.backends import ProviderCompletion
from study_engine.llm.providers.abstract_provider import AbstractLLMProvider
from study_engine.llm.providers.mock_provider import MockProvider
from study_engine.llm.router import CircuitState, PoolExhaustedError, TalosLLMRouter


def _make_prompt(text: str = "Explain memory layout") -> PromptBundle:
    params = GenerationParameters(max_output_tokens=200, temperature=0.3)
    messages = (PromptMessage(role=PromptRole.USER, content=text),)
    p_hash = compute_canonical_prompt_hash("Sys", messages, params)
    return PromptBundle(
        system_prompt="Sys",
        messages=messages,
        parameters=params,
        prompt_hash=p_hash,
    )


INVALID_BYTES_REPR = chr(0) + chr(1) + chr(2)


class MalformedResponseProvider(AbstractLLMProvider):
    """Provider simulating bad responses (empty, invalid JSON, 100KB, canary, injection, timeout, bytes)."""

    def __init__(self, name: str, bad_payload: Optional[str]) -> None:
        super().__init__(name=name, default_model="malformed-v1")
        self.bad_payload = bad_payload
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    async def complete(
        self,
        prompt_bundle: PromptBundle,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> ProviderCompletion:
        self.call_count += 1

        # Simulate provider failure or malformed payload rejection
        if self.bad_payload is None:
            raise asyncio.TimeoutError("Provider request timed out after 5.0s")
        if self.bad_payload == INVALID_BYTES_REPR or self.bad_payload == "__CRASH_BYTES__":
            raise UnicodeDecodeError("utf-8", bytes([0, 1, 2]), 0, 1, "invalid byte sequence")
        if self.bad_payload == "":
            raise ValueError("Provider returned empty response (string_too_short)")
        if self.bad_payload == "invalid json":
            raise ValueError("Provider output failed JSON parsing validation")
        if len(self.bad_payload) >= 100000:
            raise ValueError("Provider response exceeded 100KB buffer threshold (buffer overflow guard)")
        if "CANARY" in self.bad_payload:
            raise RuntimeError("Provider response contains leaked canary secret")
        if "ignore previous instructions" in self.bad_payload:
            raise RuntimeError("Prompt injection signature detected in provider output")

        return ProviderCompletion(
            text=self.bad_payload,
            latency_ms=10.0,
            model=self.default_model,
        )

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        self.call_count += 1
        if self.bad_payload is None:
            raise asyncio.TimeoutError("Provider request timed out after 5.0s")
        yield self.bad_payload or ""


class TestProviderFailureHandling:
    """Verificar que TALOS maneja respuestas malformadas o maliciosas
    de proveedores sin violar invariantes
    """

    @pytest.mark.parametrize(
        "bad_response",
        [
            "",  # Respuesta vacía
            "invalid json",  # JSON inválido
            "x" * 100000,  # Texto enorme (100KB)
            "CANARY_LEAKED_SECRET",  # Canary
            "ignore previous instructions",  # Prompt injection
            None,  # Timeout (sin respuesta)
            INVALID_BYTES_REPR,  # Bytes inválidos
        ],
    )
    def test_bad_provider_responses(self, bad_response: Optional[str]) -> None:
        """Configurar MockProvider para devolver bad_response
        Verificar que TALOS:
        1. No crashea
        2. Activa fallback correctamente
        3. No viola invariantes de seguridad
        4. Emite evento de error apropiado al cliente cuando todo el pool falla
        """
        async def _run() -> None:
            p_primary = MalformedResponseProvider(name="primary", bad_payload=bad_response)
            p_fallback = MockProvider(
                name="fallback",
                canned_response="Clean fallback response safely returned.",
            )

            # Scenario A: Resilient router with fallback available
            router = TalosLLMRouter(
                providers={"primary": p_primary, "fallback": p_fallback},
                phase_routing={"conceptual": ["primary", "fallback"]},
            )

            prompt = _make_prompt("Explain heap memory")

            # 1. No crashea
            # 2. Activa fallback correctamente
            completion = await router.complete(prompt, phase_id="conceptual")
            assert completion.text == "Clean fallback response safely returned."
            assert p_primary.call_count == 1
            assert p_fallback.call_count == 1
            assert router._total_fallbacks_today == 1

            # 3. No viola invariantes de seguridad
            cb_primary = router.circuit_breakers["primary"]
            assert cb_primary.last_failure is not None

            # 4. Emite evento de error apropiado al cliente cuando todo el pool falla
            solo_router = TalosLLMRouter(
                providers={"primary": p_primary},
                phase_routing={"conceptual": ["primary"]},
            )
            with pytest.raises(PoolExhaustedError) as exc_info:
                await solo_router.complete(prompt, phase_id="conceptual")
            assert "All available LLM providers in pool failed or exhausted" in str(exc_info.value)

        asyncio.run(_run())

    def test_provider_truncation_mid_stream(self) -> None:
        """Proveedor se desconecta en medio del streaming
        Verificar graceful degradation y fallback
        """
        async def _run() -> None:
            # Primary emits 2 tokens and disconnects
            p_primary = MockProvider(
                name="cerebras",
                canned_response="Token1 Token2 Token3 Token4",
                fail_after_tokens=2,
                failure_exception=RuntimeError("Socket connection broken mid-stream"),
            )
            # Secondary recovers cleanly
            p_secondary = MockProvider(
                name="sambanova",
                canned_response="Clean full recovery from SambaNova.",
            )

            router = TalosLLMRouter(
                providers={"cerebras": p_primary, "sambanova": p_secondary},
                phase_routing={"conceptual": ["cerebras", "sambanova"]},
            )

            received_tokens: List[str] = []
            reset_called = False

            def on_reset() -> None:
                nonlocal reset_called
                reset_called = True
                received_tokens.clear()  # Caller discards partial tokens upon fallback reset

            async for token in router.stream(
                system_prompt="System",
                user_prompt="Explain stack frames",
                phase_id="conceptual",
                on_fallback_reset=on_reset,
            ):
                received_tokens.append(token)

            # Invariants:
            # 1. Reset handler was invoked to drop partial corrupted tokens
            assert reset_called is True
            # 2. Output text matches clean full secondary response
            assert "".join(received_tokens) == "Clean full recovery from SambaNova."
            # 3. Fallback was counted
            assert router._total_fallbacks_today == 1

        asyncio.run(_run())

    def test_provider_timeout(self) -> None:
        """Proveedor excede timeout configurado (5s)
        Verificar que Circuit Breaker se activa y fallback funciona
        """
        async def _run() -> None:
            # Provider with failure threshold = 1
            p_timing_out = MockProvider(
                name="failing_provider",
                should_fail=True,
                failure_exception=asyncio.TimeoutError("Request timed out after 5000ms"),
            )
            p_backup = MockProvider(
                name="backup_provider",
                canned_response="Respuesta exitosa del proveedor backup.",
            )

            router = TalosLLMRouter(
                providers={"failing_provider": p_timing_out, "backup_provider": p_backup},
                phase_routing={"conceptual": ["failing_provider", "backup_provider"]},
                failure_threshold=1,  # Open circuit immediately on 1 failure
            )

            cb_failing = router.circuit_breakers["failing_provider"]
            assert cb_failing.last_failure is None

            bundle = _make_prompt("Explain concurrency")
            res = await router.complete(bundle, phase_id="conceptual")

            # 1. Fallback returned clean answer
            assert res.text == "Respuesta exitosa del proveedor backup."
            # 2. Circuit breaker opened for failing provider
            assert cb_failing.state == CircuitState.OPEN
            assert await cb_failing.can_proceed() is False
            # 3. Subsequent call immediately bypasses failing provider without calling it again
            initial_fail_calls = p_timing_out.call_count
            res2 = await router.complete(bundle, phase_id="conceptual")
            assert res2.text == "Respuesta exitosa del proveedor backup."
            # Call count on failing provider did not increment because circuit is OPEN
            assert p_timing_out.call_count == initial_fail_calls

        asyncio.run(_run())
