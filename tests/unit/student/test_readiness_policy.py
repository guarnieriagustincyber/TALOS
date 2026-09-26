from types import SimpleNamespace

from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import (
    PrerequisiteAssessment,
    ReadinessDecision,
    ReadinessReport,
    classify_readiness,
    is_blocking_for_advance,
    remediation_kind,
)
from study_engine.student.readiness_probe import ReadinessProbe
from study_engine.web.routes.student import ReadinessAssessPayload, assess_topic_readiness


def test_none_es_ausente_y_bloquea():
    assert classify_readiness(None) == "AUSENTE"
    assert is_blocking_for_advance("AUSENTE") is True
    assert remediation_kind("AUSENTE") == "SCAFFOLD_FROM_ZERO"


def test_bajo_dominio_intentado_bloquea():
    assert classify_readiness(0.2) == "EN_PROCESO"
    assert is_blocking_for_advance("EN_PROCESO") is True
    assert remediation_kind("EN_PROCESO") == "TARGETED_REMEDIATION"


def test_nocion_no_bloquea():
    assert classify_readiness(0.5) == "NOCIÓN"
    assert is_blocking_for_advance("NOCIÓN") is False
    assert remediation_kind("NOCIÓN") == "LIGHT_REVIEW"


def test_dominado_sin_accion():
    assert classify_readiness(0.85) == "DOMINADO"
    assert is_blocking_for_advance("DOMINADO") is False
    assert remediation_kind("DOMINADO") is None


def test_make_decision_cuenta_en_proceso():
    probe = ReadinessProbe(bkt=BKTTracker())
    assessment = PrerequisiteAssessment(kc_id="prereq", status="EN_PROCESO", p_L=0.2)
    assert probe.make_decision([assessment]) == ReadinessDecision.START_WITH_SCAFFOLD


def test_umbrales_unicos():
    probe = ReadinessProbe(bkt=BKTTracker())
    for p_L in [0.0, 0.34, 0.35, 0.69, 0.70, 1.0]:
        assert probe.classify_mastery(p_L) == classify_readiness(p_L)
    assert classify_readiness(None) == "AUSENTE"


def test_ruta_readiness_con_p_L_none():
    report = ReadinessReport(
        target_topic="target",
        assessments=[PrerequisiteAssessment(kc_id="prereq", status="AUSENTE", p_L=None)],
        decision=ReadinessDecision.START_WITH_SCAFFOLD,
    )
    container = SimpleNamespace(readiness_probe=SimpleNamespace(assess=lambda **_: report))
    result = assess_topic_readiness(ReadinessAssessPayload(topic_id="target"), container)
    assert result["prerequisites"][0]["status"] == "AUSENTE"
