"""Deterministic Tutor Policy for Subsystem S7.

Governs pedagogical action selection as a pure, deterministic function of
curriculum state, prerequisites, dialogue turn history, and assessment outcomes.
Enforces Pedagogical Invariants TUT-01 through TUT-06.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from study_engine.contracts.tutor import (
    PedagogicalAction,
    PedagogicalFollowUp,
    ResponseBudgetPolicy,
    TutorContext,
    TutorPolicyDecision,
)


class TutorPolicyConfig(BaseModel):
    """Configuration envelope for DeterministicTutorPolicy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_conceptual_turns: int = Field(
        default=5,
        ge=1,
        description="Maximum conceptual turns permitted before forcing practice dispatch to prevent infinite probe loops.",
    )
    understanding_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum NLI support score required to confirm understanding.",
    )
    default_conceptual_budget: ResponseBudgetPolicy = Field(
        default=ResponseBudgetPolicy.NORMAL,
        description="Default response budget for conceptual explanations.",
    )
    default_probe_budget: ResponseBudgetPolicy = Field(
        default=ResponseBudgetPolicy.SHORT,
        description="Default response budget for comprehension probing.",
    )
    node_to_task_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "SEC-05-BIN-SEC": "task_sec05_file_hasher.json",
        },
        description="Declarative mapping of curriculum node IDs to practical task specification IDs.",
    )


