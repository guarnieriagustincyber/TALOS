"""Folder model for hierarchical organization of study notebooks (Fase 5.7)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


class Folder(BaseModel):
    """Immutable, strongly-typed folder node representing collections of notebooks."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: StrictStr = Field(..., min_length=1, description="Identificador único del folder")
    name: StrictStr = Field(..., min_length=1, description="Nombre legible del folder")
    parent_folder_id: Optional[StrictStr] = Field(
        default=None,
        description="ID del folder padre para permitir anidación jerárquica",
    )
    description: Optional[StrictStr] = Field(
        default=None,
        description="Descripción del propósito del folder",
    )
    created_at: datetime = Field(..., description="Timestamp de creación")
    updated_at: datetime = Field(..., description="Timestamp de última modificación")

    @field_validator("id", "name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Folder id and name must not be empty or pure whitespace.")
        return v.strip()

    @field_validator("parent_folder_id")
    @classmethod
    def validate_no_self_parent(cls, v: Optional[str], info: object) -> Optional[str]:
        # Basic validation: cannot parent to itself if id is known in data
        if v is not None:
            clean = v.strip()
            if not clean:
                return None
            return clean
        return v

    def validate_not_self_referencing(self) -> None:
        """Explicit check preventing self-reference."""
        if self.parent_folder_id is not None and self.parent_folder_id == self.id:
            raise ValueError(f"Folder cannot be its own parent (id='{self.id}').")
