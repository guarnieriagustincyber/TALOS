"""StudyPlan contract."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class StudyPlan(BaseContract):
    """Pedagogical study plan sequence produced by the planner."""

    id: str = Field(..., min_length=1, description="Unique study plan identifier")
    student_id: Optional[str] = Field(default=None, description="Associated student ID")
    module: str = Field(..., min_length=1, description="Target curriculum module")
    objective: str = Field(..., min_length=1, description="Learning objective")
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisites")
    concepts: List[str] = Field(default_factory=list, description="Key concepts to cover")
    sources: List[str] = Field(default_factory=list, description="Selected source IDs")
    order: List[str] = Field(default_factory=list, description="Step-by-step sequence")
    depth: str = Field(default="standard", description="Depth level (e.g., 'introductory', 'standard', 'rigorous')")
    exercises: List[str] = Field(default_factory=list, description="Target exercise references")
    mastery_criteria: Optional[str] = Field(default=None, description="Criteria required to demonstrate mastery")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of creation")
