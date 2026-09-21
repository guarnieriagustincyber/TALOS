"""Semantic Router for intent interpretation powered by local Qwen 3.5 2B.

Maps unstructured student queries into structured IntentContract envelopes
without bypassing forensic boundaries or audit verifications.
"""

from enum import Enum
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

from study_engine.contracts.generation import (
    GenerationParameters,
)
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.backends import ProviderBackend
from study_engine.llm.factory import LLMProviderFactory, ProviderConfig


class IntentType(str, Enum):
    """Authoritative taxonomy of student interaction intents."""

    GREETING = "greeting"
    STUDY_NAVIGATION = "study_navigation"
    TECHNICAL_QUESTION = "technical_question"
    META_QUESTION = "meta_question"
    CLARIFICATION_REQUEST = "clarification_request"


class IntentContract(BaseModel):
    """Immutable intent contract parsed and validated from student interaction."""

    model_config = ConfigDict(frozen=True, strict=True)

    intent: IntentType = Field(..., description="High-level category of student intent")
    action: str = Field(..., description="Specific pedagogical or navigation action to execute")
    needs_evidence: bool = Field(..., description="Whether epistemic document retrieval is required")
    needs_curriculum: bool = Field(..., description="Whether roadmap DAG context is required")
    needs_execution: bool = Field(default=False, description="Whether code sandbox execution is needed")
    needs_clarification: bool = Field(default=False, description="Whether clarifying question is needed")
    entities: Tuple[str, ...] = Field(default_factory=tuple, description="Extracted domain entities/concepts")
    references: Tuple[str, ...] = Field(default_factory=tuple, description="References to conversational context")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Interpretation confidence score")

    @field_validator("entities", "references", mode="before")
    @classmethod
    def convert_to_tuple(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple, set)):
            return tuple(v)
        return v

    @field_validator("intent", mode="before")
    @classmethod
    def convert_str_intent(cls, v: Any) -> Any:
        if isinstance(v, str) and v in IntentType._value2member_map_:
            return IntentType(v)
        return v


