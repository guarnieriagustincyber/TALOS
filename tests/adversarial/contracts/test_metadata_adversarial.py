"""Adversarial tests: Metadata extensibility and resilience.

Attacks:
- Non-dict types passed into metadata (strings, ints, lists, booleans).
- Metadata containing keys matching root model attributes (shadowing resilience).
- Special characters, symbols, and URLs in metadata keys.
- High key cardinality (500 keys).
- Heterogeneous and deeply nested data types inside metadata.
"""

import pytest
from pydantic import ValidationError

from study_engine.contracts import Source, Document, Evidence, EvidenceStatus


@pytest.mark.parametrize("invalid_metadata", ["not-a-dict", 123, True, ["list", "of", "items"]])
def test_rejects_non_dict_metadata(invalid_metadata):
    """Metadata field must be a dictionary and reject primitives/lists."""
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", metadata=invalid_metadata)


def test_metadata_key_shadowing_resilience():
    """Metadata containing keys named identically to root attributes must not cause collision."""
    source = Source(
        source_id="root-source-id",
        title="Root Title",
        priority=1,
        metadata={
            "source_id": "inner-shadowed-id",
            "title": "Inner Title",
            "priority": "very_high",
            "role": "CUSTOM_INNER_ROLE",
        },
    )
    # Root attributes remain intact
    assert source.source_id == "root-source-id"
    assert source.title == "Root Title"
    assert source.priority == 1

    # Metadata preserves inner keys
    assert source.metadata["source_id"] == "inner-shadowed-id"
    assert source.metadata["priority"] == "very_high"

    # Serialization preserves both layers
    dumped = source.model_dump()
    assert dumped["source_id"] == "root-source-id"
    assert dumped["metadata"]["source_id"] == "inner-shadowed-id"

    reloaded = Source.model_validate(dumped)
    assert reloaded == source


def test_metadata_with_special_character_keys():
    """Metadata must support complex key names (URLs, dots, slashes, emojis, whitespace)."""
    special_metadata = {
        "http://schema.org/isbn": "978-0073523323",
        "nested.dotted.key": 100,
        "key with spaces and #!$": True,
        "🏷️_emoji_tag": "compiler",
    }
    doc = Document(
        id="doc-special",
        source_id="src-1",
        title="Doc Special",
        metadata=special_metadata,
    )
    assert doc.metadata["http://schema.org/isbn"] == "978-0073523323"
    assert doc.metadata["🏷️_emoji_tag"] == "compiler"

    reloaded = Document.model_validate_json(doc.model_dump_json())
    assert reloaded.metadata == special_metadata


def test_metadata_high_cardinality():
    """Metadata must comfortably handle 500 keys without performance or serialization failure."""
    large_metadata = {f"custom_key_{i}": f"value_{i}" for i in range(500)}
    ev = Evidence(
        id="ev-large-meta",
        claim="Claim",
        status=EvidenceStatus.SUPPORTED,
        metadata=large_metadata,
    )
    assert len(ev.metadata) == 500
    json_str = ev.model_dump_json()
    reloaded = Evidence.model_validate_json(json_str)
    assert len(reloaded.metadata) == 500
    assert reloaded.metadata["custom_key_499"] == "value_499"
