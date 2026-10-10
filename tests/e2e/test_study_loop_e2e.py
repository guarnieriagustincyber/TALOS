"""End-to-End Test Suite for TALOS V1 Study Loop Integration (CP124).

Normative Reference:
- CP123: reports/e2e_study_loop/STUDY_LOOP_ARCHAEOLOGY.md
- CP123: reports/e2e_study_loop/STUDY_LOOP_CONTRACT_MATRIX.md
- CP123: reports/e2e_study_loop/E2E_TEST_PLAN.md
- CP123: reports/e2e_study_loop/E2E_GAP_REGISTER.md
- CP123: checkpoints/123-e2e-study-loop-analysis.md

Verified Contracts & Principles:
- E2E-01: Happy Path (Session Open -> Curriculum Position -> In-scope Query -> FTS5 -> C5 -> SSE -> Citations -> Progress)
- E2E-02: Out-Of-Domain / Insufficient Grounding Abstention Fail-Closed (Zero LLM, Zero Hallucination)
- E2E-03: Source Authorization & L3 ACL Cross-Curriculum Isolation
- E2E-04: Retrieval Failure Resilience & Safe Fail-Closed
- E2E-05: Multi-Provider Fallback Cascade with C1 Grounding Preservation
- E2E-06: Session & Memory Continuity Multi-Turn Tracking
- E2E-07: S6 Sandbox Practice Fail-Closed Contract (PRACTICE_UNAVAILABLE)
- E2E-08: BKT Boundary Isolation (Chat does NOT mutate BKT; Formal Evaluation DOES mutate BKT)
- E2E-09: Historical Test Drift Verification (C5 Trust Gate Abstention on ungrounded practice)
"""

import json
from pathlib import Path
import sqlite3
from typing import Any, AsyncGenerator, Generator, Tuple
import pytest
from study_engine.diagnostics.gate2_snapshots import backup_read_only_database
from fastapi.testclient import TestClient

from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import ProviderBackend
from study_engine.llm.multi_fallback import MultiFallbackBackend
from study_engine.llm.offline_oracle import OfflinePedagogicalBackend
import study_engine.web.app as web_app
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container
import study_engine.web.routes.chat as chat_module


class FailingProviderBackend(ProviderBackend):
    """Deterministic failing provider to test MultiFallbackBackend cascade."""

    async def stream(self, prompt_bundle: PromptBundle, **kwargs) -> AsyncGenerator[str, None]:
        # Yield nothing and raise an exception simulating cloud API timeout / 504
        if False:
            yield ""
        raise RuntimeError("Primary Cloud Provider Timeout (504 Gateway Timeout)")


class DummyVectorStore:
    """Zero-overhead vector store that keeps E2E retrieval on the test workspace."""

    def get_vector_matrix(self, notebook_id: str) -> Tuple[list, Any]:
        return [], None


@pytest.fixture
def isolated_e2e_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    web_state_test_copy: Path,
) -> Generator[Tuple[TestClient, AppContainer, Path], None, None]:
    """Use per-test writable copies derived from the sealed gate snapshot."""
    tmp_knowledge = tmp_path / "knowledge_store.db"
    tmp_student = tmp_path / "student_state.db"
    backup_read_only_database(web_state_test_copy / "knowledge_store.db", tmp_knowledge)
    backup_read_only_database(web_state_test_copy / "student_state.db", tmp_student)

    # Disable background vector warmup in app.py to prevent any background disk touch
    monkeypatch.setattr(web_app, "_warmup_notebooks", lambda s: [])

    # Initialize container bound strictly to tmp_path
    container = AppContainer(working_dir=tmp_path, use_mock=False)
    # Ensure vector store resolution never touches vector_store.db
    container.knowledge_store._vector_store = DummyVectorStore()

    # Use sovereign OfflinePedagogicalBackend as default deterministic engine
    container.llm_backend = MultiFallbackBackend(
        providers=[("offline_oracle", OfflinePedagogicalBackend())],
        timeout_per_provider=10.0,
    )

    set_container(container)
    app = create_app()

    with TestClient(app) as client:
        yield client, container, tmp_path


# ---------------------------------------------------------------------------
# E2E Test Cases
# ---------------------------------------------------------------------------

