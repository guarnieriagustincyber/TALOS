import logging
import hashlib
import json
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


# M1-02 continuity cache: episode_id -> ConceptResponse APPROVED (PRESENTABLE).
# Solo respuestas con audit APPROVED se reutilizan; TTL acotado (30 min) alineado
# con _EPISODE_DIALOGUE_STATES; el packet mantiene su procedencia completa
# (reporte S4.4 + hashes) dentro del objeto reutilizado.
_EPISODE_CONCEPT_RESPONSES: TTLCache = TTLCache(maxsize=1000, ttl=1800.0)


def _load_or_reuse_concept_response(orch: Any, episode_id: str):
    """M1-02 (enmienda de rendimiento, continuidad): devolver el ConceptResponse
    ya APROBADO del mismo episode_id mientras no cambie la identidad del
    episodio ni la evidencia compilada. Regenerar la propuesta y re-auditar
    S4.4 en CADA turno (efecto medido d1/d2: 49.3s/74.2s por turno) duplica
    llamadas al proveedor y a NLI para contenido byte-idéntico ya verificado.

    Fail-closed: NUNCA se cachea una respuesta ABSTAINED/rechazada — esas se
    recomputan en cada turno; la cache sólo apunta a respuestas PRESENTABLE con
    packet (reporte S4.4 + assembly_hash viven dentro del packet, por lo que la
    reutilización conserva referencia y procedencia). Un fallo de explain_concept
    no se cachea y degrada como antes (concept_packet=None → diálogo se abstiene).
    """
    cached = _EPISODE_CONCEPT_RESPONSES.get(episode_id)
    if cached is not None:
        logger.debug("[DIALOGUE] concept cache hit para %s", episode_id)
        return cached
    try:
        concept_resp = orch.explain_concept(episode_id)
    except Exception as e:
        logger.warning(
            "explain_concept falló para '%s' (%s): el diálogo fallará cerrado.",
            episode_id, e,
        )
        return None
    if (
        getattr(concept_resp, "status", None) == "PRESENTABLE"
        and getattr(concept_resp, "packet", None) is not None
    ):
        _EPISODE_CONCEPT_RESPONSES[episode_id] = concept_resp
    return concept_resp


class DialogueMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


