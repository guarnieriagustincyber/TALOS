"""Unit tests for Deterministic Lab Grader Interface to BKT (Phase E4, Amendment E4-7, Namespace [LAB#])."""

import pytest
from study_engine.student.contracts import ObservationSource, ExerciseFormat
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.lab_observations import LabGraderBridge, LabChallengeMapping


def test_lab_grader_correct_submission_updates_bkt() -> None:
    bkt = BKTTracker()
    grader = LabGraderBridge(bkt_tracker=bkt, config_path="config/lab_kc_map.json")

    # In config/lab_kc_map.json:
    # challenge: sql-injection-login
    # expected_flag_hash: 919ce5f21037e2777757edd5ff25280ec3696bd81674c05dfc876d225dadcc0c
    # Let's find flag or inject a challenge with known plaintext
    custom_flag = "FLAG{test_deterministic_buffer_overflow_2026}"
    import hashlib
    custom_hash = hashlib.sha256(custom_flag.encode()).hexdigest()

    grader.register_challenge(
        LabChallengeMapping(
            lab_id="test-lab",
            challenge_id="test-bof",
            kc_id="SEC-03-MEM-MGMT",
            exercise_format=ExerciseFormat.SYMBOLIC_OPEN,
            expected_flag_hash=custom_hash,
        )
    )

    initial_state = bkt.get_state("SEC-03-MEM-MGMT")
    initial_p = initial_state.p_L

    # Submit correct flag
    res = grader.grade_and_record_submission(
        lab_id="test-lab",
        challenge_id="test-bof",
        submitted_flag=custom_flag,
    )

    assert res.is_correct is True
    assert res.status_code == "CORRECT"
    assert res.kc_id == "SEC-03-MEM-MGMT"
    assert res.bkt_state is not None
    # BKT mastery must increase monotonically on correct attempt
    assert res.bkt_state.p_L > initial_p


def test_lab_grader_incorrect_submission_updates_bkt() -> None:
    bkt = BKTTracker()
    grader = LabGraderBridge(bkt_tracker=bkt, config_path="config/lab_kc_map.json")

    res = grader.grade_and_record_submission(
        lab_id="juice-shop",
        challenge_id="sql-injection-login",
        submitted_flag="WRONG_FLAG_VALUE",
    )

    assert res.is_correct is False
    assert res.status_code == "INCORRECT"
    assert res.kc_id == "SEC-05-BIN-SEC"


def test_lab_grader_rejects_llm_dialogue_updates() -> None:
    """Amendment E4-7: Zero LLM dialogue updates. Source cannot be conversational or LLM."""
    grader = LabGraderBridge(config_path="config/lab_kc_map.json")

    with pytest.raises(ValueError, match="Zero LLM dialogue updates are permitted"):
        grader.grade_and_record_submission(
            lab_id="juice-shop",
            challenge_id="sql-injection-login",
            submitted_flag="ANY_FLAG",
            source_context="LLM_DIALOGUE",
        )

    with pytest.raises(ValueError, match="Zero LLM dialogue updates are permitted"):
        grader.grade_and_record_submission(
            lab_id="juice-shop",
            challenge_id="sql-injection-login",
            submitted_flag="ANY_FLAG",
            source_context="CHAT",
        )
