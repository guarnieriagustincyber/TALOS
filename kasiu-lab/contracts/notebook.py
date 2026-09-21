from pydantic import BaseModel, Field


class ScopeValidationRequest(BaseModel):
    notebook_id: str
    requested_doc_hash: str = Field(..., description="Hash del documento a aislar")


class ScopeValidationResponse(BaseModel):
    valid: bool
    active_scope_id: str
    doc_title: str
    doc_hash: str
    chunk_count: int
    isolation_confirmed: bool = Field(..., description="Garantía de contención RRF emitida por el backend")
    message: str