def require_active_episode_session(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> None:
    from study_engine.session.study_session_contracts import SessionNotFoundError, PolicyDeniedError
    episode = container.pedagogical_orchestrator.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episodio no encontrado.")
    try:
        snapshot = container.study_session_orchestrator.get_snapshot(episode.session_id)
    except (SessionNotFoundError, PolicyDeniedError) as err:
        raise HTTPException(status_code=409, detail="La sesión no está activa.") from err
    if snapshot.episode_id != episode_id or snapshot.notebook_id != episode.notebook_id:
        raise HTTPException(status_code=409, detail="El episodio no corresponde a la sesión activa.")


@router.post("", dependencies=[Depends(require_active_episode_session)])
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
            orch.save_episode(episode)
        except Exception as e:
            logger.warning("Fallo en transición de fase a DIALOGUE (%s): %s", episode_id, e)

    current_state = _EPISODE_DIALOGUE_STATES.get(
        episode_id,
        DialogueState(episode_id=episode_id),
    )

    # Obtener concept packet vigente (S4.2/S4.4). explain_concept es read-only
    # y fail-closed: si el audit rechaza, ConceptResponse.status=ABSTAINED y
    # packet=None, con lo cual el engine de diálogo también se abstiene.
    #
    # M1-02 (enmienda de rendimiento, continuidad): reutilizar el ConceptResponse
    # ya APROBADO del mismo episode_id mientras no cambie la identidad del
    # episodio ni la evidencia compilada. Regenerar la propuesta y re-auditar
    # S4.4 en CADA turno (efecto medido d1/d2: 49.3s/74.2s) duplica llamadas al
    # proveedor y a NLI para contenido byte-idéntico ya verificado. La cache
    # conserva referencia y procedencia (audit_report + assembly_hash viven
    # dentro del packet); NUNCA se cachea una respuesta ABSTAINED/rechazada:
    # esas se recomputan siempre (fail-closed de la vía de fallo).
    concept_resp = _load_or_reuse_concept_response(orch, episode_id)
    concept_packet = concept_resp.packet if concept_resp and concept_resp.packet else None

    # Procesar turno a través del engine de diálogo socrático
    resp = await container.dialogue_engine.process_turn(
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
            episode = episode.transition_to(EpisodePhase.DIALOGUE_LIMIT_REACHED, "step_dialogue_limit")
            orch.save_episode(episode)
        except Exception as e:
            logger.warning("Fallo en transición de fase a LIMIT_REACHED (%s): %s", episode_id, e)
    elif resp.status == "SUGGEST_EXERCISE":
        try:
            episode = episode.transition_to(EpisodePhase.SUGGEST_EXERCISE, "step_suggest_ex")
            orch.save_episode(episode)
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
            c.model_dump() for c in resp.citations
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


@router.post("/accept-exercise", dependencies=[Depends(require_active_episode_session)])
def accept_exercise(
    episode_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """El estudiante acepta la sugerencia de ejercicio -> transiciona a EVALUATING."""
    orch = container.pedagogical_orchestrator
    episode = orch.get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episodio '{episode_id}' no encontrado.")

    candidate = container.exercise_store.get_presentable_exercise_for_kc(episode.kc_id)
    if not candidate or not container.exercise_store.get_evaluable_exercise_by_id(candidate.exercise_id):
        return {
            "status": "NO_QUALIFIABLE_EXERCISE",
            "new_phase": episode.phase.value,
            "step_id": episode.current_step_id,
        }

    # The orchestrator records the selected exercise ID in the active episode.
    # A generic EVALUATING step is not proof that this exercise was presented.
    intervention = orch.get_next_intervention(episode_id)
    if intervention.get("intervention_type") != "EXERCISE":
        return {
            "status": "NO_QUALIFIABLE_EXERCISE",
            "new_phase": episode.phase.value,
            "step_id": episode.current_step_id,
        }
    presented = intervention["exercise"]
    if (
        presented.get("exercise_id") != candidate.exercise_id
        or presented.get("kc_id") != episode.kc_id
        or intervention.get("step_id") != f"step_eval_{candidate.exercise_id}"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identidad del ejercicio presentado no verificable.",
        )
    return {
        "status": "success",
        "new_phase": EpisodePhase.EVALUATING.value,
        "step_id": intervention["step_id"],
        "exercise_id": presented["exercise_id"],
        "kc_id": presented["kc_id"],
        "exercise_type": presented["exercise_type"],
        "options": presented["options"],
        "prompt": presented["prompt"],
    }


@router.post("/reject-exercise", dependencies=[Depends(require_active_episode_session)])
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
    container.pedagogical_orchestrator.save_episode(updated_ep)
    return {
        "status": "success",
        "new_phase": updated_ep.phase.value,
        "step_id": updated_ep.current_step_id,
    }


class SocraticEvaluationRequest(BaseModel):
    student_response: str = Field(..., min_length=1)
    exercise_id: Optional[str] = None
    session_id: Optional[str] = None
    attempt_id: Optional[str] = None
    kc_id: Optional[str] = None
    is_mc: Optional[bool] = None
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

    episode = None

    def ungraded(reason: str) -> Dict[str, Any]:
        # No consultar ni crear estado BKT cuando la identidad no es verificable.
        return {
            "status": "UNGRADED",
            "kc_id": episode.kc_id if episode else None,
            "is_correct": None,
            "feedback": reason,
            "hint": None,
            "hints": [],
            "generic_message": "Revisá el principio fundamental documentado en la bibliografía canónica del tema.",
            "p_L": None,
            "delta_p_L": 0.0,
            "attempts": None,
            "last_update": None,
        }

    orch = container.pedagogical_orchestrator
    episode = orch.get_episode(episode_id)
    if episode is None or episode.episode_id != episode_id:
        return ungraded("Episodio no verificable; evaluación omitida.")
    if not req.exercise_id:
        return ungraded("Falta la identidad del ejercicio presentado; evaluación omitida.")
    if not req.session_id or not req.attempt_id:
        return ungraded("Falta la identidad estable de sesión o intento; evaluación omitida.")
    if episode.session_id != req.session_id:
        return ungraded("La sesión no coincide con la identidad persistida del episodio; evaluación omitida.")
    session_orchestrator = getattr(container, "study_session_orchestrator", None)
    if session_orchestrator is None:
        return ungraded("La sesión persistida no está disponible; evaluación omitida.")
    try:
        session_snapshot = session_orchestrator.get_snapshot(req.session_id)
    except Exception:
        return ungraded("La sesión no existe o no se pudo rehidratar; evaluación omitida.")
    if session_snapshot.notebook_id != episode.notebook_id:
        return ungraded("La sesión no coincide con el cuaderno certificado del episodio.")
    storage = getattr(container, "student_storage", None)
    if storage is None:
        return ungraded("Persistencia idempotente no disponible; evaluación omitida.")

    exercise = container.exercise_store.get_evaluable_exercise_by_id(req.exercise_id)
    if exercise is None:
        return ungraded("Ejercicio inexistente o no certificado; evaluación omitida.")
    if (
        episode.phase != EpisodePhase.EVALUATING
        or episode.current_step_id != f"step_eval_{exercise.exercise_id}"
        or episode.kc_id != exercise.kc_id
        or (req.kc_id is not None and req.kc_id != exercise.kc_id)
    ):
        return ungraded("Ejercicio incompatible con el KC o episodio activo; evaluación omitida.")

    catalog = getattr(orch, "_kc_catalog", None)
    notebook = catalog.get(episode.notebook_id) if isinstance(catalog, dict) else None
    if not isinstance(notebook, dict) or exercise.kc_id not in {
        item.get("kc_id") for item in notebook.get("kcs", [])
        if isinstance(item, dict) and isinstance(item.get("kc_id"), str)
    }:
        return ungraded("KC ajeno al scope certificado del episodio; evaluación omitida.")

    target_kc = exercise.kc_id
    is_mc = exercise.exercise_type.value == "MC"
    n_options = len(exercise.options) if is_mc else None
    if req.is_mc is not None and req.is_mc != is_mc:
        return ungraded("Tipo de ejercicio incompatible; evaluación omitida.")
    if req.options_count is not None and req.options_count != n_options:
        return ungraded("Cantidad de opciones incompatible; evaluación omitida.")

    # 2. Calificación determinista autoritativa
    expected = exercise.expected_answer.strip()
    raw_ans = req.student_response.strip()

    if is_mc:
        grade_res = container.mc_grader.grade(raw_ans, expected)
    else:
        grade_res = container.exact_grader.grade(raw_ans, expected, exercise.exercise_type)

    is_correct = grade_res.is_correct

    fmt = ExerciseFormat.CLOSED_CHOICE if is_mc else ExerciseFormat.SYMBOLIC_OPEN
    hints: list[str] = []
    generic_msg: Optional[str] = None
    hint_to_return: Optional[str] = None

    if is_correct:
        feedback = "¡Correcto! Tu respuesta coincide con la opción esperada para este ejercicio."
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

        feedback = f"Respuesta incorrecta. No es del todo exacto. Pista: {hint_to_return} Volvé a intentarlo."

    request_identity = {
        "session_id": req.session_id,
        "episode_id": episode_id,
        "exercise_id": exercise.exercise_id,
        "attempt_id": req.attempt_id,
        "student_response": raw_ans,
        "kc_id": target_kc,
        "exercise_type": exercise.exercise_type.value,
        "options_count": n_options,
    }
    request_digest = hashlib.sha256(
        json.dumps(request_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    # BKT, SM-2, hint audit, and the replay receipt commit in one SQLite transaction.
    with storage.transaction():
        session_orchestrator.require_open_session(req.session_id)
        prior_receipt = storage.get_operation_receipt(
            session_id=req.session_id,
            episode_id=episode_id,
            exercise_id=exercise.exercise_id,
            attempt_id=req.attempt_id,
        )
        if prior_receipt is not None:
            stored_digest, stored_result = prior_receipt
            if stored_digest != request_digest:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="attempt_id ya fue usado con otro contenido dentro de esta sesión, episodio y ejercicio.",
                )
            if not stored_result:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El intento quedó incompleto; se bloquea su reejecución automática.",
                )
            replay = json.loads(stored_result)
            replay["was_idempotent_replay"] = True
            return replay

        prior_state = container.bkt_tracker.get_state(target_kc)
        bkt_res = container.bkt_tracker.update(
            kc_id=target_kc,
            correct=is_correct,
            source=ObservationSource.EXACT_CORRECTOR,
            format_type=fmt,
            n_options=n_options,
        )
        delta_p_L = round(bkt_res.p_L - prior_state.p_L, 4)

        scheduler = getattr(container, "spaced_scheduler", None)
        if scheduler is not None:
            scheduler.record_review(
                anchor_id=target_kc,
                correct=is_correct,
                format_type=fmt,
            )

        if not is_correct and hint_to_return:
            storage.record_hint(
                episode_id=episode_id,
                exercise_id=exercise.exercise_id,
                kc_id=target_kc,
                hint_level=1,
                hint_text=hint_to_return,
            )

        result = {
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
            "was_idempotent_replay": False,
        }
        storage.store_operation_receipt(
            session_id=req.session_id,
            episode_id=episode_id,
            exercise_id=exercise.exercise_id,
            attempt_id=req.attempt_id,
            request_digest=request_digest,
            result_json=json.dumps(result, sort_keys=True),
        )
        return result
