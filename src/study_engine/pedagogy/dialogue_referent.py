"""EP-01 / H1-A: resolución del referente académico antes de reutilizar un episodio.

Regla (autorización propietaria 2026-10-21, EP-01):

> Una delegación de seguimiento conversacional hacia el diálogo de un episodio
> sólo es admisible cuando el referente académico inmediato del estudiante
> queda verificado como el referente vigente del episodio. Ante tema distinto,
> referencia de actividad, identidad incompatible o ambigüedad mismo-KC sin
> desempate determinista, NO se reutiliza silenciosamente el episodio.

Cuatro situaciones (directiva EP-01 §3):
  A. Continuación verificada        → DELEGATE (continuar el episodio).
  B. Cambio explícito de tema       → CHAT_ROUTE (pipeline normal del chat).
  C. Referente ambiguo              → CLARIFY (aclaración breve; no inventar).
  D. Contexto obsoleto/incompatible → CHAT_ROUTE (rechazar reutilización).

Este módulo es política pura y determinista: recibe evidencia ya recolectada
(matching de KC, identidad, turnos de conversación) y clasifica. No hace I/O,
no recupera contenido, no genera texto académico y no toca estado pedagógico.

Advertencia de diseño (directiva §2): NO asumir que comparar únicamente KC y
episode_id resuelve el referente. Dos explicaciones distintas pueden compartir
KC; un episodio activo puede estar desactualizado frente al tema inmediato.
Por eso el mismo KC con dos explicaciones candidatas (turno del chat vs packet
del episodio) clasifica como ambiguo (CLARIFY), nunca como coincidencia.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Códigos de razón (trazabilidad de la decisión; no son autoridad adicional).
REASON_SESSION_STUDENT_MISMATCH = "SESSION_STUDENT_MISMATCH"
REASON_EPISODE_IDENTITY_UNKNOWN = "EPISODE_IDENTITY_UNKNOWN"
REASON_SCOPE_NOTEBOOK_MISMATCH = "SCOPE_NOTEBOOK_MISMATCH"
REASON_SESSION_EPISODE_KC_MISMATCH = "SESSION_EPISODE_KC_MISMATCH"
REASON_ACTIVITY_REFERENCE = "ACTIVITY_REFERENCE"
REASON_EXPLICIT_EPISODE_TOPIC = "EXPLICIT_EPISODE_TOPIC"
REASON_EXPLICIT_OTHER_TOPIC = "EXPLICIT_OTHER_TOPIC"
REASON_CHAT_REFERENT_OTHER_KC = "CHAT_REFERENT_OTHER_KC"
REASON_CHAT_REFERENT_SAME_KC = "CHAT_REFERENT_SAME_KC"
REASON_EPISODE_TURN_CONTINUATION = "EPISODE_TURN_CONTINUATION"
REASON_NO_COMPETING_REFERENT = "NO_COMPETING_REFERENT"

CLARIFICATION_ABN_CODE = "CONTEXT_REFERENCE_REQUIRES_CLARIFICATION"


class ReferentDecision(str, Enum):
    """Resultado de la resolución del referente para la delegación.

    DELEGATE   → A: el episodio es el referente verificado; continuar su diálogo.
    CHAT_ROUTE → B/D: no reutilizar el episodio; el pipeline del chat procesa.
    CLARIFY    → C: referente ambiguo; pedir aclaración breve sin inventar.
    """

    DELEGATE = "delegate"
    CHAT_ROUTE = "chat_route"
    CLARIFY = "clarify"


def resolve_recent_referent(
    turns: List[Dict[str, Any]],
    match_kc: Callable[[str], Optional[str]],
) -> Optional[Dict[str, Any]]:
    """Retorna el descriptor del turno académico más reciente de la conversación.

    Escanea desde el turno más reciente hacia atrás y retorna el primero que
    sea un turno de diálogo de episodio (marcado con ``episode_id``) o que
    matchee un KC del catálogo aplicable. Los turnos no académicos (saludos,
    abstenciones, registro administrativo) se ignoran: no desplazan ni borran
    el referente académico previo.

    El marcado ``episode_id``/``kc_id`` sólo lo produce el propio servidor al
    delegar un turno (registro del lado del servidor); los turnos aportados
    por el cliente no llevan marcador y se tratan como turnos del chat.
    """
    for turn in reversed(turns or []):
        if not isinstance(turn, dict):
            continue
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        episode_id = turn.get("episode_id")
        if isinstance(episode_id, str) and episode_id.strip():
            return {
                "kind": "episode_turn",
                "episode_id": episode_id.strip(),
                "kc_id": turn.get("kc_id") or None,
            }
        kc = match_kc(content)
        if kc:
            return {"kind": "chat_turn", "kc_id": kc}
    return None


def classify_dialogue_referent(
    *,
    message_kc: Optional[str],
    recent_referent: Optional[Dict[str, Any]],
    active_episode_id: Optional[str],
    episode_kc: Optional[str],
    episode_notebook: Optional[str],
    scope_notebook: Optional[str],
    session_student: Optional[str],
    session_kc: Optional[str],
    expected_student: Optional[str],
    activity_referenced: bool,
) -> ReferentDecision:
    """Clasifica la situación del referente (A/B/C/D) con evidencia determinista.

    Orden de evaluación (fail-closed; identidad antes que tema, tema del
    mensaje antes que tema de la conversación):

    1. session_student ≠ expected_student           → D (otro estudiante)
    2. episode_kc ausente (identidad no verificable)  → D
    3. scope_notebook ≠ episode_notebook             → D (otro cuaderno)
    4. session_kc ≠ episode_kc (sesión/episodio
       inconsistentes: referencia obsoleta)          → D
    5. referencia a actividad identificada            → B (la activity es el
                                                       referente; el pipeline
                                                       la resuelve)
    6. message_kc == episode_kc                      → A (continuación explícita)
       message_kc ≠ episode_kc                       → B (tema explícito distinto)
    7. turno más reciente del propio episodio activo
       (marcado por el servidor)                      → A
       turno del chat con KC distinto del episodio   → B
       turno del chat con el MISMO KC                → C (dos explicaciones
                                                       candidatas sin desempate)
       sin turno académico competing                 → A (por exclusión)
    """
    # D — identidad y compatibilidad del contexto.
    if (
        session_student
        and expected_student
        and session_student != expected_student
    ):
        return ReferentDecision.CHAT_ROUTE
    if not episode_kc:
        # Sin identidad verificable del referente del episodio no hay
        # continuación verificable (fail-closed).
        return ReferentDecision.CHAT_ROUTE
    if scope_notebook and episode_notebook and scope_notebook != episode_notebook:
        return ReferentDecision.CHAT_ROUTE
    if session_kc and episode_kc and session_kc != episode_kc:
        return ReferentDecision.CHAT_ROUTE

    # B — referencia a actividad identificada (el referente es la actividad).
    if activity_referenced:
        return ReferentDecision.CHAT_ROUTE

    # A/B — tema explícito en el propio mensaje.
    if message_kc is not None:
        if message_kc == episode_kc:
            return ReferentDecision.DELEGATE
        return ReferentDecision.CHAT_ROUTE

    # Referente de la conversación inmediata.
    if recent_referent is None:
        # Sin turno académico competing: el episodio activo con packet
        # aprobado es el único referente visible del estudiante (caso M1-03).
        return ReferentDecision.DELEGATE
    if recent_referent.get("kind") == "episode_turn":
        if recent_referent.get("episode_id") == active_episode_id:
            return ReferentDecision.DELEGATE
        if recent_referent.get("kc_id") and recent_referent.get("kc_id") == episode_kc:
            # Diálogo de un episodio anterior del MISMO KC: el episodio activo
            # es el canal canónico vigente de ese KC en la sesión.
            return ReferentDecision.DELEGATE
        return ReferentDecision.CHAT_ROUTE
    chat_kc = recent_referent.get("kc_id")
    if chat_kc and chat_kc != episode_kc:
        return ReferentDecision.CHAT_ROUTE
    if chat_kc and chat_kc == episode_kc:
        # Mismo KC, dos explicaciones candidatas (la del chat y el packet del
        # episodio): sin desempate determinista no se afirma coincidencia.
        return ReferentDecision.CLARIFY
    # Turno marcado sin kc_id utilizable: no verificable como continuación.
    return ReferentDecision.CHAT_ROUTE


def referent_reason_code(
    decision: ReferentDecision,
    *,
    message_kc: Optional[str],
    recent_referent: Optional[Dict[str, Any]],
    active_episode_id: Optional[str],
    episode_kc: Optional[str],
    episode_notebook: Optional[str],
    scope_notebook: Optional[str],
    session_student: Optional[str],
    session_kc: Optional[str],
    expected_student: Optional[str],
    activity_referenced: bool,
) -> str:
    """Código de razón trazable para la decisión (misma aridad que classify)."""
    if session_student and expected_student and session_student != expected_student:
        return REASON_SESSION_STUDENT_MISMATCH
    if not episode_kc:
        return REASON_EPISODE_IDENTITY_UNKNOWN
    if scope_notebook and episode_notebook and scope_notebook != episode_notebook:
        return REASON_SCOPE_NOTEBOOK_MISMATCH
    if session_kc and episode_kc and session_kc != episode_kc:
        return REASON_SESSION_EPISODE_KC_MISMATCH
    if activity_referenced:
        return REASON_ACTIVITY_REFERENCE
    if message_kc is not None:
        return (
            REASON_EXPLICIT_EPISODE_TOPIC
            if message_kc == episode_kc
            else REASON_EXPLICIT_OTHER_TOPIC
        )
    if recent_referent is None:
        return REASON_NO_COMPETING_REFERENT
    if recent_referent.get("kind") == "episode_turn":
        if recent_referent.get("episode_id") == active_episode_id:
            return REASON_EPISODE_TURN_CONTINUATION
        if recent_referent.get("kc_id") and recent_referent.get("kc_id") == episode_kc:
            return REASON_EPISODE_TURN_CONTINUATION
        return REASON_CHAT_REFERENT_OTHER_KC
    chat_kc = recent_referent.get("kc_id")
    if chat_kc and chat_kc != episode_kc:
        return REASON_CHAT_REFERENT_OTHER_KC
    if chat_kc and chat_kc == episode_kc:
        return REASON_CHAT_REFERENT_SAME_KC
    return REASON_EPISODE_IDENTITY_UNKNOWN


def referent_clarification_message() -> str:
    """Aclaración breve para el caso C (referente ambiguo mismo-KC).

    No afirma corrección ni fracaso, no inventa el referente y ofrece al
    estudiante la vía explícita para destrabar la continuación.
    """
    return (
        "No puedo determinar con certeza qué explicación querés continuar: "
        "el episodio activo y lo último que conversamos en el chat tratan el "
        "mismo tema por caminos distintos. Indicame cuál querés retomar "
        "(el episodio o lo último del chat), o pegá el fragmento concreto, "
        "y lo continúo con evidencia."
    )
