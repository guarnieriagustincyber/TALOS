"""Deterministic policy validator for IntentContract envelopes.

Enforces zero-trust boundaries between the untrusted SemanticRouter (LLM) and
the authoritative routing decision.

Authority model (INVARIANT, tested by FASE 2 adversarial suite):

    Qwen / SemanticRouter  ->  IntentContract (a *proposal* only)
                                    |
                                    v
                       DeterministicPolicyValidator
                                    |
                                    v
                           AuthoritativeRoute  (the ONLY thing that routes)

The LLM controls nothing but the `intent` field (a value from a closed
taxonomy). Every other field it emits — `action`, `needs_evidence`,
`needs_curriculum`, `needs_execution`, `needs_clarification`, `confidence`,
`entities`, `references` — is IGNORED for routing purposes. The validator
recomputes the authoritative action and needs flags deterministically from
the validated intent plus authoritative inputs (roadmap, current node).

Guarantees:
- needs_* never has routing authority.
- confidence never confers permissions.
- the LLM cannot select/change notebook_id, curriculum_id, current_node,
  current_objective, or state.
- unauthorized/unknown actions are rejected (no best-effort routing).
- contradictory payloads collapse to the validated intent (no guesswork).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, FrozenSet, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.tutor.semantic_router import IntentContract, IntentType


class RouteKind(str, Enum):
    """Authoritative, closed routing categories produced by the validator."""

    GREETING = "greeting"
    NAVIGATION = "navigation"
    TECHNICAL = "technical"
    META = "meta"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"
    REJECTED = "rejected"


class AuthoritativeRoute(BaseModel):
    """Immutable routing decision computed deterministically from validated intent.

    This is the single source of truth consumed by the StudyLoopController.
    It contains NO field copied verbatim from the LLM other than the validated
    intent; action + needs-* flags are policy-derived.

    Deep Immutability & Authority Invariants:
    - frozen=True: attributes cannot be modified.
    - execution_allowed is derived strictly from policy tables, NEVER from LLM request.
    - mutation_allowed indicates solely whether state mutations are authorized
      in this conversational turn (strictly False for all consultative turns).
      It does NOT constitute direct authorization for any specific mutation.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    route_kind: RouteKind = Field(..., description="Authoritative routing category.")
    intent: IntentType = Field(..., description="Validated intent (closed taxonomy).")
    action: str = Field(..., description="Canonical action (policy-derived, NOT LLM).")
    needs_evidence: bool = Field(..., description="Whether epistemic retrieval is required.")
    needs_curriculum: bool = Field(..., description="Whether roadmap context is required.")
    needs_execution: bool = Field(..., description="Whether sandbox execution is needed (policy-derived).")
    execution_allowed: bool = Field(
        default=False,
        description="Whether code execution in sandbox is authorized (derived strictly by policy).",
    )
    needs_clarification: bool = Field(..., description="Whether a clarifying turn is required.")
    mutation_allowed: bool = Field(
        default=False,
        description="Whether state mutation is permitted in this turn (strictly False for consultative turns).",
    )
    rejected_reason: Optional[str] = Field(
        default=None, description="Reason if the proposal was rejected."
    )

    @field_validator("route_kind", mode="before")
    @classmethod
    def convert_str_route_kind(cls, v: Any) -> Any:
        if isinstance(v, str) and v in RouteKind._value2member_map_:
            return RouteKind(v)
        return v

    @field_validator("intent", mode="before")
    @classmethod
    def convert_str_intent(cls, v: Any) -> Any:
        if isinstance(v, str) and v in IntentType._value2member_map_:
            return IntentType(v)
        return v


class ActionType(str, Enum):
    """Closed taxonomy of valid actions per intent."""

    GREET_STUDENT = "greet_student"
    GREET = "greet"
    START_CURRENT_CURRICULUM = "start_current_curriculum"
    EXPLAIN_CONCEPT = "explain_concept"
    EXPLAIN_SYSTEM = "explain_system"
    CLARIFY_QUERY = "clarify_query"