def test_e2e_01_happy_path(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-01: Happy Path of the Complete Study Loop.
    
    Verifies:
    1. Session Open (POST /api/study/session/open) returns snapshot with deterministic opening brief.
    2. In-scope query (POST /api/chat/query) retrieves authoritative FTS5 chunks.
    3. C5 Trust Gate certifies evidence sufficiency (abstained=False).
    4. SSE stream emits evidence_manifest, phase_start, phase_token, phase_complete.
    5. Final response contains valid provenance citations matching the manifest.
    6. Curriculum progress is recorded in SQLite.
    """
    client, container, tmp_path = isolated_e2e_env

    # 1. Session Open
    res_open = client.post(
        "/api/study/session/open",
        json={"notebook_id": "fadena-lenguajes", "student_id": "agustin"},
    )
    assert res_open.status_code == 200
    snap = res_open.json()
    session_id = snap["session_id"]
    assert session_id.startswith("sess_fadena-lenguajes_")
    assert snap["episode_phase"] == "OPENING_BRIEF"
    assert snap["current_kc_id"] == "leng_intro_algoritmos"
    assert snap["opening_brief_facts"] is not None
    assert len(snap["available_actions"]) > 0

    # 2. In-scope Query
    res_chat = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cuál es la diferencia entre malloc y calloc en C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": session_id,
        },
    )
    assert res_chat.status_code == 200
    assert "text/event-stream" in res_chat.headers["content-type"]

    lines = [l.strip() for l in res_chat.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]
    assert len(events) >= 5, "Expected structured SSE sequence"

    # 3. Evidence Manifest Assertion
    manifest = next((e for e in events if e.get("event_type") == "evidence_manifest"), None)
    assert manifest is not None, "evidence_manifest must be emitted"
    assert manifest["payload"]["abstained"] is False
    citations = manifest["payload"]["citations"]
    assert len(citations) > 0, "Expected non-empty retrieved citations"
    assert any("marzal" in c.get("source_id", "") or "C" in c.get("source_title", "") for c in citations)

    # 4. Phase Tokens Assertion
    phase_starts = [e for e in events if e.get("event_type") == "phase_start"]
    assert len(phase_starts) >= 1
    assert phase_starts[0]["payload"]["phase"] == "conceptual"

    tokens = [e["payload"]["token"] for e in events if e.get("event_type") == "phase_token"]
    assert len(tokens) > 10, "Expected streamed prose tokens"

    # 5. Phase Complete Assertion
    comp = next((e for e in events if e.get("event_type") == "phase_complete"), None)
    assert comp is not None, "phase_complete must be emitted"
    assert comp["payload"]["completed_phase"] == "conceptual"
    assert comp["payload"]["tokens_produced"] > 0
    assert "evidence_provenance" in comp["payload"]
    provenance = comp["payload"]["evidence_provenance"]
    assert len(provenance) > 0

    # Assert provenance chunk IDs match citations
    manifest_chunks = {c["chunk_id"] for c in citations}
    for prov in provenance:
        assert prov["chunk_id"] in manifest_chunks, f"Orphan provenance chunk {prov['chunk_id']} not in manifest"

    # 6. Curriculum Progress Assertion in SQLite
    con = sqlite3.connect(tmp_path / "student_state.db")
    progress_rows = con.execute("SELECT notebook_id, kc_id, status FROM curriculum_progress WHERE notebook_id='fadena-lenguajes'").fetchall()
    con.close()
    assert len(progress_rows) > 0, "Curriculum progress must be persisted"


def test_e2e_02_out_of_domain_insufficient_grounding(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-02: Out-Of-Domain / Insufficient Evidence Abstention (C5 Fail-Closed).
    
    Verifies:
    1. Query completely outside the curricular scope of C programming is blocked by C5 Trust Gate.
    2. Exactly 2 events are emitted: evidence_manifest (abstained=True) and abstention.
    3. ZERO LLM calls occur, ZERO tokens are streamed, and no unsupported text is hallucinated.
    """
    client, _, _ = isolated_e2e_env

    res = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cómo se entrena una red neuronal convolucional en PyTorch?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": "sess_e2e_ood",
        },
    )
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]

    assert len(events) == 2, f"Expected exactly 2 events (manifest + abstention), got {len(events)}"

    manifest = events[0]
    assert manifest["event_type"] == "evidence_manifest"
    assert manifest["payload"]["abstained"] is True
    assert manifest["payload"]["trust_status"] == "NO_EVIDENCE"
    assert manifest["payload"]["abstention_reason"] == "QUERY_OUT_OF_SCOPE"

    abst = events[1]
    assert abst["event_type"] == "abstention"
    assert abst["payload"]["abstained"] is True
    assert "No se hallaron evidencias curriculares" in abst["payload"]["reason"]
    assert abst["payload"]["notebook_id"] == "fadena-lenguajes"

    # Ensure zero token generation
    token_events = [e for e in events if e.get("event_type") == "phase_token"]
    assert len(token_events) == 0, "No tokens should be generated when abstained"


