"""Adversarial tests for Study Engine domain contracts."""

import pytest
from pydantic import ValidationError

from study_engine.contracts import (
    Notebook,
    Source,
    SourceRole,
    Document,
    Chunk,
    Evidence,
    EvidenceStatus,
    StudentState,
    StudyPlan,
    LLMRequest,
    LLMResponse,
    Event,
)


def test_adversarial_rejects_unknown_fields():
    """All contracts must reject unknown top-level fields (extra='forbid')."""
    with pytest.raises(ValidationError) as exc:
        Source(
            source_id="src-1",
            title="Title",
            unknown_injected_field="malicious_payload",
        )
    assert "extra_forbidden" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        Notebook(
            id="nb-1",
            name="Notebook",
            hacked_field=123,
        )
    assert "extra_forbidden" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        Evidence(
            id="ev-1",
            claim="Claim",
            status=EvidenceStatus.SUPPORTED,
            fabricated_score=999,
        )
    assert "extra_forbidden" in str(exc.value)


def test_adversarial_rejects_wrong_types():
    """Contracts must reject incorrect types strictly."""
    # Source priority must be integer
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", priority="not_an_int")

    # Document page_count must be int >= 0
    with pytest.raises(ValidationError):
        Document(id="d-1", source_id="s-1", title="T", page_count="invalid")

    # Evidence confidence must be float between 0.0 and 1.0
    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="C", status=EvidenceStatus.SUPPORTED, confidence="high")

    # StudentState understanding must be dict[str, bool]
    with pytest.raises(ValidationError):
        StudentState(student_id="st-1", understanding=["not", "a", "dict"])

    # LLMRequest messages must be list of dicts
    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", messages="not a list")


def test_adversarial_rejects_nulls_on_required_fields():
    """Required fields must not accept None/null."""
    with pytest.raises(ValidationError):
        Source(source_id=None, title="Title")

    with pytest.raises(ValidationError):
        Source(source_id="src-1", title=None)

    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="Claim", status=None)

    with pytest.raises(ValidationError):
        LLMResponse(request_id="req-1", content=None)


def test_adversarial_unicode_and_special_characters():
    """Contracts must safely handle diverse unicode, emojis, control sequences, and RTL text."""
    complex_title = "📚 Algoritmos & Estructuras de Datos / مرحباً / 🚀 \t \n \u200b\u200c"
    source = Source(
        source_id="src-unicode-01",
        title=complex_title,
        author="Luis Joyanes & Tanenbaum 🤖",
        metadata={
            "hebrew": "שלום",
            "japanese": "アルゴリズム",
            "emoji_list": ["🔥", "💡", "🎯"],
            "escapes": "line1\r\nline2\tline3\\path\\to\\file",
        },
    )
    assert source.title == complex_title
    dumped = source.model_dump_json()
    reconstructed = Source.model_validate_json(dumped)
    assert reconstructed.title == complex_title
    assert reconstructed.metadata["japanese"] == "アルゴリズム"


def test_adversarial_large_strings():
    """Contracts must be able to handle very large text payloads (e.g. 5MB) without crashing."""
    large_content = "A" * (5 * 1024 * 1024)  # 5 MB string
    doc = Document(
        id="doc-large-01",
        source_id="src-large",
        title="Very Large Text",
        content=large_content,
    )
    assert len(doc.content) == 5 * 1024 * 1024

    chunk = Chunk(
        id="chunk-large-01",
        document_id="doc-large-01",
        source_id="src-large",
        content=large_content,
    )
    assert len(chunk.content) == 5 * 1024 * 1024


def test_adversarial_deeply_nested_metadata():
    """Contracts must handle structured and nested metadata dictionaries safely."""
    nested = {
        "level_1": {
            "level_2": {
                "level_3": {
                    "keys": [1, 2, 3],
                    "flag": True,
                    "null_val": None,
                }
            }
        }
    }
    nb = Notebook(id="nb-nested", name="Nested Notebook", metadata=nested)
    dumped = nb.model_dump_json()
    reconstructed = Notebook.model_validate_json(dumped)
    assert reconstructed.metadata["level_1"]["level_2"]["level_3"]["flag"] is True


def test_adversarial_malformed_json_parsing():
    """model_validate_json must raise ValidationError on malformed JSON."""
    with pytest.raises(ValidationError):
        Source.model_validate_json("{malformed json: true")

    with pytest.raises(ValidationError):
        Source.model_validate_json("[]")  # array instead of object
