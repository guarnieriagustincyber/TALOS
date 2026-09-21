"""Tests for StructuredResponsePipeline multi-phase streaming and independent token budgets (Fase 5.8)."""

import asyncio
import pytest

from study_engine.contracts.evidence_engine import PackagedContext
from study_engine.llm.backends import MockBackend
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import PhaseHistory, StructuredResponsePipeline


def test_structured_pipeline_conceptual_phase_streaming():
    """Conceptual phase generates stream events and completes without raw code blocks."""
    async def _run():
        mock_llm = MockBackend(
            canned_text="Imaginate la memoria RAM como una hilera infinita de casilleros numerados en una oficina postal."
        )
        pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=mock_llm)

        events = []
        tokens = []
        async for ev in pipeline.generate_phased_response(
            user_query="¿Qué es un puntero en memoria?",
            requested_phase="conceptual",
        ):
            events.append(ev)
            if ev.event_type == "phase_token":
                tokens.append(ev.payload["token"])

        # Verify event types in lifecycle
        event_types = [e.event_type for e in events]
        assert "phase_start" in event_types
        assert "phase_token" in event_types
        assert "audit_verdict" in event_types
        assert "phase_complete" in event_types

        # Full text assembled
        full_text = "".join(tokens)
        assert "oficina postal" in full_text
        assert "```python" not in full_text

        # Complete event payload checks
        complete_ev = [e for e in events if e.event_type == "phase_complete"][0]
        assert complete_ev.payload["completed_phase"] == "conceptual"
        assert "pseudocode" in complete_ev.payload["next_phases"]
        assert complete_ev.payload["code_allowed"] is False

    asyncio.run(_run())


def test_structured_pipeline_respects_phase_token_budgets():
    """Each phase operates under its own distinct token budget configured in the contract."""
    async def _run():
        contract = FASE0_CONTRACT
        conceptual_phase = contract.get_phase("conceptual")
        pseudocode_phase = contract.get_phase("pseudocode")
        python_phase = contract.get_phase("python_code")

        # Invariants: Budgets are independent and non-zero
        assert conceptual_phase.max_tokens == 1000
        assert pseudocode_phase.max_tokens == 600
        assert python_phase.max_tokens == 800

        captured_budgets = []

        class BudgetSpyBackend:
            def complete(self, prompt_bundle):
                captured_budgets.append(prompt_bundle.parameters.max_output_tokens)
                from study_engine.llm.backends import ProviderCompletion
                return ProviderCompletion(
                    text="Texto de prueba.",
                    latency_ms=10.0,
                    model="spy",
                )

        spy_backend = BudgetSpyBackend()
        pipeline = StructuredResponsePipeline(contract=contract, llm_backend=spy_backend)

        # Run conceptual
        async for _ in pipeline.generate_phased_response(user_query="Q", requested_phase="conceptual"):
            pass
        assert captured_budgets[-1] == 1000

        # Run pseudocode
        async for _ in pipeline.generate_phased_response(user_query="Q", requested_phase="pseudocode"):
            pass
        assert captured_budgets[-1] == 600

        # Run python_code
        async for _ in pipeline.generate_phased_response(user_query="Q", requested_phase="python_code"):
            pass
        assert captured_budgets[-1] == 800

    asyncio.run(_run())
