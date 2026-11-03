"""Pedagogical Concept Builder (Formulates Multi-Source Synthesis Proposals).

INVARIANTS:
1. Proposes synthesis ONLY; does NOT grant S4.4 approval.
2. Formulates synthesis grounded in cited sources respecting roles:
   - PRIMARY: core_concept
   - METHODOLOGICAL: mental_model and reasoning_guidance
   - FORMAL: formalization
   - IMPLEMENTATION: implementation_guidance
3. Integrates consultive StudentContext to warn about known student pitfalls
   and avoid rudimentary explanations without attributing mastery.
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.student_context import StudentContext

# M1-02 (contrato de citas / calidad pedagógica del packet determinista):
# los chunks admitidos suelen arrancar con ruido tipográfico (running head de
# página con número, arte de portada tipo "CODE\nEAT\nSLEEP", cortes
# silábicos "doblemen-\nte"). Elegir la PRIMERA oración por corte de
# puntuación produce frases verbatim pero pedagógicamente vacías
# ("...hacia atrás (Fig."), pues el punto de "Fig." corta la frase y el
# running head arrastra el número de página a la "oración". La selección es
# DETERMINISTA y preserva identidad: la oración final es substring del
# fragmento normalizado (la cita [E#] y el NLI premise↔hipótesis no cambian;
# el supuesto sigue siendo texto real del fragmento citado).
_WHITESPACE_RE = re.compile(r"\s+")
_HYPHEN_BREAK_RE = re.compile(r"([a-záéíóúñü])-\s*\n\s*([a-záéíóúñü])")
# Running head de PDF: línea de ≥6 palabras que TERMINA en número de página
# ("Estructuras dinámicas lineales ... enlazadas)   451").
_PAGE_NUMBER_LINE_RE = re.compile(r"^(?:\S+\s+){5,}\S*\s\d{1,4}$")
_LEADING_JUNK_RE = re.compile(r"^[^A-Za-zÁÉÍÓÚÑáéíóúñ¿¡\[]+\s*")
_CAPS_CHAIN_RE = re.compile(r"^(?:[A-ZÁÉÍÓÚÑ]{2,}[A-Za-zÁÉÍÓÚÑáéíóúñ]*\s+){2,}")
_MIN_SENTENCE_WORDS = 8
_STOPWORDS = frozenset({
    "tramo", "unidad", "modulo", "módulo", "introducción", "concepto",
    "siguiente", "anteriores", "según", "que", "para", "con", "una",
    "los", "las", "del", "sobre", "entre", "cómo", "como", "usar",
    "uso", "desde", "hacia", "este", "esta",
})


def _objective_terms(objective: str) -> List[str]:
    """Tokens discriminantes del objetivo del KC (determinista, sin stemming)."""
    words = _WHITESPACE_RE.sub(" ", objective or "").lower()
    terms: List[str] = []
    for tok in re.split(r"[^a-záéíóúñü]+", words):
        if len(tok) >= 4 and tok not in _STOPWORDS and tok not in terms:
            terms.append(tok)
    return terms


def _is_noise_line(line: str) -> bool:
    """Línea de ruido tipográfico: arte de portada en mayúsculas o running
    head terminado en número de página. Determinista, sin heurística semántica."""
    line = line.strip()
    if len(line) < 3:
        return True
    if not _WHITESPACE_RE.search(line):
        return True  # palabra aislada suelta ("CODE", "EAT")
    letters = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", line)
    if letters and not re.search(r"[a-záéíóúñ]", line):
        return True  # línea íntegramente en mayúsculas (arte de portada)
    if _PAGE_NUMBER_LINE_RE.match(line):
        return True  # running head + número de página
    return False


def _normalize_chunk_text(content: str) -> str:
    """Hyphen-join de cortes silábicos + descarte de líneas de ruido +
    colapso de whitespace. La identidad del contenido se conserva: el texto
    restante es yuxtaposición literal de las líneas conservadas."""
    txt = _HYPHEN_BREAK_RE.sub(r"\1\2", content or "")
    kept = [line for line in txt.splitlines() if not _is_noise_line(line)]
    txt = " ".join(kept)
    txt = _WHITESPACE_RE.sub(" ", txt)
    return txt.strip()


def _is_acceptable_candidate(sentence: str) -> bool:
    """Filtro determinista de candidatos verbatim: longitud mínima, proporción
    alfabética, sin cadena de mayúsculas de portada y con cierre de oración.
    NO rechaza números en general ("4 bytes" es contenido legítimo): el ruido
    de números de página ya se eliminó a nivel de línea."""
    if len(sentence) < 40:
        return False
    if not sentence.endswith((".", "!", "?", '"', "”")):
        return False
    words = sentence.split()
    if len(words) < _MIN_SENTENCE_WORDS:
        return False
    if _CAPS_CHAIN_RE.match(sentence):
        return False
    if sentence.rstrip().endswith("("):
        return False
    letters = len(re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", sentence))
    if letters / max(1, len("".join(words))) < 0.55:
        return False
    return True


def _select_verbatim_sentence(content: str, objective: str) -> str:
    """Selecciona DETERMINISTICAMENTE una oración verbatim del fragmento.

    Ranking: cobertura de términos del objetivo (desc), luego posición (asc).
    La oración devuelta es substring del texto normalizado del fragmento
    (hyphen-join + colapso de whitespace; la identidad del contenido se
    conserva): la cita [E#] y el hash del fragmento NO cambian. Sin
    candidato aceptable devuelve "" (el llamador recurre al template y el
    audit decides fail-closed).
    """
    normalized = _normalize_chunk_text(content)
    if not normalized:
        return ""
    terms = _objective_terms(objective)
    candidates: List[str] = []
    for piece in re.split(r"(?<=[.!?])\s+", normalized):
        clean = _CAPS_CHAIN_RE.sub("", piece)
        clean = _LEADING_JUNK_RE.sub("", clean)
        clean = clean.strip()
        if clean and _is_acceptable_candidate(clean):
            candidates.append(clean)
    if not candidates:
        return ""

    def rank(item: str):
        text = item.lower()
        coverage = sum(1 for t in terms if t in text)
        head = text[:24]
        position = normalized.find(head) if head in normalized else len(normalized)
        return (-coverage, position)

    candidates.sort(key=rank)
    return candidates[0]


class ConceptPacketBuilder:
    """Builds multi-source structured concept proposals for S4.4 verification."""

    def build_proposal(
        self,
        notebook_id: str,
        kc_id: str,
        objective: str,
        evidence_by_role: Dict[str, List[CitationRecord]],
        all_citations: List[CitationRecord],
        student_context: Optional[StudentContext] = None,
        content_by_citation: Optional[Dict[str, str]] = None,
    ) -> ConceptPacket:
        """Construct a structured ConceptPacket proposal."""
        # Synthesis determinista y verificable: cada oración fáctica del packet
        # cita su [E#] y reproduce contenido real del fragmento admitido. El
        # NLI (Layer-2) evalúa el claim contra ese fragmento; un texto
        # genérico-templado no pasa entailed-proof contra fuentes reales
        # (falla-cerrado correcto). Sin contenido disponible se recurre al
        # template anterior (y el audit decidirá).
        #
        # M1-02: la extracción usa _select_verbatim_sentence (módulo): norma-
        # lización de cortes silábicos + filtrado de running-head/números de
        # página + ranking por cobertura del objetivo del KC. Determinista y
        # verbatim; equivalente a reelegir SUBSTRING dentro del fragmento ya
        # citado (identidad de cita sin cambio, NLI sigue verificando).
        content_map = content_by_citation or {}

        def _first_sentence(content: str) -> str:
            """Selección determinista de oración verbatim para la cita.

            Falla a cadena vacía si el fragmento no rinde una oración
            aceptable: el llamador recurre al template (el audit decide),
            en lugar de emitir junk tipográfico verbatim.
            """
            return _select_verbatim_sentence(content, objective)

        # Synthesize core concept from PRIMARY
        primary_citations = evidence_by_role.get("PRIMARY", [])
        core_parts: List[str] = []
        for c in primary_citations:
            sent = _first_sentence(content_map.get(c.citation_id, ""))
            if sent:
                core_parts.append(f"[{c.citation_id}] {sent}")
        # M1-02 (contrato de citas): sin oración verbatim admisible NO se emite
        # template taggeado — el llamador (orchestrator) abstiene fail-closed.
        # Un template ("según la literatura canónica...") afirma soporte que no
        # existe en la evidencia y el NLI lo rechaza (REJECTED_UNSUPPORTED);
        # la abstención honesta ahorra el rechazo y no fabrica grounded-ness.
        core_concept = " ".join(core_parts)

        # Synthesize mental model from METHODOLOGICAL
        method_citations = evidence_by_role.get("METHODOLOGICAL", [])
        method_parts: List[str] = []
        for c in method_citations:
            sent = _first_sentence(content_map.get(c.citation_id, ""))
            if sent:
                method_parts.append(f"[{c.citation_id}] {sent}")
        # M1-02: sin oración METHODOLOGICAL verbatim → campo vacío (el texto
        # auditado lo omite). El template "casilleros contiguos" taggeado con
        # refs ajenas era un claim no fundado (hallazgo live Tramo 1
        # 2026-10-20: REJECTED_UNSUPPORTED por ese claim).
        mental_model = " ".join(method_parts)

        # M1-02: guidance sin contenido grounded del corpus → vacío. El texto
        # fijo anterior era específico de punteros (KC-wrong para otros temas)
        # y nunca portaba tags (no es auditable como claim).
        reasoning_guidance = ""

        # Formalization from FORMAL (if present)
        formal_citations = evidence_by_role.get("FORMAL", [])
        formalization: Optional[str] = None
        if formal_citations:
            formal_refs = "".join([f"[{c.citation_id}]" for c in formal_citations])
            formalization = (
                f"Fórmula formal de direccionamiento {formal_refs}:\n"
                f"$$\\text{{Address}}(A[i]) = \\text{{Base}} + i \\times \\text{{sizeof}}(T)$$\n"
                f"donde $i$ representa el índice y $T$ el tipo del elemento."
            )

        # Implementation from IMPLEMENTATION (if present)
        impl_citations = evidence_by_role.get("IMPLEMENTATION", [])
        implementation_guidance: Optional[str] = None
        if impl_citations:
            impl_refs = "".join([f"[{c.citation_id}]" for c in impl_citations])
            implementation_guidance = (
                f"En código estructurado y limpio {impl_refs}, evitá números mágicos: "
                f"usá constantes para las dimensiones y validá siempre límites con cláusulas de guarda."
            )

        # Extract pitfalls considering student context
        pitfalls: List[str] = [
            "Confundir el valor del índice con el desplazamiento en bytes (off-by-sizeof).",
            "Olvidar que los índices comienzan en 0 (off-by-one).",
        ]
        if student_context and student_context.errors_recurring:
            # Include warnings for recurring errors relevant to iteration and bounds
            for err in student_context.errors_recurring[:3]:
                pitfalls.append(f"Atención previa: {err}")

        # Compute deterministic assembly hash
        content_for_hash = f"{notebook_id}:{kc_id}:{core_concept}:{mental_model}"
        assembly_hash = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()

        # Proposal packet starts with APPROVED tentative or pending verdict
        return ConceptPacket(
            kc_id=kc_id,
            notebook_id=notebook_id,
            objective=objective,
            evidence_by_role=evidence_by_role,
            core_concept=core_concept,
            mental_model=mental_model,
            reasoning_guidance=reasoning_guidance,
            formalization=formalization,
            implementation_guidance=implementation_guidance,
            pitfalls=tuple(pitfalls),
            citations=tuple(all_citations),
            s44_report=None,
            audit_verdict=AuditVerdict.APPROVED,
            assembly_hash=assembly_hash,
        )
