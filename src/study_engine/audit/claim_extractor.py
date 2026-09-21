"""Deterministic claim extraction and structural classification for S4.4.

Segments response text into granular claims and maps cited evidence tags [E#]
with structural claim typing (FACTUAL, PEDAGOGICAL, QUESTION, CONVERSATIONAL).
"""

import re
from typing import List, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.audit.contracts import ClaimType


_CITATION_PATTERN = re.compile(r"\[(E[0-9]+)\]")

_CONVERSATIONAL_PATTERNS = [
    re.compile(
        r"^\s*(hola|buenos días|buenas tardes|buenas noches|"
        r"saludos|bienvenidos)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(de nada|un gusto|hasta luego|adiós|éxitos)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(¡?excelente|¡?muy bien|¡?buen trabajo|¡?correcto)\b",
        re.IGNORECASE,
    ),
]


_PEDAGOGICAL_PATTERNS = [

    re.compile(r"^\s*vamos a (analizar|revisar|ver|desglosar)", re.IGNORECASE),
    re.compile(
        r"^\s*a continuación (explicamos|responderé|analizamos)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*considera (lo siguiente|la siguiente pregunta)",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*paso \d+:", re.IGNORECASE),
    re.compile(
        r"(siguientes|siguiente|continuación|razones|motivos|aspectos):\s*$",
        re.IGNORECASE,
    ),
]


class ExtractedClaim(BaseContract):
    """Immutable segmented claim extracted from response text."""

    model_config = ConfigDict(frozen=True)

    claim_index: int = Field(
        ..., ge=0, description="Sequential index of claim"
    )
    claim_text: str = Field(
        ..., min_length=1, description="Claim sentence text"
    )
    claim_type: ClaimType = Field(..., description="Structural classification")
    cited_tags: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Evidence tags [E#] cited in this sentence",
    )


class ClaimExtractor:
    """Deterministic extractor segmenting text and extracting claim-cites."""

    def extract_claims(self, text: str) -> Tuple[ExtractedClaim, ...]:
        """Segment text into claims and extract citations and claim types."""
        cleaned = text.strip()
        if not cleaned:
            return ()

        raw_sentences = self._split_sentences(cleaned)
        claims: List[ExtractedClaim] = []

        for idx, sentence in enumerate(raw_sentences):
            clean_sent = sentence.strip()
            if not clean_sent:
                continue

            cited_tags = self._extract_citations(clean_sent)
            claim_type = self._classify_claim_type(clean_sent)

            claims.append(
                ExtractedClaim(
                    claim_index=idx,
                    claim_text=clean_sent,
                    claim_type=claim_type,
                    cited_tags=cited_tags,
                )
            )

        return tuple(claims)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving technical symbols/numbers."""
        # Normalize double newlines as sentence breaks
        normalized = re.sub(r"\n+", "\n", text)
        # Split on sentence terminals followed by space/newline, or on newlines
        # Lookbehind for terminal punctuation (. ? ! :) or newline,
        # ignoring numbered lists (e.g. 1.)
        splits = re.split(r"(?<!\d\.)(?<=[.?!;])\s+|\n+", normalized)
        # Filter out empty or whitespace segments
        return [s.strip() for s in splits if s.strip()]

    def _extract_citations(self, text: str) -> Tuple[str, ...]:
        """Extract [E#] citations preserving first-seen lexical order."""
        seen = set()
        cites = []
        for block in re.finditer(r"\[([^\]]+)\]", text):
            for match in re.finditer(r"\b(E[0-9]+)\b", block.group(1)):
                tag = match.group(1)
                if tag not in seen:
                    seen.add(tag)
                    cites.append(tag)
        return tuple(cites)

    def _classify_claim_type(self, text: str) -> ClaimType:
        """Classify claim structurally into ClaimType."""
        # 1. Check if question
        if "?" in text or "¿" in text:
            return ClaimType.QUESTION

        # 2. Check conversational phrases
        for pattern in _CONVERSATIONAL_PATTERNS:
            if pattern.search(text):
                return ClaimType.CONVERSATIONAL

        # 3. Check pedagogical framing
        for pattern in _PEDAGOGICAL_PATTERNS:
            if pattern.search(text):
                return ClaimType.PEDAGOGICAL

        # 4. Check colon lead-in framing (introduces subsequent explanation)
        if text.rstrip().endswith(":"):
            return ClaimType.PEDAGOGICAL

        # 5. If substantive assertions
        # A factual claim typically contains substantive words (>2 words)
        words = [w for w in re.split(r"\s+", text) if len(w) > 1]
        if len(words) >= 2:
            return ClaimType.FACTUAL

        return ClaimType.UNCLASSIFIED
