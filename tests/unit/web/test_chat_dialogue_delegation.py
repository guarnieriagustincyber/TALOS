"""Tests M1-03 §5: delegación de meta-discurso al diálogo del episodio activo.

Contrato corregido (hallazgo del escenario live de 8 pasos en navegador):
- El chat real recibe los turnos del diálogo socrático por /api/chat/query con
  el session_id de la sesión de estudio; sin delegación, el gate C5 abstenía
  con QUERY_OUT_OF_SCOPE mensajes como "no entiendo, explícame de otra forma",
  rompiendo la continuidad pedagógica del episodio.
- Delegación acotada y fail-closed: SOLO mensajes meta (marcadores
  deterministas) + sesión con episodio activo en fase de diálogo + ConceptPacket
  ya APROBADO por S4.4 (no se genera contenido nuevo ni se re-audita).
- Un fallo técnico una vez delegado se reporta como error técnico (SSE error),
  nunca como abstinencia académica.
"""

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.web.routes.chat import _maybe_dialogue_turn_stream

MSG_META = "no entiendo, explícame de otra forma"
MSG_CONTENT = "El puntero guarda el valor del objeto, no la dirección de memoria."


def make_container(phase: str = "DIALOGUE", with_ep: bool = True) -> SimpleNamespace:
    # EP-01/H1-A: el gate verifica identidad de sesión (estudiante/cuaderno/KC)
    # contra el packet del episodio antes de delegar; el fixture expone esos
    # campos de la misma forma que el snapshot real.
    snap = SimpleNamespace(
        episode_id="ep_x" if with_ep else None,
        episode_phase=phase,
        session_id="sess_1",
        notebook_id="nb_x",
        student_id="agustin",
        current_kc_id="kc_x",
    )
    return SimpleNamespace(
        study_session_orchestrator=None if not with_ep else SimpleNamespace(get_snapshot=lambda s: snap),
        pedagogical_orchestrator=SimpleNamespace(),
    )


def approved_packet() -> SimpleNamespace:
    # Packet aprobado con identidad verificable (kc/cuaderno del episodio).
    return SimpleNamespace(packet=SimpleNamespace(kc_id="kc_x", notebook_id="nb_x"))


def _drink(gen):
    events = []
    for ev in asyncio.run(_adrain(gen)) if False else asyncio.run(_drink_async(gen)):
        events.append(ev)
    return events


async def _drink_async(gen):
    out = []
    async for item in gen:
        out.append(item)
    return out


def _events(gen):
    return _drink(gen)


def test_content_message_never_delegates():
    """Mensaje con afirmación de contenido → pipeline completo (sin delegar)."""
    c = make_container()
    assert (
        _maybe_dialogue_turn_stream(
            container=c, session_id="sess_1", prompt_text=MSG_CONTENT, requested_phase="conceptual"
        )
        is None
    )


def test_meta_message_without_session_falls_back():
    c = SimpleNamespace(study_session_orchestrator=None)
    assert (
        _maybe_dialogue_turn_stream(
            container=c, session_id=None, prompt_text=MSG_META, requested_phase="conceptual"
        )
        is None
    )


def test_meta_message_without_approved_packet_falls_back():
    c = make_container(phase="DIALOGUE")
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: None,
    ):
        out = _maybe_dialogue_turn_stream(
            container=c, session_id="sess_1", prompt_text=MSG_META, requested_phase="conceptual"
        )
    assert out is None


def test_delegated_turn_emits_approved_composition():
    c = make_container(phase="DIALOGUE")
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ), patch(
        "study_engine.web.routes.dialogue.process_dialogue_turn",
        _fake_process_approved,
    ):
        gen = _maybe_dialogue_turn_stream(
            container=c, session_id="sess_1", prompt_text=MSG_META, requested_phase="conceptual"
        )
        assert gen is not None
        evs = [_parse(e) for e in _events(gen)]
    types_ = [e["event_type"] for e in evs]
    assert types_[0] == "phase_start"
    assert types_[-1] == "phase_complete"
    assert "audit_verdict" in types_
    tokens = "".join(e["payload"]["token"] for e in evs if e["event_type"] == "phase_token")
    assert "[E1] claim aprobado." in tokens
    assert "¿Por qué el nodo no crece?" in tokens


def test_delegated_abstained_turn_emits_abstention_no_tokens():
    c = make_container(phase="DIALOGUE")
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ), patch(
        "study_engine.web.routes.dialogue.process_dialogue_turn",
        _fake_process_abstained,
    ):
        gen = _maybe_dialogue_turn_stream(
            container=c, session_id="sess_1", prompt_text=MSG_META, requested_phase="conceptual"
        )
        evs = [_parse(e) for e in _events(gen)]
    types_ = [e["event_type"] for e in evs]
    assert "phase_token" not in types_
    abst = [e for e in evs if e["event_type"] == "abstention"]
    assert len(abst) == 1 and abst[0]["payload"]["abstained"] is True


def test_delegated_rejected_verdict_is_fail_closed_no_tokens():
    """Veredicto no aprobatorio → abstinencia (SSE), JAMÁS tokens al estudiante."""
    c = make_container(phase="DIALOGUE")
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ), patch(
        "study_engine.web.routes.dialogue.process_dialogue_turn",
        _fake_process_rejected,
    ):
        gen = _maybe_dialogue_turn_stream(
            container=c, session_id="sess_1", prompt_text=MSG_META, requested_phase="conceptual"
        )
        evs = [_parse(e) for e in _events(gen)]
    types_ = [e["event_type"] for e in evs]
    assert "phase_token" not in types_
    abst = [e for e in evs if e["event_type"] == "abstention"]
    assert len(abst) == 1
    assert "REJECTED" in abst[0]["payload"]["abstention_code"]


def test_delegated_technical_failure_reports_error_not_abstention():
    c = make_container(phase="DIALOGUE")
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ), patch(
        "study_engine.web.routes.dialogue.process_dialogue_turn",
        _fake_process_boom,
    ):
        gen = _maybe_dialogue_turn_stream(
            container=c, session_id="sess_1", prompt_text=MSG_META, requested_phase="conceptual"
        )
        evs = [_parse(e) for e in _events(gen)]
    types_ = [e["event_type"] for e in evs]
    assert "abstention" not in types_ and "phase_token" not in types_
    assert types_ == ["error"]
    assert "técnico" in evs[0]["payload"]["message"]


# -- fakes -------------------------------------------------------------------

async def _fake_process_approved(episode_id, req, container):
    return {
        "status": "RESPONDED",
        "answer": "[E1] claim aprobado.",
        "socratic_question": {"question_text": "¿Por qué el nodo no crece?"},
        "audit_verdict": "AuditVerdict.APPROVED",
        "abstention_reason": None,
    }


async def _fake_process_abstained(episode_id, req, container):
    return {
        "status": "ABSTAINED",
        "answer": "",
        "socratic_question": None,
        "audit_verdict": None,
        "abstention_reason": "No hay material aprobado para ese turno.",
    }


async def _fake_process_rejected(episode_id, req, container):
    return {
        "status": "RESPONDED",
        "answer": "[E1] texto rechazado por S4.4.",
        "socratic_question": None,
        "audit_verdict": "AuditVerdict.REJECTED_UNSUPPORTED",
        "abstention_reason": None,
    }


async def _fake_process_boom(episode_id, req, container):
    raise RuntimeError("boom técnico")


def _parse(raw: str) -> dict:
    assert raw.startswith("data: ") and raw.endswith("\n\n")
    return json.loads(raw[len("data: ") : -2])
