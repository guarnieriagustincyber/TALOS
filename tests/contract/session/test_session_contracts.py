"""Contract tests for Subsystem S5.3 Session Orchestrator models and FSM."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.session.contracts import (
    InvalidSessionTransitionError,
    RecoveryDisposition,
    SessionDecision,
    SessionStatus,
    SessionTurnOutput,
    StudentInput,
    StudentInputType,
    TerminalAction,
    TurnActionType,
)

from study_engine.session.fsm import SessionFSM


def test_student_input_immutability_and_separation() -> None:
    """Verify StudentInput is frozen and separates requested_node_id."""
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    s_input = StudentInput(
        input_id="in-1",
        session_id="sess-1",
        turn_index=0,
        input_type=StudentInputType.QUESTION,
        content="What is a memory leak?",
        timestamp=t0,
        requested_node_id="topic-pointers",
    )

    with pytest.raises(ValidationError):
        setattr(s_input, "content", "New question")

    assert s_input.requested_node_id == "topic-pointers"
    assert s_input.turn_index == 0


def test_session_decision_contract() -> None:
    """Verify SessionDecision separates turn planning from execution."""
    decision = SessionDecision(
        decision_id="dec-1",
        session_id="sess-1",
        turn_index=0,
        resolved_target_node_id="topic-pointers",
        action_type=TurnActionType.EXPLAIN,
        requires_assessment=False,
        requires_retrieval=True,
        requires_generation=True,
        requires_ledger_append=False,
    )
    with pytest.raises(ValidationError):
        setattr(decision, "requires_generation", False)

    assert decision.resolved_target_node_id == "topic-pointers"
    assert decision.requires_retrieval is True
    assert decision.terminal_action == TerminalAction.NONE


def test_terminal_action_variants() -> None:
    """Verify TerminalAction closed enum variants."""
    assert TerminalAction.NONE.value == "NONE"
    assert TerminalAction.COMPLETE.value == "COMPLETE"
    assert TerminalAction.ABORT.value == "ABORT"


def test_session_turn_output_validation() -> None:

    """Verify SessionTurnOutput mandates resolved target and state hash."""
    t0 = datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc)
    out = SessionTurnOutput(
        turn_id="turn-1",
        session_id="sess-1",
        turn_index=0,
        action_type=TurnActionType.EXPLAIN,
        resolved_target_node_id="topic-pointers",
        content="A memory leak occurs when...",
        audit_report_id="audit-123",
        produced_evidence_id=None,
        student_state_id="0" * 64,
        created_at=t0,
    )
    assert out.student_state_id == "0" * 64
    assert out.audit_report_id == "audit-123"

    # Reject invalid state hash format
    with pytest.raises(ValidationError):
        SessionTurnOutput(
            turn_id="turn-2",
            session_id="sess-1",
            turn_index=0,
            action_type=TurnActionType.EXPLAIN,
            resolved_target_node_id="topic-pointers",
            content="Content",
            student_state_id="short-hash",
            created_at=t0,
        )


def test_recovery_disposition_variants() -> None:
    """Verify RecoveryDisposition closed enum variants."""
    assert RecoveryDisposition.REPLAY_COMPLETED.value == "REPLAY_COMPLETED"
    assert RecoveryDisposition.RESTART_EVALUATION.value == "RESTART_EVALUATION"
    assert RecoveryDisposition.RETURN_TO_WAITING.value == "RETURN_TO_WAITING"


def test_session_fsm_valid_lifecycle() -> None:
    """Verify standard happy-path progression of SessionFSM."""
    fsm = SessionFSM()
    status_0: SessionStatus = fsm.current_status
    assert status_0 == SessionStatus.CREATED
    assert fsm.is_terminal is False

    fsm.transition_to(SessionStatus.ACTIVE, "Session started")
    status_1: SessionStatus = fsm.current_status
    assert status_1 == SessionStatus.ACTIVE

    fsm.transition_to(
        SessionStatus.WAITING_FOR_STUDENT, "Initial challenge presented"
    )
    status_2: SessionStatus = fsm.current_status
    assert status_2 == SessionStatus.WAITING_FOR_STUDENT

    fsm.transition_to(SessionStatus.EVALUATING, "Input received from student")
    status_3: SessionStatus = fsm.current_status
    assert status_3 == SessionStatus.EVALUATING

    fsm.transition_to(SessionStatus.ACTIVE, "Turn evaluated")
    status_4: SessionStatus = fsm.current_status
    assert status_4 == SessionStatus.ACTIVE

    fsm.transition_to(SessionStatus.COMPLETED, "Curricular goal fulfilled")
    status_5: SessionStatus = fsm.current_status
    assert status_5 == SessionStatus.COMPLETED
    assert fsm.is_terminal is True
    assert len(fsm.transition_history) == 6


def test_session_fsm_illegal_transitions_rejected() -> None:
    """HG-S5.3-05: Illegal transitions raise InvalidSessionTransitionError."""

    fsm = SessionFSM()
    # Cannot jump directly from CREATED to EVALUATING
    with pytest.raises(InvalidSessionTransitionError):
        fsm.transition_to(SessionStatus.EVALUATING)

    # Cannot jump directly from CREATED to WAITING_FOR_STUDENT
    with pytest.raises(InvalidSessionTransitionError):
        fsm.transition_to(SessionStatus.WAITING_FOR_STUDENT)

    # Transition to ABORTED is allowed
    fsm.transition_to(SessionStatus.ABORTED, "Session cancelled")
    status_aborted: SessionStatus = fsm.current_status
    assert status_aborted == SessionStatus.ABORTED
    assert fsm.is_terminal is True

    # Cannot transition out of terminal ABORTED state
    with pytest.raises(InvalidSessionTransitionError):
        fsm.transition_to(SessionStatus.ACTIVE)


def test_contract_isolation_no_external_engine_coupling() -> None:
    """HG-S5.3-O1-01: Contracts & FSM do not import external engines."""
    # Inspect imported modules in session.contracts and session.fsm

    import study_engine.session.contracts as sc
    import study_engine.session.fsm as sf

    forbidden_prefixes = (
        "study_engine.roadmap",
        "study_engine.state",
        "study_engine.retrieval",
        "study_engine.generation",
        "study_engine.audit",
    )

    for mod in (sc, sf):
        mod_dict = mod.__dict__
        for name, val in mod_dict.items():
            if hasattr(val, "__module__") and val.__module__:
                for prefix in forbidden_prefixes:
                    assert not val.__module__.startswith(prefix), (
                        f"Contract isolation violation: {name} from {mod} "
                        f"imports from {val.__module__}"
                    )
