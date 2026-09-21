"""Data Classification Specification for TALOS (Ola 5, Fase 5.1).

Simplified data classification policy for educational sovereign usage:
- PUBLIC_EDUCATIONAL: Course material, textbooks, syllabi, exercises, code labs. Cloud allowed.
- ACCIDENTAL_PII: Accidentally pasted API keys, credentials, DNIs, emails. Blocked pre-flight.
- STUDENT_PRIVATE: Internal cognitive state (BKT, SM-2, Hint Ledger, session history). Strictly local in SQLite.
"""

from enum import Enum


class DataClassification(str, Enum):
    """Authoritative data classification tiers."""
    PUBLIC_EDUCATIONAL = "public_educational"
    ACCIDENTAL_PII = "accidental_pii"
    STUDENT_PRIVATE = "student_private"


def is_cloud_allowed(classification: DataClassification) -> bool:
    """Determine if a classified payload is permitted to be transmitted to cloud LLM providers."""
    return classification == DataClassification.PUBLIC_EDUCATIONAL
