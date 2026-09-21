"""StudySessionOrchestrator for Unified Study Session (Directiva Final v2).

INVARIANTS:
1. UNA SESIÓN, UNA AUTORIDAD: Único orquestador de la sesión de estudio.
2. VALIDACIÓN FUERTE EN 7 PASOS antes de ejecutar cualquier acción.
3. EL FRONTEND PROPONE; EL BACKEND AUTORIZA.
4. DERIVE SNAPSHOT: El snapshot es derivado del estado autoritativo e inmutable.
5. PERSISTENCIA: Las sesiones sobreviven reinicios del servidor vía SQLite.
"""

import dataclasses
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.federation.notebook_registry import NotebookRegistry
from study_engine.pedagogy.episode_contracts import EpisodePhase
from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator
from study_engine.pedagogy.student_context import get_student_context
from study_engine.session.opening_brief_builder import OpeningBriefBuilder
from study_engine.session.progression_policy import ProgressionPolicy
from study_engine.session.session_store import SessionStore
from study_engine.session.study_session_contracts import (
    ActionNotAllowedForPhaseError,
    ActionNotAvailableError,
    AuthoritativeSessionState,
    CurriculumPosition,
    InvalidPayloadError,
    OpeningBriefFacts,
    PolicyDeniedError,
    SessionNotFoundError,
    StudySessionSnapshot,
)
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage

logger = logging.getLogger(__name__)


