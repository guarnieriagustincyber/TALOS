"""Deterministic Reference Extractor (Slice 6.0.5, Punto 1).

Pure, rule-based extraction of curricular content references (exercises, sections)
from student queries WITHOUT invoking any LLM.

Two-layer resolution architecture:
- Layer A (Literal): Deterministic canonical regexes with digit & source capture
  -> content_id exact resolution with confidence=1.0.
- Layer B (Curated Fuzzy): Deterministic string similarity over known canonical items:
  * score >= 0.95: Direct resolution (confidence = score, status = ok).
  * 0.70 <= score < 0.95: Ambiguous match -> candidates list + status = needs_review.
  * score < 0.70: No match (confidence < 0.70).

HARD INVARIANT: ReferenceResult NEVER assumes a content_id below the hard 0.95 threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import difflib
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from study_engine.contracts.content_registry import ContentStatus, UnitType


@dataclass
class ReferenceResult:
    """Outcome of reference extraction from a user query."""
    matched: bool
    content_id: Optional[str] = None
    unit_type: Optional[UnitType] = None
    source_hint: Optional[str] = None
    identifier: Optional[str] = None
    confidence: float = 0.0
    status: ContentStatus = ContentStatus.OK
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    raw_query: str = ""
    raw_ref: Optional[str] = None


# Common source aliases mapping to canonical prefixes
SOURCE_ALIASES = {
    "guia": "guia",
    "guía": "guia",
    "tp": "guia",
    "practica": "guia",
    "práctica": "guia",
    "joyanes": "joyanes",
    "tanenbaum": "tanenbaum",
    "silberschatz": "silberschatz",
    "deitel": "deitel",
    "kernighan": "kr",
    "k&r": "kr",
    "kr": "kr",
    "stallings": "stallings",
    "fadena": "fadena",
}

# Regex for Layer A literal extraction
_RE_EXERCISE_PATTERNS = [
    # "guia 4 ejercicio 3", "guía 4 ej 3", "guia4:ej3", "guia 4, problema 3"
    re.compile(
        r"(?:gu[ií]a|tp|pr[aá]ctica)\s*(\d+)[,:\s]+(?:ejercicio|ej|problema|item|actividad)\s*([0-9]+[a-zA-Z]?(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
    # "ejercicio 3 de la guia 4", "problema 2 de guia 1"
    re.compile(
        r"(?:ejercicio|ej|problema|item|actividad)\s*([0-9]+[a-zA-Z]?(?:\.[0-9]+)?)\s+(?:de\s+(?:la\s+)?)?(?:gu[ií]a|tp|pr[aá]ctica)\s*(\d+)",
        re.IGNORECASE,
    ),
    # "guia 4 - ej 3" or "guia 4 : 3"
    re.compile(
        r"(?:gu[ií]a|tp|pr[aá]ctica)\s*(\d+)\s*[-:]\s*(?:ej(?:ercicio)?\s*)?([0-9]+[a-zA-Z]?(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
]

_RE_SECTION_PATTERNS = [
    # "seccion 3.1.2 de joyanes", "capitulo 4 de tanenbaum"
    re.compile(
        r"(?:secci[oó]n|sec|cap[ií]tulo|cap)\s*([0-9]+(?:\.[0-9]+)*)\s+(?:de\s+)?([a-zA-Z&]+)",
        re.IGNORECASE,
    ),
    # "joyanes seccion 3.1.2", "joyanes capitulo 4", "joyanes 3.1.2"
    re.compile(
        r"([a-zA-Z&]+)\s+(?:secci[oó]n|sec|cap[ií]tulo|cap)?\s*([0-9]+(?:\.[0-9]+)+)",
        re.IGNORECASE,
    ),
]

# Standalone patterns (exercise without source specified)
_RE_STANDALONE_EXERCISE = re.compile(
    r"\b(?:ejercicio|ej|problema)\s*([0-9]+[a-zA-Z]?(?:\.[0-9]+)?)\b",
    re.IGNORECASE,
)
_RE_STANDALONE_SECTION = re.compile(
    r"\b(?:secci[oó]n|sec)\s*([0-9]+(?:\.[0-9]+)+)\b",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    """Normalize text by lowercasing and removing accents."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _build_canonical_id(source_key: str, unit_type: UnitType, identifier: str) -> str:
    """Construct canonical content_id string."""
    norm_source = source_key.lower().replace(" ", "_")
    norm_id = identifier.lower().replace(" ", "_")
    if unit_type == UnitType.EXERCISE:
        return f"{norm_source}:ej_{norm_id}"
    return f"{norm_source}:sec_{norm_id}"


