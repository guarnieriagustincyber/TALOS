"""Deterministic lexical and technical entity diagnostics for S4.4.

Enforces HG-S4.4-06:
Lexical diagnostics provide anomaly detection telemetry; they do NOT
constitute semantic proof of truth or falsehood.
"""

import re
from typing import Set, Tuple

from study_engine.audit.contracts import (
    ClaimType,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)


_HEX_PATTERN = re.compile(r"\b0x[0-9a-fA-F]+\b")
_NUMERIC_PATTERN = re.compile(r"\b\d+\b")
_FUNC_PATTERN = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\)")
_IDENTIFIER_PATTERN = re.compile(
    r"\b(?:sys_|pthread_|str|mem)[a-zA-Z0-9_]+\b"
)


class LexicalGuard:
    """Deterministic scanner detecting lexical and symbol anomalies."""

    def diagnose(

        self,
        claim_text: str,
        evidence_text: str,
        claim_type: ClaimType = ClaimType.FACTUAL,
    ) -> LexicalDiagnostics:
        """Analyze lexical overlap and technical entity containment."""
        if not evidence_text.strip() or not claim_text.strip():
            return LexicalDiagnostics(
                status=LexicalAnomalyStatus.INCONCLUSIVE,
                token_overlap_ratio=0.0,
            )

        claim_tokens = self._tokenize(claim_text)
        evidence_tokens = self._tokenize(evidence_text)

        # 1. Overlap ratio
        if not claim_tokens:
            overlap_ratio = 0.0
        else:
            intersection = claim_tokens.intersection(evidence_tokens)
            overlap_ratio = len(intersection) / len(claim_tokens)

        # 2. Extract technical entities from claim
        claim_entities = self._extract_technical_entities(claim_text)

        # 3. Check containment in evidence text
        evidence_lower = evidence_text.lower()
        found = []
        missing = []

        for entity in claim_entities:
            # Check presence verbatim or normalized
            clean_entity = entity.strip().rstrip("()").lower()
            if clean_entity in evidence_lower:
                found.append(entity)
            else:
                missing.append(entity)

        # 4. Extract numeric constants
        claim_nums = set(_NUMERIC_PATTERN.findall(claim_text))
        evidence_nums = set(_NUMERIC_PATTERN.findall(evidence_text))
        numeric_matches = tuple(sorted(claim_nums.intersection(evidence_nums)))

        # 5. Determine diagnostic status (telemetry, not semantic truth)
        if claim_type in (ClaimType.CONVERSATIONAL, ClaimType.QUESTION):
            status = LexicalAnomalyStatus.NO_ANOMALY
        elif missing:
            # Missing code identifiers, hex addresses, or syscalls
            status = LexicalAnomalyStatus.LEXICAL_ANOMALY

        elif overlap_ratio < 0.15 and len(claim_tokens) >= 5:
            status = LexicalAnomalyStatus.LEXICAL_ANOMALY
        elif len(claim_tokens) < 3:
            status = LexicalAnomalyStatus.INCONCLUSIVE
        else:
            status = LexicalAnomalyStatus.NO_ANOMALY

        return LexicalDiagnostics(
            status=status,
            token_overlap_ratio=round(overlap_ratio, 4),
            technical_entities_found=tuple(sorted(found)),
            technical_entities_missing=tuple(sorted(missing)),
            numeric_matches=numeric_matches,
        )

    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into lowercase alphanumeric words of length >= 3."""
        words = re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())
        return set(words)

    def _extract_technical_entities(self, text: str) -> Tuple[str, ...]:
        """Extract code identifiers, syscalls, and hex addresses."""
        entities = set()
        for match in _HEX_PATTERN.finditer(text):
            entities.add(match.group(0))
        for match in _FUNC_PATTERN.finditer(text):
            entities.add(match.group(0).strip())
        for match in _IDENTIFIER_PATTERN.finditer(text):
            entities.add(match.group(0))
        return tuple(sorted(entities))
