"""Contract tests for domain boundaries and cross-contract reference integrity.

Verifies that:
1. Cross-contract ID references (Source -> Document -> Chunk -> Evidence) align cleanly.
2. Notebook and StudyPlan correctly reference Source IDs.
3. StudyPlan and StudentState associate cleanly via student_id.
4. LLMRequest and LLMResponse correlate via request_id.
5. Incomplete metadata in upstream contracts does not break downstream contracts.
6. StudentState remains a data contract without automatic progression logic.
"""

import pytest

from study_engine.contracts import (
    Notebook,
    Source,
    SourceRole,
    Document,
    Chunk,
    Evidence,
    EvidenceStatus,
    StudentState,
    StudyPlan,
    LLMRequest,
    LLMResponse,
    Event,
)


def test_source_document_chunk_evidence_pipeline_boundary():
    """Verify that identifiers flow consistently from Source to Evidence."""
    # 1. Source (upstream)
    source = Source(
        source_id="spraul-think-like-a-programmer",
        title="Think Like a Programmer",
        author="V. Anton Spraul",
        role=SourceRole.COMPLEMENTARY,
        priority=2,
    )

    # 2. Document referencing Source
    document = Document(
        id="doc-spraul-ch2",
        source_id=source.source_id,
        title="Chapter 2: Pure Puzzles",
        page_count=28,
    )
    assert document.source_id == source.source_id

    # 3. Chunk referencing Document and Source
    chunk = Chunk(
        id="chunk-spraul-2-1",
        document_id=document.id,
        source_id=source.source_id,
        content="Always have a plan before writing code.",
        page_start=15,
        page_end=16,
        index=0,
    )
    assert chunk.document_id == document.id
    assert chunk.source_id == source.source_id

    # 4. Evidence referencing Chunk, Document, and Source
    evidence = Evidence(
        id="ev-spraul-001",
        claim="Spraul recomienda planificar antes de programar.",
        status=EvidenceStatus.SUPPORTED,
        content=chunk.content,
        source_id=source.source_id,
        document_id=document.id,
        chunk_id=chunk.id,
        page=chunk.page_start,
        confidence=0.99,
    )
    assert evidence.source_id == source.source_id
    assert evidence.document_id == document.id
    assert evidence.chunk_id == chunk.id
    assert evidence.status == EvidenceStatus.SUPPORTED


def test_notebook_source_association():
    """Verify Notebook can reference multiple Source IDs."""
    source_1 = Source(source_id="src-tanenbaum", title="Computer Networks")
    source_2 = Source(source_id="src-stallings", title="Data and Computer Communications")

    notebook = Notebook(
        id="fadena_redes",
        name="FADENA - Redes de Información",
        subject="Redes",
        sources=[source_1.source_id, source_2.source_id],
    )
    assert source_1.source_id in notebook.sources
    assert source_2.source_id in notebook.sources


def test_study_plan_and_student_state_association():
    """Verify StudyPlan references StudentState via student_id."""
    student_state = StudentState(
        student_id="student-1001",
        topic="Recursividad",
        status="developing",
        understanding={"conceptual": True, "application": False},
    )

    plan = StudyPlan(
        id="plan-rec-01",
        student_id=student_state.student_id,
        module="Recursión y Divide & Conquer",
        objective="Dominar recursión simple y de cola.",
        prerequisites=["Pilas y funciones"],
        concepts=["Caso base", "Llamada recursiva", "Recursión de cola"],
        sources=["src-joyanes"],
    )
    assert plan.student_id == student_state.student_id
    assert len(plan.prerequisites) == 1


def test_llm_request_response_correlation():
    """Verify LLMRequest and LLMResponse share matching request_id."""
    request = LLMRequest(
        request_id="req-eval-999",
        mode="tester",
        system_prompt="Evalúa la respuesta del alumno.",
        messages=[{"role": "user", "content": "La recursión termina en el caso base."}],
        temperature=0.0,
    )

    response = LLMResponse(
        request_id=request.request_id,
        content="Evaluación: Correcto. El caso base detiene las llamadas recursivas.",
        mode=request.mode,
        model="gpt-oss-120b",
        provider="groq",
        finish_reason="stop",
        latency_ms=95.2,
    )
    assert response.request_id == request.request_id
    assert response.mode == request.mode


def test_event_telemetry_across_session():
    """Verify Event contract tracks session-level domain actions."""
    event = Event(
        event_id="evt-req-001",
        session_id="sess-student-1001",
        event_type="llm_interaction",
        payload={
            "request_id": "req-eval-999",
            "mode": "tester",
            "latency_ms": 95.2,
            "tokens": 120,
        },
    )
    assert event.session_id == "sess-student-1001"
    assert event.payload["request_id"] == "req-eval-999"


def test_incomplete_metadata_upstream_does_not_break_downstream():
    """Upstream sources with sparse/empty metadata must not impede downstream document or chunk creation."""
    sparse_source = Source(source_id="src-sparse", title="Minimal Source")
    doc = Document(id="doc-sparse", source_id=sparse_source.source_id, title="Minimal Doc")
    chunk = Chunk(id="chunk-sparse", document_id=doc.id, source_id=sparse_source.source_id, content="Content")

    assert sparse_source.author is None
    assert doc.path is None
    assert chunk.page_start is None
    assert chunk.content == "Content"
