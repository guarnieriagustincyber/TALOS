"""Pydantic v2 DTOs and Data Transfer Schemas for the Web API (Hito 10).

Adheres strictly to Thin Client principles:
- The UI never mutates state directly.
- All domain invariants and sovereign gate checks remain in backend controllers.
- No sensitive keys, credentials, or host secrets are exposed in response envelopes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """System health and diagnostic envelope."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(default="healthy", description="Overall system operational status.")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp of health check.")
    components: Dict[str, Any] = Field(..., description="Component-level health descriptors.")
    frozen_perimeter: str = Field(default="INTACT", description="Integrity status of frozen architectural perimeter.")
    test_suite: Dict[str, int] = Field(..., description="Total and passed counts from the canonical test suite.")


class RoadmapNodeDto(BaseModel):
    """Curricular node projection with student progression status."""

    model_config = ConfigDict(frozen=True)

    node_id: str = Field(..., description="Canonical node identifier.")
    title: str = Field(..., description="Human-readable node title.")
    status: str = Field(..., description="Progress status (AVAILABLE, LOCKED, ASSESSED_PROFICIENT, etc.).")
    prerequisites: List[str] = Field(default_factory=list, description="List of prerequisite node IDs.")
    is_root: bool = Field(default=False, description="True if node has no incoming prerequisites.")
    node_type: str = Field(default="TOPIC", description="Curricular node type (TOPIC, COMPETENCY, LAB).")
    subtopics: List[str] = Field(default_factory=list, description="Descriptive list of analytical subtopics.")
    description: Optional[str] = Field(default=None, description="Detailed pedagogical overview / objective.")
    unit: Optional[int] = Field(default=None, description="Curricular unit or tramo number.")


class RoadmapEdgeDto(BaseModel):
    """Directed curricular prerequisite relationship."""

    model_config = ConfigDict(frozen=True)

    from_node: str = Field(..., description="Prerequisite source node ID.")
    to_node: str = Field(..., description="Dependent target node ID.")
    dependency_type: str = Field(default="HARD", description="HARD (blocking) or SOFT (recommended).")


class RoadmapResponse(BaseModel):
    """Full curricular roadmap graph with pre-rendered Mermaid.js markup."""

    model_config = ConfigDict(frozen=True)

    roadmap_id: str = Field(..., description="Identifier of the active curriculum roadmap.")
    title: str = Field(..., description="Descriptive title of the roadmap.")
    nodes: List[RoadmapNodeDto] = Field(..., description="List of nodes in topological / discovery order.")
    edges: List[RoadmapEdgeDto] = Field(..., description="List of prerequisite relationships.")
    mermaid_source: str = Field(..., description="Pre-computed, styled Mermaid.js graph definition.")


class AuthorizedSourceDto(BaseModel):
    """Authorized epistemic document boundary for a curricular node."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(..., description="Document filename or ID in the repository.")
    page_start: Optional[int] = Field(default=None, description="Starting page of authorized range.")
    page_end: Optional[int] = Field(default=None, description="Ending page of authorized range.")


class PracticalTaskSummaryDto(BaseModel):
    """Summary of practical challenge bound to a node."""

    model_config = ConfigDict(frozen=True)

    task_id: str = Field(..., description="Canonical task identifier.")
    description: str = Field(..., description="Task overview and instructions.")
    rubric_id: str = Field(..., description="Associated deterministic evaluation rubric ID.")


class NodeDetailResponse(BaseModel):
    """In-depth curricular and epistemic specification for a specific node."""

    model_config = ConfigDict(frozen=True)

    node_id: str = Field(..., description="Canonical node identifier.")
    title: str = Field(..., description="Human-readable node title.")
    description: str = Field(..., description="Curricular learning objectives and description.")
    status: str = Field(..., description="Student's derived status for this node.")
    prerequisites: List[str] = Field(default_factory=list, description="List of prerequisite node IDs.")
    authorized_sources: List[AuthorizedSourceDto] = Field(
        default_factory=list, description="Epistemically authorized document scopes."
    )
    practical_task: Optional[PracticalTaskSummaryDto] = Field(
        default=None, description="Bound practical programming challenge if configured."
    )


class NodeStateDto(BaseModel):
    """Derived state projection for an individual node."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(..., description="NodeProgressStatus string value.")
    evidence_count: int = Field(default=0, description="Total evidence entries committed in ledger.")
    score: Optional[float] = Field(default=None, description="Latest verified assessment score.")


