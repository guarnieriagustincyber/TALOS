"""Test suite for Two-Stage Architecture: Controller + Narrator (Ola 6, Fase 6.1).

7 tests requeridos:
1. test_controller_extracts_facts       -> Controller extrae core_facts determinísticamente
2. test_controller_calculates_bkt       -> Controller calcula BKT y mastery_level correctamente
3. test_narrator_uses_only_payload      -> Narrator se basa estrictamente en core_facts (INV-W6-1)
4. test_narrator_respects_constraints   -> Narrator respeta suggest_exercise y forbidden_terms
5. test_narrator_tone_rioplatense       -> Narrator usa voseo natural y entra directo sin rodeos
6. test_s44_post_validation             -> S4.4 audita la prosa generada y valida citas
7. test_two_stage_latency               -> Latencia determinista del Controller es < 1.2 segundos (TTFT)
"""

import time
import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.controller_payload import (
    BKTStatus,
    Citation,
    ControllerPayload,
    ConversationStyle,
    Fact,
    PedagogicalConstraints,
)
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def _create_mock_context_pack() -> ContextPack:
    chk1 = ChunkWithProvenance(
        chunk_id="chk_ptr_1",
        document_id="doc_c",
        source_id="src_kr_c",
        source_title="Kernighan & Ritchie C",
        page_start=94,
        pos_index=1,
        section="Punteros y Memoria",
        content="Un puntero contiene la dirección de memoria de una variable.",
        is_seed_hit=True,
        relevance_score=0.95,
        token_count=12,
    )
    chk2 = ChunkWithProvenance(
        chunk_id="chk_ptr_2",
        document_id="doc_c",
        source_id="src_kr_c",
        source_title="Kernighan & Ritchie C",
        page_start=95,
        pos_index=2,
        section="Punteros y Memoria",
        content="El operador unario * es el operador de indirección o desreferenciación.",
        is_seed_hit=True,
        relevance_score=0.90,
        token_count=13,
    )
    pack = ContextPack(
        current_kc="punteros_basicos",
        previous_errors=["confundir puntero con valor"],
        total_tokens=25,
    )
    pack.add_evidence(chk1)
    pack.add_evidence(chk2)
    return pack


def test_controller_extracts_facts() -> None:
    """1. Controller accurately extracts atomic facts and citations from ContextPack."""
    controller = EpistemicController()
    pack = _create_mock_context_pack()

    payload = controller.process(
        query="¿Qué es un puntero en C?",
        context_pack=pack,
        style=ConversationStyle.NORMAL,
    )

    assert len(payload.core_facts) == 2
    assert "Un puntero contiene la dirección de memoria" in payload.core_facts[0].statement
    assert payload.core_facts[0].page == 94
    assert len(payload.citations) == 2
    assert payload.citations[0].citation_id == "E1"


def test_controller_calculates_bkt() -> None:
    """2. Controller calculates student cognitive level and BKT state deterministically."""
    storage = StudentStorage(":memory:")
    storage.save_bkt_state(BKTState(kc_id="punteros_basicos", p_L=0.75, attempts=4))

    controller = EpistemicController(student_storage=storage)
    pack = _create_mock_context_pack()

    payload = controller.process(
        query="¿Cómo desreferencio?",
        context_pack=pack,
        kc_id="punteros_basicos",
    )

    assert payload.bkt_status.kc_id == "punteros_basicos"
    assert payload.bkt_status.p_L == 0.75
    assert payload.bkt_status.mastery_level == "competent"
    assert payload.pedagogical_constraints.suggest_exercise is True


def test_narrator_uses_only_payload() -> None:
    """3. Invariant INV-W6-1: Narrator uses only facts provided in ControllerPayload."""
    narrator = PersonaNarrator()
    pack = _create_mock_context_pack()
    controller = EpistemicController()
    payload = controller.process(query="Explicame punteros", context_pack=pack)

    prose = narrator.narrate(payload)

    # Verifies facts are present in explanation
    assert "Un puntero contiene la dirección de memoria de una variable" in prose
    assert "[E1]" in prose


def test_narrator_respects_constraints() -> None:
    """4. Narrator honors pedagogical constraints and suggests exercise when instructed."""
    storage = StudentStorage(":memory:")
    storage.save_bkt_state(BKTState(kc_id="punteros_basicos", p_L=0.88, attempts=5))

    controller = EpistemicController(student_storage=storage)
    narrator = PersonaNarrator()
    pack = _create_mock_context_pack()

    payload = controller.process(
        query="Ya entiendo punteros",
        context_pack=pack,
        active_exercise_solution="int *p = &x;",
    )

    assert payload.pedagogical_constraints.suggest_exercise is True
    prose = narrator.narrate(payload)

    # Must suggest exercise
    assert "ejercicio práctico" in prose
    # Must NOT leak forbidden active exercise solution
    assert "int *p = &x;" not in prose


def test_narrator_tone_rioplatense() -> None:
    """5. Narrator uses natural rioplatense tone (voseo) without canned corporate greetings."""
    narrator = PersonaNarrator()
    pack = _create_mock_context_pack()
    controller = EpistemicController()
    payload = controller.process(query="Hola, ¿me explicás punteros?", context_pack=pack)

    prose = narrator.narrate(payload)

    # Voseo check
    lower = prose.lower()
    assert any(w in lower for w in ("fijate", "mirá", "tenés", "considerá"))
    # Zero canned greetings or fake corporate praise
    assert "¡hola!" not in lower
    assert "excelente pregunta" not in lower
    assert "buena observación" not in lower


def test_s44_post_validation() -> None:
    """6. Generated prose can be audited by S4.4 forensic adapter successfully."""
    from study_engine.audit.generation_adapter import audit_generation_payload
    from study_engine.audit.contracts import AuditVerdict

    class MockAuditor:
        def audit(self, inp):
            class Res:
                overall_verdict = AuditVerdict.APPROVED
            return Res()

    controller = EpistemicController()
    narrator = PersonaNarrator()
    pack = _create_mock_context_pack()

    payload = controller.process(query="Punteros", context_pack=pack)
    prose = narrator.narrate(payload)

    mock_auditor = MockAuditor()
    report = audit_generation_payload(
        mock_auditor,
        generated_text=prose,
        context_chunks=[{"citation_id": "E1", "content": "Un puntero contiene memoria."}],
        query="Punteros",
        notebook_id="fase0-soc",
    )
    assert report.overall_verdict == AuditVerdict.APPROVED


def test_two_stage_latency() -> None:
    """7. TTFT requirement: Controller execution latency is strictly < 1.2 seconds."""
    controller = EpistemicController()
    pack = _create_mock_context_pack()

    start = time.perf_counter()
    payload = controller.process(
        query="¿Qué es un puntero?",
        context_pack=pack,
        style=ConversationStyle.NORMAL,
    )
    elapsed_seconds = time.perf_counter() - start

    # Controller determinista must execute in under 1.2s (typically < 5ms)
    assert elapsed_seconds < 1.2
    assert elapsed_seconds < 0.10  # Even stricter: typically < 100ms
    assert len(payload.core_facts) > 0
