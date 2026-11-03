"""Tests M1-03 §3: diálogo socrático auténtico por turnos.

Requisitos de la milestone:
- Preguntas socráticas DISTINTAS por turno, derivadas determinísticamente del
  ConceptPacket aprobado (rotación de campos + pasaje verbatim), sin
  plantillas genéricas ajenas al contenido.
- El texto del turno NO repite el mismo enunciado de un turno a otro.
- Detección conservadora de posible error conceptual: presenta los pitfalls
  verbatim (solo tag-leading) + el claim central aprobado, invita a contrastar;
  jamás acredita ni evalúa al estudiante.
- Pitfalls sin formato tag-leading no entran al body (fail-closed S4.4).
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.audit.contracts import AuditVerdict
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.dialogue_engine import DialogueEngine
from study_engine.pedagogy.dialogue_policy import ValidatedIntent

CORE = "[E1] Un puntero es una variable que contiene la dirección de memoria de otro objeto."
MODEL = "[E2] La aritmética de punteros escala el desplazamiento por el tamaño del tipo apuntado."
GUIDE = "Paso 1: identificar la base. Paso 2: multiplicar por sizeof."
PITFALL_OK = "[E3] Un error frecuente es confundir el valor del puntero con el valor apuntado."
PITFALL_STALE = "Un error frecuente (sin cita en el fragmento)."


def make_packet(pitfalls=()) -> ConceptPacket:
    return ConceptPacket(
        kc_id="aritmetica_punteros",
        notebook_id="fase0-soc",
        objective="Comprender aritmética de punteros",
        evidence_by_role={"PRIMARY": []},
        core_concept=CORE,
        mental_model=MODEL,
        reasoning_guidance=GUIDE,
        formalization=None,
        implementation_guidance=None,
        pitfalls=pitfalls,
        citations=(),
        s44_report=None,
        audit_verdict=AuditVerdict.APPROVED,
        assembly_hash="0" * 64,
    )


def make_intent(proposed: str = "CLARIFICATION") -> ValidatedIntent:
    return ValidatedIntent(
        action="PROCEED_DIALOGUE",
        query_text="?",
        proposed_intent=proposed,
    )


def make_state(turn_count: int) -> SimpleNamespace:
    return SimpleNamespace(turn_count=turn_count)


def make_engine() -> DialogueEngine:
    return DialogueEngine(chunk_content_loader=lambda chunk_id: None)


def gen(state, msg="¿cómo funciona?", packet=None):
    return asyncio.run(
        make_engine()._generate_response(
            intent=make_intent(),
            evidence=SimpleNamespace(chunks=[CORE], citations=[]),
            concept_packet=packet or make_packet(),
            dialogue_state=state,
            student_message=msg,
        )
    )


def test_socratic_question_rotates_package_fields_by_turn():
    """Turnos sucesivos citan campos distintos del packet → textos distintos."""
    q0 = gen(make_state(0)).socratic_question
    q1 = gen(make_state(1)).socratic_question
    q2 = gen(make_state(2)).socratic_question
    assert all(q0 and q1 and q2)
    assert q0 != q1 and q1 != q2 and q0 != q2
    # cada pregunta cita material verbatim del packet auditado
    for q, frag in ((q0, "Un puntero es"), (q1, "escala el desplazamiento"), (q2, "Paso 1")):
        assert frag in q, (q, frag)


def test_misconception_marker_returns_documented_pitfalls_and_invites_contrast():
    turn = gen(
        make_state(0),
        msg="Igual eso está mal: un puntero no guarda la dirección del otro.",
        packet=make_packet(pitfalls=(PITFALL_OK,)),
    )
    assert turn.answer.startswith("[E3]")
    assert "confundir el valor del puntero" in turn.answer
    assert "Un puntero es una variable" in turn.answer  # claim central verbatim
    assert "difiere de esa formulación" in turn.socratic_question


def test_misconception_with_untagged_pitfalls_falls_back_to_core_only():
    turn = gen(
        make_state(0),
        msg="El puntero no guarda la dirección del objeto.",
        packet=make_packet(pitfalls=(PITFALL_STALE,)),
    )
    # pitfall sin tag-leading no entra (fail-closed frente al formato S4.4)
    assert PITFALL_STALE not in turn.answer
    assert turn.answer.startswith("[E1]")


def test_turn_answer_never_repeats_between_successive_reformulations():
    a0 = asyncio.run(
        make_engine()._generate_response(
            intent=make_intent("REFORMULATION"),
            evidence=SimpleNamespace(chunks=[CORE], citations=[]),
            concept_packet=make_packet(),
            dialogue_state=make_state(0),
            student_message="no entiendo",
        )
    ).answer
    a1 = asyncio.run(
        make_engine()._generate_response(
            intent=make_intent("REFORMULATION"),
            evidence=SimpleNamespace(chunks=[CORE], citations=[]),
            concept_packet=make_packet(),
            dialogue_state=make_state(1),
            student_message="no entiendo",
        )
    ).answer
    assert a0 != a1  # pista progresiva: cada reformulación añade otro campo
    assert "escala el desplazamiento" in a1  # turno 2 aporta el modelo mental
