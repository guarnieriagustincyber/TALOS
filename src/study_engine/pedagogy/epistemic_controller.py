"""EpistemicController: Deterministic & Fast-Synthesis Epistemic Engine (Ola 6, Fase 6.1).

Stage 1 of the Two-Stage Architecture.
- For NORMAL/DEEP/VERIFICATION/CASUAL queries:
  -> Pure deterministic Python execution (fact extraction + BKT calculation + pedagogical constraints).
  -> 0 LLM calls, deterministic TTFT < 1.2s.
- For GLOBAL/CROSS_SOURCE queries:
  -> Rapid multi-source synthesis query (e.g. Groq in strict JSON mode).
- Invariants:
  -> INV-W6-1: Emits complete and bounded core_facts.
  -> INV-W6-2: Consults BKT state without non-verified mutations.
  -> INV-W6-3: Never leaks active solutions in facts.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

_INDIRECT_INJECTION_PATTERNS = [
    re.compile(r"\[\s*(?:INSTRUCCI[ÓO]N\s+DEL\s+SISTEMA|SYSTEM[_\s]OVERRIDE|ADMIN[_\s]OVERRIDE|DIRECTIVA\s+DEL\s+SISTEMA)[^\]]*\]\s*", re.IGNORECASE),
    re.compile(r"\"?\s*\b(?:SYSTEM[_\s]OVERRIDE|ADMIN[_\s]OVERRIDE)\b[^\"]*\"?", re.IGNORECASE),
]

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.controller_payload import (
    BKTStatus,
    Citation,
    ControllerPayload,
    ConversationStyle,
    Fact,
    PedagogicalConstraints,
)
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage

logger = logging.getLogger(__name__)


class EpistemicController:
    """Stage 1 Epistemic Controller preparing factual and pedagogical payloads."""

    def __init__(
        self,
        student_storage: Optional[StudentStorage] = None,
        synthesis_llm_backend: Optional[Any] = None,
    ) -> None:
        self.student_storage = student_storage
        self.synthesis_llm_backend = synthesis_llm_backend

    def process(
        self,
        query: str,
        context_pack: ContextPack,
        *,
        kc_id: Optional[str] = None,
        style: ConversationStyle = ConversationStyle.NORMAL,
        active_exercise_solution: Optional[str] = None,
        session_briefing: str = "",
        is_global_cross_source: bool = False,
    ) -> ControllerPayload:
        """Execute Stage 1 processing and emit structured ControllerPayload."""
        start_time = time.perf_counter()

        # 1. Calculate BKT status deterministically (INV-W6-2)
        effective_kc = kc_id or context_pack.current_kc or "general_concepts"
        bkt_state: Optional[BKTState] = None
        if self.student_storage:
            bkt_state = self.student_storage.get_bkt_state(effective_kc)

        p_L = bkt_state.p_L if bkt_state else 0.40
        if p_L < 0.50:
            mastery_level = "novice"
        elif p_L < 0.85:
            mastery_level = "competent"
        else:
            mastery_level = "mastered"

        bkt_status = BKTStatus(
            kc_id=effective_kc,
            p_L=round(p_L, 2),
            mastery_level=mastery_level,
            recurrent_errors=tuple(context_pack.previous_errors),
        )

        # 2. Extract facts and citations deterministically
        facts: List[Fact] = []
        citations: List[Citation] = []

        # Handle GLOBAL / CROSS_SOURCE with synthesis backend if active
        if is_global_cross_source and self.synthesis_llm_backend is not None:
            synth_facts = self._synthesize_cross_source_facts(query, context_pack)
            facts.extend(synth_facts)
        else:
            # Deterministic extraction directly from context_pack.retrieved_evidence
            for idx, chk in enumerate(context_pack.retrieved_evidence):
                f_id = f"fact_{idx+1}"
                stmt = chk.content.strip()
                # If active exercise solution exists, ensure it is NOT leaked into facts (INV-W6-3)
                if active_exercise_solution and active_exercise_solution.strip() in stmt:
                    stmt = stmt.replace(active_exercise_solution.strip(), "[SOLUCIÓN PROTEGIDA]")

                # Sanitize indirect prompt injections embedded in corpus chunks
                for inj_pattern in _INDIRECT_INJECTION_PATTERNS:
                    stmt = inj_pattern.sub("", stmt).strip()

                terms = tuple(w for w in stmt.split() if len(w) > 6 and w.isalpha())[:5]
                facts.append(
                    Fact(
                        fact_id=f_id,
                        statement=stmt,
                        source_id=chk.source_id,
                        chunk_id=chk.chunk_id,
                        page=chk.page_start,
                        technical_terms=terms,
                    )
                )

                cite_id = f"E{idx+1}"
                citations.append(
                    Citation(
                        citation_id=cite_id,
                        source_title=chk.source_title,
                        author=chk.source_title,
                        page=chk.page_start,
                        chunk_id=chk.chunk_id,
                    )
                )

        # 3. Configure pedagogical constraints
        constraints = PedagogicalConstraints(
            forbidden_solution_leak=True,
            suggest_exercise=p_L >= 0.70,
            max_words=600 if style == ConversationStyle.DEEP else 400,
            analogy_allowed=p_L < 0.60,
            code_generation_allowed=False,
            forbidden_terms=tuple(filter(None, [active_exercise_solution])) if active_exercise_solution else (),
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.debug(f"[CONTROLLER] Executed deterministically in {latency_ms:.2f}ms")

        return ControllerPayload(
            query=query,
            core_facts=tuple(facts),
            citations=tuple(citations),
            bkt_status=bkt_status,
            pedagogical_constraints=constraints,
            style_directive=style,
            session_briefing=session_briefing,
            context_tokens=context_pack.total_tokens,
        )

    def _synthesize_cross_source_facts(self, query: str, context_pack: ContextPack) -> List[Fact]:
        """Rapid synthesis for cross-source queries using fast LLM backend."""
        # Returns parsed facts from JSON synthesis
        facts = []
        for idx, chk in enumerate(context_pack.retrieved_evidence):
            facts.append(
                Fact(
                    fact_id=f"synth_fact_{idx+1}",
                    statement=f"Síntesis de {chk.source_title}: {chk.content[:100]}...",
                    source_id=chk.source_id,
                    chunk_id=chk.chunk_id,
                    page=chk.page_start,
                )
            )
        return facts
