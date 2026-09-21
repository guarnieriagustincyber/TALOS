"""ControllerPayload dataclass for Two-Stage Architecture (Ola 6, Fase 6.1).

Defines the structured epistemic payload emitted by EpistemicController
and consumed by PersonaNarrator to prevent Prompt Congestion without hallucinations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Fact:
    """Atomic ground truth extracted strictly from evidence chunks."""
    fact_id: str
    statement: str
    source_id: str
    chunk_id: str
    page: int
    technical_terms: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Citation:
    """Authoritative citation reference for the narrator to cite."""
    citation_id: str
    source_title: str
    author: str
    page: int
    chunk_id: str


@dataclass(frozen=True)
class BKTStatus:
    """Consultive student mastery indicator (INV-W6-2)."""
    kc_id: str
    p_L: float
    mastery_level: str  # e.g., "novice", "competent", "mastered"
    recurrent_errors: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PedagogicalConstraints:
    """Strict boundaries the Narrator must respect."""
    forbidden_solution_leak: bool = True
    suggest_exercise: bool = False
    max_words: int = 450
    analogy_allowed: bool = True
    code_generation_allowed: bool = False
    forbidden_terms: Tuple[str, ...] = ()


from study_engine.pedagogy.style_contracts import ConversationStyle


@dataclass(frozen=True)
class ControllerPayload:
    """Complete structured epistemic contract emitted by the Controller."""
    query: str
    core_facts: Tuple[Fact, ...]
    citations: Tuple[Citation, ...]
    bkt_status: BKTStatus
    pedagogical_constraints: PedagogicalConstraints
    style_directive: ConversationStyle
    session_briefing: str
    context_tokens: int = 0
