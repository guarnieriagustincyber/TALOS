"""Tests for PhaseHistory accumulation and inter-phase navigation (Fase 5.8 / Refinamiento 1)."""

import pytest

from study_engine.llm.backends import MockBackend, ProviderCompletion
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.structured_pipeline import PhaseHistory, StructuredResponsePipeline


def test_phase_history_carries_analogy_and_pseudocode_to_python_code():
    """Refinamiento 1: Phase 3 prompt contains outputs from both Phase 1 (analogy) and Phase 2 (pseudocode)."""
    import asyncio

    async def _run():
        contract = FASE0_CONTRACT
        phase_history = PhaseHistory()

        prompts_seen = []

        class HistoryTrackingBackend:
            def complete(self, prompt_bundle):
                # Record user prompt assembled for this phase
                prompts_seen.append(prompt_bundle.messages[0].content)
                phase_count = len(prompts_seen)
                if phase_count == 1:
                    txt = "Analogía de las casillas de correo para punteros: cada casilla tiene un número (dirección) y contenido."
                elif phase_count == 2:
                    txt = "ALGORITMO: Leer direccion_casilla; Obtener contenido; Fin."
                else:
                    txt = "def leer_casilla(direccion_casilla):\n    return memoria[direccion_casilla]"
                return ProviderCompletion(text=txt, latency_ms=10.0, model="tracker")

        backend = HistoryTrackingBackend()
        pipeline = StructuredResponsePipeline(
            contract=contract,
            llm_backend=backend,
            phase_history=phase_history,
        )

        query = "¿Cómo funciona un puntero?"

        # 1. Execute Conceptual Phase (Phase 1)
        async for _ in pipeline.generate_phased_response(query, requested_phase="conceptual"):
            pass
        assert len(phase_history.get_all()) == 1
        assert phase_history.get_all()[0].phase_id == "conceptual"

        # 2. Execute Pseudocode Phase (Phase 2)
        async for _ in pipeline.generate_phased_response(query, requested_phase="pseudocode"):
            pass
        assert len(phase_history.get_all()) == 2
        assert phase_history.get_all()[1].phase_id == "pseudocode"

        # Inspect the prompt built for Pseudocode: must contain Phase 1's analogy
        prompt_for_pseudocode = prompts_seen[1]
        assert "casillas de correo" in prompt_for_pseudocode
        assert "FASE PREVIA COMPLETADA: [CONCEPTUAL]" in prompt_for_pseudocode

        # 3. Execute Python Code Phase (Phase 3)
        async for _ in pipeline.generate_phased_response(query, requested_phase="python_code"):
            pass
        assert len(phase_history.get_all()) == 3

        # Refinamiento 1 Invariant: Prompt for Python code must contain BOTH Phase 1 AND Phase 2!
        prompt_for_code = prompts_seen[2]
        assert "casillas de correo" in prompt_for_code
        assert "ALGORITMO: Leer direccion_casilla" in prompt_for_code
        assert "FASE PREVIA COMPLETADA: [CONCEPTUAL]" in prompt_for_code
        assert "FASE PREVIA COMPLETADA: [PSEUDOCODE]" in prompt_for_code

    asyncio.run(_run())
