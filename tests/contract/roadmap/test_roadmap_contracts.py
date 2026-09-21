"""Contract tests for Subsystem S5.1 Curricular Roadmap."""

import pytest
from pydantic import ValidationError

from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    ProposalAction,
    RoadmapDependency,
    RoadmapNode,
    RoadmapProposal,
)


def _make_dummy_node(node_id: str = "so-intro") -> RoadmapNode:
    return RoadmapNode(
        node_id=node_id,
        title="Introducción a Sistemas Operativos",
        description="Conceptos básicos de SO y kernel",
        node_type=NodeType.TOPIC,
        notebook_id="fadena-so",
        priority=1,
    )


def test_roadmap_models_immutability():
    """Verify roadmap contracts are frozen against in-place mutation."""
    node = _make_dummy_node()
    with pytest.raises(ValidationError):
        node.priority = 2  # type: ignore[misc]

    dep = RoadmapDependency(
        source_node_id="so-intro",
        target_node_id="so-processes",
        dependency_type=DependencyType.HARD,
    )
    with pytest.raises(ValidationError):
        dep.dependency_type = DependencyType.SOFT  # type: ignore[misc]

    roadmap = CurricularRoadmap(
        roadmap_id="so-core",
        title="Sistemas Operativos Troncal",
        version="1.0.0",
        nodes={node.node_id: node},
        dependencies=(dep,),
        canonical_revision_id="0" * 64,
    )
    with pytest.raises(ValidationError):
        roadmap.version = "1.0.1"  # type: ignore[misc]

    proposal = RoadmapProposal(
        proposal_id="prop-1",
        roadmap_id="so-core",
        source_agent="socratic-tutor",
        action=ProposalAction.ADD_DEPENDENCY,
        rationale="Reforzar sincronización antes de memoria virtual",
    )
    with pytest.raises(ValidationError):
        proposal.applied = True  # type: ignore[misc]


def test_node_id_validation_pattern():
    """Verify node_id must conform to regex slug and cannot have spaces."""
    valid_node = _make_dummy_node("valid_node-123")
    assert valid_node.node_id == "valid_node-123"

    with pytest.raises(ValidationError):
        _make_dummy_node("invalid node with spaces")

    with pytest.raises(ValidationError):
        _make_dummy_node("invalid!characters@#")

    with pytest.raises(ValidationError):
        _make_dummy_node("")


def test_node_priority_range():
    """Verify priority is strictly between 1 (core) and 5 (elective)."""
    assert _make_dummy_node().priority == 1

    with pytest.raises(ValidationError):
        RoadmapNode(
            node_id="node-p0",
            title="Node P0",
            description="desc",
            node_type=NodeType.TOPIC,
            notebook_id="fadena-so",
            priority=0,
        )

    with pytest.raises(ValidationError):
        RoadmapNode(
            node_id="node-p6",
            title="Node P6",
            description="desc",
            node_type=NodeType.TOPIC,
            notebook_id="fadena-so",
            priority=6,
        )


def test_canonical_revision_id_format():
    """Verify canonical_revision_id must be exactly 64 hex characters."""
    node = _make_dummy_node()
    roadmap = CurricularRoadmap(
        roadmap_id="so-core",
        title="Sistemas Operativos",
        version="1.0.0",
        nodes={node.node_id: node},
        dependencies=(),
        canonical_revision_id="a" * 64,
    )
    assert roadmap.canonical_revision_id == "a" * 64

    # Invalid length
    with pytest.raises(ValidationError):
        CurricularRoadmap(
            roadmap_id="so-core",
            title="Sistemas Operativos",
            version="1.0.0",
            nodes={node.node_id: node},
            dependencies=(),
            canonical_revision_id="short_hash",
        )

    # Invalid non-hex characters
    with pytest.raises(ValidationError):
        CurricularRoadmap(
            roadmap_id="so-core",
            title="Sistemas Operativos",
            version="1.0.0",
            nodes={node.node_id: node},
            dependencies=(),
            canonical_revision_id="z" * 64,
        )


def test_closed_enums():
    """Verify all roadmap enums contain expected closed variants."""
    assert set(NodeType) == {
        NodeType.TOPIC,
        NodeType.COMPETENCY,
        NodeType.LAB,
    }
    assert set(DependencyType) == {
        DependencyType.HARD,
        DependencyType.SOFT,
    }
    assert set(ProposalAction) == {
        ProposalAction.ADD_NODE,
        ProposalAction.REMOVE_NODE,
        ProposalAction.ADD_DEPENDENCY,
        ProposalAction.REMOVE_DEPENDENCY,
        ProposalAction.UPDATE_METADATA,
    }
