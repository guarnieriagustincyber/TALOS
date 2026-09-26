"""Cognitive Profile Memory subsystem (Opción C — Jefe Final).

Provides deterministic, persistent epistemic memory of the student's
cognitive trajectory. Zero TTFT impact: all writes are async background tasks.

Modules:
    schema  — Pydantic contracts and DDL constants.
    store   — CognitiveProfileStore: SQLite read/write layer.
    extractor — CognitiveExtractor: async LLM+heuristic extraction.
    injector  — ProfileInjector: <120-token XML block for system prompt.
"""
from study_engine.pedagogy.memory.schema import (
    CognitiveExtractionPayload,
    CognitiveItem,
    MemoryCategory,
)
from study_engine.pedagogy.memory.store import CognitiveProfileStore

__all__ = [
    "CognitiveExtractionPayload",
    "CognitiveItem",
    "CognitiveProfileStore",
    "MemoryCategory",
]
