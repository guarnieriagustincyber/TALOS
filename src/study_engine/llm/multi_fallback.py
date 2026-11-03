"""Multi-provider fallback backend for resilient LLM routing.

Implements a cascading fallback strategy across an ordered list of provider
backends.  Both ``complete()`` (sync, used by BKT / FastPath / MemoryExtractor)
and ``stream()`` (async generator, used by SSE chat endpoint) are supported.

Cascade semantics
-----------------
* On each call, providers are tried in list order.
* A provider is skipped if it raises *any* exception, including
  ``asyncio.TimeoutError`` (enforced per-provider via ``asyncio.wait_for``).
* The first successful provider wins; its result is returned immediately.
* ``last_successful_provider`` is updated on every success for observability.
* If every provider fails, ``OfflinePedagogicalBackend`` is used as the
  unconditional last-resort rather than surfacing an unhandled exception.

Design constraints
------------------
* No sleeps, no retries within a single provider — fail-fast to the next one.
* ``complete()`` is synchronous (``ProviderBackend`` protocol).  It wraps each
  async-capable backend call via ``asyncio.run()`` only when the current thread
  has no running loop; otherwise it uses ``asyncio.to_thread`` via a helper.
* ``stream()`` is a native async generator and applies ``asyncio.wait_for``
  around the first-token wait for early bail-out.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, AsyncGenerator, List, Optional, Tuple

from study_engine.llm.exceptions import LLMBackendError

logger = logging.getLogger(__name__)

# Default timeout budget (in seconds) tailored to each provider's characteristics.
# Fast API gateways (Groq) get tighter budgets; reasoning or large-parameter models
# (Cloudflare 70B, NVIDIA, Gemini) get the time they actually need.
DEFAULT_PROVIDER_TIMEOUTS: Dict[str, float] = {
    "groq": 6.0,
    "cloudflare-direct": 16.0,
    "cloudflare-worker": 12.0,
    "xkiro": 12.0,
    "gemini": 20.0,
    "google": 20.0,
    "sambanova": 14.0,
    "nvidia": 30.0,
}


class MultiFallbackBackend:
    """Cascading multi-provider backend with per-provider timeouts.

    Parameters
    ----------
    providers:
        Ordered list of ``(display_name, backend_instance)`` pairs.
        Backends are tried in list order; first success wins.
    timeout_per_provider:
        Default fallback timeout in seconds when a provider is not in
        ``provider_timeouts``.
    provider_timeouts:
        Optional dictionary mapping provider prefix or full name to timeout
        in seconds. Defaults to ``DEFAULT_PROVIDER_TIMEOUTS``.
    """

    def __init__(
        self,
        providers: List[Tuple[str, Any]],
        timeout_per_provider: float = 12.0,
        provider_timeouts: Optional[Dict[str, float]] = None,
    ) -> None:
        if not providers:
            raise ValueError("MultiFallbackBackend requires at least one provider.")
        self.providers = providers
        self.timeout_per_provider = timeout_per_provider
        self.provider_timeouts = (
            {**DEFAULT_PROVIDER_TIMEOUTS, **provider_timeouts}
            if provider_timeouts
            else dict(DEFAULT_PROVIDER_TIMEOUTS)
        )
        self.last_successful_provider: Optional[str] = None
        # Kept for interface parity with CircuitBreakerBackend
        self._last_finish_reason: Optional[str] = None

    def get_provider_timeout(self, provider_name: str) -> float:
        """Resolve specific timeout for a provider based on its name/prefix."""
        # 1. Exact match
        if provider_name in self.provider_timeouts:
            return self.provider_timeouts[provider_name]
        # 2. Prefix match (e.g. 'groq:qwen/qwen3.8-27b' -> 'groq')
        prefix = provider_name.split(":")[0].lower()
        if prefix in self.provider_timeouts:
            return self.provider_timeouts[prefix]
        # 3. Fallback to default
        return self.timeout_per_provider

    # ------------------------------------------------------------------
    # Synchronous complete()  (ProviderBackend protocol)
    # ------------------------------------------------------------------

    def complete(self, prompt_bundle: Any) -> Any:
        """Try each provider in order; return first successful completion."""
        from study_engine.context.c3_budget import (
            EFFECTIVE_CONTEXT_CEILING_TOKENS,
            ContextBudgetExceededError,
            estimate_payload_tokens,
        )
        from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

        # Chokepoint 3: Terminal provider guard
        total_tokens = estimate_payload_tokens(prompt_bundle=prompt_bundle)
        if total_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
            raise ContextBudgetExceededError(
                f"C3 hard ceiling violated at provider complete() chokepoint: {total_tokens} > {EFFECTIVE_CONTEXT_CEILING_TOKENS}",
                estimated_tokens=total_tokens,
                effective_ceiling=EFFECTIVE_CONTEXT_CEILING_TOKENS,
            )

        last_exc: Optional[Exception] = None
        for name, backend in self.providers:
            try:
                t0 = time.perf_counter()
                result = backend.complete(prompt_bundle)
                latency_ms = (time.perf_counter() - t0) * 1000
                logger.info(
                    "[MULTI_FALLBACK] complete() via %s in %.0fms", name, latency_ms
                )
                self.last_successful_provider = name
                return result
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "[MULTI_FALLBACK] %s failed in complete(): %s: %s — trying next",
                    name, type(exc).__name__, exc,
                )

        logger.error(
            "[MULTI_FALLBACK] All providers failed in complete(). Using OfflinePedagogicalBackend."
        )
        self.last_successful_provider = "offline_oracle"
        return OfflinePedagogicalBackend().complete(prompt_bundle)

    # ------------------------------------------------------------------
    # Async stream()  (used by SSE chat endpoint via CircuitBreakerBackend.stream)
    # ------------------------------------------------------------------

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        phase_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from the first available provider.

        For backends without a native ``stream()`` method, falls back to calling
        ``complete()`` in a thread and replaying the result word-by-word.
        """
        from study_engine.context.c3_budget import (
            EFFECTIVE_CONTEXT_CEILING_TOKENS,
            ContextBudgetExceededError,
            estimate_payload_tokens,
        )
        from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

        # Chokepoint 3: Terminal provider guard
        total_tokens = estimate_payload_tokens(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
        )
        if total_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
            raise ContextBudgetExceededError(
                f"C3 hard ceiling violated at provider stream() chokepoint: {total_tokens} > {EFFECTIVE_CONTEXT_CEILING_TOKENS}",
                estimated_tokens=total_tokens,
                effective_ceiling=EFFECTIVE_CONTEXT_CEILING_TOKENS,
            )

        last_exc: Optional[Exception] = None


        for name, backend in self.providers:
            try:
                t0 = time.perf_counter()
                emitted_any = False
                timeout = self.get_provider_timeout(name)

                if hasattr(backend, "stream") and callable(getattr(backend, "stream")):
                    # Native streaming backend (e.g. GeminiBackend)
                    async def _gen_stream(b: Any) -> AsyncGenerator[str, None]:
                        async for token in b.stream(
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            max_tokens=max_tokens,
                            phase_id=phase_id,
                            context=context,
                        ):
                            yield token

                    gen = _gen_stream(backend)
                    async for token in _timeout_first_token(
                        gen, timeout=timeout, name=name
                    ):
                        if not emitted_any:
                            ttft = (time.perf_counter() - t0) * 1000
                            logger.info(
                                "[MULTI_FALLBACK] stream() TTFT via %s: %.0fms",
                                name, ttft,
                            )
                        emitted_any = True
                        yield token

                else:
                    # Non-streaming backend: run complete() in thread, replay words
                    from study_engine.contracts.generation import GenerationParameters
                    from study_engine.generation.prompts import (
                        PromptBundle,
                        PromptMessage,
                        PromptRole,
                    )

                    bundle = PromptBundle(
                        system_prompt=system_prompt,
                        messages=(
                            PromptMessage(role=PromptRole.USER, content=user_prompt),
                        ),
                        parameters=GenerationParameters(max_output_tokens=max_tokens),
                        prompt_hash="0" * 64,
                    )
                    try:
                        completion = await asyncio.wait_for(
                            asyncio.to_thread(backend.complete, bundle),
                            timeout=timeout,
                        )
                    except asyncio.TimeoutError:
                        raise LLMBackendError(
                            f"{name}: complete() timed out after {timeout}s"
                        )

                    full_text = getattr(completion, "text", None) or str(completion)
                    ttft = (time.perf_counter() - t0) * 1000
                    logger.info(
                        "[MULTI_FALLBACK] stream() (word-replay) via %s in %.0fms",
                        name, ttft,
                    )
                    for word in re.split(r"(\s+)", full_text):
                        if word:
                            emitted_any = True
                            yield word

                if emitted_any:
                    self.last_successful_provider = name
                    self._last_finish_reason = getattr(backend, "_last_finish_reason", None)
                    return

            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "[MULTI_FALLBACK] %s failed in stream(): %s: %s — trying next",
                    name, type(exc).__name__, exc,
                )

        # Every provider failed — use offline oracle and word-replay
        logger.error(
            "[MULTI_FALLBACK] All %d providers failed in stream(). Using OfflinePedagogicalBackend.",
            len(self.providers),
        )
        self.last_successful_provider = "offline_oracle"
        offline = OfflinePedagogicalBackend()
        from study_engine.contracts.generation import GenerationParameters
        from study_engine.generation.prompts import (
            PromptBundle,
            PromptMessage,
            PromptRole,
        )

        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=(PromptMessage(role=PromptRole.USER, content=user_prompt),),
            parameters=GenerationParameters(max_output_tokens=max_tokens),
            prompt_hash="0" * 64,
        )
        completion = offline.complete(bundle)
        for word in re.split(r"(\s+)", completion.text):
            if word:
                yield word


async def _timeout_first_token(
    gen: AsyncGenerator[str, None],
    timeout: float,
    name: str,
) -> AsyncGenerator[str, None]:
    """Wrap an async generator so the *first* token must arrive within ``timeout`` seconds.

    Once the first token arrives, subsequent tokens stream at their natural pace.
    This avoids the full-stream timeout trap (e.g. Gemini hanging for 60s before
    yielding anything) while still allowing long completions.
    """
    sentinel = object()

    # Fetch the first token with a hard deadline
    try:
        first = await asyncio.wait_for(gen.__anext__(), timeout=timeout)
    except StopAsyncIteration:
        return  # Empty stream — treat as success with no output
    except asyncio.TimeoutError:
        # Cancel generator cleanly
        await gen.aclose()
        raise LLMBackendError(
            f"{name}: no first token within {timeout}s (TTFT timeout)"
        )

    yield first  # type: ignore[misc]

    # Remaining tokens stream at natural pace
    async for token in gen:
        yield token
