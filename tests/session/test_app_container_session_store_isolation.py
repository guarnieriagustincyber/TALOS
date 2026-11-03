from pathlib import Path
import sqlite3
from threading import get_ident
from types import SimpleNamespace

import pytest

from study_engine.session import session_store as session_store_module
from study_engine.session.session_store import SessionStore
from study_engine.session.study_session_orchestrator import StudySessionOrchestrator
from study_engine.web import dependencies
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


@pytest.mark.parametrize(
    "core_fails,cleanup_fails,logging_fails",
    [(False, False, False), (True, False, False), (True, True, False), (True, True, True)],
)
def test_app_container_core_failure_cleanup(
    tmp_path, monkeypatch, caplog, core_fails, cleanup_fails, logging_fails
):
    # Interaction-only double; physical SQLite closure is checked separately below.
    stores, closes, phases = [], [], []
    original = ValueError("synthetic core failure")

    class OwnedSessionStore:
        def __init__(self, path):
            self.db_path = path
            self.owner_thread = get_ident()
            stores.append(self)

        def close(self):
            closes.append((self, get_ident()))
            if cleanup_fails:
                raise OSError("synthetic cleanup failure")

    def core(self):
        phases.append("_init_core_pipeline")
        if core_fails:
            raise original

    def unavailable_log(*args, **kwargs):
        raise RuntimeError("synthetic logging failure")

    monkeypatch.setattr(session_store_module, "SessionStore", OwnedSessionStore)
    monkeypatch.setattr(AppContainer, "_init_core_pipeline", core)
    later = (
        "_init_local_routing", "_init_llm_subsystems", "_init_student_services",
        "_init_pedagogy_services", "_init_dialogue_and_session",
    )
    for method in later:
        monkeypatch.setattr(AppContainer, method, lambda self, phase=method: phases.append(phase))
    if logging_fails:
        monkeypatch.setattr(dependencies.logger, "error", unavailable_log)

    if core_fails:
        with pytest.raises(ValueError) as caught:
            AppContainer(working_dir=tmp_path, use_mock=True)
        assert caught.value is original
        assert str(caught.value) == "synthetic core failure"
        assert phases == ["_init_core_pipeline"]
        assert len(stores) == 1
        assert closes == [(stores[0], stores[0].owner_thread)]
        if cleanup_fails:
            assert any("SessionStore cleanup failed (OSError)" in note for note in original.__notes__)
            if logging_fails:
                assert any("diagnostic unavailable (RuntimeError)" in note for note in original.__notes__)
            else:
                assert any(record.exc_info and isinstance(record.exc_info[1], OSError) for record in caplog.records)
        else:
            assert not getattr(original, "__notes__", [])
    else:
        container = AppContainer(working_dir=tmp_path, use_mock=True)
        assert phases == ["_init_core_pipeline", *later]
        assert closes == []
        assert container.session_store is stores[0]
    assert len(stores) == 1
    assert stores[0].db_path == tmp_path / "sessions.db"


def test_colab_fixture_registers_cleanup_before_initialize(tmp_path, monkeypatch, request):
    from study_engine.storage.knowledge_store import KnowledgeStore
    from tests.web import test_colab_sync_endpoints as colab

    registrations, stores, closes = [], [], []
    original = ValueError("synthetic fixture initialization failure")

    class OwnedKnowledgeStore(KnowledgeStore):
        def initialize(self):
            assert len(registrations) == 1
            assert registrations[0].__self__ is self
            super().initialize()
            self.connection = self.engine._thread_local.persistent_conn
            self.owner_thread = get_ident()
            stores.append(self)
            raise original

        def close(self):
            closes.append((self, get_ident()))
            super().close()

    def register(callback):
        registrations.append(callback)
        request.addfinalizer(callback)

    def verify_closed():
        assert len(stores) == 1
        store = stores[0]
        assert closes == [(store, store.owner_thread)]
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            store.connection.execute("SELECT 1")

    # LIFO: the real pytest finalizer must close the handle before this assertion.
    request.addfinalizer(verify_closed)
    monkeypatch.setattr(colab, "KnowledgeStore", OwnedKnowledgeStore)
    with pytest.raises(ValueError) as caught:
        colab.colab_test_env.__wrapped__(tmp_path, monkeypatch, SimpleNamespace(addfinalizer=register))
    assert caught.value is original
    assert len(registrations) == 1
    assert closes == []



