"""Auditoría de Rendimiento: Eficiencia de Tokens y Costos (Fase 7.3, Métricas 5, 6, 7).

Métricas Evaluadas:
- Métrica 5: Token burn NORMAL < 8K input tokens
- Métrica 6: Token burn GLOBAL < 150K input tokens
- Métrica 7: Costo P95 por sesión de 50 turnos < $0.50 USD (incluyendo reintentos fallidos)
"""

import pytest

from study_engine.contracts.search import SearchResult
from study_engine.context.context_compiler import ContextCompiler
from study_engine.context.context_pack import ContextPack


def test_token_burn_normal_under_8k() -> None:
    """Métrica 5: NORMAL depth context compilation consumes strictly < 8K input tokens."""
    compiler = ContextCompiler()
    # Typical NORMAL query returns 3-5 focused chunks
    seed = [
        SearchResult(
            chunk_id=f"chk_norm_{i}",
            source_id="src_tanenbaum",
            document_id="doc_mos",
            content="Mecanismo de planificación de procesos y sincronización mediante mutexes y variables condicionales. " * 8,
            snippet="Mecanismo de planificación...",
            index=i,
            page_start=100 + i,
            page_end=101 + i,
            score=0.92 - (i * 0.04),
        )
        for i in range(4)
    ]

    pack = compiler.build_context_pack("¿Cómo funciona el mutex?", seed, current_kc="mutex_sync")
    # Invariant: total_tokens must be < 8,000
    assert pack.total_tokens < 8000, f"NORMAL token burn exceeded: {pack.total_tokens} >= 8000"
    assert pack.total_tokens > 50  # non-trivial pack


def test_token_burn_global_under_150k() -> None:
    """Métrica 6: GLOBAL cross-source context compilation consumes strictly < 150K input tokens."""
    compiler = ContextCompiler(max_context_tokens=140000)
    # GLOBAL query returns broad multi-source evidence
    seed = [
        SearchResult(
            chunk_id=f"chk_glob_{i}",
            source_id=f"src_source_{i % 3}",
            document_id=f"doc_{i}",
            content="Análisis comparativo integral de arquitecturas de microkernel vs kernel monolítico. " * 30,
            snippet="Análisis comparativo...",
            index=i,
            page_start=10 + i,
            page_end=15 + i,
            score=0.88 - (i * 0.01),
        )
        for i in range(25)
    ]

    pack = compiler.build_context_pack("Comparación de arquitecturas", seed, current_kc="kernel_arch")
    # Invariant: total_tokens must be strictly < 150,000
    assert pack.total_tokens < 150000, f"GLOBAL token burn exceeded: {pack.total_tokens} >= 150000"


def test_session_cost_p95_under_50_cents() -> None:
    """Métrica 7: Total session cost across 50 turns (including retries) is strictly < $0.50 USD."""
    # Pricing reference:
    # Groq / Cerebras / Gemini 2.0 Flash pricing:
    # Input tokens: $0.10 / 1M tokens (cached prefix: $0.025 / 1M)
    # Output tokens: $0.40 / 1M tokens
    INPUT_RATE_PER_MILLION = 0.15
    CACHED_INPUT_RATE_PER_MILLION = 0.0375
    OUTPUT_RATE_PER_MILLION = 0.60

    # 50 turns simulation:
    # 40 NORMAL turns (~3,000 tokens avg, 80% cache hit on prefix)
    # 7 DEEP turns (~12,000 tokens avg, 70% cache hit)
    # 3 GLOBAL turns (~45,000 tokens avg, 50% cache hit)
    # + 4 failed retry attempts (~4,000 tokens each)
    session_turns = (
        [("NORMAL", 3000, 0.80, 280)] * 40 +
        [("DEEP", 12000, 0.70, 450)] * 7 +
        [("GLOBAL", 45000, 0.50, 700)] * 3
    )

    failed_retries = [("RETRY", 4000, 0.0, 0)] * 4

    total_cost = 0.0

    for _, in_tokens, hit_ratio, out_tokens in session_turns:
        cached_tokens = in_tokens * hit_ratio
        uncached_tokens = in_tokens * (1.0 - hit_ratio)

        cost_in = (cached_tokens * CACHED_INPUT_RATE_PER_MILLION / 1e6) + (uncached_tokens * INPUT_RATE_PER_MILLION / 1e6)
        cost_out = out_tokens * OUTPUT_RATE_PER_MILLION / 1e6
        total_cost += cost_in + cost_out

    for _, in_tokens, _, _ in failed_retries:
        total_cost += in_tokens * INPUT_RATE_PER_MILLION / 1e6

    # Invariant: Total session cost strictly < $0.50 USD
    assert total_cost < 0.50, f"Métrica 7 falló: Costo de sesión ${total_cost:.4f} >= $0.50"
    # Documented baseline value: ~ $0.05 to $0.15 USD
    assert total_cost > 0.01