# Whitelist: the ONLY actions the policy will ever authorize, per intent.
# Any action string emitted by the LLM that is not present here is rejected.
_ALLOWED_ACTIONS: Dict[IntentType, FrozenSet[str]] = {
    IntentType.GREETING: frozenset({ActionType.GREET_STUDENT.value, ActionType.GREET.value}),
    IntentType.STUDY_NAVIGATION: frozenset({ActionType.START_CURRENT_CURRICULUM.value}),
    IntentType.TECHNICAL_QUESTION: frozenset({ActionType.EXPLAIN_CONCEPT.value}),
    IntentType.META_QUESTION: frozenset({ActionType.EXPLAIN_SYSTEM.value}),
    IntentType.CLARIFICATION_REQUEST: frozenset({ActionType.CLARIFY_QUERY.value}),
}

_CANONICAL_ACTIONS: Dict[IntentType, str] = {
    IntentType.GREETING: ActionType.GREET_STUDENT.value,
    IntentType.STUDY_NAVIGATION: ActionType.START_CURRENT_CURRICULUM.value,
    IntentType.TECHNICAL_QUESTION: ActionType.EXPLAIN_CONCEPT.value,
    IntentType.META_QUESTION: ActionType.EXPLAIN_SYSTEM.value,
    IntentType.CLARIFICATION_REQUEST: ActionType.CLARIFY_QUERY.value,
}

# Action strings the LLM is forbidden from ever requesting, regardless of intent.
_FORBIDDEN_ACTIONS: FrozenSet[str] = frozenset({
    "show_next_topic",
    "execute_code",
    "advance_curriculum",
    "mark_mastered",
    "write_ledger",
    "change_notebook",
    "change_objective",
    "change_node",
    "modify_state",
})

# Deterministic needs-flags per validated intent. These override anything the
# LLM emitted; they are the ground truth for routing.
# Invariant: mutation_allowed and execution_allowed are strictly False for all
# conversational and consultative turns.
_AUTHORITATIVE_NEEDS: Dict[IntentType, Dict[str, bool]] = {
    IntentType.GREETING: {
        "needs_evidence": False,
        "needs_curriculum": False,
        "needs_execution": False,
        "execution_allowed": False,
        "needs_clarification": False,
        "mutation_allowed": False,
    },
    IntentType.STUDY_NAVIGATION: {
        "needs_evidence": False,
        "needs_curriculum": True,
        "needs_execution": False,
        "execution_allowed": False,
        "needs_clarification": False,
        "mutation_allowed": False,
    },
    IntentType.TECHNICAL_QUESTION: {
        "needs_evidence": True,
        "needs_curriculum": False,
        "needs_execution": False,
        "execution_allowed": False,
        "needs_clarification": False,
        "mutation_allowed": False,
    },
    IntentType.META_QUESTION: {
        "needs_evidence": False,
        "needs_curriculum": False,
        "needs_execution": False,
        "execution_allowed": False,
        "needs_clarification": False,
        "mutation_allowed": False,
    },
    IntentType.CLARIFICATION_REQUEST: {
        "needs_evidence": False,
        "needs_curriculum": False,
        "needs_execution": False,
        "execution_allowed": False,
        "needs_clarification": True,
        "mutation_allowed": False,
    },
}

_ROUTE_KIND_BY_INTENT: Dict[IntentType, RouteKind] = {
    IntentType.GREETING: RouteKind.GREETING,
    IntentType.STUDY_NAVIGATION: RouteKind.NAVIGATION,
    IntentType.TECHNICAL_QUESTION: RouteKind.TECHNICAL,
    IntentType.META_QUESTION: RouteKind.META,
    IntentType.CLARIFICATION_REQUEST: RouteKind.CLARIFICATION,
}


# Legacy reason codes for validate() — preserved verbatim for backward compat.
_REASON_CODES: Dict[IntentType, str] = {
    IntentType.GREETING: "greeting_allowed",
    IntentType.STUDY_NAVIGATION: "navigation_allowed",
    IntentType.TECHNICAL_QUESTION: "technical_question_allowed",
    IntentType.META_QUESTION: "meta_question_allowed",
    IntentType.CLARIFICATION_REQUEST: "clarification_allowed",
}


