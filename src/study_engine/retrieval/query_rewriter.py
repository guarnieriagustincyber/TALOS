"""Query Rewriter for Hybrid Retrieval (Semana 4).

Translates informal, vague, or colloquially-worded student questions into canonical
academic and technical search terms for FTS5 lexical indexing and Multilingual-E5
dense vector retrieval.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common student spelling errors & typos in computer systems / programming
_TYPO_CORRECTIONS: Dict[re.Pattern, str] = {
    re.compile(r"\bpunter[os]*\b", re.IGNORECASE): "puntero",
    re.compile(r"\bsincronisaci[oó]n\b", re.IGNORECASE): "sincronización",
    re.compile(r"\bsem[aá]foros*\b", re.IGNORECASE): "semáforo",
    re.compile(r"\bmemori\b", re.IGNORECASE): "memoria",
    re.compile(r"\binstrucsi[oó]n\b", re.IGNORECASE): "instrucción",
    re.compile(r"\brecursividad\b", re.IGNORECASE): "recursión",
    re.compile(r"\bdirecsi[oó]n\b", re.IGNORECASE): "dirección",
    re.compile(r"\bassembly\b", re.IGNORECASE): "ensamblador",
    re.compile(r"\bassembler\b", re.IGNORECASE): "ensamblador",
}

# Mapping of colloquial / vague student phrases to canonical curriculum keywords
_COLLOQUIAL_EXPANSIONS: List[Tuple[re.Pattern, str]] = [
    # Sincronización y concurrencia
    (
        re.compile(r"(?:el\s+coso|lo\s+que\s+hace|mecanismo)\s+(?:de\s+)?sincronizaci[oó]n", re.IGNORECASE),
        "mecanismos de sincronización concurrente semáforos mutex variables de condición sección crítica",
    ),
    (
        re.compile(r"que\s+no\s+se\s+pisen\s+(?:los\s+)?(?:hilos|procesos|threads)", re.IGNORECASE),
        "exclusión mutua sección crítica race condition condición de carrera semáforo mutex",
    ),
    (
        re.compile(r"cuando\s+(?:dos\s+)?(?:hilos|procesos)\s+(?:se\s+traban|quedan\s+esperando|no\s+avanzan)", re.IGNORECASE),
        "interbloqueo deadlock abrazo mortal condiciones de coffman espera circular",
    ),
    # Gestión de memoria
    (
        re.compile(r"(?:la\s+memoria|pedir\s+memoria|memoria)\s+(?:a\s+mano|manualmente|en\s+ejecuci[oó]n)", re.IGNORECASE),
        "asignación dinámica de memoria heap montículo malloc free calloc punteros",
    ),
    (
        re.compile(r"(?:d[oó]nde\s+van|donde\s+se\s+guardan)\s+las\s+variables\s+locales", re.IGNORECASE),
        "stack marco de activación stack frame registro rsp rbp variables automáticas",
    ),
    (
        re.compile(r"(?:el\s+coso\s+de\s+la\s+funci[oó]n|marco\s+de\s+la\s+funci[oó]n|lo\s+que\s+crea\s+la\s+funci[oó]n)", re.IGNORECASE),
        "stack frame marco de activación prólogo epílogo llamada a función rbp rsp",
    ),
    # Llamada a funciones y pasaje de parámetros
    (
        re.compile(r"(?:pasar|pasarle)\s+(?:cosas|datos|argumentos)\s+a\s+(?:una\s+)?funci[oó]n", re.IGNORECASE),
        "convención de llamada pasaje de parámetros ABI registros rdi rsi rdx rcx stack",
    ),
    (
        re.compile(r"(?:volver|retornar)\s+de\s+(?:una\s+)?funci[oó]n", re.IGNORECASE),
        "instrucción ret dirección de retorno stack registro rax epílogo",
    ),
    # Punteros y direccionamiento
    (
        re.compile(r"(?:la\s+flechita|el\s+operador\s+flecha)\s+en\s+c", re.IGNORECASE),
        "operador de acceso a miembros por puntero desreferenciación flecha estructuras struct",
    ),
    (
        re.compile(r"(?:el\s+asterisco|el\s+cosito)\s+adelante\s+de\s+(?:un\s+)?puntero", re.IGNORECASE),
        "operador de desreferenciación indirección punteros valor apuntado",
    ),
    (
        re.compile(r"(?:el\s+ampersand|la\s+y\s+griega|el\s+s[ií]mbolo\s+&)\s+en\s+c", re.IGNORECASE),
        "operador de dirección ampersand obtención de dirección de memoria punteros",
    ),
    # CPU y arquitectura
    (
        re.compile(r"(?:las\s+cajitas|la\s+memoria\s+r[aá]pida)\s+de\s+la\s+cpu", re.IGNORECASE),
        "registros del procesador registros de propósito general rax rbx rcx rdx rsi rdi",
    ),
    (
        re.compile(r"(?:las\s+banderitas|los\s+flags)\s+de\s+la\s+cpu", re.IGNORECASE),
        "registro de estado flags RFLAGS carry flag zero flag sign flag overflow flag",
    ),
]


class QueryRewriter:
    """Expands student queries into canonical academic vocabulary for hybrid retrieval."""

    def __init__(self, use_llm_fallback: bool = False) -> None:
        self.use_llm_fallback = use_llm_fallback

    def rewrite(self, query: str) -> str:
        """Rewrite and expand query deterministically in < 0.1ms."""
        q = (query or "").strip()
        if not q or len(q) < 4:
            return q

        # 1. Apply typo corrections
        clean = q
        for pat, replacement in _TYPO_CORRECTIONS.items():
            clean = pat.sub(replacement, clean)

        # 2. Check for colloquial expansions
        expansions: List[str] = []
        for pat, canonical_terms in _COLLOQUIAL_EXPANSIONS:
            if pat.search(clean):
                expansions.append(canonical_terms)

        if not expansions:
            return clean

        # Preserve exact multi-word phrases (bigrams/trigrams) for E5 embeddings and FTS5 phrases
        seen = set()
        unique_expansions: List[str] = []
        for exp in expansions:
            if exp not in seen:
                seen.add(exp)
                unique_expansions.append(exp)

        expanded_query = f"{clean} {' '.join(unique_expansions)}".strip()
        return expanded_query
