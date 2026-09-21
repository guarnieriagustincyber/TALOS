"""Unit tests for RoadmapDAG and graph algorithms in Subsystem S5.1."""

import pytest

from study_engine.roadmap.contracts import (
    DependencyType,
    MissingNodeReferenceError,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
    SelfLoopDependencyError,
)
from study_engine.roadmap.engine import (
    RoadmapDAG,
    compute_canonical_revision_id,
)


def _make_node(node_id: str, priority: int = 3) -> RoadmapNode:
    return RoadmapNode(
        node_id=node_id,
        title=f"Node {node_id}",
        description="description",
        node_type=NodeType.TOPIC,
        notebook_id="fadena-so",
        priority=priority,
    )


def test_topological_sort_linear():
    """Verify linear chain A -> B -> C respects order."""
    nodes = {
        "c": _make_node("c", priority=1),
        "b": _make_node("b", priority=2),
        "a": _make_node("a", priority=3),
    }
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="b",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="b",
            target_node_id="c",
            dependency_type=DependencyType.HARD,
        ),
    )
    dag = RoadmapDAG(nodes=nodes, dependencies=deps)
    order = dag.get_topological_order()
    assert order == ("a", "b", "c")


def test_topological_sort_prerequisite_dominates_priority():
    """Verify prerequisites precede dependents regardless of priority."""

    # Node 'd' has priority 1 (highest), but depends on 'a' (priority 5).
    # 'a' MUST precede 'd' in topological order!
    nodes = {
        "d": _make_node("d", priority=1),
        "a": _make_node("a", priority=5),
        "x": _make_node("x", priority=1),
    }
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="d",
            dependency_type=DependencyType.HARD,
        ),
    )
    dag = RoadmapDAG(nodes=nodes, dependencies=deps)
    order = dag.get_topological_order()

    # 'x' is available with priority 1, 'a' is available with priority 5.
    # 'd' cannot be visited until 'a' is visited!
    assert order.index("a") < order.index("d")
    assert order == ("x", "a", "d")


def test_topological_sort_diamond_with_tie_breaking():
    """Verify diamond DAG resolves tie-breaks deterministically."""
    # a -> b (p2), a -> c (p1), b -> d, c -> d
    nodes = {
        "a": _make_node("a", priority=3),
        "b": _make_node("b", priority=2),
        "c": _make_node("c", priority=1),
        "d": _make_node("d", priority=3),
    }
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="b",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="a",
            target_node_id="c",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="b",
            target_node_id="d",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="c",
            target_node_id="d",
            dependency_type=DependencyType.HARD,
        ),
    )
    dag = RoadmapDAG(nodes=nodes, dependencies=deps)
    order = dag.get_topological_order()
    # 'c' (p1) is chosen before 'b' (p2)
    assert order == ("a", "c", "b", "d")


def test_unlock_evaluator_hard_vs_soft():
    """Verify HARD dependencies block unlocking while SOFT do not."""
    # root -> child_hard (HARD)
    # root -> child_soft (SOFT)
    nodes = {
        "root": _make_node("root"),
        "child_hard": _make_node("child_hard"),
        "child_soft": _make_node("child_soft"),
    }
    deps = (
        RoadmapDependency(
            source_node_id="root",
            target_node_id="child_hard",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="root",
            target_node_id="child_soft",
            dependency_type=DependencyType.SOFT,
        ),
    )
    dag = RoadmapDAG(nodes=nodes, dependencies=deps)

    # 1. Initially (nothing satisfied): root and child_soft are unlocked
    unlocked_init = dag.get_unlocked_nodes(satisfied_node_ids=set())
    assert "root" in unlocked_init
    assert "child_soft" in unlocked_init
    assert "child_hard" not in unlocked_init

    # 2. When 'root' is satisfied: child_hard unlocks
    unlocked_after = dag.get_unlocked_nodes(satisfied_node_ids={"root"})
    assert "child_hard" in unlocked_after
    assert "root" not in unlocked_after  # Already satisfied


