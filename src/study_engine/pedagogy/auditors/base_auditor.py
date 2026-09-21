"""Base contracts and abstract class for domain exercise auditors (VSCode + TALOS).

Provides standard check structures, forensic reporting, and BKT tracking integration.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from study_engine.pedagogy.submission_reader import StudentSubmission


@dataclass
class AuditCheck:
    """Individual assertion check evaluated by an exercise auditor."""

    name: str
    passed: bool
    feedback: str
    severity: str = "ERROR"  # "ERROR", "WARNING", "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExerciseAuditReport:
    """Consolidated forensic report resulting from an exercise audit."""

    exercise_id: str
    notebook_id: str
    score: float  # 0.0 - 100.0
    passed: bool
    checks: List[AuditCheck] = field(default_factory=list)
    bkt_updated: bool = False
    p_L_before: Optional[float] = None
    p_L_after: Optional[float] = None
    observations: List[str] = field(default_factory=list)
    next_exercise: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["checks"] = [c.to_dict() for c in self.checks]
        return d


class BaseExerciseAuditor(ABC):
    """Abstract base auditor enforcing forensic validation and optional BKT updates."""

    def __init__(self, bkt_tracker: Optional[Any] = None) -> None:
        self.bkt_tracker = bkt_tracker

    @abstractmethod
    def audit(self, submission: StudentSubmission) -> ExerciseAuditReport:
        """Analyze and score the given student submission."""
        ...

    def update_bkt_if_eligible(
        self, kc_id: str, passed: bool, score: float
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        """Update student BKT knowledge state if tracker is configured."""
        if not self.bkt_tracker:
            return False, None, None

        try:
            # Check current state
            state_before = self.bkt_tracker.get_state(kc_id)
            p_L_before = round(state_before.p_L, 4) if state_before else 0.0

            # Register trial in BKT
            self.bkt_tracker.update(kc_id=kc_id, correct=passed)

            state_after = self.bkt_tracker.get_state(kc_id)
            p_L_after = round(state_after.p_L, 4) if state_after else p_L_before

            return True, p_L_before, p_L_after
        except Exception:
            return False, None, None
