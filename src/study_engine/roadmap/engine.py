"""DAG engine and graph algorithms for Subsystem S5.1 (Curricular Roadmap).

INVARIANTS:
1. S5.1 has zero knowledge of student state or evidence ledgers.
2. Acyclic DAG: directed cycles raise CyclicDependencyError immediately.
3. Topological ordering is strictly deterministic (priority + node_id).
4. Prerequisite constraints strictly dominate priorities.
5. Canonical revision ID is derived from a reproducible representation.
"""

import hashlib
import json
from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple

from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    CyclicDependencyError,
    DependencyType,
    MissingNodeReferenceError,
    RoadmapDependency,
    RoadmapNode,
    SelfLoopDependencyError,
)


def compute_canonical_revision_id(
    roadmap_id: str,
    title: str,
    version: str,
    nodes: Dict[str, RoadmapNode],
    dependencies: Tuple[RoadmapDependency, ...],
) -> str:
    """Compute deterministic SHA-256 digest from canonical structure.

    Guarantees revision ID is independent of YAML formatting or order.
    """
    canonical_nodes: List[Dict[str, Any]] = []
    for node_id in sorted(nodes.keys()):
        node = nodes[node_id]
        canonical_nodes.append(
            {
                "node_id": node.node_id,
                "title": node.title,
                "description": node.description,
                "node_type": node.node_type.value,
                "notebook_id": node.notebook_id,
                "priority": node.priority,
                "target_competencies": sorted(node.target_competencies),
                "estimated_minutes": node.estimated_minutes,
                "metadata": dict(sorted(node.metadata.items())),
            }
        )

    canonical_deps: List[Dict[str, Any]] = []
    sorted_deps = sorted(
        dependencies,
        key=lambda d: (
            d.source_node_id,
            d.target_node_id,
            d.dependency_type.value,
        ),
    )
    for dep in sorted_deps:
        canonical_deps.append(
            {
                "source_node_id": dep.source_node_id,
                "target_node_id": dep.target_node_id,
                "dependency_type": dep.dependency_type.value,

                "rationale": dep.rationale,
            }
        )

    canonical_payload = {
        "roadmap_id": roadmap_id,
        "title": title,
        "version": version,
        "nodes": canonical_nodes,
        "dependencies": canonical_deps,
    }

    raw_json = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()


