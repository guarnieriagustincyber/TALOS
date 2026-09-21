import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from study_engine.pedagogy.dialogue_contracts import DialogueState
from study_engine.pedagogy.episode_contracts import EpisodePhase
from study_engine.utils.cache import TTLCache
from study_engine.web.dependencies import AppContainer, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pedagogy/episode/{episode_id}/dialogue", tags=["pedagogy", "dialogue"])

# In-memory dialogue state per episode with TTL eviction: episode_id -> DialogueState
_EPISODE_DIALOGUE_STATES: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)


class DialogueMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("")
async def process_dialogue_turn(
    episode_id: str,
    req: DialogueMessageRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Procesa un turno del diálogo socrático."""
    orch = container.pedagogical_orchestrator
    episode = orch.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episodio '{episode_id}' no encontrado.")

    # Asegurar que el episodio esté en fase de diálogo
    if episode.phase not in (EpisodePhase.DIALOGUE, EpisodePhase.DIALOGUE_LIMIT_REACHED, EpisodePhase.SUGGEST_EXERCISE):
        try:
            episode = episode.transition_to(EpisodePhase.DIALOGUE, "step_dialogue_init")
        except Exception as e:
            logger.warning("Fallo en transición de fase a DIALOGUE (%s): %s", episode_id, e)

    current_state = _EPISODE_DIALOGUE_STATES.get(
        episode_id,
        DialogueState(episode_id=episode_id),
    )

    # Obtener concept packet previo si existe
    concept_resp = orch.get_concept_packet(episode_id)
    concept_packet = concept_resp.packet if concept_resp and concept_resp.packet else None

    # Procesar turno a través de la orquestación socrática
    resp = orch.process_dialogue_turn(
        episode=episode,
        concept_packet=concept_packet,
        dialogue_state=current_state,
        student_message=req.message,
    )

    if resp.dialogue_state:
        _EPISODE_DIALOGUE_STATES[episode_id] = resp.dialogue_state

    # Manejar transiciones
    if resp.status == "LIMIT_REACHED":
        try:
            episode.transition_to(EpisodePhase.DIALOGUE_LIMIT_REACHED, "step_dialogue_limit")
        except Exception as e:
            logger.warning("Fallo en transición de fase a LIMIT_REACHED (%s): %s", episode_id, e)
    elif resp.status == "SUGGEST_EXERCISE":
        try:
            episode.transition_to(EpisodePhase.SUGGEST_EXERCISE, "step_suggest_ex")
        except Exception as e:
            logger.warning("Fallo en transición de fase a SUGGEST_EXERCISE (%s): %s", episode_id, e)

    return {
        "status": resp.status,
        "answer": resp.answer,
        "socratic_question": (
            {
                "question_id": resp.socratic_question.question_id,
                "question_text": resp.socratic_question.question_text,
                "target_dimension": resp.socratic_question.target_dimension,
                "target_dimension_note": resp.socratic_question.target_dimension_note,
                "evidence_ids": list(resp.socratic_question.evidence_ids),
                "source_ids": list(resp.socratic_question.source_ids),
                "difficulty": resp.socratic_question.difficulty,
                "policy_rule_id": resp.socratic_question.policy_rule_id,
            }
            if resp.socratic_question
            else None
        ),
        "citations": [
            {
                "citation_id": c.citation_id,
                "source_id": c.source_id,
                "text_snippet": c.text_snippet,
                "authority_weight": c.authority_weight,
            }
            for c in resp.citations
        ],
        "dialogue_state": (
            {
                "episode_id": resp.dialogue_state.episode_id,
                "turn_count": resp.dialogue_state.turn_count,
                "dialogue_limit_reached": resp.dialogue_state.dialogue_limit_reached,
                "limit_reason": resp.dialogue_state.limit_reason,
                "confusion_count": resp.dialogue_state.confusion_count,
                "reformulation_count": resp.dialogue_state.reformulation_count,
                "examples_requested": resp.dialogue_state.examples_requested,
            }
            if resp.dialogue_state
            else None
        ),
        "audit_verdict": resp.audit_verdict,
        "abstention_reason": resp.abstention_reason,
    }


@router.get("/state")
def get_dialogue_state(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retorna el estado actual del diálogo."""
    state = _EPISODE_DIALOGUE_STATES.get(episode_id, DialogueState(episode_id=episode_id))
    return {
        "episode_id": state.episode_id,
        "turn_count": state.turn_count,
        "dialogue_limit_reached": state.dialogue_limit_reached,
        "limit_reason": state.limit_reason,
        "confusion_count": state.confusion_count,
        "reformulation_count": state.reformulation_count,
        "examples_requested": state.examples_requested,
    }


@router.get("/history")
def get_dialogue_history(
    episode_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retorna el historial de turnos con paginación opcional."""
    state = _EPISODE_DIALOGUE_STATES.get(episode_id, DialogueState(episode_id=episode_id))
    turns = state.turns[offset:]
    if limit is not None:
        turns = turns[:limit]
    return {
        "episode_id": episode_id,
        "turns": [
            {
                "turn_id": t.turn_id,
                "turn_number": t.turn_number,
                "student_message": t.student_message,
                "presented_response": t.presented_response,
                "presented_socratic_question": (
                    t.presented_socratic_question.question_text if t.presented_socratic_question else None
                ),
                "s44_verdict": t.s44_verdict,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in turns
        ],
    }


@router.post("/accept-exercise")
def accept_exercise(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """El estudiante acepta la sugerencia de ejercicio -> transiciona a EVALUATING."""
    orch = container.pedagogical_orchestrator
    episode = orch.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episodio '{episode_id}' no encontrado.")

    updated_ep = container.dialogue_engine.accept_exercise_suggestion(episode)
    return {
        "status": "success",
        "new_phase": updated_ep.phase.value,
        "step_id": updated_ep.current_step_id,
    }


@router.post("/reject-exercise")
def reject_exercise(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """El estudiante rechaza la sugerencia -> permanece en DIALOGUE."""
    orch = container.pedagogical_orchestrator
    episode = orch.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episodio '{episode_id}' no encontrado.")

    updated_ep = container.dialogue_engine.reject_exercise_suggestion(episode)
    return {
        "status": "success",
        "new_phase": updated_ep.phase.value,
        "step_id": updated_ep.current_step_id,
    }


class SocraticEvaluationRequest(BaseModel):
    student_response: str = Field(..., min_length=1)
    exercise_id: Optional[str] = None
    kc_id: Optional[str] = None
    is_mc: bool = False
    options_count: Optional[int] = None


def validate_hints_socratic(hints: list[str], expected_answer: str) -> tuple[list[str], bool]:
    """Valida que ninguna pista filtre la respuesta literal esperada (E11, E16).
    
    Retorna (validated_hints, all_rejected).
    Si all_rejected == True, el llamador debe emitir un mensaje genérico.
    """
    import difflib

    validated_hints: list[str] = []
    norm_expected = " ".join(expected_answer.strip().lower().split())

    for h in hints:
        norm_h = " ".join(h.strip().lower().split())
        # 1. Chequeo de subcadena directa o palabra exacta
        if norm_expected in norm_h:
            logger.warning("Pista descartada por contener respuesta literal: %s", h[:60])
            continue

        # 2. Chequeo de similitud > 70%
        ratio = difflib.SequenceMatcher(None, norm_h, norm_expected).ratio()
        if ratio > 0.70:
            logger.warning("Pista descartada por alta similitud (%.2f) con respuesta: %s", ratio, h[:60])
            continue

        validated_hints.append(h)

    all_rejected = len(validated_hints) == 0 and len(hints) > 0
    return validated_hints, all_rejected


@router.post("/evaluate-socratic")
def evaluate_socratic_response(
    episode_id: str,
    req: SocraticEvaluationRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Evalúa la respuesta del estudiante contra un ejercicio certificado en el backend y actualiza BKT."""
    from study_engine.student.contracts import ExerciseFormat, ObservationSource

    orch = container.pedagogical_orchestrator
    episode = orch.get_episode(episode_id)
    target_kc = req.kc_id or (episode.kc_id if episode else None)
    if not target_kc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="kc_id es requerido para actualizar el estado BKT.",
        )

    # 1. Resolución autoritativa del ejercicio certificado en el backend
    exercise = None
    if req.exercise_id:
        exercise = container.exercise_store.get_exercise_by_id(req.exercise_id)
    elif target_kc:
        exercise = container.exercise_store.get_presentable_exercise_for_kc(target_kc)
        if not exercise and hasattr(container.exercise_store, "list_all"):
            # Búsqueda por prefijo de ámbito de cuaderno (ej: "fase0-soc" -> "fase0-soc-kc-01")
            candidates = [
                c for c in container.exercise_store.list_all()
                if (c.kc_id.startswith(f"{target_kc}-") or target_kc in c.kc_id) and c.is_presentable()
            ]
            if req.is_mc:
                # Si la solicitud es de opción múltiple, priorizar un ejercicio MC
                for cand in candidates:
                    cand_type = getattr(cand.exercise_type, "value", str(cand.exercise_type))
                    if cand_type == "MC":
                        exercise = cand
                        target_kc = cand.kc_id
                        break
            if not exercise and candidates:
                exercise = candidates[0]
                target_kc = exercise.kc_id

    if not exercise or not getattr(exercise, "expected_answer", None):
        # FAIL-CLOSED (Fix S1.2, E13): Sin clave certificada en backend, retornar UNGRADED sin mutar BKT
        current_state = container.bkt_tracker.get_state(target_kc)
        return {
            "status": "UNGRADED",
            "kc_id": target_kc,
            "is_correct": None,
            "feedback": (
                "Respuesta registrada. Este desafío reflexivo no posee clave determinista "
                "certificada en el backend; el estado BKT permanece inalterado."
            ),
            "hint": None,
            "hints": [],
            "generic_message": "Revisá el principio fundamental documentado en la bibliografía canónica del tema.",
            "p_L": round(current_state.p_L, 4),
            "delta_p_L": 0.0,
            "attempts": current_state.attempts,
            "last_update": current_state.last_update.isoformat(),
        }

    # 2. Calificación determinista autoritativa
    expected = exercise.expected_answer.strip()
    raw_ans = req.student_response.strip()
    is_mc = req.is_mc or (getattr(exercise.exercise_type, "value", str(exercise.exercise_type)) == "MC")

    if is_mc:
        grade_res = container.mc_grader.grade(raw_ans, expected)
    else:
        grade_res = container.exact_grader.grade(raw_ans, expected)

    is_correct = grade_res.is_correct

    # Estado previo para calcular delta
    prior_state = container.bkt_tracker.get_state(target_kc)
    prior_p_L = prior_state.p_L

    # 3. Actualización determinista en BKT (Corbett & Anderson 1995)
    fmt = ExerciseFormat.CLOSED_CHOICE if is_mc else ExerciseFormat.SYMBOLIC_OPEN
    bkt_res = container.bkt_tracker.update(
        kc_id=target_kc,
        correct=is_correct,
        source=ObservationSource.EXACT_CORRECTOR,
        format_type=fmt,
        n_options=req.options_count or (len(exercise.options) if exercise.options else (4 if is_mc else None)),
    )
    delta_p_L = round(bkt_res.p_L - prior_p_L, 4)

    # 4. Actualización en SM-2 (Spaced Repetition) si la respuesta es calificada (E14)
    if hasattr(container, "spaced_scheduler") and container.spaced_scheduler:
        try:
            container.spaced_scheduler.record_review(
                anchor_id=target_kc,
                correct=is_correct,
                format_type=fmt,
            )
        except Exception as sm2_err:
            logger.warning("Fallo al actualizar SM-2 (%s): %s", target_kc, sm2_err)

    # 5. Generación y validación estricta de pistas (E11, E16)
    hints: list[str] = []
    generic_msg: Optional[str] = None
    hint_to_return: Optional[str] = None

    if is_correct:
        feedback = "¡Correcto! Razonamiento verificado con éxito contra el corpus epistemológico."
    else:
        candidate_hints: list[str] = []
        sol_exp = getattr(exercise, "solution_explanation", "") or ""
        if sol_exp:
            sentences = [s.strip() for s in sol_exp.split(".") if s.strip() and len(s.strip()) > 10]
            candidate_hints.extend(sentences)

        validated_hints, all_rejected = validate_hints_socratic(candidate_hints, expected)
        generic_msg = "Revisá el principio fundamental documentado en la bibliografía canónica del tema."

        if all_rejected or not validated_hints:
            hints = []
            hint_to_return = generic_msg
        else:
            hints = validated_hints
            hint_to_return = validated_hints[0]

        # 6. Trazabilidad de Pistas (E15, E18)
        if hasattr(container, "student_storage") and container.student_storage and hint_to_return:
            try:
                container.student_storage.record_hint(
                    episode_id=episode_id,
                    exercise_id=exercise.exercise_id,
                    kc_id=target_kc,
                    hint_level=1,
                    hint_text=hint_to_return,
                )
            except Exception as hint_err:
                logger.warning("Fallo al registrar student_hint: %s", hint_err)

        feedback = f"Respuesta incorrecta. No es del todo exacto. Pista: {hint_to_return} Volvé a intentarlo."

    return {
        "status": "EVALUATED",
        "kc_id": target_kc,
        "exercise_id": exercise.exercise_id,
        "is_correct": is_correct,
        "feedback": feedback,
        "hint": hint_to_return,
        "hints": hints,
        "generic_message": generic_msg,
        "normalization_policy": getattr(grade_res, "normalization_policy", None),
        "comparison_result": getattr(grade_res, "comparison_result", None),
        "p_L": round(bkt_res.p_L, 4),
        "delta_p_L": delta_p_L,
        "attempts": bkt_res.attempts,
        "last_update": bkt_res.last_update.isoformat(),
    }


