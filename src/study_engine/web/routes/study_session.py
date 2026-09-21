"""FastAPI router for Unified Study Session endpoints (Directiva Final v2).

Endpoints:
- POST /api/study/session/open -> StudySessionSnapshot
- GET /api/study/session/{session_id}/snapshot -> StudySessionSnapshot (derivado)
- POST /api/study/session/{session_id}/action -> StudySessionSnapshot (con validación de 7 pasos)
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from study_engine.session.study_session_contracts import (
    ActionNotAllowedForPhaseError,
    ActionNotAvailableError,
    InvalidPayloadError,
    PolicyDeniedError,
    SessionNotFoundError,
    StudySessionSnapshot,
)
from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/study/session", tags=["study_session"])


class OpenSessionRequest(BaseModel):
    notebook_id: str = Field(..., min_length=1, description="ID del notebook a abrir")
    student_id: Optional[str] = Field(default="agustin", description="ID del estudiante")


class ExecuteActionRequest(BaseModel):
    action: str = Field(..., min_length=1, description="Acción propuesta por el frontend")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Datos asociados a la acción")


def _snapshot_to_dict(snap: StudySessionSnapshot) -> Dict[str, Any]:
    """Serializa el snapshot inmutable a un diccionario compatible con JSON."""
    return {
        "session_id": snap.session_id,
        "notebook_id": snap.notebook_id,
        "student_id": snap.student_id,
        "session_state_hash": snap.session_state_hash,
        "curriculum_position": {
            "unit_or_module": snap.curriculum_position.unit_or_module,
            "unit_name": snap.curriculum_position.unit_name,
            "kcs_in_unit": list(snap.curriculum_position.kcs_in_unit),
            "kcs_completed": list(snap.curriculum_position.kcs_completed),
            "kcs_in_progress": list(snap.curriculum_position.kcs_in_progress),
            "kcs_pending": list(snap.curriculum_position.kcs_pending),
        },
        "eligible_kcs": list(snap.eligible_kcs),
        "current_kc_id": snap.current_kc_id,
        "current_kc_name": snap.current_kc_name,
        "bkt_estimate": snap.bkt_estimate,
        "bkt_note": snap.bkt_note,
        "student_context": snap.student_context.to_dict() if snap.student_context else None,
        "student_context_note": snap.student_context_note,
        "episode_id": snap.episode_id,
        "episode_phase": snap.episode_phase,
        "available_actions": list(snap.available_actions),
        "source_roles": snap.source_roles,
        "evidence_status": snap.evidence_status,
        "exercise_available": snap.exercise_available,
        "exercise_type": snap.exercise_type,
        "opening_brief_facts": (
            {
                "notebook_id": snap.opening_brief_facts.notebook_id,
                "notebook_name": snap.opening_brief_facts.notebook_name,
                "notebook_purpose": snap.opening_brief_facts.notebook_purpose,
                "curriculum_position": {
                    "unit_or_module": snap.opening_brief_facts.curriculum_position.unit_or_module,
                    "unit_name": snap.opening_brief_facts.curriculum_position.unit_name,
                    "kcs_in_unit": list(snap.opening_brief_facts.curriculum_position.kcs_in_unit),
                    "kcs_completed": list(snap.opening_brief_facts.curriculum_position.kcs_completed),
                    "kcs_in_progress": list(snap.opening_brief_facts.curriculum_position.kcs_in_progress),
                    "kcs_pending": list(snap.opening_brief_facts.curriculum_position.kcs_pending),
                },
                "eligible_kcs": list(snap.opening_brief_facts.eligible_kcs),
                "selected_kc": snap.opening_brief_facts.selected_kc,
                "selected_kc_rationale": snap.opening_brief_facts.selected_kc_rationale,
                "bkt_estimate": snap.opening_brief_facts.bkt_estimate,
                "bkt_note": snap.opening_brief_facts.bkt_note,
                "student_context_note": snap.opening_brief_facts.student_context_note,
                "proposed_action": snap.opening_brief_facts.proposed_action,
                "proposed_action_rationale": snap.opening_brief_facts.proposed_action_rationale,
                "selected_kc_display_name": getattr(snap.opening_brief_facts, "selected_kc_display_name", snap.opening_brief_facts.selected_kc),
            }
            if snap.opening_brief_facts
            else None
        ),
        "opening_brief_narrative": snap.opening_brief_narrative,
        "derived_at": snap.derived_at.isoformat(),
        "policy_version": snap.policy_version,
    }


@router.post("/open")
async def open_study_session(
    req: OpenSessionRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Abre una sesión de estudio y retorna el StudySessionSnapshot inicial."""
    orch = container.study_session_orchestrator
    try:
        import asyncio as _asyncio
        from study_engine.config import CANONICAL_STUDENT_ID
        snapshot = await _asyncio.to_thread(
            orch.open_session,
            req.notebook_id,
            CANONICAL_STUDENT_ID,
        )
        return _snapshot_to_dict(snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{session_id}/snapshot")
async def get_session_snapshot(
    session_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retorna el StudySessionSnapshot derivado del estado autoritativo."""
    orch = container.study_session_orchestrator
    state = orch._sessions.get(session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión '{session_id}' no encontrada.",
        )
    import asyncio as _asyncio
    snapshot = await _asyncio.to_thread(orch.derive_snapshot, state)
    return _snapshot_to_dict(snapshot)


@router.post("/{session_id}/action")
async def execute_session_action(
    session_id: str,
    req: ExecuteActionRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Valida en 7 pasos y ejecuta una acción propuesta por el cliente."""
    orch = container.study_session_orchestrator
    try:
        import asyncio as _asyncio
        snapshot = await _asyncio.to_thread(
            orch.execute_action,
            session_id,
            req.action,
            req.payload,
        )
        return _snapshot_to_dict(snapshot)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ActionNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ActionNotAllowedForPhaseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except InvalidPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PolicyDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
