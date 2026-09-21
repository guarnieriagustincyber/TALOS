"""Contracts and domain models for Subsystem S5.1 (Curricular Roadmap).

INVARIANTS:
1. S5.1 has zero knowledge of student state or evidence ledgers.
2. CurricularRoadmap is an immutable, sovereign curricular artifact.
3. Dependencies strictly distinguish HARD (blocking) vs SOFT (recommending).
4. Canonical revision ID is an immutable 64-char SHA-256 digest.
"""

from enum import Enum
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract


class NodeType(str, Enum):
    """Categorization of curricular nodes."""

    TOPIC = "TOPIC"
    COMPETENCY = "COMPETENCY"
    LAB = "LAB"


class DependencyType(str, Enum):
    """Prerequisite dependency semantics between roadmap nodes."""

    HARD = "HARD"
    SOFT = "SOFT"


class ProposalAction(str, Enum):
    """Restricted actions that AI agents can propose on a roadmap."""

    ADD_NODE = "ADD_NODE"
    REMOVE_NODE = "REMOVE_NODE"
    ADD_DEPENDENCY = "ADD_DEPENDENCY"
    REMOVE_DEPENDENCY = "REMOVE_DEPENDENCY"
    UPDATE_METADATA = "UPDATE_METADATA"


class RoadmapDependency(BaseContract):
    """Directed dependency between two roadmap nodes.

    source_node_id must be satisfied before target_node_id unlocks (if HARD).
    """

    model_config = ConfigDict(frozen=True)

    source_node_id: str = Field(

        ..., min_length=1, description="Prerequisite node ID"
    )
    target_node_id: str = Field(
        ..., min_length=1, description="Dependent node ID"
    )
    dependency_type: DependencyType = Field(
        ..., description="HARD (blocking) or SOFT (recommended)"
    )
    rationale: Optional[str] = Field(
        default=None, description="Pedagogical justification for dependency"
    )


class RoadmapNode(BaseContract):
    """Individual curricular unit, competency, or laboratory."""

    model_config = ConfigDict(frozen=True)

    node_id: str = Field(
        ...,
        min_length=1,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Unique identifier slug",
    )
    title: str = Field(
        ..., min_length=1, description="Human-readable title"
    )
    description: str = Field(
        ..., min_length=1, description="Detailed pedagogical description"
    )
    node_type: NodeType = Field(
        ..., description="TOPIC, COMPETENCY, or LAB"
    )
    notebook_id: str = Field(
        ..., min_length=1, description="Authoritative curricular notebook ID"
    )
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Curricular priority (1=Trunk/Core, 5=Elective)",
    )
    target_competencies: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Competencies exercised or reinforced by this node",
    )
    estimated_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        description="Estimated student investment time in minutes",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible metadata for labs, tools, or tags",
    )


class CurricularRoadmap(BaseContract):
    """Complete, sovereign curricular roadmap DAG."""

    model_config = ConfigDict(frozen=True)

    roadmap_id: str = Field(
        ..., min_length=1, description="Unique roadmap identifier"
    )
    title: str = Field(
        ..., min_length=1, description="Roadmap title"
    )
    version: str = Field(
        ..., min_length=1, description="Semantic version string (e.g. 1.0.0)"
    )
    nodes: Dict[str, RoadmapNode] = Field(
        ..., description="All nodes indexed by node_id"
    )
    dependencies: Tuple[RoadmapDependency, ...] = Field(
        default_factory=tuple,
        description="All directed dependencies in the roadmap",
    )
    canonical_revision_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Reproducible SHA-256 digest of canonical structure",
    )


class RoadmapProposal(BaseContract):
    """Read-only change proposal produced by AI or pedagogical agents.

    RULE: AI can only emit this proposal. Human must approve and apply it.
    """

    model_config = ConfigDict(frozen=True)

    proposal_id: str = Field(
        ..., min_length=1, description="Unique proposal identifier"
    )
    roadmap_id: str = Field(
        ..., min_length=1, description="Target roadmap identifier"
    )
    source_agent: str = Field(
        ..., min_length=1, description="Agent or module originating proposal"
    )
    action: ProposalAction = Field(
        ..., description="Proposed structural or metadata action"
    )
    rationale: str = Field(
        ..., min_length=1, description="Pedagogical reasoning for proposal"
    )
    proposed_node: Optional[RoadmapNode] = Field(
        default=None, description="Proposed node payload if applicable"
    )
    proposed_dependency: Optional[RoadmapDependency] = Field(
        default=None, description="Proposed dependency payload if applicable"
    )
    applied: bool = Field(
        default=False,
        description="True if human sovereign approved and applied proposal",
    )


class RoadmapContractError(Exception):
    """Base exception for all roadmap structural or semantic violations."""


class CyclicDependencyError(RoadmapContractError):
    """Raised when directed cycles are detected in roadmap dependencies."""


class MissingNodeReferenceError(RoadmapContractError):
    """Raised when dependency references a node_id not present in roadmap."""


class DuplicateNodeError(RoadmapContractError):
    """Raised when duplicate node identifiers are defined."""


class SelfLoopDependencyError(RoadmapContractError):
    """Raised when a dependency has identical source and target node IDs."""


class RoadmapSerializationError(RoadmapContractError):
    """Raised when YAML/JSON parsing or validation fails."""