class DeterministicTutorPolicy:
    """Pure, deterministic policy selecting PedagogicalAction without autonomous LLM agency."""

    def __init__(self, config: Optional[TutorPolicyConfig] = None) -> None:
        self.config = config or TutorPolicyConfig()

    def decide(self, context: TutorContext) -> TutorPolicyDecision:
        """Select next structural pedagogical action based on state, intent, and dialogue history.

        Pure mathematical function: same inputs strictly produce identical decision.
        """
        msg = (context.last_student_message or "").strip().lower()
        followup = self._generate_followup(context)

        # 1. HARD GATE: Prerequisites unfulfilled or node locked (TUT-04)
        if context.unfulfilled_prerequisites or context.node_status == "LOCKED":
            return TutorPolicyDecision(
                action=PedagogicalAction.ABSTAIN,
                budget=ResponseBudgetPolicy.SHORT,
                target_node_id=context.active_node_id,
                rationale="PREREQUISITES_UNFULFILLED_OR_LOCKED",
                pedagogical_intent="FAIL_CLOSED_LOCK",
                allow_code_snippets=False,
                followup=followup,
            )

        # 2. POST-FEEDBACK CLARIFICATION OR PRESENTATION (Aclaración 3 + TUT-04)
        if (
            context.practice_attempts_count > 0
            and context.last_assessment_verdict is not None
        ):
            if self._is_explanation_request(msg):
                return TutorPolicyDecision(
                    action=PedagogicalAction.EXPLAIN,
                    budget=ResponseBudgetPolicy.SHORT,
                    target_node_id=context.active_node_id,
                    rationale="POST_FEEDBACK_CLARIFICATION",
                    pedagogical_intent="CLARIFY_FAILED_DIMENSION_WITHOUT_SOLUTION",
                    allow_code_snippets=False,
                    followup=followup,
                )
            if context.last_assessment_verdict == "PASS":
                return TutorPolicyDecision(
                    action=PedagogicalAction.GIVE_FEEDBACK,
                    budget=ResponseBudgetPolicy.NORMAL,
                    target_node_id=context.active_node_id,
                    rationale="PRACTICE_ASSESSMENT_PASSED",
                    pedagogical_intent="CELEBRATE_MASTERY_AND_UNLOCK_DOWNSTREAM",
                    allow_code_snippets=False,
                    followup=followup,
                )
            else:
                return TutorPolicyDecision(
                    action=PedagogicalAction.GIVE_FEEDBACK,
                    budget=ResponseBudgetPolicy.NORMAL,
                    target_node_id=context.active_node_id,
                    rationale="PRACTICE_ASSESSMENT_FAILED",
                    pedagogical_intent="DIAGNOSE_FAILURE_AND_SUGGEST_REMEDIATION",
                    allow_code_snippets=False,
                    followup=followup,
                )

        resolved_task_id = self.config.node_to_task_mapping.get(
            context.active_node_id,
            f"task_{context.active_node_id.lower().replace('-', '_')}.json",
        )

        # 3. ESCAPE RULE: Max conceptual turns reached -> Force practice dispatch (Aclaración 1)
        if context.conceptual_turns_completed >= self.config.max_conceptual_turns:
            return TutorPolicyDecision(
                action=PedagogicalAction.REQUEST_PRACTICE,
                budget=ResponseBudgetPolicy.DETAILED,
                target_node_id=context.active_node_id,
                rationale="MAX_CONCEPTUAL_TURNS_REACHED",
                pedagogical_intent="FORCE_PRACTICE_ESCAPE",
                suggested_task_id=resolved_task_id,
                allow_code_snippets=False,
                followup=followup,
            )

        # 4. EXPLICIT PRACTICE INTENT (Student requests practice after at least 1 conceptual turn)
        if context.conceptual_turns_completed >= 1 and self._is_practice_intent(msg):
            return TutorPolicyDecision(
                action=PedagogicalAction.REQUEST_PRACTICE,
                budget=ResponseBudgetPolicy.DETAILED,
                target_node_id=context.active_node_id,
                rationale="STUDENT_REQUESTED_PRACTICE",
                pedagogical_intent="DISPATCH_PRACTICAL_CHALLENGE",
                suggested_task_id=resolved_task_id,
                allow_code_snippets=False,
                followup=followup,
            )

        # Determine conceptual budget (escalate to DETAILED if student requests elaboration)
        effective_conceptual_budget = (
            ResponseBudgetPolicy.DETAILED
            if self._is_detailed_request(msg)
            else self.config.default_conceptual_budget
        )

        # 5. INITIAL CONCEPTUAL EXPLANATION (Turn 0 on active node)
        if context.conceptual_turns_completed == 0:
            return TutorPolicyDecision(
                action=PedagogicalAction.EXPLAIN,
                budget=effective_conceptual_budget,
                target_node_id=context.active_node_id,
                rationale="INITIAL_CONCEPTUAL_EXPLANATION",
                pedagogical_intent="CONCEPTUAL_GROUNDING",
                allow_code_snippets=True,
                followup=followup,
            )

        # 6. COMPREHENSION PROBE (Following conceptual explanation)
        return TutorPolicyDecision(
            action=PedagogicalAction.CHECK_UNDERSTANDING,
            budget=self.config.default_probe_budget,
            target_node_id=context.active_node_id,
            rationale="PROBE_COMPREHENSION",
            pedagogical_intent="PROBE_COMPREHENSION_CONFIRMATION",
            allow_code_snippets=False,
            followup=followup,
        )

    def _generate_followup(self, ctx: TutorContext) -> Optional[PedagogicalFollowUp]:
        """Build deterministic follow-up controls from a curricular context.

        The policy deliberately uses only curriculum-derived values already
        present in ``TutorContext``.  It does not inspect generated language,
        evidence, or model output, so it cannot introduce un-audited factual
        claims into the S4.4 boundary.
        """
        if ctx.node_status == "LOCKED" or ctx.unfulfilled_prerequisites:
            return None

        node_label = ctx.active_node_title or ctx.active_node_id
        # ``StudyLoopController`` supplies curricular-order adjacency.  Keep
        # that order while removing malformed duplicate edges deterministically.
        seen_node_ids = set()
        ordered_adjacent_node_ids: List[str] = []
        for node_id in ctx.adjacent_node_ids:
            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)
                ordered_adjacent_node_ids.append(node_id)
        adjacent_node_ids = tuple(ordered_adjacent_node_ids)
        next_node_id = (
            ctx.next_node_id
            if ctx.next_node_id in adjacent_node_ids
            else (adjacent_node_ids[0] if adjacent_node_ids else None)
        )

        return PedagogicalFollowUp(
            verification_question=(
                f"¿Cómo explicarías con tus palabras el concepto central de {node_label}?"
            ),
            deepen_options=adjacent_node_ids,
            code_example_available=ctx.code_example_available,
            next_node_id=next_node_id,
            suggested_budget=self.config.default_conceptual_budget,
        )

    def evaluate_understanding(self, nli_support_score: float) -> bool:
        """Determine if comprehension is confirmed based on calibrated NLI score (Aclaración 2)."""
        return nli_support_score >= self.config.understanding_threshold

    @staticmethod
    def _is_practice_intent(message: str) -> bool:
        """Detect explicit student readiness or intent to attempt practical programming challenge."""
        if not message:
            return False
        patterns = [
            r"\bpractica\b",
            r"\bpráctica\b",
            r"\bejercicio\b",
            r"\bprogramar\b",
            r"\bcódigo\b",
            r"\bhasher\b",
            r"\blisto para practicar\b",
            r"\bdesafío\b",
            r"\btask\b",
            r"\bprobar\b",
        ]
        return any(re.search(p, message) for p in patterns)

    @staticmethod
    def _is_explanation_request(message: str) -> bool:
        """Detect student query seeking conceptual clarification post-feedback."""
        if not message:
            return False
        patterns = [
            r"por qu[eé]",
            r"porque",
            r"explica",
            r"explicar",
            r"duda",
            r"qu[eé] significa",
            r"fall[eé]",
            r"falla",
            r"tamaño",
            r"dimension",
            r"dimensión",
            r"error",
        ]
        return any(re.search(p, message) for p in patterns)

    @staticmethod
    def _is_detailed_request(message: str) -> bool:
        """Detect student request for detailed elaboration, deep walkthrough, or thorough explanation."""
        if not message:
            return False
        patterns = [
            r"m[aá]s detalladamente",
            r"explicame m[aá]s",
            r"expl[ií]came m[aá]s",
            r"\bprofundiz\w*",
            r"\ben detalle\b",
            r"\brecorrido completo\b",
            r"\bdetallad[oa]\b",
        ]
        return any(re.search(p, message) for p in patterns)
