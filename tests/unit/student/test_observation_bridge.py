"""Unit tests for ObservationBridge in Subsystem E3 (Amendment H2)."""

import pytest

from study_engine.evidence.symbolic_verifier import SymbolicVerdict
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import ExerciseFormat, RemediationOption
from study_engine.student.laguna_detector import LagunaDetector
from study_engine.student.observation_bridge import ObservationBridge
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
from study_engine.student.storage import StudentStorage


def test_bridge_symbolic_verified_true():
    """Symbolic VERIFIED_TRUE triggers P(L) boost (p_G=0.02) and SM-2 quality 5."""
    storage = StudentStorage(db_path=":memory:")
    bkt = BKTTracker(storage=storage)
    laguna = LagunaDetector(bkt=bkt, storage=storage)
    spaced = SpacedRepetitionScheduler(storage=storage)
    bridge = ObservationBridge(bkt=bkt, laguna_detector=laguna, spaced_repetition=spaced)

    kc = "U01-T01"
    anchor = "ANCHOR-SYM"
    p_initial = bkt.get_state(kc).p_L

    bkt_state, interrupt = bridge.process_symbolic_result(
        kc_id=kc,
        symbolic_verdict=SymbolicVerdict.VERIFIED_TRUE,
        current_topic_id="U02-T01",
        anchor_id=anchor,
    )

    assert bkt_state.p_L > p_initial
    assert bkt_state.p_G == 0.02
    assert interrupt is None

    # Check that anchor received quality 5
    anchor_state = spaced.get_anchor_state(anchor)
    assert anchor_state.last_quality == 5
    assert anchor_state.repetitions == 1


def test_bridge_symbolic_rejected_hallucination_triggers_laguna():
    """REJECTED_HALLUCINATION in a prerequisite triggers LagunaDetector interrupt."""
    storage = StudentStorage(db_path=":memory:")
    bkt = BKTTracker(storage=storage)
    laguna = LagunaDetector(bkt=bkt, storage=storage)
    bridge = ObservationBridge(bkt=bkt, laguna_detector=laguna)

    current_topic = "U02-T01"
    prereq = "U01-T01"
    laguna.register_prerequisites(current_topic, {prereq})

    bkt_state, interrupt = bridge.process_symbolic_result(
        kc_id=prereq,
        symbolic_verdict=SymbolicVerdict.REJECTED_HALLUCINATION,
        current_topic_id=current_topic,
    )

    assert interrupt is not None
    assert interrupt.kc_id == prereq
    assert interrupt.p_L < 0.60
    assert RemediationOption.PAUSE_AND_REMEDIATE in interrupt.options


def test_bridge_rejects_unverifiable_verdict():
    """UNVERIFIABLE verdict cannot mutate student cognitive state (Fail-Closed H2)."""
    storage = StudentStorage(db_path=":memory:")
    bkt = BKTTracker(storage=storage)
    laguna = LagunaDetector(bkt=bkt, storage=storage)
    bridge = ObservationBridge(bkt=bkt, laguna_detector=laguna)

    with pytest.raises(ValueError, match="non-verifiable verdict"):
        bridge.process_symbolic_result(
            kc_id="U01-T01",
            symbolic_verdict=SymbolicVerdict.UNVERIFIABLE,
            current_topic_id="U02-T01",
        )


def test_bridge_exact_correction_flow():
    """Deterministic exact correction updates BKT and SpacedRepetition atomically."""
    storage = StudentStorage(db_path=":memory:")
    bkt = BKTTracker(storage=storage)
    laguna = LagunaDetector(bkt=bkt, storage=storage)
    spaced = SpacedRepetitionScheduler(storage=storage)
    bridge = ObservationBridge(bkt=bkt, laguna_detector=laguna, spaced_repetition=spaced)

    kc = "U01-T02"
    anchor = "ANCHOR-EXACT"

    bkt_state, interrupt = bridge.process_exact_correction(
        kc_id=kc,
        correct=True,
        current_topic_id="U01-T02",
        format_type=ExerciseFormat.CLOSED_CHOICE,
        n_options=4,
        anchor_id=anchor,
    )

    assert bkt_state.attempts == 1
    assert bkt_state.p_G == 0.25
    assert interrupt is None

    anchor_state = spaced.get_anchor_state(anchor)
    assert anchor_state.last_quality == 4