class SemanticRouter:
    """Semantic router that interprets intent via Qwen 3.5 2B into an IntentContract."""

    # Hard cap on raw provider output to bound memory/DoS exposure (Group M).
    MAX_OUTPUT_CHARS: int = 16_384

    def __init__(
        self,
        local_backend: Optional[ProviderBackend] = None,
        factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.factory = factory or LLMProviderFactory()
        if local_backend is not None:
            self.local_backend = local_backend
        else:
            try:
                self.local_backend = self.factory.create_provider(
                    ProviderConfig(
                        provider_type="ollama",
                        timeout_seconds=5.0,
                        connect_timeout_seconds=2.0,
                        fallback_to_mock_if_missing_key=True,
                    )
                )
            except Exception:
                self.local_backend = self.factory.create_provider(
                    ProviderConfig(provider_type="mock")
                )

    def interpret(self, query: str, context: Optional[Dict[str, Any]] = None) -> IntentContract:
        """Use local LLM to interpret query into a validated IntentContract envelope.

        The query is Unicode-sanitised at the boundary and the whole LLM path
        is wrapped in a try/except, so any failure (malformed Unicode,
        oversized payload, JSON error, provider crash) collapses to a safe
        deterministic fallback instead of escaping the router.
        """
        # Remove surrogate codepoints that would break Pydantic JSON parsing.
        safe_query = re.sub(r'[\ud800-\udfff]', '', query)
        ctx = context or {}
        active_node = ctx.get("active_node", "unknown")
        history = ctx.get("history", [])
        history_len = len(history) if isinstance(history, (list, tuple)) else 0

        system_prompt = (
            "Sos un router semántico para un tutor pedagógico estructurado. "
            "Analizá la intención del estudiante y respondé ÚNICAMENTE con un JSON válido con esta estructura:\n"
            "{\n"
            '  "intent": "greeting" | "study_navigation" | "technical_question" | "meta_question" | "clarification_request",\n'
            '  "action": "descripción de la acción",\n'
            '  "needs_evidence": true/false,\n'
            '  "needs_curriculum": true/false,\n'
            '  "needs_execution": true/false,\n'
            '  "needs_clarification": true/false,\n'
            '  "entities": ["concepto1", ...],\n'
            '  "references": ["referencia", ...],\n'
            '  "confidence": 0.0 a 1.0\n'
            "}\n"
            "No incluyas explicaciones, markdown adicional ni bloques fuera del JSON."
        )

        user_content = (
            f"Contexto:\n"
            f"- Nodo activo: {active_node}\n"
            f"- Turnos previos en historial: {history_len}\n\n"
            f"Consulta del estudiante: {safe_query}\n"
        )

        messages = (
            PromptMessage(
                role=PromptRole.USER,
                content=user_content,
            ),
        )
        params = GenerationParameters(
            temperature=0.0,
            max_output_tokens=250,
            suggested_model="qwen3.5:2b",
        )
        prompt_hash = compute_canonical_prompt_hash(system_prompt, messages, params)
        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=prompt_hash,
        )

        try:
            completion = self.local_backend.complete(bundle)
            raw_text = completion.text.strip()

            # Bound oversized provider output before any parsing attempt.
            if len(raw_text) > self.MAX_OUTPUT_CHARS:
                return self._fallback_intent(query)

            # Clean possible markdown fence
            if raw_text.startswith("```json"):
                raw_text = raw_text[len("```json"):].strip()
            if raw_text.startswith("```"):
                raw_text = raw_text[len("```"):].strip()
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

            intent_data = json.loads(raw_text)

            # Only a JSON object with a valid intent is ever trusted; anything
            # else (array, string, null, extra objects, unknown intent) falls
            # back to the deterministic safe path.
            if not isinstance(intent_data, dict):
                return self._fallback_intent(query)

            raw_intent = intent_data.get("intent")
            if raw_intent not in IntentType._value2member_map_:
                return self._fallback_intent(query)

            return IntentContract(**intent_data)
        except Exception:
            return self._fallback_intent(query)

    def _fallback_intent(self, query: str) -> IntentContract:
        """Deterministic fail-safe fallback preserving strict epistemic verification."""
        clean_q = query.strip().lower()

        # Heuristic greeting check
        if any(g in clean_q for g in ["hola", "buenos dias", "buenas", "saludos", "hey"]):
            return IntentContract(
                intent=IntentType.GREETING,
                action="greet_student",
                needs_evidence=False,
                needs_curriculum=False,
                needs_execution=False,
                needs_clarification=False,
                entities=(),
                references=(),
                confidence=0.8,
            )

        # Heuristic navigation check
        if any(c in clean_q for c in [
            "por donde empezamos",
            "por dónde empezamos",
            "qué tema sigue",
            "que tema sigue",
            "en qué tema quedamos",
            "en que tema quedamos",
            "próximo nodo",
            "proximo nodo",
            "roadmap",
            "siguiente paso",
        ]):
            return IntentContract(
                intent=IntentType.STUDY_NAVIGATION,
                action="start_current_curriculum",
                needs_evidence=False,
                needs_curriculum=True,
                needs_execution=False,
                needs_clarification=False,
                entities=(),
                references=(),
                confidence=0.8,
            )

        # Meta question check
        if any(m in clean_q for m in ["quién te creó", "cómo funcionas", "qué eres", "quién eres", "qué haces"]):
            return IntentContract(
                intent=IntentType.META_QUESTION,
                action="explain_system",
                needs_evidence=False,
                needs_curriculum=False,
                needs_execution=False,
                needs_clarification=False,
                entities=(),
                references=(),
                confidence=0.8,
            )

        # Default safe fallback: Clarification request to prevent turning infrastructure failure into ungrounded retrieval
        return IntentContract(
            intent=IntentType.CLARIFICATION_REQUEST,
            action="clarify_query",
            needs_evidence=False,
            needs_curriculum=False,
            needs_execution=False,
            needs_clarification=True,
            entities=(),
            references=(),
            confidence=0.3,
        )


