"""Tests verifying the relationship between Notebooks and their parent Folders (Fase 5.7)."""

from datetime import datetime, timezone
import pytest

from study_engine.contracts.catalog import NotebookConflictError
from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.storage.knowledge_store import FolderNotFoundError, KnowledgeStore


@pytest.fixture
def store() -> KnowledgeStore:
    ks = KnowledgeStore(":memory:")
    ks.initialize()
    return ks


def test_notebook_assigned_to_specific_folder(store: KnowledgeStore):
    """Notebook correctly persists and exposes its parent folder_id."""
    now = datetime.now(timezone.utc)
    folder = Folder(
        id="f_seguridad",
        name="Seguridad Ofensiva",
        parent_folder_id="folder_root",
        created_at=now,
        updated_at=now,
    )
    store.create_folder(folder)

    nb = Notebook(
        id="nb_exploits",
        name="Exploits & Buffer Overflows",
        folder_id="f_seguridad",
        description="Laboratorio práctico",
    )
    created_nb = store.create_notebook(nb)

    assert created_nb.id == "nb_exploits"
    assert created_nb.folder_id == "f_seguridad"

    # Query back from store
    fetched = store.get_notebook("nb_exploits")
    assert fetched.folder_id == "f_seguridad"


def test_list_notebooks_in_folder(store: KnowledgeStore):
    """list_notebooks_in_folder isolates notebooks strictly by folder."""
    now = datetime.now(timezone.utc)
    f_c = store.create_folder(Folder(id="f_c", name="Lenguaje C", parent_folder_id="folder_root", created_at=now, updated_at=now))
    f_py = store.create_folder(Folder(id="f_py", name="Python", parent_folder_id="folder_root", created_at=now, updated_at=now))

    store.create_notebook(Notebook(id="nb_c_pointers", name="Punteros en C", folder_id="f_c"))
    store.create_notebook(Notebook(id="nb_c_memory", name="Memoria en C", folder_id="f_c"))
    store.create_notebook(Notebook(id="nb_py_basics", name="Basics Python", folder_id="f_py"))

    c_notebooks = store.list_notebooks_in_folder("f_c")
    py_notebooks = store.list_notebooks_in_folder("f_py")

    assert len(c_notebooks) == 2
    assert {nb.id for nb in c_notebooks} == {"nb_c_pointers", "nb_c_memory"}

    assert len(py_notebooks) == 1
    assert py_notebooks[0].id == "nb_py_basics"


def test_notebook_unique_name_per_folder(store: KnowledgeStore):
    """Notebook name must be unique within the same folder_id."""
    now = datetime.now(timezone.utc)
    store.create_folder(Folder(id="f_math", name="Matemáticas", parent_folder_id="folder_root", created_at=now, updated_at=now))
    store.create_folder(Folder(id="f_phys", name="Física", parent_folder_id="folder_root", created_at=now, updated_at=now))

    # Create first notebook in f_math
    store.create_notebook(Notebook(id="nb_intro_m", name="Introducción", folder_id="f_math"))

    # Attempt to create second notebook with SAME name in SAME folder -> Conflict
    with pytest.raises(NotebookConflictError, match="already exists in folder"):
        store.create_notebook(Notebook(id="nb_intro_m_dup", name="Introducción", folder_id="f_math"))

    # Create notebook with SAME name in DIFFERENT folder -> Allowed
    nb_phys = store.create_notebook(Notebook(id="nb_intro_p", name="Introducción", folder_id="f_phys"))
    assert nb_phys.name == "Introducción"
    assert nb_phys.folder_id == "f_phys"


def test_notebook_in_nonexistent_folder_fails_closed(store: KnowledgeStore):
    """Creating a notebook in a nonexistent folder raises FolderNotFoundError."""
    with pytest.raises(FolderNotFoundError, match="f_phantom"):
        store.create_notebook(Notebook(id="nb_lost", name="Perdido", folder_id="f_phantom"))


def test_deleting_folder_reparents_notebooks_to_root(store: KnowledgeStore):
    """Deleting a non-root folder re-parents its notebooks to 'folder_root' safely."""
    now = datetime.now(timezone.utc)
    store.create_folder(Folder(id="f_archived", name="Archivados", parent_folder_id="folder_root", created_at=now, updated_at=now))
    store.create_notebook(Notebook(id="nb_saved", name="Notas Guardadas", folder_id="f_archived"))

    assert store.get_notebook("nb_saved").folder_id == "f_archived"

    # Delete folder
    store.delete_folder("f_archived")

    # Notebook survived and is now in folder_root
    reparented = store.get_notebook("nb_saved")
    assert reparented.folder_id == "folder_root"
