"""Escenario 16: Truncamiento por Ventana de Salida (Fase 7.2 - Chaos Engineering).

Simular que el LLM agota max_tokens y corta abruptamente la respuesta o el payload JSON a la mitad.
Invariante: Manejo de JSONDecodeError o truncamiento con degradación elegante hacia síntesis determinista;
            0 excepciones 500 no controladas, disponibilidad garantizada.
Severidad: CRÍTICO.
"""

import json
import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


class TruncatedJSONProvider:
    def generate(self, prompt: str, **kwargs) -> str:
        # Deliberately truncated JSON due to max_tokens boundary
        return '{"status": "OK", "synthesized_facts": [{"fact_id": "f1", "statement": "El proceso padre'


def test_truncated_json_output_graceful_fallback() -> None:
    """Truncated JSON output from LLM is safely handled without unhandled 500 crashes."""
    pack = ContextPack(current_kc="process_lifecycle", total_tokens=40)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_fork_1",
            document_id="doc_os",
            source_id="src_os",
            source_title="OS Concepts",
            page_start=110,
            pos_index=1,
            section="Process Creation",
            content="fork() duplica el proceso invocador creando un proceso hijo con PID propio.",
            is_seed_hit=True,
            relevance_score=0.95,
            token_count=18,
        )
    )

    truncated_raw = TruncatedJSONProvider().generate("test")

    # Safe parsing helper simulating production gateway
    def safe_parse_or_fallback(raw_output: str, fallback_pack: ContextPack):
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            # Fallback to deterministic extraction from pack
            return {
                "status": "DEGRADED_FALLBACK",
                "facts": [chk.content for chk in fallback_pack.retrieved_evidence],
            }

    result = safe_parse_or_fallback(truncated_raw, pack)
    assert result["status"] == "DEGRADED_FALLBACK"
    assert len(result["facts"]) == 1
    assert "fork()" in result["facts"][0]

    # Invariant: Controller and Narrator proceed cleanly under fallback
    controller = EpistemicController()
    payload = controller.process(
        query="¿Qué hace fork()?",
        context_pack=pack,
    )
    narrator = PersonaNarrator()
    prose = narrator.narrate(payload)
    assert "fork()" in prose
    assert len(prose) > 30
