"""Unit tests for RoadmapLoader in Subsystem S5.1."""

from pathlib import Path
import pytest

from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapSerializationError,
)
from study_engine.roadmap.loader import RoadmapLoader


_VALID_YAML_LIST = """
roadmap_id: so-troncal
title: Sistemas Operativos Troncal
version: "1.0.0"
nodes:
  - node_id: proc-intro
    title: Concepto de Proceso
    description: Definición de proceso y PCB
    node_type: TOPIC
    notebook_id: fadena-so
    priority: 1
    target_competencies:
      - explicar-pcb
    estimated_minutes: 45
  - node_id: proc-scheduling
    title: Planificación de CPU
    description: Algoritmos de planificación
    node_type: TOPIC
    notebook_id: fadena-so
    priority: 2
dependencies:
  - source_node_id: proc-intro
    target_node_id: proc-scheduling
    dependency_type: HARD
    rationale: Necesario entender procesos antes de planificarlos
"""

_VALID_YAML_DICT = """
roadmap_id: redes-troncal
title: Redes Troncal
version: "2.0.0"
nodes:
  net-osi:
    title: Modelo OSI
    description: Capas y encapsulamiento
    node_type: TOPIC
    notebook_id: fadena-redes
    priority: 1
  net-tcp:
    title: Protocolo TCP
    description: 3-way handshake y control de flujo
    node_type: TOPIC
    notebook_id: fadena-redes
    priority: 2
dependencies:
  - source_node_id: net-osi
    target_node_id: net-tcp
    dependency_type: HARD
"""


def test_roadmap_loader_from_yaml_string():
    """Verify loading from valid YAML text string."""
    roadmap = RoadmapLoader.load_from_yaml(_VALID_YAML_LIST)
    assert isinstance(roadmap, CurricularRoadmap)
    assert roadmap.roadmap_id == "so-troncal"
    assert roadmap.title == "Sistemas Operativos Troncal"
    assert len(roadmap.nodes) == 2
    assert "proc-intro" in roadmap.nodes
    assert "proc-scheduling" in roadmap.nodes
    assert len(roadmap.dependencies) == 1
    dep = roadmap.dependencies[0]
    assert dep.source_node_id == "proc-intro"
    assert dep.target_node_id == "proc-scheduling"
    assert dep.dependency_type == DependencyType.HARD
    assert len(roadmap.canonical_revision_id) == 64


def test_roadmap_loader_dict_format():
    """Verify loading YAML when nodes are provided as a dictionary mapping."""
    roadmap = RoadmapLoader.load_from_yaml(_VALID_YAML_DICT)
    assert roadmap.roadmap_id == "redes-troncal"
    assert "net-osi" in roadmap.nodes
    assert roadmap.nodes["net-osi"].node_id == "net-osi"
    assert roadmap.nodes["net-osi"].node_type == NodeType.TOPIC


def test_roadmap_loader_from_file(tmp_path: Path):
    """Verify loading roadmap directly from a filesystem file path."""
    yaml_file = tmp_path / "sample_roadmap.yaml"
    yaml_file.write_text(_VALID_YAML_LIST, encoding="utf-8")

    roadmap = RoadmapLoader.load_from_yaml(yaml_file)
    assert roadmap.roadmap_id == "so-troncal"
    assert len(roadmap.nodes) == 2


def test_roadmap_loader_roundtrip():
    """Verify dump_to_yaml produces YAML that reloads identically."""
    original = RoadmapLoader.load_from_yaml(_VALID_YAML_LIST)
    dumped_yaml = RoadmapLoader.dump_to_yaml(original)

    reloaded = RoadmapLoader.load_from_yaml(dumped_yaml)
    assert reloaded.roadmap_id == original.roadmap_id
    assert reloaded.title == original.title
    assert reloaded.version == original.version
    assert set(reloaded.nodes.keys()) == set(original.nodes.keys())
    assert len(reloaded.dependencies) == len(original.dependencies)
    assert reloaded.canonical_revision_id == original.canonical_revision_id


def test_roadmap_loader_file_not_found():
    """Verify missing file raises RoadmapSerializationError."""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml("/non/existent/path/roadmap.yaml")
    assert "not found" in str(exc_info.value)


def test_roadmap_loader_malformed_yaml():

    """Verify malformed YAML syntax raises RoadmapSerializationError."""
    malformed = "roadmap_id: [broken yaml: invalid"
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(malformed)
    assert "YAML parsing error" in str(exc_info.value)


def test_roadmap_loader_root_not_mapping():
    """Verify non-mapping root raises RoadmapSerializationError."""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml("- item1\n- item2")
    assert "Root of roadmap YAML must be a mapping" in str(exc_info.value)


def test_roadmap_loader_missing_required_fields():
    """Verify missing required roadmap fields raise error."""
    yaml_missing_id = "title: No ID\nnodes: []"
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_missing_id)
    assert "required field 'roadmap_id'" in str(exc_info.value)


def test_roadmap_loader_duplicate_node_ids():
    """Verify duplicate node IDs in nodes list raise error."""
    yaml_dup = """
roadmap_id: dup-map
title: Duplicate
nodes:
  - node_id: node-1
    title: N1
    description: d
    node_type: TOPIC
    notebook_id: nb
  - node_id: node-1
    title: N1 duplicate
    description: d
    node_type: TOPIC
    notebook_id: nb
"""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_dup)
    assert "Duplicate node_id 'node-1'" in str(exc_info.value)


def test_roadmap_loader_empty_nodes_error():
    """Verify roadmap without nodes raises RoadmapSerializationError."""
    yaml_empty = "roadmap_id: empty-map\ntitle: Empty\nnodes: []"
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_empty)
    assert "must contain at least one node" in str(exc_info.value)


def test_roadmap_loader_invalid_dependencies():
    """Verify invalid dependencies format raises error."""
    # Not a list
    yaml_dep_not_list = """
roadmap_id: dep-not-list
title: Dep test
nodes:
  - node_id: n1
    title: N1
    description: d
    node_type: TOPIC
    notebook_id: nb
dependencies: "invalid"
"""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_dep_not_list)
    assert "'dependencies' field must be a list" in str(exc_info.value)

    # Item not a dict
    yaml_dep_item_not_dict = """
roadmap_id: dep-item-not-dict
title: Dep test
nodes:
  - node_id: n1
    title: N1
    description: d
    node_type: TOPIC
    notebook_id: nb
dependencies:
  - "not-a-dict"
"""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_dep_item_not_dict)
    assert "Dependency at index 0 must be a dictionary" in str(exc_info.value)


def test_roadmap_loader_dag_validation_failure_in_yaml():
    """Verify cycle in YAML raises DAG structural validation failed."""
    yaml_cycle = """
roadmap_id: cycle-map
title: Cycle
nodes:
  - node_id: a
    title: A
    description: d
    node_type: TOPIC
    notebook_id: nb
  - node_id: b
    title: B
    description: d
    node_type: TOPIC
    notebook_id: nb
dependencies:
  - source_node_id: a
    target_node_id: b
    dependency_type: HARD
  - source_node_id: b
    target_node_id: a
    dependency_type: HARD
"""
    with pytest.raises(RoadmapSerializationError) as exc_info:
        RoadmapLoader.load_from_yaml(yaml_cycle)
    assert "DAG structural validation failed" in str(exc_info.value)