class StudentSummaryDto(BaseModel):
    """Global aggregate progression metrics."""

    model_config = ConfigDict(frozen=True)

    total_nodes: int = Field(..., description="Total nodes defined in the curriculum.")
    completed: int = Field(..., description="Count of nodes marked ASSESSED_PROFICIENT.")
    available: int = Field(..., description="Count of unlocked nodes available for study.")
    locked: int = Field(..., description="Count of nodes locked by unfulfilled prerequisites.")
    progress_percentage: float = Field(..., description="Completion percentage (0.0 to 100.0).")


class StudentStateResponse(BaseModel):
    """Full authoritative student state derived purely from the EvidenceLedger."""

    model_config = ConfigDict(frozen=True)

    student_id: str = Field(..., description="Student identifier.")
    as_of_time: str = Field(..., description="Timestamp of state derivation.")
    nodes: Dict[str, NodeStateDto] = Field(..., description="State by node ID.")
    summary: StudentSummaryDto = Field(..., description="Aggregate summary metrics.")


class StudentProfileDto(BaseModel):
    """Profile envelope for an active student."""

    model_config = ConfigDict(frozen=True)

    student_id: str = Field(..., description="Unique student identifier.")
    name: str = Field(..., description="Full name of student.")
    email: str = Field(..., description="Student contact email.")
    created_at: str = Field(..., description="ISO 8601 timestamp of registration.")
    timezone: str = Field(default="America/Argentina/Buenos_Aires", description="Student timezone.")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="UI and notification preferences.")
    mastery_percentage: float = Field(default=65.0, description="Overall mastery percentage.")
    study_hours: float = Field(default=12.5, description="Logged study hours.")


class LedgerEntryDto(BaseModel):
    """Sanitized, immutable entry record from the sovereign EvidenceLedger."""

    model_config = ConfigDict(frozen=True)

    entry_index: int = Field(..., description="Monotonically increasing sequence index.")
    node_id: str = Field(..., description="Curricular node targeted.")
    evaluation_attempt_id: str = Field(..., description="Evaluation attempt ID.")
    outcome: str = Field(..., description="Evaluation verdict (PASS/FAIL).")
    score: float = Field(..., description="Numeric score achieved.")
    committed_at: str = Field(..., description="ISO 8601 timestamp of commitment.")
    entry_hash_prefix: str = Field(..., description="First 16 chars of SHA-256 integrity hash.")


class LedgerResponse(BaseModel):
    """Ledger history and integrity status."""

    model_config = ConfigDict(frozen=True)

    entries: List[LedgerEntryDto] = Field(..., description="Chronological ledger records.")
    total_entries: int = Field(..., description="Total entries committed.")
    integrity_status: str = Field(default="VALID", description="Cryptographic integrity verification result.")





class NodeStatus(str, Enum):
    MASTERED = "MASTERED"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"


class SparklinePoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_rel: int = Field(..., description="Punto relativo en timeline")
    value: float = Field(..., description="Métrica (ej. tasa pps, entropía)")


class NodeTelemetry(BaseModel):
    """Métricas asociadas a la adquisición de maestría del nodo."""

    model_config = ConfigDict(frozen=True)

    execution_count: int = Field(default=0)
    avg_score: float = Field(default=0.0, ge=0.0, le=100.0)
    sparkline: List[SparklinePoint] = Field(default_factory=list, description="Puntos para trazar curvas SVG")


class CurriculumNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    description: str
    phase_id: str = Field(..., description="Agrupador de fase curricular")
    status: NodeStatus
    progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    evidence_count: int = Field(default=0)
    ledger_block_hash: Optional[str] = Field(None, description="Obligatorio solo si status=MASTERED")
    dependencies: List[str] = Field(default_factory=list, description="Lista de node_ids requeridos")
    telemetry: NodeTelemetry = Field(default_factory=NodeTelemetry)


class CurriculumEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_node: str
    to_node: str
    curve_type: str = Field(default="bezier")
    is_active: bool = Field(default=False)


class CurriculumGraphResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    phases: List[str]
    nodes: List[CurriculumNode]
    edges: List[CurriculumEdge]
    global_progress: float
    mastered_count: int
    total_nodes: int
    ledger_chain_length: int

