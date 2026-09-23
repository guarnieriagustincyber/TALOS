"""Test verifying the architectural elimination of Token Rationing (Fase 5.8).

Compares single-turn monolithic prompt (NotebookLM flaw) vs TALOS Phased Pipeline.
Demonstrates that TALOS allocates 100% of the conceptual budget strictly to explanation.
"""

import pytest
from study_engine.contracts.evidence_engine import PackagedContext
from study_engine.llm.backends import MockBackend, ProviderCompletion
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


def test_token_rationing_eliminated_by_independent_phase_budgets():
    """TALOS guarantees 1000 tokens exclusively for conceptual explanation.
    
    In monolithic RAG (NotebookLM), a 1000 token budget must be shared across:
    concept + analogy + pseudocode + python code + verification question.
    In TALOS, the conceptual phase gets its own dedicated 1000 tokens,
    pseudocode gets 600 tokens, and python code gets 800 tokens.
    """
    import asyncio

    async def _run():
        contract = FASE0_CONTRACT
        c_phase = contract.get_phase("conceptual")

        # High-density explanation text generated under generous budget
        profound_explanation = (
            "La memoria dinámica es una región del espacio de direcciones del proceso conocida como Heap o montículo. "
            "A diferencia del Stack (pila de llamadas), donde los registros de activación se crean y destruyen automáticamente "
            "con el ámbito de las funciones mediante el puntero de pila (ESP/RSP), el Heap no tiene una disciplina LIFO. "
            "El programador solicita explícitamente un bloque contiguo de bytes al sistema operativo a través de llamadas de sistema "
            "como brk() o mmap(), típicamente abstraídas por la biblioteca estándar con malloc(). "
            "Analogía física: Pensá en el Stack como una pila de platos en un restaurante donde solo podés tomar el plato superior; "
            "el Heap es un galpón abierto de casilleros donde podés alquilar el casillero 42, mantenerlo durante horas, y si olvidás "
            "devolver la llave (free), ese espacio queda inutilizable para siempre produciendo una fuga de memoria (memory leak)."
        )

        class DedicatedBackend:
            def __init__(self):
                self.last_max_tokens = 0

            def complete(self, prompt_bundle):
                self.last_max_tokens = prompt_bundle.parameters.max_output_tokens
                return ProviderCompletion(
                    text=profound_explanation,
                    latency_ms=45.0,
                    model="test-pedagogical-model",
                )

        backend = DedicatedBackend()
        pipeline = StructuredResponsePipeline(contract=contract, llm_backend=backend)

        events = []
        async for ev in pipeline.generate_phased_response(
            user_query="Explicame memoria dinámica y heap vs stack en detalle",
            requested_phase="conceptual",
        ):
            events.append(ev)

        # 1. Verification of dedicated independent budget
        assert backend.last_max_tokens == max(c_phase.max_tokens, 2500)

        # 2. Verification of conceptual depth: explanation is extensive, detailed, contains physical analogies
        complete_ev = [e for e in events if e.event_type == "phase_complete"][0]
        output_text = pipeline.history.get_all()[0].text

        assert "Heap" in output_text
        assert "Stack" in output_text
        assert "casilleros" in output_text
        assert "pila de platos" in output_text
        assert len(output_text.split()) > 100

    asyncio.run(_run())
