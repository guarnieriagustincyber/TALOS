"""Adversarial and Contractual Test Suite for C3 Hard Ceiling (Gate B).

Normative Reference: CP108 Adjudication & CP109 Implementation.
Contracts Verified:
  - D_C3_1 = C (Layered Budget: nominal 5000, effective 4761)
  - D_C3_2 = A+B (Deterministic Hierarchical Pruning + Fail-Closed)
  - D_C3_3 = A (ceil(chars / 4) with 5% safety margin)
  - Zero blind truncation
  - Triple Chokepoint Enforcement:
      1. StructuredResponsePipeline.generate_phased_response
      2. StructuredResponsePipeline._stream_tokens
      3. MultiFallbackBackend (complete & stream)
  - Robustness across Cases 1-8 and Fixtures A-E from CP108.
"""

import asyncio
import time
from typing import Any, AsyncGenerator, List, Optional
import pytest


from study_engine.context.c3_budget import (
    GLOBAL_CONTEXT_CEILING_TOKENS,
    EFFECTIVE_CONTEXT_CEILING_TOKENS,
    EFFECTIVE_CONTEXT_CEILING_CHARS,
    BUDGET_SYSTEM_TOKENS,
    BUDGET_QUERY_TOKENS,
    BUDGET_PRIMARY_EVIDENCE_TOKENS,
    BUDGET_SECONDARY_EVIDENCE_TOKENS,
    BUDGET_HISTORY_TOKENS,
    BUDGET_PEDAGOGY_TOKENS,
    BUDGET_MEMORY_TOKENS,
    BUDGET_RESERVE_TOKENS,
    ContextBudgetExceededError,
    estimate_tokens,
    estimate_payload_tokens,
    enforce_c3_budget,
    prune_evidence_text_deterministically,
    prune_history_turns_deterministically,
)
from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
from study_engine.pedagogy.contract import PedagogicalContract, ResponsePhase
from study_engine.pedagogy.structured_pipeline import (
    StructuredResponsePipeline,
    StreamEvent,
)
from study_engine.web.routes.chat import EpistemicContextPack
from study_engine.llm.multi_fallback import MultiFallbackBackend


class MockBackendTracking:
    """Mock LLM backend that records whether it was called and with what arguments."""

    def __init__(self, token_response: str = "Respuesta simulada del LLM."):
        self.called = False
        self.call_count = 0
        self.last_system_prompt: Optional[str] = None
        self.last_user_prompt: Optional[str] = None
        self.last_bundle: Optional[PromptBundle] = None
        self.token_response = token_response

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        phase_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        self.called = True
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        for word in self.token_response.split():
            yield word + " "

    def complete(self, prompt_bundle: PromptBundle) -> Any:
        self.called = True
        self.call_count += 1
        self.last_bundle = prompt_bundle

        class _MockResp:
            text = "Respuesta completada mock"
            finish_reason = "stop"

        return _MockResp()


@pytest.fixture
def mock_backend():
    return MockBackendTracking()


@pytest.fixture
def test_contract():
    return PedagogicalContract(
        notebook_id="fase0-soc",
        base_system_prompt="Base Pedagogical Prompt TALOS Cátedra Sistemas Operativos.",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                phase_prompt_template="Fase conceptual para: {user_query}",
                max_tokens=1000,
            )
        ],
    )


@pytest.fixture
def pipeline(mock_backend, test_contract):
    return StructuredResponsePipeline(contract=test_contract, llm_backend=mock_backend)



# ==============================================================================
# UNIT & CONTRACT TESTS
# ==============================================================================

def test_c3_normative_constants_and_sub_budgets():
    """Verify that all C3 constants and sub-budgets are mathematically coherent."""
    assert GLOBAL_CONTEXT_CEILING_TOKENS == 5000
    assert EFFECTIVE_CONTEXT_CEILING_TOKENS == 4761
    assert EFFECTIVE_CONTEXT_CEILING_CHARS == 19044

    # Verify sum of sub-budgets does not exceed effective ceiling
    sub_sum = (
        BUDGET_SYSTEM_TOKENS
        + BUDGET_QUERY_TOKENS
        + BUDGET_PRIMARY_EVIDENCE_TOKENS
        + BUDGET_SECONDARY_EVIDENCE_TOKENS
        + BUDGET_HISTORY_TOKENS
        + BUDGET_PEDAGOGY_TOKENS
        + BUDGET_MEMORY_TOKENS
        + BUDGET_RESERVE_TOKENS
    )
    assert sub_sum <= EFFECTIVE_CONTEXT_CEILING_TOKENS
    assert sub_sum == 4761


