"""Subsystem E3: Student Cognitive Layer (Capa Cognitiva Determinista del Estudiante).

Implements Bayesian Knowledge Tracing (Corbett & Anderson 1995), Prerequisite Readiness Probing,
Prerequisite Lag Detection, Pedagogical Depth Modulation, Spaced Repetition (SM-2), and
Deterministic Grading Bridges.
"""

from study_engine.student.bkt_tracker import DEFAULT_BKT_PARAMS, BKTTracker
from study_engine.student.contracts import (
    AnchorState,
    BKTState,
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
    PrerequisiteAssessment,
    ReadinessDecision,
    ReadinessReport,
    RemediationInterrupt,
    RemediationOption,
)
from study_engine.student.depth_modulator import DepthModulator
from study_engine.student.laguna_detector import LagunaDetector
from study_engine.student.observation_bridge import ObservationBridge
from study_engine.student.readiness_probe import ReadinessProbe
from study_engine.student.spaced_repetition import (
    SpacedRepetitionScheduler,
    derive_sm2_quality,
)
from study_engine.student.storage import StudentStorage
from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
from study_engine.student.memory_extractor import PedagogicalMemoryExtractor

__all__ = [
    "DEFAULT_BKT_PARAMS",
    "AnchorState",
    "BKTState",
    "BKTTracker",
    "DepthModulator",
    "ExerciseFormat",
    "LagunaDetector",
    "ObservationBridge",
    "ObservationPayload",
    "ObservationSource",
    "PedagogicalMemoryTracker",
    "PedagogicalMemoryExtractor",
    "PrerequisiteAssessment",
    "ReadinessDecision",
    "ReadinessProbe",
    "ReadinessReport",
    "RemediationInterrupt",
    "RemediationOption",
    "SpacedRepetitionScheduler",
    "StudentStorage",
    "derive_sm2_quality",
]
