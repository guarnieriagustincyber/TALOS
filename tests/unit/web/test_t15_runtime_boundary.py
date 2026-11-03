"""Focused synthetic tests for T15 runtime-boundary controls.

These tests do not construct AppContainer, enter FastAPI lifespan, or access
benchmark data, databases, providers, or network resources.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.experiments.run_study_loop_v1 import _should_ingest_benchmark_corpus
from study_engine.web.app import _schedule_retrieval_warmup, create_app
from study_engine.web.dependencies import (
    AppContainer,
    _resolve_synthetic_working_dir,
)


def test_create_app_uses_explicit_static_roots_without_creating_them(
    tmp_path: Path,
) -> None:
    static_dir = tmp_path / "not-created-static"
    storage_dir = tmp_path / "not-created-storage"

    app = create_app(
        static_dir=static_dir,
        storage_dir=storage_dir,
        enable_retrieval_warmup=False,
    )

    assert app.state.static_dir == static_dir.resolve()
    assert app.state.storage_dir == storage_dir.resolve()
    assert not static_dir.exists()
    assert not storage_dir.exists()

    mounts = {route.name: route.app for route in app.routes if route.name in {"static", "storage"}}
    assert mounts["static"].directory == str(static_dir.resolve())
    assert mounts["storage"].directory == str(storage_dir.resolve())


def test_disabled_warmup_does_not_create_a_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import threading

    def forbidden_thread(*args, **kwargs):
        pytest.fail("disabled synthetic profile must not schedule a warmup thread")

    monkeypatch.setattr(threading, "Thread", forbidden_thread)
    _schedule_retrieval_warmup(SimpleNamespace(), enabled=False)


def test_mock_dotenv_loader_returns_before_filesystem_access(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("TALOS_T15_SYNTHETIC_SENTINEL=must-not-load\n", encoding="utf-8")
    container = AppContainer.__new__(AppContainer)
    container.use_mock = True
    container.repo_root = tmp_path

    original_exists = Path.exists

    def fail_if_env_checked(path: Path) -> bool:
        if path == env_path:
            pytest.fail("synthetic AppContainer must not inspect .env")
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", fail_if_env_checked)
    monkeypatch.delenv("TALOS_T15_SYNTHETIC_SENTINEL", raising=False)
    container._load_dotenv()
    assert "TALOS_T15_SYNTHETIC_SENTINEL" not in __import__("os").environ


def test_synthetic_working_dir_rejects_repository_and_symlink_paths(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "synthetic-state"

    assert _resolve_synthetic_working_dir(outside, repo_root) == outside.resolve()
    with pytest.raises(ValueError, match="inside the repository"):
        _resolve_synthetic_working_dir(repo_root / "state", repo_root)

    alias = tmp_path / "state-alias"
    try:
        alias.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("filesystem does not support creating symlinks")
    with pytest.raises(ValueError, match="symlinks"):
        _resolve_synthetic_working_dir(alias, repo_root)


def test_mock_container_uses_durable_synthetic_student_and_exercise_paths(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    synthetic_root = tmp_path / "synthetic-state"
    container = AppContainer(
        repo_root=repo_root,
        working_dir=synthetic_root,
        use_mock=True,
        load_dotenv=False,
    )

    assert container.student_storage.db_path == synthetic_root / "student_state.db"
    assert container.exercise_store.storage_path == synthetic_root / "exercises.json"
    assert container.session_store.db_path == synthetic_root / "sessions.db"
    assert container.knowledge_store.engine.db_path == synthetic_root / "knowledge_store.db"
    assert Path(container.context["vstore"].db_path) == synthetic_root / "vector_store.db"
    assert not container.exercise_store.storage_path.exists()
    assert all(
        path.resolve().is_relative_to(synthetic_root.resolve())
        for path in (
            container.student_storage.db_path,
            container.exercise_store.storage_path,
            container.session_store.db_path,
            container.knowledge_store.engine.db_path,
            Path(container.context["vstore"].db_path),
        )
    )
    container.student_storage.close()


@pytest.mark.parametrize(
    ("allowed", "source_count", "expected"),
    [(False, 0, False), (True, 0, True), (True, 2, False)],
)
def test_benchmark_ingestion_requires_explicit_permission_and_empty_store(
    allowed: bool,
    source_count: int,
    expected: bool,
) -> None:
    assert _should_ingest_benchmark_corpus(
        allowed=allowed,
        source_count=source_count,
    ) is expected
