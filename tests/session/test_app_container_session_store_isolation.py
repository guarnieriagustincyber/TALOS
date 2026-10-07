from pathlib import Path

from study_engine.session.session_store import SessionStore
from study_engine.session.study_session_orchestrator import StudySessionOrchestrator
from study_engine.web.dependencies import AppContainer


def test_app_container_session_store_uses_working_dir_and_rehydrates(
    tmp_path: Path,
) -> None:
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    orchestrator = container.study_session_orchestrator
    session_db = tmp_path / "sessions.db"

    assert orchestrator.session_store.db_path == session_db
    snapshot = orchestrator.open_session(notebook_id="fase0-soc", student_id="agustin")

    restarted_orchestrator = StudySessionOrchestrator(
        notebook_registry=container.notebook_registry,
        pedagogical_orchestrator=container.pedagogical_orchestrator,
        session_store=SessionStore(session_db),
    )

    restored_snapshot = restarted_orchestrator.get_snapshot(snapshot.session_id)
    assert restored_snapshot.session_id == snapshot.session_id
    assert orchestrator.session_store.db_path != Path("data/student/sessions.db")
