"""Unit tests for S1.3 Source Registration and SourceCatalog."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import (
    SourceConflictError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.enums import SourceRole
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source
from study_engine.ingestion.catalog import SourceCatalog

HASH_A = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
HASH_B = "b1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"


def make_manifest(source_id: str, sha256: str = HASH_A, filename: str = "book.pdf") -> SourceManifest:
    return SourceManifest(
        source_id=source_id,
        filename=filename,
        byte_size=12345,
        sha256=sha256,
        media_type="application/pdf",
        metadata={"scanned": False},
    )


def test_catalog_empty_initially():
    catalog = SourceCatalog()
    assert catalog.count() == 0
    assert catalog.list_sources() == []
    assert not catalog.contains("non_existent")
    assert catalog.get_optional("non_existent") is None

    with pytest.raises(SourceNotFoundError) as exc:
        catalog.get("non_existent")
    assert exc.value.source_id == "non_existent"


def test_register_valid_source():
    catalog = SourceCatalog()
    manifest = make_manifest("joyanes-fp-4e", HASH_A, "joyanes.pdf")
    source = Source(
        source_id="joyanes-fp-4e",
        title="Fundamentos de Programación",
        author="Luis Joyanes Aguilar",
        role=SourceRole.PRIMARY,
    )

    record = catalog.register(manifest=manifest, source=source, metadata={"curator": "agustin"})

    assert isinstance(record, SourceRecord)
    assert record.source_id == "joyanes-fp-4e"
    assert record.manifest == manifest
    assert record.source == source
    assert record.metadata["curator"] == "agustin"
    assert catalog.count() == 1
    assert catalog.contains("joyanes-fp-4e")


def test_register_manifest_convenience_method():
    catalog = SourceCatalog()
    manifest = make_manifest("stallings-redes-7e", HASH_A)
    record = catalog.register_manifest(manifest=manifest)

    assert record.source_id == "stallings-redes-7e"
    assert record.source is None
    assert catalog.get("stallings-redes-7e") == record


def test_get_registered_source():
    catalog = SourceCatalog()
    manifest = make_manifest("joyanes-fp-4e")
    catalog.register(manifest)

    record = catalog.get("joyanes-fp-4e")
    assert record.source_id == "joyanes-fp-4e"
    assert record.manifest.filename == "book.pdf"


def test_exact_idempotent_registration():
    """Case A: Registering exact same source_id + identical payload is strictly idempotent."""
    catalog = SourceCatalog()
    manifest1 = make_manifest("joyanes-fp-4e", HASH_A, "joyanes.pdf")
    manifest2 = make_manifest("joyanes-fp-4e", HASH_A, "joyanes.pdf")

    record1 = catalog.register(manifest1, metadata={"tag": "v1"})
    record2 = catalog.register(manifest2, metadata={"tag": "v1"})

    assert catalog.count() == 1
    assert record1 == record2


def test_reject_divergent_metadata_on_same_hash():
    """Registering same source_id with identical hash but different metadata must reject divergence."""
    catalog = SourceCatalog()
    m1 = make_manifest("src-drift", HASH_A)
    m2 = make_manifest("src-drift", HASH_A)
    m2.metadata["new_field"] = "divergent_value"

    catalog.register(manifest=m1, metadata={"attempt": 1})

    with pytest.raises(SourceConflictError) as exc:
        catalog.register(manifest=m2, metadata={"attempt": 1})
    assert "Semantic divergence" in str(exc.value)

    with pytest.raises(SourceConflictError) as exc:
        catalog.register(manifest=m1, metadata={"attempt": 2})
    assert "Semantic divergence" in str(exc.value)


def test_reject_divergent_source_entity_on_same_hash():
    """Registering same source_id with identical hash but different Source entity must reject divergence."""
    catalog = SourceCatalog()
    m = make_manifest("src-drift-source", HASH_A)
    s1 = Source(source_id="src-drift-source", title="Title V1")
    s2 = Source(source_id="src-drift-source", title="Title V2 - Changed")

    catalog.register(manifest=m, source=s1)

    with pytest.raises(SourceConflictError) as exc:
        catalog.register(manifest=m, source=s2)
    assert "Semantic divergence" in str(exc.value)


def test_reject_divergent_manifest_filename_on_same_hash():
    """Registering same source_id with identical hash but different manifest filename must reject divergence."""
    catalog = SourceCatalog()
    m1 = make_manifest("src-diff-file", HASH_A, filename="edition_1.pdf")
    m2 = make_manifest("src-diff-file", HASH_A, filename="edition_2.pdf")

    catalog.register(m1)

    with pytest.raises(SourceConflictError) as exc:
        catalog.register(m2)
    assert "Semantic divergence" in str(exc.value)


def test_register_conflict_same_source_different_hash():
    """Case B: Registering same source_id with different sha256 must raise SourceConflictError."""
    catalog = SourceCatalog()
    manifest1 = make_manifest("joyanes-fp-4e", HASH_A)
    manifest2 = make_manifest("joyanes-fp-4e", HASH_B)

    catalog.register(manifest1)

    with pytest.raises(SourceConflictError) as exc:
        catalog.register(manifest2)

    assert exc.value.source_id == "joyanes-fp-4e"
    assert exc.value.existing_sha256 == HASH_A
    assert exc.value.new_sha256 == HASH_B

    # Verify original catalog record was NOT modified or corrupted
    assert catalog.count() == 1
    assert catalog.get("joyanes-fp-4e").manifest.sha256 == HASH_A


def test_register_coexistence_different_source_same_hash():
    """Case C: Distinct source_ids sharing identical physical sha256 can coexist."""
    catalog = SourceCatalog()
    manifest1 = make_manifest("joyanes-fp-4e", HASH_A)
    manifest2 = make_manifest("joyanes-fp-alias", HASH_A)

    record1 = catalog.register(manifest1)
    record2 = catalog.register(manifest2)

    assert catalog.count() == 2
    assert catalog.get("joyanes-fp-4e") == record1
    assert catalog.get("joyanes-fp-alias") == record2

    matching = catalog.find_by_sha256(HASH_A)
    assert len(matching) == 2
    assert [r.source_id for r in matching] == ["joyanes-fp-4e", "joyanes-fp-alias"]


def test_list_sources_deterministic_ordering():
    catalog = SourceCatalog()
    catalog.register(make_manifest("zeta-source"))
    catalog.register(make_manifest("alpha-source"))
    catalog.register(make_manifest("middle-source"))

    sources = catalog.list_sources()
    assert [s.source_id for s in sources] == ["alpha-source", "middle-source", "zeta-source"]


def test_clear_catalog():
    catalog = SourceCatalog()
    catalog.register(make_manifest("src-1"))
    catalog.register(make_manifest("src-2"))
    assert catalog.count() == 2

    catalog.clear()
    assert catalog.count() == 0
    assert not catalog.contains("src-1")


def test_defensive_copy_on_register_and_get():
    """Mutating objects passed to register or returned by get must NOT alter catalog internal state."""
    catalog = SourceCatalog()
    manifest = make_manifest("src-defensive", HASH_A)
    manifest.metadata["initial"] = True

    # 1. Mutating original manifest after register
    record = catalog.register(manifest=manifest, metadata={"catalog_meta": "orig"})
    manifest.metadata["initial"] = False
    assert catalog.get("src-defensive").manifest.metadata["initial"] is True

    # 2. Mutating retrieved record from get()
    retrieved = catalog.get("src-defensive")
    retrieved.metadata["catalog_meta"] = "hacked"
    retrieved.manifest.filename = "hacked.pdf"
    assert catalog.get("src-defensive").metadata["catalog_meta"] == "orig"
    assert catalog.get("src-defensive").manifest.filename == "book.pdf"


def test_defensive_copy_on_find_by_sha256_and_list_sources():
    """Mutating records from find_by_sha256 or list_sources must NOT alter catalog state."""
    catalog = SourceCatalog()
    catalog.register(make_manifest("src-find", HASH_A))

    found_list = catalog.find_by_sha256(HASH_A)
    found_list[0].manifest.filename = "mutated.pdf"
    assert catalog.get("src-find").manifest.filename == "book.pdf"

    listed = catalog.list_sources()
    listed[0].manifest.filename = "mutated2.pdf"
    assert catalog.get("src-find").manifest.filename == "book.pdf"


def test_from_dict_valid_empty_and_populated():
    catalog = SourceCatalog()
    m1 = make_manifest("src-1", HASH_A)
    m2 = make_manifest("src-2", HASH_B)
    catalog.register(m1)
    catalog.register(m2)

    data = catalog.to_dict()
    restored = SourceCatalog.from_dict(data)
    assert restored.count() == 2
    assert restored.get("src-1") == catalog.get("src-1")
    assert restored.get("src-2") == catalog.get("src-2")

    empty_cat = SourceCatalog.from_dict({"records": {}})
    assert empty_cat.count() == 0


@pytest.mark.parametrize("invalid_data", [None, [], "not-a-dict", 123, {}])
def test_from_dict_rejects_non_mapping_data_or_missing_records(invalid_data):
    with pytest.raises(ValueError):
        SourceCatalog.from_dict(invalid_data)


@pytest.mark.parametrize("invalid_records", [None, [], "not-a-dict", 123])
def test_from_dict_rejects_invalid_records_container(invalid_records):
    with pytest.raises(ValueError):
        SourceCatalog.from_dict({"records": invalid_records})


def test_from_dict_rejects_null_or_invalid_record_payload():
    with pytest.raises(ValueError):
        SourceCatalog.from_dict({"records": {"src-1": None}})

    with pytest.raises(ValueError):
        SourceCatalog.from_dict({"records": {"src-1": "invalid-payload"}})

    with pytest.raises(ValidationError):
        SourceCatalog.from_dict({"records": {"src-1": {}}})


def test_from_dict_rejects_outer_key_source_id_mismatch():
    valid_record_dict = SourceRecord(
        source_id="inner-id",
        manifest=make_manifest("inner-id", HASH_A),
    ).model_dump()

    with pytest.raises(ValueError) as exc:
        SourceCatalog.from_dict({"records": {"outer-key-mismatch": valid_record_dict}})
    assert "Snapshot identity mismatch" in str(exc.value)


def test_hash_casing_behavior():
    """Verify casing differences do not produce false conflicts and original hash is preserved."""
    catalog = SourceCatalog()
    hash_upper = HASH_A.upper()
    hash_lower = HASH_A.lower()

    m_upper = make_manifest("src-casing", hash_upper)
    m_lower = make_manifest("src-casing", hash_lower)

    # Register uppercase
    r1 = catalog.register(m_upper)
    assert r1.manifest.sha256 == hash_upper

    # Register lowercase with same source_id and otherwise identical manifest is idempotent
    r2 = catalog.register(m_lower)
    assert r1 == r2
    assert r2.manifest.sha256 == hash_upper  # Original uppercase preserved


def test_semantic_equivalence_helper_different_source_ids():
    from study_engine.ingestion.catalog import _is_semantically_equivalent

    r1 = SourceRecord(source_id="src-1", manifest=make_manifest("src-1"))
    r2 = SourceRecord(source_id="src-2", manifest=make_manifest("src-2"))
    assert not _is_semantically_equivalent(r1, r2)

