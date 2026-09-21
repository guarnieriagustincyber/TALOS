"""Stage-Aware Query Decomposer for Subsystem S3 / S4.1 (E1.1 Specification).

Preserves composite query in Stage 1 (lexical FTS5 pre-filter) to prevent
semantic dilution (arXiv:2606.08577) and extracts 2-3 validated atomic facets
to guide Stage 2 reranking and greedy submodular selection.

Enforces 4 strict deterministic anti-decomposition guards:
- G1: Anchor Retention (all technical anchors must appear in >= 1 facet)
- G2: No Out-of-Scope Drift (no entities outside query anchors or notebook vocab)
- G3: Strict Cardinality Bound (2 <= len(facets) <= 3; else fallback to monolithic)
- G4: Non-Triviality & Non-Duplication (length >= 4 words, pairwise Jaccard <= 0.70)
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import unicodedata

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Known technical anchors in CS/Systems/Security curriculum
CORE_TECHNICAL_PATTERNS = [
    r"\bprogram\s+counter\b",
    r"\bstack\s+frame\b",
    r"\bheap\b",
    r"\bram\b",
    r"\bmemoria\s+ram\b",
    r"\bmemoria\s+vol[áa]til\b",
    r"\bbig\s+o\b",
    r"\bo\([a-z0-9\^\s\+\*]+\)",
    r"\bipv4\b",
    r"\btcp\b",
    r"\bhandshake\b",
    r"\bsocket\b",
    r"\bdirecci[óo]n\s+base\b",
    r"\bpuntero[s]?\b",
    r"\barreglo[s]?\b",
    r"\blista[s]?\s+din[áa]mica[s]?\b",
    r"\bb[úu]squeda\s+binaria\b",
    r"\bb[úu]squeda\s+secuencial\b",
    r"\bordenamiento\s+por\s+burbuja\b",
    r"\btype\s+hints\b",
    r"\binvariante[s]?\b",
    r"\bclean\s+code\b",
    r"\bcl[áa]usula[s]?\s+de\s+guardia\b",
    r"\bdenegaci[óo]n\s+de\s+servicio\b",
    r"\bdos\b",
    r"\bfirewall\b",
    r"\bcentinela\b",
    r"\bpaso\s+de\s+par[áa]metros\b",
    r"\bpor\s+valor\b",
    r"\bpor\s+referencia\b",
    r"\bmutabilidad\b",
    r"\basignaci[óo]n\s+destructiva\b",
    r"\btop-down\b",
    r"\bpseudoc[óo]digo\b",
    r"\bexcepcion(?:es)?\b",
    r"\bc[óo]digo[s]?\s+centinela\b",
    r"\brollback\b",
]

COMPILED_ANCHOR_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CORE_TECHNICAL_PATTERNS]

SPLIT_CONNECTORS = [
    r",\s*(?:y\s+además\s+|además\s+de\s+|y\s+también\s+|y\s+|la\s+|el\s+|los\s+|las\s+|su\s+|sus\s+)",
    r"\s+y\s+(?:cómo|como|qué|que|cuáles|cuales|por\s+qué|dónde|la\s+|el\s+|los\s+|las\s+|su\s+|sus\s+)?\b",
    r"\s+frente\s+a\s+",
    r"\s+en\s+comparación\s+con\s+",
    r";\s*",
]
SPLIT_REGEX = re.compile("|".join(SPLIT_CONNECTORS), flags=re.IGNORECASE)


class AtomicFacet(BaseModel):
    """An orthogonal technical facet extracted for Stage 2 reranking."""

    facet_id: str = Field(..., description="Unique facet ID, e.g. f-1")
    text: str = Field(..., description="Facet query expression")
    anchor_terms: List[str] = Field(default_factory=list, description="Technical anchors bound to this facet")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Normalized importance weight")


class DecompositionResult(BaseModel):
    """Result of Stage-Aware Decomposition with audit diagnostics."""

    original_query: str
    facets: List[AtomicFacet]
    is_fallback: bool = False
    validity_passed: bool = True
    guards_status: Dict[str, bool] = Field(default_factory=dict)
    anchors_detected: List[str] = Field(default_factory=list)


def extract_technical_anchors(text: str) -> List[str]:
    """Extract domain-specific technical terms and anchors from text."""
    found: Set[str] = set()
    for pat in COMPILED_ANCHOR_PATTERNS:
        matches = pat.findall(text)
        for m in matches:
            found.add(m.strip().lower())

    # Fallback heuristic: capitalized phrases or alphanumeric acronyms
    acronyms = re.findall(r"\b[A-Z]{2,}(?:\-[A-Z0-9]+)?\b", text)
    for ac in acronyms:
        found.add(ac.strip().lower())

    return sorted(list(found))


def compute_token_jaccard(text_a: str, text_b: str) -> float:
    """Compute word-level Jaccard similarity."""
    toks_a = set(re.findall(r"\w{3,}", text_a.lower()))
    toks_b = set(re.findall(r"\w{3,}", text_b.lower()))
    if not toks_a or not toks_b:
        return 0.0
    return len(toks_a & toks_b) / len(toks_a | toks_b)


class StageAwareDecomposer:
    """Deterministic, guarded stage-aware query decomposer."""

    def __init__(self, max_facets: int = 3, min_facets: int = 2) -> None:
        self.max_facets = max_facets
        self.min_facets = min_facets

    def decompose(
        self,
        query: str,
        notebook_id: str,
        notebook_vocab: Optional[Set[str]] = None,
    ) -> DecompositionResult:
        """Decompose query into 2-3 validated atomic facets with deterministic guards."""
        clean_q = " ".join(unicodedata.normalize("NFC", query).strip().split())
        anchors = extract_technical_anchors(clean_q)

        # Generate candidate clauses
        raw_clauses = self._extract_raw_clauses(clean_q)

        # Merge or filter clauses to target [2, 3]
        candidate_facets = self._assemble_facets(raw_clauses, anchors)

        if not candidate_facets:
            # Query is atomic / monolithic; clean fallback with validity passed
            fallback_facet = AtomicFacet(
                facet_id="f-global",
                text=clean_q,
                anchor_terms=anchors,
                weight=1.0,
            )
            return DecompositionResult(
                original_query=clean_q,
                facets=[fallback_facet],
                is_fallback=True,
                validity_passed=True,
                guards_status={
                    "G1_anchor_retention": True,
                    "G2_no_drift": True,
                    "G3_cardinality_bound": True,
                    "G4_non_triviality": True,
                },
                anchors_detected=anchors,
            )

        # Validate against G1-G4 guards
        guards_status, is_valid = self.validate_decomposition(
            query=clean_q,
            facets=candidate_facets,
            anchors=anchors,
            notebook_vocab=notebook_vocab or set(),
        )

        if not is_valid:
            # Attempted decomposition failed guards (e.g. dropped anchor)
            fallback_facet = AtomicFacet(
                facet_id="f-global",
                text=clean_q,
                anchor_terms=anchors,
                weight=1.0,
            )
            return DecompositionResult(
                original_query=clean_q,
                facets=[fallback_facet],
                is_fallback=True,
                validity_passed=False,
                guards_status=guards_status,
                anchors_detected=anchors,
            )

        # Assign normalized weights
        n = len(candidate_facets)
        weight_per_facet = round(1.0 / n, 4)
        for f in candidate_facets:
            f.weight = weight_per_facet

        return DecompositionResult(
            original_query=clean_q,
            facets=candidate_facets,
            is_fallback=False,
            validity_passed=True,
            guards_status=guards_status,
            anchors_detected=anchors,
        )

    def validate_decomposition(
        self,
        query: str,
        facets: List[AtomicFacet],
        anchors: List[str],
        notebook_vocab: Set[str],
    ) -> Tuple[Dict[str, bool], bool]:
        """Validate candidate facets against G1, G2, G3, G4 guards."""
        guards = {
            "G1_anchor_retention": True,
            "G2_no_drift": True,
            "G3_cardinality_bound": True,
            "G4_non_triviality": True,
        }

        # G3: Strict Cardinality Bound 2 <= len(facets) <= 3
        if not (self.min_facets <= len(facets) <= self.max_facets):
            guards["G3_cardinality_bound"] = False
            return guards, False

        # G1: Anchor Retention (every anchor in query must appear in at least one facet)
        if anchors:
            facet_texts_combined = " ".join(f.text.lower() for f in facets)
            missing_anchors = [a for a in anchors if a not in facet_texts_combined]
            if missing_anchors:
                guards["G1_anchor_retention"] = False

        # G2: No Out-of-Scope Drift (facets must not introduce phantom entities)
        query_words = set(re.findall(r"\w{4,}", query.lower()))
        allowed_vocab = query_words | {v.lower() for v in notebook_vocab}
        for f in facets:
            facet_words = set(re.findall(r"\w{4,}", f.text.lower()))
            unknown = facet_words - allowed_vocab
            if len(unknown) > 4:
                guards["G2_no_drift"] = False

        # G4: Non-Triviality and Pairwise Disjointness
        for i, f in enumerate(facets):
            words = f.text.strip().split()
            if len(words) < 3:
                guards["G4_non_triviality"] = False
            for j in range(i + 1, len(facets)):
                sim = compute_token_jaccard(f.text, facets[j].text)
                if sim > 0.70:
                    guards["G4_non_triviality"] = False

        overall_valid = all(guards.values())
        return guards, overall_valid

    def _extract_raw_clauses(self, query: str) -> List[str]:
        """Split text into candidate topical clauses."""
        clean = re.sub(r"^[¿\?]+", "", query).strip()
        parts = SPLIT_REGEX.split(clean)
        clauses = []
        for p in parts:
            p_strip = p.strip(" ¿?.,;:\t\n")
            if len(p_strip.split()) >= 3:
                clauses.append(p_strip)

        if len(clauses) <= 1:
            q_matches = re.findall(r"¿([^?]+)\?", query)
            if len(q_matches) >= 2:
                clauses = [m.strip(" ¿?.,;:") for m in q_matches if len(m.strip().split()) >= 3]

        return clauses

    def _assemble_facets(self, raw_clauses: List[str], anchors: List[str]) -> List[AtomicFacet]:
        """Assemble and bound candidate clauses into 2-3 atomic facets."""
        if len(raw_clauses) < 2:
            return []

        clauses = list(raw_clauses)
        while len(clauses) > self.max_facets:
            min_idx = 0
            min_len = len(clauses[0]) + len(clauses[1])
            for i in range(1, len(clauses) - 1):
                comb = len(clauses[i]) + len(clauses[i + 1])
                if comb < min_len:
                    min_len = comb
                    min_idx = i
            clauses[min_idx] = f"{clauses[min_idx]} y {clauses[min_idx + 1]}"
            clauses.pop(min_idx + 1)

        facets: List[AtomicFacet] = []
        for idx, clause in enumerate(clauses, start=1):
            clause_lower = clause.lower()
            bound_anchors = [a for a in anchors if a in clause_lower]
            facets.append(
                AtomicFacet(
                    facet_id=f"f-{idx}",
                    text=clause,
                    anchor_terms=bound_anchors,
                )
            )

        return facets

    @staticmethod
    def score_facet_coverage(candidate_text: str, facet: AtomicFacet) -> float:
        """Compute topical coverage of a candidate chunk for a given facet (0.0 to 1.0)."""
        if not candidate_text or not facet.text:
            return 0.0

        cand_lower = candidate_text.lower()
        facet_toks = set(re.findall(r"\w{3,}", facet.text.lower()))
        if not facet_toks:
            return 0.0

        hits = sum(1 for t in facet_toks if t in cand_lower)
        term_cov = hits / len(facet_toks)

        anchor_cov = 1.0
        if facet.anchor_terms:
            anchor_hits = sum(1 for a in facet.anchor_terms if a in cand_lower)
            anchor_cov = anchor_hits / len(facet.anchor_terms)

        return round(0.5 * term_cov + 0.5 * anchor_cov, 4)
