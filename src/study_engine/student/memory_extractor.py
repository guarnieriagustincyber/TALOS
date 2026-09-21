"""Pedagogical Memory Extractor for Student Interactions (Semana 2).

Extracts conceptual misconceptions, explanation preferences, and domain analogy
affinities from student dialogue using deterministic heuristics and optional
lightweight LLM distillation in background tasks.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker

logger = logging.getLogger(__name__)

# Heuristic patterns identifying explicit misconceptions or epistemic conflict in Spanish
_MISCONCEPTION_PATTERNS = [
    re.compile(
        r"(?:pens[eé]|cre[ií]|asum[ií])\s+que\s+(.+?)(?:,\s*pero|\s+y\s+no|\s+y\s+resulta|\.|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"por\s+qu[eé]\s+(.+?)\s+si\s+(?:en\s+realidad|para\s+m[ií]|yo\s+pensaba|deber[ií]a)\s+(.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"no\s+entiendo\s+por\s+qu[eé]\s+(.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:me\s+confund[ií]|me\s+confunde|confundo)\s+(?:entre\s+)?(.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"yo\s+pensaba\s+que\s+(.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
]

# Heuristic patterns identifying pedagogical explanation preferences
_PREFERENCE_PATTERNS = [
    re.compile(
        r"(?:prefiero|me\s+sirve\s+m[aá]s|me\s+ayuda\s+m[aá]s|explicame\s+con)\s+(.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:mostrame|dame)\s+(?:un\s+ejemplo|un\s+diagrama|una\s+tabla|paso\s+a\s+paso)",
        re.IGNORECASE,
    ),
]


class PedagogicalMemoryExtractor:
    """Extracts and persists qualitative insights without blocking response streams."""

    def __init__(self, tracker: Optional[PedagogicalMemoryTracker] = None) -> None:
        self.tracker = tracker or PedagogicalMemoryTracker()

    def extract_heuristic_misconception(self, query: str) -> Optional[str]:
        """Extract misconception deterministically from student query in < 1ms."""
        clean_q = (query or "").strip("¿¡!?. \t\n\r")
        if len(clean_q) < 8:
            return None

        for pat in _MISCONCEPTION_PATTERNS:
            m = pat.search(clean_q)
            if m:
                # Format extracted capture cleanly
                matched_parts = [p.strip() for p in m.groups() if p and p.strip()]
                if matched_parts:
                    insight = "Confusión expresada: " + " en vez de ".join(matched_parts)
                    return insight[:200]
        return None

    def extract_heuristic_preference(self, query: str) -> Optional[str]:
        """Extract learning preference deterministically from student query in < 1ms."""
        clean_q = (query or "").strip()
        for pat in _PREFERENCE_PATTERNS:
            m = pat.search(clean_q)
            if m:
                matched_parts = [p.strip() for p in m.groups() if p and p.strip()]
                if matched_parts:
                    return f"Preferencia didáctica: {matched_parts[0][:150]}"
                return f"Preferencia didáctica: {m.group(0).strip()[:150]}"
        return None

    async def extract_llm_misconception(
        self,
        query: str,
        response_text: str,
        llm_backend: Any,
    ) -> Optional[str]:
        """Distill underlying misconception into 1 concise sentence via Micro-LLM in background."""
        from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

        if (
            llm_backend is None
            or isinstance(llm_backend, OfflinePedagogicalBackend)
            or not hasattr(llm_backend, "complete")
        ):
            return None

        system_prompt = (
            "Sos un asistente pedagógico forense. Tu única tarea es identificar si el estudiante "
            "expresó una confusión conceptual o error de razonamiento en su consulta. "
            "Si hubo un misconception, resumilo en UNA SOLA oración concisa en español comenzando con 'Cree que...' o 'Confunde...'. "
            "Si la consulta fue una pregunta normal sin error conceptual previo, respondé exactamente 'NONE'."
        )
        user_content = (
            f"Consulta del estudiante: \"{query}\"\n"
            f"Respuesta del tutor: \"{response_text[:400]}\""
        )
        messages = (PromptMessage(role=PromptRole.USER, content=user_content),)
        params = GenerationParameters(temperature=0.1, max_output_tokens=50)
        p_hash = compute_canonical_prompt_hash(system_prompt, messages, params)
        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=p_hash,
        )

        def _sync_call() -> str:
            comp = llm_backend.complete(bundle)
            return getattr(comp, "text", "").strip()

        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=2.0,
            )
            cleaned = raw_text.strip().strip("'\"")
            if not cleaned or "NONE" in cleaned.upper() or len(cleaned) < 10:
                return None
            return cleaned[:200]
        except Exception as exc:
            logger.debug("Background LLM misconception extraction skipped: %s", exc)
            return None

    async def process_turn_and_persist(
        self,
        student_id: str,
        query: str,
        response_text: str,
        active_kc: Optional[str] = None,
        pedagogical_mode: Optional[str] = None,
        llm_backend: Optional[Any] = None,
    ) -> Optional[int]:
        """Analyze turn in background and persist to SQLite if insights are discovered."""
        try:
            # 1. Check for explicit learning preference first
            pref = self.extract_heuristic_preference(query)
            if pref:
                # Check duplication before saving
                existing = self.tracker.storage.get_pedagogical_memories(
                    student_id=student_id,
                    category="preference",
                    limit=5,
                )
                for m in existing:
                    if pref.lower() in m.get("insight", "").lower():
                        self.tracker.storage.touch_pedagogical_memory(m["id"])
                        return m["id"]
                return self.tracker.record_preference(
                    student_id=student_id,
                    preference_text=pref,
                    confidence=1.0,
                )

            # 2. Check for misconception (heuristic or resolve_misconception mode)
            misconception = self.extract_heuristic_misconception(query)

            if not misconception and pedagogical_mode == "resolve_misconception" and llm_backend:
                misconception = await self.extract_llm_misconception(
                    query=query,
                    response_text=response_text,
                    llm_backend=llm_backend,
                )

            if misconception:
                # Check duplication for this KC
                existing_kc = self.tracker.storage.get_pedagogical_memories(
                    student_id=student_id,
                    category="misconception",
                    kc_id=active_kc,
                    limit=5,
                )
                for m in existing_kc:
                    if misconception.lower() in m.get("insight", "").lower():
                        self.tracker.storage.touch_pedagogical_memory(m["id"])
                        return m["id"]

                return self.tracker.record_misconception(
                    student_id=student_id,
                    kc_id=active_kc or "GENERAL",
                    misconception=misconception,
                    confidence=0.85,
                )

        except Exception as exc:
            logger.warning("Error processing background pedagogical memory: %s", exc)

        return None