def test_c3_token_estimation_conservative():
    """Verify ceil(len(text)/4) token estimation formula."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("1") == 1
    assert estimate_tokens("1234") == 1
    assert estimate_tokens("12345") == 2
    assert estimate_tokens("a" * 19044) == 4761
    assert estimate_tokens("a" * 19045) == 4762


# ==============================================================================
# PIPELINE INTEGRATION CASES (CASES 1 - 8)
# ==============================================================================

@pytest.mark.anyio
async def test_case_1_small_prompt_passes_intact(pipeline, mock_backend):
    """Caso 1: Prompt pequeño dentro de presupuesto -> pasa intacto sin podas."""
    user_query = "¿Qué es una llamada al sistema en Linux?"
    events = []
    async for event in pipeline.generate_phased_response(user_query=user_query):
        events.append(event)

    # Must emit phase_start and tokens, must NOT emit error
    assert any(e.event_type == "phase_start" for e in events)
    assert any(e.event_type == "phase_token" for e in events)
    assert not any(e.event_type == "error" for e in events)
    assert mock_backend.called is True
    assert mock_backend.call_count == 1

    # Check payload size sent to backend
    payload_tokens = estimate_payload_tokens(
        mock_backend.last_system_prompt, mock_backend.last_user_prompt
    )
    assert payload_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_case_2_evidence_overflow_prunes_secondary(pipeline, mock_backend):
    """Caso 2: Evidence overflow -> poda evidencia periférica preservando primaria."""
    primary_chunk = "[Fuente: Guía Cátedra SOC] " + ("Llamadas al sistema y modo kernel. " * 80)
    peripheral_chunk_1 = "[Fuente: Manual Externo POSIX] " + ("Detalle secundario de estándares. " * 300)
    peripheral_chunk_2 = "[Fuente: Libro Anexo] " + ("Notas históricas sobre UNIX v6. " * 300)

    massive_evidence = f"{primary_chunk}\n\n{peripheral_chunk_1}\n\n{peripheral_chunk_2}"
    assert estimate_tokens(massive_evidence) > BUDGET_PRIMARY_EVIDENCE_TOKENS + BUDGET_SECONDARY_EVIDENCE_TOKENS

    pack = EpistemicContextPack(
        formatted_context=massive_evidence,
        citations=["Guía Cátedra", "Manual Externo", "Libro Anexo"],
        chunks=["chunk1", "chunk2", "chunk3"],
    )

    events = []
    async for event in pipeline.generate_phased_response(
        user_query="Explicá syscalls",
        context_pack=pack,
    ):
        events.append(event)

    # Must succeed after pruning
    assert any(e.event_type == "phase_start" for e in events)
    assert not any(e.event_type == "error" for e in events)
    assert mock_backend.called is True

    # Primary evidence must still be preserved in prompt sent to LLM
    assert "Guía Cátedra SOC" in mock_backend.last_user_prompt

    # Total payload delivered must be strictly <= effective ceiling
    payload_tokens = estimate_payload_tokens(
        mock_backend.last_system_prompt, mock_backend.last_user_prompt
    )
    assert payload_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_case_3_history_overflow_prunes_progressively(pipeline, mock_backend):
    """Caso 3: History overflow -> poda turnos progresivamente del más viejo al más nuevo."""
    history = [
        {"role": "user", "content": "Pregunta antigua turno 1: " + ("detalles iniciales " * 60)},
        {"role": "assistant", "content": "Respuesta antigua turno 1: " + ("explicación previa " * 60)},
        {"role": "user", "content": "Pregunta antigua turno 2: " + ("más dudas " * 60)},
        {"role": "assistant", "content": "Respuesta antigua turno 2: " + ("más respuestas " * 60)},
        {"role": "user", "content": "Pregunta reciente turno 3: contexto inmediato importante"},
    ]

    evidence = "[Fuente: Silberschatz] " + ("Procesos y threads en SO. " * 150)
    pack = EpistemicContextPack(
        formatted_context=evidence,
        citations=["Silberschatz"],
        chunks=["chunk_proc"],
    )

    events = []
    async for event in pipeline.generate_phased_response(
        user_query="¿Cómo interactúan?",
        context_pack=pack,
        recent_turns=history,
    ):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert not any(e.event_type == "error" for e in events)
    assert mock_backend.called is True

    # Total payload delivered must be strictly <= effective ceiling
    payload_tokens = estimate_payload_tokens(
        mock_backend.last_system_prompt, mock_backend.last_user_prompt
    )
    assert payload_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_case_4_memory_overflow_pruning(pipeline, mock_backend):
    """Caso 4: Memory overflow -> poda memoria contextual según prioridad."""
    huge_memory = "Memoria contextual histórica: " + ("conceptos previos del alumno " * 400)
    events = []
    async for event in pipeline.generate_phased_response(
        user_query="Explicá interrupciones",
        cognitive_profile_block=huge_memory,
    ):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert not any(e.event_type == "error" for e in events)
    assert mock_backend.called is True
    payload_tokens = estimate_payload_tokens(
        mock_backend.last_system_prompt, mock_backend.last_user_prompt
    )
    assert payload_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_case_5_fallback_overflow_protected(pipeline, mock_backend):
    """Caso 5: Fallback overflow -> el fallback masivo de citas queda acotado."""
    citations_raw = [
        f"[Fuente Cita {i}]: " + ("Texto extenso de fallback de la cita. " * 50)
        for i in range(25)
    ]
    # Simulate what chat.py does when expansion fails:
    from study_engine.context.c3_budget import (
        BUDGET_PRIMARY_EVIDENCE_TOKENS,
        BUDGET_SECONDARY_EVIDENCE_TOKENS,
    )
    raw_fallback = "\n\n".join(citations_raw)
    max_ev_tokens = BUDGET_PRIMARY_EVIDENCE_TOKENS + BUDGET_SECONDARY_EVIDENCE_TOKENS
    bounded_fallback, was_p = prune_evidence_text_deterministically(raw_fallback, max_tokens=max_ev_tokens)
    assert was_p is True
    assert estimate_tokens(bounded_fallback) <= max_ev_tokens

    pack = EpistemicContextPack(
        formatted_context=bounded_fallback,
        citations=["cit1", "cit2"],
        chunks=["c1", "c2"],
    )

    events = []
    async for event in pipeline.generate_phased_response(
        user_query="¿Qué dice el programa?",
        context_pack=pack,
    ):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert not any(e.event_type == "error" for e in events)
    payload_tokens = estimate_payload_tokens(
        mock_backend.last_system_prompt, mock_backend.last_user_prompt
    )
    assert payload_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_case_6_irreducible_overflow_fails_closed(pipeline, mock_backend):
    """Caso 6: Irreducible overflow -> FAIL-CLOSED con 0 llamadas al LLM."""
    # A user query so massive (e.g. 25,000 characters = ~6250 tokens) that cannot fit
    # into EFFECTIVE_CONTEXT_CEILING_TOKENS (4761 tokens) even if everything else is 0.
    massive_query = "Query adversarial irreducible: " + ("palabra clave " * 3000)
    assert estimate_tokens(massive_query) > EFFECTIVE_CONTEXT_CEILING_TOKENS

    events = []
    async for event in pipeline.generate_phased_response(user_query=massive_query):
        events.append(event)

    # Invariant check:
    # 1. Must emit event_type="error" with error_code="CONTEXT_BUDGET_EXCEEDED"
    error_events = [e for e in events if e.event_type == "error"]
    assert len(error_events) >= 1
    assert error_events[0].payload.get("error_code") == "CONTEXT_BUDGET_EXCEEDED"

    # 2. Must NOT emit phase_start
    assert not any(e.event_type == "phase_start" for e in events)

    # 3. Must NOT invoke LLM (0 provider calls)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_case_7_and_8_provider_window_independence(pipeline, mock_backend):
    """Casos 7 y 8: TALOS aplica su propio ceiling de 4.761 tokens independientemente

    de si el provider declara 1.000 tokens o 1.000.000 tokens.
    """
    # Mocking provider with 1M tokens capacity
    setattr(mock_backend, "max_context_tokens", lambda: 1_000_000)

    # Large evidence that would be allowed by a 1M provider but exceeds TALOS 4761
    oversized_evidence = "[Fuente: Enciclopedia] " + ("Contenido voluminoso " * 1500)
    pack = EpistemicContextPack(
        formatted_context=oversized_evidence,
        citations=["Enciclopedia"],
        chunks=["e1"],
    )

    events = []
    async for event in pipeline.generate_phased_response(
        user_query="¿Qué contiene?",
        context_pack=pack,
    ):
        events.append(event)

    assert mock_backend.called is True
    # TALOS strictly enforced its own 4761 limit!
    final_tokens = estimate_payload_tokens(
        mock_backend.last_system_prompt, mock_backend.last_user_prompt
    )
    assert final_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


# ==============================================================================
# REPRODUCTION OF CP108 FIXTURES A - E
# ==============================================================================

@pytest.mark.anyio
async def test_fixture_a_reproduction(pipeline, mock_backend):
    """Fixture A (Modest retrieval 2.5k, before C3 was 6.306 tokens).

    Now with C3: must be <= 4.761 tokens.
    """
    evidence = "[Fuente: Cátedra SOC] " + ("Concepto formal de proceso y hebra. " * 250)
    pack = EpistemicContextPack(formatted_context=evidence, citations=["Cátedra SOC"], chunks=["c1"])
    events = []
    async for event in pipeline.generate_phased_response(user_query="Explicá procesos", context_pack=pack):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert mock_backend.called is True
    tokens = estimate_payload_tokens(mock_backend.last_system_prompt, mock_backend.last_user_prompt)
    assert tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_fixture_b_reproduction(pipeline, mock_backend):
    """Fixture B (Retrieval near ceiling 4.6k, before C3 was 10.678 tokens).

    Now with C3: pruned to <= 4.761 tokens.
    """
    evidence = "[Fuente: Stallman C] " + ("Punteros, estructuras y memoria dinámica en ANSI C. " * 450)
    pack = EpistemicContextPack(formatted_context=evidence, citations=["Stallman C"], chunks=["c1"])
    events = []
    async for event in pipeline.generate_phased_response(user_query="Explicá malloc y free", context_pack=pack):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert mock_backend.called is True
    tokens = estimate_payload_tokens(mock_backend.last_system_prompt, mock_backend.last_user_prompt)
    assert tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_fixture_c_reproduction(pipeline, mock_backend):
    """Fixture C (Empty Fallback, before C3 was 10.886 tokens).

    Now with C3: bounded and pruned to <= 4.761 tokens.
    """
    citations = [f"[Fuente: Cita {i}] " + ("Contenido extenso de cita " * 80) for i in range(15)]
    evidence = "\n\n".join(citations)
    pack = EpistemicContextPack(formatted_context=evidence, citations=["cit"], chunks=["c"])
    events = []
    async for event in pipeline.generate_phased_response(user_query="Consulta sin expansión", context_pack=pack):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert mock_backend.called is True
    tokens = estimate_payload_tokens(mock_backend.last_system_prompt, mock_backend.last_user_prompt)
    assert tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_fixture_d_reproduction(pipeline, mock_backend):
    """Fixture D (Long History 4 turns, before C3 was 10.936 tokens).

    Now with C3: pruned to <= 4.761 tokens.
    """
    history = [
        {"role": "user", "content": "Turno 1: " + ("historia previa " * 50)},
        {"role": "assistant", "content": "Respuesta 1: " + ("explicación " * 50)},
        {"role": "user", "content": "Turno 2: " + ("más preguntas " * 50)},
        {"role": "assistant", "content": "Respuesta 2: " + ("más detalles " * 50)},
    ]
    evidence = "[Fuente: Guía] " + ("Evidencia sustantiva del tema. " * 350)
    pack = EpistemicContextPack(formatted_context=evidence, citations=["Guía"], chunks=["c"])
    events = []
    async for event in pipeline.generate_phased_response(
        user_query="Continuar tema",
        context_pack=pack,
        recent_turns=history,
    ):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert mock_backend.called is True
    tokens = estimate_payload_tokens(mock_backend.last_system_prompt, mock_backend.last_user_prompt)
    assert tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


@pytest.mark.anyio
async def test_fixture_e_reproduction(pipeline, mock_backend):
    """Fixture E (Evidence 8k, before C3 was 10.825 tokens).

    Now with C3: pruned to <= 4.761 tokens.
    """
    evidence = "[Fuente: Bibliografía Completa] " + ("Capítulo entero de memoria virtual y paginación. " * 750)
    pack = EpistemicContextPack(formatted_context=evidence, citations=["Bibliografía"], chunks=["c"])
    events = []
    async for event in pipeline.generate_phased_response(user_query="Explicá paginación", context_pack=pack):
        events.append(event)

    assert any(e.event_type == "phase_start" for e in events)
    assert mock_backend.called is True
    tokens = estimate_payload_tokens(mock_backend.last_system_prompt, mock_backend.last_user_prompt)
    assert tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


# ==============================================================================
# DEFENSE-IN-DEPTH CHOKEPOINTS 2 & 3 TESTS
# ==============================================================================

@pytest.mark.anyio
async def test_chokepoint_2_stream_tokens_raises_on_breach(pipeline):
    """Chokepoint 2: Directly calling _stream_tokens with oversized payload must raise ContextBudgetExceededError."""
    huge_system = "A" * (EFFECTIVE_CONTEXT_CEILING_CHARS + 500)
    with pytest.raises(ContextBudgetExceededError) as exc_info:
        async for _ in pipeline._stream_tokens(
            system_prompt=huge_system,
            user_prompt="test",
            max_tokens=500,
        ):
            pass

    assert exc_info.value.estimated_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS


def test_chokepoint_3_multi_fallback_complete_raises_on_breach():
    """Chokepoint 3: Calling MultiFallbackBackend.complete with oversized bundle must raise ContextBudgetExceededError."""
    backend = MultiFallbackBackend(providers=[("mock", MockBackendTracking())])
    huge_text = "B" * (EFFECTIVE_CONTEXT_CEILING_CHARS + 500)
    bundle = PromptBundle(
        system_prompt=huge_text,
        messages=(PromptMessage(role=PromptRole.USER, content="hello"),),
        parameters=GenerationParameters(max_output_tokens=500),
        prompt_hash="0" * 64,
    )

    with pytest.raises(ContextBudgetExceededError) as exc_info:
        backend.complete(bundle)

    assert exc_info.value.estimated_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS
    assert backend.last_successful_provider is None


@pytest.mark.anyio
async def test_chokepoint_3_multi_fallback_stream_raises_on_breach():
    """Chokepoint 3: Calling MultiFallbackBackend.stream with oversized payload must raise ContextBudgetExceededError."""
    backend = MultiFallbackBackend(providers=[("mock", MockBackendTracking())])
    huge_text = "C" * (EFFECTIVE_CONTEXT_CEILING_CHARS + 500)

    with pytest.raises(ContextBudgetExceededError) as exc_info:
        async for _ in backend.stream(
            system_prompt=huge_text,
            user_prompt="hello",
            max_tokens=500,
        ):
            pass

    assert exc_info.value.estimated_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS


# ==============================================================================
# PERFORMANCE OVERHEAD MEASUREMENT
# ==============================================================================

def test_performance_overhead_measurement():
    """Measure the computational latency of C3 budget evaluation and pruning."""
    sample_system = "Base system prompt de cátedra con instrucciones completas. " * 30
    sample_query = "¿Cómo funciona la gestión de páginas sucias (dirty pages) en el kernel?"
    sample_evidence = "[Fuente: Linux Kernel] " + ("Código del subsistema mm y page cache. " * 200)

    latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        retained, report = enforce_c3_budget(
            system_prompt=sample_system,
            user_query=sample_query,
            evidence_text=sample_evidence,
        )
        t_el = (time.perf_counter() - t0) * 1000
        latencies.append(t_el)

    avg_ms = sum(latencies) / len(latencies)
    max_ms = max(latencies)
    print(f"\n[PERFORMANCE] C3 enforce_c3_budget Latency: avg={avg_ms:.3f}ms, max={max_ms:.3f}ms")
    # Must run smoothly and fast (under 50ms)
    assert avg_ms < 50.0
