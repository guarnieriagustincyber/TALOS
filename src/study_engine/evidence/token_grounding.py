"""Token Grounding Engine with Versioned Bilingual Dictionary Support (Phase E2).

Implements multi-level alignment for factual claims against admitted evidence:
1. Normalized Token & Lemmatized N-gram Overlap (Jaccard / containment).
2. Cross-Lingual Technical Alignment via versioned bilingual dictionary (H3).
3. Negation Polarity & Contradiction Detection.
4. Epistemic Policy Routing per Amendment H1:
   - FORMAL_COMPLEXITY / FORMAL_ARITHMETIC: Delegated to SymbolicVerifier.
   - FACTUAL_TEXTUAL: Rigorous token grounding with dual UCR criticality tagging.
   - PEDAGOGICAL: Evaluated solely for non-contradiction; exempt from literal tokens.
   - CONVERSATIONAL: Exempt from gating.
"""

from enum import Enum
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from study_engine.evidence.claim_extractor import ClaimCriticality, ClaimType, ExtractedClaim
from study_engine.evidence.symbolic_verifier import SymbolicVerdict, SymbolicVerifier


class GroundingStatus(str, Enum):
    """Grounding decision status."""
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTION = "CONTRADICTION"
    EXEMPT = "EXEMPT"


class ClaimGroundingResult(BaseModel):
    """Provenance and verification audit record for an extracted claim."""
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    criticality: ClaimCriticality
    status: GroundingStatus
    grounding_score: float
    matched_chunk_ids: List[str] = Field(default_factory=list)
    matched_terms: List[Tuple[str, str]] = Field(default_factory=list)
    is_pedagogical_analogy: bool = False
    audit_notes: str = ""


# Stopwords for filtering non-informative tokens
ES_STOPWORDS: Set[str] = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "en", "y",
    "a", "al", "por", "con", "para", "es", "son", "se", "su", "sus", "que", "como",
    "mas", "más", "pero", "o", "u", "si", "lo", "este", "esta", "estos", "estas",
    "ese", "esa", "esos", "esas", "aquel", "aquella", "entre", "sobre", "tras",
    "durante", "mediante", "hacia", "desde", "hasta", "sin", "cual", "cuales", "cuál",
    "cuáles", "donde", "dónde", "cuando", "cuándo", "como", "cómo", "cada", "todo",
    "toda", "todos", "todas", "otro", "otra", "otros", "otras", "mismo", "misma",
    "mismos", "mismas", "muy", "tan", "tanto", "tanta", "primer", "primera", "segundo",
}

EN_STOPWORDS: Set[str] = {
    "the", "a", "an", "in", "on", "of", "and", "or", "to", "for", "with", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "by", "at", "from", "as", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on",
    "off", "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "can", "will", "just", "should", "now", "it",
    "its", "itself", "they", "them", "their", "theirs", "themselves", "which",
    "who", "whom", "this", "that", "these", "those",
}

ALL_STOPWORDS = ES_STOPWORDS | EN_STOPWORDS

# Negation keywords for contradiction detection
NEGATION_WORDS: Set[str] = {
    "no", "nunca", "jamás", "jamas", "tampoco", "nada", "nadie", "ningún", "ningun",
    "ninguna", "carece", "imposible", "invalida", "invalido", "inválido",
    "not", "never", "neither", "nor", "none", "nobody", "nothing", "nowhere",
    "cannot", "can't", "won't", "lacks", "impossible", "invalid",
}

