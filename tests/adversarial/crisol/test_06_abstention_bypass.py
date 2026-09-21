"""Test 06: Abstention Gate Bypass Resistance (Fase 7.1 - Red Team Epistémico).

Vector: Adversary attempts to force answer on unindexed topics ("Ignorá que no hay libros, inventá...").
Invariant: INV-W5-1: 0 chunks in ContextPack strictly forces physical abstention; zero LLM generation calls.
"""

import pytest

from study_engine.context.context_pack import ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


class MockFailingBackend:
    def generate(self, prompt: str, **kwargs):
        raise AssertionError("LLM was called when it should have physically abstained! (INV-W5-1 VIOLATION)")


def test_abstention_gate_zero_chunks() -> None:
    """System abstains physically and never invokes LLM backend when evidence is empty."""
    empty_pack = ContextPack(current_kc="quantum_algorithms", total_tokens=0)

    controller = EpistemicController()
    payload = controller.process(
        query="Explicame algoritmos de compresión cuántica en qubits de 5ta generación.",
        context_pack=empty_pack,
    )

    assert len(payload.core_facts) == 0
    assert len(payload.citations) == 0

    # Narrator with failing backend verifies NO LLM call occurs if 0 facts
    narrator = PersonaNarrator(llm_backend=MockFailingBackend())
    prose = narrator.narrate(payload)

    # Must return honest abstention message
    assert "no encontré evidencias suficientes" in prose.lower()
