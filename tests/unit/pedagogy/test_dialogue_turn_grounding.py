"""Unit tests M1-02: respuesta del turno de diálogo fundada en el packet.

Hallazgo live (run 21:37) + repro offline (offline_dialogue_l1.py): los
templates del diálogo citaban con tag TRAILING ("oración. [E1]"); el
ClaimExtractor canónico exige tag LEADING para asociar la cita al claim →
claim factual sin tags → CHECK_FACTUAL_GROUNDING FAIL → REJECTED_UNSUPPORTED
fail-closed en <300ms. Además, el texto de los templates era contenido
genérico propio no presente en la evidencia (inadmisible para S4.4).

Contrato corregido:
- El cuerpo factual del turno es el contenido del ConceptPacket ya APROBADO
  (continuidad; pares premise/hypothesis byte-idénticos → reuse de veredictos).
- La respuesta produce claims con tag LEADING: CHECK_FACTUAL_GROUNDING PASS
  verificada contra el L1 REAL (DeterministicAuditEngine), no contra una
  heurística propia del test.
"""

import asyncio
import hashlib
import sys
import pytest
from unittest.mock import AsyncMock, Mock
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.audit.contracts import (
    ForensicAuditInput,
    AuditVerdict,
    ForensicAuditReport,
)
from study_engine.contracts.evidence_engine import GroundingDecision  # noqa: F401
from study_engine.audit.engine import DeterministicAuditEngine
from study_engine.audit.generation_adapter import audit_generation_payload
from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.dialogue_engine import DialogueEngine
from study_engine.pedagogy.dialogue_policy import ValidatedIntent

CHUNK_CONTENT = (
    "Un puntero es una variable que contiene la dirección de memoria de otro objeto. "
    "La aritmética de punteros escala el desplazamiento por el tamaño del tipo apuntado."
)
CONTENT_HASH = hashlib.sha256(CHUNK_CONTENT.encode("utf-8")).hexdigest()

CITATION = CitationRecord(
    citation_id="E1",
    chunk_id="chk_E1",
    document_id="doc_E1",
    source_id="src_joyanes_fundamentos",
    source_title="Joyanes - Fundamentos de Programación",
    content_hash=CONTENT_HASH,
)


def make_packet() -> ConceptPacket:
    """Packet con core_concept TAG-LEADING (formato canónico del builder)."""
    return ConceptPacket(
        kc_id="aritmetica_punteros",
        notebook_id="fase0-soc",
        objective="Comprender aritmética de punteros",
        evidence_by_role={"PRIMARY": [CITATION]},
        core_concept="[E1] Un puntero es una variable que contiene la dirección de memoria de otro objeto.",
        mental_model="[E1] La aritmética de punteros escala el desplazamiento por el tamaño del tipo apuntado.",
        reasoning_guidance="Paso 1: identificar la base. Paso 2: multiplicar por sizeof.",
        formalization=None,
        implementation_guidance=None,
        pitfalls=(),
        citations=(CITATION,),
        s44_report=None,
        audit_verdict=AuditVerdict.APPROVED,
        assembly_hash="d" * 64,
    )


def make_engine() -> DialogueEngine:
    store = {"chk_E1": SimpleNamespace(content=CHUNK_CONTENT, id="chk_E1")}
    loader = lambda chunk_id: store.get(chunk_id)  # noqa: E731
    return DialogueEngine(chunk_content_loader=loader)


def make_intent(proposed: str = "CLARIFICATION") -> ValidatedIntent:
    return ValidatedIntent(
        action="PROCEED_DIALOGUE",
        query_text="¿cómo funciona?",
        proposed_intent=proposed,
    )


def retrieve_evidence(engine: DialogueEngine):
    return asyncio.run(
        engine._retrieve_evidence(
            concept_packet=make_packet(),
            intent=make_intent(),
            notebook_id="fase0-soc",
        )
    )


def test_turn_answer_is_packet_derived_and_tag_leading():
    engine = make_engine()
    out = asyncio.run(
        engine._generate_response(
            intent=make_intent(),
            evidence=retrieve_evidence(engine),
            concept_packet=make_packet(),
            dialogue_state=SimpleNamespace(),
            student_message="¿Cómo funciona la aritmética de punteros?",
        )
    )
    # Tag LEADING (formato canónico), jamás trailing.
    assert out.answer.startswith("[E1]")
    assert not out.answer.rstrip().endswith("[E1]")
    # El cuerpo factual proviene del packet aprobado (continuidad).
    assert "Un puntero es una variable que contiene la dirección" in out.answer
    # Pregunta socrática determinista presente.
    assert out.socratic_question


def test_example_request_includes_tagged_mental_model():
    engine = make_engine()
    out = asyncio.run(
        engine._generate_response(
            intent=make_intent("EXAMPLE_REQUEST"),
            evidence=retrieve_evidence(engine),
            concept_packet=make_packet(),
            dialogue_state=SimpleNamespace(),
            student_message="¿Me das un ejemplo?",
        )
    )
    assert out.answer.startswith("[E1]")
    assert "escala el desplazamiento" in out.answer


