"""C5 Trust Gate & Epistemic Abstention Contract (Gate B - CP111).

Establece la frontera epistemológica pre-LLM, determinística y fail-closed:
    NO_AUTHORIZED_SUFFICIENT_EVIDENCE -> NO_UNGROUNDED_LLM_ANSWER

Principios y Restricciones Vinculantes (Addendum CP111):
1. Relevance Threshold (theta):
   Mantenido como PENDING_EMPIRICAL_CALIBRATION debido a la heterogeneidad de escalas
   (BM25: [0, 20+], Cosine: ~0.83-0.95, RRF: [0.01, 0.05], Local: [0, 1.0]).
2. Fail-Closed Estricto:
   Nunca usar defaults permisivos (e.g. is_sufficient=True). Todo estado desconocido,
   pack ausente o contrato incompleto produce FAIL-CLOSED -> NO LLM.
3. Conflict Detection:
   Detector acotado y explícito de divergencias entre fuentes autorizadas.
   Representa CONFLICTING_EVIDENCE sin forzar silenciosamente consenso ni apagón total.
4. Citation Mismatch:
   Una cita inválida ([E99]) nunca puede establecer grounding. C5 actúa pre-LLM.
5. Modularidad:
   Separación limpia entre salud de retrieval, relevancia, suficiencia léxica/conceptual,
   detección de conflicto, compatibilidad de rescate y decisión final C5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from study_engine.storage.lexical_index import _BILINGUAL_MAP, SPANISH_STOPWORDS

logger = logging.getLogger(__name__)

# Semántica de Threshold θ (D_C5_1 & Addendum 1)
RELEVANCE_THRESHOLD_STATUS: str = "PENDING_EMPIRICAL_CALIBRATION"


class EpistemicTrustStatus(str, Enum):
    """Estados tipados de la frontera epistemológica C5."""
    NO_AUTHORIZED_EVIDENCE = "NO_AUTHORIZED_EVIDENCE"
    NO_EVIDENCE = "NO_EVIDENCE"
    LOW_RELEVANCE = "LOW_RELEVANCE"
    PARTIAL_EVIDENCE = "PARTIAL_EVIDENCE"
    RELATED_INSUFFICIENT = "RELATED_INSUFFICIENT"
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"


@dataclass(frozen=True)
class EpistemicTrustEvaluation:
    """Resultado determinista e inmutable de la evaluación epistemológica C5."""
    status: EpistemicTrustStatus
    is_sufficient: bool
    abstained: bool
    abstention_reason: Optional[str] = None
    coverage_ratio: float = 0.0
    missing_critical_terms: List[str] = field(default_factory=list)
    is_conflicting: bool = False
    conflict_details: Optional[str] = None
    max_relevance: float = 0.0


# Palabras de encuadre pedagógico o metadatos de cátedra
_PEDAGOGICAL_FRAME_WORDS: Set[str] = {
    "explicame", "explica", "explicar", "decime", "dime", "dame", "contame",
    "como", "funciona", "que", "cual", "cuales", "porque", "consiste",
    "definicion", "ejemplo", "ejercicios", "ejercicio", "mostrar", "ver", "analizar",
    "diferencia", "versus", "respecto", "relacion", "significa", "importancia",
    "exactamente", "especificamente", "detalle", "sistema", "sistemas",
    "operativo", "operativos", "computacion", "materia", "catedra", "programa",
    "pasa", "pasar", "ocurre", "ocurrir", "sucede", "suceder", "anda", "andar",
    "sirve", "servir", "usa", "usar", "queda", "quedar", "hace", "hacer",
    "ahi", "aca", "alla", "alli", "esto", "eso", "aquello", "aquel", "aquella",
    "anterior", "coso", "ese", "esa", "dijiste",
    # Verbos y conectores de solicitud o consigna
    "encaro", "encarar", "resuelvo", "resolver", "resolucion", "planteo", "plantear",
    "ayuda", "ayudame", "puedo", "debo", "quiero", "necesito", "entender",
    "pregunto", "consulta", "duda", "pasame", "pasar", "paso", "dar", "mostrame",
    "trae", "traeme", "solucion", "soluciones", "completo", "completa", "ahora",
    "luego", "despues", "entonces", "guia", "guias", "practica", "practicas",
    "practico", "practicos", "consigna", "enunciado", "problema", "problemas",
    "item", "items", "tema", "curricular", "activo", "estudiante", "kc",
    "indica", "indicar", "indique", "dice", "decir", "describe", "describir",
    "representa", "representar", "establece", "establecer", "menciona", "mencionar",
    "trata", "tratar", "refiere", "referir",
}

_TECHNICAL_BILINGUAL_EXTENSIONS: Dict[str, str] = {
    "paginacion": "paging",
    "pagina": "page",
    "paginas": "page",
    "paging": "paginacion",
    "page": "pagina",
    "pages": "pagina",
    "segmentacion": "segmentation",
    "segmento": "segment",
    "segmentos": "segment",
    "segmentation": "segmentacion",
    "demanda": "demand",
    "demand": "demanda",
    "traduccion": "translation",
    "translation": "traduccion",
}

# Mapa inverso para traducción bidireccional inglés <-> español
_REVERSE_BILINGUAL_MAP: Dict[str, str] = {v: k for k, v in _BILINGUAL_MAP.items()}
_REVERSE_BILINGUAL_MAP.update({v: k for k, v in _TECHNICAL_BILINGUAL_EXTENSIONS.items()})


def normalize_term(term: str) -> str:
    """Normaliza un término léxico para comparación canónica insensible a acentos y plurales."""
    t = term.lower().strip()
    unaccented = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    if unaccented in _BILINGUAL_MAP:
        return _BILINGUAL_MAP[unaccented]
    if unaccented in _TECHNICAL_BILINGUAL_EXTENSIONS:
        return _TECHNICAL_BILINGUAL_EXTENSIONS[unaccented]
    # Lematización básica de sufijos en español/inglés
    if len(unaccented) > 4 and unaccented.endswith("es"):
        unaccented = unaccented[:-2]
    elif len(unaccented) > 3 and unaccented.endswith("s"):
        unaccented = unaccented[:-1]
    if unaccented in _BILINGUAL_MAP:
        return _BILINGUAL_MAP[unaccented]
    if unaccented in _TECHNICAL_BILINGUAL_EXTENSIONS:
        return _TECHNICAL_BILINGUAL_EXTENSIONS[unaccented]
    return unaccented


def extract_critical_query_terms(query: str) -> List[str]:
    """Extrae términos técnicos sustantivos y entidades de la consulta del estudiante."""
    # Descartar prefijos de enriquecimiento de template de búsqueda si están presentes
    m_student = re.search(r"Consulta del estudiante:\s*(.*)", query, re.IGNORECASE | re.DOTALL)
    effective_q = m_student.group(1) if m_student else query

    clean_q = effective_q.replace("-", " ").replace("_", " ").replace(".", " ")
    tokens = re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ%]+", clean_q)
    critical_terms: List[str] = []
    
    # Secuencias numéricas o porcentajes explícitos
    numbers_and_percents = re.findall(r"\b\d+(?:\.\d+)?%?\b", effective_q)

    for tok in tokens:
        norm = normalize_term(tok)
        if len(norm) <= 1:
            continue
        if norm in SPANISH_STOPWORDS or tok.lower() in SPANISH_STOPWORDS:
            continue
        if norm in _PEDAGOGICAL_FRAME_WORDS or tok.lower() in _PEDAGOGICAL_FRAME_WORDS:
            continue
        critical_terms.append(norm)

    for np in numbers_and_percents:
        np_norm = np.lower().strip()
        if np_norm not in critical_terms:
            critical_terms.append(np_norm)

    return list(dict.fromkeys(critical_terms))


def evaluate_term_coverage(
    critical_terms: Sequence[str],
    raw_chunks: Sequence[Any],
) -> Tuple[float, List[str]]:
    """Evalúa la cobertura de los términos críticos sobre el conjunto de fragmentos recuperados.
    
    Retorna (coverage_ratio, missing_terms).
    """
    if not critical_terms:
        return 1.0, []
    if not raw_chunks:
        return 0.0, list(critical_terms)

    # Extraer todo el texto de los chunks incluyendo metadatos relevantes (fuente, sección, id)
    all_chunk_text = []
    for c in raw_chunks:
        if isinstance(c, dict):
            text = " ".join(filter(None, [
                c.get("chunk_text") or c.get("content") or "",
                c.get("source_title") or "",
                c.get("source_id") or "",
                c.get("section") or "",
                c.get("document_id") or "",
            ]))
        else:
            text = " ".join(filter(None, [
                getattr(c, "content", "") or getattr(c, "chunk_text", "") or "",
                getattr(c, "source_title", "") or "",
                getattr(c, "source_id", "") or "",
                getattr(c, "section", "") or "",
                getattr(c, "document_id", "") or "",
            ]))
        all_chunk_text.append(text)
    combined = " ".join(all_chunk_text).lower()

    chunk_tokens = re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ%]+", combined)
    chunk_norm_set = {normalize_term(tok) for tok in chunk_tokens}
    clean_combined_flat = combined.replace(" ", "")

    covered_count = 0
    missing: List[str] = []

    for term in critical_terms:
        norm_t = normalize_term(term)
        # 1. Match directo en set normalizado o texto plano
        if norm_t in chunk_norm_set or term.lower() in chunk_norm_set:
            covered_count += 1
            continue
        # 2. Match bidireccional bilingüe
        en_target = _BILINGUAL_MAP.get(norm_t) or _BILINGUAL_MAP.get(term.lower())
        if en_target and (en_target in chunk_norm_set or en_target in combined):
            covered_count += 1
            continue
        es_target = _REVERSE_BILINGUAL_MAP.get(norm_t) or _REVERSE_BILINGUAL_MAP.get(term.lower())
        if es_target and (es_target in chunk_norm_set or es_target in combined):
            covered_count += 1
            continue
        # 3. Match de substring para números, porcentajes o códigos
        if term.lower() in combined or term.lower().replace(" ", "") in clean_combined_flat:
            covered_count += 1
            continue
        missing.append(term)

    coverage_ratio = round(covered_count / len(critical_terms), 3)
    return coverage_ratio, missing


def detect_evidence_conflicts(
    raw_chunks: Sequence[Any],
    query: str = "",
) -> Tuple[bool, Optional[str]]:
    """Detector acotado de divergencias o afirmaciones incompatibles entre fuentes autorizadas (D_C5_3).
    
    Perímetro documentado (Addendum 3):
    - Opera determinísticamente sobre múltiples fuentes autorizadas distintas.
    - Detecta discrepancias explícitas en parámetros numéricos, definiciones ontológicas
      o polaridades contrapuestas (afirma vs niega) sobre el mismo objeto.
    - No pretende ser un demostrador universal de contradicciones teóricas.
    """
    if len(raw_chunks) < 2:
        return False, None

    sources_seen = set()
    chunks_by_source: Dict[str, List[str]] = {}
    for c in raw_chunks:
        if isinstance(c, dict):
            s_id = c.get("source_id") or "src"
            text = c.get("chunk_text") or c.get("content") or ""
        else:
            s_id = getattr(c, "source_id", "src")
            text = getattr(c, "content", "") or getattr(c, "chunk_text", "") or ""
        sources_seen.add(s_id)
        chunks_by_source.setdefault(s_id, []).append(text.lower())

    if len(sources_seen) < 2:
        return False, None

    conflict_markers = [
        (re.compile(r"\b(?:es\s+posible|se\s+puede|permite|soporta)\b"),
         re.compile(r"\b(?:no\s+es\s+posible|no\s+se\s+puede|no\s+permite|no\s+soporta|incompatible)\b")),
        (re.compile(r"\b(?:monol[ií]tico)\b"),
         re.compile(r"\b(?:microkernel|micro-kernel|modular\s+puro)\b")),
        (re.compile(r"\b(?:estricto|bloqueante)\b"),
         re.compile(r"\b(?:no\s+bloqueante|relajado|as[ií]ncrono)\b")),
    ]

    source_list = list(chunks_by_source.keys())
    for i in range(len(source_list)):
        s1 = source_list[i]
        text1 = " ".join(chunks_by_source[s1])
        for j in range(i + 1, len(source_list)):
            s2 = source_list[j]
            text2 = " ".join(chunks_by_source[s2])

            for pat_pos, pat_neg in conflict_markers:
                if (pat_pos.search(text1) and pat_neg.search(text2)) or (pat_neg.search(text1) and pat_pos.search(text2)):
                    detail = (
                        f"Divergencia doctrinal detectada entre fuente '{s1}' y fuente '{s2}'. "
                        "Existen afirmaciones antagónicas sobre el mismo objeto de estudio."
                    )
                    return True, detail

    return False, None


def evaluate_conversational_rescue_compatibility(
    new_query: str,
    previous_context_pack: Any,
    previous_chunks: Sequence[Any],
    *,
    contextual_query: Optional[str] = None,
    topic_query: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Verifica la compatibilidad temática entre la nueva consulta y el contexto previo (D_C5_6).
    
    Impide que consultas cortas OOD o con cambio de tema reutilicen por inercia
    evidencia de un tema diferente.
    """
    from study_engine.pedagogy.conversation_state import has_explicit_topic_change

    q = (new_query or "").strip()
    if not q:
        return False, "Consulta vacía no rescata contexto."

    # 1. Quiebre explícito de tema
    if has_explicit_topic_change(q):
        return False, "Quiebre explícito de tema detectado."

    critical_new = extract_critical_query_terms(topic_query if topic_query is not None else q)
    has_topic_terms = bool(critical_new)

    # 2. Consulta puramente deíctica o sin nuevos sustantivos
    if not critical_new:
        if contextual_query is None:
            return True, "Continuidad deíctica pura sin nuevos términos temáticos."

    # 3. Extraer vocabulario del contexto previo
    prev_text_parts = []
    if previous_context_pack and hasattr(previous_context_pack, "formatted_context"):
        prev_text_parts.append(getattr(previous_context_pack, "formatted_context") or "")
    for chk in (previous_chunks or []):
        if isinstance(chk, dict):
            prev_text_parts.append(chk.get("chunk_text") or chk.get("content") or "")
        else:
            prev_text_parts.append(getattr(chk, "content", "") or getattr(chk, "chunk_text", "") or "")
    
    prev_combined = " ".join(prev_text_parts).lower()
    if not prev_combined:
        return False, "Contexto previo sin texto disponible para evaluar compatibilidad."

    prev_tokens = {normalize_term(w) for w in re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+", prev_combined)}

    # 4. Medir solapamiento
    overlap_count = 0
    terms_to_compare = critical_new
    if not terms_to_compare and contextual_query:
        terms_to_compare = extract_critical_query_terms(contextual_query)

    for term in terms_to_compare:
        norm_t = normalize_term(term)
        if norm_t in prev_tokens or term.lower() in prev_combined or _BILINGUAL_MAP.get(norm_t) in prev_tokens:
            overlap_count += 1

    if not terms_to_compare:
        return False, "La consulta contextual no contiene términos que permitan validar el antecedente."

    overlap_ratio = overlap_count / len(terms_to_compare)

    if overlap_count == 0:
        return False, f"Incompatibilidad temática total: 0/{len(terms_to_compare)} términos solapan con contexto previo."
    if topic_query is not None and has_topic_terms and overlap_count < len(critical_new):
        return False, "La consulta de seguimiento introduce términos temáticos que no están respaldados por el contexto previo."

    return True, f"Compatibilidad temática verificada (solapamiento={overlap_ratio:.2f})."


def evaluate_epistemic_trust(
    query: str,
    raw_chunks: Sequence[Any],
    *,
    retrieval_failed: bool = False,
    retrieval_error: Optional[str] = None,
    scope_authorized: bool = True,
    scope_error_reason: Optional[str] = None,
    resolved_content_item: Optional[Any] = None,
    has_reference_disclaimer: bool = False,
) -> EpistemicTrustEvaluation:
    """Frontera central de evaluación epistémica pre-LLM (C5 Trust Gate).
    
    Determina si existe evidencia autorizada y suficiente antes de habilitar
    cualquier respuesta fundamentada.
    """
    critical_terms = extract_critical_query_terms(query)

    # 1. Retrieval Failure (Fail-Closed Absoluto - D_C5_4)
    if retrieval_failed:
        reason = retrieval_error or "RETRIEVAL_FAILURE"
        return EpistemicTrustEvaluation(
            status=EpistemicTrustStatus.RETRIEVAL_FAILURE,
            is_sufficient=False,
            abstained=True,
            abstention_reason=reason,
            coverage_ratio=0.0,
            missing_critical_terms=critical_terms,
        )

    # 2. Scope Authorization (C1-C4 Invariants)
    if not scope_authorized:
        reason = scope_error_reason or "NO_AUTHORIZED_ACTIVE_SOURCES"
        return EpistemicTrustEvaluation(
            status=EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
            is_sufficient=False,
            abstained=True,
            abstention_reason=reason,
            coverage_ratio=0.0,
            missing_critical_terms=critical_terms,
        )

    # 3. Zero Evidence (D_C5_1)
    if not raw_chunks:
        return EpistemicTrustEvaluation(
            status=EpistemicTrustStatus.NO_EVIDENCE,
            is_sufficient=False,
            abstained=True,
            abstention_reason="QUERY_OUT_OF_SCOPE",
            coverage_ratio=0.0,
            missing_critical_terms=critical_terms,
        )

    # 3b. Resolución canónica vía ContentRegistry
    if resolved_content_item is not None and raw_chunks:
        return EpistemicTrustEvaluation(
            status=EpistemicTrustStatus.SUFFICIENT_EVIDENCE,
            is_sufficient=True,
            abstained=False,
            coverage_ratio=1.0,
            missing_critical_terms=[],
            max_relevance=1.0,
        )

    # 4. Relevance evaluation (D_C5_1)
    scores: List[float] = []
    for c in raw_chunks:
        if isinstance(c, dict):
            s = c.get("relevance_score") or c.get("score") or 0.0
        else:
            s = getattr(c, "relevance_score", None) or getattr(c, "score", None) or 0.0
        try:
            scores.append(float(s))
        except (ValueError, TypeError):
            scores.append(0.0)

    max_rel = max(scores) if scores else 0.0

    # 5. Sufficiency Gate & Coverage Guard (D_C5_2 & OC-1..OC-5)
    # RELATED != SUFFICIENT
    critical_terms = extract_critical_query_terms(query)
    coverage_ratio, missing_terms = evaluate_term_coverage(critical_terms, raw_chunks)

    # Regla determinística de suficiencia
    if critical_terms:
        is_substantive_miss = False
        if len(critical_terms) == 1 and coverage_ratio < 1.0:
            is_substantive_miss = True
        elif len(critical_terms) == 2 and coverage_ratio < 1.0:
            is_substantive_miss = True
        elif len(critical_terms) >= 3 and coverage_ratio < 0.60:
            is_substantive_miss = True
        elif missing_terms:
            if has_reference_disclaimer:
                conceptual_missing = [m for m in missing_terms if not m.isdigit()]
                if conceptual_missing or coverage_ratio < 0.70:
                    is_substantive_miss = True
            else:
                specific_missing = [
                    m for m in missing_terms
                    if any(c.isdigit() for c in m) or len(m) >= 5 or "%" in m
                ]
                if specific_missing:
                    is_substantive_miss = True

        if is_substantive_miss:
            logger.info(
                "C5 Sufficiency Gate Miss: query='%s', critical=%s, missing=%s, cov=%.2f",
                query, critical_terms, missing_terms, coverage_ratio
            )
            return EpistemicTrustEvaluation(
                status=EpistemicTrustStatus.RELATED_INSUFFICIENT,
                is_sufficient=False,
                abstained=True,
                abstention_reason="QUERY_OUT_OF_SCOPE",
                coverage_ratio=coverage_ratio,
                missing_critical_terms=missing_terms,
                max_relevance=max_rel,
            )

    # 6. Conflict Detection (D_C5_3 & Addendum 3)
    is_conflicting, conflict_details = detect_evidence_conflicts(raw_chunks, query)
    if is_conflicting:
        return EpistemicTrustEvaluation(
            status=EpistemicTrustStatus.CONFLICTING_EVIDENCE,
            is_sufficient=True,
            abstained=False,
            abstention_reason=None,
            coverage_ratio=coverage_ratio,
            missing_critical_terms=missing_terms,
            is_conflicting=True,
            conflict_details=conflict_details,
            max_relevance=max_rel,
        )

    # 7. Evidencia Suficiente Verificada
    return EpistemicTrustEvaluation(
        status=EpistemicTrustStatus.SUFFICIENT_EVIDENCE,
        is_sufficient=True,
        abstained=False,
        abstention_reason=None,
        coverage_ratio=coverage_ratio,
        missing_critical_terms=[],
        is_conflicting=False,
        conflict_details=None,
        max_relevance=max_rel,
    )
