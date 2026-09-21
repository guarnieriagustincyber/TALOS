"""Unit and integration tests for Session Briefing & Episodic Memory (Semana 3)."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from study_engine.memory.session_briefing import SessionBriefingGenerator
from study_engine.memory.session_history import SessionHistory, SessionRecord
from study_engine.student.storage import StudentStorage
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.tutor.fastpath_service import FastPathConversationalService
from study_engine.tutor.policy_validator import RouteKind
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def test_session_briefing_generation():
    """Verify SessionBriefingGenerator produces coherent Rioplatense brief from history and BKT."""
    hist = SessionHistory(":memory:")
    storage = StudentStorage(":memory:")
    bkt = BKTTracker(storage)

    # Record previous session
    rec = SessionRecord(
        session_id="sess_1",
        notebook_id="nb_sistemas",
        student_id="agustin",
        topic="Punteros y Memoria Virtual",
        next_topic="Estructura del Stack Frame",
        timestamp=datetime.now(timezone.utc),
        hints_requested=2,
    )
    hist.record_session(rec)

    # Set weak KC in BKT
    from study_engine.student.contracts import BKTState
    storage.save_bkt_state(
        BKTState(
            kc_id="KC_PTR_ARITH",
            p_L=0.35,
            p_T=0.1,
            p_G=0.2,
            p_S=0.1,
            attempts=3,
            last_update=datetime.now(timezone.utc),
        )
    )

    gen = SessionBriefingGenerator(
        bkt_tracker=bkt,
        session_history=hist,
        student_storage=storage,
    )

    briefing = gen.generate_briefing(
        student_id="agustin",
        notebook_id="nb_sistemas",
        student_name="Agustín",
    )

    assert "Agustín, la última vez estuviste trabajando en Punteros y Memoria Virtual" in briefing
    assert "KC PTR ARITH" in briefing or "0.35" in briefing
    assert "Estructura del Stack Frame" in briefing


def test_get_briefing_rest_endpoint(tmp_path):
    """Verify GET /api/chat/briefing returns episodic summary."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)

    # Preload a session record in container's session_history
    rec = SessionRecord(
        session_id="sess_prev",
        notebook_id="nb_test_brief",
        student_id="agustin",
        topic="Interrupciones y Modos de CPU",
        next_topic="Llamadas al Sistema (syscalls)",
        timestamp=datetime.now(timezone.utc),
    )
    container.session_history.record_session(rec)

    client = TestClient(app)
    resp = client.get("/api/chat/briefing?notebook_id=nb_test_brief&student_id=agustin")
    assert resp.status_code == 200
    data = resp.json()

    assert "briefing" in data
    assert "Interrupciones y Modos de CPU" in data["briefing"]
    assert "weak_kcs" in data
    assert "due_reviews_count" in data


def test_fastpath_greeting_incorporates_briefing(tmp_path):
    """Verify FastPath greeting incorporates episodic briefing if previous session exists."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)

    # Preload session history
    rec = SessionRecord(
        session_id="sess_rec",
        notebook_id="nb_fastpath_brief",
        student_id="default_student",
        topic="Registros y Punteros en x86_64",
        next_topic="Instrucciones de Salto Condicional",
        timestamp=datetime.now(timezone.utc),
    )
    container.session_history.record_session(rec)

    fastpath = FastPathConversationalService()
    context = fastpath.extract_student_context(container, "nb_fastpath_brief")

    assert "session_briefing" in context
    assert "Registros y Punteros en x86_64" in context["session_briefing"]

    import asyncio
    reply = asyncio.run(
        fastpath.generate_response(
            query="¡Hola!",
            route_kind=RouteKind.GREETING,
            context=context,
            llm_backend=None,
        )
    )

    assert "Registros y Punteros en x86_64" in reply
