"""Pedagogical Memory Extractor for explicit student preferences.

The turn-processing path persists explicit preferences only. A single confusion
or a model-generated interpretation is not sufficient evidence for permanent
student-profile mutation.
"""

from __future__ import annotations

import asyncio
import logging
import os
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
from study_engine.student.preference_tracker import is_explicit_preference_statement

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

        # Priorizar Groq para destilación ultrarrápida (<50ms) si está configurado en .env
        active_backend = llm_backend
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key and groq_key.startswith("gsk_"):
            try:
                from study_engine.llm.backends import HttpOpenAIBackend
                active_backend = HttpOpenAIBackend(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1",
                    default_model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    timeout_seconds=5.0,
                )
            except Exception as e:
                logger.debug("No se pudo instanciar Groq para extracción de misconceptions: %s", e)

        if (
            active_backend is None
            or isinstance(active_backend, OfflinePedagogicalBackend)
            or not hasattr(active_backend, "complete")
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
            comp = active_backend.complete(bundle)
            return getattr(comp, "text", "").strip()

        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(_sync_call),
                timeout=3.5,
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
            if pref and is_explicit_preference_statement(query):
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

        except Exception as exc:
            logger.warning("Error processing background pedagogical memory: %s", exc)

        return None
