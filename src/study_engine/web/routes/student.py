"""Student Cognitive State, Spaced Repetition, and Remediation Endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.student.contracts import classify_readiness
from study_engine.web.admin_auth import require_admin_token
from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/student", tags=["Student"])



class ReadinessAssessPayload(BaseModel):
    topic_id: str = Field(..., description="Curricular node or topic identifier to assess")
    plan_only: bool = Field(default=True, description="When true, does not administer diagnostic questions")


class RemediationRespondPayload(BaseModel):
    interrupt_id: str = Field(..., description="Remediation interrupt identifier")
    choice: str = Field(..., description="PAUSE_AND_REMEDIATE | NOTE_AND_CONTINUE | DUAL_TRACK")


@router.get("/cognitive-state")
def get_cognitive_state(
    limit: Optional[int] = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retrieve full cognitive state including BKT Knowledge Component masteries and alerts."""
    all_bkt = container.student_storage.get_all_bkt_states(limit=limit, offset=offset)
    kc_mastery: Dict[str, Dict[str, Any]] = {}
    for kc_id, state in all_bkt.items():
        kc_mastery[kc_id] = {
            "p_L": round(state.p_L, 4),
            "attempts": state.attempts,
            "last_update": state.last_update.isoformat(),
        }

    # Derive active alerts from low BKT mastery on prerequisites
    active_alerts: List[Dict[str, Any]] = []
    roadmap = container.get_roadmap()
    for node_id, node in roadmap.nodes.items():
        state = container.bkt_tracker.get_state(node_id)
        if state.attempts > 0 and state.p_L < 0.35:
            active_alerts.append({
                "alert_id": f"laguna_{node_id.lower().replace('-', '_')}",
                "kc_id": node_id,
                "title": node.title,
                "p_L": round(state.p_L, 4),
                "severity": "CRITICAL" if state.p_L < 0.20 else "WARNING",
                "detected_at": state.last_update.isoformat(),
            })

    return {
        "student_id": "student-study-loop-v1",
        "kc_mastery": kc_mastery,
        "active_alerts": active_alerts,
        "readiness_cache": {},
    }


@router.get("/spaced-repetition/due")
def get_due_spaced_repetition(
    limit: Optional[int] = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    container: AppContainer = Depends(get_container),
) -> List[Dict[str, Any]]:
    """Retrieve items due for SM-2 spaced repetition review."""
    now = datetime.now(timezone.utc)
    all_anchors = container.spaced_scheduler.storage.get_all_anchor_states(limit=limit, offset=offset)
    results: List[Dict[str, Any]] = []
    for anchor_id, state in all_anchors.items():
        topic_title = anchor_id
        if hasattr(container, "curriculum_registry") and container.curriculum_registry:
            topic_title = container.curriculum_registry.get_kc_display_name(anchor_id)

        results.append({
            "anchor_id": anchor_id,
            "topic_title": topic_title,
            "interval_days": state.interval,
            "due_date": state.next_review.isoformat(),
            "ef": round(state.EF, 2),
            "is_due": state.next_review <= now,
        })

    return results


@router.post("/readiness/assess")
def assess_topic_readiness(
    payload: ReadinessAssessPayload,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Evaluate prerequisite readiness for a topic before starting."""
    report = container.readiness_probe.assess(
        target_topic_id=payload.topic_id,
        plan_only=payload.plan_only,
    )
    raw = report.model_dump()
    prereqs = []
    for ass in report.assessments:
        status_str = classify_readiness(ass.p_L)
        prereqs.append({
            "prereq_id": ass.kc_id,
            "p_L": ass.p_L,
            "status": status_str,
        })
    dec_val = report.decision.value if hasattr(report.decision, "value") else str(report.decision)
    return {
        **raw,
        "target_topic_id": report.target_topic,
        "decision": dec_val,
        "recommendation": dec_val,
        "prerequisites": prereqs,
        "notes": [
            f"Prerrequisitos evaluados: {len(report.assessments)}",
            f"Decisión de readiness: {dec_val}",
        ],
    }



@router.post("/remediation/respond")
def respond_remediation(
    payload: RemediationRespondPayload,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Record student choice for a remediation interrupt."""
    from study_engine.student.contracts import RemediationInterrupt, RemediationOption

    valid_choices = {
        "PAUSE_AND_REMEDIATE": RemediationOption.PAUSE_AND_REMEDIATE,
        "NOTE_AND_CONTINUE": RemediationOption.NOTE_AND_CONTINUE,
        "DUAL_TRACK": RemediationOption.DUAL_TRACK,
    }

    choice_enum = valid_choices.get(payload.choice.upper())
    if not choice_enum:
        raise HTTPException(
            status_code=400,
            detail=f"Elección inválida '{payload.choice}'. Opciones válidas: {list(valid_choices.keys())}",
        )

    interrupt = RemediationInterrupt(
        kc_id=payload.interrupt_id,
        p_L=0.25,
        reason="Interrupción pedagógica por laguna detectada",
        current_topic_id=payload.interrupt_id,
    )

    container.student_storage.record_remediation_choice(
        interrupt=interrupt,
        chosen_option=choice_enum,
    )

    return {
        "status": "RECORDED",
        "interrupt_id": payload.interrupt_id,
        "choice": choice_enum.value,
        "next_action": f"Ejecutando política de remediación: {choice_enum.value}",
    }


@router.get("/metacognitive-profile", response_model=Dict[str, Any])
def get_metacognitive_profile(
    student_id: str = Query(default=CANONICAL_STUDENT_ID),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Consulta el perfil metacognitivo del estudiante y métricas de dependencia/autonomía (M4)."""
    require_admin_token(
        x_admin_token,
        forbidden_detail="Forbidden: se requiere header X-Admin-Token válido para consultar el perfil metacognitivo.",
    )

    storage = getattr(container, "student_storage", None)
    if storage is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage del estudiante no inicializado.",
        )

    profile = storage.calculate_solution_dependency(student_id)
    from study_engine.pedagogy.student_context import get_scaffolding_directive
    preview = get_scaffolding_directive(profile)
    res = dict(profile)
    res["scaffolding_directive_preview"] = preview
    return res