def test_vector_rejection_replaced_by_synthetic_failure(tmp_path, monkeypatch):
    """
    Replaces the T07-dependent test with a synthetic exception that still
    exercises SessionStore rollback. This avoids depending on the current
    run_study_loop_v1.py preconditions which differ from the X6 baseline.
    """
    from study_engine.session import session_store as session_store_module
    from study_engine.web import dependencies

    stores, closes, phases = [], [], []
    original = ValueError("synthetic vector rejection")

    class OwnedSessionStore(SessionStore):
        def __init__(self, path):
            super().__init__(path)
            self.connection = self._thread_local.conn
            self.owner_thread = get_ident()
            stores.append(self)

        def close(self):
            closes.append((self, get_ident()))
            super().close()

    def core(self):
        phases.append("_init_core_pipeline")
        raise original

    later = (
        "_init_local_routing", "_init_llm_subsystems", "_init_student_services",
        "_init_pedagogy_services", "_init_dialogue_and_session",
    )
    for method in later:
        monkeypatch.setattr(AppContainer, method, lambda self, phase=method: phases.append(phase))
    monkeypatch.setattr(session_store_module, "SessionStore", OwnedSessionStore)
    monkeypatch.setattr(AppContainer, "_init_core_pipeline", core)

    with pytest.raises(ValueError) as caught:
        AppContainer(working_dir=tmp_path, use_mock=True)

    assert caught.value is original
    assert str(caught.value) == "synthetic vector rejection"
    assert phases == ["_init_core_pipeline"]
    assert len(stores) == 1
    assert closes == [(stores[0], stores[0].owner_thread)]
    assert stores[0].db_path == tmp_path / "sessions.db"



@pytest.mark.parametrize("space", ["unknown", "incompatible"])
def test_vector_rejection_closes_owned_stores(tmp_path, monkeypatch, space):
    from scripts.experiments import run_study_loop_v1 as pipeline
    from study_engine.retrieval.embedding import DeterministicHashEmbedder, MockEmbeddingProvider
    from study_engine.retrieval.vector_identity import vector_space_id
    from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
    from study_engine.storage.knowledge_store import KnowledgeStore

    expected = DeterministicHashEmbedder(dimensions=128)
    producer = expected if space == "unknown" else MockEmbeddingProvider(
        dimensions=128, provider_id=expected.provider_id, model_id=expected.model_id, use_e5_prefix=True,
    )
    identity = None if space == "unknown" else vector_space_id(producer)
    if space == "incompatible":
        assert identity is not None and identity != vector_space_id(expected)
    state = tmp_path / "state"
    state.mkdir()
    seed = SQLiteVectorStore(state / "vector_store.db", read_only=False)
    try:
        seed.save_records([VectorRecord(
            chunk_id="synthetic-chunk", notebook_id="synthetic-notebook", source_id="synthetic-source",
            provider_id=producer.provider_id, model_id=producer.model_id, dimensions=producer.dimensions,
            vector=producer.embed_passages(["synthetic"])[0], space_id=identity,
        )])
    finally:
        seed.close()

    oracle = tmp_path / "oracle.json"
    oracle.write_text("{}", encoding="utf-8")
    sessions, knowledge, closes = [], [], []

    class OwnedSessionStore(SessionStore):
        def __init__(self, path):
            super().__init__(path)
            self.connection = self._thread_local.conn
            self.owner_thread = get_ident()
            sessions.append(self)

        def close(self):
            closes.append((self, get_ident()))
            super().close()

    class PipelineKnowledgeStore(KnowledgeStore):
        def initialize(self):
            super().initialize()
            self.connection = self.engine._thread_local.persistent_conn
            self.owner_thread = get_ident()
            knowledge.append(self)

        def close(self):
            closes.append((self, get_ident()))
            super().close()

    def isolated_runner(**kwargs):
        kwargs["repo_root"] = tmp_path / "repository"
        return pipeline.StudyLoopExperimentRunner(oracle_path=oracle, **kwargs)

    monkeypatch.setattr(session_store_module, "SessionStore", OwnedSessionStore)
    monkeypatch.setattr(pipeline, "KnowledgeStore", PipelineKnowledgeStore)
    monkeypatch.setattr(dependencies, "StudyLoopExperimentRunner", isolated_runner)
    with pytest.raises(ValueError, match="Index embedding space is incompatible or UNKNOWN"):
        AppContainer(working_dir=state, use_mock=True)

    assert len(sessions) == len(knowledge) == 1
    assert sessions[0].db_path == state / "sessions.db"
    assert sessions[0].connection is not knowledge[0].connection
    assert closes == [(knowledge[0], knowledge[0].owner_thread), (sessions[0], sessions[0].owner_thread)]
    for store in [*knowledge, *sessions]:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            store.connection.execute("SELECT 1")
