"""StudentState contract."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class StudentState(BaseContract):
    """Structured student learning state without automatic progression logic."""

    student_id: str = Field(..., min_length=1, description="Unique student identifier")
    topic: Optional[str] = Field(default=None, description="Current topic being studied")
    status: str = Field(default="developing", description="Learning state (e.g., 'not_started', 'developing', 'mastered')")
    understanding: Dict[str, bool] = Field(
        default_factory=dict,
        description="Understanding dimensions (e.g., {'conceptual': True, 'application': False, 'transfer': False})"
    )
    strengths: List[str] = Field(default_factory=list, description="Identified strength concepts")
    weaknesses: List[str] = Field(default_factory=list, description="Identified weakness concepts")
    recurring_errors: List[str] = Field(default_factory=list, description="Observed recurring errors")
    last_evaluation: Optional[Dict[str, Any]] = Field(default=None, description="Result of last evaluation")
    next_action: Optional[Dict[str, Any]] = Field(default=None, description="Recommended next action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp of last update")