def extract_reference(
    query: str,
    known_content_ids: Optional[List[str]] = None,
) -> ReferenceResult:
    """Deterministically extracts a curricular content reference from a query.

    Args:
        query: Student raw input query.
        known_content_ids: Optional catalog of active content_ids in the notebook/registry.

    Returns:
        ReferenceResult indicating match status, content_id, and confidence.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return ReferenceResult(matched=False, raw_query=query)

    # -------------------------------------------------------------
    # CAPA A: Coincidencia Literal Determinista (Confidence = 1.0)
    # -------------------------------------------------------------

    # 1. Ejercicios con Guía y Número
    for pattern in _RE_EXERCISE_PATTERNS:
        match = pattern.search(cleaned_query)
        if match:
            # Pattern 1 & 3: (guide_num, exercise_num)
            # Pattern 2: (exercise_num, guide_num)
            groups = match.groups()
            if pattern == _RE_EXERCISE_PATTERNS[1]:
                ex_num, guide_num = groups[0], groups[1]
            else:
                guide_num, ex_num = groups[0], groups[1]

            canonical_source = f"guia_{guide_num}"
            canonical_id = f"guia_{guide_num}:ej_{ex_num}"
            return ReferenceResult(
                matched=True,
                content_id=canonical_id,
                unit_type=UnitType.EXERCISE,
                source_hint=canonical_source,
                identifier=f"ej_{ex_num}",
                confidence=1.0,
                status=ContentStatus.OK,
                raw_query=query,
                raw_ref=match.group(0).strip(),
            )

    # 2. Secciones con Fuente y Número
    for pattern in _RE_SECTION_PATTERNS:
        match = pattern.search(cleaned_query)
        if match:
            groups = match.groups()
            if pattern == _RE_SECTION_PATTERNS[0]:
                sec_num, raw_source = groups[0], groups[1]
            else:
                raw_source, sec_num = groups[0], groups[1]

            norm_src = _normalize_text(raw_source)
            mapped_src = SOURCE_ALIASES.get(norm_src, norm_src)
            canonical_id = f"{mapped_src}:sec_{sec_num}"
            return ReferenceResult(
                matched=True,
                content_id=canonical_id,
                unit_type=UnitType.SECTION,
                source_hint=mapped_src,
                identifier=f"sec_{sec_num}",
                confidence=1.0,
                status=ContentStatus.OK,
                raw_query=query,
                raw_ref=match.group(0).strip(),
            )

    # -------------------------------------------------------------
    # CAPA B: Coincidencia Difusa Curada (Score >= 0.95 / 0.70 - 0.95)
    # -------------------------------------------------------------
    if known_content_ids:
        norm_q = _normalize_text(cleaned_query)
        scored_candidates: List[Tuple[float, str]] = []

        for cid in known_content_ids:
            # Normalize cid into human-like forms for comparison
            # e.g., "guia_4:ej_3" -> "guia 4 ej 3", "guia 4 ejercicio 3"
            parts = cid.replace(":", " ").replace("_", " ")
            norm_cid = _normalize_text(parts)

            # Check similarity on both the full string and matching token patterns
            matcher = difflib.SequenceMatcher(None, norm_q, norm_cid)
            score = matcher.ratio()

            # Also check if query contains the token components
            cid_tokens = set(norm_cid.split())
            q_tokens = set(norm_q.split())
            if cid_tokens and cid_tokens.issubset(q_tokens):
                score = max(score, 0.96)

            scored_candidates.append((score, cid))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        if scored_candidates:
            best_score, best_cid = scored_candidates[0]

            # Umbral duro >= 0.95 -> Direct Resolution
            if best_score >= 0.95:
                u_type = UnitType.EXERCISE if ":ej_" in best_cid else UnitType.SECTION
                return ReferenceResult(
                    matched=True,
                    content_id=best_cid,
                    unit_type=u_type,
                    source_hint=best_cid.split(":")[0] if ":" in best_cid else None,
                    identifier=best_cid.split(":")[1] if ":" in best_cid else None,
                    confidence=round(best_score, 4),
                    status=ContentStatus.OK,
                    candidates=[{"content_id": c[1], "score": round(c[0], 4)} for c in scored_candidates[:3]],
                    raw_query=query,
                    raw_ref=cleaned_query,
                )

            # Umbral ambiguo 0.70 <= score < 0.95 -> Candidates + needs_review (no direct resolution)
            if best_score >= 0.70:
                review_candidates = [
                    {"content_id": c[1], "score": round(c[0], 4)}
                    for c in scored_candidates
                    if c[0] >= 0.70
                ][:5]
                u_type = UnitType.EXERCISE if ":ej_" in best_cid else UnitType.SECTION
                return ReferenceResult(
                    matched=True,
                    content_id=None,  # NEVER assume direct content_id below 0.95
                    unit_type=u_type,
                    source_hint=best_cid.split(":")[0] if ":" in best_cid else None,
                    identifier=best_cid.split(":")[1] if ":" in best_cid else None,
                    confidence=round(best_score, 4),
                    status=ContentStatus.NEEDS_REVIEW,
                    candidates=review_candidates,
                    raw_query=query,
                    raw_ref=cleaned_query,
                )

    # -------------------------------------------------------------
    # CAPA C: Fallback para queries sin fuentes explícitas (< 0.70)
    # -------------------------------------------------------------
    standalone_ex = _RE_STANDALONE_EXERCISE.search(cleaned_query)
    if standalone_ex:
        ex_num = standalone_ex.group(1)
        return ReferenceResult(
            matched=True,
            content_id=None,
            unit_type=UnitType.EXERCISE,
            source_hint=None,
            identifier=f"ej_{ex_num}",
            confidence=0.50,
            status=ContentStatus.NEEDS_REVIEW,
            raw_query=query,
            raw_ref=standalone_ex.group(0).strip(),
        )

    standalone_sec = _RE_STANDALONE_SECTION.search(cleaned_query)
    if standalone_sec:
        sec_num = standalone_sec.group(1)
        return ReferenceResult(
            matched=True,
            content_id=None,
            unit_type=UnitType.SECTION,
            source_hint=None,
            identifier=f"sec_{sec_num}",
            confidence=0.50,
            status=ContentStatus.NEEDS_REVIEW,
            raw_query=query,
            raw_ref=standalone_sec.group(0).strip(),
        )

    return ReferenceResult(matched=False, raw_query=query)
