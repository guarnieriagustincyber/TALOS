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
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from study_engine.pedagogy.exercise_contracts import ExerciseType
from study_engine.pedagogy.student_context import get_student_context
from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/pedagogy", tags=["pedagogy"])


class StartEpisodeRequest(BaseModel):
    notebook_id: str = Field(..., min_length=1)
    kc_id: str = Field(..., min_length=1)
    episode_id: Optional[str] = None


class RespondEpisodeRequest(BaseModel):
    step_id: str = Field(..., min_length=1)
    response_text: str = Field(...)


@router.post("/episode/start")
def start_episode(
    req: StartEpisodeRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Start a validated interactive learning episode."""
    try:
        episode, title = container.pedagogical_orchestrator.start_episode(
            notebook_id=req.notebook_id,
            kc_id=req.kc_id,
            episode_id=req.episode_id,
        )
        return {
            "episode_id": episode.episode_id,
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
        return container.pedagogical_orchestrator.get_next_intervention(episode_id)
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

    # Fetch active exercise for the step
    exercise = container.exercise_store.get_presentable_exercise_for_kc(episode.kc_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No hay ejercicio activo para el KC '{episode.kc_id}'.",
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
    new_state, was_new_obs = container.observation_bridge.process_grade(
        episode_id=episode_id,
        step_id=req.step_id,
        kc_id=episode.kc_id,
        grade_result=grade_res,
        n_options=n_options,
    )

    # Deterministic next eligible action recommendation
    next_action = orchestrator.get_next_eligible_action(
        notebook_id=episode.notebook_id,
        current_kc_id=episode.kc_id,
    )

    return {
        "episode_id": episode_id,
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
