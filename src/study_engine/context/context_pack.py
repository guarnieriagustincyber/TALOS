"""ContextPack data structures and structural representations (Ola 5, Fase 5.4).

Encapsulates complete structural retrieval, provenance chains, expanded sections,
and physical pre-LLM abstention states (INV-W5-1).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ChunkWithProvenance:
    """Retrieved chunk retaining strict provenance metadata and position."""
    chunk_id: str
    document_id: str
    source_id: str
    source_title: str
    page_start: int
    pos_index: int
    section: str
    content: str
    is_seed_hit: bool
    relevance_score: float
    token_count: int


@dataclass(frozen=True)
class SourceContribution:
    """Aggregated contribution summary for a specific source."""
    source_id: str
    source_title: str
    chunk_count: int
    total_tokens: int
    pages_covered: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class ExpandedSection:
    """Contiguous window of chunks representing a section topic."""
    document_id: str
    section_name: str
    chunks: List[ChunkWithProvenance]
    start_pos: int
    end_pos: int
    total_tokens: int


@dataclass(frozen=True)
class CrossSourceRelation:
    """Explicit mapping or bridge relationship between sources."""
    source_a: str
    source_b: str
    topic: str
    relation_type: str = "comparative"


@dataclass
class ContextPack:
    """Complete structural context package assembled for LLM generation."""
    session_state: Dict[str, Any] = field(default_factory=dict)
    current_kc: Optional[str] = None
    previous_errors: List[str] = field(default_factory=list)
    previous_hints: List[str] = field(default_factory=list)
    source_map: Dict[str, SourceContribution] = field(default_factory=dict)
    retrieved_evidence: List[ChunkWithProvenance] = field(default_factory=list)
    expanded_sections: List[ExpandedSection] = field(default_factory=list)
    cross_source_relations: List[CrossSourceRelation] = field(default_factory=list)
    total_tokens: int = 0
    expansion_budget_used: int = 0
    abstained: bool = False
    abstention_reason: Optional[str] = None
    formatted_text: str = ""
    is_sufficient: bool = False
    trust_status: Optional[Any] = None

    def add_evidence(self, chunk: ChunkWithProvenance) -> None:
        self.retrieved_evidence.append(chunk)
        self.total_tokens += chunk.token_count
        if not self.abstained and len(self.retrieved_evidence) > 0:
            self.is_sufficient = True

    @property
    def has_evidence(self) -> bool:
        return len(self.retrieved_evidence) > 0 and not self.abstained and self.is_sufficient
