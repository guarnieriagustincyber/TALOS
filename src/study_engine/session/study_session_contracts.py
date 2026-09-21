"""Contracts and domain models for Unified Study Session (Directiva Final v2).

INVARIANTS:
1. UNA SESIÓN, UNA AUTORIDAD: No existe lógica paralela en el cliente.
2. SNAPSHOT DERIVADO: StudySessionSnapshot es derivado e inmutable.
3. BKT NO DEFINE CURRÍCULO: Roadmap + prerequisitos definen elegibilidad. BKT solo prioriza.
4. OBSERVACIÓN PRIMARIA: La evidencia primaria es la observación determinista.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from study_engine.pedagogy.student_context import StudentContext


@dataclass(frozen=True)
class CurriculumPosition:
    """Posición en el currículo. Determinada por roadmap + prerequisitos."""

    unit_or_module: str          # "Unidad 3" / "Módulo 2" / "Tramo 5"
    unit_name: str               # "Iniciación en C" / "Aritmética de Punteros"
    kcs_in_unit: Tuple[str, ...]
    kcs_completed: Tuple[str, ...]      # KCs con P(L) >= umbral de completitud
    kcs_in_progress: Tuple[str, ...]    # KCs con P(L) entre umbral bajo y alto
    kcs_pending: Tuple[str, ...]        # KCs con P(L) < umbral bajo


@dataclass(frozen=True)
class OpeningBriefFacts:
    """Hechos autoritativos del Opening Brief.
    
    Estos hechos son DETERMINISTAS e inmutables. El LLM solo puede redactar
    texto natural SOBRE estos hechos sin contradecirlos ni mutarlos.
    """

    notebook_id: str
    notebook_name: str
    notebook_purpose: str

    # Posición curricular (determinada por roadmap + prerequisitos, NO por BKT)
    curriculum_position: CurriculumPosition
    eligible_kcs: Tuple[str, ...]          # KCs habilitados por prerequisitos
    selected_kc: str                       # KC seleccionado por política de priorización
    selected_kc_rationale: str             # Por qué se seleccionó este KC

    # Estimación BKT (consultiva, no verdad)
    bkt_estimate: float
    bkt_note: str                          # "Estimación basada en N observaciones"

    # Contexto consultivo (de NotebookLM, NO es BKT)
    student_context: Optional[StudentContext]
    student_context_note: str              # "Contexto consultivo. No acredita dominio."

    # Próxima acción (determinada por política versionada)
    proposed_action: str
    proposed_action_rationale: str

    # Nombre legible del KC seleccionado para UI
    selected_kc_display_name: str = ""


@dataclass(frozen=True)
class ProgressionDecision:
    """Decisión de progresión pedagógica emitida por ProgressionPolicy."""

    action: str                            # "START_FOUNDATIONS" | "CONTINUE_CONSOLIDATION" | "ADVANCE_TO_NEXT" | "REVIEW_PREREQUISITE" | "SUGGEST_EXERCISE"
    rationale: str
    next_kc: Optional[str] = None
    policy_version: str = "v1.0"


@dataclass(frozen=True)
class AuthoritativeSessionState:
    """Estado autoritativo de la sesión. Fuente de verdad.
    
    El snapshot se DERIVA de esto. La sesión nunca se muta directamente
    desde el exterior.
    """

    session_id: str
    notebook_id: str
    student_id: str
    created_at: datetime

    # Currículo
    curriculum_id: str
    current_kc_id: str
    episode_id: Optional[str]
    episode_phase: str

    # Acciones disponibles en este estado
    available_actions: Tuple[str, ...]

    # Referencias de estado cognitivo y consultivo
    bkt_state_ref: str
    student_context_ref: Optional[str]

    # Hechos autoritativos
    opening_brief_facts: OpeningBriefFacts
    opening_brief_narrative: Optional[str]

    # Hash criptográfico de integridad
    state_hash: str

    @classmethod
    def compute_hash(
        cls,
        session_id: str,
        notebook_id: str,
        student_id: str,
        current_kc_id: str,
        episode_id: Optional[str],
        episode_phase: str,
        available_actions: Tuple[str, ...],
    ) -> str:
        payload = f"{session_id}:{notebook_id}:{student_id}:{current_kc_id}:{episode_id}:{episode_phase}:{','.join(available_actions)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StudySessionSnapshot:
    """Snapshot DERIVADO del estado autoritativo de la sesión.
    
    Se regenera en cada request. Nunca se modifica directamente.
    """

    session_id: str
    notebook_id: str
    student_id: str

    # Estado autoritativo (fuente de verdad)
    session_state_hash: str

    # Currículo
    curriculum_position: CurriculumPosition
    eligible_kcs: Tuple[str, ...]
    current_kc_id: str
    current_kc_name: str

    # Estado cognitivo (estimación consultiva)
    bkt_estimate: float
    bkt_note: str

    # Contexto consultivo
    student_context: Optional[StudentContext]
    student_context_note: str

    # Episodio actual
    episode_id: Optional[str]
    episode_phase: str

    # Acciones disponibles (determinadas por política)
    available_actions: Tuple[str, ...]

    # Fuentes y evidencia
    source_roles: Dict[str, str]
    evidence_status: str

    # Ejercicio
    exercise_available: bool
    exercise_type: Optional[str]

    # Opening Brief
    opening_brief_facts: Optional[OpeningBriefFacts]
    opening_brief_narrative: Optional[str]

    # Metadata
    derived_at: datetime
    policy_version: str


# Excepciones canónicas de la sesión de estudio
class SessionDomainError(Exception):
    """Excepción base del dominio de sesiones de estudio."""


class SessionNotFoundError(SessionDomainError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Sesión '{session_id}' no encontrada.")
        self.session_id = session_id


class ActionNotAvailableError(SessionDomainError):
    def __init__(self, action: str, available_actions: Tuple[str, ...]) -> None:
        super().__init__(f"Acción '{action}' no disponible. Acciones válidas: {list(available_actions)}")
        self.action = action
        self.available_actions = available_actions


class ActionNotAllowedForPhaseError(SessionDomainError):
    def __init__(self, action: str, phase: str) -> None:
        super().__init__(f"Acción '{action}' no permitida en la fase '{phase}'.")
        self.action = action
        self.phase = phase


class PolicyDeniedError(SessionDomainError):
    def __init__(self, action: str, reason: str) -> None:
        super().__init__(f"Acción '{action}' denegada por política determinista: {reason}")
        self.action = action
        self.reason = reason


class InvalidPayloadError(SessionDomainError):
    def __init__(self, action: str, details: str) -> None:
        super().__init__(f"Payload inválido para la acción '{action}': {details}")
        self.action = action
        self.details = details
