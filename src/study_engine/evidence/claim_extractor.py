"""Deterministic Claim Extractor for Phase E2 (Zero-LLM Pipeline).

Decomposes generated answers into atomic, verifiable claims with strict H1 typing:
- FORMAL_COMPLEXITY: Asymptotic Big-O relations and runtime/space bounds.
- FORMAL_ARITHMETIC: Pointer offsets, byte sizes, address calculations.
- FACTUAL_TEXTUAL: Concrete factual statements grounded in evidence chunks.
- PEDAGOGICAL: Metaphors, teaching analogies (exempt from literal token grounding).
- CONVERSATIONAL: Greetings, pleasantries, sign-offs (exempt from gating).

Also extracts citation anchors ([E#]) and determines claim criticality.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """Canonical claim types specified in Amendment H1."""
    FORMAL_COMPLEXITY = "FORMAL_COMPLEXITY"
    FORMAL_ARITHMETIC = "FORMAL_ARITHMETIC"
    FACTUAL_TEXTUAL = "FACTUAL_TEXTUAL"
    PEDAGOGICAL = "PEDAGOGICAL"
    CONVERSATIONAL = "CONVERSATIONAL"


class ClaimCriticality(str, Enum):
    """Criticality level for dual UCR gating (Amendment H2)."""
    CRITICAL = "CRITICAL"
    NON_CRITICAL = "NON_CRITICAL"


class ExtractedClaim(BaseModel):
    """Atomic claim extracted deterministically from generated response."""
    claim_id: str
    text: str
    claim_type: ClaimType
    criticality: ClaimCriticality
    cited_evidence_indices: List[str] = Field(default_factory=list)
    formal_parameters: Optional[Dict[str, Any]] = None
    is_pedagogical_analogy: bool = False
    source_language: str = "es"


# Abbreviations and tokens to protect during sentence segmentation
PROTECTED_ABBREVIATIONS = [
    r"e\.g\.",
    r"i\.e\.",
    r"vs\.",
    r"Fig\.",
    r"Dr\.",
    r"p\.ej\.",
    r"n[úu]m\.",
    r"art\.",
    r"etc\.",
    r"approx\.",
    r"dept\.",
    r"v[oó]l\.",
]

# Patterns indicating conversational statements
CONVERSATIONAL_PATTERNS = [
    r"^\s*(?:hola|buenos d[íi]as|buenas tardes|saludos|bienvenido|¡hola)",
    r"^\s*(?:welcome|hello|hi|good morning|greetings)",
    r"(?:espero que|que tengas|un saludo cordial)",
    r"(?:let me know|feel free|hope this helps|happy to help|if you have any other questions)",
    r"(?:si tienes m[áa]s dudas|no dudes en consultar|estoy para ayudarte)",
]

# Patterns indicating pedagogical analogies and metaphors
PEDAGOGICAL_PATTERNS = [
    r"(?:podemos (?:imaginar|ver|pensar)|imagina(?:te)? que)",
    r"(?:como (?:una hilera de|un casillero|una pila de platos|un director de orquesta|un sem[áa]foro de|un escritorio|un cajero))",
    r"(?:funciona como|opera como|act[úu]a como|se comporta como)",
    r"(?:is like a|can be envisioned as|think of .* as|acts like a|behaves like a)",
    r"(?:met[áa]fora|analog[íi]a|pedag[óo]gic)",
]

# Patterns for formal complexity
BIG_O_PATTERNS = [
    r"\b(?:O|Θ|θ|Ω|omega|theta)\s*\([^\)]+\)",
    r"\bcomplejidad (?:temporal|espacial|asint[óo]tica)\b",
    r"\b(?:time|space|asymptotic) complexity\b",
    r"\b(?:peor|mejor|promedio) caso\b",
    r"\b(?:worst|best|average)-case\b",
]

# Patterns for pointer arithmetic and addresses
ARITHMETIC_POINTER_PATTERNS = [
    r"\b0x[0-9a-fA-F]+\b",
    r"(?:direcci[óo]n|posici[óo]n|address).*?\b[0-9]{4,}\b",
    r"\b(?:base_address|direcci[óo]n base|puntero base)\b",
    r"\b\*(?:ptr|\w+)\s*\+\s*\d+\b",
    r"\bsizeof\b",
    r"\b(?:desplazamiento|offset)\b",
]

# High criticality keywords
CRITICAL_TOPIC_PATTERNS = [
    r"\b(?:pcb|bloque de control|context switch|cambio de contexto|proceso|procesos|process|processes|hilo|hilos|thread|threads)\b",
    r"\b(?:paginaci[óo]n|paging|tlb|marco de p[áa]gina|page frame|memoria virtual|virtual memory|segmentaci[óo]n|page fault|fallo de p[áa]gina)\b",
    r"\b(?:exclusi[óo]n mutua|mutual exclusion|mutex|sem[áa]foro|semaphore|coffman|deadlock|interbloqueo|2pl|two-phase locking|cas|compare-and-swap|aba problem)\b",
    r"\b(?:buffer overflow|desbordamiento de b[úu]fer|rsa|inyecci[óo]n sql|sql injection)\b",
    r"\b(?:handshake|tres v[íi]as|three-way|congestion control|control de flujo|tcp|udp)\b",
    r"\b(?:dijkstra|quicksort|mergesort|avl|heap|bst|[áa]rbol binario|binary search tree|grafo|hash table|tabla hash|stack|call stack|pila)\b",
    r"\b(?:cpu|registro|registros|register|registers|branch prediction|interrupci[óo]n|interrupciones|interrupt|interrupts|kernel|cach[ée]|cache|mode bit)\b",
    r"\b(?:ram|dram|sram|random access memory|memoria principal|main memory|nvme|ssd)\b",
]


class DeterministicClaimExtractor:
    """Zero-LLM deterministic sentence and clause segmenter for response verification."""

    def __init__(self, default_language: str = "es") -> None:
        self.default_language = default_language

    def segment_sentences(self, text: str) -> List[str]:
        """Split text into sentences while protecting abbreviations, equations, and citations."""
        # 1. Normalize line breaks and spaces
        cleaned = text.strip()
        if not cleaned:
            return []

        # 2. Replace protected abbreviations with placeholders
        placeholders: Dict[str, str] = {}
        for idx, pattern in enumerate(PROTECTED_ABBREVIATIONS):
            matches = list(re.finditer(pattern, cleaned, re.IGNORECASE))
            for m in matches:
                ph = f"__ABBR_{idx}_{m.start()}__"
                placeholders[ph] = m.group(0)
                cleaned = cleaned[:m.start()] + ph + cleaned[m.end():]

        # Also protect decimals like 3.14
        decimal_matches = list(re.finditer(r"\b\d+\.\d+\b", cleaned))
        for idx, m in enumerate(decimal_matches):
            ph = f"__DEC_{idx}__"
            placeholders[ph] = m.group(0)
            cleaned = cleaned[:m.start()] + ph + cleaned[m.end():]

        # 3. Split by sentence terminators: (. | ? | ! | \n+) followed by space or end
        raw_segments = re.split(r"(?:[\.\?\!]\s+|\n+)", cleaned)

        # 4. Restore placeholders and clean
        sentences: List[str] = []
        for seg in raw_segments:
            s = seg.strip()
            # Restore
            for ph, original in placeholders.items():
                s = s.replace(ph, original)
            
            # Clean list bullets / numbering: "1.", "2. ", "* ", "- "
            s = re.sub(r"^(?:\d+[\.\)]\s*|[\*\-]\s*)", "", s).strip()
            
            # Filter empty or too short segments (< 3 words)
            if s and len(s.split()) >= 3:
                sentences.append(s)

        return sentences

    def extract_citations(self, text: str) -> Tuple[str, List[str]]:
        """Extract citations like [E1], [E2], [E1, E2] and return (clean_text, citations)."""
        citations: List[str] = []
        
        def _cite_repl(match: re.Match) -> str:
            raw = match.group(1)
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            for p in parts:
                if p not in citations:
                    citations.append(p)
            return ""

        clean_text = re.sub(r"\[([E|e]\d+(?:\s*,\s*[E|e]\d+)*)\]", _cite_repl, text).strip()
        # Clean double spaces
        clean_text = re.sub(r"\s+", " ", clean_text)
        return clean_text, citations

    def detect_language(self, text: str) -> str:
        """Heuristic language detection between Spanish and English."""
        t_lower = text.lower()
        es_markers = [" el ", " la ", " de ", " en ", " y ", " que ", " los ", " las ", " por ", " un ", " una ", " es "]
        en_markers = [" the ", " of ", " in ", " and ", " that ", " to ", " a ", " is ", " for ", " with ", " as "]
        
        padded = f" {t_lower} "
        es_score = sum(1 for m in es_markers if m in padded)
        en_score = sum(1 for m in en_markers if m in padded)
        
        if es_score > en_score:
            return "es"
        elif en_score > es_score:
            return "en"
        return self.default_language

    def classify_claim(self, text: str) -> Tuple[ClaimType, ClaimCriticality, bool, Optional[Dict[str, Any]]]:
        """Classify claim into ClaimType, Criticality, pedagogical flag, and formal params."""
        t_lower = text.lower()

        # 1. Check CONVERSATIONAL
        for pat in CONVERSATIONAL_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return ClaimType.CONVERSATIONAL, ClaimCriticality.NON_CRITICAL, False, None

        # 2. Check PEDAGOGICAL
        for pat in PEDAGOGICAL_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return ClaimType.PEDAGOGICAL, ClaimCriticality.NON_CRITICAL, True, None

        # 3. Check FORMAL_COMPLEXITY
        is_complexity = any(re.search(pat, text, re.IGNORECASE) for pat in BIG_O_PATTERNS)
        if is_complexity:
            # Extract Big-O expression if present
            big_o_match = re.search(r"\b(?:O|Θ|θ|Ω)\s*\(([^\)]+)\)", text)
            params = {}
            if big_o_match:
                params["complexity"] = f"o({big_o_match.group(1).strip()})"
            return ClaimType.FORMAL_COMPLEXITY, ClaimCriticality.CRITICAL, False, params

        # 4. Check FORMAL_ARITHMETIC
        is_arithmetic = any(re.search(pat, text, re.IGNORECASE) for pat in ARITHMETIC_POINTER_PATTERNS)
        if is_arithmetic:
            # Extract numeric parameters if present
            params = {}
            hex_match = re.search(r"\b0x[0-9a-fA-F]+\b", text)
            if hex_match:
                params["hex_address"] = hex_match.group(0)
            return ClaimType.FORMAL_ARITHMETIC, ClaimCriticality.CRITICAL, False, params

        # 5. FACTUAL_TEXTUAL
        # Determine criticality
        is_critical = any(re.search(pat, text, re.IGNORECASE) for pat in CRITICAL_TOPIC_PATTERNS)
        criticality = ClaimCriticality.CRITICAL if is_critical else ClaimCriticality.NON_CRITICAL

        return ClaimType.FACTUAL_TEXTUAL, criticality, False, None

    def extract_claims(self, text: str, claim_prefix: str = "CLM") -> List[ExtractedClaim]:
        """Segment and classify all atomic claims in response text."""
        sentences = self.segment_sentences(text)
        claims: List[ExtractedClaim] = []

        for idx, sentence in enumerate(sentences, start=1):
            clean_text, citations = self.extract_citations(sentence)
            if not clean_text:
                continue

            lang = self.detect_language(clean_text)
            claim_type, criticality, is_pedagogical, formal_params = self.classify_claim(clean_text)

            claims.append(
                ExtractedClaim(
                    claim_id=f"{claim_prefix}-{idx:03d}",
                    text=clean_text,
                    claim_type=claim_type,
                    criticality=criticality,
                    cited_evidence_indices=citations,
                    formal_parameters=formal_params,
                    is_pedagogical_analogy=is_pedagogical,
                    source_language=lang,
                )
            )

        return claims
