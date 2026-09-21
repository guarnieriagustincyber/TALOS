"""Contract tests for domain enum stability and immutability.

Verifies that SourceRole and EvidenceStatus enums strictly maintain
the exact values specified in docs/01-SPEC-V1.0.md (§5, §2.P4, §2.P5).
"""

import pytest
from pydantic import ValidationError

from study_engine.contracts.enums import EvidenceStatus, SourceRole
from study_engine.contracts.evidence import Evidence
from study_engine.contracts.source import Source


def test_source_role_exact_members():
    """SourceRole must contain exactly the 7 roles specified in docs/01-SPEC-V1.0.md §5."""
    expected_roles = {
        "PRIMARY",
        "SECONDARY",
        "REFERENCE",
        "OFFICIAL",
        "COURSE",
        "PRACTICAL",
        "COMPLEMENTARY",
    }
    actual_roles = {member.value for member in SourceRole}
    assert actual_roles == expected_roles, f"SourceRole drift detected: {actual_roles} != {expected_roles}"
    assert len(SourceRole) == 7


def test_source_role_string_behavior():
    """SourceRole members must be instances of str and match their name/value."""
    for member in SourceRole:
        assert isinstance(member, str)
        assert member.name == member.value


def test_evidence_status_exact_members():
    """EvidenceStatus must contain exactly the 5 statuses specified in docs/01-SPEC-V1.0.md §2 (P4, P5)."""
    expected_statuses = {
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "COMPLEMENT",
        "INFERENCE",
        "NO_EVIDENCE",
    }
    actual_statuses = {member.value for member in EvidenceStatus}
    assert actual_statuses == expected_statuses, f"EvidenceStatus drift detected: {actual_statuses} != {expected_statuses}"
    assert len(EvidenceStatus) == 5


def test_evidence_status_string_behavior():
    """EvidenceStatus members must be instances of str and match their name/value."""
    for member in EvidenceStatus:
        assert isinstance(member, str)
        assert member.name == member.value


@pytest.mark.parametrize("invalid_role", ["MAIN", "primary", "TERTIARY", "CUSTOM_ROLE", "", None, 123])
def test_source_rejects_unauthorized_role(invalid_role):
    """Source must reject any role value not explicitly in SourceRole."""
    with pytest.raises(ValidationError):
        Source(source_id="src-test", title="Test Title", role=invalid_role)


@pytest.mark.parametrize("invalid_status", ["VERIFIED", "supported", "TRUE", "UNKNOWN", "", None, 0])
def test_evidence_rejects_unauthorized_status(invalid_status):
    """Evidence must reject any status value not explicitly in EvidenceStatus."""
    with pytest.raises(ValidationError):
        Evidence(id="ev-test", claim="Test claim", status=invalid_status)