def test_e2e_03_source_authorization_l3_acl_isolation(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-03: Cross-Curriculum Source Authorization & L3 ACL Isolation.
    
    Verifies:
    1. Explicitly requesting a source belonging exclusively to another notebook (fadena-so2)
       from within fadena-lenguajes is intercepted by L3 ACL.
    2. The unauthorized source is discarded before retrieval and never reaches the ContextPack or LLM.
    3. System abstains fail-closed with NO_AUTHORIZED_ACTIVE_SOURCES.
    """
    client, _, _ = isolated_e2e_env

    # src_0bc5d20dcc91895f is Tanenbaum OS, belonging to fadena-so2, NOT authorized in fadena-lenguajes
    res = client.post(
        "/api/chat/query",
        json={
            "prompt": "Explica la planificación de procesos",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "active_sources": ["src_0bc5d20dcc91895f"],
            "session_id": "sess_e2e_l3",
        },
    )
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]

    assert len(events) == 2
    manifest = events[0]
    assert manifest["payload"]["abstained"] is True
    assert manifest["payload"]["abstention_reason"] == "NO_AUTHORIZED_ACTIVE_SOURCES"
    assert manifest["payload"]["trust_status"] == "NO_AUTHORIZED_EVIDENCE"

    abst = events[1]
    assert abst["event_type"] == "abstention"
    assert abst["payload"]["abstention_code"] == "NO_AUTHORIZED_ACTIVE_SOURCES"


def test_e2e_04_retrieval_failure_resilience(isolated_e2e_env: Tuple[TestClient, AppContainer, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """E2E-04: Retrieval Service Outage & Fail-Closed Resilience.
    
    Verifies:
    1. When an unexpected retrieval crash occurs (disk lock, corruption, or syntax error),
       the endpoint catches it and does NOT crash with HTTP 500.
    2. Emits streaming error event with safe message, preserving zero ungrounded generation.
    """
    client, _, _ = isolated_e2e_env

    # Simulate retrieval crash
    def crashing_auth_sources(*args, **kwargs):
        raise RuntimeError("Simulated Database I/O Disk Crash in Retrieval Engine")

    monkeypatch.setattr(chat_module, "_authorized_sources_for_scope", crashing_auth_sources)

    res = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cuál es la diferencia entre malloc y calloc en C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": "sess_e2e_retrieval_fail",
        },
    )
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]

    assert len(events) >= 2
    manifest = events[0]
    assert manifest["payload"]["abstained"] is True
    assert manifest["payload"]["trust_status"] in ("NO_AUTHORIZED_EVIDENCE", "RETRIEVAL_FAILURE")

    error_or_abst = events[1]
    assert error_or_abst["event_type"] in ("abstention", "error")
    assert error_or_abst["payload"]["abstained"] is True

    # Zero token generation
    assert not any(e.get("event_type") == "phase_token" for e in events)


def test_e2e_05_provider_fallback_cascade(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-05: Multi-Provider Fallback Cascade with Grounding Preservation.
    
    Verifies:
    1. When Provider A raises an error/timeout, MultiFallbackBackend intercepts it and cascades to Provider B.
    2. Response streaming completes successfully without losing evidence citations.
    3. Grounding and L3 ACL invariants are preserved across provider fallback.
    """
    client, container, _ = isolated_e2e_env

    # Reconfigure backend with a failing primary and sovereign offline secondary
    container.llm_backend = MultiFallbackBackend(
        providers=[
            ("failing_primary", FailingProviderBackend()),
            ("offline_secondary", OfflinePedagogicalBackend()),
        ],
        timeout_per_provider=5.0,
    )

    res = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cuál es la diferencia entre malloc y calloc en C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": "sess_e2e_fallback",
        },
    )
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]

    # Verify fallback succeeded and completed phase
    tokens = [e["payload"]["token"] for e in events if e.get("event_type") == "phase_token"]
    assert len(tokens) > 0, "Tokens must be streamed from the fallback provider"

    comp = next((e for e in events if e.get("event_type") == "phase_complete"), None)
    assert comp is not None, "phase_complete must be emitted after fallback"
    assert comp["payload"]["completed_phase"] == "conceptual"
    assert len(comp["payload"]["evidence_provenance"]) > 0