class DeterministicPolicyValidator:
    """Validates IntentContract proposals against deterministic policy invariants."""

    def __init__(
        self,
        roadmap: Optional[CurricularRoadmap],
        current_node: Optional[str],
    ) -> None:
        self.roadmap = roadmap
        self.current_node = current_node

    def validate(self, intent: IntentContract) -> Tuple[bool, str]:
        """Validate the proposal; returns (is_valid, reason_code).

        Preserves the legacy reason-code contract:
        - greeting_allowed / navigation_allowed / technical_question_allowed /
          meta_question_allowed / clarification_allowed
        - no_active_node / node_not_in_roadmap
        - unknown_intent / forbidden_action:*

        The authoritative routing decision is available via :meth:`resolve`.
        """
        route = self.resolve(intent)
        if route.route_kind == RouteKind.REJECTED:
            return False, route.rejected_reason or "rejected"
        if route.intent in _REASON_CODES:
            return True, _REASON_CODES[route.intent]
        return True, "allowed"

    def resolve(self, intent: IntentContract) -> AuthoritativeRoute:
        """Produce the authoritative route for a proposal (may be REJECTED).

        The route is derived ONLY from the validated ``intent`` plus
        authoritative inputs. ``action``, ``needs_*`` and ``confidence`` from
        the LLM proposal are discarded.
        """
        itype = intent.intent

        # 1. Unknown/future intents are rejected outright (no best-effort).
        if itype not in _ROUTE_KIND_BY_INTENT:
            return self._rejected(itype, "unknown_intent")

        # 2. Forbidden actions are rejected regardless of intent.
        if intent.action in _FORBIDDEN_ACTIONS:
            return self._rejected(itype, f"forbidden_action:{intent.action}")

        # 2b. Unknown / unauthorized actions are rejected fail-closed (VULN-02).
        allowed_for_intent = _ALLOWED_ACTIONS.get(itype, frozenset())
        if (
            not isinstance(intent.action, str)
            or not intent.action
            or intent.action.strip() != intent.action
            or intent.action not in allowed_for_intent
        ):
            return self._rejected(itype, f"unauthorized_action:{intent.action}")

        # 3. State-dependent gating (deterministic, not LLM-influenced).
        if itype == IntentType.STUDY_NAVIGATION:
            if not self.current_node:
                return self._rejected(itype, "no_active_node")
            if (
                self.roadmap
                and hasattr(self.roadmap, "nodes")
                and self.roadmap.nodes
                and self.current_node not in self.roadmap.nodes
            ):
                return self._rejected(itype, "node_not_in_roadmap")

        # 4. Derive canonical action + needs from the policy tables.
        needs = _AUTHORITATIVE_NEEDS[itype]
        canonical_action = _CANONICAL_ACTIONS[itype]
        return AuthoritativeRoute(
            route_kind=_ROUTE_KIND_BY_INTENT[itype],
            intent=itype,
            action=canonical_action,
            needs_evidence=needs["needs_evidence"],
            needs_curriculum=needs["needs_curriculum"],
            needs_execution=needs["needs_execution"],
            execution_allowed=needs["execution_allowed"],
            needs_clarification=needs["needs_clarification"],
            mutation_allowed=needs["mutation_allowed"],
        )

    def resolve_from_intent_type(self, itype: IntentType) -> AuthoritativeRoute:
        """Convenience method to resolve a route directly from a trusted IntentType enum.

        Used by deterministic / fallback routing paths (e.g., keyword or heuristic
        classification) to produce a canonical AuthoritativeRoute without
        synthesizing an intermediate unvalidated LLM payload.
        """
        canonical_action = _CANONICAL_ACTIONS[itype]
        dummy_contract = IntentContract(
            intent=itype,
            action=canonical_action,
            needs_evidence=False,
            needs_curriculum=False,
            needs_execution=False,
            needs_clarification=False,
            confidence=1.0,
        )
        return self.resolve(dummy_contract)

    @staticmethod
    def _rejected(itype: IntentType, reason: str) -> AuthoritativeRoute:
        return AuthoritativeRoute(
            route_kind=RouteKind.REJECTED,
            intent=itype,
            action="reject",
            needs_evidence=False,
            needs_curriculum=False,
            needs_execution=False,
            execution_allowed=False,
            needs_clarification=False,
            mutation_allowed=False,
            rejected_reason=reason,
        )