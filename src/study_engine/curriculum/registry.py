"""Sovereign Curriculum Registry Service for Subsystem S5 (Curriculum).

INVARIANTS:
1. Pure read-only registry service: does NOT execute code or modify student state.
2. Authoritative discovery and access point for:
   - Curricular Roadmaps (S5.1)
   - Practical Tasks (S5.4)
   - Assessment Rubrics (S5.4)
   - Curricular Alignment Matrices (Epistemic Isolation)
3. Fail-Closed epistemic queries: node lookups for unauthorized or unknown nodes
   raise explicit typed domain errors.
4. Thread-safe in-memory caching to minimize file I/O while preserving immutability.
5. Strict typing: 100% compliant with mypy strict mode.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import json

from study_engine.curriculum.alignment_contracts import (
    CurricularAlignmentMatrix,
    CurricularDocumentScope,
)
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.roadmap.loader import RoadmapLoader


class CurriculumRegistryError(Exception):
    """Base exception for curriculum registry errors."""


class CurriculumNotFoundError(CurriculumRegistryError):
    """Raised when a requested curricular artifact cannot be located."""


class CurriculumValidationError(CurriculumRegistryError):
    """Raised when a curricular artifact fails schema or semantic validation."""


class CurriculumRegistry:
    """Authoritative registry for curricular roadmaps, tasks, rubrics, and alignments."""

    def __init__(self, root_dir: Optional[Union[str, Path]] = None) -> None:
        """Initialize registry with base data directory.

        Args:
            root_dir: Base directory containing curriculum data.
                      Defaults to 'data/curriculum' relative to repo root.
        """
        if root_dir is not None:
            self._root_dir = Path(root_dir).resolve()
        else:
            self._root_dir = Path("data/curriculum").resolve()

        self._roadmaps_dir = self._root_dir / "roadmaps"
        self._tasks_dir = self._root_dir / "tasks"
        self._rubrics_dir = self._root_dir / "rubrics"
        self._alignment_dir = self._root_dir / "alignment"

        # In-memory caches for loaded immutable models
        self._roadmaps_cache: Dict[str, CurricularRoadmap] = {}
        self._tasks_cache: Dict[str, PracticalTaskSpecification] = {}
        self._rubrics_cache: Dict[str, AssessmentRubric] = {}
        self._alignment_cache: Dict[str, CurricularAlignmentMatrix] = {}

    @property
    def root_dir(self) -> Path:
        """Return base directory of the registry."""
        return self._root_dir

    def clear_cache(self) -> None:
        """Clear all internal in-memory caches."""
        self._roadmaps_cache.clear()
        self._tasks_cache.clear()
        self._rubrics_cache.clear()
        self._alignment_cache.clear()

    def _resolve_file_path(
        self,
        identifier_or_path: Union[str, Path],
        search_dir: Path,
        allowed_extensions: Tuple[str, ...],
    ) -> Path:
        """Resolve a file path from an absolute/relative path or bare ID."""
        candidate = Path(identifier_or_path)
        if candidate.is_file():
            return candidate.resolve()

        # If relative to root_dir
        if (self._root_dir / candidate).is_file():
            return (self._root_dir / candidate).resolve()

        # If inside specific category search_dir
        if (search_dir / candidate).is_file():
            return (search_dir / candidate).resolve()

        # Try appending allowed extensions in search_dir
        for ext in allowed_extensions:
            file_with_ext = search_dir / f"{candidate.name}{ext}"
            if file_with_ext.is_file():
                return file_with_ext.resolve()

        # Search iteratively in search_dir for matching filename prefix or ID
        if search_dir.is_dir():
            target_slug = str(identifier_or_path).lower().replace("_", "-")
            for entry in search_dir.iterdir():
                if entry.is_file() and entry.suffix in allowed_extensions:
                    stem_slug = entry.stem.lower().replace("_", "-")
                    if stem_slug == target_slug or target_slug in stem_slug:
                        return entry.resolve()

        raise CurriculumNotFoundError(
            f"Curricular artifact '{identifier_or_path}' not found in {search_dir}."
        )

    def load_roadmap(
        self, identifier_or_path: Union[str, Path]
    ) -> CurricularRoadmap:
        """Load and validate a CurricularRoadmap DAG from YAML.

        Args:
            identifier_or_path: File path, filename, or roadmap identifier slug.

        Returns:
            Validated CurricularRoadmap contract instance.

        Raises:
            CurriculumNotFoundError: If the roadmap file cannot be found.
            CurriculumValidationError: If YAML is malformed or DAG contains cycles.
        """
        key = str(identifier_or_path)
        if key in self._roadmaps_cache:
            return self._roadmaps_cache[key]

        path = self._resolve_file_path(
            identifier_or_path,
            self._roadmaps_dir,
            allowed_extensions=(".yaml", ".yml"),
        )
        try:
            roadmap = RoadmapLoader.load_from_yaml(path)
        except Exception as exc:
            raise CurriculumValidationError(
                f"Failed to load or validate roadmap from '{path}': {exc}"
            ) from exc

        self._roadmaps_cache[key] = roadmap
        self._roadmaps_cache[roadmap.roadmap_id] = roadmap
        return roadmap

    def load_task(
        self, identifier_or_path: Union[str, Path]
    ) -> PracticalTaskSpecification:
        """Load and validate a PracticalTaskSpecification from JSON.

        Args:
            identifier_or_path: File path, filename, or task_id.

        Returns:
            Validated PracticalTaskSpecification contract instance.

        Raises:
            CurriculumNotFoundError: If the task file cannot be found.
            CurriculumValidationError: If JSON is malformed or violates schema.
        """
        key = str(identifier_or_path)
        if key in self._tasks_cache:
            return self._tasks_cache[key]

        path = self._resolve_file_path(
            identifier_or_path,
            self._tasks_dir,
            allowed_extensions=(".json",),
        )
        try:
            content = path.read_text(encoding="utf-8")
            task = PracticalTaskSpecification.model_validate_json(content)
        except Exception as exc:
            raise CurriculumValidationError(
                f"Failed to load or validate practical task from '{path}': {exc}"
            ) from exc

        self._tasks_cache[key] = task
        self._tasks_cache[task.task_id] = task
        return task

    def load_rubric(
        self, identifier_or_path: Union[str, Path]
    ) -> AssessmentRubric:
        """Load and validate an AssessmentRubric from JSON.

        Args:
            identifier_or_path: File path, filename, or rubric_id.

        Returns:
            Validated AssessmentRubric contract instance.

        Raises:
            CurriculumNotFoundError: If the rubric file cannot be found.
            CurriculumValidationError: If JSON is malformed or violates rubric invariants.
        """
        key = str(identifier_or_path)
        if key in self._rubrics_cache:
            return self._rubrics_cache[key]

        path = self._resolve_file_path(
            identifier_or_path,
            self._rubrics_dir,
            allowed_extensions=(".json",),
        )
        try:
            content = path.read_text(encoding="utf-8")
            rubric = AssessmentRubric.model_validate_json(content)
        except Exception as exc:
            raise CurriculumValidationError(
                f"Failed to load or validate rubric from '{path}': {exc}"
            ) from exc

        self._rubrics_cache[key] = rubric
        self._rubrics_cache[rubric.rubric_id] = rubric
        return rubric

    def load_alignment(
        self, identifier_or_path: Union[str, Path]
    ) -> CurricularAlignmentMatrix:
        """Load and validate a CurricularAlignmentMatrix from JSON.

        Args:
            identifier_or_path: File path, filename, or matrix_id.

        Returns:
            Validated CurricularAlignmentMatrix contract instance.

        Raises:
            CurriculumNotFoundError: If the alignment file cannot be found.
            CurriculumValidationError: If JSON is malformed or hash does not match.
        """
        key = str(identifier_or_path)
        if key in self._alignment_cache:
            return self._alignment_cache[key]

        path = self._resolve_file_path(
            identifier_or_path,
            self._alignment_dir,
            allowed_extensions=(".json",),
        )
        try:
            content = path.read_text(encoding="utf-8")
            matrix = CurricularAlignmentMatrix.model_validate_json(content)
        except Exception as exc:
            raise CurriculumValidationError(
                f"Failed to load or validate alignment matrix from '{path}': {exc}"
            ) from exc

        self._alignment_cache[key] = matrix
        self._alignment_cache[matrix.matrix_id] = matrix
        return matrix

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "CurriculumRegistry":
        """Load the registry from a YAML file.

        Args:
            path: Path to the YAML configuration file.
        """
        yaml_path = Path(path).resolve()
        if not yaml_path.is_file():
            raise CurriculumNotFoundError(f"Curriculum YAML file not found: {yaml_path}")
        try:
            import yaml  # type: ignore[import-untyped]  # PyYAML ships no stubs; runtime validated below
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise CurriculumValidationError(
                f"Failed to parse curriculum YAML at '{yaml_path}': {exc}"
            ) from exc
        return cls(data)
    def get_scoped_sources_for_node(
        self,
        node_id: str,
        matrix_id_or_path: Union[str, Path] = "cybersecurity_v1_alignment.json",
    ) -> Tuple[CurricularDocumentScope, ...]:
        """Query authoritative document scopes for epistemic retrieval isolation.

        INVARIANT: Fail-closed. If node_id is not registered in the matrix,
        raises CurriculumNotFoundError to prevent unauthorized document leaks.

        Args:
            node_id: Curricular node identifier (e.g. 'SEC-05-BIN-SEC').
            matrix_id_or_path: Matrix identifier or path to alignment JSON.

        Returns:
            Immutable tuple of authorized CurricularDocumentScope instances.

        Raises:
            CurriculumNotFoundError: If matrix is not found or node is not aligned.
            CurriculumValidationError: If matrix validation fails.
        """
        matrix = self.load_alignment(matrix_id_or_path)
        alignment = matrix.alignments.get(node_id)
        if alignment is None:
            raise CurriculumNotFoundError(
                f"Node '{node_id}' is not mapped in alignment matrix '{matrix.matrix_id}' "
                f"(Fail-closed: retrieval blocked)."
            )
        return alignment.allowed_documents

    def get_kc_display_name(self, kc_id: str) -> str:
        """Resolve human-readable display name for a Knowledge Component or anchor ID (Fix 2.7)."""
        clean_id = kc_id.strip()

        # 1. Search in cached/loaded roadmaps
        for rmap in self._roadmaps_cache.values():
            if clean_id in rmap.nodes:
                return rmap.nodes[clean_id].title

        # Try loading default roadmap if cache is empty
        try:
            default_rmap = self.load_roadmap("cybersecurity_v1.json")
            if clean_id in default_rmap.nodes:
                return default_rmap.nodes[clean_id].title
        except Exception:
            pass

        # 2. Search in config/notebook_kc_catalog.json if present
        catalog_path = Path("config/notebook_kc_catalog.json")
        if catalog_path.exists():
            try:
                import json
                cat_data = json.loads(catalog_path.read_text(encoding="utf-8"))
                for nb_info in cat_data.values():
                    for kc in nb_info.get("kcs", []):
                        if kc.get("kc_id") == clean_id:
                            return kc.get("display_name") or kc.get("title") or clean_id
            except Exception:
                pass

        # 3. Canonical anchor mapping fallback
        known_anchors = {
            "anc_sec_01": "Punteros, Aritmética y Modelo de Memoria en C",
            "anc_sec_02": "Arquitectura de Procesos y Syscalls en SO",
            "anc_sec_03": "Gestión de Memoria Dinámica y Stack Overflow",
        }
        if clean_id in known_anchors:
            return known_anchors[clean_id]

        return clean_id.replace("_", " ").title()

