"""Deterministic heuristics for Intent & Context Routing (Ola 5, Fase 5.2).

Capa 1: Heurísticas deterministas basadas en regex y reglas canónicas (0 llamadas de red/LLM).
Invariante INV-W5-3: Ninguna regla ni decisión evalúa, muta ni decide sobre BKT o maestría del alumno.
"""

import re
from typing import Any, Optional, Tuple
from study_engine.context.routing_decision import RoutingDecision


class ContextHeuristics:
    """Evaluates deterministic lexical patterns and context state to route queries without LLM overhead."""

    # Regex patterns for query routing
    GLOBAL_CROSS_PATTERNS = (
        re.compile(r"(?i)\b(?:compar[aá]|diferencia|versus|\bvs\b)\b"),
        re.compile(r"(?i)\b(?:todos\s+los\s+libros|a\s+lo\s+largo\s+de\s+todo|en\s+todas\s+las\s+fuentes|entre\s+autores)\b"),
        re.compile(r"(?i)\b(?:panorama\s+general|visi[oó]n\s+global|resumen\s+completo|estado\s+del\s+arte)\b"),
    )

    DEEP_CHAPTER_PATTERNS = (
        re.compile(r"(?i)\b(?:cap[ií]tulo\s+\d+|secci[oó]n\s+\d+|unidad\s+\d+)\b"),
        re.compile(r"(?i)\b(?:desglos[aá]|analiz[aá]\s+en\s+detalle|profundiz[aá]|en\s+detalle|paso\s+a\s+paso)\b"),
        re.compile(r"(?i)\b(?:explicaci[oó]n\s+exhaustiva|desarrollo\s+formal|demostraci[oó]n)\b"),
    )

    NORMAL_FOCAL_PATTERNS = (
        re.compile(r"(?i)^\s*¿?\s*(?:qu[eé]\s+es|qu[eé]\s+significa|c[oó]mo\s+se\s+define|definici[oó]n\s+de)\b"),
        re.compile(r"(?i)^\s*¿?\s*(?:cu[aá]l\s+es\s+la\s+f[oó]rmula|cu[aá]l\s+es\s+el\s+prop[oó]sito)\b"),
        re.compile(r"(?i)^\s*¿?\s*(?:dame\s+un\s+ejemplo|un\s+ejemplo\s+concreto)\b"),
    )

    GREETING_PATTERNS = (
        re.compile(r"(?i)^\s*(?:hola|buenas|buenos\s+d[ií]as|buenas\s+tardes|chau|adi[oó]s|gracias|muchas\s+gracias)\s*[!.]?\s*$"),
    )

    PEDAGOGICAL_BLOCK_PATTERNS = (
        re.compile(r"(?i)\b(?:dame\s+la\s+soluci[oó]n\s+completa|resolv[eé]melo\s+todo|haceme\s+el\s+ejercicio|dame\s+el\s+c[oó]digo\s+resuelto)\b"),
    )

    @classmethod
    def evaluate(
        cls,
        query: str,
        *,
        has_multimodal_asset: bool = False,
        active_kc_id: Optional[str] = None,
        has_active_exercise: bool = False,
    ) -> Tuple[Optional[RoutingDecision], float]:
        """Evaluate deterministic layer.

        Returns (RoutingDecision, confidence). If confidence >= 0.9, routing can proceed immediately.
        """
        q = query.strip()
        if not q:
            return (
                RoutingDecision(
                    depth="NORMAL",
                    requires_multimodal=has_multimodal_asset,
                    requires_multi_source=False,
                    requires_long_context=False,
                    max_context_tokens=5000,
                    cloud_allowed=True,
                    suggested_provider=None,
                    explanation="Empty query routed to default focal context.",
                ),
                1.0,
            )

        # 1. Chequeo de pacto pedagógico (bloqueo determinista de soluciones completas)
        for pat in cls.PEDAGOGICAL_BLOCK_PATTERNS:
            if pat.search(q):
                return (
                    RoutingDecision(
                        depth="NORMAL",
                        requires_multimodal=has_multimodal_asset,
                        requires_multi_source=False,
                        requires_long_context=False,
                        max_context_tokens=2000,
                        cloud_allowed=True,
                        suggested_provider=None,
                        explanation="Pedagogical block: direct answer requested, bounded to minimal guidance context.",
                    ),
                    1.0,
                )

        # 2. Saludo / despedida / cortesía pura
        for pat in cls.GREETING_PATTERNS:
            if pat.match(q):
                return (
                    RoutingDecision(
                        depth="NORMAL",
                        requires_multimodal=has_multimodal_asset,
                        requires_multi_source=False,
                        requires_long_context=False,
                        max_context_tokens=0,
                        cloud_allowed=True,
                        suggested_provider=None,
                        explanation="Greeting/courtesy query requiring zero corpus retrieval.",
                    ),
                    1.0,
                )

        # 3. Ejercicio activo en curso -> NORMAL focal
        if has_active_exercise:
            return (
                RoutingDecision(
                    depth="NORMAL",
                    requires_multimodal=has_multimodal_asset,
                    requires_multi_source=False,
                    requires_long_context=False,
                    max_context_tokens=5000,
                    cloud_allowed=True,
                    suggested_provider=None,
                    explanation="Active exercise context: bounded focal context for guided evaluation.",
                ),
                0.95,
            )

        # 4. GLOBAL / Cross-Source / Comparaciones / Panorama
        for pat in cls.GLOBAL_CROSS_PATTERNS:
            if pat.search(q):
                return (
                    RoutingDecision(
                        depth="GLOBAL",
                        requires_multimodal=has_multimodal_asset,
                        requires_multi_source=True,
                        requires_long_context=True,
                        max_context_tokens=40000,
                        cloud_allowed=True,
                        suggested_provider=None,
                        explanation="Global cross-source / synthesis query requiring multi-source long context.",
                    ),
                    0.95,
                )

        # 5. DEEP / Capítulo / Desglose detallado
        for pat in cls.DEEP_CHAPTER_PATTERNS:
            if pat.search(q):
                return (
                    RoutingDecision(
                        depth="DEEP",
                        requires_multimodal=has_multimodal_asset,
                        requires_multi_source=False,
                        requires_long_context=True,
                        max_context_tokens=16000,
                        cloud_allowed=True,
                        suggested_provider=None,
                        explanation="Deep chapter/section analysis query requiring expanded context window.",
                    ),
                    0.95,
                )

        # 6. NORMAL / Focal definicional ("¿Qué es X?", "¿Cómo se define X?", etc.)
        for pat in cls.NORMAL_FOCAL_PATTERNS:
            if pat.search(q):
                return (
                    RoutingDecision(
                        depth="NORMAL",
                        requires_multimodal=has_multimodal_asset,
                        requires_multi_source=False,
                        requires_long_context=False,
                        max_context_tokens=5000,
                        cloud_allowed=True,
                        suggested_provider=None,
                        explanation="Focal conceptual definition query requiring standard bounded context.",
                    ),
                    0.95,
                )

        # Si hay KC activo y es una consulta corta (<= 8 palabras)
        word_count = len(q.split())
        if active_kc_id and word_count <= 8:
            return (
                RoutingDecision(
                    depth="NORMAL",
                    requires_multimodal=has_multimodal_asset,
                    requires_multi_source=False,
                    requires_long_context=False,
                    max_context_tokens=5000,
                    cloud_allowed=True,
                    suggested_provider=None,
                    explanation=f"Short query aligned with active KC ({active_kc_id}): focal routing.",
                ),
                0.90,
            )

        # No match contundente en Capa 1
        return None, 0.0
