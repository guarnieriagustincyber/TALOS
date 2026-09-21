"""Unit tests for CurriculumRegistry service.

INVARIANTS:
1. Validates discovery and parsing of Roadmaps, Tasks, Rubrics, and Alignments.
2. In-memory caching preserves identity and eliminates redundant disk I/O.
3. Fail-Closed queries: unmapped nodes strictly raise CurriculumNotFoundError.
4. Error handling: missing files raise CurriculumNotFoundError, malformed data raises CurriculumValidationError.
"""

from pathlib import Path
import pytest

from study_engine.curriculum.registry import (
    CurriculumNotFoundError,
    CurriculumRegistry,
    CurriculumValidationError,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import (
    DIMENSION_FOUNDATIONS,
    DIMENSION_LIVE_DEMO,
)
from study_engine.curriculum.task_contracts import TaskDifficulty
from study_engine.roadmap.contracts import NodeType


@pytest.fixture
def registry() -> CurriculumRegistry:
    """Fixture providing a standard CurriculumRegistry pointing to data/curriculum."""
    return CurriculumRegistry()


def test_registry_initialization(registry: CurriculumRegistry) -> None:
    """Registry initializes with correct root and subdirectories."""
    assert registry.root_dir.is_dir()
    assert registry.root_dir.name == "curriculum"


def test_load_roadmap_success(registry: CurriculumRegistry) -> None:
    """Loads cybersecurity_v1.yaml roadmap and validates DAG structure."""
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    assert roadmap.roadmap_id == "ROADMAP-CYBERSECURITY-V1"
    assert len(roadmap.nodes) == 6
    assert len(roadmap.dependencies) == 6

    # Invariants on nodes
    node_sec01 = roadmap.nodes["SEC-01-C-PTR"]
    assert node_sec01.node_type == NodeType.TOPIC
    assert node_sec01.priority == 1

    node_sec05 = roadmap.nodes["SEC-05-BIN-SEC"]
    assert node_sec05.node_type == NodeType.LAB
    assert "COMP-CRYPTO-HASHING" in node_sec05.target_competencies

    # Invariants on dependencies
    hard_deps = [d for d in roadmap.dependencies if d.dependency_type.value == "HARD"]
    assert len(hard_deps) == 6


def test_load_roadmap_caching(registry: CurriculumRegistry) -> None:
    """Subsequent loads return identical cached instance."""
    rm1 = registry.load_roadmap("cybersecurity_v1.yaml")
    rm2 = registry.load_roadmap("cybersecurity_v1.yaml")
    rm3 = registry.load_roadmap("ROADMAP-CYBERSECURITY-V1")
    assert rm1 is rm2
    assert rm1 is rm3

    registry.clear_cache()
    rm4 = registry.load_roadmap("cybersecurity_v1.yaml")
    assert rm4 is not rm1
    assert rm4.canonical_revision_id == rm1.canonical_revision_id


def test_load_task_success(registry: CurriculumRegistry) -> None:
    """Loads task_sec05_file_hasher.json and validates requirements."""
    task = registry.load_task("task_sec05_file_hasher.json")
    assert task.task_id == "TASK-SEC05-HASHER"
    assert task.curriculum_node_id == "SEC-05-BIN-SEC"
    assert task.difficulty == TaskDifficulty.INTERMEDIATE
    assert len(task.required_artifacts) == 1

    art_req = task.required_artifacts[0]
    assert art_req.requirement_id == "output_hash.txt"
    assert art_req.min_size_bytes == 64
    assert art_req.max_size_bytes == 128


def test_load_rubric_success(registry: CurriculumRegistry) -> None:
    """Loads rubric_sec05_deterministic.json and validates dimensions and weights."""
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")
    assert rubric.rubric_id == "RUBRIC-SEC05-DETERMINISTIC"
    assert len(rubric.dimensions) == 2

    dim_ids = [d.dimension_id for d in rubric.dimensions]
    assert DIMENSION_LIVE_DEMO in dim_ids
    assert DIMENSION_FOUNDATIONS in dim_ids

    total_weight = sum(d.weight for d in rubric.dimensions)
    assert abs(total_weight - 1.0) < 1e-6
    assert rubric.default_pass_level == PerformanceLevel.N3_COMPETENT


def test_load_alignment_matrix_success(registry: CurriculumRegistry) -> None:
    """Loads cybersecurity_v1_alignment.json and validates node alignments."""
    matrix = registry.load_alignment("cybersecurity_v1_alignment.json")
    assert matrix.matrix_id == "ALIGN-CYBERSECURITY-V1"
    assert matrix.roadmap_id == "ROADMAP-CYBERSECURITY-V1"
    assert len(matrix.alignments) == 6
    assert "SEC-01-C-PTR" in matrix.alignments
    assert "SEC-05-BIN-SEC" in matrix.alignments


def test_get_scoped_sources_for_node(registry: CurriculumRegistry) -> None:
    """Resolves authorized document scopes for a specific node."""
    scopes = registry.get_scoped_sources_for_node("SEC-05-BIN-SEC")
    assert len(scopes) == 2

    primary = next(s for s in scopes if s.is_primary)
    assert primary.document_id == "prog_archivos.pdf"
    assert primary.page_start == 1
    assert primary.page_end == 15

    secondary = next(s for s in scopes if not s.is_primary)
    assert secondary.document_id == "so_memoria.pdf"
    assert secondary.page_start == 5
    assert secondary.page_end == 12


def test_get_scoped_sources_unknown_node_fails_closed(registry: CurriculumRegistry) -> None:
    """Unknown node raises CurriculumNotFoundError (fail-closed epistemic boundary)."""
    with pytest.raises(CurriculumNotFoundError, match="Fail-closed: retrieval blocked"):
        registry.get_scoped_sources_for_node("UNKNOWN-NODE-999")


def test_not_found_errors(registry: CurriculumRegistry) -> None:
    """Non-existent artifacts raise CurriculumNotFoundError."""
    with pytest.raises(CurriculumNotFoundError):
        registry.load_roadmap("non_existent_roadmap.yaml")

    with pytest.raises(CurriculumNotFoundError):
        registry.load_task("non_existent_task.json")

    with pytest.raises(CurriculumNotFoundError):
        registry.load_rubric("non_existent_rubric.json")

    with pytest.raises(CurriculumNotFoundError):
        registry.load_alignment("non_existent_alignment.json")


def test_validation_errors(tmp_path: Path) -> None:
    """Malformed files raise CurriculumValidationError."""
    reg = CurriculumRegistry(root_dir=tmp_path)
    (tmp_path / "roadmaps").mkdir()
    (tmp_path / "tasks").mkdir()

    bad_yaml = tmp_path / "roadmaps" / "bad.yaml"
    bad_yaml.write_text("not a valid roadmap mapping: [1, 2, 3]", encoding="utf-8")

    with pytest.raises(CurriculumValidationError):
        reg.load_roadmap("bad.yaml")

    bad_json = tmp_path / "tasks" / "bad.json"
    bad_json.write_text("{'invalid_json': True}", encoding="utf-8")

    with pytest.raises(CurriculumValidationError):
        reg.load_task("bad.json")