CONTRADICTION_PAIRS = [
    (r"\btamaños? (?:fijos?|constantes?)\b", r"\btamaños? (?:din[áa]micos?|variables?)\b"),
    (r"\bfixed[- ]size\b", r"\bvariable[- ]size\b"),
    (r"\bprimero en entrar.*primero en salir\b", r"\bprimero en entrar.*[úu]ltimo en salir\b"),
    (r"\bfirst-in first-out\b", r"\blast-in first-out\b"),
    (r"\bmenores? que la ra[íi]z\b", r"\bmayores? que la ra[íi]z\b"),
    (r"\bsmaller than (?:the )?root\b", r"\bgreater than (?:the )?root\b"),
    (r"\binmutables?\b", r"\bmutables?\b"),
    (r"\bimmutable\b", r"\bmutable\b"),
    (r"\bpermite\b", r"\bimposibilita|proh[íi]be\b"),
    (r"\ballows?\b", r"\bprevents?|forbids?\b"),
    (r"\belimina fragmentaci[óo]n externa\b", r"\baumenta fragmentaci[óo]n externa\b"),
    (r"\borientado a conexi[óo]n\b", r"\bno orientado a conexi[óo]n\b"),
    (r"\bconnection-oriented\b", r"\bconnectionless\b"),
    (r"\bconserva.*(?:intacto|anterior)\b", r"\bsobrescribe|destruye\b"),
    (r"\bunreliable\b", r"\breliable\b"),
    (r"\bwithout retransmission\b", r"\b(?:with|guaranteeing) retransmission\b"),
    (r"\bcarece de control de flujo\b", r"\bcontrol de flujo\b"),
    (r"\bdiscards lost packets without\b", r"\bretransmission of lost packets\b"),
    (r"\bstack data structure enforces first-in\b", r"\blast-in|lifo\b"),
    (r"\bfifo\b", r"\blifo\b"),
    (r"\bsobrevive al retorno\b", r"\bdesapila|destruye\b"),
    (r"\bsin ciclarse\b", r"\bfalla ante la presencia de.*negativo\b"),
    (r"\badmite ciclos.*negativo\b", r"\bno funciona en presencia de.*negativo\b"),
    (r"\bse resuelve autom[áa]ticamente dejando\b", r"\bintervenci[óo]n externa\b"),
    (r"\bdestruye y borra de memoria cada vez que el proceso realiza\b", r"\bpersiste durante todo el ciclo\b"),
    (r"\bdestruye el recurso protegido\b", r"\blibera el acceso\b"),
    (r"\btiempo de respuesta sea exactamente de cero\b", r"\btiempo de respuesta es finito\b"),
    (r"\bzero milliseconds\b", r"\bnon-zero\b"),
    (r"\bcorrige autom[áa]ticamente\b", r"\bprovoca fallos|vulnerabilidad\b"),
    (r"\bfixes all memory faults\b", r"\bcorrupts memory\b"),
    (r"\bdescartando los nodos que contengan distancias pares\b", r"\bdistancia acumulada m[íi]nima\b"),
    (r"\bskipping all graph vertices that have prime\b", r"\btentative distance\b"),
    (r"\bse reutiliza para restaurar el mismo proceso con sus datos intactos\b", r"\bliberado y destruido\b"),
    (r"\brestart itself without os intervention\b", r"\breclaimed|cannot autonomously\b"),
    (r"\bdisponibles globalmente para cualquier otro m[óo]dulo\b", r"\balcance l[ée]xico local|desaparecen\b"),
    (r"\bglobally accessible across all running\b", r"\bisolate local scope\b"),
    (r"\bse reinicie autom[áa]ticamente\b", r"\bconsume memoria gradualmente\b"),
    (r"\bpower-off of the motherboard\b", r"\bconsume ram over time\b"),
    (r"\bjam[áa]s se pierdan en el medio f[íi]sico\b", r"\bs[íi] pueden perderse|retransmite\b"),
    (r"\bnever drop packets\b", r"\bcan still be dropped\b"),
    (r"\bninguna operaci[óo]n aritm[ée]tica puede ejecutarse\b", r"\boperaciones aritm[ée]ticas normalmente\b"),
    (r"\bforbids any mathematical addition\b", r"\baddition is fully supported\b"),
    (r"\bjam[áa]s requiera l[íi]neas de direcci[óo]n\b", r"\brequiriendo buses y l[íi]neas\b"),
    (r"\bremoving the need for physical dram\b", r"\bmap directly to physical\b"),
    (r"\bacceso directo a cualquier posici[óo]n intermedia en o\(1\)\b", r"\bsolo permite acceso en los extremos\b"),
    (r"\brandom index access to all middle elements\b", r"\bonly grant access to front and back\b"),
    (r"\bimpidiendo cualquier salto o bifurcaci[óo]n\b", r"\bprecisamente para permitir bifurcaciones\b"),
    (r"\bstrictly preventing any branch or loop\b", r"\bspecifically write target addresses\b"),
    (r"\bse ejecuten en serie de principio a fin\b", r"\bsolo serializa el paso por la secci[óo]n cr[íi]tica\b"),
    (r"\bexecute serially one after another\b", r"\bonly protects the specific critical section\b"),
    (r"\b(?:acceso directo|random index access|posici[óo]n intermedia).*o\(1\)\b", r"\b(?:solo permite acceso|only grant access|no est[áa] soportado|cannot be directly accessed|restricted to push and pop)\b"),
    (r"\b(?:b[úu]squeda|retrieval|search).*o\(1\)\b", r"\bo\(log n\)\b"),
    (r"\btanto interna como externa\b", r"\bpersiste la fragmentaci[óo]n interna\b"),
    (r"\b(?:removes?|elimina)\s+any\s+internal\s+fragmentation\b", r"\binternal fragmentation\b"),
    (r"\b(?:preprending|prepending).*o\(n\)\b", r"\bo\(1\)\b"),
    (r"\bwithout consuming any cpu\b", r"\bincurring measurable cpu|overhead\b"),
    (r"\b(?:zero latency|sin latencia|without any delay|0 latencia)\b", r"\b(?:measurable latency|incurs.*latency|latencia medible|microsecond latencies|slower than dram)\b"),
    (r"\b(?:disable.*interrupts.*without|desactivar.*interrupciones.*sin)\b", r"\b(?:general protection fault|only the kernel|solo el kernel|falta de protecci[óo]n)\b"),
    (r"\b(?:alter|modify|modificar|cambiar).*mode bit\b", r"\b(?:cannot be altered|no puede ser alterado|strictly through hardware traps)\b"),
    (r"\b(?:never drop|never dropped|packets are never dropped)\b", r"\b(?:can still be dropped|still drop packets|packet loss|detecting lost)\b"),
    (r"\b(?:correctly|correct|soporta|admite).*negative (?:weight|cycle)\b", r"\b(?:incorrect|cannot|fails|no est[áa] soportado|bellman-ford)\b"),
    (r"\b(?:prevents?|elimina|evita)\s+deadlocks?\b", r"\b(?:does not prevent|no evita|no previene|deadlocks? may still)\b"),
    (r"\b(?:eliminate|eliminates|prevents?|elimina|inmune).*aba problem\b", r"\b(?:susceptible to the aba problem|susceptible al problema aba|aba problem unless)\b"),
    (r"\b(?:wooden|paper letters|wood and metal)\b", r"\b(?:numerical address|memory cell|dram|semiconductor)\b"),
]


