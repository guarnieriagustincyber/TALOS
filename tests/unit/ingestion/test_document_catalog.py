"""Unit tests for S1.4 Document Registration and DocumentCatalog."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import (
    DocumentConflictError,
    DocumentNotFoundError,
    SourceNotFoundError,
)
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.ingestion.catalog import SourceCatalog
from study_engine.ingestion.document_catalog import DocumentCatalog

HASH_A = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"


def make_document(
    doc_id: str = "doc-001",
    source_id: str = "joyanes-fp-4e",
    title: str = "Capítulo 1: Introducción",
    content: str = "Texto del capítulo 1...",
    path: str = "Fase-0/Joyanes/ch01.pdf",
    page_count: int = 35,
    language: str = "es",
    metadata: dict = None,
    created_at: datetime = None,
) -> Document:
    return Document(
        id=doc_id,
        source_id=source_id,
        title=title,
        content=content,
        path=path,
        page_count=page_count,
        language=language,
        metadata=metadata if metadata is not None else {"scanned": False},
        created_at=created_at,
    )


def make_source_catalog_with(source_id: str) -> SourceCatalog:
    catalog = SourceCatalog()
    manifest = SourceManifest(
        source_id=source_id,
        filename="source.pdf",
        byte_size=1000,
        sha256=HASH_A,
    )
    catalog.register(manifest)
    return catalog


def test_document_catalog_empty_initially():
    catalog = DocumentCatalog()
    assert catalog.count() == 0
    assert catalog.list_documents() == []
    assert not catalog.contains("non_existent")
    assert catalog.get_optional("non_existent") is None

    with pytest.raises(DocumentNotFoundError) as exc:
        catalog.get("non_existent")
    assert exc.value.document_id == "non_existent"


def test_register_valid_document_standalone():
    catalog = DocumentCatalog()
    doc = make_document("doc-1", "src-1", "Capítulo 1")
    registered = catalog.register(doc)

    assert isinstance(registered, Document)
    assert registered.id == "doc-1"
    assert registered.source_id == "src-1"
    assert registered.title == "Capítulo 1"
    assert catalog.count() == 1
    assert catalog.contains("doc-1")
    assert catalog.get("doc-1") == doc


def test_register_with_source_catalog_success():
    source_catalog = make_source_catalog_with("joyanes-fp-4e")
    doc_catalog = DocumentCatalog(source_catalog=source_catalog)

    doc = make_document("doc-joy-1", "joyanes-fp-4e", "Capítulo 1")
    registered = doc_catalog.register(doc)

    assert registered.id == "doc-joy-1"
    assert doc_catalog.count() == 1
    assert doc_catalog.contains("doc-joy-1")


def test_register_with_source_catalog_missing_source_fails():
    source_catalog = make_source_catalog_with("joyanes-fp-4e")
    doc_catalog = DocumentCatalog(source_catalog=source_catalog)

    doc = make_document("doc-missing", "stallings-redes-7e", "Capítulo 1")
    with pytest.raises(SourceNotFoundError) as exc:
        doc_catalog.register(doc)

    assert exc.value.source_id == "stallings-redes-7e"
    assert doc_catalog.count() == 0
    assert not doc_catalog.contains("doc-missing")


def test_register_invalid_document_type():
    catalog = DocumentCatalog()
    with pytest.raises(ValueError) as exc:
        catalog.register({"id": "doc-1", "source_id": "src-1", "title": "Title"})
    assert "must be an instance of Document" in str(exc.value)


def test_get_registered_document():
    catalog = DocumentCatalog()
    doc = make_document("doc-get", "src-1", "Title")
    catalog.register(doc)

    retrieved = catalog.get("doc-get")
    assert retrieved == doc


def test_get_optional_document():
    catalog = DocumentCatalog()
    doc = make_document("doc-opt", "src-1", "Title")
    catalog.register(doc)

    assert catalog.get_optional("doc-opt") == doc
    assert catalog.get_optional("non-existent") is None


def test_exact_idempotent_registration():
    """Registering an identical Document is strictly idempotent."""
    catalog = DocumentCatalog()
    doc1 = make_document("doc-idemp", "src-1", "Title", metadata={"v": 1})
    doc2 = make_document("doc-idemp", "src-1", "Title", metadata={"v": 1})

    r1 = catalog.register(doc1)
    r2 = catalog.register(doc2)

    assert catalog.count() == 1
    assert r1 == r2


@pytest.mark.parametrize(
    "modified_kwargs",
    [
        {"title": "Divergent Title"},
        {"source_id": "different-source"},
        {"content": "Divergent content"},
        {"path": "different/path.pdf"},
        {"page_count": 999},
        {"language": "en"},
        {"metadata": {"divergent": True}},
        {"created_at": datetime.now(timezone.utc)},
    ],
)
def test_register_conflict_divergent_attributes(modified_kwargs):
    catalog = DocumentCatalog()
    base_doc = make_document("doc-diverge", "src-1", "Original Title")
    catalog.register(base_doc)

    # Construct divergent document
    divergent_kwargs = {
        "doc_id": "doc-diverge",
        "source_id": "src-1",
        "title": "Original Title",
        "content": "Texto del capítulo 1...",
        "path": "Fase-0/Joyanes/ch01.pdf",
        "page_count": 35,
        "language": "es",
        "metadata": {"scanned": False},
        "created_at": None,
    }
    for k, v in modified_kwargs.items():
        if k == "source_id":
            divergent_kwargs["source_id"] = v
        elif k == "title":
            divergent_kwargs["title"] = v
        elif k == "content":
            divergent_kwargs["content"] = v
        elif k == "path":
            divergent_kwargs["path"] = v
        elif k == "page_count":
            divergent_kwargs["page_count"] = v
        elif k == "language":
            divergent_kwargs["language"] = v
        elif k == "metadata":
            divergent_kwargs["metadata"] = v
        elif k == "created_at":
            divergent_kwargs["created_at"] = v

    divergent_doc = Document(
        id=divergent_kwargs["doc_id"],
        source_id=divergent_kwargs["source_id"],
        title=divergent_kwargs["title"],
        content=divergent_kwargs["content"],
        path=divergent_kwargs["path"],
        page_count=divergent_kwargs["page_count"],
        language=divergent_kwargs["language"],
        metadata=divergent_kwargs["metadata"],
        created_at=divergent_kwargs["created_at"],
    )

    with pytest.raises(DocumentConflictError) as exc:
        catalog.register(divergent_doc)
    assert exc.value.document_id == "doc-diverge"
    assert "Semantic divergence" in str(exc.value)

    # Verify original document was not modified
    assert catalog.count() == 1
    assert catalog.get("doc-diverge") == base_doc


def test_find_by_source_id_deterministic_ordering():
    catalog = DocumentCatalog()
    catalog.register(make_document("doc-z", "source-A", "Zeta"))
    catalog.register(make_document("doc-a", "source-A", "Alpha"))
    catalog.register(make_document("doc-b", "source-B", "Beta"))
    catalog.register(make_document("doc-m", "source-A", "Middle"))

    matching = catalog.find_by_source_id("source-A")
    assert len(matching) == 3
    assert [d.id for d in matching] == ["doc-a", "doc-m", "doc-z"]


def test_list_documents_deterministic_ordering():
    catalog = DocumentCatalog()
    catalog.register(make_document("zeta-doc", "src-1"))
    catalog.register(make_document("alpha-doc", "src-1"))
    catalog.register(make_document("middle-doc", "src-1"))

    docs = catalog.list_documents()
    assert [d.id for d in docs] == ["alpha-doc", "middle-doc", "zeta-doc"]


def test_clear_catalog():
    catalog = DocumentCatalog()
    catalog.register(make_document("doc-1", "src-1"))
    catalog.register(make_document("doc-2", "src-1"))
    assert catalog.count() == 2

    catalog.clear()
    assert catalog.count() == 0
    assert not catalog.contains("doc-1")


def test_defensive_copying_on_register_and_get():
    catalog = DocumentCatalog()
    doc = make_document("doc-def", "src-1", metadata={"key": "orig"})

    # 1. Mutate original doc after register
    catalog.register(doc)
    doc.metadata["key"] = "mutated-externally"
    doc.title = "Mutated Title"
    assert catalog.get("doc-def").metadata["key"] == "orig"
    assert catalog.get("doc-def").title != "Mutated Title"

    # 2. Mutate retrieved doc from get()
    retrieved = catalog.get("doc-def")
    retrieved.metadata["key"] = "hacked"
    retrieved.title = "Hacked Title"
    assert catalog.get("doc-def").metadata["key"] == "orig"
    assert catalog.get("doc-def").title != "Hacked Title"


def test_defensive_copying_on_find_and_list():
    catalog = DocumentCatalog()
    catalog.register(make_document("doc-find", "src-1", metadata={"tag": "orig"}))

    found = catalog.find_by_source_id("src-1")
    found[0].metadata["tag"] = "mutated"
    assert catalog.get("doc-find").metadata["tag"] == "orig"

    listed = catalog.list_documents()
    listed[0].metadata["tag"] = "mutated2"
    assert catalog.get("doc-find").metadata["tag"] == "orig"


def test_to_dict_and_from_dict_roundtrip():
    catalog = DocumentCatalog()
    doc1 = make_document("doc-1", "src-1", "Title 1")
    doc2 = make_document("doc-2", "src-2", "Title 2")
    catalog.register(doc1)
    catalog.register(doc2)

    data = catalog.to_dict()
    assert "records" in data
    assert "doc-1" in data["records"]
    assert "doc-2" in data["records"]

    restored = DocumentCatalog.from_dict(data)
    assert restored.count() == 2
    assert restored.get("doc-1") == doc1
    assert restored.get("doc-2") == doc2


def test_from_dict_with_source_catalog_referential_integrity():
    source_cat = make_source_catalog_with("src-valid")
    doc = make_document("doc-1", "src-valid", "Title 1")
    standalone_cat = DocumentCatalog()
    standalone_cat.register(doc)
    snapshot = standalone_cat.to_dict()

    # Valid when source exists
    restored = DocumentCatalog.from_dict(snapshot, source_catalog=source_cat)
    assert restored.count() == 1

    # Fails when source does not exist
    empty_source_cat = SourceCatalog()
    with pytest.raises(SourceNotFoundError) as exc:
        DocumentCatalog.from_dict(snapshot, source_catalog=empty_source_cat)
    assert exc.value.source_id == "src-valid"


@pytest.mark.parametrize("invalid_data", [None, [], "not-a-dict", 123, {}])
def test_from_dict_rejects_non_mapping_data_or_missing_records(invalid_data):
    with pytest.raises(ValueError):
        DocumentCatalog.from_dict(invalid_data)


@pytest.mark.parametrize("invalid_records", [None, [], "not-a-dict", 123])
def test_from_dict_rejects_invalid_records_container(invalid_records):
    with pytest.raises(ValueError):
        DocumentCatalog.from_dict({"records": invalid_records})


def test_from_dict_rejects_null_or_invalid_record_payload():
    with pytest.raises(ValueError):
        DocumentCatalog.from_dict({"records": {"doc-1": None}})

    with pytest.raises(ValueError):
        DocumentCatalog.from_dict({"records": {"doc-1": "string-payload"}})

    with pytest.raises(ValidationError):
        DocumentCatalog.from_dict({"records": {"doc-1": {}}})


def test_from_dict_rejects_outer_key_document_id_mismatch():
    valid_doc_dict = make_document("inner-id", "src-1").model_dump()
    with pytest.raises(ValueError) as exc:
        DocumentCatalog.from_dict({"records": {"outer-mismatch": valid_doc_dict}})
    assert "Snapshot identity mismatch" in str(exc.value)
