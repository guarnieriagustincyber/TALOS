"""YAML/JSON loader and serializer for Subsystem S5.1 (Curricular Roadmap).

INVARIANTS:
1. YAML editing is a first-class, sovereign operation for human users.
2. Loader validates schemas, cycles, missing references, and self-loops.
3. Canonical revision ID is automatically derived upon loading.
"""

from pathlib import Path
from typing import Any, Dict, List, Union
import yaml  # type: ignore[import-untyped]


from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    RoadmapDependency,
    RoadmapNode,
    RoadmapSerializationError,
)
from study_engine.roadmap.engine import (
    RoadmapDAG,
    compute_canonical_revision_id,
)


class RoadmapLoader:
    """Sovereign loader and dumper for Curricular Roadmap definitions."""

    @staticmethod
    def load_from_yaml(source: Union[str, Path]) -> CurricularRoadmap:
        """Parse, validate, and construct a CurricularRoadmap from YAML.

        Args:
            source: File path to a YAML document or raw YAML text string.

        Returns:
            Fully validated CurricularRoadmap with canonical revision ID.

        Raises:
            RoadmapSerializationError: If YAML syntax, types, or DAG fail.
        """
        raw_text: str
        is_file_path = False
        if isinstance(source, Path):
            is_file_path = True
        elif isinstance(source, str):
            if source.endswith((".yaml", ".yml")):
                is_file_path = True
            elif "\n" not in source and ":" not in source:
                p = Path(source)
                if p.is_file():
                    is_file_path = True

        if is_file_path:
            p = Path(source)
            if not p.is_file():
                raise RoadmapSerializationError(
                    f"Roadmap file '{source}' not found."
                )
            try:
                raw_text = p.read_text(encoding="utf-8")
            except Exception as exc:
                raise RoadmapSerializationError(
                    f"Failed to read roadmap file '{source}': {exc}"
                ) from exc
        else:
            raw_text = str(source)

        try:
            data = yaml.safe_load(raw_text)

        except yaml.YAMLError as exc:
            raise RoadmapSerializationError(
                f"YAML parsing error: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise RoadmapSerializationError(
                "Root of roadmap YAML must be a mapping (dictionary)."
            )

        roadmap_id = data.get("roadmap_id")
        title = data.get("title")
        version = str(data.get("version", "1.0.0"))

        if not roadmap_id or not isinstance(roadmap_id, str):
            raise RoadmapSerializationError(
                "Missing or invalid required field 'roadmap_id'."
            )
        if not title or not isinstance(title, str):
            raise RoadmapSerializationError(
                "Missing or invalid required field 'title'."
            )

        # Parse nodes (supporting either a list of node dicts or a mapping)
        raw_nodes = data.get("nodes", [])
        nodes: Dict[str, RoadmapNode] = {}

        if isinstance(raw_nodes, list):
            for idx, item in enumerate(raw_nodes):
                if not isinstance(item, dict):
                    raise RoadmapSerializationError(
                        f"Node at index {idx} must be a dictionary."
                    )
                try:
                    node = RoadmapNode(**item)
                    if node.node_id in nodes:
                        raise RoadmapSerializationError(
                            f"Duplicate node_id '{node.node_id}' in nodes."
                        )
                    nodes[node.node_id] = node
                except Exception as exc:
                    nid = item.get("node_id", idx)
                    raise RoadmapSerializationError(
                        f"Validation error in node {nid}: {exc}"
                    ) from exc
        elif isinstance(raw_nodes, dict):
            for nid, item in raw_nodes.items():
                if not isinstance(item, dict):
                    raise RoadmapSerializationError(
                        f"Node '{nid}' must be a dictionary."
                    )
                item_copy = dict(item)
                item_copy.setdefault("node_id", nid)
                try:
                    node = RoadmapNode(**item_copy)
                    nodes[node.node_id] = node
                except Exception as exc:
                    raise RoadmapSerializationError(
                        f"Validation error in node '{nid}': {exc}"
                    ) from exc
        else:
            raise RoadmapSerializationError(
                "'nodes' field must be a list or mapping."
            )

        if not nodes:
            raise RoadmapSerializationError(
                "Roadmap must contain at least one node."
            )

        # Parse dependencies
        raw_deps = data.get("dependencies", [])
        dependencies: List[RoadmapDependency] = []

        if not isinstance(raw_deps, list):
            raise RoadmapSerializationError(
                "'dependencies' field must be a list."
            )

        for idx, item in enumerate(raw_deps):
            if not isinstance(item, dict):
                raise RoadmapSerializationError(
                    f"Dependency at index {idx} must be a dictionary."
                )
            try:
                dep = RoadmapDependency(**item)
                dependencies.append(dep)
            except Exception as exc:
                raise RoadmapSerializationError(
                    f"Validation error in dependency at index {idx}: {exc}"
                ) from exc

        deps_tuple = tuple(dependencies)

        # RoadmapDAG enforces acyclicity, self-loops, and references
        try:
            RoadmapDAG(nodes=nodes, dependencies=deps_tuple)
        except Exception as exc:
            raise RoadmapSerializationError(
                f"DAG structural validation failed: {exc}"
            ) from exc

        # Calculate reproducible canonical revision ID
        rev_id = compute_canonical_revision_id(
            roadmap_id=roadmap_id,
            title=title,
            version=version,
            nodes=nodes,
            dependencies=deps_tuple,
        )

        return CurricularRoadmap(
            roadmap_id=roadmap_id,
            title=title,
            version=version,
            nodes=nodes,
            dependencies=deps_tuple,
            canonical_revision_id=rev_id,
        )

    @staticmethod
    def dump_to_yaml(roadmap: CurricularRoadmap) -> str:
        """Serialize a CurricularRoadmap into a clean, human-readable YAML."""
        nodes_list = []
        for node_id in sorted(roadmap.nodes.keys()):
            node = roadmap.nodes[node_id]
            node_dict: Dict[str, Any] = {
                "node_id": node.node_id,
                "title": node.title,
                "description": node.description,
                "node_type": node.node_type.value,
                "notebook_id": node.notebook_id,
                "priority": node.priority,
            }
            if node.target_competencies:
                node_dict["target_competencies"] = list(
                    node.target_competencies
                )
            if node.estimated_minutes is not None:
                node_dict["estimated_minutes"] = node.estimated_minutes
            if node.metadata:
                node_dict["metadata"] = dict(node.metadata)
            nodes_list.append(node_dict)

        deps_list = []

        sorted_deps = sorted(
            roadmap.dependencies,
            key=lambda d: (d.source_node_id, d.target_node_id),
        )
        for dep in sorted_deps:
            dep_dict: Dict[str, Any] = {
                "source_node_id": dep.source_node_id,
                "target_node_id": dep.target_node_id,
                "dependency_type": dep.dependency_type.value,
            }
            if dep.rationale:
                dep_dict["rationale"] = dep.rationale
            deps_list.append(dep_dict)

        payload = {
            "roadmap_id": roadmap.roadmap_id,
            "title": roadmap.title,
            "version": roadmap.version,
            "nodes": nodes_list,
            "dependencies": deps_list,
        }

        res = yaml.dump(
            payload,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        return str(res)
