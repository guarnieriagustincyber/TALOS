"""FastAPI Router for Sovereign Pedagogical Operations (Vertical Slice 48h).

Endpoints:
- POST /api/pedagogy/episode/start
- GET /api/pedagogy/episode/{episode_id}/concept
- GET /api/pedagogy/episode/{episode_id}/next
- POST /api/pedagogy/episode/{episode_id}/respond
- GET /api/pedagogy/notebook/{notebook_id}/kcs

INVARIANTS:
1. S4.4 audit is strictly enforced. Concept endpoints emit PRESENTABLE or ABSTAINED.
2. The orchestrator never decides student mastery or next KC via LLM. BKT + roadmap decide.
3. Response processing is idempotent via (episode_id, step_id).
4. kc_id is validated fail-closed against notebook catalog and curriculum.
5. student_context (consultive) and bkt (authoritative) are strictly separated in API models.
"""

from typing import Any, Dict, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from study_engine.pedagogy.exercise_contracts import ExerciseType
from study_engine.pedagogy.student_context import get_student_context
from study_engine.session.study_session_contracts import PolicyDeniedError, SessionNotFoundError
from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/pedagogy", tags=["pedagogy"])


class StartEpisodeRequest(BaseModel):
    notebook_id: str = Field(..., min_length=1)
    kc_id: str = Field(..., min_length=1)
    episode_id: Optional[str] = None
    session_id: str = Field(..., min_length=1)


class RespondEpisodeRequest(BaseModel):
    step_id: str = Field(..., min_length=1)
    response_text: str = Field(...)
    session_id: str = Field(..., min_length=1)


