"""Contract tests for Subsystem S4.2 Generation Contracts."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    CurricularIsolationError,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
)
from study_engine.contracts.generation import (
    AbstentionDetails,
    AbstentionOrigin,
    AbstentionType,
    ConversationRole,
    ConversationTurn,
    GenerationMode,
    GenerationParameters,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    RawGenerationResult,
    ResponseValidationStatus,
    TokenUsage,
)
from study_engine.generation.base import BaseGenerator
from study_engine.generation.mock import MockGenerator


def _build_test_context(notebook_id: str = "fadena-so") -> PackagedContext:
    """Helper to build minimal valid PackagedContext."""
    packet = EvidencePacket(
        original_query="What is a process?",
        normalized_query="What is a process?",
        notebook_id=notebook_id,
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
    )
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        source_title="SO",
        content_hash="a" * 64,
    )
    manifest = CitationManifest(records={"E1": rec})
    return PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        formatted_context_block="[E1] Fuente: SO",
        total_characters=15,
        epistemic_policy="Mandatory policy",
    )


def test_generation_models_immutability():
    """Verify HG-S4.2-08: Generation contract models are strictly frozen."""
    ctx = _build_test_context()

    # 1. ConversationTurn
    turn = ConversationTurn(role=ConversationRole.STUDENT, content="Hola")
    with pytest.raises((ValidationError, TypeError)):
        turn.content = "Nuevo mensaje"  # type: ignore[misc]

    # 2. TokenUsage
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    with pytest.raises((ValidationError, TypeError)):
        usage.total_tokens = 50  # type: ignore[misc]

    # 3. GenerationParameters
    params = GenerationParameters(temperature=0.5, max_output_tokens=500)
    with pytest.raises((ValidationError, TypeError)):
        params.temperature = 0.8  # type: ignore[misc]

    # 4. ParsedCitation
    cite = ParsedCitation(citation_id="E1", in_manifest=True)
    with pytest.raises((ValidationError, TypeError)):
        cite.in_manifest = False  # type: ignore[misc]

    # 5. AbstentionDetails
    ab_det = AbstentionDetails(
        origin=AbstentionOrigin.EVIDENCE_POLICY,
        abstention_type=AbstentionType.NO_EVIDENCE,
        reason="Sin evidencias.",
    )
    with pytest.raises((ValidationError, TypeError)):
        ab_det.reason = "Modificada"  # type: ignore[misc]

    # 6. GenerationRequest
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="Explica procesos",
        packaged_context=ctx,
    )
    with pytest.raises((ValidationError, TypeError)):
        req.query = "Pregunta cambiada"  # type: ignore[misc]

    # 7. RawGenerationResult
    raw = RawGenerationResult(raw_content="Respuesta")
    with pytest.raises((ValidationError, TypeError)):
        raw.raw_content = "Otra respuesta"  # type: ignore[misc]

    # 8. GenerationResponse
    resp = GenerationResponse(
        response_id="resp-1",
        request_id="req-1",
        notebook_id="fadena-so",
        mode=GenerationMode.EXPLANATION,
        text="Respuesta limpia",
        raw_content="Respuesta limpia",
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
    )
    with pytest.raises((ValidationError, TypeError)):
        resp.text = "Texto alterado"  # type: ignore[misc]


def test_notebook_id_isolation_enforced():
    """Verify HG-S4.2-09: Request notebook_id must match context."""
    ctx_so = _build_test_context(notebook_id="fadena-so")

    # Mismatch between request notebook and context notebook must raise
    with pytest.raises(CurricularIsolationError) as exc_info:
        GenerationRequest(
            request_id="req-cross",
            notebook_id="fadena-prog",  # Mismatched notebook!
            query="Pregunta de programacion",
            packaged_context=ctx_so,  # Built for fadena-so!
        )
    assert "does not match PackagedContext notebook_id" in str(exc_info.value)


def test_conversation_role_enum_enforced():
    """Verify HG-S4.2-10: Only STUDENT and TUTOR roles are allowed."""
    assert ConversationRole.STUDENT.value == "student"
    assert ConversationRole.TUTOR.value == "tutor"

    turn = ConversationTurn(role=ConversationRole.STUDENT, content="Pregunta")
    assert turn.role == ConversationRole.STUDENT

    with pytest.raises(ValidationError):
        ConversationTurn(
            role="admin",  # type: ignore[arg-type]
            content="Intento de rol no autorizado",
        )


def test_no_automatic_mastery_advancement_fields():
    """Verify HG-S4.2-06: Response has no student advancement fields."""
    forbidden_fields = {
        "mastery_updated",
        "student_state",
        "advance_curricular",
        "mastered",
        "skill_level",
        "passed",
    }
    response_fields = set(GenerationResponse.model_fields.keys())
    assert forbidden_fields.isdisjoint(response_fields)


def test_base_generator_protocol_runtime_checkable():
    """Verify HG-S4.2-01: Mock implements runtime-checkable BaseGenerator."""
    gen = MockGenerator()
    assert isinstance(gen, BaseGenerator)


def test_enums_domain_integrity():

    """Verify closed domain enums retain all contract values."""
    assert set(GenerationMode) == {
        GenerationMode.EXPLANATION,
        GenerationMode.SOCRATIC_TUTOR,
        GenerationMode.EVALUATION,
        GenerationMode.PRACTICE_GENERATION,
    }
    assert set(AbstentionType) == {
        AbstentionType.NO_EVIDENCE,
        AbstentionType.INSUFFICIENT_CONTEXT,
        AbstentionType.CURRICULAR_LEAKAGE,
        AbstentionType.POLICY_REFUSAL,
    }
    assert set(AbstentionOrigin) == {
        AbstentionOrigin.EVIDENCE_POLICY,
        AbstentionOrigin.GENERATOR,
    }
    assert set(ResponseValidationStatus) == {
        ResponseValidationStatus.VALID,
        ResponseValidationStatus.INVALID_CITATION_DETECTED,
        ResponseValidationStatus.MALFORMED_OUTPUT,
    }
