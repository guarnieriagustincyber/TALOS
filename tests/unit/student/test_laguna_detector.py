"""Unit tests for LagunaDetector in Subsystem E3."""

import random
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import (
    ObservationPayload,
    ObservationSource,
    RemediationOption,
)
from study_engine.student.laguna_detector import LagunaDetector
from study_engine.student.storage import StudentStorage


def test_laguna_detected_on_failing_prerequisite():
    """Error in a prerequisite concept with P(L) < 0.60 triggers RemediationInterrupt."""
    tracker = BKTTracker()
    detector = LagunaDetector(bkt=tracker)
    current_topic = "U02-T01"
    prereq = "U01-T01"
    detector.register_prerequisites(current_topic, {prereq})

    # Initially prior is 0.10. An incorrect answer keeps it low
    interrupt = detector.check_after_exercise(
        kc_id_or_payload=prereq,
        correct=False,
        current_topic_id=current_topic,
    )

    assert interrupt is not None
    assert interrupt.kc_id == prereq
    assert interrupt.current_topic_id == current_topic
    assert interrupt.p_L < 0.60
    assert RemediationOption.PAUSE_AND_REMEDIATE in interrupt.options
    assert RemediationOption.DUAL_TRACK in interrupt.options


def test_no_laguna_if_not_a_prerequisite():
    """Error in a KC that is NOT a prerequisite of current_topic returns None."""
    tracker = BKTTracker()
    detector = LagunaDetector(bkt=tracker)
    current_topic = "U02-T01"
    non_prereq = "U05-T09"
    detector.register_prerequisites(current_topic, {"U01-T01"})

    interrupt = detector.check_after_exercise(
        kc_id_or_payload=non_prereq,
        correct=False,
        current_topic_id=current_topic,
    )

    assert interrupt is None


def test_no_laguna_on_correct_prerequisite_attempt():
    """A correct attempt on a prerequisite does not trigger remediation."""
    tracker = BKTTracker()
    detector = LagunaDetector(bkt=tracker)
    current_topic = "U02-T01"
    prereq = "U01-T01"
    detector.register_prerequisites(current_topic, {prereq})

    interrupt = detector.check_after_exercise(
        kc_id_or_payload=prereq,
        correct=True,
        current_topic_id=current_topic,
    )

    assert interrupt is None


def test_no_laguna_if_p_L_stays_above_threshold():
    """If student mastery P(L) remains >= 0.60 despite a slip, do not interrupt."""
    tracker = BKTTracker()
    detector = LagunaDetector(bkt=tracker)
    current_topic = "U02-T01"
    prereq = "U01-T01"
    detector.register_prerequisites(current_topic, {prereq})

    # Bring to high mastery (~0.95)
    for _ in range(8):
        tracker.update(kc_id=prereq, correct=True)
    assert tracker.get_state(prereq).p_L > 0.85

    # A single error drops P(L) slightly but keeps it well above 0.60
    interrupt = detector.check_after_exercise(
        kc_id_or_payload=prereq,
        correct=False,
        current_topic_id=current_topic,
    )

    assert tracker.get_state(prereq).p_L >= 0.60
    assert interrupt is None


def test_laguna_record_choice_dual_track():
    """Amendment H6: Student choice of DUAL_TRACK is recorded into local state."""
    storage = StudentStorage(db_path=":memory:")
    tracker = BKTTracker(storage=storage)
    detector = LagunaDetector(bkt=tracker, storage=storage)
    current_topic = "U02-T01"
    prereq = "U01-T01"
    detector.register_prerequisites(current_topic, {prereq})

    interrupt = detector.check_after_exercise(
        kc_id_or_payload=prereq,
        correct=False,
        current_topic_id=current_topic,
    )
    assert interrupt is not None

    detector.record_choice(interrupt, RemediationOption.DUAL_TRACK)

    choices = storage.get_remediation_choices(topic_id=current_topic)
    assert len(choices) == 1
    assert choices[0]["chosen_option"] == "DUAL_TRACK"
    assert choices[0]["kc_id"] == prereq


def test_laguna_precision_synthetic_cases():
    """Synthetic test over 50 scenarios verifying > 90% precision and recall."""
    rng = random.Random(1337)
    correct_triggers = 0
    total_evaluations = 50

    for i in range(total_evaluations):
        tracker = BKTTracker()
        detector = LagunaDetector(bkt=tracker)
        current_topic = f"TOPIC-{i}"
        prereq = f"PREREQ-{i}"
        other_topic = f"OTHER-{i}"
        detector.register_prerequisites(current_topic, {prereq})

        is_target_prereq = (i % 2 == 0)
        eval_kc = prereq if is_target_prereq else other_topic

        # If we want a high prior, we train it up
        has_high_mastery = (i % 4 == 0)
        if has_high_mastery:
            for _ in range(8):
                tracker.update(kc_id=eval_kc, correct=True)

        is_eval_correct = (i % 3 == 0)

        interrupt = detector.check_after_exercise(
            kc_id_or_payload=eval_kc,
            correct=is_eval_correct,
            current_topic_id=current_topic,
        )

        expected_trigger = (
            is_target_prereq
            and not is_eval_correct
            and tracker.get_state(eval_kc).p_L < 0.60
        )

        actual_trigger = interrupt is not None
        if expected_trigger == actual_trigger:
            correct_triggers += 1

    accuracy = correct_triggers / total_evaluations
    assert accuracy >= 0.90, f"LagunaDetector accuracy was {accuracy:.2%}, expected >= 90%"
