"""Unit tests for Evidence contract."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.evidence import Evidence
from study_engine.contracts.enums import EvidenceStatus


def test_evidence_valid_supported():
    ev = Evidence(
        id="ev-001",
        claim="La recursión requiere un caso base para evitar bucles infinitos.",
        status=EvidenceStatus.SUPPORTED,
        content="En toda función recursiva debe existir al menos un caso base.",
        source_id="joyanes-fp-4e",
        document_id="doc-ch5",
        chunk_id="chunk-5-2",
        page=120,
        confidence=0.95,
    )
    assert ev.status == EvidenceStatus.SUPPORTED
    assert ev.confidence == 0.95


def test_evidence_valid_no_evidence():
    # Specification rule: [NO_EVIDENCE] is valid and preferred over guessing
    ev = Evidence(
        id="ev-002",
        claim="Joyanes recomienda utilizar siempre loops while en lugar de for.",
        status=EvidenceStatus.NO_EVIDENCE,
    )
    assert ev.status == EvidenceStatus.NO_EVIDENCE
    assert ev.content is None
    assert ev.source_id is None


def test_evidence_all_statuses_valid():
    for status in EvidenceStatus:
        ev = Evidence(id=f"ev-{status.value}", claim="Some claim", status=status)
        assert ev.status == status


def test_evidence_invalid_status():
    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="Claim", status="INVALID_STATUS")


def test_evidence_invalid_confidence_range():
    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="Claim", status=EvidenceStatus.SUPPORTED, confidence=1.5)

    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="Claim", status=EvidenceStatus.SUPPORTED, confidence=-0.1)
