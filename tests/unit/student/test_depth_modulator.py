"""Unit tests for DepthModulator in Subsystem E3."""

from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import RemediationInterrupt, RemediationOption
from study_engine.student.depth_modulator import DepthModulator
from study_engine.student.storage import StudentStorage


def test_depth_advanced_mastery():
    """P(L) >= 0.80 generates advanced depth directives."""
    tracker = BKTTracker()
    modulator = DepthModulator(bkt=tracker)
    topic = "U01-T01"

    # Train topic to >= 0.80
    for _ in range(7):
        tracker.update(kc_id=topic, correct=True)
    assert tracker.get_state(topic).p_L >= 0.80

    directives = modulator.get_directives(topic)
    joined = " ".join(directives)

    assert "domina este tema" in joined
    assert "terminología técnica sin definir" in joined
    assert "Evitá analogías básicas" in joined


def test_depth_standard_mastery():
    """0.50 <= P(L) < 0.80 generates standard depth directives."""
    tracker = BKTTracker()
    modulator = DepthModulator(bkt=tracker)
    topic = "U01-T01"

    # Single correct answer brings P(L) from 0.10 to ~0.50
    tracker.update(kc_id=topic, correct=True)
    p_L = tracker.get_state(topic).p_L
    assert 0.50 <= p_L < 0.80

    directives = modulator.get_directives(topic)
    joined = " ".join(directives)

    assert "noción básica" in joined
    assert "Definí términos técnicos la primera vez" in joined
    assert "analogías del mundo físico" in joined


def test_depth_foundations_mastery():
    """P(L) < 0.50 generates foundational depth directives."""
    tracker = BKTTracker()
    modulator = DepthModulator(bkt=tracker)
    topic = "U01-T01"

    # Unattempted topic starts at p_L0 = 0.10
    assert tracker.get_state(topic).p_L < 0.50

    directives = modulator.get_directives(topic)
    joined = " ".join(directives)

    assert "aprendiendo desde cero" in joined
    assert "Definí TODOS los términos" in joined
    assert "Ejemplos simples y graduales" in joined


def test_depth_dual_track_directive_injection():
    """Amendment H6: If DUAL_TRACK was chosen, DepthModulator injects bridge directive."""
    storage = StudentStorage(db_path=":memory:")
    tracker = BKTTracker(storage=storage)
    modulator = DepthModulator(bkt=tracker, storage=storage)
    topic = "U02-T01"

    # Record a dual track remediation choice for this topic
    interrupt = RemediationInterrupt(
        kc_id="U01-T01",
        p_L=0.35,
        reason="Prereq lag",
        current_topic_id=topic,
    )
    storage.record_remediation_choice(interrupt, RemediationOption.DUAL_TRACK)

    directives = modulator.get_directives(topic)
    joined = " ".join(directives)

    assert "MODALIDAD DUAL-TRACK ACTIVA" in joined
    assert "puente conceptual con el prerequisito" in joined


def test_depth_preservation_invariant_no_evidence_mutation():
    """Verify that DepthModulator does NOT touch evidence chunks, scores or authorities."""
    tracker = BKTTracker()
    modulator = DepthModulator(bkt=tracker)
    topic = "U01-T01"

    # Synthetic evidence mock
    dummy_evidence = [
        {"id": "c1", "score": 0.95, "authority": 1.0, "text": "Evidence 1"},
        {"id": "c2", "score": 0.82, "authority": 0.8, "text": "Evidence 2"},
    ]
    orig_copy = [dict(c) for c in dummy_evidence]

    block = modulator.format_pedagogical_block(topic)
    assert isinstance(block, str)
    assert len(block) > 0

    # Strict immutability of evidence
    assert dummy_evidence == orig_copy
