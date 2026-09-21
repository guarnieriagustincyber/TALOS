from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    MASTERED = "MASTERED"  # Certificado con bloque en Ledger
    ACTIVE = "ACTIVE"  # Prerrequisitos cumplidos, listo para operar
    LOCKED = "LOCKED"  # Bloqueado por el motor de estado del backend


class SparklinePoint(BaseModel):
    timestamp_rel: int = Field(..., description="Punto relativo en timeline")
    value: float = Field(..., description="Métrica (ej. tasa pps, entropía)")


class NodeTelemetry(BaseModel):
    """Métricas asociadas a la adquisición de maestría del nodo."""

    execution_count: int = Field(default=0)
    avg_score: float = Field(default=0.0, ge=0.0, le=100.0)
    sparkline: List[SparklinePoint] = Field(default_factory=list, description="Puntos para trazar curvas SVG")


class CurriculumNode(BaseModel):
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
    from_node: str
    to_node: str
    curve_type: str = Field(default="bezier")
    is_active: bool = Field(default=False)


class CurriculumGraphResponse(BaseModel):
    phases: List[str]
    nodes: List[CurriculumNode]
    edges: List[CurriculumEdge]
    global_progress: float
    mastered_count: int
    total_nodes: int
    ledger_chain_length: int
