"""Unit tests for ReadinessProbe in Subsystem E3."""

import pytest

from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import ReadinessDecision
from study_engine.student.readiness_probe import ReadinessProbe


def test_readiness_no_prerequisites():
    """Topic without prerequisites returns START decision."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    probe.register_prerequisites("U01-T01", [])

    report = probe.assess("U01-T01")
    assert report.decision == ReadinessDecision.START
    assert len(report.missing_prereqs) == 0
    assert len(report.assessments) == 0


def test_readiness_all_prerequisites_mastered():
    """When all prerequisites have P(L) >= 0.80, returns START."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    target = "U03-T01"
    prereqs = ["U01-T01", "U02-T01"]
    probe.register_prerequisites(target, prereqs)

    # Master both prerequisites
    for pr in prereqs:
        for _ in range(6):
            tracker.update(kc_id=pr, correct=True)
        assert tracker.get_state(pr).p_L >= 0.80

    report = probe.assess(target)
    assert report.decision == ReadinessDecision.START
    assert len(report.missing_prereqs) == 0
    assert all(a.status == "DOMINADO" for a in report.assessments)


def test_readiness_up_to_two_missing_scaffold():
    """When 1 or 2 prerequisites are missing, returns START_WITH_SCAFFOLD."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    target = "U04-T01"
    prereqs = ["U01-T01", "U02-T01", "U03-T01"]
    probe.register_prerequisites(target, prereqs)

    # Master U01-T01, leave U02-T01 and U03-T01 unattempted (missing)
    for _ in range(6):
        tracker.update(kc_id="U01-T01", correct=True)

    report = probe.assess(target, plan_only=True)
    assert report.decision == ReadinessDecision.START_WITH_SCAFFOLD
    assert len(report.missing_prereqs) == 2


def test_readiness_more_than_two_missing_remediate_first():
    """When > 2 prerequisites are missing, returns REMEDIATE_FIRST."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    target = "U05-T01"
    prereqs = ["U01-T01", "U02-T01", "U03-T01", "U04-T01"]
    probe.register_prerequisites(target, prereqs)

    report = probe.assess(target, plan_only=True)
    assert report.decision == ReadinessDecision.REMEDIATE_FIRST
    assert len(report.missing_prereqs) == 4
    assert all(a.confidence == "low" for a in report.assessments)


def test_readiness_probe_determinism():
    """10 consecutive runs with identical inputs produce identical reports."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    target = "U02-T01"
    prereqs = ["U01-T01", "U01-T02"]
    probe.register_prerequisites(target, prereqs)

    tracker.update(kc_id="U01-T01", correct=True)

    first_report = probe.assess(target, plan_only=True)
    for _ in range(9):
        subsequent_report = probe.assess(target, plan_only=True)
        assert subsequent_report.decision == first_report.decision
        assert len(subsequent_report.assessments) == len(first_report.assessments)
        for a1, a2 in zip(first_report.assessments, subsequent_report.assessments):
            assert a1.kc_id == a2.kc_id
            assert a1.status == a2.status
            assert a1.p_L == a2.p_L
            assert a1.confidence == a2.confidence


def test_readiness_probe_advisory_never_raises_veto():
    """ReadinessProbe provides recommendations and NEVER raises a blocker or veto exception."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    probe.register_prerequisites("ADVANCED-01", ["BASIC-01", "BASIC-02", "BASIC-03"])

    report = probe.assess("ADVANCED-01")
    assert report.decision == ReadinessDecision.REMEDIATE_FIRST
    # Still valid and accessible, report carries decision as an advisory attribute


def test_readiness_probe_administer_vs_plan_only():
    """Amendment H8: administer=True administers questions vs plan_only=True."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)
    target = "U02-T01"
    prereq = "U01-T01"
    probe.register_prerequisites(target, [prereq])

    # In plan_only mode, unattempted prereq remains unadministered
    rep_plan = probe.assess(target, plan_only=True, administer=False)
    assert rep_plan.assessments[0].confidence == "low"
    assert rep_plan.assessments[0].p_L is None

    # In administer mode with interactive answers, answers update mastery deterministically
    rep_admin = probe.assess(
        target,
        plan_only=False,
        administer=True,
        interactive_answers={prereq: [True, True, True, True]},
    )
    assert rep_admin.assessments[0].confidence == "medium"
    assert rep_admin.assessments[0].p_L is not None
    assert rep_admin.decision == ReadinessDecision.START


def test_readiness_fail_closed_empty_target():
    """Fail-closed on empty or blank target_topic_id (H4)."""
    tracker = BKTTracker()
    probe = ReadinessProbe(bkt=tracker)

    with pytest.raises(ValueError, match="target_topic_id cannot be empty"):
        probe.assess("")