class StudySessionOrchestrator:
    """Orquestador autoritativo soberano de sesiones de estudio."""

    def __init__(
        self,
        notebook_registry: NotebookRegistry,
        pedagogical_orchestrator: PedagogicalOrchestrator,
        student_storage: Optional[StudentStorage] = None,
        progression_policy: Optional[ProgressionPolicy] = None,
        opening_brief_builder: Optional[OpeningBriefBuilder] = None,
        session_store: Optional[SessionStore] = None,
    ) -> None:
        self.notebook_registry = notebook_registry
        self.pedagogical_orchestrator = pedagogical_orchestrator
        self.student_storage = student_storage
        self.progression_policy = progression_policy or ProgressionPolicy()
        self.brief_builder = opening_brief_builder or OpeningBriefBuilder(self.progression_policy)
        self.session_store = session_store or SessionStore()

        # Repositorio autoritativo en memoria: session_id -> AuthoritativeSessionState
        self._sessions: Dict[str, AuthoritativeSessionState] = {}

        # Rehidratar sesiones activas desde SQLite (Fix 1)
        self._rehydrate_sessions()

    def _serialize_state(self, state: AuthoritativeSessionState) -> Dict:
        """Convert an AuthoritativeSessionState to a JSON-serializable dict."""
        d = dataclasses.asdict(state)
        # datetime objects need to be ISO strings for JSON
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d

    def _rehydrate_sessions(self) -> None:
        """Reload non-closed sessions from SQLite into the in-memory dict on startup."""
        try:
            blobs = self.session_store.load_all_active()
        except Exception as exc:
            logger.warning("StudySessionOrchestrator: could not rehydrate sessions — %s", exc)
            return

        for blob in blobs:
            try:
                sid = blob["session_id"]
                # Reconstruct the frozen dataclass from the persisted dict.
                # We only need enough to answer get_snapshot() / execute_action().
                # OpeningBriefFacts and CurriculumPosition are nested dataclasses;
                # restore them via their constructors from the stored dict.
                cp_d = blob["opening_brief_facts"]["curriculum_position"]
                curriculum_pos = CurriculumPosition(
                    unit_or_module=cp_d.get("unit_or_module", ""),
                    unit_name=cp_d.get("unit_name", ""),
                    kcs_in_unit=tuple(cp_d.get("kcs_in_unit", [])),
                    kcs_completed=tuple(cp_d.get("kcs_completed", [])),
                    kcs_in_progress=tuple(cp_d.get("kcs_in_progress", [])),
                    kcs_pending=tuple(cp_d.get("kcs_pending", [])),
                )
                obf_d = blob["opening_brief_facts"]
                opening_facts = OpeningBriefFacts(
                    notebook_id=obf_d.get("notebook_id", ""),
                    notebook_name=obf_d.get("notebook_name", ""),
                    notebook_purpose=obf_d.get("notebook_purpose", ""),
                    curriculum_position=curriculum_pos,
                    eligible_kcs=tuple(obf_d.get("eligible_kcs", [])),
                    selected_kc=obf_d.get("selected_kc", ""),
                    selected_kc_rationale=obf_d.get("selected_kc_rationale", ""),
                    bkt_estimate=obf_d.get("bkt_estimate", 0.0),
                    bkt_note=obf_d.get("bkt_note", ""),
                    student_context=None,  # consultive — rebuilt fresh when needed
                    student_context_note=obf_d.get("student_context_note", ""),
                    proposed_action=obf_d.get("proposed_action", ""),
                    proposed_action_rationale=obf_d.get("proposed_action_rationale", ""),
                    selected_kc_display_name=obf_d.get("selected_kc_display_name", obf_d.get("selected_kc", "")),
                )
                created_at_raw = blob.get("created_at", datetime.now(timezone.utc).isoformat())
                if isinstance(created_at_raw, str):
                    try:
                        created_at = datetime.fromisoformat(created_at_raw)
                    except ValueError:
                        created_at = datetime.now(timezone.utc)
                else:
                    created_at = created_at_raw

                state = AuthoritativeSessionState(
                    session_id=sid,
                    notebook_id=blob["notebook_id"],
                    student_id=blob.get("student_id", CANONICAL_STUDENT_ID),
                    created_at=created_at,
                    curriculum_id=blob.get("curriculum_id", f"curr_{blob['notebook_id']}"),
                    current_kc_id=blob.get("current_kc_id", ""),
                    episode_id=blob.get("episode_id"),
                    episode_phase=blob.get("episode_phase", "OPENING_BRIEF"),
                    available_actions=tuple(blob.get("available_actions", [])),
                    bkt_state_ref=blob.get("bkt_state_ref", ""),
                    student_context_ref=blob.get("student_context_ref"),
                    opening_brief_facts=opening_facts,
                    opening_brief_narrative=blob.get("opening_brief_narrative"),
                    state_hash=blob.get("state_hash", ""),
                )
                self._sessions[sid] = state
            except Exception as exc:
                logger.warning("StudySessionOrchestrator: could not rehydrate session %s — %s",
                               blob.get("session_id", "?"), exc)

        if self._sessions:
            logger.info("StudySessionOrchestrator: rehydrated %d active session(s) from SQLite.",
                        len(self._sessions))

    def _get_bkt_states(self) -> Dict[str, BKTState]:
        """Obtiene estados BKT del almacenamiento de estudiantes o tracker soberano."""
        if self.student_storage and hasattr(self.student_storage, "get_all_bkt_states"):
            try:
                states = self.student_storage.get_all_bkt_states()
                if states:
                    return states
            except Exception:
                pass
        if hasattr(self.pedagogical_orchestrator, "bkt_tracker") and self.pedagogical_orchestrator.bkt_tracker:
            try:
                # Si el tracker tiene storage subyacente
                return self.pedagogical_orchestrator.bkt_tracker.storage.get_all_bkt_states()
            except Exception:
                pass
        return {}

    def get_snapshot(self, session_id: str) -> StudySessionSnapshot:
        """Obtiene el snapshot derivado de la sesión o lanza SessionNotFoundError."""
        state = self._sessions.get(session_id)
        if state is None:
            raise SessionNotFoundError(session_id)
        return self.derive_snapshot(state)

    def derive_snapshot(self, state: AuthoritativeSessionState) -> StudySessionSnapshot:
        """Deriva un snapshot inmutable desde el estado autoritativo."""
        bkt_states = self._get_bkt_states()
        kc_bkt = bkt_states.get(state.current_kc_id)
        if kc_bkt is None and hasattr(self.pedagogical_orchestrator, "bkt_tracker") and self.pedagogical_orchestrator.bkt_tracker:
            try:
                kc_bkt = self.pedagogical_orchestrator.bkt_tracker.get_state(state.current_kc_id)
            except Exception:
                pass
        bkt_val = kc_bkt.p_L if kc_bkt is not None else 0.0
        attempts = kc_bkt.attempts if kc_bkt is not None else 0
        bkt_note = f"Estimación probabilística basada en {attempts} observaciones deterministas."

        # Consultar si hay ejercicio disponible en el episodio actual
        exercise_available = False
        exercise_type = None
        episode_phase = state.episode_phase

        if state.episode_id:
            ep = self.pedagogical_orchestrator.get_episode(state.episode_id)
            if ep:
                episode_phase = ep.phase.value if hasattr(ep.phase, "value") else str(ep.phase)
                # Si está en evaluación o sugerencia de ejercicio
                if episode_phase in ("SUGGEST_EXERCISE", "EVALUATING"):
                    exercise_available = True
                    exercise_type = "QUALIFIABLE_EXACT"

        # Contexto consultivo
        student_ctx = state.opening_brief_facts.student_context
        ctx_note = state.opening_brief_facts.student_context_note

        # Nombre legible para UI
        nb_catalog = getattr(self.pedagogical_orchestrator, "_kc_catalog", {}).get(state.notebook_id, {})
        kcs_list = nb_catalog.get("kcs", [])
        current_kc_name = state.current_kc_id
        for kc_item in kcs_list:
            if kc_item.get("kc_id") == state.current_kc_id:
                current_kc_name = kc_item.get("display_name") or kc_item.get("title") or state.current_kc_id
                break

        return StudySessionSnapshot(
            session_id=state.session_id,
            notebook_id=state.notebook_id,
            student_id=state.student_id,
            session_state_hash=state.state_hash,
            curriculum_position=state.opening_brief_facts.curriculum_position,
            eligible_kcs=state.opening_brief_facts.eligible_kcs,
            current_kc_id=state.current_kc_id,
            current_kc_name=current_kc_name,
            bkt_estimate=bkt_val,
            bkt_note=bkt_note,
            student_context=student_ctx,
            student_context_note=ctx_note,
            episode_id=state.episode_id,
            episode_phase=episode_phase,
            available_actions=state.available_actions,
            source_roles={s: "PRIMARY" for s in self.notebook_registry.get_sources_for_notebook(state.notebook_id)},
            evidence_status="VERIFIED_IN_CORPUS",
            exercise_available=exercise_available,
            exercise_type=exercise_type,
            opening_brief_facts=state.opening_brief_facts,
            opening_brief_narrative=state.opening_brief_narrative,
            derived_at=datetime.now(timezone.utc),
            policy_version=self.progression_policy.policy_version,
        )

    def open_session(
        self,
        notebook_id: str,
        student_id: str = CANONICAL_STUDENT_ID,
        session_id: Optional[str] = None,
    ) -> StudySessionSnapshot:
        """Abre una nueva sesión de estudio autoritativa y deriva el primer snapshot."""
        # Uso siempre el ID canónico (sistema single-user — Fix 4)
        canonical_sid = CANONICAL_STUDENT_ID

        # 1. Validar notebook
        notebook = self.notebook_registry.get_notebook(notebook_id)
        if not notebook:
            raise ValueError(f"Notebook '{notebook_id}' no encontrado o inactivo.")

        # 2. Cargar KCs del catálogo pedagógico
        nb_catalog = self.pedagogical_orchestrator._kc_catalog.get(notebook_id, {})
        curriculum_kcs = nb_catalog.get("kcs", [])
        if not curriculum_kcs:
            # Fallback para cuadernos sin catálogo JSON explícito
            curriculum_kcs = [
                {"kc_id": f"{notebook_id}_core", "title": notebook.name, "unit": 1, "prerequisites": []}
            ]

        # 3. Consultar BKT y StudentContext
        bkt_states = self._get_bkt_states()
        student_ctx = get_student_context(notebook_id, student_id=canonical_sid)

        # 4. Construir OpeningBriefFacts (determinista) y narrativa opcional
        facts, narrative = self.brief_builder.build(
            notebook=notebook,
            curriculum_kcs=curriculum_kcs,
            bkt_states=bkt_states,
            student_context=student_ctx,
            unit_info=(f"Unidad 1", notebook.subject),
        )

        sid = session_id or f"sess_{notebook_id}_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        # Acciones iniciales permitidas en fase de bienvenida
        initial_actions = (
            "START_EXPLANATION",
            "REVIEW_PREREQUISITE",
            "SELECT_DIFFERENT_KC",
        )

        state_hash = AuthoritativeSessionState.compute_hash(
            session_id=sid,
            notebook_id=notebook_id,
            student_id=canonical_sid,
            current_kc_id=facts.selected_kc,
            episode_id=None,
            episode_phase="OPENING_BRIEF",
            available_actions=initial_actions,
        )

        authoritative_state = AuthoritativeSessionState(
            session_id=sid,
            notebook_id=notebook_id,
            student_id=canonical_sid,
            created_at=now,
            curriculum_id=nb_catalog.get("curriculum_id", f"curr_{notebook_id}"),
            current_kc_id=facts.selected_kc,
            episode_id=None,
            episode_phase="OPENING_BRIEF",
            available_actions=initial_actions,
            bkt_state_ref=facts.selected_kc,
            student_context_ref=canonical_sid,
            opening_brief_facts=facts,
            opening_brief_narrative=narrative,
            state_hash=state_hash,
        )

        self._sessions[sid] = authoritative_state

        # Persistir en SQLite para sobrevivir reinicios (Fix 1)
        try:
            self.session_store.upsert(self._serialize_state(authoritative_state))
        except Exception as exc:
            logger.warning("StudySessionOrchestrator: could not persist new session — %s", exc)

        return self.derive_snapshot(authoritative_state)

    def execute_action(
        self,
        session_id: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> StudySessionSnapshot:
        """Validación fuerte de 7 pasos antes de autorizar y ejecutar la acción propuesta."""
        # Paso 1: Sesión existe -> 404 si no
        state = self._sessions.get(session_id)
        if state is None:
            raise SessionNotFoundError(session_id)

        # Paso 2: Acción está disponible -> 400 si no
        if action not in state.available_actions:
            raise ActionNotAvailableError(action, state.available_actions)

        # Paso 3: Acción permitida para la fase actual -> 400 si no
        if not self._action_allowed_for_phase(action, state.episode_phase):
            raise ActionNotAllowedForPhaseError(action, state.episode_phase)

        # Paso 4: Payload schema válido -> 422 si no
        if payload is not None:
            self._validate_payload_schema(action, payload)

        # Paso 5: Política determinista autoriza -> 403 si no
        is_approved, deny_reason = self._policy_check(action, state, payload)
        if not is_approved:
            raise PolicyDeniedError(action, deny_reason or "Denegado por política.")

        # Paso 6: Ejecutar la transición de estado autoritativa
        updated_state = self._execute_transition(action, state, payload)
        self._sessions[session_id] = updated_state

        # Persistir en SQLite (Fix 1)
        try:
            self.session_store.upsert(self._serialize_state(updated_state))
        except Exception as exc:
            logger.warning("StudySessionOrchestrator: could not persist session after action — %s", exc)

        # Paso 7: Derivar y retornar el snapshot
        return self.derive_snapshot(updated_state)

    def _action_allowed_for_phase(self, action: str, phase: str) -> bool:
        """Valida que la acción corresponda formalmente al estado de la máquina FSM."""
        phase_actions_map = {
            "OPENING_BRIEF": {"START_EXPLANATION", "REVIEW_PREREQUISITE", "SELECT_DIFFERENT_KC"},
            "EXPLAINING": {"REQUEST_DIALOGUE", "SKIP_TO_EXERCISE", "REQUEST_EXAMPLE"},
            "DIALOGUE": {
                "SUBMIT_MESSAGE", "REQUEST_EXAMPLE", "REQUEST_REFORMULATION",
                "SKIP_TO_EXERCISE", "ACCEPT_EXERCISE", "REJECT_EXERCISE",
            },
            # Fix 7: DIALOGUE_LIMIT_REACHED ahora expone REQUEST_EXERCISE y CONTINUE_EXPLORATION
            # para que el estudiante pueda actuar sin quedarse bloqueado
            "DIALOGUE_LIMIT_REACHED": {
                "ACCEPT_EXERCISE", "REJECT_EXERCISE",
                "REQUEST_EXERCISE", "CONTINUE_EXPLORATION",
            },
            "SUGGEST_EXERCISE": {"ACCEPT_EXERCISE", "REJECT_EXERCISE", "REQUEST_EXPLANATION"},
            "EVALUATING": {"SUBMIT_ANSWER", "REQUEST_HINT"},
            "CLOSED": {"START_NEXT_KC", "REVIEW_TOPIC"},
        }
        allowed = phase_actions_map.get(phase, set())
        return action in allowed

    def _validate_payload_schema(self, action: str, payload: Dict[str, Any]) -> None:
        """Valida deterministamente el schema de datos según la acción."""
        if action == "SELECT_DIFFERENT_KC":
            if "kc_id" not in payload or not isinstance(payload["kc_id"], str):
                raise InvalidPayloadError(action, "Campo 'kc_id' requerido y debe ser string.")
        elif action == "SUBMIT_MESSAGE":
            if "message" not in payload or not isinstance(payload["message"], str) or not payload["message"].strip():
                raise InvalidPayloadError(action, "Campo 'message' requerido y no vacío.")
        elif action == "SUBMIT_ANSWER":
            if "answer" not in payload or not isinstance(payload["answer"], str) or not payload["answer"].strip():
                raise InvalidPayloadError(action, "Campo 'answer' requerido y no vacío.")

    def _policy_check(
        self,
        action: str,
        state: AuthoritativeSessionState,
        payload: Optional[Dict[str, Any]],
    ) -> Tuple[bool, Optional[str]]:
        """Verificación determinista de invariantes y prerequisitos."""
        if action == "SELECT_DIFFERENT_KC":
            target_kc = payload.get("kc_id", "") if payload else ""
            if target_kc not in state.opening_brief_facts.eligible_kcs:
                return False, f"El KC '{target_kc}' no está habilitado por prerequisitos."

        return True, None

    def _execute_transition(
        self,
        action: str,
        state: AuthoritativeSessionState,
        payload: Optional[Dict[str, Any]],
    ) -> AuthoritativeSessionState:
        """Aplica la transición de estado autoritativo determinista."""
        now = datetime.now(timezone.utc)

        if action == "START_EXPLANATION":
            # Iniciar episodio en PedagogicalOrchestrator
            episode, _ = self.pedagogical_orchestrator.start_episode(
                notebook_id=state.notebook_id,
                kc_id=state.current_kc_id,
            )
            # Invocar explicación conceptual con S4.4
            self.pedagogical_orchestrator.explain_concept(episode.episode_id)

            new_actions = ("REQUEST_DIALOGUE", "SKIP_TO_EXERCISE", "REQUEST_EXAMPLE")
            new_phase = "EXPLAINING"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                state.current_kc_id, episode.episode_id, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=state.current_kc_id,
                episode_id=episode.episode_id,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=state.bkt_state_ref,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        elif action == "REQUEST_DIALOGUE":
            ep = self.pedagogical_orchestrator.get_episode(state.episode_id) if state.episode_id else None
            if ep:
                try:
                    updated_ep = ep.transition_to(EpisodePhase.DIALOGUE, "req_dialogue")
                    self.pedagogical_orchestrator._active_episodes[state.episode_id] = updated_ep
                except Exception:
                    pass

            new_actions = ("SUBMIT_MESSAGE", "REQUEST_EXAMPLE", "REQUEST_REFORMULATION", "SKIP_TO_EXERCISE")
            new_phase = "DIALOGUE"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                state.current_kc_id, state.episode_id, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=state.current_kc_id,
                episode_id=state.episode_id,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=state.bkt_state_ref,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        elif action in ("SKIP_TO_EXERCISE", "ACCEPT_EXERCISE"):
            ep = self.pedagogical_orchestrator.get_episode(state.episode_id) if state.episode_id else None
            if ep:
                try:
                    updated_ep = ep.transition_to(EpisodePhase.EVALUATING, "step_eval")
                    self.pedagogical_orchestrator._active_episodes[state.episode_id] = updated_ep
                except Exception:
                    pass

            new_actions = ("SUBMIT_ANSWER", "REQUEST_HINT")
            new_phase = "EVALUATING"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                state.current_kc_id, state.episode_id, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=state.current_kc_id,
                episode_id=state.episode_id,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=state.bkt_state_ref,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        elif action == "REJECT_EXERCISE":
            ep = self.pedagogical_orchestrator.get_episode(state.episode_id) if state.episode_id else None
            if ep:
                try:
                    updated_ep = ep.transition_to(EpisodePhase.DIALOGUE, "reject_exercise")
                    self.pedagogical_orchestrator._active_episodes[state.episode_id] = updated_ep
                except Exception:
                    pass

            new_actions = ("SUBMIT_MESSAGE", "REQUEST_EXAMPLE", "REQUEST_REFORMULATION", "SKIP_TO_EXERCISE")
            new_phase = "DIALOGUE"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                state.current_kc_id, state.episode_id, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=state.current_kc_id,
                episode_id=state.episode_id,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=state.bkt_state_ref,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        elif action == "SELECT_DIFFERENT_KC":
            target_kc = payload.get("kc_id") if payload else state.current_kc_id
            new_actions = ("START_EXPLANATION", "REVIEW_PREREQUISITE", "SELECT_DIFFERENT_KC")
            new_phase = "OPENING_BRIEF"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                target_kc, None, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=target_kc,
                episode_id=None,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=target_kc,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        # Fix 7: DIALOGUE_LIMIT_REACHED → SUGGEST_EXERCISE (transición automática con REQUEST_EXERCISE)
        elif action == "REQUEST_EXERCISE":
            new_actions = ("ACCEPT_EXERCISE", "REJECT_EXERCISE")
            new_phase = "SUGGEST_EXERCISE"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                state.current_kc_id, state.episode_id, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=state.current_kc_id,
                episode_id=state.episode_id,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=state.bkt_state_ref,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        # Fix 7: DIALOGUE_LIMIT_REACHED → DIALOGUE (volver al diálogo libre sin ejercicio formal)
        elif action == "CONTINUE_EXPLORATION":
            new_actions = ("SUBMIT_MESSAGE", "REQUEST_EXAMPLE", "REQUEST_REFORMULATION", "SKIP_TO_EXERCISE")
            new_phase = "DIALOGUE"
            new_hash = AuthoritativeSessionState.compute_hash(
                state.session_id, state.notebook_id, state.student_id,
                state.current_kc_id, state.episode_id, new_phase, new_actions
            )
            return AuthoritativeSessionState(
                session_id=state.session_id,
                notebook_id=state.notebook_id,
                student_id=state.student_id,
                created_at=state.created_at,
                curriculum_id=state.curriculum_id,
                current_kc_id=state.current_kc_id,
                episode_id=state.episode_id,
                episode_phase=new_phase,
                available_actions=new_actions,
                bkt_state_ref=state.bkt_state_ref,
                student_context_ref=state.student_context_ref,
                opening_brief_facts=state.opening_brief_facts,
                opening_brief_narrative=state.opening_brief_narrative,
                state_hash=new_hash,
            )

        # Fallback neutro
        return state