def test_grounded_answer_passes_real_l1_grounding_check():
    """Extremo a extremo con el L1 REAL: la respuesta del turno producida por
    `_generate_response` no dispara CHECK_FACTUAL_GROUNDING FAIL (el fallo del
    formato tag-trailing). Sin NLI ni proveedor: sólo capa determinista."""
    engine = make_engine()
    packet = make_packet()
    out = asyncio.run(
        engine._generate_response(
            intent=make_intent(),
            evidence=retrieve_evidence(engine),
            concept_packet=packet,
            dialogue_state=SimpleNamespace(),
            student_message="¿Cómo funciona?",
        )
    )
    verdict_holder = {}
    report = audit_generation_payload(
        SimpleNamespace(
            audit=lambda audit_input: _engine_only_audit(audit_input, verdict_holder)
        ),
        generated_text=out.answer,
        context_chunks=list(retrieve_evidence(engine).chunks),
        query="dialogue_turn",
        notebook_id="fase0-soc",
        provider_id="dialogue_engine",
        prompt_hash="e" * 64,
    )
    checks = {c.check_id: c for c in report.deterministic_checks}
    grounding = checks.get("CHECK_FACTUAL_GROUNDING")
    assert grounding is not None, list(checks)
    assert grounding.status.value == "PASS", grounding.reason


def _engine_only_audit(audit_input: ForensicAuditInput, holder: dict) -> ForensicAuditReport:
    """Ejecuta SOLO el L1 determinista (sin NLI) y devuelve un reporte con el
    early verdict si hubiera fallo crítico — replica el fail-closed del
    auditor sin llamadas al proveedor."""
    det = DeterministicAuditEngine().evaluate(audit_input)
    holder["det"] = det
    if det.has_critical_failure:
        return ForensicAuditReport(
            audit_id="audit_offline_l1",
            request_id=audit_input.request.request_id,
            notebook_id=audit_input.request.notebook_id,
            overall_verdict=det.early_verdict or AuditVerdict.REJECTED_POLICY_VIOLATION,
            deterministic_checks=det.checks,
            claim_verifications=(),
            nli_executed=False,
            prompt_hash=audit_input.prompt_hash,
            audit_latency_ms=0.1,
            auditor_backend="offline-l1",
        )
    # Sin fallo crítico: el L1 no decide APPROVED (eso corresponde al NLI);
    # reporte neutro FLAGGED_UNASSESSED para no escalar epistemicamente.
    return ForensicAuditReport(
        audit_id="audit_offline_l1",
        request_id=audit_input.request.request_id,
        notebook_id=audit_input.request.notebook_id,
        overall_verdict=AuditVerdict.FLAGGED_UNASSESSED,
        deterministic_checks=det.checks,
        claim_verifications=(),
        nli_executed=False,
        prompt_hash=audit_input.prompt_hash,
        audit_latency_ms=0.1,
        auditor_backend="offline-l1",
    )


def test_trailing_tag_answer_would_fail_l1():
    """Negativa de control: el formato PREVIO (tag trailing) SÍ dispara el
    FAIL de grounding en el L1 real — documenta el bug corregido."""
    old_style = (
        "La estructura contigua en memoria permite determinar la dirección de cualquier elemento "
        "en tiempo O(1). [E1]"
    )
    report = audit_generation_payload(
        SimpleNamespace(
            audit=lambda audit_input: _engine_only_audit(audit_input, {})
        ),
        generated_text=old_style,
        context_chunks=[{
            "citation_id": "E1",
            "chunk_id": "chk_E1",
            "document_id": "doc_E1",
            "source_id": "src_joyanes_fundamentos",
            "source_title": "Joyanes - Fundamentos de Programación",
            "content": CHUNK_CONTENT.strip(),
            "content_hash": hashlib.sha256(CHUNK_CONTENT.strip().encode()).hexdigest(),
        }],
        query="dialogue_turn",
        notebook_id="fase0-soc",
        provider_id="dialogue_engine",
        prompt_hash="f" * 64,
    )
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def binding_fixture():
    """Synthetic, agent-authored evidence; no store, provider or StudentState."""
    from study_engine.pedagogy.dialogue_engine import EvidenceResult

    engine = make_engine()
    citations = tuple(
        CITATION.model_copy(update={
            "citation_id": f"E{i}", "chunk_id": f"chk_E{i}",
            "document_id": f"doc_E{i}", "source_id": f"synthetic_{i}",
            "source_title": f"Synthetic source {i}", "author": "Synthetic author",
            "page_start": i, "page_end": i,
        }) for i in range(1, 5)
    )
    store = {c.chunk_id: SimpleNamespace(content=CHUNK_CONTENT) for c in citations}
    engine.chunk_content_loader = store.get
    chunks = [engine._load_verified_chunk(c) for c in citations]
    assert all(chunks)
    evidence = EvidenceResult(chunks, citations, "CONCEPT_PACKET")
    evidence.notebook_id = "synthetic-notebook"
    return engine, evidence