class RoadmapDAG:
    """Directed Acyclic Graph governing curricular progression."""

    def __init__(

        self,
        nodes: Dict[str, RoadmapNode],
        dependencies: Tuple[RoadmapDependency, ...] = (),
    ) -> None:
        self._nodes = dict(nodes)
        self._dependencies = dependencies
        self._adj_out: Dict[str, List[RoadmapDependency]] = defaultdict(list)
        self._adj_in: Dict[str, List[RoadmapDependency]] = defaultdict(list)

        self._validate_and_build_graph()

    @classmethod
    def from_roadmap(cls, roadmap: CurricularRoadmap) -> "RoadmapDAG":
        """Construct RoadmapDAG from a CurricularRoadmap instance."""
        return cls(nodes=roadmap.nodes, dependencies=roadmap.dependencies)

    @property
    def nodes(self) -> Dict[str, RoadmapNode]:
        """Return all nodes in graph."""
        return dict(self._nodes)

    @property
    def dependencies(self) -> Tuple[RoadmapDependency, ...]:
        """Return all dependencies in graph."""
        return self._dependencies

    def _validate_and_build_graph(self) -> None:
        """Validate integrity, missing references, self-loops, and cycles."""
        for dep in self._dependencies:
            # 1. Missing reference check
            if dep.source_node_id not in self._nodes:
                raise MissingNodeReferenceError(
                    f"Dependency source node '{dep.source_node_id}' does not "
                    f"exist in roadmap nodes."
                )
            if dep.target_node_id not in self._nodes:
                raise MissingNodeReferenceError(
                    f"Dependency target node '{dep.target_node_id}' does not "
                    f"exist in roadmap nodes."
                )

            # 2. Self-loop check
            if dep.source_node_id == dep.target_node_id:
                raise SelfLoopDependencyError(
                    f"Self-loop dependency detected on node "
                    f"'{dep.source_node_id}'."
                )

            self._adj_out[dep.source_node_id].append(dep)
            self._adj_in[dep.target_node_id].append(dep)

        # 3. Cycle check via Kahn's algorithm
        in_degree: Dict[str, int] = {k: 0 for k in self._nodes}
        for dep in self._dependencies:
            in_degree[dep.target_node_id] += 1

        queue: deque[str] = deque(
            [node_id for node_id, deg in in_degree.items() if deg == 0]
        )
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for edge in self._adj_out.get(curr, []):
                in_degree[edge.target_node_id] -= 1
                if in_degree[edge.target_node_id] == 0:
                    queue.append(edge.target_node_id)

        if visited_count != len(self._nodes):
            # Graph has at least one cycle
            cycle_nodes = [
                node_id for node_id, deg in in_degree.items() if deg > 0
            ]
            nodes_str = sorted(cycle_nodes)
            raise CyclicDependencyError(
                f"Cyclic dependency detected among nodes: {nodes_str}."
            )

    def get_topological_order(self) -> Tuple[str, ...]:

        """Compute deterministic topological ordering of all nodes.

        TIE-BREAKING:
        Among nodes whose prerequisites are all satisfied:
        1. priority (ascending: 1=trunk before 5=elective)
        2. node_id (lexicographic ascending)
        """
        in_degree: Dict[str, int] = {k: 0 for k in self._nodes}
        for dep in self._dependencies:
            in_degree[dep.target_node_id] += 1

        # Available candidates with 0 in-degree
        available: List[str] = [
            node_id for node_id, deg in in_degree.items() if deg == 0
        ]

        result: List[str] = []

        while available:
            # Deterministic selection: min priority, then min node_id
            available.sort(
                key=lambda nid: (self._nodes[nid].priority, nid)
            )
            selected = available.pop(0)
            result.append(selected)

            for edge in self._adj_out.get(selected, []):
                in_degree[edge.target_node_id] -= 1
                if in_degree[edge.target_node_id] == 0:
                    available.append(edge.target_node_id)

        return tuple(result)

    def get_unlocked_nodes(
        self, satisfied_node_ids: Set[str]
    ) -> Tuple[str, ...]:
        """Compute nodes whose HARD prerequisites are fully satisfied.

        SOFT dependencies do NOT block unlocking.
        Returns nodes sorted deterministically by (priority, node_id).
        """
        unlocked: List[str] = []

        for node_id, node in self._nodes.items():
            if node_id in satisfied_node_ids:
                # Already satisfied, omit from unlocked candidates
                continue

            incoming_hard = [
                dep for dep in self._adj_in.get(node_id, [])
                if dep.dependency_type == DependencyType.HARD
            ]

            # All hard prerequisites must be present in satisfied_node_ids
            all_satisfied = all(
                d.source_node_id in satisfied_node_ids for d in incoming_hard
            )
            if all_satisfied:
                unlocked.append(node_id)

        unlocked.sort(key=lambda nid: (self._nodes[nid].priority, nid))

        return tuple(unlocked)

    def get_prerequisites(
        self, node_id: str, hard_only: bool = True
    ) -> Tuple[RoadmapDependency, ...]:
        """Return incoming prerequisite dependencies for a given node."""
        if node_id not in self._nodes:
            raise MissingNodeReferenceError(f"Node '{node_id}' not found.")
        deps = self._adj_in.get(node_id, [])
        if hard_only:
            return tuple(
                d for d in deps if d.dependency_type == DependencyType.HARD
            )
        return tuple(deps)

    def get_dependents(
        self, node_id: str, hard_only: bool = True
    ) -> Tuple[RoadmapDependency, ...]:
        """Return outgoing dependent dependencies for a given node."""
        if node_id not in self._nodes:
            raise MissingNodeReferenceError(f"Node '{node_id}' not found.")
        deps = self._adj_out.get(node_id, [])
        if hard_only:
            return tuple(
                d for d in deps if d.dependency_type == DependencyType.HARD
            )
        return tuple(deps)
