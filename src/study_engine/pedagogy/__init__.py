"""Pedagogical domain package for structured response pipelines and contracts (Fase 5.8)."""

from study_engine.pedagogy.contract import PedagogicalContract, PersonaType
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT, get_default_contract
from study_engine.pedagogy.response_phase import PhaseIdType, ResponsePhase
from study_engine.pedagogy.socratic_guard import GuardResult, SocraticGuard
from study_engine.pedagogy.structured_pipeline import (
    PhaseHistory,
    PhaseOutput,
    StreamEvent,
    StreamEventType,
    StructuredResponsePipeline,
)

__all__ = [
    "PedagogicalContract",
    "PersonaType",
    "ResponsePhase",
    "PhaseIdType",
    "FASE0_CONTRACT",
    "get_default_contract",
    "SocraticGuard",
    "GuardResult",
    "PhaseOutput",
    "PhaseHistory",
    "StreamEvent",
    "StreamEventType",
    "StructuredResponsePipeline",
]
