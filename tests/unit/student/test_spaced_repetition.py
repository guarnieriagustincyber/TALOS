"""Unit tests for SpacedRepetitionScheduler (SM-2) in Subsystem E3."""

from datetime import datetime, timedelta, timezone
import pytest

from study_engine.student.contracts import (
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
)
from study_engine.student.spaced_repetition import (
    SpacedRepetitionScheduler,
    derive_sm2_quality,
)
from study_engine.student.storage import StudentStorage


def test_sm2_standard_progression():
    """Consecutive high quality scores expand interval according to SM-2."""
    scheduler = SpacedRepetitionScheduler()
    anchor = "ANCHOR-01"
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    # Repetition 1
    t1 = scheduler.schedule_review(anchor, quality=5, as_of=base_time)
    s1 = scheduler.get_anchor_state(anchor)
    assert s1.repetitions == 1
    assert s1.interval == 1
    assert t1 == base_time + timedelta(days=1)

    # Repetition 2
    t2 = scheduler.schedule_review(anchor, quality=5, as_of=t1)
    s2 = scheduler.get_anchor_state(anchor)
    assert s2.repetitions == 2
    assert s2.interval == 6
    assert t2 == t1 + timedelta(days=6)

    # Repetition 3: interval = round(6 * EF)
    t3 = scheduler.schedule_review(anchor, quality=5, as_of=t2)
    s3 = scheduler.get_anchor_state(anchor)
    assert s3.repetitions == 3
    assert s3.interval == round(6 * s2.EF)
    assert t3 == t2 + timedelta(days=s3.interval)


def test_sm2_lapse_resets_interval():
    """Quality < 3 resets repetition count and sets interval back to 1."""
    scheduler = SpacedRepetitionScheduler()
    anchor = "ANCHOR-02"
    base_time = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    # Build up 2 repetitions
    scheduler.schedule_review(anchor, quality=5, as_of=base_time)
    scheduler.schedule_review(anchor, quality=5, as_of=base_time)
    assert scheduler.get_anchor_state(anchor).repetitions == 2
    assert scheduler.get_anchor_state(anchor).interval == 6

    # Quality = 1 (forgotten)
    scheduler.schedule_review(anchor, quality=1, as_of=base_time)
    s_reset = scheduler.get_anchor_state(anchor)
    assert s_reset.repetitions == 0
    assert s_reset.interval == 1


def test_sm2_ef_absolute_floor():
    """Easiness Factor (EF) never drops below 1.30 even after continuous low grades."""
    scheduler = SpacedRepetitionScheduler()
    anchor = "ANCHOR-03"

    for _ in range(25):
        scheduler.schedule_review(anchor, quality=0)

    state = scheduler.get_anchor_state(anchor)
    assert state.EF == 1.30
    assert state.EF >= 1.30


def test_sm2_due_anchors_filtering():
    """get_due_anchors returns past and due items, excluding future items."""
    scheduler = SpacedRepetitionScheduler()
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

    # Schedule anchor 1 for yesterday
    scheduler.schedule_review("ANCHOR-PAST", quality=1, as_of=now - timedelta(days=2))
    # Schedule anchor 2 for far in the future
    scheduler.schedule_review("ANCHOR-FUTURE", quality=5, as_of=now)

    due = scheduler.get_due_anchors(as_of=now)
    assert "ANCHOR-PAST" in due
    assert "ANCHOR-FUTURE" not in due


def test_sm2_quality_mapping_derivation():
    """Amendment H7: derive_sm2_quality maps observations deterministically."""
    # Symbolic correct -> 5
    assert derive_sm2_quality(correct=True, format_type=ExerciseFormat.SYMBOLIC_OPEN) == 5

    # Correct with retry -> 4
    assert derive_sm2_quality(correct=True, format_type=ExerciseFormat.SYMBOLIC_OPEN, is_retry=True) == 4

    # Closed choice correct -> 4
    assert derive_sm2_quality(correct=True, format_type=ExerciseFormat.CLOSED_CHOICE) == 4

    # Recoverable incorrect -> 3
    assert derive_sm2_quality(correct=False, is_recoverable=True) == 3

    # Hard incorrect -> 1
    assert derive_sm2_quality(correct=False, is_recoverable=False) == 1


def test_sm2_schedule_from_observation():
    """Schedule review directly via ObservationPayload (H7)."""
    scheduler = SpacedRepetitionScheduler()
    anchor = "ANCHOR-OBS"
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    payload = ObservationPayload(
        kc_id="TOPIC-01",
        correct=True,
        source=ObservationSource.SYMBOLIC_VERIFIER,
        format=ExerciseFormat.SYMBOLIC_OPEN,
    )

    next_rev = scheduler.schedule_from_observation(anchor, payload, as_of=now)
    state = scheduler.get_anchor_state(anchor)
    assert state.last_quality == 5
    assert next_rev == now + timedelta(days=1)


def test_sm2_sqlite_persistence(tmp_path):
    """Anchor states survive reload from disk."""
    db_file = tmp_path / "student_sm2.db"
    storage1 = StudentStorage(db_path=db_file)
    scheduler1 = SpacedRepetitionScheduler(storage=storage1)
    anchor = "ANCHOR-PERSIST"

    scheduler1.schedule_review(anchor, quality=5)
    scheduler1.schedule_review(anchor, quality=5)
    saved_state = scheduler1.get_anchor_state(anchor)

    storage2 = StudentStorage(db_path=db_file)
    scheduler2 = SpacedRepetitionScheduler(storage=storage2)
    reloaded_state = scheduler2.get_anchor_state(anchor)

    assert reloaded_state.repetitions == saved_state.repetitions
    assert reloaded_state.interval == saved_state.interval
    assert reloaded_state.EF == pytest.approx(saved_state.EF, rel=1e-5)
