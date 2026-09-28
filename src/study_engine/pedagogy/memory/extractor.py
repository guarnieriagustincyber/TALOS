"""CognitiveExtractor — Explicit-preference profile updates (Opción C).

Design & Guarantees:
- A single turn never writes an inferred weakness or mastery claim to the profile.
- Only explicit preference statements are persisted by the turn-processing path.
- Existing extraction helpers remain available for offline analysis and tests.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.pedagogy.memory.schema import (
    CognitiveExtractionPayload,
    CognitiveItem,
    MemoryCategory,
)
from study_engine.pedagogy.memory.store import CognitiveProfileStore
from study_engine.student.preference_tracker import is_explicit_preference_statement

logger = logging.getLogger(__name__)

# Heurísticas deterministas de respaldo (Offline Fallback)
_HEURISTIC_MISCONCEPTIONS = [
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

_HEURISTIC_PREFERENCES = [
    re.compile(
        r"(?:prefiero|me\s+sirve\s+m[aá]s|me\s+ayuda\s+m[aá]s)\s+(.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:explicame\s+con|mostrame|dame)\s+(?:un\s+ejemplo|un\s+diagrama|una\s+tabla|paso\s+a\s+paso|.+?)(?:\.|\?|$)",
        re.IGNORECASE,
    ),
]


class CognitiveExtractor:
    """Persist explicit preferences without treating one turn as domain evidence."""

    def __init__(
        self,
        store: CognitiveProfileStore,
        catalog_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.store = store
        self.catalog_path = Path(catalog_path or "config/notebook_kc_catalog.json")
        self._kc_catalog: Dict[str, Set[str]] = self._load_kc_catalog()

    def _load_kc_catalog(self) -> Dict[str, Set[str]]:
        """Loads valid KC IDs mapped by notebook_id."""
        mapping: Dict[str, Set[str]] = {}
        if not self.catalog_path.exists():
            logger.warning("[COGNITIVE_EXTRACTOR] KC catalog not found at %s", self.catalog_path)
            return mapping

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for nb_id, nb_info in data.items():
                kcs = nb_info.get("kcs", [])
                mapping[nb_id] = {k["kc_id"] for k in kcs if "kc_id" in k}
        except Exception as exc:
            logger.error("[COGNITIVE_EXTRACTOR] Error loading KC catalog: %s", exc)
        return mapping

    def get_valid_kcs(self, notebook_id: str) -> Set[str]:
        return self._kc_catalog.get(notebook_id, set())

    def validate_kc(self, notebook_id: str, kc_id: Optional[str]) -> Optional[str]:
        if not kc_id:
            return None
        valid_set = self.get_valid_kcs(notebook_id)
        if kc_id in valid_set:
            return kc_id
        # Fallback: check across all notebooks if known
        for nb, kcs in self._kc_catalog.items():
            if kc_id in kcs:
                return kc_id
        return None

    def _extract_heuristics(
        self,
        query: str,
        student_id: str,
        active_kc: str,
    ) -> List[CognitiveItem]:
        """Deterministic offline rule-based extraction in <1ms."""
        items: List[CognitiveItem] = []
        clean_q = (query or "").strip()

        # Check preferences
        for pat in _HEURISTIC_PREFERENCES:
            m = pat.search(clean_q)
            if m:
                matched = [p.strip() for p in m.groups() if p and p.strip()]
                desc = f"Preferencia didáctica: {matched[0] if matched else m.group(0)}"[:200]
                items.append(
                    CognitiveItem(
                        user_id=student_id,
                        kc_id=active_kc,
                        category=MemoryCategory.PREFERENCE,
                        description=desc,
                        evidence_quote=clean_q[:120],
                        confidence=1.0,
                    )
                )
                break

        # Check misconceptions
        for pat in _HEURISTIC_MISCONCEPTIONS:
            m = pat.search(clean_q)
            if m:
                matched = [p.strip() for p in m.groups() if p and p.strip()]
                desc = ("Confusión expresada: " + " en vez de ".join(matched))[:200]
                items.append(
                    CognitiveItem(
                        user_id=student_id,
                        kc_id=active_kc,
                        category=MemoryCategory.WEAKNESS,
                        description=desc,
                        evidence_quote=clean_q[:120],
                        confidence=0.85,
                    )
                )
                break

        return items

    async def _extract_with_llm(
        self,
        query: str,
        response_text: str,
        student_id: str,
        notebook_id: str,
        active_kc: str,
        llm_backend: Optional[Any],
    ) -> Optional[CognitiveExtractionPayload]:
        """Cascade: Groq -> Gemini -> None."""
        valid_kcs = sorted(list(self.get_valid_kcs(notebook_id)))
        kc_context = f"KCs válidos para este módulo ({notebook_id}):\n" + ", ".join(valid_kcs[:25])

        system_prompt = (
            "Sos un evaluador cognitivo de precisión pedagógica. Analizá el turno del estudiante.\n"
            "Tu tarea es identificar si expresó una confusión conceptual (WEAKNESS / RECURRING_MISCONCEPTION),\n"
            "una preferencia didáctica explícita (PREFERENCE) o afinidad con analogías (ANALOGY_AFFINITY).\n"
            "REGLAS CRÍTICAS:\n"
            "1. Grounding estricto: kc_id DEBE ser uno de los KCs provistos o el default provisto.\n"
            "2. Sin prosa adicional: Devolvé ÚNICAMENTE un objeto JSON válido con la clave 'items'.\n"
            "3. Cada item tiene: {'kc_id', 'category', 'description', 'evidence_quote', 'confidence'}.\n"
            "4. Si no hay confusión ni preferencia relevante, devolvé: {\"items\": []}.\n"
            "5. description máx 200 caracteres. evidence_quote máx 120 caracteres de las palabras del estudiante."
        )

        user_content = (
            f"{kc_context}\n"
            f"KC Activo por defecto: {active_kc}\n\n"
            f"Consulta del estudiante: \"{query}\"\n"
            f"Respuesta pedagógica dada: \"{response_text[:350]}\""
        )

        messages = (PromptMessage(role=PromptRole.USER, content=user_content),)
        params = GenerationParameters(temperature=0.0, max_output_tokens=220)
        p_hash = compute_canonical_prompt_hash(system_prompt, messages, params)
        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=p_hash,
        )

        # 1. Intentar Groq Fast Micro-LLM si existe API key
        backends_to_try = []
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key and groq_key.startswith("gsk_"):
            try:
                from study_engine.llm.backends import HttpOpenAIBackend
                backends_to_try.append(
                    (
                        "groq-micro",
                        HttpOpenAIBackend(
                            api_key=groq_key,
                            base_url="https://api.groq.com/openai/v1",
                            default_model=os.environ.get("GROQ_MICRO_MODEL", "qwen/qwen3.8-27b"),
                            timeout_seconds=4.0,
                        ),
                    )
                )
            except Exception:
                pass

        # 2. Intentar backend principal provisto (Gemini Flash Lite / MultiFallback)
        if llm_backend and hasattr(llm_backend, "complete"):
            backends_to_try.append(("primary-fallback", llm_backend))

        for name, backend in backends_to_try:
            t0 = time.perf_counter()
            try:
                import asyncio
                comp = await asyncio.wait_for(
                    asyncio.to_thread(backend.complete, bundle),
                    timeout=5.0,
                )
                raw_text = getattr(comp, "text", "").strip()
                if not raw_text:
                    continue

                # Parse JSON
                json_str = raw_text
                if "```json" in raw_text:
                    json_str = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    json_str = raw_text.split("```")[1].split("```")[0].strip()

                data = json.loads(json_str)
                raw_items = data.get("items", [])
                parsed_items: List[CognitiveItem] = []

                for it in raw_items:
                    raw_kc = it.get("kc_id", active_kc)
                    grounded_kc = self.validate_kc(notebook_id, raw_kc) or active_kc
                    cat_str = str(it.get("category", "WEAKNESS")).upper()
                    try:
                        cat = MemoryCategory(cat_str)
                    except ValueError:
                        cat = MemoryCategory.WEAKNESS

                    parsed_items.append(
                        CognitiveItem(
                            user_id=student_id,
                            kc_id=grounded_kc,
                            category=cat,
                            description=str(it.get("description", ""))[:200],
                            evidence_quote=(str(it.get("evidence_quote", ""))[:120]) if it.get("evidence_quote") else None,
                            confidence=float(it.get("confidence", 0.9)),
                        )
                    )

                latency = (time.perf_counter() - t0) * 1000.0
                return CognitiveExtractionPayload(
                    items=parsed_items,
                    extraction_model=name,
                    extraction_latency_ms=latency,
                    grounded=True,
                )
            except Exception as exc:
                logger.debug("[COGNITIVE_EXTRACTOR] Backend %s failed: %s", name, exc)
                continue

        return None

    async def process_turn_and_persist(
        self,
        student_id: str,
        notebook_id: str,
        query: str,
        response_text: str,
        active_kc: Optional[str] = None,
        llm_backend: Optional[Any] = None,
    ) -> List[str]:
        """Persist only explicit learning preferences; a single answer is not mastery evidence."""
        valid_kc = self.validate_kc(notebook_id, active_kc) or active_kc or "GENERAL_STUDY"
        persisted_ids: List[str] = []

        try:
            # A one-turn misconception or an LLM classification is insufficient
            # evidence for a persistent learner-domain profile.
            items_to_persist = []
            if is_explicit_preference_statement(query):
                items_to_persist = [
                    item
                    for item in self._extract_heuristics(
                        query=query,
                        student_id=student_id,
                        active_kc=valid_kc,
                    )
                    if item.category == MemoryCategory.PREFERENCE
                ]

            # Persistir únicamente declaraciones de preferencia explícitas.
            for item in items_to_persist:
                row_id = self.store.upsert_item(item)
                persisted_ids.append(row_id)
                logger.info(
                    "[COGNITIVE_EXTRACTOR] Persisted explicit preference %s for KC %s: %s",
                    row_id,
                    item.kc_id,
                    item.description[:60],
                )

        except Exception as exc:
            logger.warning("[COGNITIVE_EXTRACTOR] Unhandled error in background extraction: %s", exc)

        return persisted_ids