def run_binding_turn(engine, evidence, answer, *, real_auditor=False, verdict="APPROVED"):
    from study_engine.audit.auditor import ForensicAuditor
    from study_engine.audit.nli import MockNLIJudge
    from study_engine.pedagogy.dialogue_engine import LLMDialogueOutput
    from study_engine.pedagogy.dialogue_contracts import DialogueState

    engine._retrieve_evidence = AsyncMock(return_value=evidence)
    engine._generate_response = AsyncMock(return_value=LLMDialogueOutput(answer))
    if real_auditor:
        # Actual S4.4 orchestration and L1; only semantic NLI is simulated.
        engine.forensic_auditor = ForensicAuditor(nli_judge=MockNLIJudge())
    else:
        engine._execute_s44_audit = Mock(return_value=verdict)
    state = DialogueState(episode_id="synthetic-episode")
    engine.state_tracker.update_from_turn = Mock(wraps=engine.state_tracker.update_from_turn)
    response = asyncio.run(engine.process_turn(
        episode=SimpleNamespace(episode_id=state.episode_id, notebook_id="synthetic-notebook", kc_id="synthetic-kc"),
        concept_packet=None, dialogue_state=state, student_message="Explicame el concepto",
    ))
    return response, state


@pytest.mark.parametrize("answer", [
    "[E1] Un puntero es una variable. [E2] La aritmética escala el desplazamiento.",
    "[E1, E2] Un puntero es una variable. [E1] Un puntero contiene una dirección.",
])
def test_binding_returns_only_used_original_citations(answer):
    engine, evidence = binding_fixture()
    response, _ = run_binding_turn(engine, evidence, answer)
    assert response.status == "RESPONDED"
    assert response.answer == answer
    assert response.citations == evidence.citations[:2]
    assert all(a is b for a, b in zip(response.citations, evidence.citations))


@pytest.mark.parametrize("failure", [
    "unknown", "duplicate_record", "duplicate_chunk", "missing_chunk", "document", "page", "hash", "content",
])
def test_binding_abstains_without_recording_approved_turn(failure):
    engine, evidence = binding_fixture()
    answer = "[E1] Un puntero es una variable."
    if failure == "unknown":
        answer = "[E99] Un puntero es una variable."
    elif failure == "duplicate_record":
        evidence.citations += (evidence.citations[0].model_copy(update={"document_id": "other"}),)
    elif failure == "duplicate_chunk":
        evidence.chunks += (dict(evidence.chunks[0]),)
    elif failure == "missing_chunk":
        evidence.chunks = evidence.chunks[1:]
    else:
        field, value = {
            "document": ("document_id", "other"), "page": ("page_start", 999),
            "hash": ("original_content_hash", "a" * 64), "content": ("content", "Tampered evidence"),
        }[failure]
        evidence.chunks[0][field] = value
    response, state = run_binding_turn(engine, evidence, answer)
    assert response.status == "ABSTAINED"
    assert response.answer is None and response.citations == ()
    assert response.audit_verdict != "APPROVED"
    assert response.dialogue_state is state and state.turn_count == 0
    engine.state_tracker.update_from_turn.assert_not_called()


@pytest.mark.parametrize("answer, expected", [
    ("[E1] " + CHUNK_CONTENT.split(". ")[0] + ". [E2] " + CHUNK_CONTENT.split(". ")[1], "RESPONDED"),
    ("[E99] Un puntero es una variable.", "ABSTAINED"),
    ("Un puntero es una variable.", "ABSTAINED"),
    ("Hola", "RESPONDED"),
])
def test_binding_with_effective_auditor_and_synthetic_nli(answer, expected):
    engine, evidence = binding_fixture()
    response, state = run_binding_turn(engine, evidence, answer, real_auditor=True)
    assert response.status == expected
    if expected == "RESPONDED":
        assert response.audit_verdict == "APPROVED" and response.answer == answer
        expected_citations = evidence.citations[:2] if "[E1]" in answer else ()
        assert response.citations == expected_citations
    else:
        assert response.audit_verdict != "APPROVED"
        assert response.dialogue_state is state
        engine.state_tracker.update_from_turn.assert_not_called()


def test_binding_rejected_audit_never_records_turn():
    engine, evidence = binding_fixture()
    response, state = run_binding_turn(engine, evidence, "[E1] Un puntero es una variable.", verdict="REJECTED_UNSUPPORTED")
    assert response.status == "ABSTAINED" and response.dialogue_state is state
    engine.state_tracker.update_from_turn.assert_not_called()
