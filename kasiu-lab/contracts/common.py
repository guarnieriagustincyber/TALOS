from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class HashDigest(BaseModel):
    """Estructura canónica de digest criptográfico."""

    algorithm: str = Field(default="sha256", description="Algoritmo de hash")
    digest: str = Field(..., description="Hash hexadecimal inmutable")


class CitationLocation(BaseModel):
    """Localizador granular dentro del documento fuente."""

    page_start: int = Field(..., ge=1, description="Página de inicio (1-indexed)")
    page_end: int = Field(..., ge=1, description="Página de fin (1-indexed)")
    section: Optional[str] = Field(None, description="Sección o capítulo textual")
