"""Tests for deterministic ScopeResolver (Fase 5.7)."""

from datetime import datetime, timezone
import pytest

from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.hierarchy.scope_resolver import (
    ResolvedScope,
    ScopeNotFoundError,
    ScopeResolver,
    ScopeType,
)
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def store() -> KnowledgeStore:
    ks = KnowledgeStore(":memory:")
    ks.initialize()
    now = datetime.now(timezone.utc)
    ks.create_folder(
        Folder(
            id="f_sistemas",
            name="Sistemas",
            parent_folder_id="folder_root",
            created_at=now,
            updated_at=now,
        )
    )
    ks.create_notebook(
        Notebook(
            id="nb_so_kernel",
            name="Kernel Linux",
            folder_id="f_sistemas",
        )
    )
    return ks


def test_scope_resolver_folder_scope(store: KnowledgeStore):
    """Resolving a FOLDER scope produces ResolvedScope with folder_id and no notebook_id."""
    resolver = ScopeResolver(store)
    scope = resolver.resolve(ScopeType.FOLDER, "f_sistemas")

    assert isinstance(scope, ResolvedScope)
    assert scope.scope_type == ScopeType.FOLDER
    assert scope.scope_id == "f_sistemas"
    assert scope.folder_id == "f_sistemas"
    assert scope.notebook_id is None


def test_scope_resolver_notebook_scope(store: KnowledgeStore):
    """Resolving a NOTEBOOK scope produces ResolvedScope with both notebook_id and parent folder_id."""
    resolver = ScopeResolver(store)
    scope = resolver.resolve(ScopeType.NOTEBOOK, "nb_so_kernel")

    assert isinstance(scope, ResolvedScope)
    assert scope.scope_type == ScopeType.NOTEBOOK
    assert scope.scope_id == "nb_so_kernel"
    assert scope.notebook_id == "nb_so_kernel"
    assert scope.folder_id == "f_sistemas"


def test_scope_resolver_root_folder(store: KnowledgeStore):
    """Resolving the default 'folder_root' works out of the box."""
    resolver = ScopeResolver(store)
    scope = resolver.resolve(ScopeType.FOLDER, "folder_root")

    assert scope.scope_type == ScopeType.FOLDER
    assert scope.scope_id == "folder_root"
    assert scope.folder_id == "folder_root"


def test_scope_resolver_nonexistent_folder_fails_closed(store: KnowledgeStore):
    """Resolving nonexistent folder raises ScopeNotFoundError."""
    resolver = ScopeResolver(store)
    with pytest.raises(ScopeNotFoundError) as exc_info:
        resolver.resolve(ScopeType.FOLDER, "f_ghost")

    assert exc_info.value.scope_type == ScopeType.FOLDER
    assert exc_info.value.scope_id == "f_ghost"


def test_scope_resolver_nonexistent_notebook_fails_closed(store: KnowledgeStore):
    """Resolving nonexistent notebook raises ScopeNotFoundError."""
    resolver = ScopeResolver(store)
    with pytest.raises(ScopeNotFoundError) as exc_info:
        resolver.resolve(ScopeType.NOTEBOOK, "nb_ghost")

    assert exc_info.value.scope_type == ScopeType.NOTEBOOK
    assert exc_info.value.scope_id == "nb_ghost"


def test_scope_resolver_empty_id_fails_closed(store: KnowledgeStore):
    """Empty or whitespace scope_id raises ScopeNotFoundError."""
    resolver = ScopeResolver(store)
    with pytest.raises(ScopeNotFoundError):
        resolver.resolve(ScopeType.FOLDER, "  ")


def test_scope_resolver_access_validation(store: KnowledgeStore):
    """validate_scope_access correctly approves authenticated requests and blocks empty users."""
    resolver = ScopeResolver(store)
    scope = resolver.resolve(ScopeType.FOLDER, "f_sistemas")

    assert resolver.validate_scope_access("student_42", scope) is True
    assert resolver.validate_scope_access("", scope) is False
    assert resolver.validate_scope_access("   ", scope) is False
