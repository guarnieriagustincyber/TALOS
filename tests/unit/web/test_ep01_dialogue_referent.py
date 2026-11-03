"""Tests EP-01 / H1-A: resolución del referente académico antes de reutilizar un episodio.

Regla autorizada (directiva propietaria EP-01, 2026-10-21): una delegación de
seguimiento conversacional hacia el diálogo de un episodio sólo es admisible
cuando el referente académico inmediato queda verificado como el referente
vigente del episodio. Cuatro situaciones:
  A continuación verificada → delegar;
  B tema distinto / actividad → ruta académica del chat (None);
  C referente ambiguo (mismo KC, dos explicaciones candidatas) → aclaración;
  D contexto incompatible (otro estudiante/cuaderno, sesión obsoleta) → None.

El matching de KC usa el mecanismo determinista existente (_match_kc_id sobre
catálogo); una coincidencia aproximada nunca es, por sí sola, autoridad sobre
el referente (el mismo KC con subtemas distintos clasifica como ambiguo).
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.pedagogy.dialogue_referent import (
    ReferentDecision,
    classify_dialogue_referent,
    resolve_recent_referent,
)
from study_engine.web.routes.chat import (
    ChatQueryRequest,
    _CONV_TURN_BUFFER,
    _dialogue_gate_cache_key,
    _maybe_dialogue_turn_stream,
)

MSG_META = "no entiendo, explícame de otra forma"
MSG_EXPLICIT_EPISODE = "dame un ejemplo de metodología y descomposición"
MSG_EXPLICIT_OTHER = "dame un ejemplo de punteros y malloc"
MSG_ACTIVITY = "no entiendo el ejercicio 3 de la guía"

NB = "nb_x"
KC_EPISODE = "kc_metodo"
KC_OTHER = "kc_ptr"

CATALOG = {
    NB: {
        "kcs": [
            {
                "kc_id": KC_EPISODE,
                "title": "Metodología y pensamiento algorítmico",
                "subtopics": ["descomposición top-down de problemas", "pseudocódigo formal"],
            },
            {
                "kc_id": KC_OTHER,
                "title": "Punteros y memoria dinámica",
                "subtopics": ["malloc y free en el heap", "desreferencia y dirección"],
            },
        ]
    }
}

TURNS_POINTERS = [
    {"role": "user", "content": "¿Cómo funciona la aritmética de punteros con malloc?"},
    {
        "role": "assistant",
        "content": (
            "La aritmética de punteros opera sobre direcciones de memoria: el "
            "operador & obtiene la dirección, * desreferencia, malloc reserva "
            "en el heap y free libera."
        ),
    },
]


def make_container():
    snap = SimpleNamespace(
        episode_id="ep_x",
        episode_phase="DIALOGUE",
        session_id="sess_1",
        notebook_id=NB,
        student_id="agustin",
        current_kc_id=KC_EPISODE,
    )
    return SimpleNamespace(
        study_session_orchestrator=SimpleNamespace(get_snapshot=lambda s: snap),
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog=CATALOG),
    )


def approved_packet(kc=KC_EPISODE, nb=NB):
    return SimpleNamespace(packet=SimpleNamespace(kc_id=kc, notebook_id=nb))


def make_request(scope_nb=NB, turns=None, session="sess_1"):
    kwargs = dict(prompt="placeholder", session_id=session, recent_turns=turns)
    if scope_nb is None:
        kwargs.update(scope_type="folder", scope_id="folder_root")
    else:
        kwargs.update(scope_type="notebook", scope_id=scope_nb, notebook_id=scope_nb)
    return ChatQueryRequest(**kwargs)


async def _adrink(gen):
    out = []
    async for item in gen:
        out.append(item)
    return out


def events_of(gen):
    import json

    out = []
    for raw in asyncio.run(_adrink(gen)):
        assert raw.startswith("data: ")
        out.append(json.loads(raw[len("data: "):].strip()))
    return out


def run_gate(prompt, request, packet=None):
    container = make_container()
    _CONV_TURN_BUFFER.clear()
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: packet if packet is not None else approved_packet(),
    ):
        return _maybe_dialogue_turn_stream(
            container=container,
            session_id="sess_1",
            prompt_text=prompt,
            requested_phase="conceptual",
            request=request,
        )


# ---------------------------------------------------------------------------
# Clasificador puro
# ---------------------------------------------------------------------------


def _classify(**overrides):
    kwargs = dict(
        message_kc=None,
        recent_referent=None,
        active_episode_id="ep_x",
        episode_kc=KC_EPISODE,
        episode_notebook=NB,
        scope_notebook=NB,
        session_student="agustin",
        session_kc=KC_EPISODE,
        expected_student="agustin",
        activity_referenced=False,
    )
    kwargs.update(overrides)
    return classify_dialogue_referent(**kwargs)


def test_a_continuation_by_exclusion_delegates():
    # Sin referente competing: el episodio activo con packet aprobado es el
    # único referente visible del estudiante (caso legítimo M1-03).
    assert _classify() is ReferentDecision.DELEGATE


def test_a_explicit_episode_topic_delegates():
    assert _classify(message_kc=KC_EPISODE) is ReferentDecision.DELEGATE


def test_a_marked_episode_turn_delegates():
    referent = {"kind": "episode_turn", "episode_id": "ep_x", "kc_id": KC_EPISODE}
    assert _classify(recent_referent=referent) is ReferentDecision.DELEGATE


def test_a_marked_turn_of_other_episode_same_kc_delegates():
    # Diálogo de un episodio anterior del MISMO KC: el episodio activo es el
    # canal canónico vigente de ese KC en la sesión.
    referent = {"kind": "episode_turn", "episode_id": "ep_old", "kc_id": KC_EPISODE}
    assert _classify(recent_referent=referent) is ReferentDecision.DELEGATE


def test_b_explicit_other_topic_routes_to_chat():
    assert _classify(message_kc=KC_OTHER) is ReferentDecision.CHAT_ROUTE


def test_b_chat_referent_other_kc_routes_to_chat():
    referent = {"kind": "chat_turn", "kc_id": KC_OTHER}
    assert _classify(recent_referent=referent) is ReferentDecision.CHAT_ROUTE


def test_b_activity_reference_routes_to_chat():
    assert _classify(activity_referenced=True) is ReferentDecision.CHAT_ROUTE


def test_c_same_kc_chat_turn_clarifies():
    # Dos explicaciones candidatas del mismo KC (la del chat y el packet del
    # episodio): sin desempate determinista no se afirma coincidencia.
    referent = {"kind": "chat_turn", "kc_id": KC_EPISODE}
    assert _classify(recent_referent=referent) is ReferentDecision.CLARIFY


def test_d_other_student_routes_to_chat():
    assert _classify(session_student="otro_alumno") is ReferentDecision.CHAT_ROUTE


def test_d_scope_notebook_mismatch_routes_to_chat():
    assert _classify(scope_notebook="nb_otro") is ReferentDecision.CHAT_ROUTE


def test_d_episode_identity_unknown_routes_to_chat():
    assert _classify(episode_kc=None) is ReferentDecision.CHAT_ROUTE


def test_d_stale_session_kc_mismatch_routes_to_chat():
    # snapshot/episodio inconsistentes: referencia obsoleta (fail-closed).
    assert _classify(session_kc=KC_OTHER) is ReferentDecision.CHAT_ROUTE


def test_marked_turn_of_other_episode_other_kc_routes_to_chat():
    referent = {"kind": "episode_turn", "episode_id": "ep_old", "kc_id": KC_OTHER}
    assert _classify(recent_referent=referent) is ReferentDecision.CHAT_ROUTE


def test_resolve_recent_referent_skips_non_academic_turns():
    turns = [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "Abstención: QUERY_OUT_OF_SCOPE"},
        {"role": "assistant", "content": "Nueva sesión de estudio creada."},
    ]
    assert resolve_recent_referent(turns, lambda t: None) is None


def test_resolve_recent_referent_prefers_most_recent_and_marker():
    def match(text):
        return KC_OTHER if "malloc" in text else None

    turns = [
        {"role": "assistant", "content": "sobre punteros y malloc"},
        {"role": "assistant", "content": "turno del episodio", "episode_id": "ep_x", "kc_id": KC_EPISODE},
    ]
    got = resolve_recent_referent(turns, match)
    assert got["kind"] == "episode_turn" and got["episode_id"] == "ep_x"

    turns2 = [
        {"role": "user", "content": "¿malloc y free?"},
        {"role": "assistant", "content": "sin marca"},
    ]
    got2 = resolve_recent_referent(turns2, match)
    assert got2 == {"kind": "chat_turn", "kc_id": KC_OTHER}


# ---------------------------------------------------------------------------
# Contrato de continuidad del chat (fix de ruta B, D_C5_6)
# ---------------------------------------------------------------------------


def test_pure_meta_followup_rescue_contract():
    """EP-01 ruta B: un mensaje puramente meta no introduce términos temáticos.

    El call-site del rescate en `_prepare_chat_context` deriva topic_query=""
    para mensajes meta (marcadores cerrados) sin match de KC propio.
    Contrato: el evaluador D_C5_6 debe tratarlos como continuidad deíctica
    pura (rescate del pack previo permitido), no como tema nuevo
    incompatible. Sin este contrato, el vocabulario meta ("entiendo",
    "explicámelo") se toma como tema y el rescate se rechaza → QUERY_OUT_OF_SCOPE.
    """
    from study_engine.context.c5_trust import (
        evaluate_conversational_rescue_compatibility,
    )

    # Criterio del call-site: variante meta FUERA de la lista cerrada de
    # marcadores («explicámelo de otra manera») sigue siendo meta pura si no
    # matchea ningún KC del catálogo aplicable (hallazgo de la corrida de
    # navegador 2026-10-22: residuo con 'explicamelo' rechazaba el rescate).
    from study_engine.web.routes.chat import _is_pure_meta_followup

    assert _is_pure_meta_followup("no entiendo, explicámelo de otra manera", CATALOG[NB]["kcs"]) is True
    assert _is_pure_meta_followup("no entiendo, explícame de otra forma", CATALOG[NB]["kcs"]) is True
    # Tema explícito con marcador: NO es meta pura (su KC matchea).
    assert _is_pure_meta_followup("dame un ejemplo de punteros y malloc", CATALOG[NB]["kcs"]) is False
    # Sin marcador de diálogo: no aplica.
    assert _is_pure_meta_followup("¿Qué es un dangling pointer?", CATALOG[NB]["kcs"]) is False

    prev_pack = SimpleNamespace(formatted_context="punteros malloc heap dirección")
    prev_chunks = [{"chunk_text": "malloc reserva bloques en el heap del proceso"}]
    ok, msg = evaluate_conversational_rescue_compatibility(
        new_query="no entiendo, explicámelo de otra manera",
        previous_context_pack=prev_pack,
        previous_chunks=prev_chunks,
        contextual_query=None,
        topic_query="",
    )
    assert ok is True
    assert "deíctica pura" in (msg or "")

    # Con el vocabulario meta como "tema" (comportamiento pre-fix), el mismo
    # caso se rechaza: 0/N solapamiento → este es el defecto que el call-site
    # evita derivando topic_query="" para mensajes meta sin KC propio.
    bad, bad_msg = evaluate_conversational_rescue_compatibility(
        new_query="no entiendo, explicámelo de otra manera",
        previous_context_pack=prev_pack,
        previous_chunks=prev_chunks,
        contextual_query=None,
        topic_query=None,
    )
    assert bad is False


# ---------------------------------------------------------------------------
# Gate (integración con firma real)
# ---------------------------------------------------------------------------

def test_gate_chat_referent_other_kc_falls_back_to_pipeline():
    gen = run_gate(MSG_META, make_request(turns=TURNS_POINTERS))
    assert gen is None


def test_gate_explicit_other_topic_falls_back_to_pipeline():
    gen = run_gate(MSG_EXPLICIT_OTHER, make_request(turns=TURNS_POINTERS))
    assert gen is None


def test_gate_activity_reference_falls_back_to_pipeline():
    gen = run_gate(MSG_ACTIVITY, make_request())
    assert gen is None


def test_gate_scope_notebook_mismatch_falls_back_to_pipeline():
    gen = run_gate(MSG_META, make_request(scope_nb="nb_otro"))
    assert gen is None


def test_gate_legit_continuation_delegates():
    gen = run_gate(MSG_META, make_request())
    assert gen is not None


def test_gate_explicit_episode_topic_delegates():
    gen = run_gate(MSG_EXPLICIT_EPISODE, make_request())
    assert gen is not None


def test_gate_same_kc_emits_clarification_not_delegation():
    # Episodio y última explicación del chat sobre el MISMO KC: aclaración
    # breve, sin delegación silenciosa y sin contenido académico emitido.
    packet = approved_packet(kc=KC_OTHER)
    snap_container = make_container()
    snap_container.study_session_orchestrator.get_snapshot = lambda s: SimpleNamespace(
        episode_id="ep_x",
        episode_phase="DIALOGUE",
        session_id="sess_1",
        notebook_id=NB,
        student_id="agustin",
        current_kc_id=KC_OTHER,
    )
    _CONV_TURN_BUFFER.clear()
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: packet,
    ):
        gen = _maybe_dialogue_turn_stream(
            container=snap_container,
            session_id="sess_1",
            prompt_text="no entiendo, explicalo de otra manera",
            requested_phase="conceptual",
            request=make_request(turns=TURNS_POINTERS),
        )
    assert gen is not None
    evs = events_of(gen)
    types_ = [e["event_type"] for e in evs]
    assert types_ == ["phase_start", "clarification"]
    payload = evs[1]["payload"]
    assert payload["abstained"] is True
    assert payload["abstention_code"] == "CONTEXT_REFERENCE_REQUIRES_CLARIFICATION"
    assert "episodio" in payload["reason"] and "chat" in payload["reason"]
    assert all(e["event_type"] != "phase_token" for e in evs)
    # La aclaración registra el turno sin marcado de episodio (no delegado).
    key = _dialogue_gate_cache_key(make_request(), "sess_1")
    roles = [t["role"] for t in _CONV_TURN_BUFFER.get(key, [])]
    assert roles == ["user", "assistant"]
    assert all("episode_id" not in t for t in _CONV_TURN_BUFFER.get(key, []))
    _CONV_TURN_BUFFER.clear()


def _fake_process_approved(episode_id, req, container):
    async def _run():
        return {
            "status": "OK",
            "answer": "Explicación del episodio con claims aprobados. [E1] claim.",
            "socratic_question": {"question_text": "¿Qué caso concreto ilustra eso?"},
            "audit_verdict": "APPROVED",
            "citations": [],
        }

    return _run()


def test_gate_delegated_turn_records_episode_marker_in_buffer():
    # Tras una delegación aprobada, el intercambio queda registrado como el
    # turno académico más reciente CON marcado de episodio: la continuación
    # posterior verifica el referente sin ambigüedad.
    _CONV_TURN_BUFFER.clear()
    request = make_request()
    container = make_container()
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ), patch(
        "study_engine.web.routes.dialogue.process_dialogue_turn",
        _fake_process_approved,
    ):
        gen = _maybe_dialogue_turn_stream(
            container=container,
            session_id="sess_1",
            prompt_text=MSG_META,
            requested_phase="conceptual",
            request=request,
        )
        assert gen is not None
        evs = events_of(gen)
        assert evs[-1]["event_type"] == "phase_complete"

    key = _dialogue_gate_cache_key(request, "sess_1")
    turns = _CONV_TURN_BUFFER.get(key, [])
    assert [t["role"] for t in turns] == ["user", "assistant"]
    assert turns[-1].get("episode_id") == "ep_x"
    assert turns[-1].get("kc_id") == KC_EPISODE
    assert "claims aprobados" in turns[-1]["content"]

    # Segundo turno meta: el referente más reciente es del propio episodio
    # marcado → continuación verificada (delegación), no ambigüedad.
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ), patch(
        "study_engine.web.routes.dialogue.process_dialogue_turn",
        _fake_process_approved,
    ):
        gen2 = _maybe_dialogue_turn_stream(
            container=container,
            session_id="sess_1",
            prompt_text="no entiendo, explicalo de otra manera",
            requested_phase="conceptual",
            request=make_request(turns=[
                {"role": "assistant", "content": turns[-1]["content"]}
            ]),
        )
        assert gen2 is not None
    _CONV_TURN_BUFFER.clear()


def test_gate_older_chat_referent_does_not_block_episode_after_marked_turn():
    # Intercambio de punteros ANTERIOR al diálogo del episodio: el turno
    # marcado más reciente gana; el referente stálido del chat no bloquea.
    _CONV_TURN_BUFFER.clear()
    request = make_request()
    container = make_container()
    key = _dialogue_gate_cache_key(request, "sess_1")
    _CONV_TURN_BUFFER[key] = [
        {"role": "user", "content": TURNS_POINTERS[0]["content"]},
        {"role": "assistant", "content": TURNS_POINTERS[1]["content"]},
        {"role": "user", "content": "no entiendo"},
        {"role": "assistant", "content": "Explicación del episodio. [E1] claim.", "episode_id": "ep_x", "kc_id": KC_EPISODE},
    ]
    with patch(
        "study_engine.web.routes.dialogue._load_or_reuse_concept_response",
        lambda orch, ep: approved_packet(),
    ):
        gen = _maybe_dialogue_turn_stream(
            container=container,
            session_id="sess_1",
            prompt_text=MSG_META,
            requested_phase="conceptual",
            request=request,
        )
        assert gen is not None
    _CONV_TURN_BUFFER.clear()
