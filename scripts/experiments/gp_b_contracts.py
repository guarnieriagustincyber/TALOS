"""Canonical experiment contracts for Golden Path B (GP-B-V0).

Defines all specifications, rubrics, policies, and roadmap structures
without modifying any production code in src/study_engine/.
"""

from typing import Dict, Tuple

from study_engine.contracts.assessment import compute_canonical_sha256
from study_engine.curriculum.artifact_contracts import (
    ArtifactRequirement,
    ArtifactType,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import (
    AssessmentRubric,
    RubricDimension,
)
from study_engine.curriculum.task_contracts import (
    PracticalTaskSpecification,
    TaskDifficulty,
)
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.policy_contracts import (
    AssessmentPolicy,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id

# Canonical Constants
CAMPAIGN_ID = "GP-B-V0"
STUDENT_ID = "student-gp-b"

NODE_ROOT = "PROG-01"
NODE_DOWNSTREAM = "PROG-02"

TASK_ID = "task-prog01-file-hasher"
RUBRIC_ID = "rubric-prog01-deterministic"
CRITERIA_ID = "crit-prog-01-mastery"

ATTEMPT_B1 = "attempt-prog01-b1"
ATTEMPT_B2 = "attempt-prog01-b2"

CANONICAL_STDIN = "STUDY_ENGINE_CANONICAL_INPUT"

EXPECTED_CLEAN_ARTIFACT_FILENAME = "output_hash.txt"
EXPECTED_CLEAN_ARTIFACT_MIN_SIZE = 64
EXPECTED_CLEAN_ARTIFACT_MAX_SIZE = 65

BAD_ARTIFACT_CONTENT = "ERROR: INVALID_INPUT"


def build_task_specification() -> PracticalTaskSpecification:
    """Build the canonical task specification for PROG-01."""
    artifact_req = ArtifactRequirement(
        requirement_id=EXPECTED_CLEAN_ARTIFACT_FILENAME,
        artifact_type=ArtifactType.CONFIGURATION_FILE,
        min_size_bytes=EXPECTED_CLEAN_ARTIFACT_MIN_SIZE,
        max_size_bytes=EXPECTED_CLEAN_ARTIFACT_MAX_SIZE,
        expected_mime_types=("text/plain",),
        description="Canonical SHA-256 hexadecimal digest of stdin payload",
    )

    return PracticalTaskSpecification(
        task_id=TASK_ID,
        curriculum_node_id=NODE_ROOT,
        title="Deterministic Canonical File Hasher",
        difficulty=TaskDifficulty.FUNDAMENTAL,
        description=(
            "Lea la entrada canonica provista por stdin, calcule su digest "
            "SHA-256 en formato hexadecimal minuscula y escriba exactamente "
            "los 64 caracteres en el archivo output_hash.txt."
        ),
        required_artifacts=(artifact_req,),
        time_limit_minutes=1,
    )


def build_rubric() -> AssessmentRubric:
    """Build the canonical multi-dimensional assessment rubric for PROG-01."""
    live_demo_dim = RubricDimension(
        dimension_id="live_demo",
        title="Live Process Execution and Conformance",
        weight=0.5,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )

    foundations_dim = RubricDimension(
        dimension_id="foundations",
        title="Artifact Conformance and Integrity",
        weight=0.5,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )

    return AssessmentRubric(
        rubric_id=RUBRIC_ID,
        title="Deterministic Evaluation Rubric for Hasher",
        dimensions=(live_demo_dim, foundations_dim),
        default_pass_level=PerformanceLevel.N3_COMPETENT,
        allow_compensation=False,
    )


def build_node_criteria() -> NodeAssessmentCriteria:
    """Build the canonical assessment criteria for PROG-01."""
    evidence_req = EvidenceRequirement(
        requirement_id="req-clean-execution-and-artifact",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
        max_age_days=None,
        requires_audit_approved=False,
        required_tool_backend="python.adapter",
    )

    return NodeAssessmentCriteria(
        criteria_id=CRITERIA_ID,
        target_node_id=NODE_ROOT,
        requirements=(evidence_req,),
        regression_threshold_failures=2,
        allow_exempt=False,
    )


def build_assessment_policy() -> AssessmentPolicy:
    """Build the canonical AssessmentPolicy covering PROG-01 and PROG-02."""
    root_criteria = build_node_criteria()

    downstream_req = EvidenceRequirement(
        requirement_id="req-downstream-execution",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
        max_age_days=None,
        requires_audit_approved=False,
        required_tool_backend="python.adapter",
    )
    downstream_criteria = NodeAssessmentCriteria(
        criteria_id="crit-prog-02-mastery",
        target_node_id=NODE_DOWNSTREAM,
        requirements=(downstream_req,),
        regression_threshold_failures=2,
        allow_exempt=False,
    )

    default_crit = NodeAssessmentCriteria(
        criteria_id="crit-default-competency",
        target_node_type=NodeType.COMPETENCY,
        requirements=(downstream_req,),
        regression_threshold_failures=2,
        allow_exempt=False,
    )

    default_criteria = {NodeType.COMPETENCY: default_crit}
    node_overrides = {
        NODE_ROOT: root_criteria,
        NODE_DOWNSTREAM: downstream_criteria,
    }

    policy_id = "policy-gp-b-v0"
    title = "Golden Path B Assessment Policy"
    version = "1.0.0"

    canonical_hash = compute_canonical_policy_id(
        policy_id=policy_id,
        title=title,
        version=version,
        default_criteria=default_criteria,
        node_overrides=node_overrides,
    )

    return AssessmentPolicy(
        policy_id=policy_id,
        title=title,
        version=version,
        default_criteria=default_criteria,
        node_overrides=node_overrides,
        canonical_policy_id=canonical_hash,
    )


def build_roadmap() -> CurricularRoadmap:
    """Build the canonical CurricularRoadmap with PROG-01 -> PROG-02."""
    node_1 = RoadmapNode(
        node_id=NODE_ROOT,
        title="Canonical Hasher",
        description="Root hashing node (S6 -> S9 -> S5.2 validation)",
        node_type=NodeType.COMPETENCY,
        notebook_id="nb-prog-01",
        priority=1,
    )

    node_2 = RoadmapNode(
        node_id=NODE_DOWNSTREAM,
        title="Downstream Consumer",
        description="Dependent node requiring PROG-01 proficiency",
        node_type=NodeType.COMPETENCY,
        notebook_id="nb-prog-02",
        priority=2,
    )

    dependency = RoadmapDependency(
        source_node_id=NODE_ROOT,
        target_node_id=NODE_DOWNSTREAM,
        dependency_type=DependencyType.HARD,
        rationale="PROG-01 is a strict hard prerequisite for PROG-02",
    )

    nodes = {NODE_ROOT: node_1, NODE_DOWNSTREAM: node_2}
    dependencies = (dependency,)

    roadmap_id = "roadmap-gp-b-v0"
    title = "Golden Path B Validation Roadmap"
    version = "1.0.0"

    canonical_rev = compute_canonical_revision_id(
        roadmap_id=roadmap_id,
        title=title,
        version=version,
        nodes=nodes,
        dependencies=dependencies,
    )

    return CurricularRoadmap(
        roadmap_id=roadmap_id,
        title=title,
        version=version,
        nodes=nodes,
        dependencies=dependencies,
        canonical_revision_id=canonical_rev,
    )
