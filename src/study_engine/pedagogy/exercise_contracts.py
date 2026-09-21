"""Exercise Contracts and Provenance Models for Subsystem E3 / S4.

INVARIANTS:
1. Every candidate has a cryptographic content_hash and source_hash.
2. Operational definitions:
   - UNVERIFIED: extracted automatically or unassessed. FORBIDDEN from presentation.
   - QUALIFIABLE: verified by an epistemic authority (prompt, expected answer, location, type).
3. Evaluation is restricted to N1 (MC, EXACT_TEXT, NUMERIC).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class ExerciseVerificationStatus(str, Enum):
    """Operational certification status of an exercise candidate."""

    UNVERIFIED = "UNVERIFIED"
    QUALIFIABLE = "QUALIFIABLE"


class ExerciseType(str, Enum):
    """Pedagogical evaluation format (Strict N1 for 48h MVP)."""

    MC = "MC"
    EXACT_TEXT = "EXACT_TEXT"
    NUMERIC = "NUMERIC"


@dataclass(frozen=True)
class ExerciseCandidate:
    """Rigorous exercise representation with end-to-end cryptographic provenance."""

    exercise_id: str
    source_id: str
    source_location: str
    source_hash: str
    extractor_version: str
    extraction_method: str
    verification_status: ExerciseVerificationStatus
    verified_by: Optional[str]
    verification_timestamp: Optional[datetime]
    content_hash: str
    kc_id: str
    prompt: str
    exercise_type: ExerciseType
    options: Optional[Tuple[str, ...]] = None  # Mandatory for MC
    expected_answer: str = ""
    solution_explanation: Optional[str] = None

    def is_presentable(self) -> bool:
        """Fail-closed invariant: only QUALIFIABLE candidates may be presented to students."""
        return self.verification_status == ExerciseVerificationStatus.QUALIFIABLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exercise_id": self.exercise_id,
            "source_id": self.source_id,
            "source_location": self.source_location,
            "source_hash": self.source_hash,
            "extractor_version": self.extractor_version,
            "extraction_method": self.extraction_method,
            "verification_status": self.verification_status.value,
            "verified_by": self.verified_by,
            "verification_timestamp": (
                self.verification_timestamp.isoformat()
                if self.verification_timestamp
                else None
            ),
            "content_hash": self.content_hash,
            "kc_id": self.kc_id,
            "prompt": self.prompt,
            "exercise_type": self.exercise_type.value,
            "options": list(self.options) if self.options else None,
            "expected_answer": self.expected_answer,
            "solution_explanation": self.solution_explanation,
        }
