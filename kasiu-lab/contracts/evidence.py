from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .common import CitationLocation, HashDigest


class AuditStatus(str, Enum):
    GROUNDED = "GROUNDED"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"


class CitationItem(BaseModel):
    """Representación formal de una evidencia forense citada."""

    evidence_id: str = Field(
        ...,
        examples=["E1"],
        description="Identificador tokenizado en el texto",
    )
    document_hash: HashDigest
    document_title: str
    location: CitationLocation
    verified_text_chunk: str = Field(..., description="Texto literal extraído por el motor RRF")
    audit_status: AuditStatus = Field(default=AuditStatus.GROUNDED)
    rrf_score: float = Field(..., ge=0.0, le=1.0, description="Score de confianza del retrieval")


class ClaimAudit(BaseModel):
    """Vinculación entre afirmación del LLM y su respaldo empírico."""

    claim_text: str = Field(..., description="Afirmación sintetizada por el modelo")
    evidence_id: str = Field(..., description="Puntero al token [E#]")


class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    notebook_id: str = Field(default="default_nb")
    requested_scope_id: Optional[str] = Field(None, description="Hash de documento si se enfoca alcance")


class ChatQueryResponse(BaseModel):
    """Respuesta orquestada con estricta fundamentación epistémica."""

    reply_text: str = Field(..., description="Texto con tokens interactivos [E#]")
    claims: List[ClaimAudit] = Field(default_factory=list, description="Desglose de afirmaciones auditables")
    citation_manifest: Dict[str, CitationItem] = Field(
        default_factory=dict,
        description="Mapa evidence_id -> Evidencia forense",
    )
    mermaid_diagram: Optional[str] = Field(None, description="Especificación Mermaid (Ilustración no auditable)")
    abstained: bool = Field(default=False, description="True si RRF no superó el umbral tau")
    abstention_reason: Optional[str] = None
