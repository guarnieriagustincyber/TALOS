"""Tests for Folder model and KnowledgeStore Folder CRUD operations (Fase 5.7)."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.hierarchy.folder import Folder
from study_engine.storage.knowledge_store import (
    FolderConflictError,
    FolderNotFoundError,
    KnowledgeStore,
)


@pytest.fixture
def store() -> KnowledgeStore:
    ks = KnowledgeStore(":memory:")
    ks.initialize()
    return ks


def test_folder_model_immutability_and_validation():
    """Folder model is strictly frozen and rejects invalid attributes."""
    now = datetime.now(timezone.utc)
    folder = Folder(
        id="f_cs",
        name="Ciencias de la Computación",
        parent_folder_id="folder_root",
        description="Carrera de grado",
        created_at=now,
        updated_at=now,
    )
    assert folder.id == "f_cs"
    assert folder.name == "Ciencias de la Computación"
    assert folder.parent_folder_id == "folder_root"

    # Frozen immutability
    with pytest.raises(ValidationError):
        folder.name = "Otro nombre"  # type: ignore

    # Rejection of empty id or name
    with pytest.raises(ValidationError):
        Folder(
            id="",
            name="Valido",
            created_at=now,
            updated_at=now,
        )

    with pytest.raises(ValidationError):
        Folder(
            id="f_valid",
            name="   ",
            created_at=now,
            updated_at=now,
        )


def test_folder_self_reference_prevention():
    """Folder cannot be its own parent."""
    now = datetime.now(timezone.utc)
    folder = Folder(
        id="f_loop",
        name="Bucle",
        parent_folder_id="f_loop",
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(ValueError, match="cannot be its own parent"):
        folder.validate_not_self_referencing()


def test_folder_crud_in_knowledge_store(store: KnowledgeStore):
    """KnowledgeStore creates, retrieves, and lists folders."""
    now = datetime.now(timezone.utc)
    f1 = Folder(
        id="f_fadena",
        name="FADENA Ciberseguridad",
        parent_folder_id="folder_root",
        description="Plan de estudios de ciberseguridad",
        created_at=now,
        updated_at=now,
    )
    created = store.create_folder(f1)
    assert created.id == "f_fadena"
    assert store.contains_folder("f_fadena") is True

    # Retrieve
    retrieved = store.get_folder("f_fadena")
    assert retrieved.id == "f_fadena"
    assert retrieved.name == "FADENA Ciberseguridad"
    assert retrieved.parent_folder_id == "folder_root"

    # List
    folders = store.list_folders()
    ids = [f.id for f in folders]
    assert "folder_root" in ids
    assert "f_fadena" in ids


def test_nested_folders_hierarchy(store: KnowledgeStore):
    """Folders can be arbitrarily nested (Root -> Year 1 -> Semester 1)."""
    now = datetime.now(timezone.utc)

    # Year 1 under folder_root
    f_y1 = Folder(
        id="f_year_1",
        name="1er Año",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(f_y1)

    # Semester 1 under Year 1
    f_s1 = Folder(
        id="f_sem_1",
        name="1er Cuatrimestre",
        parent_folder_id="f_year_1",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(f_s1)

    # Subject under Semester 1
    f_so = Folder(
        id="f_so",
        name="Sistemas Operativos",
        parent_folder_id="f_sem_1",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(f_so)

    # List children of Year 1
    y1_children = store.list_folders(parent_folder_id="f_year_1")
    assert len(y1_children) == 1
    assert y1_children[0].id == "f_sem_1"

    # List children of Semester 1
    s1_children = store.list_folders(parent_folder_id="f_sem_1")
    assert len(s1_children) == 1
    assert s1_children[0].id == "f_so"


def test_folder_unique_name_per_parent(store: KnowledgeStore):
    """Enforce UNIQUE(name, parent_folder_id) constraint within same parent."""
    now = datetime.now(timezone.utc)
    f1 = Folder(
        id="f_prog_a",
        name="Programación",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(f1)

    # Duplicate name in same parent -> FolderConflictError
    f2 = Folder(
        id="f_prog_b",
        name="Programación",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(FolderConflictError, match="already exists"):
        store.create_folder(f2)

    # Same name in DIFFERENT parent -> Allowed
    f_other_parent = Folder(
        id="f_special",
        name="Especialización",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(f_other_parent)

    f3 = Folder(
        id="f_prog_diff_parent",
        name="Programación",
        parent_folder_id="f_special",
        created_at=now,
        updated_at=now,
    )
    created_f3 = store.create_folder(f3)
    assert created_f3.id == "f_prog_diff_parent"


def test_delete_folder_protection_and_cleanup(store: KnowledgeStore):
    """Default 'folder_root' cannot be deleted; other folders can be deleted."""
    with pytest.raises(ValueError, match="Cannot delete the default root folder"):
        store.delete_folder("folder_root")

    now = datetime.now(timezone.utc)
    f_temp = Folder(
        id="f_temp",
        name="Carpeta Temporal",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(f_temp)
    assert store.contains_folder("f_temp") is True

    deleted = store.delete_folder("f_temp")
    assert deleted is True
    assert store.contains_folder("f_temp") is False

    with pytest.raises(FolderNotFoundError):
        store.get_folder("f_temp")
