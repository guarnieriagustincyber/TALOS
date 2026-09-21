"""Generation package for Subsystem S4.2 and S4.3."""

from study_engine.generation.base import BaseGenerator
from study_engine.generation.mock import MockGenerator
from study_engine.generation.parser import GenerationOutputParser
from study_engine.generation.prompts import (
    PromptAssembler,
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.generation.tutor import StructuredTutor

__all__ = [
    "BaseGenerator",
    "GenerationOutputParser",
    "MockGenerator",
    "PromptAssembler",
    "PromptBundle",
    "PromptMessage",
    "PromptRole",
    "StructuredTutor",
    "compute_canonical_prompt_hash",
]
