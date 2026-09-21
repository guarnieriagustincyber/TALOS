"""Source contract."""

from typing import Any, Dict, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract
from study_engine.contracts.enums import SourceRole


class Source(BaseContract):
    """Knowledge source contract."""

    source_id: str = Field(..., min_length=1, description="Unique identifier for the source")
    title: str = Field(..., min_length=1, description="Title of the source")
    author: Optional[str] = Field(default=None, description="Author or authors of the source")
    type: Optional[str] = Field(default=None, description="Type of source (e.g., book, pdf, syllabus)")
    language: Optional[str] = Field(default="es", description="Language of the content (default: 'es')")
    role: SourceRole = Field(default=SourceRole.PRIMARY, description="Role of the source in the curriculum")
    priority: int = Field(default=1, ge=1, description="Priority integer (1 = highest priority)")
    subject: Optional[str] = Field(default=None, description="Subject domain")
    course: Optional[str] = Field(default=None, description="Associated course name or code")
    phase: Optional[str] = Field(default=None, description="Curriculum phase (e.g., 'Fase-0')")
    chapter: Optional[str] = Field(default=None, description="Chapter reference if applicable")
    section: Optional[str] = Field(default=None, description="Section reference if applicable")
    page: Optional[int] = Field(default=None, ge=1, description="Page number if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary extensible metadata dictionary")