def test_canonical_revision_id_stability():
    """Verify revision ID is deterministic regardless of dict order."""
    n1 = _make_node("node-1")
    n2 = _make_node("node-2")
    dep = RoadmapDependency(
        source_node_id="node-1",
        target_node_id="node-2",
        dependency_type=DependencyType.HARD,
    )

    rev1 = compute_canonical_revision_id(
        roadmap_id="map-1",
        title="Title",
        version="1.0.0",
        nodes={"node-1": n1, "node-2": n2},
        dependencies=(dep,),
    )

    # Inverted dictionary insertion order
    rev2 = compute_canonical_revision_id(
        roadmap_id="map-1",
        title="Title",
        version="1.0.0",
        nodes={"node-2": n2, "node-1": n1},
        dependencies=(dep,),
    )
    assert rev1 == rev2
    assert len(rev1) == 64

    # Any modification changes revision ID
    rev_diff = compute_canonical_revision_id(
        roadmap_id="map-1",
        title="Title Modified",
        version="1.0.0",
        nodes={"node-1": n1, "node-2": n2},
        dependencies=(dep,),
    )
    assert rev_diff != rev1


def test_dag_missing_reference_error():
    """Verify non-existent node references raise MissingNodeReferenceError."""
    nodes = {"a": _make_node("a")}

    deps = (

        RoadmapDependency(
            source_node_id="a",
            target_node_id="b",
            dependency_type=DependencyType.HARD,
        ),
    )
    with pytest.raises(MissingNodeReferenceError):
        RoadmapDAG(nodes=nodes, dependencies=deps)


def test_dag_self_loop_error():
    """Verify self-loops raise SelfLoopDependencyError."""
    nodes = {"a": _make_node("a")}
    deps = (
        RoadmapDependency(
            source_node_id="a",
            target_node_id="a",
            dependency_type=DependencyType.HARD,
        ),
    )
    with pytest.raises(SelfLoopDependencyError):
        RoadmapDAG(nodes=nodes, dependencies=deps)


def test_dag_from_roadmap_and_queries():
    """Verify from_roadmap, properties, prerequisites, and dependents."""
    from study_engine.roadmap.contracts import CurricularRoadmap

    na = _make_node("a")
    nb = _make_node("b")
    dep = RoadmapDependency(
        source_node_id="a",
        target_node_id="b",
        dependency_type=DependencyType.HARD,
    )
    roadmap = CurricularRoadmap(
        roadmap_id="map-1",
        title="Title",
        version="1.0.0",
        nodes={"a": na, "b": nb},
        dependencies=(dep,),
        canonical_revision_id="0" * 64,
    )
    dag = RoadmapDAG.from_roadmap(roadmap)
    assert set(dag.nodes.keys()) == {"a", "b"}
    assert len(dag.dependencies) == 1

    # Prerequisites of 'b'
    prereqs = dag.get_prerequisites("b", hard_only=True)
    assert len(prereqs) == 1
    assert prereqs[0].source_node_id == "a"

    # Dependents of 'a'
    deps_a = dag.get_dependents("a", hard_only=True)
    assert len(deps_a) == 1
    assert deps_a[0].target_node_id == "b"

    # Query non-existent node raises error
    with pytest.raises(MissingNodeReferenceError):
        dag.get_prerequisites("non-existent")
    with pytest.raises(MissingNodeReferenceError):
        dag.get_dependents("non-existent")


def test_dag_missing_source_node_error():
    """Verify missing source node raises MissingNodeReferenceError."""
    nodes = {"b": _make_node("b")}
    deps = (
        RoadmapDependency(
            source_node_id="missing-a",
            target_node_id="b",
            dependency_type=DependencyType.HARD,
        ),
    )
    with pytest.raises(MissingNodeReferenceError):
        RoadmapDAG(nodes=nodes, dependencies=deps)
