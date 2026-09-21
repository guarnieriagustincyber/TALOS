"""Adversarial tests for Subsystem S5.1 (Curricular Roadmap).

Validates strict security and structural boundaries:
- Direct and transitive dependency cycles
- Isolated cycles in disconnected components
- Self-loops
- Dangling edges (referencing non-existent nodes)
- YAML code injection prevention
- Immutable containment against post-creation tampering
"""

import pytest
from pydantic import ValidationError

from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    CyclicDependencyError,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
    RoadmapSerializationError,
    SelfLoopDependencyError,
)
from study_engine.roadmap.engine import RoadmapDAG
from study_engine.roadmap.loader import RoadmapLoader


def _make_node(node_id: str) -> RoadmapNode:
    return RoadmapNode(
        node_id=node_id,
        title=f"Node {node_id}",
        description="desc",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=3,
    )


def test_adversarial_direct_cycle():
    """Verify 2-node cycle A -> B -> A raises CyclicDependencyError."""

    nodes = {"a": _make_node("a"), "b": _make_node("b")}
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="b",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="b",
            target_node_id="a",
            dependency_type=DependencyType.HARD,
        ),
    )
    with pytest.raises(CyclicDependencyError) as exc_info:
        RoadmapDAG(nodes=nodes, dependencies=deps)
    assert "Cyclic dependency detected" in str(exc_info.value)


def test_adversarial_transitive_cycle():
    """Verify multi-node cycle A -> B -> C -> D -> A is rejected."""
    nodes = {k: _make_node(k) for k in ("a", "b", "c", "d")}
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="b",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="b",
            target_node_id="c",
            dependency_type=DependencyType.SOFT,
        ),
        RoadmapDependency(
            source_node_id="c",
            target_node_id="d",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="d",
            target_node_id="a",
            dependency_type=DependencyType.HARD,
        ),
    )
    with pytest.raises(CyclicDependencyError) as exc_info:
        RoadmapDAG(nodes=nodes, dependencies=deps)
    assert "Cyclic dependency detected" in str(exc_info.value)


def test_adversarial_disconnected_cycle():
    """Verify a cycle hidden in an isolated sub-component is detected."""
    # Component 1: root -> child (acyclic)
    # Component 2: c1 -> c2 -> c1 (cyclic)
    nodes = {k: _make_node(k) for k in ("root", "child", "c1", "c2")}
    deps = (
        RoadmapDependency(
            source_node_id="root",
            target_node_id="child",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="c1",
            target_node_id="c2",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="c2",
            target_node_id="c1",
            dependency_type=DependencyType.HARD,
        ),
    )
    with pytest.raises(CyclicDependencyError) as exc_info:
        RoadmapDAG(nodes=nodes, dependencies=deps)
    assert "Cyclic dependency detected" in str(exc_info.value)
    assert "c1" in str(exc_info.value)
    assert "c2" in str(exc_info.value)


def test_adversarial_self_loop():
    """Verify node depending on itself triggers SelfLoopDependencyError."""
    nodes = {"a": _make_node("a")}
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="a",
            dependency_type=DependencyType.SOFT,
        ),
    )
    with pytest.raises(SelfLoopDependencyError):
        RoadmapDAG(nodes=nodes, dependencies=deps)


def test_adversarial_dangling_dependency_in_yaml():
    """Verify YAML referencing undeclared node raises error."""
    yaml_dangling = """

roadmap_id: test-dangling
title: Dangling test
nodes:
  - node_id: node-1
    title: N1
    description: d
    node_type: TOPIC
    notebook_id: nb
dependencies:
  - source_node_id: node-1
    target_node_id: ghost-node-99
    dependency_type: HARD
"""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_dangling)
    assert "ghost-node-99" in str(exc_info.value)


def test_adversarial_yaml_python_code_injection():
    """Verify PyYAML safe_load rejects Python object execution tags."""
    # Attempting arbitrary code execution via PyYAML tags
    malicious_yaml = """
roadmap_id: injection-test
title: Injection
nodes:
  - node_id: !!python/object/apply:os.system ['echo PWNED']
    title: Injected
    description: d
    node_type: TOPIC
    notebook_id: nb
"""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(malicious_yaml)
    assert "YAML parsing error" in str(exc_info.value)


def test_adversarial_post_creation_tampering():
    """Verify returned CurricularRoadmap is frozen and resists tampering."""
    yaml_clean = """
roadmap_id: immutable-map
title: Immutable
nodes:
  - node_id: n1
    title: N1
    description: d
    node_type: TOPIC
    notebook_id: nb
"""
    roadmap = RoadmapLoader.load_from_yaml(yaml_clean)
    assert isinstance(roadmap, CurricularRoadmap)

    # 1. Attribute modification forbidden
    with pytest.raises(ValidationError):
        roadmap.title = "Hacked Title"  # type: ignore[misc]

    # 2. Node modification forbidden
    with pytest.raises(ValidationError):
        roadmap.nodes["n1"].priority = 1  # type: ignore[misc]
