"""Notebook identity checks for source uploads."""

import asyncio
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator, cast

import pytest
from fastapi import HTTPException, UploadFile

from study_engine.federation.notebook_registry import DEFAULT_NOTEBOOKS
from study_engine.contracts.notebook import Notebook as StoredNotebook
from study_engine.web.dependencies import (
    AppContainer,
    _load_notebook_curriculum_ids,
)
from study_engine.web.routes.notebook import (
    sync_sources_folder_to_notebook,
    upload_source_to_notebook,
)


class _UnregisteredNotebookStore:
    def __init__(self) -> None:
        self.checked_notebooks: list[str] = []

    def contains_notebook(self, notebook_id: str) -> bool:
        self.checked_notebooks.append(notebook_id)
        return False


class _Container:
    def __init__(self) -> None:
        self.knowledge_store = _UnregisteredNotebookStore()


class _Cursor:
    def execute(self, _query: str) -> None:
        pass

    def fetchall(self) -> list[tuple[str, ...]]:
        return []


class _Connection:
    def cursor(self) -> _Cursor:
        return _Cursor()


class _Engine:
    @contextmanager
    def transaction(self) -> Iterator[_Connection]:
        yield _Connection()


class _ProvisioningStore:
    def __init__(self) -> None:
        self.engine = _Engine()
        self.created_notebooks: list[StoredNotebook] = []

    def contains_folder(self, _folder_id: str) -> bool:
        return True

    def contains_notebook(self, _notebook_id: str) -> bool:
        return False

    def create_notebook(self, notebook: StoredNotebook) -> None:
        self.created_notebooks.append(notebook)


def test_source_upload_rejects_unregistered_notebook_before_side_effects() -> None:
    container = _Container()
    upload = UploadFile(filename="curriculum.pdf", file=BytesIO(b"not read"))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_source_to_notebook(
                notebook_id="not-onboarded",
                file=upload,
                container=cast(AppContainer, container),
            )
        )

    assert exc_info.value.status_code == 404
    assert "Register the notebook before uploading sources" in exc_info.value.detail
    assert container.knowledge_store.checked_notebooks == ["not-onboarded"]


def test_source_sync_rejects_unregistered_notebook_before_side_effects() -> None:
    container = _Container()

    with pytest.raises(HTTPException) as exc_info:
        sync_sources_folder_to_notebook(
            notebook_id="not-onboarded",
            container=cast(AppContainer, container),
        )

    assert exc_info.value.status_code == 404
    assert "Register the notebook before syncing sources" in exc_info.value.detail
    assert container.knowledge_store.checked_notebooks == ["not-onboarded"]


def test_curriculum_ids_are_loaded_only_from_exact_catalog_entries() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    curriculum_ids = _load_notebook_curriculum_ids(
        repo_root / "config" / "notebook_kc_catalog.json"
    )

    assert curriculum_ids["fase0-soc"] == "roadmap_kasiu_v4_fase0"
    assert curriculum_ids["fadena-lenguajes"] == "fadena_lenguajes_2026"
    assert curriculum_ids["fadena-so2"] == "fadena_so2_2026"
    assert curriculum_ids["fadena-std"] == "fadena_std_2026"
    assert curriculum_ids["fadena-teleco"] == "fadena_teleco_2025"
    assert curriculum_ids["fadena-sye"] == "fadena_sye_2026"
    assert "fadena-prog" not in curriculum_ids
    assert "fadena-so" not in curriculum_ids


def test_default_notebook_provisioning_uses_exact_curriculum_ids() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    container = AppContainer.__new__(AppContainer)
    container.repo_root = repo_root
    store = _ProvisioningStore()

    container._seed_curriculum_tree(
        store,
        SimpleNamespace(list_notebooks=lambda: DEFAULT_NOTEBOOKS),
    )

    provisioned = {notebook.id: notebook for notebook in store.created_notebooks}
    assert provisioned["fase0-soc"].curriculum_id == "roadmap_kasiu_v4_fase0"
    assert provisioned["fadena-lenguajes"].curriculum_id == "fadena_lenguajes_2026"
    assert provisioned["fadena-so2"].curriculum_id == "fadena_so2_2026"
    assert provisioned["fadena-std"].curriculum_id == "fadena_std_2026"
    assert provisioned["fadena-teleco"].curriculum_id == "fadena_teleco_2025"
    assert provisioned["fadena-prog"].curriculum_id is None
    assert provisioned["fadena-so"].curriculum_id is None
