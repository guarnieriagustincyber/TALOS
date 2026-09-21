"""Adversarial tests: Enum corruption.

Attacks:
- Casing mutations (lowercase, MixedCase).
- Similar / misspelled names (PRIMARI, DEFAULT, NONE, SUPPORT).
- Cross-enum injection (EvidenceStatus passed to Source.role).
- Numeric or structural inputs into enum fields.
"""

import pytest
from pydantic import ValidationError

from study_engine.contracts import Source, Evidence, SourceRole, EvidenceStatus


@pytest.mark.parametrize(
    "corrupted_role",
    [
        "primary",
        "Primary",
        "pRIMARY",
        "PRIMARI",
        "PRIMARY_SOURCE",
        "MAIN",
        "DEFAULT",
        "OFFICIAL_SOURCE",
        "complementary",
        "SUPPORTED",  # EvidenceStatus value injected
        "NO_EVIDENCE",  # EvidenceStatus value injected
        "",
        " ",
        1,
        True,
        ["PRIMARY"],
        {"role": "PRIMARY"},
    ],
)
def test_source_role_corruption_rejected(corrupted_role):
    with pytest.raises(ValidationError):
        Source(source_id="src-1", title="Title", role=corrupted_role)


@pytest.mark.parametrize(
    "corrupted_status",
    [
        "supported",
        "Supported",
        "sUPPORTED",
        "SUPPORT",
        "PARTIAL",
        "PARTIALLY-SUPPORTED",
        "COMPLEMENTS",
        "INFERRED",
        "NO-EVIDENCE",
        "NONE",
        "PRIMARY",  # SourceRole value injected
        "OFFICIAL",  # SourceRole value injected
        "",
        " ",
        0,
        False,
        ["SUPPORTED"],
        {"status": "SUPPORTED"},
    ],
)
def test_evidence_status_corruption_rejected(corrupted_status):
    with pytest.raises(ValidationError):
        Evidence(id="ev-1", claim="Claim", status=corrupted_status)
