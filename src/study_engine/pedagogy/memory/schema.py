"""Pydantic contracts and DDL for the Cognitive Profile Memory subsystem (Opción C).

Design axioms:
1. Memoria Epistémica Estructurada — tuplas deterministas, sin prosa libre.
2. Grounded KC — solo KCs validados contra notebook_kc_catalog.json.
3. Anti-saturación — máx 10 ítems ACTIVE por KC inyectados en prompt.
4. Cobertura cero: si no hay memoria, no se altera el prompt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumeraciones
# ---------------------------------------------------------------------------

class MemoryCategory(str, Enum):
    """Categorías deterministas de ítems cognitivos.

    WEAKNESS           — KC con ≥1 intento fallido documentado.
    STRENGTH           — KC dominado (confidence ≥ 0.85, ≥2 confirmaciones).
    RECURRING_MISCONCEPTION — Mismo error ≥2 sesiones.
    PREFERENCE         — Preferencia didáctica declarada explícitamente.
    ANALOGY_AFFINITY   — Analogía que resonó positivamente con el estudiante.
    """
    WEAKNESS = "WEAKNESS"
    STRENGTH = "STRENGTH"
    RECURRING_MISCONCEPTION = "RECURRING_MISCONCEPTION"
    PREFERENCE = "PREFERENCE"
    ANALOGY_AFFINITY = "ANALOGY_AFFINITY"


class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"   # Debilidad superada (P(L) ≥ 0.80 post-update)
    ARCHIVED = "ARCHIVED"   # Más de 30 días sin acceso


# ---------------------------------------------------------------------------
# Modelos Pydantic
# ---------------------------------------------------------------------------

class CognitiveItem(BaseModel):
    """Una entrada atómica del perfil cognitivo del estudiante.

    Invariante: description ≤ 200 chars.  evidence_quote ≤ 120 chars.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    kc_id: str                              # KC grounded contra catalog
    category: MemoryCategory
    description: str = Field(..., max_length=200)
    evidence_quote: Optional[str] = Field(None, max_length=120)
    occurrences: int = Field(default=1, ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: MemoryStatus = MemoryStatus.ACTIVE
    last_observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class CognitiveExtractionPayload(BaseModel):
    """Output completo de una extracción LLM sobre un turno de diálogo.

    El extractor LLM devuelve exactamente este schema (JSON estructurado).
    Si no hay hallazgos, items=[].
    """
    items: List[CognitiveItem] = Field(default_factory=list)
    extraction_model: str = ""
    extraction_latency_ms: float = 0.0
    grounded: bool = False   # True si todos los kc_id fueron validados


# ---------------------------------------------------------------------------
# DDL SQL (sqlite3 executescript)
# ---------------------------------------------------------------------------

COGNITIVE_PROFILE_DDL = """
CREATE TABLE IF NOT EXISTS student_cognitive_profile (
    id                TEXT PRIMARY KEY NOT NULL,
    user_id           TEXT NOT NULL,
    kc_id             TEXT NOT NULL,
    category          TEXT NOT NULL,
    description       TEXT NOT NULL,
    evidence_quote    TEXT,
    occurrences       INTEGER NOT NULL DEFAULT 1,
    confidence        REAL NOT NULL DEFAULT 1.0,
    status            TEXT NOT NULL DEFAULT 'ACTIVE',
    last_observed_at  TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cogprof_user_kc
    ON student_cognitive_profile(user_id, kc_id);

CREATE INDEX IF NOT EXISTS idx_cogprof_user_cat
    ON student_cognitive_profile(user_id, category);

CREATE INDEX IF NOT EXISTS idx_cogprof_status
    ON student_cognitive_profile(status);
"""
