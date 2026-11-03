"""PED-F2 focal fix: consume an available grounded alternate on the first request.

The oracle is the existing approved packet's verbatim fields, not generated
judgments of student understanding. Mock audit outcomes below exercise delivery
gates only; they do not constitute real-provider E2E evidence.
"""

import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from study_engine.pedagogy.dialogue_contracts import DialogueState
from study_engine.web.routes.chat import ChatQueryRequest, _maybe_dialogue_turn_stream
from tests.unit.pedagogy.test_dialogue_socratic_turns import (
    CORE, MODEL, make_engine, make_intent, make_packet,
)
from tests.unit.pedagogy.test_dialogue_turn_grounding import (
    make_engine as grounded_engine, make_packet as grounded_packet,
)
from tests.unit.web.test_ep04a_struggle_atomicity import container_at, snapshot


def generate(packet=None, message="No entiendo, explicámelo de otra manera", turn=0):
    return asyncio.run(make_engine()._generate_response(
        intent=make_intent("REFORMULATION"), evidence=SimpleNamespace(chunks=[CORE]),
        concept_packet=packet or make_packet(), dialogue_state=DialogueState("synthetic-episode", turn_count=turn),
        student_message=message,
    ))


def test_first_reformulation_consumes_available_mental_model():
    output = generate()
    assert output.answer == MODEL and output.answer != CORE
    assert "campo=mental_model" in output.rationale
    assert "consultiva" in output.rationale and "UNKNOWN" in output.rationale


def test_grounded_guidance_keeps_existing_priority():
    guidance = "[E3] Primero identificá el tipo apuntado y después su tamaño."
    output = generate(replace(make_packet(), reasoning_guidance=guidance))
    assert output.answer == guidance
    assert "campo=reasoning_guidance" in output.rationale


def test_later_reformulation_keeps_existing_progressive_contrast():
    first, later = generate(), generate(turn=1)
    assert first.answer != later.answer
    assert later.answer == f"{CORE} {MODEL}"


def test_no_new_facts_when_no_cited_alternative_exists():
    output = generate(replace(make_packet(), mental_model="an unverified analogy"))
    assert output.answer == CORE
    assert "unverified analogy" not in output.answer
    assert "campo=" not in output.rationale  # No claim that an alternate was delivered.
    assert "sin alternativa citada" in output.rationale


def test_pending_answer_does_not_invent_a_misconception():
    engine = make_engine()
    intent = engine._propose_intent("Todavía no respondí la pregunta")
    assert intent.proposed_intent == "CLARIFICATION"
    output = asyncio.run(engine._generate_response(
        intent=make_intent(intent.proposed_intent), evidence=SimpleNamespace(chunks=[CORE]),
        concept_packet=make_packet(), dialogue_state=DialogueState("pending"),
        student_message="Todavía no respondí la pregunta",
    ))
    assert "posible.error" not in output.rationale


def test_two_kcs_do_not_share_the_selected_content():
    other = replace(make_packet(), kc_id="other-kc", mental_model="[E2] Otra representación sintética.")
    assert generate(other).answer == other.mental_model
    assert generate().answer == MODEL
    assert "Otra representación" not in generate().answer


def test_selection_survives_reconstitution_of_consultive_state():
    from dataclasses import asdict
    original = DialogueState("synthetic-episode")
    restored = DialogueState(**asdict(original))

    def select(state):
        return asyncio.run(make_engine()._generate_response(
            intent=make_intent("REFORMULATION"), evidence=SimpleNamespace(chunks=[CORE]),
            concept_packet=make_packet(), dialogue_state=state,
            student_message="No entiendo, explicámelo de otra manera",
        ))

    before, after = select(original), select(restored)
    assert (before.answer, before.socratic_question, before.rationale) == (
        after.answer, after.socratic_question, after.rationale,
    )
    assert original.perceived_comprehension == restored.perceived_comprehension == {}


@pytest.mark.parametrize("verdict", ["APPROVED", "REJECTED_UNSUPPORTED", "TIMEOUT"])
def test_delegated_intervention_consumed_audited_and_delivered_without_academic_updates(tmp_path, monkeypatch, verdict):
    import json
    from study_engine.web.routes import chat, dialogue

    c = container_at(tmp_path / "synthetic.db")
    episode = c.pedagogical_orchestrator.get_episode("episode-synthetic-1")
    original_snapshot = c.study_session_orchestrator.get_snapshot(episode.session_id)
    c.study_session_orchestrator.get_snapshot = lambda sid: SimpleNamespace(
        **vars(original_snapshot), episode_phase="DIALOGUE", current_kc_id=episode.kc_id,
    )
    c.pedagogical_orchestrator.save_episode = lambda ep: None
    packet = replace(grounded_packet(), kc_id=episode.kc_id, notebook_id=episode.notebook_id)
    monkeypatch.setattr(chat, "_CONV_TURN_BUFFER", {})
    monkeypatch.setattr(dialogue, "_EPISODE_DIALOGUE_STATES", {})
    monkeypatch.setattr(dialogue, "_load_or_reuse_concept_response", lambda orch, eid: SimpleNamespace(packet=packet))
    audited = []

    class AuditDouble:
        def audit_claims(self, claims, chunks):
            audited.extend(claims)
            if verdict == "TIMEOUT":
                raise TimeoutError("synthetic provider timeout")
            return SimpleNamespace(verdict=verdict)

    c.dialogue_engine = grounded_engine()
    c.dialogue_engine.forensic_auditor = AuditDouble()
    req = ChatQueryRequest(
        prompt="No entiendo, explicámelo de otra manera", session_id=episode.session_id,
        notebook_id=episode.notebook_id,
    )
    before = snapshot(c)
    stream = _maybe_dialogue_turn_stream(c, req.session_id, req.prompt, "conceptual", request=req)
    assert stream is not None

    async def drain():
        return [json.loads(raw.removeprefix("data: ")) async for raw in stream]

    events = asyncio.run(drain())
    assert audited == [packet.mental_model]
    delivered = "".join(e["payload"]["token"] for e in events if e["event_type"] == "phase_token")
    if verdict == "APPROVED":
        assert delivered.startswith(packet.mental_model)
        assert packet.core_concept not in delivered.split("\n\n")[0]
        turn = dialogue._EPISODE_DIALOGUE_STATES[episode.episode_id].turns[-1]
        assert turn.comprehension_signal == "UNKNOWN"
        assert "campo=mental_model" in turn.llm_rationale
    else:
        assert not delivered
        assert any(e["event_type"] == "abstention" for e in events)
    assert snapshot(c) == before
    c.student_storage.close()


def test_open_exercise_help_does_not_bypass_solution_protection():
    packet = grounded_packet()
    engine = grounded_engine()
    engine.exercise_selector = SimpleNamespace(
        get_presentable_exercise_for_kc=lambda kc: SimpleNamespace(expected_answer=packet.mental_model),
    )
    from study_engine.pedagogy.episode_contracts import Episode
    episode = Episode(episode_id="protected", notebook_id="fase0-soc", kc_id="aritmetica_punteros", objective="synthetic")
    response = asyncio.run(engine.process_turn(
        episode, packet, DialogueState(episode.episode_id), "No entiendo, explicámelo de otra manera",
    ))
    assert response.status == "ABSTAINED"
    assert "solución" in response.abstention_reason
    assert response.answer is None
