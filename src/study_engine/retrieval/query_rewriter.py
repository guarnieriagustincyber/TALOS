"""Query Rewriter for Hybrid Retrieval (Semana 4).

Translates informal, vague, or colloquially-worded student questions into canonical
academic and technical search terms for FTS5 lexical indexing and Multilingual-E5
dense vector retrieval.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReferenceResolution:
    """Deterministic resolution result for a contextual reference."""

    status: str
    candidates: Tuple[str, ...] = ()


def resolve_contextual_reference(
    query: str,
    recent_turns: Optional[List[Dict[str, str]]] = None,
) -> ReferenceResolution:
    """Resolve only references with an unambiguous local antecedent."""
    clean = (query or "").strip()
    turns = [t for t in (recent_turns or []) if isinstance(t, dict) and t.get("content")]
    explicit_deictic = re.search(
        r"\b(?:eso|esto|aquello|lo\s+anterior|lo\s+que\s+dijiste)\b",
        clean,
        re.IGNORECASE,
    )
    ordinal = re.search(
        r"\b(?:el|la)\s+(primero|segundo|tercero|anterior|siguiente)\b",
        clean,
        re.IGNORECASE,
    )
    if not turns and ordinal is None and explicit_deictic is None:
        return ReferenceResolution("not_applicable")
    if not turns:
        return ReferenceResolution("missing")

    if ordinal:
        index = {"primero": 0, "segundo": 1, "tercero": 2}.get(ordinal.group(1).lower())
        for turn in reversed(turns):
            if turn.get("role") != "assistant":
                continue
            items = re.findall(r"(?m)^\s*(?:[-*]|\d+[.)])\s+(.+?)\s*$", turn["content"])
            if index is not None and len(items) > index:
                return ReferenceResolution("unique", (items[index][:180],))
        return ReferenceResolution("missing")

    substantive = [
        t["content"].strip()
        for t in reversed(turns)
        if len(t["content"].split()) >= 4
    ]
    if not substantive:
        return ReferenceResolution("missing")
    if len(substantive) == 1:
        return ReferenceResolution("unique", (substantive[0][:180],))
    if explicit_deictic is None:
        return ReferenceResolution("unique", (substantive[0][:180],))
    first_words = set(re.findall(r"\w+", substantive[0].lower()))
    second_words = set(re.findall(r"\w+", substantive[1].lower()))
    overlap = len(first_words & second_words) / max(1, len(first_words | second_words))
    if overlap >= 0.35:
        return ReferenceResolution("unique", (substantive[0][:180],))
    return ReferenceResolution("ambiguous", tuple(item[:180] for item in substantive[:2]))

# Common student spelling errors & typos in computer systems / programming
_TYPO_CORRECTIONS: Dict[re.Pattern, str] = {
    re.compile(r"\bpunter\b", re.IGNORECASE): "puntero",
    re.compile(r"\bsincronisaci[oó]n\b", re.IGNORECASE): "sincronización",
    re.compile(r"\bsemaforo\b", re.IGNORECASE): "semáforo",
    re.compile(r"\bsemaforos\b", re.IGNORECASE): "semáforos",
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
        re.compile(r"(?:la\s+flechita|el\s+operador\s+flecha)(?:\s+en\s+c)?", re.IGNORECASE),
        "operador de acceso a miembros por puntero desreferenciación flecha estructuras struct",
    ),
    (
        re.compile(r"(?:el\s+asterisco|el\s+cosito)(?:\s+adelante\s+de\s+(?:un\s+)?puntero)?|\basterisco\b", re.IGNORECASE),
        "operador de desreferenciación indirección punteros * valor apuntado",
    ),
    (
        re.compile(r"\b(?:el\s+)?(?:ampersand|s[ií]mbolo\s+&|operador\s+&)\b", re.IGNORECASE),
        "operador de dirección ampersand & obtención de dirección de memoria punteros",
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
    # Identificadores técnicos y llamadas al sistema (Fase 5 / Hotfix v1.2.1)
    (
        re.compile(r"\bpthread_mutex_lock\b", re.IGNORECASE),
        "mutex lock cerrojo exclusión mutua sincronización",
    ),
    (
        re.compile(r"\breg_rsp\b", re.IGNORECASE),
        "registro rsp stack pointer marco de pila",
    ),
    (
        re.compile(r"\breg_rbp\b", re.IGNORECASE),
        "registro rbp base pointer marco de pila",
    ),
    (
        re.compile(r"\breg_rip\b", re.IGNORECASE),
        "registro rip instruction pointer contador de programa",
    ),
    (
        re.compile(r"\breg_rdi_rsi\b", re.IGNORECASE),
        "registros rdi rsi paso de argumentos ABI System V",
    ),
    (
        re.compile(r"\bsyscall_instruction\b", re.IGNORECASE),
        "instrucción syscall llamada al sistema paso usuario kernel",
    ),
    (
        re.compile(r"\bstruct_dirent\b", re.IGNORECASE),
        "directorio archivos entradas inodo sistema de archivos",
    ),
    (
        re.compile(r"\bselect_poll_epoll\b", re.IGNORECASE),
        "multiplexación de entrada salida select poll epoll descriptores",
    ),
    (
        re.compile(r"\bbrk_sbrk\b", re.IGNORECASE),
        "llamada brk sbrk asignación memoria dinámica heap",
    ),
    (
        re.compile(r"\bsetjmp_longjmp\b", re.IGNORECASE),
        "funciones setjmp longjmp saltos no locales registros stack",
    ),
    (
        re.compile(r"\bsigaction\b", re.IGNORECASE),
        "señales signal struct sigaction manejador handler proceso",
    ),
    (
        re.compile(r"\bwaitpid\b", re.IGNORECASE),
        "espera de procesos wait waitpid procesos zombis terminación",
    ),
    (
        re.compile(r"\bvalgrind\s+memcheck\b", re.IGNORECASE),
        "detección de fugas de memoria memory leak herramientas análisis dinámico",
    ),
    (
        re.compile(r"\baddresssanitizer\b", re.IGNORECASE),
        "detección de accesos inválidos memoria asan compilador",
    ),
]


# Canonical singular -> plural inflection mappings for short technical terms (<5 chars or specific inflection needs).
# Empirically validated against the corpus (hits(plural) > 0 and hits(singular) <= hits(plural)).
_CANONICAL_INFLECTIONS: Dict[str, str] = {
    "pila": "pilas",
    "grafo": "grafos",
    "hilo": "hilos",
    "nodo": "nodos",
}

_INFLECTION_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(rf"\b{re.escape(sing)}\b", re.IGNORECASE), plur)
    for sing, plur in _CANONICAL_INFLECTIONS.items()
]


class QueryRewriter:
    """Expands student queries into canonical academic vocabulary for hybrid retrieval."""

    def __init__(self, use_llm_fallback: bool = False) -> None:
        self.use_llm_fallback = use_llm_fallback

    def rewrite(self, query: str) -> str:
        """Rewrite and expand query deterministically in < 0.1ms.
        
        Strict transformation order (C2):
        1. _TYPO_CORRECTIONS (basic normalization)
        2. _CANONICAL_INFLECTIONS (substitutive replacement)
        3. _COLLOQUIAL_EXPANSIONS (additive, strictly idempotent expansion)
        """
        q = (query or "").strip()
        if not q or len(q) < 4:
            return q

        # Stage 1: Apply typo corrections (basic normalization)
        clean = q
        for pat, replacement in _TYPO_CORRECTIONS.items():
            clean = pat.sub(replacement, clean)

        # Stage 2: Apply canonical inflections (substitutive replacement with word boundary \b)
        for pat, replacement in _INFLECTION_PATTERNS:
            clean = pat.sub(replacement, clean)

        # Stage 3: Check for colloquial expansions (additive, strictly idempotent)
        tokens_in_clean = set(re.findall(r"\w+", clean.lower()))
        expansions: List[str] = []
        for pat, canonical_terms in _COLLOQUIAL_EXPANSIONS:
            if pat.search(clean):
                substantive = [w for w in re.findall(r"\w+", canonical_terms.lower()) if len(w) > 2]
                if not all(w in tokens_in_clean for w in substantive):
                    expansions.append(canonical_terms)
                    tokens_in_clean.update(substantive)

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

    def rewrite_contextual(
        self,
        query: str,
        recent_turns: Optional[List[Dict[str, str]]] = None,
        llm_backend: Optional[Any] = None,
    ) -> str:
        """Condense a multi-turn contextual/deictic query into a standalone canonical search query."""
        base_query = self.rewrite(query)
        if not should_rewrite_contextual(query, recent_turns):
            return base_query

        turns = recent_turns or []

        # 1. Extraer el contexto sustantivo de turnos previos
        substantive_tokens: List[str] = []
        user_prompts: List[str] = []
        for t in reversed(turns):
            content = (t.get("content") or "").strip()
            if not content:
                continue
            if t.get("role") == "user":
                if not has_deictic_markers(content) and len(content.split()) >= 3:
                    user_prompts.append(content)
            elif t.get("role") == "assistant":
                tech_words = re.findall(
                    r"\b(?:swap|punteros?|memoria|stack|heap|direcci[oó]n|funci[oó]n|registros?|rdi|rsi|rsp|rbp|valor|referencia|sem[aá]foros?|mutex|hilos?|threads?|procesos?|tuber[ií]as?|pipes?|sockets?|inodos?|inodes?|mmu|paginaci[oó]n|segmentos?|deadlocks?|interbloqueos?|schedulers?|planificadores?|despacho|dispatch|contexto|pcb|fork|exec|wait|signal|sistemas?|systems?)\b",
                    content,
                    re.IGNORECASE,
                )
                for tw in tech_words:
                    if tw.lower() not in [st.lower() for st in substantive_tokens]:
                        substantive_tokens.append(tw)

        # 2. Si hay LLM backend disponible y configurado para reescritura rápida
        if self.use_llm_fallback and llm_backend is not None and hasattr(llm_backend, "complete"):
            try:
                context_summary = " ".join(user_prompts[:2]) + " " + " ".join(substantive_tokens[:6])
                prompt = (
                    f"Historial técnico previo: {context_summary[:300]}\n"
                    f"Pregunta del estudiante: {query}\n"
                    "Reescribí la pregunta del estudiante en UNA sola consulta técnica de búsqueda (máximo 12 palabras, sin explicaciones):"
                )
                from study_engine.contracts.generation import PromptBundle
                bundle = PromptBundle(system="Sos un optimizador de búsqueda RAG.", user=prompt)
                resp = llm_backend.complete(bundle)
                ans = getattr(resp, "text", str(resp)).strip().strip('"').strip("'")
                if ans and len(ans.split()) >= 2:
                    return self.rewrite(ans)
            except Exception as e:
                logger.debug("LLM query rewrite fallback exception: %s", e)

        # 3. Condensación determinista de alto rendimiento (< 0.1ms)
        context_prefix = ""
        if user_prompts:
            clean_substantive = user_prompts[0]
            sub_words = [w for w in re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_]+", clean_substantive) if len(w) > 2]
            context_prefix = " ".join(sub_words[:8])
        elif substantive_tokens:
            context_prefix = " ".join(substantive_tokens[:6])

        if context_prefix:
            return f"{context_prefix} {base_query}".strip()
        return base_query


_DEICTIC_PATTERNS = [
    re.compile(r"\b(?:ah[ií]|ac[aá]|all[aá]|eso|esto|aquello|lo\s+anterior|lo\s+que\s+dijiste)\b", re.IGNORECASE),
    re.compile(r"\b(?:en\s+ese\s+caso|en\s+esta\s+funci[oó]n|en\s+este\s+c[oó]digo|el\s+coso|ese|esa)\b", re.IGNORECASE),
    re.compile(r"\b(?:c[oó]mo\s+uso|qu[eé]\s+pasa\s+si|y\s+con\s+eso|por\s*qu[eé]\s+ah[ií])\b", re.IGNORECASE),
]


def has_deictic_markers(query: str) -> bool:
    """Return True if query contains deictic, spatial, or contextual markers."""
    q = (query or "").strip()
    return any(p.search(q) for p in _DEICTIC_PATTERNS)


def should_rewrite_contextual(query: str, recent_turns: Optional[List[Dict[str, str]]]) -> bool:
    """Determine if a query requires contextual condensation with prior dialogue turns."""
    if not recent_turns:
        return False
    words = (query or "").split()
    if len(words) < 12 and (has_deictic_markers(query) or len(words) <= 7):
        return True
    return False