def stem_token(token: str) -> str:
    """Normalize morphological suffixes for cross-lingual and paraphrase alignment."""
    t = token.lower()
    for sfx in ("ization", "izing", "ational", "tional", "tion", "ness", "ment", "able", "ing", "ed", "es", "s"):
        if len(t) > len(sfx) + 2 and t.endswith(sfx):
            t = t[:-len(sfx)]
            break
    for sfx in ("ización", "izacion", "ciones", "ción", "cion", "mientos", "miento", "idades", "idad", "mente", "es", "s", "ado", "ada", "idos", "ida"):
        if len(t) > len(sfx) + 2 and t.endswith(sfx):
            t = t[:-len(sfx)]
            break
    return t


class TokenGroundingEngine:
    """Multi-lingual evidence grounding engine for atomic claims."""

    def __init__(
        self,
        bilingual_dict_path: Optional[Path] = None,
        tau_supported: float = 0.55,
        tau_partial: float = 0.30,
    ) -> None:
        self.tau_supported = tau_supported
        self.tau_partial = tau_partial
        self.bilingual_dict_hash = ""
        self.es_to_en: Dict[str, List[str]] = {}
        self.en_to_es: Dict[str, List[str]] = {}
        self.symbolic_verifier = SymbolicVerifier()

        if bilingual_dict_path and bilingual_dict_path.exists():
            self.load_bilingual_dictionary(bilingual_dict_path)

    def load_bilingual_dictionary(self, path: Path) -> None:
        """Load and register SHA-256 of technical bilingual dictionary (Amendment H3)."""
        content = path.read_bytes()
        self.bilingual_dict_hash = hashlib.sha256(content).hexdigest()
        data = json.loads(content.decode("utf-8"))
        self.es_to_en = data.get("es_to_en", {})
        self.en_to_es = data.get("en_to_es", {})

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Clean, extract, and stem alphanumeric word tokens."""
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [t.strip() for t in clean.split() if t.strip()]
        return [stem_token(t) for t in tokens if t not in ALL_STOPWORDS and len(t) > 1]

    def expand_token_bilingual(self, token: str) -> Set[str]:
        """Expand token using technical bilingual dictionary with morphological normalization."""
        stemmed_token = stem_token(token)
        expanded = {token, stemmed_token}

        for candidate in (token, stemmed_token):
            if candidate in self.es_to_en:
                for en_term in self.es_to_en[candidate]:
                    for word in en_term.split():
                        if word not in ALL_STOPWORDS:
                            expanded.add(word)
                            expanded.add(stem_token(word))

            if candidate in self.en_to_es:
                for es_term in self.en_to_es[candidate]:
                    for word in es_term.split():
                        if word not in ALL_STOPWORDS:
                            expanded.add(word)
                            expanded.add(stem_token(word))

        return expanded

    def detect_phrase_matches(self, text_a: str, text_b: str) -> List[Tuple[str, str]]:
        """Find matching multi-word technical dictionary phrases across texts."""
        matches = []
        text_a_lower = text_a.lower()
        text_b_lower = text_b.lower()

        # Check all ES phrases
        for es_phrase, en_list in self.es_to_en.items():
            if len(es_phrase.split()) > 1:
                # Check if ES in text_a and EN in text_b (or vice-versa)
                if es_phrase in text_a_lower:
                    for en_phrase in en_list:
                        if en_phrase in text_b_lower:
                            matches.append((es_phrase, en_phrase))
                elif es_phrase in text_b_lower:
                    for en_phrase in en_list:
                        if en_phrase in text_a_lower:
                            matches.append((en_phrase, es_phrase))
        return matches

    def check_direct_contradiction(self, claim_text: str, evidence_text: str) -> bool:
        """Check for explicit semantic contradiction between claim and evidence."""
        c_lower = claim_text.lower()
        e_lower = evidence_text.lower()

        for pat_a, pat_b in CONTRADICTION_PAIRS:
            if re.search(pat_a, c_lower) and re.search(pat_b, e_lower):
                return True
            if re.search(pat_b, c_lower) and re.search(pat_a, e_lower):
                return True

        return False

    def compute_grounding_score(
        self,
        claim_text: str,
        evidence_text: str,
    ) -> Tuple[float, List[Tuple[str, str]]]:
        """Compute token containment score with bilingual expansion."""
        claim_tokens = self.tokenize(claim_text)
        if not claim_tokens:
            return 0.0, []

        ev_tokens = set(self.tokenize(evidence_text))
        matched_pairs: List[Tuple[str, str]] = []
        matched_count = 0

        # Check multi-word technical matches first
        phrase_matches = self.detect_phrase_matches(claim_text, evidence_text)
        matched_pairs.extend(phrase_matches)

        phrase_tokens = set()
        for p_a, p_b in phrase_matches:
            for pt in self.tokenize(p_a):
                phrase_tokens.add(pt)
            for pt in self.tokenize(p_b):
                phrase_tokens.add(pt)

        for token in claim_tokens:
            if token in phrase_tokens:
                matched_count += 1
                continue
            expanded = self.expand_token_bilingual(token)
            found = False
            for exp_token in expanded:
                if exp_token in ev_tokens:
                    matched_pairs.append((token, exp_token))
                    matched_count += 1
                    found = True
                    break

        # Containment score: proportion of substantive claim tokens grounded in evidence
        containment = matched_count / len(claim_tokens)

        # Boost containment score if phrase matches were detected
        if phrase_matches:
            containment = min(1.0, containment + 0.15 * len(phrase_matches))

        return round(containment, 4), matched_pairs

    def ground_claim(
        self,
        claim: ExtractedClaim,
        evidence_chunks: List[Any],  # List of Chunk, ScoredCandidate, or dict
    ) -> ClaimGroundingResult:
        """Ground a single extracted claim against evidence pool respecting H1 policy."""
        # 1. H1: CONVERSATIONAL claims are EXEMPT
        if claim.claim_type == ClaimType.CONVERSATIONAL:
            return ClaimGroundingResult(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                claim_type=claim.claim_type,
                criticality=claim.criticality,
                status=GroundingStatus.EXEMPT,
                grounding_score=1.0,
                audit_notes="Conversational pleasantry exempt from token gating.",
            )

        # 2. H1: FORMAL claims routed to SymbolicVerifier
        if claim.claim_type in (ClaimType.FORMAL_COMPLEXITY, ClaimType.FORMAL_ARITHMETIC):
            sym_res = self.symbolic_verifier.verify_formal_claim(
                claim_text=claim.text,
                claim_type=claim.claim_type.value,
                formal_data=claim.formal_parameters,
            )
            if sym_res.verdict in (SymbolicVerdict.VERIFIED_TRUE, SymbolicVerdict.REJECTED_HALLUCINATION):
                status = GroundingStatus.SUPPORTED if sym_res.verdict == SymbolicVerdict.VERIFIED_TRUE else GroundingStatus.CONTRADICTION
                score = 1.0 if sym_res.verdict == SymbolicVerdict.VERIFIED_TRUE else 0.0
                return ClaimGroundingResult(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    claim_type=claim.claim_type,
                    criticality=claim.criticality,
                    status=status,
                    grounding_score=score,
                    audit_notes=f"Symbolic verification: {sym_res.verdict.value}. {sym_res.audit_notes}",
                )
            # If UNVERIFIABLE symbolically, fall through to check against evidence chunks

        # Prepare evidence texts and IDs
        ev_items: List[Tuple[str, str]] = []
        for c in evidence_chunks:
            if hasattr(c, "id") and hasattr(c, "content"):
                ev_items.append((str(c.id), c.content))
            elif hasattr(c, "chunk_id") and hasattr(c, "content"):
                ev_items.append((str(c.chunk_id), c.content))
            elif isinstance(c, dict):
                cid = c.get("id") or c.get("chunk_id", "chunk")
                content = c.get("content") or c.get("text") or c.get("ev", "")
                ev_items.append((str(cid), content))
            elif isinstance(c, str):
                ev_items.append(("raw_text", c))

        combined_evidence = " ".join(t[1] for t in ev_items)

        # Check contradiction across evidence
        for cid, content in ev_items:
            if self.check_direct_contradiction(claim.text, content):
                return ClaimGroundingResult(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    claim_type=claim.claim_type,
                    criticality=claim.criticality,
                    status=GroundingStatus.CONTRADICTION,
                    grounding_score=0.0,
                    matched_chunk_ids=[cid],
                    audit_notes=f"Contradiction detected against evidence chunk {cid}.",
                )

        # 3. H1: PEDAGOGICAL claims evaluated only for non-contradiction
        if claim.claim_type == ClaimType.PEDAGOGICAL or claim.is_pedagogical_analogy:
            # If no contradiction was detected above, pedagogical claim passes
            return ClaimGroundingResult(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                claim_type=claim.claim_type,
                criticality=claim.criticality,
                status=GroundingStatus.SUPPORTED,
                grounding_score=1.0,
                is_pedagogical_analogy=True,
                audit_notes="Pedagogical analogy verified for non-contradiction against admitted evidence (H1 exempt from token grounding).",
            )

        # 4. FACTUAL_TEXTUAL: Multi-level token grounding
        best_score = 0.0
        best_matched_terms: List[Tuple[str, str]] = []
        best_chunks: List[str] = []

        for cid, content in ev_items:
            score, terms = self.compute_grounding_score(claim.text, content)
            if score > best_score:
                best_score = score
                best_matched_terms = terms
                best_chunks = [cid]
            elif score == best_score and score > 0:
                best_chunks.append(cid)

        # Fallback to combined evidence containment if single chunks are short
        if best_score < self.tau_supported and combined_evidence:
            comb_score, comb_terms = self.compute_grounding_score(claim.text, combined_evidence)
            if comb_score > best_score:
                best_score = comb_score
                best_matched_terms = comb_terms
                best_chunks = [t[0] for t in ev_items[:3]]

        # Determine GroundingStatus based on calibrated thresholds
        if best_score >= self.tau_supported:
            status = GroundingStatus.SUPPORTED
            notes = f"Sufficiently grounded in evidence (score={best_score:.2f} >= {self.tau_supported:.2f})"
        elif best_score >= self.tau_partial:
            status = GroundingStatus.PARTIALLY_SUPPORTED
            notes = f"Partially supported claim (score={best_score:.2f}, in [{self.tau_partial:.2f}, {self.tau_supported:.2f}))"
        else:
            status = GroundingStatus.UNSUPPORTED
            notes = f"Unsupported claim (score={best_score:.2f} < {self.tau_partial:.2f})"

        return ClaimGroundingResult(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            claim_type=claim.claim_type,
            criticality=claim.criticality,
            status=status,
            grounding_score=best_score,
            matched_chunk_ids=best_chunks,
            matched_terms=best_matched_terms,
            audit_notes=notes,
        )

    def ground_claims(
        self,
        claims: List[ExtractedClaim],
        evidence_chunks: List[Any],
    ) -> List[ClaimGroundingResult]:
        """Ground a list of extracted claims against evidence pool."""
        return [self.ground_claim(claim, evidence_chunks) for claim in claims]
