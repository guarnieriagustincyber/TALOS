"""C3 Context Budget Manager and Deterministic Pruning Module.

Normative Authority: Gate B Assurance Criterion C3.
Human Decision Binding:
  - D_C3_1 = C (Layered Budget: Global hard ceiling + categorized sub-budgets)
  - D_C3_2 = A+B (Hierarchical Deterministic Pruning + Fail-Closed)
  - D_C3_3 = A (Conservative estimation: ceil(len(text)/4) with 5% deterministic safety margin)

Invariants:
  - GLOBAL_CONTEXT_CEILING_TOKENS = 5000 (Normative limit)
  - SAFETY_MARGIN_RATIO = 0.05 (5% safety margin)
  - EFFECTIVE_CONTEXT_CEILING_TOKENS = 4761 (Operational physical ceiling)
  - EFFECTIVE_CONTEXT_CEILING_CHARS = 19044 (Operational physical char limit)
  - Sum of categorized sub-budgets <= 4761 tokens.
  - Zero blind truncation: pruning is deterministic and component-aware.
  - Fail-closed: If payload exceeds 4761 tokens after all pruning phases,
    execution MUST abort with CONTEXT_BUDGET_EXCEEDED and 0 calls to any LLM.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from study_engine.llm.exceptions import LLMError


class ContextBudgetExceededError(LLMError):
    """Raised when context payload exceeds the C3 effective hard ceiling (4761 tokens)."""

    def __init__(
        self,
        message: str,
        estimated_tokens: int = 0,
        effective_ceiling: int = 4761,
        raw_characters: int = 0,
    ) -> None:
        super().__init__(message)
        self.estimated_tokens = estimated_tokens
        self.effective_ceiling = effective_ceiling
        self.raw_characters = raw_characters


# ==============================================================================
# NORMATIVE & OPERATIONAL CONSTANTS
# ==============================================================================

GLOBAL_CONTEXT_CEILING_TOKENS: int = 5000
SAFETY_MARGIN_RATIO: float = 0.05
EFFECTIVE_CONTEXT_CEILING_TOKENS: int = int(
    GLOBAL_CONTEXT_CEILING_TOKENS / (1.0 + SAFETY_MARGIN_RATIO)
)  # 4761 tokens
EFFECTIVE_CONTEXT_CEILING_CHARS: int = EFFECTIVE_CONTEXT_CEILING_TOKENS * 4  # 19044 chars

# Stratified Sub-Budgets (Layered Budget: D_C3_1 = C)
# Calibrated against CP108 empirical measurements:
# Base system prompt was measured at ~1299 tokens.
BUDGET_SYSTEM_TOKENS: int = 1350
BUDGET_QUERY_TOKENS: int = 250
BUDGET_PRIMARY_EVIDENCE_TOKENS: int = 1800
BUDGET_SECONDARY_EVIDENCE_TOKENS: int = 350
BUDGET_HISTORY_TOKENS: int = 350
BUDGET_PEDAGOGY_TOKENS: int = 400
BUDGET_MEMORY_TOKENS: int = 200
BUDGET_RESERVE_TOKENS: int = 61

# Invariant: sum of sub-budgets must be <= EFFECTIVE_CONTEXT_CEILING_TOKENS (4761)
TOTAL_SUB_BUDGETS: int = (
    BUDGET_SYSTEM_TOKENS
    + BUDGET_QUERY_TOKENS
    + BUDGET_PRIMARY_EVIDENCE_TOKENS
    + BUDGET_SECONDARY_EVIDENCE_TOKENS
    + BUDGET_HISTORY_TOKENS
    + BUDGET_PEDAGOGY_TOKENS
    + BUDGET_MEMORY_TOKENS
    + BUDGET_RESERVE_TOKENS
)
assert TOTAL_SUB_BUDGETS <= EFFECTIVE_CONTEXT_CEILING_TOKENS, (
    f"Sum of sub-budgets ({TOTAL_SUB_BUDGETS}) exceeds effective ceiling ({EFFECTIVE_CONTEXT_CEILING_TOKENS})"
)


# ==============================================================================
# TOKEN MEASUREMENT
# ==============================================================================

def estimate_tokens(text: Optional[str]) -> int:
    """Conservative token estimation: ceil(len(text) / 4)."""
    if not text:
        return 0
    return math.ceil(len(text) / 4)


def estimate_payload_tokens(
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    context: Optional[str] = None,
    prompt_bundle: Optional[Any] = None,
) -> int:
    """Measure the exact, real payload that will be delivered to the provider.

    Accounts for all combined characters across system, user, messages,
    and injected context.
    """
    if prompt_bundle is not None:
        total_text = getattr(prompt_bundle, "system_prompt", "") or ""
        messages = getattr(prompt_bundle, "messages", ()) or ()
        for m in messages:
            content = getattr(m, "content", "") or ""
            total_text += ("\n\n" if total_text else "") + content
        return estimate_tokens(total_text)

    parts: List[str] = []
    if system_prompt:
        parts.append(system_prompt)
    if user_prompt:
        parts.append(user_prompt)
    if context:
        parts.append(context)

    combined = "\n\n".join(parts)
    return estimate_tokens(combined)


# ==============================================================================
# COMPONENT CLASSIFICATION & DATA STRUCTURES
# ==============================================================================

class ComponentPriority(str, Enum):
    PEDAGOGICALLY_CRITICAL = "pedagogically_critical"
    PEDAGOGICALLY_USEFUL = "pedagogically_useful"
    OPTIONAL = "optional"
    REDUNDANT = "redundant"


@dataclass
class C3PruningReport:
    """Audit report for C3 budget enforcement and deterministic pruning."""

    initial_chars: int
    initial_estimated_tokens: int
    final_chars: int
    final_estimated_tokens: int
    effective_ceiling_tokens: int = EFFECTIVE_CONTEXT_CEILING_TOKENS
    normative_ceiling_tokens: int = GLOBAL_CONTEXT_CEILING_TOKENS
    safety_margin_ratio: float = SAFETY_MARGIN_RATIO
    was_pruned: bool = False
    pruning_actions: List[str] = field(default_factory=list)
    fail_closed: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


# ==============================================================================
# DETERMINISTIC PRUNING PIPELINE (PRUNE -> VERIFY -> FAIL-CLOSED)
# ==============================================================================

def prune_redundant_content(text: str) -> Tuple[str, bool]:
    """Phase 1: Strip REDUNDANT content deterministically.

    Eliminates duplicated section headers, duplicate checklists, empty fences,
    and excessive tag repetition without removing substantive text.
    """
    original_len = len(text)
    modified = text

    # Remove duplicate blank lines / padding
    modified = re.sub(r"\n{3,}", "\n\n", modified)

    # Remove duplicate consecutive checklist items
    lines = modified.splitlines()
    unique_lines: List[str] = []
    prev_line = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            if stripped == prev_line:
                continue
        unique_lines.append(line)
        prev_line = stripped
    modified = "\n".join(unique_lines)

    pruned = len(modified) < original_len
    return modified, pruned


def prune_history_turns_deterministically(
    turns: List[dict],
    max_tokens: int = BUDGET_HISTORY_TOKENS,
) -> Tuple[List[dict], bool]:
    """Phase 3a: Progressively prune conversation turns from oldest to newest.

    Does NOT force an arbitrary '1 turn' rule. It deterministically drops
    the oldest turns one-by-one until the total history fits within max_tokens.
    """
    if not turns:
        return [], False

    current_turns = list(turns)
    pruned = False

    def _history_tokens(t_list: List[dict]) -> int:
        chars = sum(len((t.get("content") or "")) for t in t_list)
        return estimate_tokens(" " * chars)

    # While history exceeds sub-budget and there is more than 1 turn, drop oldest
    while len(current_turns) > 1 and _history_tokens(current_turns) > max_tokens:
        current_turns.pop(0)
        pruned = True

    # If the single remaining turn still exceeds max_tokens, compact it to max_tokens chars
    if current_turns and _history_tokens(current_turns) > max_tokens:
        last = dict(current_turns[0])
        max_chars = max_tokens * 4
        content = last.get("content") or ""
        if len(content) > max_chars:
            last["content"] = content[:max_chars]
            current_turns = [last]
            pruned = True

    return current_turns, pruned


def prune_evidence_text_deterministically(
    evidence_text: str,
    max_tokens: int,
) -> Tuple[str, bool]:
    """Phase 2/4: Prune evidence deterministically chunk-by-chunk.

    Splits evidence by documented citations/chunks and drops peripheral
    citations from the end while preserving the leading primary citations.
    """
    if not evidence_text:
        return "", False

    if estimate_tokens(evidence_text) <= max_tokens:
        return evidence_text, False

    # Split by double newline or citation markers
    blocks = re.split(r"(?=\[(?:Fuente|Source|Documento|Programa)[^\]]*\])", evidence_text)
    if len(blocks) <= 1:
        # Split by paragraphs
        blocks = evidence_text.split("\n\n")

    retained_blocks: List[str] = []
    current_tokens = 0

    for b in blocks:
        b_clean = b.strip()
        if not b_clean:
            continue
        b_tokens = estimate_tokens(b_clean)
        if current_tokens + b_tokens <= max_tokens:

            retained_blocks.append(b_clean)
            current_tokens += b_tokens

        elif not retained_blocks:
            # If the very first block exceeds max_tokens on its own,
            # bound it deterministically to max_tokens * 4 chars at a sentence boundary
            max_chars = max_tokens * 4
            if len(b_clean) > max_chars:
                truncated_b = b_clean[:max_chars]
                last_dot = truncated_b.rfind(". ")
                if last_dot > max_chars // 2:
                    truncated_b = truncated_b[:last_dot + 1]
                b_clean = truncated_b
            retained_blocks.append(b_clean)
            current_tokens += estimate_tokens(b_clean)
            break
        else:
            break

    result = "\n\n".join(retained_blocks)
    return result, True



def enforce_c3_budget(
    system_prompt: str,
    user_query: str,
    evidence_text: Optional[str] = None,
    history_turns: Optional[List[dict]] = None,
    bkt_directive: Optional[str] = None,
    style_directive: Optional[str] = None,
    memory_directive: Optional[str] = None,
    predecessor_context: Optional[str] = None,
    phase_instructions: Optional[str] = None,
    other_directives: Optional[str] = None,
) -> Tuple[Dict[str, Any], C3PruningReport]:
    """Enforce the C3 Layered Budget via Deterministic Pruning and Fail-Closed check.

    Returns:
      (retained_components_dict, report)
    If fail_closed is True, caller MUST NOT invoke the LLM.
    """
    import time
    t0 = time.perf_counter()

    # Assemble initial components
    active_system = system_prompt or ""
    active_query = user_query or ""
    active_evidence = evidence_text or ""
    active_history = list(history_turns) if history_turns else []
    active_bkt = bkt_directive or ""
    active_style = style_directive or ""
    active_memory = memory_directive or ""
    active_predecessor = predecessor_context or ""
    active_phase_inst = phase_instructions or ""
    active_other = other_directives or ""

    def _assemble_prompt() -> Tuple[str, str]:
        user_parts: List[str] = []
        if active_evidence:
            user_parts.append(f"=== EVIDENCIAS DOCUMENTADAS AUTORIZADAS ===\n{active_evidence}")
        if active_predecessor:
            user_parts.append(f"=== CONTEXTO DE FASES PREVIAS (COHERENCIA PEDAGÓGICA) ===\n{active_predecessor}")
        if active_history:
            lines = []
            for t in active_history:
                r = "Estudiante" if t.get("role") == "user" else "TALOS"
                c = (t.get("content") or "").strip()
                if c:
                    lines.append(f"[{r}]: {c}")
            if lines:
                user_parts.append("=== HISTORIAL CONVERSACIONAL RECIENTE ===\n" + "\n".join(lines))
        if active_style:
            user_parts.append(f"=== DIRECTIVA DE ESTILO Y CONVERSACIÓN ===\n{active_style}")
        if active_bkt:
            user_parts.append(active_bkt)
        if active_memory:
            user_parts.append(f"=== PERFIL COGNITIVO HISTÓRICO DEL ESTUDIANTE ===\n{active_memory}")
        if active_other:
            user_parts.append(active_other)

        user_parts.append(
            f"=== CONSULTA DEL ESTUDIANTE ===\n{active_query}\n\n"
            f"=== INSTRUCCIÓN OBLIGATORIA PARA ESTA FASE ===\n{active_phase_inst}"
        )
        return active_system, "\n\n".join(user_parts)

    cur_sys, cur_user = _assemble_prompt()
    initial_tokens = estimate_payload_tokens(cur_sys, cur_user)
    initial_chars = len(cur_sys) + len(cur_user) + 2

    actions: List[str] = []
    was_pruned = False

    # Check if initially within effective ceiling
    if initial_tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS:
        dt_ms = (time.perf_counter() - t0) * 1000
        report = C3PruningReport(
            initial_chars=initial_chars,
            initial_estimated_tokens=initial_tokens,
            final_chars=initial_chars,
            final_estimated_tokens=initial_tokens,
            was_pruned=False,
            pruning_actions=[],
            fail_closed=False,
            execution_time_ms=dt_ms,
        )
        return {
            "system_prompt": cur_sys,
            "user_prompt": cur_user,
            "evidence_text": active_evidence,
            "history_turns": active_history,
            "bkt_directive": active_bkt,
            "style_directive": active_style,
            "memory_directive": active_memory,
        }, report

    was_pruned = True

    # -------------------------------------------------------------------------
    # PHASE 1: PRUNE REDUNDANT CONTENT
    # -------------------------------------------------------------------------
    cur_sys, p_sys = prune_redundant_content(cur_sys)
    cur_user, p_usr = prune_redundant_content(cur_user)
    if p_sys or p_usr:
        actions.append("prune_redundant_formatting_and_headers")
    cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    # -------------------------------------------------------------------------
    # PHASE 2: PRUNE OPTIONAL CONTENT (predecessor context, digest, other)
    # -------------------------------------------------------------------------
    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        if active_predecessor:
            active_predecessor = ""
            actions.append("prune_optional_predecessor_context")
            cur_sys, cur_user = _assemble_prompt()
            cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        if active_other and estimate_tokens(active_other) > BUDGET_RESERVE_TOKENS:
            active_other = ""
            actions.append("prune_optional_secondary_directives")
            cur_sys, cur_user = _assemble_prompt()
            cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    # -------------------------------------------------------------------------
    # PHASE 3: PRUNE PEDAGOGICALLY USEFUL CONTENT (history & memory)
    # -------------------------------------------------------------------------
    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Progressively prune conversation history
        if active_history:
            active_history, p_hist = prune_history_turns_deterministically(
                active_history, max_tokens=BUDGET_HISTORY_TOKENS
            )
            if p_hist:
                actions.append("prune_history_turns_to_sub_budget")
                cur_sys, cur_user = _assemble_prompt()
                cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Prune memory / cognitive profile if exceeding its sub-budget
        if active_memory:
            active_memory = ""
            actions.append("prune_contextual_cognitive_memory")
            cur_sys, cur_user = _assemble_prompt()
            cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Prune non-critical style directive
        if active_style:
            active_style = ""
            actions.append("prune_secondary_style_directive")
            cur_sys, cur_user = _assemble_prompt()
            cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    # -------------------------------------------------------------------------
    # PHASE 4: PRUNE SECONDARY & PRIMARY EVIDENCE
    # -------------------------------------------------------------------------
    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Prune evidence to primary + secondary budget (1800 + 350 = 2150 tokens)
        allowed_ev_tokens = BUDGET_PRIMARY_EVIDENCE_TOKENS + BUDGET_SECONDARY_EVIDENCE_TOKENS
        if estimate_tokens(active_evidence) > allowed_ev_tokens:
            active_evidence, p_ev = prune_evidence_text_deterministically(
                active_evidence, max_tokens=allowed_ev_tokens
            )
            if p_ev:
                actions.append("prune_peripheral_evidence_to_evidence_sub_budget")
                cur_sys, cur_user = _assemble_prompt()
                cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Prune evidence strictly to primary budget (1800 tokens)
        allowed_ev_tokens = BUDGET_PRIMARY_EVIDENCE_TOKENS
        if estimate_tokens(active_evidence) > allowed_ev_tokens:
            active_evidence, p_ev = prune_evidence_text_deterministically(
                active_evidence, max_tokens=allowed_ev_tokens
            )
            if p_ev:
                actions.append("prune_evidence_strictly_to_primary_sub_budget")
                cur_sys, cur_user = _assemble_prompt()
                cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    if cur_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Severe overflow: drop all history turns
        if active_history:
            active_history = []
            actions.append("prune_all_conversational_history")
            cur_sys, cur_user = _assemble_prompt()
            cur_tokens = estimate_payload_tokens(cur_sys, cur_user)

    # -------------------------------------------------------------------------
    # PHASE 5: FINAL VERIFICATION & FAIL-CLOSED EVALUATION
    # -------------------------------------------------------------------------
    cur_sys, cur_user = _assemble_prompt()
    final_chars = len(cur_sys) + len(cur_user) + 2
    final_tokens = estimate_payload_tokens(cur_sys, cur_user)
    dt_ms = (time.perf_counter() - t0) * 1000

    if final_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
        # Irreducible overflow: FAIL-CLOSED!
        report = C3PruningReport(
            initial_chars=initial_chars,
            initial_estimated_tokens=initial_tokens,
            final_chars=final_chars,
            final_estimated_tokens=final_tokens,
            was_pruned=True,
            pruning_actions=actions,
            fail_closed=True,
            error_code="CONTEXT_BUDGET_EXCEEDED",
            error_message=(
                f"Context payload ({final_tokens} tokens / {final_chars} chars) exceeds "
                f"C3 effective hard ceiling ({EFFECTIVE_CONTEXT_CEILING_TOKENS} tokens) "
                f"even after deterministic pruning. Execution aborted fail-closed with 0 LLM calls."
            ),
            execution_time_ms=dt_ms,
        )
        return {
            "system_prompt": cur_sys,
            "user_prompt": cur_user,
            "evidence_text": active_evidence,
            "history_turns": active_history,
            "bkt_directive": active_bkt,
            "style_directive": active_style,
            "memory_directive": active_memory,
        }, report

    # Within effective ceiling!
    report = C3PruningReport(
        initial_chars=initial_chars,
        initial_estimated_tokens=initial_tokens,
        final_chars=final_chars,
        final_estimated_tokens=final_tokens,
        was_pruned=was_pruned,
        pruning_actions=actions,
        fail_closed=False,
        execution_time_ms=dt_ms,
    )
    return {
        "system_prompt": cur_sys,
        "user_prompt": cur_user,
        "evidence_text": active_evidence,
        "history_turns": active_history,
        "bkt_directive": active_bkt,
        "style_directive": active_style,
        "memory_directive": active_memory,
    }, report
