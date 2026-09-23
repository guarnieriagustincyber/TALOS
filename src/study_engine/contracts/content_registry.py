"""Content Registry Contracts (Slice 6.0.5).

Defines canonical types, statuses, and data structures for exact identity indexing
of curricular content (exercises and sections) and solution protection.

REGLA: UnitType contiene exclusivamente 'exercise' y 'section'.
La incorporación de 'example' o 'definition' exige parser y tests en el mismo commit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class UnitType(str, Enum):
    """Canonical curricular content unit types.
    
    Restricted strictly to exercise and section for Slice 6.0.5.
    """
    EXERCISE = "exercise"
    SECTION = "section"


class ContentStatus(str, Enum):
    """Integrity and review status for indexed content units."""
    OK = "ok"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ContentItem:
    """Represents an exact-identity curricular content unit."""
    content_id: str
    source_id: str
    unit_type: UnitType
    statement_text: str
    chunk_ids: List[str]
    solution_chunk_ids: Optional[List[str]] = None
    status: ContentStatus = ContentStatus.OK
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary representation."""
        return {
            "content_id": self.content_id,
            "source_id": self.source_id,
            "unit_type": self.unit_type.value if isinstance(self.unit_type, UnitType) else str(self.unit_type),
            "statement_text": self.statement_text,
            "chunk_ids": list(self.chunk_ids),
            "solution_chunk_ids": list(self.solution_chunk_ids) if self.solution_chunk_ids is not None else [],
            "status": self.status.value if isinstance(self.status, ContentStatus) else str(self.status),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContentItem:
        """Instantiate item from dictionary representation."""
        raw_type = data.get("unit_type", "exercise")
        unit_type = UnitType(raw_type) if isinstance(raw_type, str) else raw_type

        raw_status = data.get("status", "ok")
        status = ContentStatus(raw_status) if isinstance(raw_status, str) else raw_status

        return cls(
            content_id=data["content_id"],
            source_id=data["source_id"],
            unit_type=unit_type,
            statement_text=data.get("statement_text", ""),
            chunk_ids=data.get("chunk_ids", []),
            solution_chunk_ids=data.get("solution_chunk_ids"),
            status=status,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            metadata=data.get("metadata", {}),
        )