# =========================================================================
# Category-Specific Regression Fallback Policy (E1.1 Specification)
# =========================================================================

logger = logging.getLogger("study_engine.tutor.semantic_router")
DISABLED_FACET_CATEGORIES: Set[str] = set()


def check_e1_category_policy(category: str, delta_sac: float) -> bool:
    """Enforce deterministic category-specific regression fallback.

    If E1 degrades SAC on a given category by > 0.02 (2pp) relative to E0,
    the router permanently disables facet decomposition for that category,
    turning it into a monolithic query policy, and emits a REGRESSION_GUARD event.

    Returns:
        True if regression guard was triggered (category disabled), False otherwise.
    """
    if delta_sac < -0.02:
        DISABLED_FACET_CATEGORIES.add(category)
        logger.warning(
            "REGRESSION_GUARD triggered for category '%s' (delta_sac=%.4f < -0.02). Facets disabled.",
            category,
            delta_sac,
        )
        return True
    return False


def is_facet_decomposition_allowed(category: Optional[str]) -> bool:
    """Check if facet decomposition is active for the given category."""
    if not category:
        return True
    return category not in DISABLED_FACET_CATEGORIES


def save_category_policy(path: Union[str, Path]) -> None:
    """Persist current category fallback policies to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "policy_version": "1.1",
        "policy_name": "E1_CATEGORY_REGRESSION_GUARD",
        "delta_threshold": -0.02,
        "disabled_categories": sorted(list(DISABLED_FACET_CATEGORIES)),
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_category_policy(path: Union[str, Path]) -> None:
    """Load category fallback policies from a JSON file."""
    p = Path(path)
    if not p.exists():
        return
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    for cat in data.get("disabled_categories", []):
        DISABLED_FACET_CATEGORIES.add(cat)


def reset_category_policy() -> None:
    """Reset disabled categories in memory (useful for test isolation)."""
    DISABLED_FACET_CATEGORIES.clear()




# =========================================================================
# Phase E5.3 Deterministic Boundary Activation Rule (Enmienda E5-A5)
# =========================================================================

def should_activate_facet_decomposition(
    query_text: str,
    category: Optional[str] = None,
    estimated_facets: int = 1,
    min_tokens_threshold: int = 5,
) -> Tuple[bool, str]:
    """Phase E5.3 Deterministic Boundary Activation Rule (E5-A5).

    Codifies the exact causal boundary where E1d is superior to E1c/E0:
    1. Category is multi-facet ('multi_source', 'multi_topic') OR estimated_facets >= 2.
    2. Category is NOT disabled by REGRESSION_GUARD in DISABLED_FACET_CATEGORIES.
    3. Query token length >= min_tokens_threshold (prevents fragmentation on atomic queries).

    When these conditions are not satisfied, the router defaults to monolithic
    retrieval (E1c/E0) preventing semantic degradation.

    Returns:
        (should_activate, reason)
    """
    clean_text = query_text.strip()
    tokens = clean_text.split()

    if category and category in DISABLED_FACET_CATEGORIES:
        return False, f"REGRESSION_GUARD active: category '{category}' is disabled."

    if len(tokens) < min_tokens_threshold and estimated_facets < 2:
        return False, f"Atomic query below token threshold ({len(tokens)} < {min_tokens_threshold}): monolithic retrieval E1c/E0 preferred."

    if category in ("multi_source", "multi_topic") or estimated_facets >= 2:
        return True, f"Multi-facet boundary met (category='{category}', facets={estimated_facets}): activating E1d decomposition."

    return False, f"Default monolithic retrieval for category='{category}'."
