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
        self,
        kc_id: str,
        passed: bool,
        score: float,
        content_hash: Optional[str] = None,
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        """Update student BKT knowledge state if tracker is configured.

        Idempotency guard: if *content_hash* is provided and matches the hash
        stored in the last report for this kc_id, the BKT is NOT updated again.
        This prevents P(L) from artificially saturating to 1.0 when the student
        re-submits the same unchanged file.
        """
        if not self.bkt_tracker:
            return False, None, None

        try:
            state_before = self.bkt_tracker.get_state(kc_id)
            p_L_before = round(state_before.p_L, 4) if state_before else 0.0

            # --- Idempotency check ---
            if content_hash is not None:
                # The hash of the last evaluated submission is stored as a custom
                # attribute on the BKT state.  If it matches, skip the update.
                last_hash = getattr(state_before, "_submission_hash", None)
                if last_hash == content_hash:
                    # Same content: return current state without mutating
                    return True, p_L_before, p_L_before

            # Register trial in BKT
            new_state = self.bkt_tracker.update(kc_id=kc_id, correct=passed)

            # Attach the hash so the next call can detect a duplicate
            if content_hash is not None and new_state is not None:
                try:
                    new_state._submission_hash = content_hash
                    self.bkt_tracker.save_state(new_state)
                except Exception:
                    pass  # Non-critical; idempotency degrades gracefully

            state_after = self.bkt_tracker.get_state(kc_id)
            p_L_after = round(state_after.p_L, 4) if state_after else p_L_before

            return True, p_L_before, p_L_after
        except Exception:
            return False, None, None