@router.post("/episode/start")
def start_episode(
    req: StartEpisodeRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Start a validated interactive learning episode."""
    try:
        session_orchestrator = getattr(container, "study_session_orchestrator", None)
        if session_orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Persistencia de sesión no disponible.",
            )
        try:
            snapshot = session_orchestrator.get_snapshot(req.session_id)
        except SessionNotFoundError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="session_id no corresponde a una sesión persistida.",
            ) from err
        if snapshot.notebook_id != req.notebook_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La sesión no pertenece al cuaderno solicitado.",
            )
        episode, title = container.pedagogical_orchestrator.start_episode(
            notebook_id=req.notebook_id,
            kc_id=req.kc_id,
            episode_id=req.episode_id,
            session_id=req.session_id,
        )
        return {
            "episode_id": episode.episode_id,
            "session_id": episode.session_id,
            "notebook_id": episode.notebook_id,
            "kc_id": episode.kc_id,
            "objective": title,
            "phase": episode.phase.value,
            "current_step_id": episode.current_step_id,
        }
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.get("/episode/{episode_id}/concept")
def get_concept_explanation(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Obtain multi-source integrated explanation approved by S4.4 (or explicit ABSTAINED)."""
    concept_resp = container.pedagogical_orchestrator.explain_concept(episode_id)
    return concept_resp.to_dict()


@router.get("/episode/{episode_id}/next")
def get_next_intervention(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Fetch next deterministic action (presents QUALIFIABLE exercise or next phase)."""
    try:
        return container.study_session_orchestrator.next_intervention(episode_id)
    except PolicyDeniedError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/episode/{episode_id}/respond")
def respond_intervention(
    episode_id: str,
    req: RespondEpisodeRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Submit answer for deterministic evaluation with strict idempotency and BKT update."""
    orchestrator = container.pedagogical_orchestrator
    episode = orchestrator.get_episode(episode_id)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episodio '{episode_id}' no encontrado.",
        )
    if not episode.session_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El episodio no está vinculado a una sesión persistente; evaluación bloqueada.",
        )
    if req.session_id != episode.session_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="session_id no coincide con la identidad persistida del episodio.",
        )
    session_orchestrator = getattr(container, "study_session_orchestrator", None)
    if session_orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistencia de sesión no disponible.",
        )
    try:
        session_snapshot = session_orchestrator.get_snapshot(req.session_id)
    except SessionNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión persistida no existe o no pudo restaurarse.",
        ) from err
    except PolicyDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El estado persistido de la sesión es irreconciliable: {err}",
        ) from err
    if session_snapshot.notebook_id != episode.notebook_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión persistida no corresponde al cuaderno del episodio.",
        )
    active_episode_id = getattr(session_snapshot, "episode_id", None)
    if active_episode_id is not None and active_episode_id != episode_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="episode_id no coincide con el episodio activo de la sesión.",
        )
    if req.step_id != episode.current_step_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="step_id no coincide con el paso de evaluación activo del episodio.",
        )

    # Resolve the exact server-certified exercise named by the active step.
    if not req.step_id.startswith("step_eval_"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El paso activo no contiene una identidad de ejercicio verificable.",
        )
    exercise_id = req.step_id.removeprefix("step_eval_")
    exercise = container.exercise_store.get_evaluable_exercise_by_id(exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No hay ejercicio activo para el KC '{episode.kc_id}'.",
        )
    if exercise.kc_id != episode.kc_id or episode.current_step_id != f"step_eval_{exercise.exercise_id}":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ejercicio activo no coincide con la identidad certificada del episodio.",
        )

    # Deterministic grading
    if exercise.exercise_type == ExerciseType.MC:
        grade_res = container.mc_grader.grade(
            selected_option=req.response_text,
            expected_option=exercise.expected_answer,
        )
        n_options = len(exercise.options) if exercise.options else 4
    else:
        grade_res = container.exact_grader.grade(
            student_answer=req.response_text,
            expected_answer=exercise.expected_answer,
            exercise_type=exercise.exercise_type,
        )
        n_options = None

    # Idempotent mutation of BKT
    try:
        storage = container.observation_bridge.storage
        session_orchestrator = container.study_session_orchestrator
        with storage.transaction():
            try:
                session_orchestrator.require_open_session(req.session_id)
            except (PolicyDeniedError, SessionNotFoundError) as err:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="La sesión está cerrada; evaluación rechazada.",
                ) from err
            new_state, was_new_obs = container.observation_bridge.process_grade(
                session_id=episode.session_id,
                episode_id=episode_id,
                step_id=req.step_id,
                exercise_id=exercise.exercise_id,
                kc_id=episode.kc_id,
                grade_result=grade_res,
                n_options=n_options,
                # H7 defines quality for numeric/symbolic and closed-choice, not exact prose recall.
                anchor_id=episode.kc_id if exercise.exercise_type in (ExerciseType.NUMERIC, ExerciseType.MC) else None,
            )
            if was_new_obs:
                receipt = storage.get_operation_receipt(
                    session_id=episode.session_id, episode_id=episode_id,
                    exercise_id=exercise.exercise_id, attempt_id=req.step_id,
                )
                storage.store_operation_receipt(
                    session_id=episode.session_id, episode_id=episode_id,
                    exercise_id=exercise.exercise_id, attempt_id=f"advance:{req.step_id}",
                    request_digest=receipt[0],
                    result_json=json.dumps({
                        "is_correct": grade_res.is_correct, "kc_id": episode.kc_id,
                        "p_L": new_state.p_L, "attempts": new_state.attempts,
                    }),
                )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La identidad del intento ya fue utilizada con otro resultado.",
        ) from exc

    # Deterministic next eligible action recommendation
    next_action = orchestrator.get_next_eligible_action(
        notebook_id=episode.notebook_id,
        current_kc_id=episode.kc_id,
        correct=grade_res.is_correct,
    )

    return {
        "episode_id": episode_id,
        "session_id": episode.session_id,
        "exercise_id": exercise.exercise_id,
        "step_id": req.step_id,
        "is_correct": grade_res.is_correct,
        "raw_answer": grade_res.raw_answer,
        "normalized_answer": grade_res.normalized_answer,
        "feedback": grade_res.feedback,
        "was_idempotent_replay": not was_new_obs,
        "bkt_update": {
            "kc_id": new_state.kc_id,
            "p_L": new_state.p_L,
            "attempts": new_state.attempts,
        },
        "next_eligible_action": next_action,
    }


@router.get("/notebook/{notebook_id}/kcs")
def get_notebook_kcs(
    notebook_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """List KCs of notebook with consultive student context and authoritative BKT states."""
    if not container.notebook_registry.validate_notebook_scope(notebook_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook '{notebook_id}' no encontrado o inactivo.",
        )

    nb_data = container.pedagogical_orchestrator._kc_catalog.get(notebook_id, {})
    raw_kcs = nb_data.get("kcs", [])

    # Enrich KCs with authoritative BKT and consultive context strictly separated
    kcs_out = []
    for k in raw_kcs:
        kc_id = k["kc_id"]
        bkt_state = container.bkt_tracker.get_state(kc_id)
        kcs_out.append({
            "kc_id": kc_id,
            "title": k["title"],
            "unit": k.get("unit", 1),
            "priority": k.get("priority", "Media"),
            "prerequisites": k.get("prerequisites", []),
            "contextual_status": k.get("contextual_status", "Pendiente"),  # Consultive
            "bkt": {  # Authoritative
                "p_L": bkt_state.p_L,
                "attempts": bkt_state.attempts,
            },
        })

    consultive_ctx = get_student_context(notebook_id)

    return {
        "notebook_id": notebook_id,
        "name": nb_data.get("name", notebook_id),
        "curriculum_id": nb_data.get("curriculum_id", ""),
        "kcs": kcs_out,
        "consultive_student_context": consultive_ctx.to_dict(),
    }
