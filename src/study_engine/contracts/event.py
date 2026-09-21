"""Event contract."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class Event(BaseContract):
    """Structured telemetry, logging, and observability event."""

    event_id: str = Field(..., min_length=1, description="Unique event identifier")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    event_type: str = Field(..., min_length=1, description="Category/type of the event")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the event"
    )
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
