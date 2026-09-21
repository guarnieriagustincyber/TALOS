"""Unit tests for CircuitBreakerBackend.stream() (F2: SSE real, no replay).

Validates:
- Progressive chunk streaming from primary backend.
- Clean fallback when the primary fails before any token was emitted.
- Circuit opening after N consecutive stream failures (fail-closed).
- Mid-stream failures propagate (no content duplication).
- Fallback without native stream() uses complete() + word replay.
"""

import asyncio

from study_engine.contracts.generation import GenerationParameters, TokenUsage
from study_engine.llm.backends import ProviderCompletion
from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitBreakerBackend, CircuitState


class _FakeStreamingBackend:
    """Backend fake con stream() nativo controlado."""

    def __init__(self, chunks=None, fail=False, fail_after_n=None):
        self.chunks = chunks if chunks is not None else ["Hola ", "mundo", "."]
        self.fail = fail
        self.fail_after_n = fail_after_n
        self.stream_calls = 0
        self.complete_calls = 0

    async def stream(self, **kwargs):
        self.stream_calls += 1
        for i, chunk in enumerate(self.chunks):
            if self.fail and (self.fail_after_n is None or i == self.fail_after_n):
                raise RuntimeError("primary blew up")
            yield chunk

    def complete(self, bundle):
        self.complete_calls += 1
        return ProviderCompletion(
            text="respuesta completa del fallback",
            latency_ms=1.0,
            tokens_used=TokenUsage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
            model="fake",
            generator_abstained=False,
        )


class _CompleteOnlyBackend:
    """Backend fake sin stream(): solo complete()."""

    def __init__(self):
        self.complete_calls = 0

    def complete(self, bundle):
        self.complete_calls += 1
        assert bundle.parameters.max_output_tokens > 0
        return ProviderCompletion(
            text="texto sin streaming",
            latency_ms=1.0,
            tokens_used=TokenUsage(prompt_tokens=2, completion_tokens=4, total_tokens=6),
            model="fake-nostream",
            generator_abstained=False,
        )


def _collect(cb, **kwargs):
    async def _run():
        out = []
        async for tok in cb.stream(
            system_prompt=kwargs.get("system_prompt", "sys"),
            user_prompt=kwargs.get("user_prompt", "hola"),
            max_tokens=kwargs.get("max_tokens", 64),
        ):
            out.append(tok)
        return out

    return asyncio.run(_run())


def test_stream_delegates_real_chunks_progressively():
    primary = _FakeStreamingBackend(chunks=["a", "b", "c"])
    breaker = CircuitBreaker(failure_threshold=3)
    cb = CircuitBreakerBackend(primary, _FakeStreamingBackend(), breaker)

    chunks = _collect(cb)

    assert chunks == ["a", "b", "c"]
    assert primary.stream_calls == 1
    assert primary.complete_calls == 0
    assert breaker.state == CircuitState.CLOSED
    assert breaker.consecutive_failures == 0


def test_stream_fallback_when_primary_fails_before_first_token():
    primary = _FakeStreamingBackend(fail=True)
    fallback = _FakeStreamingBackend(chunks=["fallback ", "ok"])
    breaker = CircuitBreaker(failure_threshold=3)
    cb = CircuitBreakerBackend(primary, fallback, breaker)

    chunks = _collect(cb)

    assert chunks == ["fallback ", "ok"]
    assert primary.stream_calls == 1
    assert breaker.consecutive_failures == 1
    assert breaker.state == CircuitState.CLOSED  # aún bajo el umbral


def test_stream_circuit_opens_after_threshold_and_skips_primary():
    breaker = CircuitBreaker(failure_threshold=2, initial_cooldown=60.0)
    primary = _FakeStreamingBackend(fail=True)
    fallback = _FakeStreamingBackend(chunks=["fb"])
    cb = CircuitBreakerBackend(primary, fallback, breaker)

    for _ in range(2):
        assert _collect(cb) == ["fb"]
    assert breaker.state == CircuitState.OPEN

    # Circuito abierto: el primario ya no se llama, va directo al fallback.
    assert _collect(cb) == ["fb"]
    assert primary.stream_calls == 2


def test_stream_midstream_failure_propagates_without_duplication():
    # Falla DESPUÉS de emitir 1 token: no debe reiniciar ni caer al fallback.
    primary = _FakeStreamingBackend(chunks=["parcial", "nunca"], fail=True, fail_after_n=1)
    fallback = _FakeStreamingBackend(chunks=["fallback"])
    cb = CircuitBreakerBackend(primary, fallback, CircuitBreaker())

    async def _run():
        out = []
        try:
            async for tok in cb.stream(system_prompt="s", user_prompt="u", max_tokens=32):
                out.append(tok)
        except RuntimeError:
            return out, "raised"
        return out, "no-raise"

    chunks, outcome = asyncio.run(_run())
    assert outcome == "raised"
    assert chunks == ["parcial"]  # contenido parcial sin duplicar
    assert fallback.stream_calls == 0


def test_stream_fallback_without_native_stream_uses_complete_replay():
    primary = _FakeStreamingBackend(fail=True)
    fallback = _CompleteOnlyBackend()
    cb = CircuitBreakerBackend(primary, fallback, CircuitBreaker())

    chunks = _collect(cb)

    assert fallback.complete_calls == 1
    text = "".join(chunks)
    assert "texto sin streaming" in text
    assert len(chunks) > 1  # replay por palabras, no un solo blob
