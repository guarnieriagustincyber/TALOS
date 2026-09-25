"""Conversational State Machine with Epistemic Inertia (CAL §3.2 Multi-Turn).

Distinguishes between genuine out-of-domain (OOD) queries, cold starts,
and ambiguous/deictic followups within an active technical thread.
"""

from __future__ import annotations

from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    COLD_START = "cold_start"           # Primera consulta de la sesión
    ACTIVE_TECHNICAL_THREAD = "active"  # Hilo técnico en curso
    TOPIC_BREAK = "break"               # Usuario cambió de tema explícitamente
    AMBIGUOUS_FOLLOWUP = "ambiguous"    # Consulta corta/deíctica en hilo activo


_TOPIC_BREAK_PATTERNS = [
    re.compile(r"\b(?:cambiando\s+de\s+tema|otro\s+tema|hablemos\s+de\s+otra\s+cosa|nada\s+que\s+ver|dejemos\s+esto)\b", re.IGNORECASE),
    re.compile(r"\b(?:pasemos\s+a\s+otra\s+cosa|ahora\s+quiero\s+ver\s+otra\s+cosa)\b", re.IGNORECASE),
]

_DEICTIC_PATTERNS = [
    re.compile(r"\b(?:ah[ií]|ac[aá]|all[aá]|eso|esto|aquello|lo\s+anterior|lo\s+que\s+dijiste)\b", re.IGNORECASE),
    re.compile(r"\b(?:en\s+ese\s+caso|en\s+esta\s+funci[oó]n|en\s+este\s+c[oó]digo|el\s+coso|ese|esa)\b", re.IGNORECASE),
    re.compile(r"\b(?:c[oó]mo\s+uso|qu[eé]\s+pasa\s+si|y\s+con\s+eso|por\s*qu[eé]\s+ah[ií])\b", re.IGNORECASE),
    re.compile(r"\b(?:el\s+ampersand|el\s+asterisco|la\s+flechita)\b", re.IGNORECASE),
]


def has_explicit_topic_change(query: str) -> bool:
    """Detect if the student is explicitly requesting a topic change."""
    q = (query or "").strip()
    return any(p.search(q) for p in _TOPIC_BREAK_PATTERNS)


def has_deictic_markers(query: str) -> bool:
    """Return True if query contains deictic, spatial, or contextual markers."""
    q = (query or "").strip()
    return any(p.search(q) for p in _DEICTIC_PATTERNS)


def classify_conversation_state(
    query: str,
    recent_turns: Optional[List[Dict[str, str]]] = None,
    retrieval_results: Optional[List[Any]] = None,
    has_fallback_pack: bool = False,
) -> ConversationState:
    """Classify the current turn into the conversation state machine with epistemic inertia."""
    turns = [
        t for t in (recent_turns or [])
        if isinstance(t, dict) and (t.get("content") or "").strip()
    ]
    results = retrieval_results or []

    if not turns:
        return ConversationState.COLD_START

    if has_explicit_topic_change(query):
        return ConversationState.TOPIC_BREAK

    word_count = len((query or "").split())
    is_deictic = has_deictic_markers(query)

    # Si hay historial técnico activo y la consulta es corta o deíctica
    if word_count < 12 and (is_deictic or word_count <= 6 or len(results) < 3):
        return ConversationState.AMBIGUOUS_FOLLOWUP

    if len(results) >= 3:
        return ConversationState.ACTIVE_TECHNICAL_THREAD

    # Con historial previo y sin quiebre explícito, mantener inercia de hilo técnico
    return ConversationState.ACTIVE_TECHNICAL_THREAD if turns else ConversationState.COLD_START


def should_abstain(
    state: ConversationState,
    retrieval_results: Optional[List[Any]] = None,
    has_fallback_pack: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Determine whether to abstain under CAL §3.2 taking conversational state into account.
    
    Returns:
        (abstained, reason)
    """
    results = retrieval_results or []

    if state == ConversationState.COLD_START:
        # En arranque en frío sin turnos previos, abstenerse si no hay resultados
        if len(results) == 0:
            return True, "QUERY_OUT_OF_SCOPE"
        return False, None

    if state == ConversationState.TOPIC_BREAK:
        # Tras quiebre explícito de tema, abstenerse si la nueva consulta no tiene hits
        if len(results) == 0:
            return True, "QUERY_OUT_OF_SCOPE"
        return False, None

    if state == ConversationState.AMBIGUOUS_FOLLOWUP:
        # En hilo activo con consulta ambigua/deíctica, NUNCA abstenerse si hay fallback pack previo
        if len(results) == 0 and not has_fallback_pack:
            return True, "QUERY_OUT_OF_SCOPE"
        return False, None

    if state == ConversationState.ACTIVE_TECHNICAL_THREAD:
        # Hilo activo: tolerar retrieval débil si existe un paquete epistémico previo
        if len(results) == 0 and not has_fallback_pack:
            return True, "QUERY_OUT_OF_SCOPE"
        return False, None

    return False, None
