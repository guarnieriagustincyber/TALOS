"""A4: actual builder/orchestrator/API, synthetic evidence, instrumented audit.

APPROVED below exercises propagation only, never real S4.4/NLI correctness.
No startup, corpus, providers or persistent student state are used.
"""

import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.encoders import jsonable_encoder

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.pedagogy.concept_builder import ConceptPacketBuilder
from study_engine.pedagogy.concept_packet import ConceptResponse
from study_engine.pedagogy.episode_contracts import Episode
from study_engine.pedagogy.evidence_assembler import AssembledEvidenceBundle
from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
from study_engine.web.routes import dialogue
from study_engine.web.routes.pedagogy import get_concept_explanation
from tests.unit.pedagogy.test_concept_evidence_binding import _citation
from tests.unit.pedagogy.test_ep05_first_reformulation import generate
from tests.unit.pedagogy.test_dialogue_socratic_turns import make_packet


EXTRAS = {
    "objective": "A4_OBJECTIVE La ficha sintetica pesa nueve gramos.",
    "reasoning_guidance": "A4_REASONING La ficha sintetica siempre contiene tres letras.",
    "formalization": "A4_FORMAL La ficha sintetica vale 999 unidades <sin soporte>.",
    "implementation_guidance": "A4_IMPL El registro sintetico siempre ocupa ocho bytes.",
    "pitfalls": ("A4_PITFALL Todas las fichas sinteticas tienen siete caras.",),
}


def concept_case(verdict=AuditVerdict.APPROVED, extras=True):
    texts = [
        "A4_CORE En este modelo sintetico la ficha roja tiene dos posiciones permitidas.",
        "A4_MODEL En esta representacion sintetica cada casillero corresponde a una posicion de la ficha.",
    ]
    citations = [_citation(f"E{i + 1}", text) for i, text in enumerate(texts)]
    bundle = AssembledEvidenceBundle(
        {"PRIMARY": [citations[0]], "METHODOLOGICAL": [citations[1]]},
        citations, dict(zip(["E1", "E2"], texts)),
    )
    episode = Episode(
        episode_id="a4-synthetic-episode", session_id="a4-synthetic-session",
        notebook_id="a4-synthetic-notebook", kc_id="a4-synthetic-kc",
        objective="A4 synthetic ficha",
    )
    proposals, audit_inputs = [], []

    def build(**kwargs):
        proposal = ConceptPacketBuilder().build_proposal(**kwargs)
        if extras:
            proposal = replace(proposal, **EXTRAS)
        proposals.append(proposal)
        return proposal

    def audit(inp):
        audit_inputs.append(inp)
        return ForensicAuditReport(
            audit_id="A4_INSTRUMENTED_NOT_REAL_APPROVAL", request_id=inp.request.request_id,
            notebook_id=inp.request.notebook_id, overall_verdict=verdict,
            prompt_hash=inp.prompt_hash, evidence_hashes=tuple(c.content_hash for c in citations),
            nli_executed=False, audit_latency_ms=0,
            auditor_backend="A4_CONTROLLED_DOUBLE_NOT_REAL_S44",
        )

    orch = PedagogicalOrchestrator.__new__(PedagogicalOrchestrator)
    orch.get_episode = lambda eid: episode if eid == episode.episode_id else None
    orch.evidence_assembler = SimpleNamespace(assemble_evidence_bundle_for_kc=lambda **kwargs: bundle)
    orch.concept_builder = SimpleNamespace(build_proposal=build)
    orch.forensic_auditor = SimpleNamespace(audit=audit)
    with patch("study_engine.pedagogy.orchestrator.get_student_context", return_value=None):
        response = orch.explain_concept(episode.episode_id)
    # Exercise the API function without regenerating or mutating its internal response.
    container = SimpleNamespace(pedagogical_orchestrator=SimpleNamespace(explain_concept=lambda eid: response))
    payload = get_concept_explanation(episode.episode_id, container)
    return response, payload, audit_inputs[0], proposals[0]


def test_public_projection_excludes_all_unaudited_factual_fields_without_mutation():
    response, payload, inp, proposal = concept_case()
    before = response.packet.to_dict()
    public = json.loads(json.dumps(jsonable_encoder(payload)))
    assert public["status"] == "PRESENTABLE"
    packet = public["packet"]
    assert inp.response.text == f"{packet['core_concept']}\n{packet['mental_model']}"
    assert packet["objective"] == packet["reasoning_guidance"] == ""
    assert packet["formalization"] is packet["implementation_guidance"] is None
    assert packet["pitfalls"] == []
    assert not any(marker in json.dumps(public) for marker in ["A4_OBJECTIVE", "A4_REASONING", "A4_FORMAL", "A4_IMPL", "A4_PITFALL"])
    for field in ("kc_id", "notebook_id", "citations", "evidence_by_role", "assembly_hash", "audit_verdict"):
        assert packet[field] == before[field]
    assert response.packet.to_dict() == before
    for field, value in EXTRAS.items():
        assert getattr(response.packet, field) == getattr(proposal, field) == value
    assert response.to_dict() == payload  # Repeated/cached serialization uses the same projection.


@pytest.mark.parametrize("verdict", [AuditVerdict.REJECTED_UNSUPPORTED, AuditVerdict.FLAGGED_UNASSESSED])
def test_rejected_and_inconclusive_responses_stay_abstained(verdict):
    response, payload, _, _ = concept_case(verdict)
    assert response.packet is None
    assert payload["status"] == "ABSTAINED" and payload["packet"] is None
    assert payload["audit_verdict"] == verdict.value


def test_extra_content_neither_changes_audit_binding_nor_becomes_public():
    baseline, base_payload, base_input, _ = concept_case(extras=False)
    extra, extra_payload, extra_input, _ = concept_case(extras=True)
    assert baseline.packet != extra.packet
    assert base_input.response.text == extra_input.response.text
    assert baseline.packet.assembly_hash == extra.packet.assembly_hash
    assert base_payload == extra_payload
    assert extra.packet.s44_report.prompt_hash == extra_input.prompt_hash
    assert extra.packet.s44_report.evidence_hashes == tuple(c.content_hash for c in extra.packet.citations)


def test_cached_internal_packet_keeps_ep05_guidance_after_public_serialization(monkeypatch):
    guidance = "[E3] Primero identificá el tipo apuntado y después su tamaño."
    packet = replace(make_packet(), reasoning_guidance=guidance)
    response = ConceptResponse(status="PRESENTABLE", packet=packet, audit_verdict=AuditVerdict.APPROVED)
    monkeypatch.setattr(dialogue, "_EPISODE_CONCEPT_RESPONSES", {})
    orch = SimpleNamespace(explain_concept=lambda eid: response)
    cached = dialogue._load_or_reuse_concept_response(orch, "a4-synthetic-ep05")
    assert cached.to_dict()["packet"]["reasoning_guidance"] == ""
    reused = dialogue._load_or_reuse_concept_response(orch, "a4-synthetic-ep05")
    assert reused is cached and reused.packet is packet
    output = generate(reused.packet)
    assert output.answer == guidance
    assert "campo=reasoning_guidance" in output.rationale


def frontend_scenarios():
    """Pipe these actual API payloads to the React test; no fixture files needed."""
    return {
        name: concept_case(verdict, extras)[1]
        for name, verdict, extras in [
            ("approved", AuditVerdict.APPROVED, False),
            ("extra", AuditVerdict.APPROVED, True),
            ("rejected", AuditVerdict.REJECTED_UNSUPPORTED, True),
            ("inconclusive", AuditVerdict.FLAGGED_UNASSESSED, True),
        ]
    }
