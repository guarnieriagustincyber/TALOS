"""Granularity Router for Hierarchical RAG (Parent-Document Retrieval - Fase 3).

Decides deterministically in <0.5 ms whether a query requires:
- MICRO (Level 3 leaf chunks): forensic, debugging, specific code/registers.
- MACRO (Level 2 chapter summaries): holistic synthesis, global overview, syllabus comparisons.
- HYBRID (Level 2 parent summary + Level 3 deduplicated chunks): conceptual questions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import re
from typing import Any, List, Optional, Sequence

logger = logging.getLogger(__name__)


class RetrievalGranularity(Enum):
    MICRO = "micro"       # Solo Chunks Hoja (Nivel 3)
    MACRO = "macro"       # Solo Resúmenes de Capítulo (Nivel 2)
    HYBRID = "hybrid"     # 1 Capítulo Padre (Contexto) + Chunks Hoja (Evidencia)


@dataclass(frozen=True)
class RoutingDecision:
    granularity: RetrievalGranularity
    max_parent_nodes: int
    max_leaf_chunks: int
    target_token_budget: int


class GranularityRouter:
    """Deterministic, zero-latency classifier of query granularity."""

    # Señales de depuración, bajo nivel, registros o sintaxis de código
    _RE_FORENSIC = re.compile(
        r"(?i)\b("
        r"sigsegv|segfault|crash|crashea|crashes|core\s*dumped|overflow|null\s*pointer|wild\s*pointer|"
        r"puntero\s*salvaje|segmentation\s*fault|falla\s*de\s*segmentaci[oó]n|"
        r"strcpy|strncpy|malloc|free|sizeof|printf|scanf|memcpy|memmove|"
        r"%?rdi|%?rsi|%?rax|%?rbx|%?rcx|%?rdx|%?rsp|%?rbp|%?r8|%?r9|system\s*v(\s*abi)?|"
        r"char\s*\*|int\s*\*|void\s*\*|&[a-zA-Z_]|\*[a-zA-Z_]|"
        r"linea\s*\d+|línea\s*\d+|error\s*de\s*compilaci[oó]n|todo:|ejercicio\s*\d+|tp\s*\d+|"
        r"ampersand|asterisco|desreferenci\w*|lea\b|movq\b|pushq\b|popq\b"
        r")\b"
    )

    # Señales de análisis holístico, curricular o de síntesis
    _RE_SYNTHESIS = re.compile(
        r"(?i)\b("
        r"resumen|resumime|sintesis|síntesis|panorama(?:\s*general)?|visi[oó]n\s*(?:global|general)|"
        r"qu[eé]\s+temas\s+cubre|temas\s+que\s+cubre|temario|contenido\s+de\s+la\s+unidad|"
        r"c[oó]mo\s*se\s*relaciona|relaci[oó]n\s*entre|c[oó]mo\s*se\s*articula|articulaci[oó]n\s*entre|"
        r"a\s*lo\s*largo\s*de|en\s*todo\s*el\s*libro|en\s*todo\s*el\s*cap[ií]tulo|"
        r"en\s*toda\s*la\s*materia|en\s*todo\s*el\s*programa|"
        r"[ií]ndice|syllabus|unidades\s*curriculares|evoluci[oó]n\s*hist[oó]rica|marco\s*te[oó]rico|"
        r"principios\s*rectores|diferencias\s*fundamentales\s*entre\s*cap[ií]tulos"
        r")\b"
    )

    @classmethod
    def route(cls, query: str, has_code_block: bool = False) -> RoutingDecision:
        """Route the query deterministically to a granularity level."""
        q = (query or "").strip()

        # 1. Si el usuario pegó un bloque de código o consulta por una falla forense -> MICRO estricto
        if has_code_block or "```" in q or cls._RE_FORENSIC.search(q):
            return RoutingDecision(
                granularity=RetrievalGranularity.MICRO,
                max_parent_nodes=0,
                max_leaf_chunks=6,
                target_token_budget=1800,
            )

        # 2. Si pide visión de pájaro o síntesis global -> MACRO
        if cls._RE_SYNTHESIS.search(q):
            return RoutingDecision(
                granularity=RetrievalGranularity.MACRO,
                max_parent_nodes=2,
                max_leaf_chunks=0,
                target_token_budget=2200,
            )

        # 3. Por defecto (preguntas conceptuales o teóricas) -> HÍBRIDO
        return RoutingDecision(
            granularity=RetrievalGranularity.HYBRID,
            max_parent_nodes=1,
            max_leaf_chunks=3,
            target_token_budget=2000,
        )

    @staticmethod
    def deduplicate_hybrid_chunks(
        candidate_chunks: Sequence[Any],
        parent_summary: Optional[Any],
        similarity_threshold: float = 0.85,
        max_leaves: int = 3,
    ) -> List[Any]:
        """Filter out redundant chunks whose information is already captured in parent_summary (Enmienda E-M4).
        
        Preserves chunks that contain concrete code, diagrams, or specific invariants, while
        dropping high-overlap generic prose.
        """
        if not candidate_chunks:
            return []

        if parent_summary is None:
            return list(candidate_chunks[:max_leaves])

        summary_text = getattr(parent_summary, "summary_text", "")
        summary_words = set(re.findall(r"\w+", summary_text.lower()))

        filtered: List[Any] = []
        for ch in candidate_chunks:
            ch_content = getattr(ch, "content", "") or getattr(ch, "chunk_text", "") or ""
            if not ch_content:
                continue

            # Invariante: Fragmentos con código fuente o diagramas NUNCA se descartan por redundancia
            is_code_heavy = (
                "```" in ch_content
                or any(kw in ch_content for kw in ("#include", "typedef", "struct", "void ", "int ", "char *", "->", "/*", "*/"))
            )
            if is_code_heavy:
                filtered.append(ch)
                if len(filtered) >= max_leaves:
                    break
                continue

            # Chequeo léxico / overlap con el resumen padre
            ch_words = set(re.findall(r"\w+", ch_content.lower()))
            if not ch_words:
                continue

            overlap = len(ch_words & summary_words) / float(len(ch_words))
            # Si el fragmento es prosa pura y supera el umbral de solapamiento, descartar
            if overlap >= similarity_threshold:
                logger.debug(
                    "Deduplicating chunk %s (overlap %.2f >= threshold %.2f)",
                    getattr(ch, "chunk_id", getattr(ch, "id", "unknown")),
                    overlap,
                    similarity_threshold,
                )
                continue

            filtered.append(ch)
            if len(filtered) >= max_leaves:
                break

        return filtered


deduplicate_hybrid_chunks = GranularityRouter.deduplicate_hybrid_chunks
