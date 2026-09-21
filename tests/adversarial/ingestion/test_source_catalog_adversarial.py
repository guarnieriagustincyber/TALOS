"""Adversarial tests for SourceCatalog and SourceRecord."""

import json
import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import (
    SourceConflictError,
    SourceRecord,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.ingestion.catalog import SourceCatalog

VALID_HASH = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
ANOTHER_HASH = "fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321"


def test_source_record_rejects_empty_or_null_source_id():
    manifest = SourceManifest(
        source_id="valid-id",
        filename="f.pdf",
        byte_size=10,
        sha256=VALID_HASH,
    )
    with pytest.raises(ValidationError):
        SourceRecord(source_id="", manifest=manifest)

    with pytest.raises(ValidationError):
        SourceRecord(source_id=None, manifest=manifest)


def test_source_record_handles_complex_unicode_and_emojis():
    unicode_id = "📚-algoritmos_joyanes_capítulo-01_#1_🔥"
    manifest = SourceManifest(
        source_id=unicode_id,
        filename="joyanes.pdf",
        byte_size=1024,
        sha256=VALID_HASH,
    )
    record = SourceRecord(source_id=unicode_id, manifest=manifest)
    assert record.source_id == unicode_id

    catalog = SourceCatalog()
    catalog.register(manifest)
    assert catalog.get(unicode_id) == record


def test_source_catalog_stress_idempotency():
    catalog = SourceCatalog()
    manifest = SourceManifest(
        source_id="stress-src",
        filename="file.pdf",
        byte_size=5000,
        sha256=VALID_HASH,
    )

    first_record = catalog.register(manifest)
    for _ in range(100):
        res = catalog.register(manifest)
        assert res == first_record

    assert catalog.count() == 1


def test_source_catalog_state_preserved_after_failed_conflict():
    catalog = SourceCatalog()
    initial_manifest = SourceManifest(
        source_id="stable-src",
        filename="stable.pdf",
        byte_size=100,
        sha256=VALID_HASH,
    )
    catalog.register(initial_manifest)

    conflicting_manifest = SourceManifest(
        source_id="stable-src",
        filename="attacker.pdf",
        byte_size=999,
        sha256=ANOTHER_HASH,
    )

    for _ in range(10):
        with pytest.raises(SourceConflictError):
            catalog.register(conflicting_manifest)

    assert catalog.count() == 1
    assert catalog.get("stable-src").manifest.sha256 == VALID_HASH
    assert catalog.get("stable-src").manifest.filename == "stable.pdf"


def test_source_catalog_find_by_sha256_case_insensitive():
    catalog = SourceCatalog()
    manifest_lower = SourceManifest(
        source_id="src-lower",
        filename="f1.pdf",
        byte_size=10,
        sha256=VALID_HASH.lower(),
    )
    manifest_upper = SourceManifest(
        source_id="src-upper",
        filename="f2.pdf",
        byte_size=10,
        sha256=VALID_HASH.upper(),
    )

    catalog.register(manifest_lower)
    catalog.register(manifest_upper)

    results = catalog.find_by_sha256(VALID_HASH)
    assert len(results) == 2
    assert [r.source_id for r in results] == ["src-lower", "src-upper"]


def test_source_record_metadata_key_shadowing():
    manifest = SourceManifest(
        source_id="src-meta",
        filename="f.pdf",
        byte_size=100,
        sha256=VALID_HASH,
    )
    record = SourceRecord(
        source_id="src-meta",
        manifest=manifest,
        metadata={"source_id": "inner_id", "manifest": "inner_manifest"},
    )
    assert record.source_id == "src-meta"
    assert record.metadata["source_id"] == "inner_id"


@pytest.mark.parametrize(
    "corrupted_snapshot",
    [
        {"records": {"key": None}},
        {"records": {"key": "string-payload"}},
        {"records": {"key": 12345}},
        {"records": {"key": []}},
        {"records": {"": {"source_id": "src", "manifest": {"source_id": "src", "filename": "f", "byte_size": 1, "sha256": VALID_HASH}}}},
        {"records": {"outer": {"source_id": "different-inner", "manifest": {"source_id": "different-inner", "filename": "f", "byte_size": 1, "sha256": VALID_HASH}}}},
    ],
)
def test_adversarial_snapshot_corruption_rejected(corrupted_snapshot):
    with pytest.raises((ValueError, ValidationError)):
        SourceCatalog.from_dict(corrupted_snapshot)


def test_adversarial_divergence_attack_on_registered_source():
    """Attempting to subtly alter metadata or attributes on same hash is rejected as a conflict."""
    catalog = SourceCatalog()
    manifest = SourceManifest(
        source_id="critical-source",
        filename="doc.pdf",
        byte_size=1000,
        sha256=VALID_HASH,
        metadata={"security_level": "HIGH"},
    )
    catalog.register(manifest)

    # Attacker tries to register same source with modified metadata
    tampered_manifest = SourceManifest(
        source_id="critical-source",
        filename="doc.pdf",
        byte_size=1000,
        sha256=VALID_HASH,
        metadata={"security_level": "LOW"},  # Tampered metadata
    )
    with pytest.raises(SourceConflictError) as exc:
        catalog.register(tampered_manifest)
    assert "Semantic divergence" in str(exc.value)

    # Verify original security level was preserved
    assert catalog.get("critical-source").manifest.metadata["security_level"] == "HIGH"