def test_e2e_06_session_and_memory_continuity(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-06: Session & Memory Continuity Multi-Turn Tracking.
    
    Verifies:
    1. Turn 1 establishes conversation history buffer.
    2. Turn 2 in the same session increments turn count and passes server turns context.
    3. Conversation rescue compatibility evaluates thematic coherence.
    """
    client, _, _ = isolated_e2e_env
    sess_id = "sess_e2e_continuity_01"

    # Turn 1
    res1 = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cuál es la diferencia entre malloc y calloc en C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": sess_id,
        },
    )
    assert res1.status_code == 200

    # Turn 2
    res2 = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Y cómo se usa realloc para cambiar el tamaño?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": sess_id,
        },
    )
    assert res2.status_code == 200
    lines2 = [l.strip() for l in res2.text.split("\n") if l.startswith("data: ")]
    events2 = [json.loads(l[6:]) for l in lines2]

    comp2 = next((e for e in events2 if e.get("event_type") == "phase_complete"), None)
    assert comp2 is not None, "Turn 2 must complete"
    conv_ctx = comp2["payload"].get("conversation_context", {})
    assert conv_ctx.get("turn_count", 0) >= 2, f"Expected turn_count >= 2, got {conv_ctx}"
    assert conv_ctx.get("source") == "server"


def test_e2e_07_practice_contract_fail_closed(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-07: S6 Sandbox Practice Fail-Closed Contract (PRACTICE_UNAVAILABLE).
    
    Verifies:
    1. Code submission to /api/practice/evaluate returns HTTP 200.
    2. Payload status is strictly PRACTICE_UNAVAILABLE with S6 sandbox message.
    3. Demonstrates that TALOS V1 safely fails closed without pretending to execute code.
    """
    client, _, _ = isolated_e2e_env

    res = client.post(
        "/api/practice/evaluate",
        json={
            "task_id": "task_ptr_01",
            "file_path": "data/student_submissions/ptr.c",
            "command": ":eval",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "PRACTICE_UNAVAILABLE"
    assert "[S6] Sandbox de ejecución real no disponible en esta versión." in body["stdout"]
    assert body["assertions_passed"] == 0
    assert body["assertions_total"] == 0


def test_e2e_08_bkt_boundary_isolation(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-08: BKT Boundary Isolation (Chat does NOT mutate BKT; Formal Evaluation DOES).
    
    Verifies:
    1. Conversational chat interactions on /api/chat/query DO NOT mutate student BKT mastery P(L).
    2. Formal evaluations on /api/chat/evaluate DO mutate BKT mastery deterministically.
    3. Confirms intentional anti-gaming architectural boundary.
    """
    client, container, _ = isolated_e2e_env
    kc = "leng_pseudocodigo_estructurado"

    # 1. Initial State
    prior = container.bkt_tracker.get_state(kc)
    assert prior.attempts == 0
    assert prior.p_L == pytest.approx(0.1, abs=0.01)

    # 2. Chat queries must NOT mutate BKT
    for _ in range(3):
        res_chat = client.post(
            "/api/chat/query",
            json={
                "prompt": "¿Qué es el pseudocódigo estructurado y qué estructuras incluye?",
                "scope_type": "notebook",
                "scope_id": "fadena-lenguajes",
                "session_id": "sess_bkt_boundary",
            },
        )
        assert res_chat.status_code == 200

    post_chat = container.bkt_tracker.get_state(kc)
    assert post_chat.p_L == pytest.approx(prior.p_L, abs=0.0001), "Chat MUST NOT mutate BKT p_L"
    assert post_chat.attempts == prior.attempts, "Chat MUST NOT increment BKT attempts"

    # 3. Formal evaluation MUST mutate BKT
    res_eval = client.post(
        "/api/chat/evaluate",
        json={
            "exercise_id": "ex_lenguajes_pseudo_01",
            "user_answer": "C",
            "session_id": "sess_bkt_boundary",
        },
    )
    assert res_eval.status_code == 200
    eval_json = res_eval.json()
    assert eval_json["status"] == "GRADED"
    assert eval_json["is_correct"] is True
    assert eval_json["p_L"] > prior.p_L

    # Verify mutation persisted in SQLite
    post_eval = container.bkt_tracker.get_state(kc)
    assert post_eval.attempts == 1
    assert post_eval.p_L > prior.p_L
    assert post_eval.p_L == pytest.approx(eval_json["p_L"], abs=0.0001)


def test_e2e_09_certified_practice_dispatch(isolated_e2e_env: Tuple[TestClient, AppContainer, Path]) -> None:
    """E2E-09: A qualified exercise for the requested topic dispatches deterministically.
    
    The exercise registry contains a QUALIFIABLE pointer exercise sourced from
    the Fadena programming material; this is not a generic retrieval response.
    """
    client, container, _ = isolated_e2e_env
    assert any(
        exercise.is_presentable()
        and exercise.kc_id == "aritmetica_punteros"
        and exercise.source_id == "src_fadena_prog_punteros"
        for exercise in container.exercise_store.list_all()
    )

    res = client.post(
        "/api/chat/query",
        json={
            "prompt": "/practicar punteros",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "session_id": "sess_hist_drift",
        },
    )
    assert res.status_code == 200
    lines = [l.strip() for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]

    assert [event["event_type"] for event in events] == [
        "evidence_manifest",
        "exercise_proposal",
        "phase_complete",
    ]
    assert events[0]["payload"]["abstained"] is False
    assert events[1]["payload"]["kc_id"] == "aritmetica_punteros"
    assert events[2]["payload"]["status"] == "EXERCISE_PROPOSED"
    tokens = [e["payload"]["token"] for e in events if e.get("event_type") == "phase_token"]
    assert len(tokens) == 0, "Certified practice dispatch must not use generic response tokens"
