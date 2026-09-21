"""Notebook contract for Subsystem S2 & S5 study context.

Authoritative container binding a study domain to its formal CurricularRoadmap
and associated epistemic knowledge sources.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class Notebook(BaseContract):
    """Independent domain study notebook or knowledge base."""

    id: str = Field(..., min_length=1, description="Unique notebook identifier or slug")
    name: str = Field(..., min_length=1, description="Human-readable notebook name")
    description: Optional[str] = Field(default=None, description="Notebook purpose or overview")
    subject: Optional[str] = Field(default=None, description="Subject area")
    curriculum_id: Optional[str] = Field(
        default=None,
        description="Formal curricular roadmap ID bound authoritatively to this notebook",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of source IDs associated with this notebook",
    )
    folder_id: str = Field(
        default="folder_root",
        min_length=1,
        description="Referencia al Folder contenedor padre (default: folder_root)",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of creation")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp of last update")
