"""Finite State Machine governing session lifecycle in Subsystem S5.3."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from study_engine.session.contracts import (
    InvalidSessionTransitionError,
    SessionStatus,
)

_VALID_TRANSITIONS: Dict[SessionStatus, Tuple[SessionStatus, ...]] = {
    SessionStatus.CREATED: (SessionStatus.ACTIVE, SessionStatus.ABORTED),
    SessionStatus.ACTIVE: (
        SessionStatus.WAITING_FOR_STUDENT,
        SessionStatus.COMPLETED,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
    ),
    SessionStatus.WAITING_FOR_STUDENT: (
        SessionStatus.EXECUTING,
        SessionStatus.ACTIVE,
        SessionStatus.RECOVERING,
        SessionStatus.COMPLETED,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
        SessionStatus.EVALUATING,
    ),
    SessionStatus.EXECUTING: (
        SessionStatus.ASSESSING,
        SessionStatus.RECOVERING,
        SessionStatus.WAITING_FOR_STUDENT,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
    ),
    SessionStatus.ASSESSING: (
        SessionStatus.INGESTING,
        SessionStatus.RECOVERING,
        SessionStatus.WAITING_FOR_STUDENT,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
    ),
    SessionStatus.INGESTING: (
        SessionStatus.WAITING_FOR_STUDENT,
        SessionStatus.RECOVERING,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
    ),
    SessionStatus.RECOVERING: (
        SessionStatus.WAITING_FOR_STUDENT,
        SessionStatus.INGESTING,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
    ),
    SessionStatus.EVALUATING: (
        SessionStatus.ACTIVE,
        SessionStatus.WAITING_FOR_STUDENT,
        SessionStatus.COMPLETED,
        SessionStatus.ABORTED,
        SessionStatus.EXPIRED,
    ),
    SessionStatus.COMPLETED: (),
    SessionStatus.ABORTED: (),
    SessionStatus.EXPIRED: (),
}


class SessionFSM:
    """Strict finite state machine governing session transitions."""

    def __init__(
        self, initial_status: SessionStatus = SessionStatus.CREATED
    ) -> None:
        self._current_status = initial_status
        self._history: List[Dict[str, Any]] = [
            {
                "from_status": None,
                "to_status": initial_status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rationale": "Initial state",
            }
        ]

    @property
    def current_status(self) -> SessionStatus:
        """Return the current FSM lifecycle status."""
        return self._current_status

    @property
    def is_terminal(self) -> bool:
        """Return True if session has reached a terminal state."""
        return self._current_status in (
            SessionStatus.COMPLETED,
            SessionStatus.ABORTED,
            SessionStatus.EXPIRED,
        )

    @property
    def transition_history(self) -> Tuple[Dict[str, Any], ...]:
        """Return immutable chronological record of state transitions."""
        return tuple(self._history)

    def can_transition_to(self, target: SessionStatus) -> bool:
        """Return True if transition to target status is valid."""
        return target in _VALID_TRANSITIONS.get(self._current_status, ())

    def transition_to(
        self, target: SessionStatus, rationale: Optional[str] = None
    ) -> None:
        """Execute a state transition or raise error if invalid.

        Raises:
            InvalidSessionTransitionError: If target transition is forbidden.
        """
        if not self.can_transition_to(target):
            msg = (
                f"Illegal session transition from "
                f"'{self._current_status.value}' to '{target.value}'."
            )
            raise InvalidSessionTransitionError(msg)

        from_status = self._current_status

        self._current_status = target
        self._history.append(
            {
                "from_status": from_status.value,
                "to_status": target.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rationale": rationale or "Standard state transition",
            }
        )
