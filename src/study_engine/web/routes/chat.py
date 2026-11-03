"""Interactive Chat & Streaming Phased Pedagogical Endpoints (Fase 5.8)."""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import logging
import re
import sqlite3
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Collection, Dict, List, Literal, Optional, Sequence, Tuple
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.contracts.notebook import GLOBAL_SCOPE_ID
from study_engine.hierarchy.scope_resolver import ScopeNotFoundError, ScopeResolver, ScopeType
from study_engine.pedagogy.structured_pipeline import (
    PhaseHistory,
    StructuredResponsePipeline,
    resolve_epistemic_role,
)
from study_engine.pedagogy.dialogue_referent import (
    ReferentDecision,
    classify_dialogue_referent,
    referent_clarification_message,
    resolve_recent_referent,
)
from study_engine.utils.cache import TTLCache
from study_engine.web.dependencies import AppContainer, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Fixed arity for `_prepare_chat_context` / `chat_query` unpacking (P0).
# 0 resolved_scope, 1 contract, 2 context_pack, 3 raw_chunks, 4 folder_decision,
# 5 context_mode, 6 bkt_directive, 7 style_result, 8 conv_payload,
# 9 matched_kc_id, 10 bkt_meta
PREPARE_CONTEXT_ARITY = 11

FALLBACK_DISCLAIMER = (
    "No pude confirmar un concepto específico del cuaderno; respondo con base conceptual general de fuentes verificadas."
)

_MAX_RECENT_MESSAGES = 20
_MAX_RECENT_TURN_CHARS = 4000
_MAX_RECENT_HISTORY_CHARS = 12000


def _route_content_binding_matches(
    audited_content_hash: object,
    emitted_text: str,
    audited_binding_id: object,
    expected_binding_id: str,
) -> bool:
    """Return whether route output is exactly the text audited upstream."""
    if (
        not isinstance(audited_content_hash, str)
        or not isinstance(audited_binding_id, str)
        or not isinstance(expected_binding_id, str)
    ):
        return False
    return (
        audited_binding_id == expected_binding_id
        and hashlib.sha256(emitted_text.encode("utf-8")).hexdigest() == audited_content_hash
    )


def _bind_audit_event(event: dict, *, session_id: str, scope_type: str, scope_id: str, emission: str) -> dict:
    """Attach invocation identity only at the route's final emission boundary."""
    payload = dict(event["payload"])
    projection = payload.get("audit_projection")
    if projection is not None:
        payload["audit_projection"] = {
            **projection, "session_id": session_id,
            "scope_type": scope_type, "scope_id": scope_id,
            "decision": payload["verdict"], "emission": emission,
        }
    return {**event, "payload": payload}


def _style_directive_for_task(style_result: Any, task: str) -> Optional[str]:
    """Keep direct and comparative answers bounded by evidence and citations."""
    if style_result is None:
        return None
    style = getattr(style_result, "style", None)
    if (
        task == "comparar"
        and getattr(style, "value", style) == "FORMAL_EXPLANATION"
    ):
        return (
            "COMPARACIÓN ACADÉMICA CON EVIDENCIA:\n"
            "- Compará solo dimensiones presentes en las fuentes recuperadas; no agregues pros, "
            "contras, escenarios ni trade-offs inferidos.\n"
            "- Cada celda factual de la tabla debe incluir su cita [E#] válida en esa misma celda; "
            "cada frase factual fuera de la tabla requiere cita propia.\n"
            "- Si una dimensión no está documentada, omitila. No conviertas resistencia a cambios "
            "en garantía de equivalencia exacta."
        )
    if (
        task == "responder la consulta"
        and getattr(style, "value", style) == "FORMAL_EXPLANATION"
    ):
        return (
            "RESPUESTA BÁSICA ANCLADA EN EVIDENCIA:\n"
            "- Contestá directamente en pocas oraciones, sin secciones ni nivel de máquina obligatorio.\n"
            "- Cada oración declarativa que afirme un hecho técnico, incluidos los ejemplos, "
            "debe llevar su propio [E#] válido al final. Una cita de la oración anterior no se hereda.\n"
            "- Usá solo hechos y ejemplos respaldados por el fragmento citado; "
            "si un detalle no está respaldado, omitilo o declará que falta evidencia.\n"
            "- Si se pide una definición, limitate a las equivalencias y calificadores expresos de la fuente; "
            "no amplíes una definición con propiedades, sinónimos o consecuencias que el fragmento no establezca. "
            "Cuando el fragmento proporcione una equivalencia breve, conservá ese alcance y no la expandas.\n"
            "- No agregues ejemplos inventados para completar una plantilla."
        )
    return getattr(style_result, "instruction_directive", None)


def _sanitize_recent_turns(
    recent_turns: Optional[List[Dict[str, Any]]],
    *,
    current_prompt: str,
) -> List[Dict[str, str]]:
    """Normalize and bound untrusted client history to complete alternating turns."""
    role_aliases = {
        "user": "user",
        "student": "user",
        "assistant": "assistant",
        "tutor": "assistant",
    }
    normalized: List[Dict[str, str]] = []
    for turn in recent_turns or []:
        if not isinstance(turn, dict):
            continue
        role = role_aliases.get(str(turn.get("role", "")).strip().lower())
        content = turn.get("content")
        if role is None or not isinstance(content, str):
            continue
        content = content.strip()
        if not content:
            continue
        entry = {"role": role, "content": content[:_MAX_RECENT_TURN_CHARS]}
        if normalized and normalized[-1]["role"] == role:
            normalized[-1] = entry
        else:
            normalized.append(entry)

    if normalized and normalized[-1]["role"] == "user":
        if normalized[-1]["content"] == current_prompt.strip():
            normalized.pop()
        else:
            normalized.pop()

    bounded: List[Dict[str, str]] = []
    char_budget = _MAX_RECENT_HISTORY_CHARS
    for turn in reversed(normalized[-_MAX_RECENT_MESSAGES:]):
        if char_budget <= 0:
            break
        content = turn["content"][:char_budget]
        bounded.append({"role": turn["role"], "content": content})
        char_budget -= len(content)
    bounded.reverse()
    if bounded and bounded[0]["role"] == "assistant":
        bounded.pop(0)
    return bounded


def _resolve_conversation_turns(
    *,
    server_turns: Optional[List[Dict[str, Any]]],
    client_turns: Optional[List[Dict[str, Any]]],
    current_prompt: str,
) -> List[Dict[str, str]]:
    """Prefer this scope's server buffer; use sanitized client history only on cold start."""
    trusted_buffer = _sanitize_recent_turns(server_turns, current_prompt=current_prompt)
    if trusted_buffer:
        return trusted_buffer
    return _sanitize_recent_turns(client_turns, current_prompt=current_prompt)


def _conversation_context_metadata(
    *,
    server_turns: Optional[List[Dict[str, Any]]],
    client_turns: Optional[List[Dict[str, Any]]],
    resolved_turns: List[Dict[str, str]],
    current_prompt: str,
) -> Dict[str, Any]:
    """Describe which bounded history was used without exposing its contents."""
    sanitized_server = _sanitize_recent_turns(server_turns, current_prompt=current_prompt)
    sanitized_client = _sanitize_recent_turns(client_turns, current_prompt=current_prompt)
    if sanitized_server:
        source = "server"
    elif sanitized_client:
        source = "client"
    else:
        source = "none"

    def exceeded_limits(turns: Optional[List[Dict[str, Any]]]) -> bool:
        if not turns:
            return False
        if len(turns) > _MAX_RECENT_MESSAGES:
            return True
        if any(
            isinstance(turn, dict)
            and isinstance(turn.get("content"), str)
            and len(turn["content"]) > _MAX_RECENT_TURN_CHARS
            for turn in turns
        ):
            return True
        return sum(
            len(turn.get("content", ""))
            for turn in turns
            if isinstance(turn, dict) and isinstance(turn.get("content"), str)
        ) > _MAX_RECENT_HISTORY_CHARS

    return {
        "source": source,
        "turn_count": len(resolved_turns),
        "missing": source == "none",
        "truncated": exceeded_limits(server_turns) or exceeded_limits(client_turns),
    }


def _detect_evidence_discrepancies(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flag explicit polarity/version conflicts among retrieved evidence."""
    polarity = re.compile(
        r"\b(?:no|nunca|jam[aá]s|imposible|proh[ií]be|prohibido|"
        r"siempre|permite|permitido|obligatorio|requiere)\b",
        re.IGNORECASE,
    )
    version = re.compile(r"\b(?:v(?:ersi[oó]n)?\s*)?\d+(?:\.\d+){1,2}\b", re.IGNORECASE)
    findings: List[Dict[str, Any]] = []
    for index, left in enumerate(chunks):
        left_text = str(left.get("chunk_text") or "")
        left_terms = set(re.findall(r"[a-záéíóúñ]{5,}", left_text.lower()))
        for right in chunks[index + 1 :]:
            if left.get("source_id") == right.get("source_id"):
                continue
            right_text = str(right.get("chunk_text") or "")
            right_terms = set(re.findall(r"[a-záéíóúñ]{5,}", right_text.lower()))
            if len(left_terms & right_terms) < 2:
                continue
            left_polarity = set(item.lower() for item in polarity.findall(left_text))
            right_polarity = set(item.lower() for item in polarity.findall(right_text))
            version_conflict = bool(version.findall(left_text)) and bool(version.findall(right_text)) and (
                version.findall(left_text) != version.findall(right_text)
            )
            polarity_conflict = (
                ("no" in left_polarity and "permite" in right_polarity)
                or ("permite" in left_polarity and "no" in right_polarity)
                or ("nunca" in left_polarity and "siempre" in right_polarity)
                or ("siempre" in left_polarity and "nunca" in right_polarity)
                or ("prohibido" in left_polarity and "permitido" in right_polarity)
                or ("permitido" in left_polarity and "prohibido" in right_polarity)
            )
            if not (version_conflict or polarity_conflict):
                continue
            findings.append(
                {
                    "type": "version" if version_conflict else "polarity",
                    "scope": sorted(left_terms & right_terms)[:8],
                    "sources": [
                        {
                            "citation_id": left.get("citation_id") or left.get("id"),
                            "source_id": left.get("source_id"),
                            "page_start": left.get("page_start"),
                        },
                        {
                            "citation_id": right.get("citation_id") or right.get("id"),
                            "source_id": right.get("source_id"),
                            "page_start": right.get("page_start"),
                        },
                    ],
                }
            )
    return findings


def _protected_solutions_for_item(store: Any, item: Any) -> Optional[List[str]]:
    """Load protected answers through the explicit solution-only registry accessor."""
    registry = getattr(store, "content_registry", None)
    chunk_repository = getattr(store, "chunks", None)
    if registry is None or chunk_repository is None or not getattr(item, "solution_chunk_ids", None):
        return None
    try:
        chunks = registry.get_solution_chunks(item.content_id, chunk_repository)
    except sqlite3.Error:
        logger.exception("No se pudieron cargar las soluciones del ítem protegido %s", item.content_id)
        return None
    solutions = [
        content
        for chunk in chunks
        if isinstance((content := getattr(chunk, "content", None)), str) and content.strip()
    ]
    return solutions or None


def _epistemic_cache_key(
    *,
    session_id: Optional[str],
    scope_type: str,
    scope_id: str,
    notebook_id: str,
    active_sources: Optional[List[str]],
    requested_scope_id: Optional[str] = None,
) -> str:
    """Partition fallback evidence by session, resolved scope, and source restrictions."""
    key_parts = [
        session_id or "anon",
        scope_type,
        scope_id,
        notebook_id,
        requested_scope_id or "",
        sorted(set(active_sources or [])),
    ]
    return f"epistemic:{json.dumps(key_parts, ensure_ascii=False, separators=(',', ':'))}"


def _request_context_cache_key(
    request: "ChatQueryRequest",
    resolved_scope: Any,
    notebook_id: str,
) -> str:
    return _epistemic_cache_key(
        session_id=request.session_id,
        scope_type=resolved_scope.scope_type.value,
        scope_id=resolved_scope.scope_id,
        notebook_id=notebook_id,
        active_sources=request.active_sources,
        requested_scope_id=request.requested_scope_id,
    )


def _pack_prepare_context(
    resolved_scope: Any,
    *,
    contract: Any = None,
    context_pack: Any = None,
    raw_chunks: Optional[List[Any]] = None,
    folder_decision: Any = None,
    context_mode: Any = None,
    bkt_directive: Any = None,
    style_result: Any = None,
    conv_payload: Any = None,
    matched_kc_id: Any = None,
    bkt_meta: Any = None,
) -> Tuple[Any, Any, Any, List[Any], Any, Any, Any, Any, Any, Any, Any]:
    """Pack chat context-prep as a stable 11-tuple.

    Folder routing and conversational fast-path leave ``matched_kc_id`` and
    ``bkt_meta`` as ``None`` by design: greetings, follow-ups and folder
    organisational queries are not technical KC turns, so BKT is not computed.
    Those Nones are not a pending bug.
    """
    packed = (
        resolved_scope,
        contract,
        context_pack,
        [] if raw_chunks is None else raw_chunks,
        folder_decision,
        context_mode,
        bkt_directive,
        style_result,
        conv_payload,
        matched_kc_id,
        bkt_meta,
    )
    if len(packed) != PREPARE_CONTEXT_ARITY:
        raise RuntimeError(
            f"prepare-context contract broken: expected {PREPARE_CONTEXT_ARITY}, got {len(packed)}"
        )
    return packed


class ChatQueryRequest(BaseModel):
    """Payload for multi-phase streaming chat queries."""

    model_config = ConfigDict(strict=False)

    prompt: Optional[str] = Field(default=None, max_length=15000, description="Student message or technical prompt.")
    query: Optional[str] = Field(default=None, max_length=15000, description="Alternative field for user query.")
    scope_type: Optional[Literal["folder", "notebook"]] = Field(
        default=None, description="Target hierarchical scope type."
    )
    scope_id: Optional[str] = Field(default=None, description="Target scope identifier.")
    notebook_id: Optional[str] = Field(default=None, description="Alternative field for notebook scope.")
    requested_scope_id: Optional[str] = Field(
        default=None, description="Requested human-readable scope title or identifier."
    )
    session_id: Optional[str] = Field(
        default=None, description="Active interactive session ID if present."
    )
    requested_phase: Optional[
        Literal["conceptual", "pseudocode", "python_code", "verification", "socratic_question"]
    ] = Field(
        default="conceptual",
        description="Specific generation phase requested (defaults to 'conceptual').",
    )
    active_sources: Optional[List[str]] = Field(
        default=None,
        description="Optional list of authorized source identifiers or doc hashes to restrict retrieval.",
    )
    recent_turns: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional unverified client conversation context, sanitized before use.",
    )

    @property
    def effective_prompt(self) -> str:
        val = self.prompt or self.query or ""
        return val.strip()

    @property
    def effective_scope_type(self) -> Literal["folder", "notebook"]:
        raw_id = (self.scope_id or self.notebook_id or "").strip()
        if raw_id in ("root_global", "folder_root", "f_prog", "folder_fase0", "fadena", "roadmap", "fadena_1ano", "fadena_1ano_2cuat", "roadmap_fase0"):
            return "folder"
        if self.notebook_id in ("root_global", "folder_root", "f_prog", "folder_fase0"):
            return "folder"
        if self.scope_type in ("folder", "notebook"):
            return self.scope_type
        return "notebook"

    @property
    def effective_scope_id(self) -> str:
        raw_id = (self.scope_id or self.notebook_id or "").strip()
        if raw_id in ("root_global", "folder_root", ""):
            return "folder_root"
        return raw_id


# In-memory turn accumulator map with TTL eviction: (session_id or scope_id) -> PhaseHistory
_ACTIVE_TURN_HISTORIES: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)
_ACTIVE_PROTECTED_ASSESSMENTS: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)

# Buffer conversacional efímero, particionado por sesión y alcance.
# Conserva hasta 20 mensajes validados por clave de contexto.
_CONV_TURN_BUFFER: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)

# Almacena el último EpistemicContextPack exitoso particionado por sesión,
# alcance curricular y restricciones de fuentes.
_LAST_EPISTEMIC_PACK: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)

# Fase 5.3: racha de turnos consecutivos por KC por sesión/cuaderno —
# cuando llega a N turnos, TALOS propone un ejercicio certificado para
# cerrar el loop de evaluación.
_KC_TURN_STREAKS: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)

from study_engine.context.c5_trust import (
    EpistemicTrustStatus,
    evaluate_epistemic_trust,
    evaluate_conversational_rescue_compatibility,
    extract_critical_query_terms,
)

# Session Digest (Fase 5.4): la directiva de la sesión anterior se inyecta
# UNA sola vez por history_key (primer turno de la sesión).
_DIGEST_SHOWN: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)


class EpistemicContextPack:
    """Pack of epistemic context, citations and chunks for prompt augmentation."""

    def __init__(
        self,
        formatted_context: str,
        citations: list,
        chunks: list,
        abstained: bool = False,
        abstention_reason: Optional[str] = None,
        reference_disclaimer: Optional[str] = None,
        resolved_item: Optional[Any] = None,
        clarification_message: Optional[str] = None,
        trust_status: Optional[EpistemicTrustStatus] = None,
        is_sufficient: Optional[bool] = None,
        is_conflicting: bool = False,
        conflict_details: Optional[str] = None,
        missing_critical_terms: Optional[List[str]] = None,
        coverage_ratio: float = 0.0,
        max_relevance: float = 0.0,
    ):
        self.formatted_context = formatted_context
        self.citations = citations
        self.chunks = chunks
        self.abstained = abstained
        self.abstention_reason = abstention_reason
        self.reference_disclaimer = reference_disclaimer
        self.resolved_item = resolved_item
        self.clarification_message = clarification_message
        self.is_conflicting = is_conflicting
        self.conflict_details = conflict_details
        self.missing_critical_terms = missing_critical_terms or []
        self.coverage_ratio = coverage_ratio
        self.max_relevance = max_relevance

        if abstained:
            self.is_sufficient = False
            self.trust_status = trust_status or (
                EpistemicTrustStatus.RETRIEVAL_FAILURE
                if abstention_reason == "RETRIEVAL_FAILURE"
                else EpistemicTrustStatus.NO_EVIDENCE
            )
        else:
            if is_sufficient is not None:
                self.is_sufficient = is_sufficient
            else:
                self.is_sufficient = bool(chunks)
            if trust_status is not None:
                self.trust_status = trust_status
            else:
                self.trust_status = (
                    EpistemicTrustStatus.SUFFICIENT_EVIDENCE
                    if self.is_sufficient
                    else EpistemicTrustStatus.NO_EVIDENCE
                )


class OfflineKnowledgeBackend:
    """Offline pedagogical oracle backend with pure corpus retrieval (Fix S4.3)."""

    def __init__(self, knowledge_store: Optional[Any] = None) -> None:
        self.store = knowledge_store

    def __call__(self, prompt_bundle_or_query: Any) -> Any:
        if isinstance(prompt_bundle_or_query, str):
            from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
            from study_engine.contracts.generation import GenerationParameters
            bundle = PromptBundle(
                system_prompt="Oracle",
                messages=(PromptMessage(role=PromptRole.USER, content=prompt_bundle_or_query),),
                parameters=GenerationParameters(max_output_tokens=400),
                prompt_hash="0" * 64,
            )
            return self.complete(bundle)
        return self.complete(prompt_bundle_or_query)

    def generate_response(self, query: str, notebook_id: str = "fase0-soc") -> str:
        """Pure retrieval from knowledge store organized by pedagogical, formal, and technical layers."""
        # 1. Buscar los chunks más relevantes del corpus
        results: List[Any] = []
        if self.store is not None:
            try:
                allowed_srcs = sorted(_source_ids_for_notebook(self.store, notebook_id))
                if not allowed_srcs:
                    return (
                        f"TALOS se abstiene de responder: No se encontraron fuentes autorizadas en el cuaderno '{notebook_id}' "
                        f"para fundamentar una respuesta sobre '{query}'."
                    )
                if hasattr(self.store, "search_hybrid"):
                    results = self.store.search_hybrid(query, notebook_id=notebook_id, limit=5, source_ids=allowed_srcs)
                elif hasattr(self.store, "search"):
                    results = self.store.search(query, notebook_id=notebook_id, limit=5, source_ids=allowed_srcs)
            except Exception as e:
                logger.warning("Error en búsqueda de OfflineKnowledgeBackend: %s", e)
                results = []

        # 2. Si no hay chunks recuperados del store
        if not results:
            if self.store is not None:
                return (
                    f"TALOS se abstiene de responder: No se encontraron evidencias curriculares verificables en el cuaderno '{notebook_id}' "
                    f"para fundamentar una respuesta sobre '{query}'. Consultá el catálogo de fuentes del cuaderno o reformulá la consulta."
                )
            return (
                "### 1. Intuición Conceptual (Estilo Feynman)\n"
                f"Para comprender a fondo '{query}', el primer paso metodológico consiste en visualizar el modelo mental "
                "del problema concreto antes de pasar a la formulación abstracta o la sintaxis.\n\n"
                "### 2. Mecanismo y Formalismo Riguroso\n"
                f"En el entorno de estudio de '{notebook_id}', las definiciones formales y teoremas fundamentales "
                "se encuentran verificados en los textos de referencia de la cátedra. Cuando no se cuenta con chunks específicos indexados, "
                "se recomienda consultar el índice temático del cuaderno correspondiente.\n\n"
                "### 3. Nivel de Máquina e Implementación Práctica\n"
                "Toda abstracción de software tiene un correlato directo en el hardware: asignación de frames en la pila, "
                "punteros en memoria física y despacho de instrucciones en la CPU.\n\n"
                f"**Desafío Socrático:** ¿Qué consecuencias inmediatas en la consistencia del sistema ocurrirían si se violara la invariante de estado asociada a '{query}'?"
            )

        # 3. Organizar por rol de autor (Capa 1/2/3)
        from study_engine.pedagogy.structured_pipeline import AUTHOR_ROLES_BY_NOTEBOOK
        classified: Dict[str, List[Any]] = {"pedagogical": [], "formal": [], "technical": [], "other": []}
        
        nb_key = (notebook_id or "").lower().strip()
        matched_roles = None
        for key, role_dict in AUTHOR_ROLES_BY_NOTEBOOK.items():
            if key in nb_key or nb_key in key:
                matched_roles = role_dict
                break
        if not matched_roles:
            matched_roles = AUTHOR_ROLES_BY_NOTEBOOK.get("fase0-soc", {})

        for r in results:
            s_id = str(getattr(r, "source_id", "")).lower()
            assigned = False
            for role_name in ("pedagogical", "formal", "technical"):
                authors = matched_roles.get(role_name, [])
                if any(auth in s_id for auth in authors):
                    classified[role_name].append(r)
                    assigned = True
                    break
            if not assigned:
                classified["other"].append(r)

        # Distribuir chunks no asignados a capas vacías
        available = list(classified["other"])
        for role_name in ("pedagogical", "formal", "technical"):
            if not classified[role_name] and available:
                classified[role_name].append(available.pop(0))

        layer_texts: List[str] = []

        # Capa 1: Pedagógica / Intuición
        c1 = classified["pedagogical"][0] if classified["pedagogical"] else (results[0] if results else None)
        if c1:
            src = getattr(c1, "source_id", "Fuente")
            p = getattr(c1, "page_start", 1) or 1
            snip = getattr(c1, "snippet", "") or getattr(c1, "content", "")[:350]
            layer_texts.append(
                f"### 1. Intuición Conceptual y Analogía (Estilo Feynman)\n"
                f"{snip.strip()}\n\n*Evidencia pedagógica:* `{src}` (p. {p})"
            )
        else:
            layer_texts.append(
                "### 1. Intuición Conceptual y Analogía (Estilo Feynman)\n"
                f"La intuición fundamental de '{query}' radica en modelar el flujo de datos y estados de forma predecible."
            )

        # Capa 2: Formal / Mecanismo
        c2 = classified["formal"][0] if classified["formal"] else (results[1] if len(results) > 1 else c1)
        if c2:
            src = getattr(c2, "source_id", "Fuente")
            p = getattr(c2, "page_start", 1) or 1
            snip = getattr(c2, "snippet", "") or getattr(c2, "content", "")[:350]
            layer_texts.append(
                f"### 2. Mecanismo y Formalismo Riguroso\n"
                f"{snip.strip()}\n\n*Evidencia formal documentada en:* `{src}` (p. {p})"
            )
        else:
            layer_texts.append(
                "### 2. Mecanismo y Formalismo Riguroso\n"
                "El mecanismo formal impone invariantes de consistencia, restricciones de tipos y relaciones algebraicas deterministas."
            )

        # Capa 3: Técnica / Nivel de Máquina
        c3 = classified["technical"][0] if classified["technical"] else (results[2] if len(results) > 2 else c1)
        if c3:
            src = getattr(c3, "source_id", "Fuente")
            p = getattr(c3, "page_start", 1) or 1
            snip = getattr(c3, "snippet", "") or getattr(c3, "content", "")[:350]
            layer_texts.append(
                f"### 3. Nivel de Máquina e Implementación Práctica\n"
                f"{snip.strip()}\n\n*Especificación técnica en:* `{src}` (p. {p})"
            )
        else:
            layer_texts.append(
                "### 3. Nivel de Máquina e Implementación Práctica\n"
                "A nivel físico, las instrucciones se ejecutan en registros de la CPU, manipulan frames de pila o interactúan con llamadas al sistema."
            )

        # Cierre socrático dinámico anclado al contenido del chunk primario
        top_chunk = results[0]
        t_src = getattr(top_chunk, "source_id", "corpus")
        t_page = getattr(top_chunk, "page_start", 1) or 1
        socratic_challenge = (
            f"**Desafío Socrático:** A partir de los principios documentados en `{t_src}` (p. {t_page}) sobre '{query}', "
            f"¿qué consecuencias de rendimiento o consistencia surgirían si se modificara este comportamiento en un entorno de alta concurrencia?"
        )

        return "\n\n".join(layer_texts) + f"\n\n{socratic_challenge}"

    def complete(self, prompt_bundle: Any) -> Any:
        from study_engine.contracts.generation import TokenUsage
        from study_engine.llm.backends import ProviderCompletion
        msgs = getattr(prompt_bundle, "messages", [])
        user_queries = [
            m.content for m in msgs if getattr(m, "role", None) and str(getattr(m.role, "value", m.role)) == "user"
        ]
        q = (user_queries[-1] if user_queries else "").strip()

        # Extraer consulta limpia si viene con wrappers de prompt de fase
        if "=== CONSULTA DEL ESTUDIANTE ===" in q:
            match = re.search(r"=== CONSULTA DEL ESTUDIANTE ===\s*\n(.*?)(?:\n\n===|\Z)", q, re.DOTALL)
            clean_q = match.group(1).strip() if match else q
        else:
            clean_q = q

        from study_engine.pedagogy.command_parser import parse_student_command, CommandType
        cmd = parse_student_command(clean_q)
        if cmd is not None:
            if cmd.command_type == CommandType.DAME_UN_EJERCICIO:
                # Despacho determinista de ejercicio certificado QUALIFIABLE (E13)
                target_topic = cmd.target_arg
                store = getattr(self, "store", None)
                exercise = None
                exercise_store = None
                if hasattr(self, "exercise_store"):
                    exercise_store = getattr(self, "exercise_store")

                if exercise_store is None:
                    try:
                        from study_engine.pedagogy.exercise_store import ExerciseStore
                        exercise_store = ExerciseStore()
                    except Exception:
                        exercise_store = None

                if exercise_store:
                    all_qual = [ex for ex in exercise_store.list_all() if ex.is_presentable()]
                    if target_topic:
                        norm_t = target_topic.lower().strip()
                        matches = [
                            ex for ex in all_qual
                            if (ex.kc_id and norm_t in ex.kc_id.lower())
                            or (ex.prompt and norm_t in ex.prompt.lower())
                        ]
                        if matches:
                            exercise = matches[0]
                    elif all_qual:
                        exercise = all_qual[0]

                if exercise:
                    opts_text = ""
                    if exercise.options:
                        opts_text = "\n" + "\n".join(
                            f"{chr(65 + i)}) {opt}" for i, opt in enumerate(exercise.options)
                        )
                    ans = (
                        f"### Ejercicio Práctico Certificado [{exercise.kc_id}]\n\n"
                        f"{exercise.prompt}\n{opts_text}\n\n"
                        f"### Desafío Socrático:\n"
                        f"{exercise.prompt}{opts_text}\n\n"
                        f"*Ejercicio ID:* `{exercise.exercise_id}` | *Estado:* `QUALIFIABLE`"
                    )
                    return ProviderCompletion(
                        text=ans,
                        latency_ms=2.0,
                        tokens_used=TokenUsage(prompt_tokens=40, completion_tokens=80, total_tokens=120),
                        model="talos-exercise-dispatcher-v1",
                        generator_abstained=False,
                    )
                else:
                    # Fail-closed (E13): No hay ejercicio certificado para el tema solicitado
                    ans = (
                        f"TALOS se abstiene de evaluar: No existe actualmente un ejercicio con clave "
                        f"certificada en el backend para el tema '{target_topic or 'solicitado'}'.\n\n"
                        f"Para no comprometer la validez de tu modelo cognitivo (BKT), solo se despachan "
                        f"desafíos certificados de la bibliografía canónica. Podés explorar otros conceptos o consultar los textos oficiales."
                    )
                    return ProviderCompletion(
                        text=ans,
                        latency_ms=2.0,
                        tokens_used=TokenUsage(prompt_tokens=30, completion_tokens=60, total_tokens=90),
                        model="talos-exercise-dispatcher-v1",
                        generator_abstained=True,
                    )

            if cmd.is_structured:
                ans = (
                    "No puedo generar una respuesta estructurada sin el motor de IA activo.\n\n"
                    "Verificá que el proveedor LLM esté conectado y volvé a intentar.\n\n"
                    "Mientras tanto, podés consultar directamente las fuentes del cuaderno "
                    "en el panel de fuentes curriculares."
                )
                return ProviderCompletion(
                    text=ans,
                    latency_ms=5.0,
                    tokens_used=TokenUsage(prompt_tokens=40, completion_tokens=50, total_tokens=90),
                    model="talos-offline-oracle-v2",
                    generator_abstained=True,
                )

        ans = self.generate_response(clean_q)
        is_abstained = "TALOS se abstiene de responder" in ans
        return ProviderCompletion(
            text=ans,
            latency_ms=10.0,
            tokens_used=TokenUsage(prompt_tokens=80, completion_tokens=180, total_tokens=260),
            model="talos-offline-oracle-v2",
            generator_abstained=is_abstained,
        )


def _handle_folder_streaming(decision: Dict[str, Any]) -> StreamingResponse:
    """Stream folder organizational responses via SSE."""
    async def folder_event_stream() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'event_type': 'phase_start', 'payload': {'phase': 'folder_organizational'}})}\n\n"
        msg = decision["message"]
        for word in msg.split(" "):
            await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'event_type': 'phase_token', 'payload': {'phase': 'folder_organizational', 'token': word + ' '}})}\n\n"
        yield f"data: {json.dumps({'event_type': 'phase_complete', 'payload': {'completed_phase': 'folder_organizational', 'decision': decision}})}\n\n"

    return StreamingResponse(folder_event_stream(), media_type="text/event-stream")


def _resolve_chat_backend(container: AppContainer, estimated_tokens: Optional[int] = None) -> Any:
    """Determine active LLM backend from container or fall back to offline oracle.

    If estimated_tokens is provided and container provides select_provider_tier,
    dynamically reorders the cascade so large prompts (>5000 tokens) route
    directly to Gemini/Cloudflare without bouncing on Groq's 7k ITPM rate limit.
    """
    llm_backend = getattr(container, "llm_backend", None)
    if llm_backend is not None:
        if estimated_tokens is not None and hasattr(container, "select_provider_tier"):
            try:
                from study_engine.llm.multi_fallback import MultiFallbackBackend
                ordered = container.select_provider_tier(estimated_tokens)
                return MultiFallbackBackend(
                    providers=ordered,
                    timeout_per_provider=llm_backend.timeout_per_provider,
                    provider_timeouts=getattr(llm_backend, "provider_timeouts", None),
                )
            except Exception as e:
                logger.debug("Error adaptando backend por tokens: %s", e)
        return llm_backend
    if hasattr(container.controller, "tutor_policy") and hasattr(container.controller.tutor_policy, "generator"):
        return container.controller.tutor_policy.generator
    return OfflineKnowledgeBackend(knowledge_store=getattr(container, "knowledge_store", None))


# Heurística de amplitud de consulta (Semana 1 - Calibración Chat):
# preguntas específicas (un concepto puntual) -> contexto chico y preciso;
# preguntas amplias (resúmenes, unidades, mapas, repasos) -> contexto ancho
# al estilo NotebookLM (más fuentes y chunks recuperados).
_BROAD_QUERY_PATTERN = re.compile(
    r"\b(resumen|resumime|resumime|sinte[sz]is|sintetiz[áa]|unidad|cap[íi]tulo|mapa|"
    r"repaso|repas[ée]o|temario|programa|[íi]ndice|overview|repasemos|"
    r"todos? los temas|temas principales|puntos clave|ideas principales|"
    r"qu[ée] vimos|de qu[ée] trata|recorrido|panorama|compar[áa] todo)\b",
    re.IGNORECASE,
)


def _resolve_retrieval_depth(prompt_text: str) -> Tuple[int, int]:
    """Return (limit, min_sources) for retrieval according to query breadth.

    - Consulta de depuración / crash / segfault: 8 chunks, >=2 fuentes (evita sobre-expansión y timeout).
    - Consulta amplia (resumen, repaso de unidad, panorama): 25 chunks, >=4 fuentes.
    - Consulta específica (déficit de un concepto, cómo se hace X): 15 chunks, >=3 fuentes.
    """
    q = (prompt_text or "").strip().lower()
    if re.search(r"\b(?:falla|crashea|segfault|crash|segmentation\s+fault|se\s+rompe|puntero\s+salvaje|wild\s+pointer)\b", q):
        return 8, 2
    if len(q) >= 220 or _BROAD_QUERY_PATTERN.search(q):
        return 25, 4
    return 15, 3


# M1-03 §1: parámetros del pase de recuperación dirigido por cobertura.
# Una query multi-aspecto con conjunción FTS estricta puede resolver 0 hits
# y que el fallback disyuntivo seleccione chunks por conteo de términos
# incidentales (≥2), dejando fuera los pasajes tópicos que cubren el término
# distintivo de la pregunta (hallazgo 2026-10-21: 'aritmética de punteros'
# existía en 66 chunks vinculados de Joyanes y el top-15 NO trajo ninguno;
# el gate C5 abstuvo por términos críticos presentes EN EL CORPUS pero
# ausentes EN LA SELECCIÓN). La pasada añade deterministamente los chunks
# que cubren los términos críticos aún descubiertos, con el MISMO índice
# FTS, la MISMA allowlist de fuentes autorizadas y el filtro anti-leakage
# obligatorio. No relaja umbrales ni fabrica evidencia: amplía recall para
# que el gate falle cerrado con información completa, no con la seleccion
# sesgada de una sóla pasada.
_COVERAGE_RECOVERY_PER_TERM_LIMIT = 4
_COVERAGE_RECOVERY_MAX_TERMS = 8

_COVERAGE_RECOVERY_SKIP_TERMS = re.compile(r"^\d+%?$")


def _recover_coverage_gaps(
    store: Any,
    results: List[Any],
    coverage_query: str,
    authorized_source_ids: Collection[str],
    notebook_id: Optional[str],
) -> List[Any]:
    """Recupera chunks aún no recuperados que cubren términos críticos faltantes.

    Determinista: usa extract_critical_query_terms / evaluate_term_coverage
    del propio gate C5 (misma identidad de política, cero drift) para
    detectar el hueco de cobertura de la selección actual y completa el
    recall con consultas léxicas dirigidas por término sobre fuentes
    autorizadas. Devuelve NUEVOS resultados (dedupe por chunk_id) ya
    filtrados por presentation_filter; nunca modifica los originales.
    """
    try:
        from study_engine.context.c5_trust import (
            evaluate_term_coverage,
            extract_critical_query_terms,
            retrieval_variants_for_term,
        )
        from study_engine.retrieval.presentation_filter import filter_presentation
    except ImportError:  # pragma: no cover
        return []

    q = (coverage_query or "").strip()
    if not q or not authorized_source_ids:
        return []

    terms = extract_critical_query_terms(q)
    if not terms:
        return []

    seen_ids: set[str] = set()
    for r in results:
        chunk_key = getattr(r, "chunk_id", None) or getattr(r, "id", None)
        if chunk_key:
            seen_ids.add(chunk_key)

    cov, missing = evaluate_term_coverage(terms, results)
    if not missing:
        return []

    recoverable = [t for t in missing if not _COVERAGE_RECOVERY_SKIP_TERMS.match(t)]
    recoverable = recoverable[:_COVERAGE_RECOVERY_MAX_TERMS]
    if not recoverable:
        return []

    source_ids_param = sorted({s for s in authorized_source_ids if s})
    recovered: List[Any] = []
    recovered_keys: set[str] = set()
    registry = getattr(store, "content_registry", None)

    for term in recoverable:
        for variant in retrieval_variants_for_term(term):
            try:
                extra = store.search(
                    query=variant,
                    notebook_id=notebook_id,
                    limit=_COVERAGE_RECOVERY_PER_TERM_LIMIT,
                    source_ids=source_ids_param,
                )
            except Exception:
                logger.debug("Cobertura: búsqueda dirigida falló para %r", variant, exc_info=True)
                continue
            new_items = []
            for item in extra or []:
                key = getattr(item, "chunk_id", None) or getattr(item, "id", None)
                if not key or key in seen_ids or key in recovered_keys:
                    continue
                recovered_keys.add(key)
                new_items.append(item)
            if new_items and registry is not None:
                try:
                    new_items, _sol = filter_presentation(new_items, registry)
                except Exception:
                    logger.warning("Cobertura: presentation_filter falló; término %r sin aporte", variant)
                    new_items = []
            recovered.extend(new_items)
            if recovered and evaluate_term_coverage(terms, list(results) + recovered)[1] == []:
                break  # cobertura completa del término pendiente
        # El desambiguado entre candidatos idénticos por contenido es estable
        # por orden de llegada determinista (orden del índice).

    return recovered


def _notebook_ids_for_folder(store: Any, folder_id: str) -> List[str]:
    """Return notebooks explicitly placed in a folder or one of its descendants."""
    with store.engine.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            WITH RECURSIVE scope_folders(id) AS (
                SELECT id FROM folders WHERE id = ?
                UNION
                SELECT child.id
                FROM folders child
                JOIN scope_folders parent ON child.parent_folder_id = parent.id
            )
            SELECT DISTINCT notebooks.id
            FROM notebooks
            JOIN scope_folders ON notebooks.folder_id = scope_folders.id
            JOIN notebook_sources ON notebook_sources.notebook_id = notebooks.id
            ORDER BY notebooks.id;
            """,
            (folder_id,),
        )
        return [row[0] for row in cursor.fetchall()]


def _source_ids_for_notebook(store: Any, notebook_id: str) -> set[str]:
    with store.engine.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT source_id FROM notebook_sources WHERE notebook_id = ? ORDER BY source_id;",
            (notebook_id,),
        )
        tech_sources = {row[0] for row in cursor.fetchall()}

    manifest_path = getattr(store, "l3_manifest_path", None)
    from pathlib import Path
    if not isinstance(manifest_path, (str, Path)):
        manifest_path = None

    from study_engine.contracts.l3_manifest import get_l3_authorized_sources
    return tech_sources.intersection(get_l3_authorized_sources(notebook_id, manifest_path=manifest_path))


def _search_chapter_summaries_for_scope(
    store: Any,
    query: str,
    target_notebook_id: str,
    global_folder_id: Optional[str],
    authorized_source_ids: set[str],
    limit: int,
) -> List[Any]:
    """Search chapter summaries only in notebooks reachable from this scope."""
    notebook_ids = (
        _notebook_ids_for_folder(store, global_folder_id)
        if target_notebook_id == GLOBAL_SCOPE_ID and global_folder_id
        else [target_notebook_id]
    )
    summaries: List[Any] = []
    for notebook_id in notebook_ids:
        notebook_sources = _source_ids_for_notebook(store, notebook_id)
        if not notebook_sources.intersection(authorized_source_ids):
            continue
        summaries.extend(
            summary
            for summary in store.search_chapter_summaries(
                query=query,
                notebook_id=notebook_id,
                limit=limit,
            )
            if summary.source_id in authorized_source_ids
        )
    summaries.sort(key=lambda summary: summary.score or 0.0, reverse=True)
    return summaries[:limit]


def _authorized_sources_for_scope(
    store: Any,
    target_notebook_id: str,
    global_folder_id: Optional[str],
) -> set[str]:
    """Resolve the source allowlist from explicit notebook-source links intersected with L3 authorization manifest."""
    if target_notebook_id == GLOBAL_SCOPE_ID:
        if not global_folder_id:
            raise ValueError("Global retrieval requires its resolved folder scope")
        notebook_ids = _notebook_ids_for_folder(store, global_folder_id)
    else:
        notebook_ids = [target_notebook_id]
    if not notebook_ids:
        return set()

    effective_sources: set[str] = set()
    for nb_id in notebook_ids:
        effective_sources.update(_source_ids_for_notebook(store, nb_id))
    return effective_sources


def _filter_requested_sources(
    authorized_source_ids: set[str],
    requested_sources: Optional[List[str]],
    source_metadata: Dict[str, Dict[str, str]],
) -> set[str]:
    """Resolve optional source IDs or hashes only inside a server-owned allowlist."""
    if requested_sources is None:
        return set(authorized_source_ids)
    requested = set(requested_sources)
    return {
        source_id
        for source_id in authorized_source_ids
        if source_id in requested
        or source_metadata.get(source_id, {}).get("sha256") in requested
    }


def _trust_level_from_manifest(manifest_json: object) -> str:
    """Resolve S4.4 source trust from persisted provenance; unknown values fail closed.

    This mirrors EvidenceEngine's existing manifest contract: registered source
    manifests default to canonical unless explicitly marked unverified. The
    source must separately pass the notebook/L3 allowlist before this value is
    attached to a retrieved citation.
    """
    if not isinstance(manifest_json, str) or not manifest_json.strip():
        return "unverified"
    try:
        manifest = json.loads(manifest_json)
    except (TypeError, ValueError):
        return "unverified"
    metadata = manifest.get("metadata") if isinstance(manifest, dict) else None
    trust_level = metadata.get("trust_level", "canonical") if isinstance(metadata, dict) else None
    return trust_level if trust_level in {"canonical", "unverified"} else "unverified"


def _iter_pack_source_ids(pack: Any) -> set[str]:
    """Extract source IDs from a cached pack without trusting the pack implicitly."""
    if pack is None:
        return set()
    source_ids: set[str] = set()
    for citation in getattr(pack, "citations", []) or []:
        source_id = getattr(citation, "source_id", None)
        if isinstance(source_id, str) and source_id.strip():
            source_ids.add(source_id.strip())
    for chunk in getattr(pack, "chunks", []) or []:
        if isinstance(chunk, dict):
            source_id = chunk.get("source_id")
        else:
            source_id = getattr(chunk, "source_id", None)
        if isinstance(source_id, str) and source_id.strip():
            source_ids.add(source_id.strip())
    return source_ids


def _is_authorized_reusable_pack(
    pack: Any,
    chunks: Sequence[Any],
    *,
    store: Any,
    target_notebook_id: str,
    global_folder_id: Optional[str],
) -> bool:
    """Only reuse a pack when all provenance is still tied to currently authorized sources."""
    if pack is None or not getattr(pack, "formatted_context", None) and not chunks:
        return False
    # Bridge evidence must be replanned, even when its source also belongs to the active notebook.
    if any(isinstance(c, dict) and c.get("bridge_id") for c in list(getattr(pack, "chunks", []) or []) + list(chunks or [])):
        return False

    try:
        authorized_sources = _authorized_sources_for_scope(store, target_notebook_id, global_folder_id)
    except Exception:
        return False
    if not authorized_sources:
        return False

    pack_source_ids = _iter_pack_source_ids(pack)
    chunk_source_ids = set()
    for chunk in chunks or []:
        if isinstance(chunk, dict):
            source_id = chunk.get("source_id")
        else:
            source_id = getattr(chunk, "source_id", None)
        if isinstance(source_id, str) and source_id.strip():
            chunk_source_ids.add(source_id.strip())

    candidate_sources = pack_source_ids | chunk_source_ids
    if not candidate_sources:
        return False
    return candidate_sources.issubset(authorized_sources)


def _federated_source_ids(
    store: Any, planner: Any, plan: Any, subquery: Any,
    active_sources: Optional[List[str]], source_metadata: Dict[str, Dict[str, str]],
) -> set[str]:
    """Consume a planner target without treating a bridge as source authorization."""
    target = subquery.target_notebook_id
    constraint = subquery.scope_constraint
    # The current planner emits notebook-only constraints; never silently drop a new bound.
    if constraint.model_dump(exclude_none=True) != {
        "notebook_id": target, "bridge_id": subquery.bridge_id,
    }:
        raise ValueError("Unsupported federated retrieval constraint")
    notebook = planner.notebook_registry.get_notebook(target)
    authorized, _, bridge = planner.bridge_registry.is_bridge_authorized(
        plan.active_notebook_id, target, subquery.topic,
    )
    if (
        notebook is None or not notebook.is_active
        or subquery.topic not in notebook.authority_matrix_ref
        or not authorized or bridge is None or bridge.bridge_id != subquery.bridge_id
    ):
        raise ValueError("Federated bridge is not currently authorized")
    from study_engine.contracts.l3_manifest import get_l3_authorized_sources

    sources = _filter_requested_sources(
        _authorized_sources_for_scope(store, target, None).intersection(
            get_l3_authorized_sources(target, manifest_path=getattr(store, "l3_manifest_path", None)),
        ), active_sources, source_metadata,
    )
    if not sources:
        raise ValueError("No authorized sources for federated target")
    return sources


def _merge_federated_results(
    store: Any, planner: Any, plan: Any, local_results: List[Any],
    active_sources: Optional[List[str]], source_metadata: Dict[str, Dict[str, str]],
) -> Tuple[List[Any], Dict[str, Any]]:
    """Retrieve scoped targets and materialize identities before the existing C5/S4.4 path."""
    from study_engine.federation.federated_query_planner import FederatedRetrievalCandidate
    from study_engine.retrieval.presentation_filter import filter_presentation

    candidates = []

    def add_results(results, notebook_id, source_ids, authority_weight, bridge_id=None):
        for result in results:
            chunk = store.get_chunk(result.chunk_id)
            meta = source_metadata.get(result.source_id, {})
            if (
                chunk is None or result.source_id not in source_ids
                or (chunk.source_id, chunk.document_id, chunk.content, chunk.page_start, chunk.page_end)
                != (result.source_id, result.document_id, result.content, result.page_start, result.page_end)
                or not re.fullmatch(r"[a-fA-F0-9]{64}", meta.get("sha256", ""))
                or meta.get("trust_level") != "canonical"
            ):
                raise ValueError("Inconsistent federated evidence identity or provenance")
            with store.engine.transaction() as conn:
                source = conn.execute(
                    "SELECT sha256, manifest_json FROM sources WHERE source_id = ?", (result.source_id,),
                ).fetchone()
            if source is None or source[0] != meta["sha256"] or _trust_level_from_manifest(source[1]) != "canonical":
                raise ValueError("Federated source provenance changed during retrieval")
            candidates.append(FederatedRetrievalCandidate(
                chunk_id=result.chunk_id, doc_id=result.document_id,
                notebook_id=notebook_id, content=result.content,
                content_hash=hashlib.sha256(result.content.strip().encode("utf-8")).hexdigest(),
                authority_weight=authority_weight, retrieval_score=result.score,
                bridge_id=bridge_id, metadata={"result": result},
            ))

    local_sources = _filter_requested_sources(
        _authorized_sources_for_scope(store, plan.active_notebook_id, None), active_sources, source_metadata,
    )
    local_weight = max(
        sq.authority_weight for sq in plan.subqueries
        if sq.target_notebook_id == plan.active_notebook_id
    )
    add_results(local_results, plan.active_notebook_id, local_sources, local_weight)
    limit, min_sources = _resolve_retrieval_depth(plan.original_query)
    for subquery in plan.subqueries:
        if subquery.target_notebook_id == plan.active_notebook_id:
            continue
        source_ids = _federated_source_ids(
            store, planner, plan, subquery, active_sources, source_metadata,
        )
        results = store.search_hybrid(
            query=subquery.query_text, notebook_id=subquery.target_notebook_id,
            limit=limit, min_sources=min_sources, source_ids=sorted(source_ids),
        )
        results = list(results) + _recover_coverage_gaps(
            store=store, results=results, coverage_query=subquery.query_text,
            authorized_source_ids=source_ids, notebook_id=subquery.target_notebook_id,
        )
        if not results:
            raise ValueError("Federated target returned no evidence")
        add_results(results, subquery.target_notebook_id, source_ids, subquery.authority_weight, subquery.bridge_id)

    # Recheck TTL/revocation after all I/O, not just when the plan was constructed.
    for subquery in plan.subqueries:
        if subquery.target_notebook_id == plan.active_notebook_id:
            continue
        current_sources = _federated_source_ids(
            store, planner, plan, subquery, active_sources, source_metadata,
        )
        if any(
            c.notebook_id == subquery.target_notebook_id
            and c.metadata["result"].source_id not in current_sources for c in candidates
        ):
            raise ValueError("Federated source authorization changed during retrieval")
    deduplicated = planner.deduplicate_candidates(candidates)
    results, _ = filter_presentation([c.metadata["result"] for c in deduplicated], store.content_registry)
    return results, {c.chunk_id: c for c in deduplicated}


def _assemble_epistemic_context(
    store: Any,
    container: AppContainer,
    prompt_text: str,
    target_notebook_id: str,
    active_sources: Optional[List[str]] = None,
    granularity_decision: Optional[Any] = None,
    global_folder_id: Optional[str] = None,
    original_user_query: Optional[str] = None,
) -> Tuple[Optional[EpistemicContextPack], list]:
    """Search knowledge store and build formatted citations and chunks with SectionExpander (Ola 5)."""
    try:
        citations_formatted: list[str] = []
        raw_chunks: list[dict] = []

        from study_engine.pedagogy.command_parser import parse_student_command, CommandType
        cmd = parse_student_command(prompt_text)
        search_query = prompt_text
        if cmd is not None and cmd.target_arg:
            search_query = cmd.target_arg

        from study_engine.retrieval.reference_extractor import extract_reference
        from study_engine.retrieval.presentation_filter import filter_presentation
        from study_engine.contracts.content_registry import ContentStatus, UnitType
        from study_engine.contracts.search import SearchResult

        known_ids = []
        if hasattr(store, "content_registry") and store.content_registry:
            try:
                known_items = store.content_registry.list_all()
                known_ids = [it.content_id for it in known_items]
            except Exception as e:
                logger.debug("Error listing known content items: %s", e)
                known_ids = []

        ref_res = extract_reference(search_query, known_content_ids=known_ids)
        resolved_item = None
        reference_disclaimer = None

        if ref_res is not None and ref_res.matched:
            if ref_res.confidence >= 0.95 and ref_res.status == ContentStatus.OK and ref_res.content_id:
                if hasattr(store, "content_registry") and store.content_registry:
                    resolved_item = store.content_registry.get(ref_res.content_id)
            if resolved_item is None:
                raw_ref_str = ref_res.raw_ref or ref_res.content_id or "contenido solicitado"
                reference_disclaimer = f"No puedo confirmar que esto sea exactamente el {raw_ref_str}; te respondo basándome en el tema general de las fuentes verificadas."

        src_meta_cache: Dict[str, Dict[str, str]] = {}
        try:
            with store.engine.transaction() as conn:
                cur = conn.cursor()
                cur.execute("SELECT source_id, title, sha256, author, manifest_json FROM sources;")
                for row in cur.fetchall():
                    src_meta_cache[row[0]] = {
                        "title": row[1] or row[0],
                        "sha256": row[2] or "",
                        "author": row[3] or "",
                        "trust_level": _trust_level_from_manifest(row[4]),
                    }
        except Exception as meta_err:
            logger.warning("Fallo al consultar metadatos de fuentes: %s", meta_err)

        federated_plan = None
        planner = vars(container).get("federated_query_planner")
        if (
            planner is not None and target_notebook_id != GLOBAL_SCOPE_ID and resolved_item is None
            and planner.notebook_registry.get_notebook(target_notebook_id) is not None
        ):
            federated_plan = planner.plan_query(target_notebook_id, search_query)
            if (
                federated_plan.status != "READY"
                or federated_plan.active_notebook_id != target_notebook_id
                or federated_plan.original_query != search_query.strip()
            ):
                raise ValueError(f"Federated planning rejected: {federated_plan.guardrail_code}")

        try:
            scope_source_ids = _authorized_sources_for_scope(
                store,
                target_notebook_id,
                global_folder_id,
            )
            if federated_plan is not None and federated_plan.is_cross_curricular:
                for subquery in federated_plan.subqueries:
                    if subquery.target_notebook_id != target_notebook_id:
                        scope_source_ids.update(_federated_source_ids(
                            store, planner, federated_plan, subquery, active_sources, src_meta_cache,
                        ))
        except Exception:
            logger.exception(
                "Cannot resolve source allowlist for scope %s; retrieval is closed",
                target_notebook_id,
            )
            return EpistemicContextPack(
                formatted_context="",
                citations=[],
                chunks=[],
                abstained=True,
                abstention_reason="SCOPE_AUTHORIZATION_UNAVAILABLE",
                trust_status=EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
                is_sufficient=False,
            ), []

        retrieval_source_ids = _filter_requested_sources(
            scope_source_ids,
            active_sources,
            src_meta_cache,
        )

        if not retrieval_source_ids:
            return EpistemicContextPack(
                formatted_context="",
                citations=[],
                chunks=[],
                abstained=True,
                abstention_reason=(
                    "NO_AUTHORIZED_ACTIVE_SOURCES"
                    if active_sources is not None
                    else "NO_AUTHORIZED_SOURCES_IN_SCOPE"
                ),
                trust_status=EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
                is_sufficient=False,
            ), []

        search_results = []
        if resolved_item is not None:
            chunk_repo = getattr(store, "chunks", None) or getattr(getattr(store, "repositories", None), "chunks", None)
            stmt_chunks, had_sol = store.content_registry.get_statement_chunks(resolved_item.content_id, chunk_repo)
            if not stmt_chunks and had_sol:
                return EpistemicContextPack(
                    formatted_context="",
                    citations=[],
                    chunks=[],
                    abstained=True,
                    abstention_reason="QUERY_OUT_OF_SCOPE",
                    reference_disclaimer=reference_disclaimer,
                    resolved_item=resolved_item,
                    trust_status=EpistemicTrustStatus.NO_EVIDENCE,
                    is_sufficient=False,
                ), []
            if stmt_chunks:
                for rank, chk in enumerate(stmt_chunks):
                    chk_content = getattr(chk, "content", "")
                    sr = SearchResult(
                        content=chk_content,
                        index=getattr(chk, "index", rank) or rank,
                        chunk_id=getattr(chk, "id", None),
                        document_id=getattr(chk, "document_id", None),
                        source_id=getattr(chk, "source_id", resolved_item.source_id),
                        snippet=chk_content[:200],
                        page_start=getattr(chk, "page_start", None),
                        page_end=getattr(chk, "page_end", None),
                        score=1.0,
                    )
                    search_results.append(sr)

        if not search_results:
            from study_engine.retrieval.granularity_router import RetrievalGranularity, GranularityRouter

            gran_mode = getattr(granularity_decision, "granularity", None) if granularity_decision else None

            if gran_mode == RetrievalGranularity.MACRO and hasattr(store, "search_chapter_summaries"):
                max_parents = getattr(granularity_decision, "max_parent_nodes", 2)
                try:
                    ch_summaries = _search_chapter_summaries_for_scope(
                        store,
                        search_query,
                        target_notebook_id,
                        global_folder_id,
                        retrieval_source_ids,
                        max_parents,
                    )
                    for rank, cs in enumerate(ch_summaries):
                        sr = SearchResult(
                            content=cs.summary_text,
                            index=rank,
                            chunk_id=cs.id,
                            document_id="chapter_summary",
                            source_id=cs.source_id,
                            snippet=f"[{cs.title}] {cs.summary_text[:200]}",
                            page_start=cs.page_start,
                            page_end=cs.page_end,
                            score=cs.score or 1.0,
                        )
                        search_results.append(sr)
                except Exception as macro_err:
                    logger.debug("Error in search_chapter_summaries (MACRO): %s", macro_err)

            elif gran_mode == RetrievalGranularity.HYBRID and hasattr(store, "search_chapter_summaries"):
                max_parents = getattr(granularity_decision, "max_parent_nodes", 1)
                max_leaves = getattr(granularity_decision, "max_leaf_chunks", 3)
                top_parent = None
                preferred_cid = None
                try:
                    ch_summaries = _search_chapter_summaries_for_scope(
                        store,
                        search_query,
                        target_notebook_id,
                        global_folder_id,
                        retrieval_source_ids,
                        max_parents,
                    )
                    if ch_summaries:
                        top_parent = ch_summaries[0]
                        preferred_cid = top_parent.id
                except Exception as hy_ch_err:
                    logger.debug("Error searching parent summaries in HYBRID: %s", hy_ch_err)

                retrieval_limit, min_sources = _resolve_retrieval_depth(search_query)
                leaf_candidates = []
                if hasattr(store, "search_hybrid"):
                    notebook_ids = (
                        _notebook_ids_for_folder(store, global_folder_id)
                        if target_notebook_id == GLOBAL_SCOPE_ID and global_folder_id
                        else [target_notebook_id]
                    )
                    for notebook_id in notebook_ids:
                        notebook_source_filter = sorted(
                            _source_ids_for_notebook(store, notebook_id).intersection(
                                retrieval_source_ids
                            )
                        )
                        if not notebook_source_filter:
                            continue
                        try:
                            leaf_candidates.extend(
                                store.search_hybrid(
                                    query=search_query,
                                    notebook_id=notebook_id,
                                    limit=max_leaves * 2,
                                    min_sources=min_sources,
                                    preferred_chapter_id=preferred_cid,
                                    source_ids=notebook_source_filter,
                                )
                            )
                        except Exception as hy_leaf_err:
                            logger.warning(
                                "Error in scoped search_hybrid for notebook %s: %s",
                                notebook_id,
                                hy_leaf_err,
                            )
                    leaf_candidates.sort(
                        key=lambda candidate: getattr(candidate, "score", 0.0),
                        reverse=True,
                    )
                    leaf_candidates = leaf_candidates[: max_leaves * 2]

                deduped = GranularityRouter.deduplicate_hybrid_chunks(
                    candidate_chunks=leaf_candidates,
                    parent_summary=top_parent,
                    similarity_threshold=0.85,
                    max_leaves=max_leaves,
                )

                if top_parent:
                    sr_parent = SearchResult(
                        content=top_parent.summary_text,
                        index=0,
                        chunk_id=top_parent.id,
                        document_id="chapter_summary",
                        source_id=top_parent.source_id,
                        snippet=f"[{top_parent.title}] {top_parent.summary_text[:200]}",
                        page_start=top_parent.page_start,
                        page_end=top_parent.page_end,
                        score=top_parent.score or 1.0,
                    )
                    search_results.append(sr_parent)
                search_results.extend(deduped)

        if not search_results:
            retrieval_limit, min_sources = _resolve_retrieval_depth(search_query)
            gran_mode = getattr(granularity_decision, "granularity", None) if granularity_decision else None
            if gran_mode == RetrievalGranularity.MICRO and getattr(granularity_decision, "max_leaf_chunks", None):
                retrieval_limit = min(retrieval_limit, granularity_decision.max_leaf_chunks)
            if target_notebook_id == GLOBAL_SCOPE_ID:
                # Scope global: fundir por chunk_id el retrieval de notebooks
                # asociados al folder seleccionado.
                try:
                    all_notebooks = (
                        _notebook_ids_for_folder(store, global_folder_id)
                        if global_folder_id
                        else []
                    )
                except Exception as nb_err:
                    logger.exception(
                        "No se pudo resolver notebooks autorizados para scope global: %s",
                        nb_err,
                    )
                    all_notebooks = []

                from concurrent.futures import ThreadPoolExecutor, as_completed

                def _search_single_nb(nb_id: str) -> List[Any]:
                    try:
                        notebook_source_filter = sorted(
                            _source_ids_for_notebook(store, nb_id).intersection(
                                retrieval_source_ids
                            )
                        )
                        if not notebook_source_filter:
                            return []
                        return store.search_hybrid(
                            query=search_query,
                            notebook_id=nb_id,
                            limit=retrieval_limit,
                            min_sources=min_sources,
                            source_ids=notebook_source_filter,
                        ) if hasattr(store, "search_hybrid") else store.search(
                            query=search_query,
                            notebook_id=nb_id,
                            limit=retrieval_limit,
                            source_ids=notebook_source_filter,
                        )
                    except Exception as nb_search_err:
                        logger.debug("Scope global: fallo retrieval en %s: %s", nb_id, nb_search_err)
                        return []

                merged: Dict[str, Tuple[int, Any]] = {}
                workers = min(len(all_notebooks), 8) if all_notebooks else 1
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    future_to_nb = {executor.submit(_search_single_nb, nb_id): nb_id for nb_id in all_notebooks}
                    for future in as_completed(future_to_nb):
                        nb_results = future.result()
                        for rank, res in enumerate(nb_results):
                            cid = getattr(res, "chunk_id", None) or getattr(res, "id", None) or str(rank)
                            if cid not in merged or merged[cid][0] > rank:
                                merged[cid] = (rank, res)
                search_results = [res for rank, res in sorted(merged.values(), key=lambda t: t[0])]
                search_results = search_results[: max(retrieval_limit, min_sources * 2)]
            elif hasattr(store, "search_hybrid"):
                try:
                    search_results = store.search_hybrid(
                        query=search_query,
                        notebook_id=target_notebook_id,
                        limit=retrieval_limit,
                        min_sources=min_sources,
                        source_ids=sorted(retrieval_source_ids),
                    )
                except Exception as hybrid_err:
                    logger.debug("Fallo en search_hybrid, fallback a search(): %s", hybrid_err)
                    search_results = []

            if not search_results and hasattr(store, "search"):
                try:
                    search_results = store.search(
                        query=search_query,
                        notebook_id=target_notebook_id,
                        limit=retrieval_limit,
                        source_ids=sorted(retrieval_source_ids),
                    )
                except Exception as search_err:
                    logger.warning("Fallo en búsqueda de cuaderno %s: %s", target_notebook_id, search_err)
                    search_results = []

            if not search_results and not target_notebook_id and hasattr(store, "search"):
                try:
                    search_results = store.search(query=search_query, limit=retrieval_limit)
                except Exception as fallback_err:
                    logger.warning("Fallo en búsqueda global fallback: %s", fallback_err)
                    search_results = []

        search_results = [
            result
            for result in search_results
            if getattr(result, "source_id", None) in retrieval_source_ids
        ]

        # Filtrado de presentación mandatorio (Slice 6.0.5 - Anti-leakage universal)
        if search_results and hasattr(store, "content_registry") and store.content_registry:
            filtered_results, had_sol = filter_presentation(search_results, store.content_registry)
            if not filtered_results and had_sol:
                return EpistemicContextPack(
                    formatted_context="",
                    citations=[],
                    chunks=[],
                    abstained=True,
                    abstention_reason="QUERY_OUT_OF_SCOPE",
                    reference_disclaimer=reference_disclaimer,
                    resolved_item=resolved_item,
                    trust_status=EpistemicTrustStatus.NO_EVIDENCE,
                    is_sufficient=False,
                ), []
            search_results = filtered_results

        # M1-03 §1: pase de recuperación dirigido por cobertura. Antes del
        # gate C5, si la selección actual no cubre términos críticos que el
        # CORPUS AUTORIZADO sí contiene (query conjuntiva estricta que
        # resuelve 0 hits + fallback disyuntivo sesgado por conteo), se
        # completa el recall con búsquedas léxicas dirigidas por término
        # sobre la MISMA allowlist. El gate conserva su criterio intacto:
        # sigue absteniendo si ni siquiera el índice completo cubre la
        # consulta (fail-closed genuino).
        try:
            recovered_results = _recover_coverage_gaps(
                store=store,
                results=search_results,
                coverage_query=original_user_query or search_query,
                authorized_source_ids=retrieval_source_ids,
                notebook_id=target_notebook_id,
            )
            if recovered_results:
                search_results = list(search_results) + list(recovered_results)
                logger.info(
                    "C5 coverage recovery: +%d chunks por términos no cubiertos en la selección",
                    len(recovered_results),
                )
                # M1-03 §1 (invariante C3, fail-closed de presupuesto): el
                # pack enriquecido debe respetar el sub-presupuesto de
                # evidencia (BUDGET_PRIMARY+SECONDARY). Poda determinista por
                # CHUNK COMPLETO (sin truncar contenido) con cobertura
                # preservada: se computan los términos que faltaban con la
                # selección ORIGINAL (miss0); todo chunk que cubre al menos
                # un término de miss0 es NÚCLEO y jamás se descarta; el
                # resto se suelta primero por índice descendente (determinista)
                # y luego por menor score. Si aún así no cabe, se conserva
                # el pack y el chokepoint C3 decide fail-closed (nunca se
                # trunca contenido ni se degrada la cobertura).
                try:
                    from study_engine.context.c3_budget import (
                        BUDGET_PRIMARY_EVIDENCE_TOKENS,
                        BUDGET_SECONDARY_EVIDENCE_TOKENS,
                        estimate_tokens,
                    )
                    from study_engine.context.c5_trust import (
                        evaluate_term_coverage as _etc,
                        extract_critical_query_terms as _ecqt,
                    )

                    _ev_budget = BUDGET_PRIMARY_EVIDENCE_TOKENS + BUDGET_SECONDARY_EVIDENCE_TOKENS
                    _crit = _ecqt(original_user_query or search_query or "")

                    def _key(r: Any) -> str:
                        return str(getattr(r, "chunk_id", None) or getattr(r, "id", None) or "")

                    def _covered_by(r: Any) -> set:
                        if not _crit:
                            return set()
                        _, miss = _etc(_crit, [r])
                        return {t for t in (set(_crit) - set(miss)) if t is not None}

                    def _text_of(items: List[Any]) -> str:
                        return "\n".join((getattr(r, "content", "") or "") for r in items)

                    def _drop_is_safe(i: int) -> bool:
                        # Invariante de cobertura: el drop solo es seguro si
                        # cada término crítico que cubre el chunk sigue cubierto
                        # por otro chunk de la selección ACTUAL (protección
                        # dinámica; la sola cobertura de la pasada ORIGINAL
                        # jamás se degrada por la poda).
                        cov_i = _covered_by(search_results[i])
                        if not cov_i:
                            return True
                        others = [o for j, o in enumerate(search_results) if j != i]
                        for t in cov_i:
                            if not any(t in _covered_by(o) for o in others):
                                return False
                        return True

                    _guard = 0
                    _max_guard = 4 * (len(search_results) + len(recovered_results)) + 8
                    while (
                        len(search_results) > 1
                        and _crit
                        and estimate_tokens(_text_of(search_results)) > _ev_budget
                        and _guard < _max_guard
                    ):
                        _guard += 1
                        drop_i = None
                        # 1) primer chunk sin cobertura de NINGÚN término
                        # crítico (tangencial para el gate) — recorrido
                        # descendente determinista; recovery es cola, así el
                        # añadido superfluo se aligera primero.
                        for i in range(len(search_results) - 1, 0, -1):
                            if not _covered_by(search_results[i]) and _drop_is_safe(i):
                                drop_i = i
                                break
                        # 2) si todos cubren algo: menor score entre los drops
                        # seguros (excluyendo el índice 0 como ancla).
                        if drop_i is None and len(search_results) > 1:
                            best_low = None
                            best_i = None
                            for i, r in enumerate(search_results[:-1]):
                                s = float(getattr(r, "score", 0.0) or 0.0)
                                if (best_low is None or s < best_low) and _drop_is_safe(i):
                                    best_low = s
                                    best_i = i
                            drop_i = best_i
                        # 3) si nada es droppable sin degradar cobertura: no se
                        # sacrifica; el chokepoint C3 decide fail-closed.
                        if drop_i is None:
                            break
                        search_results.pop(drop_i)
                except Exception:
                    logger.exception("Poda de presupuesto de evidencia falló; el chokepoint C3 decide fail-closed.")
        except Exception:
            logger.exception("Fallo en coverage recovery; se conserva la selección original (fail-closed).")

        federation_provenance = {}
        if federated_plan is not None and federated_plan.is_cross_curricular:
            search_results, federation_provenance = _merge_federated_results(
                store, planner, federated_plan, search_results, active_sources, src_meta_cache,
            )

        # Enmienda E23 & E26: Expansión de sección mediante SectionExpander
        expanded_chunks = []
        expanded_context_text = ""
        if search_results and hasattr(store, "engine"):
            try:
                from study_engine.retrieval.expansion import SectionExpander
                is_debug_q = bool(re.search(r"\b(?:falla|crashea|segfault|crash|segmentation\s+fault|se\s+rompe)\b", (search_query or "").lower()))
                exp_ceiling = 1800 if is_debug_q else 5000
                expander = SectionExpander(engine=store.engine, hard_ceiling_tokens=exp_ceiling)
                expanded_chunks, expanded_context_text = expander.expand_results(
                    seed_results=search_results[:6] if is_debug_q else search_results,
                    source_meta_cache=src_meta_cache,
                    allowed_source_ids=retrieval_source_ids,
                )
                if expanded_chunks and hasattr(store, "content_registry") and store.content_registry:
                    sol_ids = store.content_registry.get_solution_chunk_ids()
                    if sol_ids:
                        expanded_chunks = [c for c in expanded_chunks if getattr(c, "id", "") not in sol_ids]
            except Exception as exp_err:
                logger.warning("Error durante SectionExpander: %s", exp_err)
                expanded_chunks = []
                expanded_context_text = ""

        citation_idx = 1
        for res in search_results:
            content_clean = getattr(res, "content", "").strip()
            if not content_clean:
                continue
            src_id = getattr(res, "source_id", None)
            meta = src_meta_cache.get(src_id, {"title": src_id, "sha256": "", "author": ""})
            src_title = f"{meta['author']} - {meta['title']}" if meta.get("author") else meta.get("title", src_id)
            p_start = getattr(res, "page_start", None)
            doc_hash = meta.get("sha256") or ""
            chunk_id = getattr(res, "chunk_id", None)
            score_val = getattr(res, "score", 0.85)
            norm_score = round(min(1.0, max(0.1, abs(float(score_val)))), 2) if score_val else 0.85

            page_label = f" (Pág: {p_start})" if p_start is not None else ""
            citations_formatted.append(
                f"[E{citation_idx}] Fuente: {src_title}{page_label}:\n\"{content_clean}\""
            )

            author_str = meta.get("author", "")
            section_str = getattr(res, "section_path", "") or getattr(res, "section", "") or ""
            role_str = resolve_epistemic_role(
                source_id=src_id,
                source_title=src_title,
                author=author_str,
                notebook_id=target_notebook_id,
            )

            raw_chunks.append({
                "id": f"E{citation_idx}",
                "citation_id": f"E{citation_idx}",
                "source_id": src_id,
                "source_title": src_title,
                "page": p_start,
                "page_start": p_start,
                "page_end": getattr(res, "page_end", p_start),
                "chunk_text": content_clean,
                "chunk_id": chunk_id,
                "relevance_score": norm_score,
                "doc_hash": doc_hash,
                "authority_weight": 1.0,
                "namespace": "E",
                "author": author_str,
                "section": section_str,
                "epistemic_role": role_str,
                "document_id": getattr(res, "document_id", None),
                "trust_level": meta.get("trust_level", "unverified"),
            })
            if chunk_id in federation_provenance:
                provenance = federation_provenance[chunk_id]
                raw_chunks[-1].update({
                    "notebook_id": provenance.notebook_id,
                    "bridge_id": provenance.bridge_id,
                    "plan_id": federated_plan.plan_id,
                    "content_hash": provenance.content_hash,
                    "authority_weight": provenance.authority_weight,
                })
            citation_idx += 1

        kc_catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
        nb_catalog = kc_catalog.get(target_notebook_id, {})
        kcs_list = nb_catalog.get("kcs", [])
        if kcs_list:
            units_summary = ", ".join([f"{k.get('unit', '')}: {k.get('title', '')}" for k in kcs_list[:8]])
            citations_formatted.append(f"[Programa Oficial de Cátedra - {target_notebook_id}]: {units_summary}")

        # Enmienda E2: Si 0 fragmentos canónicos fueron recuperados del store, emitir abstención explícita
        if not raw_chunks:
            return EpistemicContextPack(
                formatted_context="",
                citations=[],
                chunks=[],
                abstained=True,
                abstention_reason="QUERY_OUT_OF_SCOPE",
                reference_disclaimer=reference_disclaimer,
                resolved_item=resolved_item,
                trust_status=EpistemicTrustStatus.NO_EVIDENCE,
                is_sufficient=False,
            ), []

        # Evaluación pre-LLM del C5 Trust Gate (Sufficiency, Coverage, Conflict, Relevance).
        # Cuando la consulta actual lleva anclaje deíctico/contextual, C5 debe
        # valorar la intención resuelta por el rewrite contextual, no la cadena
        # literal del turno anterior. Esto preserva fail-closed y evita un false
        # negative de continuidad técnica.
        eval_query = original_user_query or search_query
        trust_eval = evaluate_epistemic_trust(
            eval_query,
            raw_chunks,
            resolved_content_item=resolved_item,
            has_reference_disclaimer=bool(reference_disclaimer),
            contextual_query=search_query,
        )
        if trust_eval.abstained:
            return EpistemicContextPack(
                formatted_context="",
                citations=[],
                chunks=[],
                abstained=True,
                abstention_reason=trust_eval.abstention_reason or "QUERY_OUT_OF_SCOPE",
                reference_disclaimer=reference_disclaimer,
                resolved_item=resolved_item,
                trust_status=trust_eval.status,
                is_sufficient=False,
                missing_critical_terms=trust_eval.missing_critical_terms,
                coverage_ratio=trust_eval.coverage_ratio,
                max_relevance=trust_eval.max_relevance,
            ), []

        if citations_formatted:
            from study_engine.context.c3_budget import (
                BUDGET_PRIMARY_EVIDENCE_TOKENS,
                BUDGET_SECONDARY_EVIDENCE_TOKENS,
                prune_evidence_text_deterministically,
            )
            raw_fallback = "\n\n".join(citations_formatted)
            max_ev_tokens = BUDGET_PRIMARY_EVIDENCE_TOKENS + BUDGET_SECONDARY_EVIDENCE_TOKENS
            bounded_fallback, _ = prune_evidence_text_deterministically(raw_fallback, max_tokens=max_ev_tokens)
            # Only the E-tagged search results have exact identities in the
            # citation manifest passed to S4.4. The section expansion uses
            # [CHUNK ...] markers (and may add neighbors absent from that
            # manifest), so it cannot authorize a cited answer on this route.
            base_formatted = bounded_fallback

            # Si se detecta divergencia entre fuentes autorizadas (D_C5_3 & Addendum 3), explicitar el conflicto
            if trust_eval.is_conflicting:
                conflict_banner = (
                    "=== EVIDENCIA CONFLICTIVA ENTRE FUENTES AUTORIZADAS ===\n"
                    f"{trust_eval.conflict_details or 'Discrepancia detectada entre fuentes autorizadas.'}\n"
                    "El tutor debe explicitar y contrastar las posturas discrepantes sin asumir consenso falso.\n\n"
                )
                final_formatted = conflict_banner + base_formatted
            else:
                final_formatted = base_formatted

            pack = EpistemicContextPack(
                formatted_context=final_formatted,
                citations=search_results,
                chunks=raw_chunks,
                abstained=False,
                reference_disclaimer=reference_disclaimer,
                resolved_item=resolved_item,
                trust_status=trust_eval.status,
                is_sufficient=trust_eval.is_sufficient,
                is_conflicting=trust_eval.is_conflicting,
                conflict_details=trust_eval.conflict_details,
                missing_critical_terms=trust_eval.missing_critical_terms,
                coverage_ratio=trust_eval.coverage_ratio,
                max_relevance=trust_eval.max_relevance,
            )

            setattr(pack, "expanded_chunks", expanded_chunks)
            setattr(pack, "expanded_context_text", expanded_context_text)
            return pack, raw_chunks
    except Exception as ctx_err:
        logger.warning("Advertencia al ensamblar evidencias epistémicas: %s", ctx_err, exc_info=True)
        return EpistemicContextPack(
            formatted_context="",
            citations=[],
            chunks=[],
            abstained=True,
            abstention_reason="RETRIEVAL_FAILURE",
            trust_status=EpistemicTrustStatus.RETRIEVAL_FAILURE,
            is_sufficient=False,
        ), []


def _update_curriculum_progress(
    container: AppContainer,
    target_notebook_id: str,
    prompt_text: str,
    raw_chunks: list,
) -> None:
    """Update curriculum progress in student storage upon phase completion using batch updates."""
    if not (hasattr(container, "student_storage") and container.student_storage):
        return
    try:
        kc_catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
        nb_catalog = kc_catalog.get(target_notebook_id, {})
        kcs_list = nb_catalog.get("kcs", [])
        q_lower = prompt_text.lower()
        conn = container.student_storage._get_connection()
        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).isoformat()
        params = []
        for kc in kcs_list:
            kc_id = kc.get("kc_id", "")
            title = (kc.get("title") or "").lower()
            title_words = [w for w in title.replace(",", " ").replace(":", " ").split() if len(w) > 3]
            matches = any(w in q_lower for w in title_words) or kc_id.lower() in q_lower
            if matches:
                status_to_set = "covered" if raw_chunks else "in_progress"
                ev_inc = len(raw_chunks) if raw_chunks else 0
                params.append((target_notebook_id, kc_id, status_to_set, ev_inc, now_str))

        if params:
            with conn:
                conn.executemany(
                    """
                    INSERT INTO curriculum_progress (notebook_id, kc_id, status, evidence_count, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(notebook_id, kc_id) DO UPDATE SET
                        status = CASE 
                            WHEN curriculum_progress.status = 'mastered' THEN 'mastered'
                            WHEN excluded.status = 'covered' THEN 'covered'
                            ELSE curriculum_progress.status
                        END,
                        evidence_count = curriculum_progress.evidence_count + excluded.evidence_count,
                        last_updated = excluded.last_updated;
                    """,
                    params,
                )
    except Exception as prog_err:
        logger.warning("Error actualizando progreso curricular: %s", prog_err)


def _trigger_background_memory_extraction(
    container: Any,
    student_id: str,
    prompt_text: str,
    response_text: str,
    active_kc: Optional[str],
    pedagogical_mode: Optional[str],
    llm_backend: Optional[Any],
    notebook_id: str,
) -> None:
    """Asynchronously extract and persist misconceptions or preferences in background."""
    extractor = getattr(container, "pedagogical_memory_extractor", None)
    if extractor is None and hasattr(container, "student_storage") and container.student_storage:
        from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
        from study_engine.student.memory_extractor import PedagogicalMemoryExtractor
        tracker = PedagogicalMemoryTracker(container.student_storage)
        extractor = PedagogicalMemoryExtractor(tracker)

    mem0 = getattr(container, "mem0_manager", None)
    cog_extractor = getattr(container, "cognitive_extractor", None)
    if not extractor and not mem0 and not cog_extractor:
        return

    async def _run_bg() -> None:
        if cog_extractor:
            try:
                await cog_extractor.process_turn_and_persist(
                    student_id=student_id,
                    notebook_id=notebook_id,
                    query=prompt_text,
                    response_text=response_text,
                    active_kc=active_kc,
                    llm_backend=llm_backend,
                )
            except Exception as exc:
                logger.debug("Background cognitive profile extraction error: %s", exc)
        if extractor:
            try:
                await extractor.process_turn_and_persist(
                    student_id=student_id,
                    query=prompt_text,
                    response_text=response_text,
                    active_kc=active_kc,
                    pedagogical_mode=pedagogical_mode,
                    llm_backend=llm_backend,
                )
            except Exception as exc:
                logger.debug("Background pedagogical memory extraction error: %s", exc)
        if mem0 and response_text.strip():
            try:
                mem0.process_turn_memories(
                    student_id=student_id,
                    user_query=prompt_text,
                    response_text=response_text,
                    notebook_id=notebook_id,
                    active_kc=active_kc,
                )
            except Exception as exc:
                logger.debug("Background Mem0 process_turn_memories error: %s", exc)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run_bg())
    except RuntimeError:
        asyncio.run(_run_bg())


@router.get("/briefing")
async def get_session_briefing(
    notebook_id: Optional[str] = None,
    student_id: str = CANONICAL_STUDENT_ID,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Return opening session briefing summarizing previous trajectory and recommendations."""
    gen = getattr(container, "session_briefing_generator", None)
    target_nb = notebook_id or "default_notebook"
    if not gen:
        return {
            "briefing": "¡Hola Agustín! Todo listo para comenzar una nueva sesión de estudio.",
            "weak_kcs": [],
            "due_reviews_count": 0,
            "notebook_id": target_nb,
        }

    briefing_fn = getattr(gen, "generate_with_cognitive_profile", gen.generate_briefing)
    briefing_text = briefing_fn(
        student_id=student_id,
        notebook_id=target_nb,
        student_name="Agustín",
    )
    weak_kcs = [
        {"kc_id": k.kc_id, "title": k.title, "p_L": k.p_L}
        for k in gen._get_weak_kcs(student_id=student_id)
    ]
    due_reviews = gen._get_due_reviews(student_id=student_id)

    return {
        "briefing": briefing_text,
        "weak_kcs": weak_kcs,
        "due_reviews_count": len(due_reviews),
        "notebook_id": target_nb,
    }


def _kc_search_terms(kc: Dict[str, Any]) -> List[str]:
    """Extract matchable terms from a KC entry: title + display_name + subtopics."""
    from study_engine.storage.lexical_index import SPANISH_STOPWORDS

    raw_parts: List[str] = [str(kc.get("title") or ""), str(kc.get("display_name") or "")]
    raw_parts.extend(str(s) for s in (kc.get("subtopics") or []))
    words = re.findall(r"\w+", " ".join(raw_parts).lower())
    base = {w for w in words if len(w) > 3 and w not in SPANISH_STOPWORDS}
    # Variantes sing/plur ingenuas para no perder matches por número gramatical
    # (ej. query "un puntero" debe matchear el término del catálogo "punteros").
    terms = set(base)
    for w in base:
        if w.endswith("s") and len(w) > 4:
            terms.add(w[:-1])
        else:
            terms.add(w + "s")
    return sorted(terms)


def _match_kc_id(kcs_list: List[Dict[str, Any]], prompt_text: str) -> Optional[str]:
    """Best-effort KC matching for a chat query (F3: honest matching, no fallback).

    Returns the ``kc_id`` with the most term hits in the query, or ``None``
    when no KC matches. A KC qualifies when either:
    - its exact ``kc_id`` appears in the query, or
    - >= 2 of its terms appear.

    Single-term hits do NOT qualify: a shared word across domains (e.g.
    "procesos" = flowchart symbol vs OS scheduling) would otherwise attribute
    the turn to the wrong KC.

    F3 contract: when this returns ``None`` the turn is NOT attributed to any
    KC. ``phase_complete`` then emits ``bkt_context.fallback=True`` with
    neutral values (p_L=0.5, context_mode='intermediate') instead of silently
    reporting the turn as ``kcs_list[0]``.
    """
    q = (prompt_text or "").lower()
    best_kc: Optional[str] = None
    best_hits = 0
    for kc in kcs_list:
        kid = str(kc.get("kc_id") or "")
        if kid and kid.lower() in q:
            return kid
        aliases = {
            str(alias).strip().lower()
            for alias in (kc.get("aliases") or [])
            if isinstance(alias, str) and alias.strip()
        }
        matched_aliases = {alias for alias in aliases if alias in q}
        alias_tokens = {
            token
            for alias in matched_aliases
            for token in re.findall(r"\w+", alias)
        }
        hit_terms = [
            term for term in _kc_search_terms(kc)
            if term not in alias_tokens and re.search(rf"\b{re.escape(term)}\b", q)
        ]
        hits = len(hit_terms) + len(matched_aliases)
        if hits >= 2 and hits > best_hits:
            best_kc, best_hits = kid, hits
    return best_kc


def _match_context_kc_id(
    kcs_list: List[Dict[str, Any]],
    prompt_text: str,
    retrieval_query: str,
    *,
    is_followup: bool,
    context_pack: Any = None,
) -> Optional[str]:
    matched_kc_id = _match_kc_id(kcs_list, prompt_text) if kcs_list else None
    if matched_kc_id is None and is_followup and kcs_list:
        matched_kc_id = _match_kc_id(kcs_list, retrieval_query)
        if matched_kc_id:
            logger.debug("KC matched via retrieval_query fallback for deictic query")
    if not matched_kc_id and context_pack and getattr(context_pack, "resolved_item", None):
        resolved_item = context_pack.resolved_item
        matched_kc_id = _match_kc_id(
            kcs_list,
            getattr(resolved_item, "statement_text", ""),
        )
    return matched_kc_id


def _build_cognitive_profile_block(prof_injector: Any, active_kc: Optional[str]) -> str:
    if not prof_injector:
        return ""
    try:
        return prof_injector.build_injection_block(
            student_id=CANONICAL_STUDENT_ID,
            active_kc=active_kc,
        )
    except Exception as c_err:
        logger.warning("Error building cognitive profile block: %s", c_err)
        return ""


# Marcador de scope global (COMMIT 2 fix/scope): una query técnica emitida con
# scope de carpeta (roadmap, Programación) no se desvía al usuario al cuaderno
# "correcto"; el roadmap es acceso global por defecto y el retrieval corre
# contra TODOS los cuadernos, fundiendo resultados por chunk_id.

# COMMIT 3 (fix/scope): intención no curricular — opinión personal, ficción,
# cotidiano, actualidad. Es INDEPENDIENTE del match léxico de contenido: el
# corpus menciona Star Wars (ejemplo didáctico) pero "¿Qué opinás de Star Wars?"
# no es consulta curricular. El umbral vectorial 0.87 no se toca.
_NON_CURRICULAR_INTENT_RE = re.compile(
    r"(qu[ée]\s+opin[áa]s|qu[ée]\s+pens[áa]s|opin[oa]\s+que|creo\s+que|te\s+gusta|te\s+copa|"
    r"star\s+wars|pel[íi]cula|serie\s+de|f[úu]tbol|partido\s+de|"
    r"noticias?\s+de|clima|pron[óo]stico|receta\s+de|chiste|broma|"
    r"videojuego|jueguito|m[úu]sica\s+para)",
    re.IGNORECASE,
)


def _is_non_curricular_intent(prompt_text: str, kcs_list: List[Dict[str, Any]]) -> bool:
    """Verdadero si la query pide opinión/ficción/cotidiano SIN vocabulario curricular.

    Un patrón no curricular + cero match con el catálogo KC => abstención.
    Si la query mezcla ("¿qué opinás de la búsqueda binaria?"), el vocabulario
    curricular gana y la consulta continúa.
    """
    if not _NON_CURRICULAR_INTENT_RE.search(prompt_text or ""):
        return False
    return _match_kc_id(kcs_list, prompt_text) is None


def _global_default_contract() -> Any:
    """Contrato pedagógico neutral para scope global (roadmap cross-notebook).

    El pipeline requiere un contract (get_phase, SocraticGuard, system prompt);
    en scope global no hay contrato de cuaderno, así que se sintetiza uno
    genérico con la fase 'conceptual' y el tono soberano por defecto.
    """
    from study_engine.pedagogy.contract import PedagogicalContract
    from study_engine.pedagogy.response_phase import ResponsePhase

    return PedagogicalContract(
        notebook_id=GLOBAL_SCOPE_ID,
        base_system_prompt=(
            "Sos TALOS, tutor soberano en modo roadmap global: respondé con rigor, "
            "socrático y siempre anclado a la evidencia citada del corpus recuperado."
        ),
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                max_tokens=3500,
                phase_prompt_template="Resolvé pedagógicamente: {concept}",
            )
        ],
    )


def maybe_inject_session_digest(
    container: Any,
    history_key: str,
    bkt_directive: Optional[str],
) -> Optional[str]:
    """Inyecta el digest de la sesión anterior UNA vez por history_key.

    Devuelve el bkt_directive original (o None) si no hay digest o ya se
    mostró; si hay directiva nueva, la concatena al final.
    """
    if history_key in _DIGEST_SHOWN:
        return bkt_directive
    storage = getattr(container, "student_storage", None)
    if storage is None:
        return bkt_directive
    try:
        from study_engine.pedagogy.session_digest import digest_directive, get_latest_digest
        digest = get_latest_digest(storage, CANONICAL_STUDENT_ID)
        directive = digest_directive(digest) if digest else ""
        _DIGEST_SHOWN[history_key] = True
        if directive:
            logger.info("[SESSION-DIGEST] primer turno de sesión digest inyectado (fricción previa: %s)",
                        digest.get("friction_level"))
            return f"{bkt_directive}\n\n{directive}" if bkt_directive else directive
    except Exception as dig_err:
        logger.debug("No se pudo inyectar session digest: %s", dig_err)
    return bkt_directive


def _prepare_chat_context(
    *,
    store: Any,
    resolver: Any,
    container: Any,
    prompt_text: str,
    request: "ChatQueryRequest",
    target_scope_type: str,
    target_scope_id: str,
) -> Tuple[Any, Any, Any, List[Any], Any, Any, Any, Any, Any, Any, Any]:
    """Resolve scope, retrieval, BKT and Mem0 for a chat turn.

    Always returns ``PREPARE_CONTEXT_ARITY`` (11) items. Folder and
    conversational fast-path pack ``matched_kc_id`` / ``bkt_meta`` as None
    by design (non-technical routes do not run BKT).

    F3: on the notebook path, ``matched_kc_id`` is None when no KC of the
    notebook catalog matches the query (see ``_match_kc_id``). The SSE
    ``phase_complete`` payload then reports ``bkt_context.fallback=True``
    with neutral values instead of attributing the turn to an arbitrary KC.

    COMMIT 2: folder scopes solo deflectan queries organizacionales. Si la
    query es técnica, el routing continúa por el pipeline normal con scope
    global (retrieval cross-notebook sobre todo el corpus).
    """
    if target_scope_id == "folder_root" and hasattr(store, "contains_folder") and not store.contains_folder("folder_root"):
        from study_engine.hierarchy.folder import Folder
        now = datetime.now(timezone.utc)
        store.create_folder(
            Folder(
                id="folder_root",
                name="Root Workspace",
                parent_folder_id=None,
                created_at=now,
                updated_at=now,
            )
        )

    resolved_scope = resolver.resolve(
        scope_type=ScopeType(target_scope_type),
        scope_id=target_scope_id,
    )

    global_scope = False
    target_folder_id: Optional[str] = None
    if resolved_scope.scope_type == ScopeType.FOLDER:
        from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator
        target_folder_id = resolved_scope.folder_id or target_scope_id
        orch = FolderOrchestrator(
            folder_id=target_folder_id,
            knowledge_store=store,
            ledger=getattr(container, "ledger", None),
        )
        decision = orch.route_query(prompt_text)
        if decision.get("action") != "delegate_to_notebook":
            return _pack_prepare_context(resolved_scope, folder_decision=decision)
        # Query técnica bajo scope de carpeta -> acceso global por defecto.
        global_scope = True

    target_notebook_id = GLOBAL_SCOPE_ID if global_scope else (resolved_scope.notebook_id or target_scope_id)

    # FAST-PATH CONVERSACIONAL (Fase 1: Sub-100ms Gatekeeping)
    from study_engine.tutor.fastpath_service import FastPathConversationalService
    is_conv, route_kind = FastPathConversationalService.detect_conversational_route(prompt_text)
    if is_conv and route_kind is not None:
        fastpath = FastPathConversationalService()
        context = fastpath.extract_student_context(
            container,
            target_notebook_id,
            student_id=CANONICAL_STUDENT_ID,
        )
        return _pack_prepare_context(
            resolved_scope,
            conv_payload=(fastpath, route_kind, context),
        )

    # BKT Adaptation determination (Fix S4.2)
    # F3: matching honesto — si ningún KC matchea, matched_kc_id queda None y
    # el phase_complete lo declara con bkt_context.fallback=True + p_L neutral.
    orch = getattr(container, "pedagogical_orchestrator", None)
    kc_catalog = getattr(orch, "_kc_catalog", {}) if orch is not None else {}
    if target_notebook_id == GLOBAL_SCOPE_ID:
        # Scope global: matchear contra la unión de todos los catálogos KC.
        kcs_list = [
            kc
            for nb_entry in (kc_catalog.values() if isinstance(kc_catalog, dict) else [])
            for kc in (nb_entry.get("kcs", []) if isinstance(nb_entry, dict) else [])
        ]
    else:
        nb_catalog = kc_catalog.get(target_notebook_id, {}) if isinstance(kc_catalog, dict) else {}
        kcs_list = nb_catalog.get("kcs", []) if isinstance(nb_catalog, dict) else []

    # COMMIT 3 (fix/scope): intención no curricular abstiene ANTES del
    # retrieval y aunque haya match léxico de contenido (independencia total).
    history_key = f"{request.session_id or 'anon'}:{target_notebook_id}"
    context_cache_key = _request_context_cache_key(
        request,
        resolved_scope,
        target_notebook_id,
    )

    conv_turns = _resolve_conversation_turns(
        server_turns=_CONV_TURN_BUFFER.get(context_cache_key),
        client_turns=request.recent_turns,
        current_prompt=prompt_text,
    )
    from study_engine.retrieval.query_rewriter import (
        QueryRewriter,
        has_deictic_markers,
        resolve_contextual_reference,
        should_rewrite_contextual,
    )
    from study_engine.pedagogy.conversation_state import ConversationState, classify_conversation_state, should_abstain

    rewriter = QueryRewriter()
    conv_state = ConversationState.COLD_START
    clean_p = (prompt_text or "").strip()
    is_explicit_reference = bool(_ACTIVITY_REFERENCE_RE.search(clean_p))
    is_deictic = has_deictic_markers(clean_p)
    should_rew = should_rewrite_contextual(clean_p, conv_turns)
    reference_resolution = resolve_contextual_reference(clean_p, conv_turns)

    re_followup = re.compile(
        r"\b(?:pod[eé]s\s+(?:detallarme|explicarme|profundizar|ampliar|darme\s+m[aá]s|explicar)|"
        r"explicame(?:\s+m[aá]s)?(?:\s+a\s+detalle)?|"
        r"detallame(?:\s+m[aá]s)?|"
        r"profundiz[aá]|"
        r"ampli[aá](?:\s+eso)?|"
        r"m[aá]s\s+(?:detalles?|ejemplos?|info)|"
        r"no\s+(?:logr[eé]\s+)?(?:entender|comprendo|comprend[ií]|entend[ií])|"
        r"no\s+me\s+qued[oó]\s+claro|"
        r"me\s+cuesta\s+entender|"
        r"por\s*qu[eé]\s+(?:es|pasa|ocurre|dec[ií]s|dices|deber[ií]a|se|el)|"
        r"qu[eé]\s+significa|"
        r"a\s+qu[eé]\s+te\s+refer[ií]s|"
        r"me\s+lo\s+explic[aá]s\s+de\s+nuevo|"
        r"segu[ií]|contin[uú]a|qu[eé]\s+m[aá]s|"
        r"y\s+eso\s+por\s+qu[eé]\s+pasa|"
        r"y\s+c[oó]mo\s+ser[ií]a\b|"
        r"dame\s+un\s+ejemplo|"
        r"dame\s+m[aá]s\s+ejemplos|"
        r"c[oó]mo\s+ser[ií]a|"
        r"mostrame\s+un\s+ejemplo|"
        r"podr[ií]as\s+explicar(?:\s+de\s+manera\s+conceptual\s+y\s+clara)?|"
        r"explicame\s+de\s+manera\s+conceptual\s+y\s+clara)\b",
        re.IGNORECASE,
    )
    is_deictic_or_clarification = bool(re.search(
        r"\b(?:eso|esto|aquello|lo\s+anterior|lo\s+que\s+dijiste|entender|comprend\w*|por\s*qu[eé]|explic\w*|detall\w*|ampli\w*|metadato\w*|integridad|stack|heap|pila|memoria|puntero\w*)\b",
        clean_p,
        re.IGNORECASE,
    ))

    epistemic_key = context_cache_key
    has_fallback_pack = epistemic_key in _LAST_EPISTEMIC_PACK
    is_followup = (
        not is_explicit_reference
        and bool(
            should_rew
            or is_deictic
            or re_followup.search(clean_p)
            or (conv_turns and is_deictic_or_clarification and len(clean_p.split()) <= 10)
            or (conv_turns and len(clean_p.split()) <= 4)
        )
    )

    if is_followup:
        retrieval_query = rewriter.rewrite_contextual(clean_p, conv_turns)
    else:
        retrieval_query = rewriter.rewrite(clean_p)

    if reference_resolution.status in {"ambiguous", "missing"}:
        detail = (
            "No pude identificar un único antecedente en el historial disponible."
            if reference_resolution.status == "ambiguous"
            else "No tengo el turno anterior necesario para resolver esa referencia."
        )
        context_pack = EpistemicContextPack(
            formatted_context="",
            citations=[],
            chunks=[],
            abstained=True,
            abstention_reason="CONTEXT_REFERENCE_REQUIRES_CLARIFICATION",
            clarification_message=(
                f"{detail} Indicame el tema o pegá el fragmento al que te referís."
            ),
            trust_status=EpistemicTrustStatus.PARTIAL_EVIDENCE,
            is_sufficient=False,
        )
        raw_chunks = []
    elif _is_non_curricular_intent(retrieval_query, kcs_list):
        context_pack = EpistemicContextPack(
            formatted_context="",
            citations=[],
            chunks=[],
            abstained=True,
            abstention_reason=(
                "Consulta fuera del ámbito curricular (opinión, ficción, actualidad o vida cotidiana). "
                "TALOS está acotado a la bibliografía del roadmap; planteá la pregunta en términos del programa."
            ),
            trust_status=EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
            is_sufficient=False,
        )
        raw_chunks: List[Any] = []
    else:
        from study_engine.retrieval.granularity_router import GranularityRouter
        granularity_decision = GranularityRouter.route(
            retrieval_query,
            has_code_block="```" in clean_p,
        )
        context_pack, raw_chunks = _assemble_epistemic_context(
            store=store,
            container=container,
            prompt_text=retrieval_query,
            target_notebook_id=target_notebook_id,
            active_sources=request.active_sources,
            granularity_decision=granularity_decision,
            global_folder_id=target_folder_id if global_scope else None,
            original_user_query=clean_p,
        )

        # Máquina de estados conversacional con inercia epistémica (CAL §3.2 Multi-Turn)
        conv_state = classify_conversation_state(
            query=clean_p,
            recent_turns=conv_turns,
            retrieval_results=raw_chunks,
            has_fallback_pack=has_fallback_pack,
        )

        # Rescate epistémico para consultas de seguimiento / deícticas en contexto conversacional:
        # Si la consulta es de seguimiento (o conv_state en AMBIGUOUS_FOLLOWUP / ACTIVE_TECHNICAL_THREAD)
        # y el retrieval devolvió 0 fragmentos nuevos, reusar el pack epistémico verificado del turno previo
        # ÚNICAMENTE si existe compatibilidad temática verificable (D_C5_6 & Addendum 5).
        should_abst, abst_reason = should_abstain(conv_state, raw_chunks, has_fallback_pack=has_fallback_pack)
        if (
            (getattr(context_pack, "abstained", False) or len(raw_chunks) == 0)
            and not should_abst
            and has_fallback_pack
            and not getattr(context_pack, "resolved_item", None)
            and getattr(context_pack, "trust_status", None) not in {
                EpistemicTrustStatus.RETRIEVAL_FAILURE, EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
            }
        ):
            last_pack_tuple = _LAST_EPISTEMIC_PACK.get(epistemic_key)
            if last_pack_tuple:
                prev_pack, prev_chunks = last_pack_tuple
                followup_match = re_followup.search(clean_p)
                followup_residue = re_followup.sub(" ", clean_p) if followup_match else None
                topic_terms = (
                    extract_critical_query_terms(followup_residue)
                    if followup_residue is not None
                    else None
                )
                contextual_query = (
                    retrieval_query
                    if reference_resolution.status == "unique" and topic_terms == []
                    else None
                )
                topic_query = (
                    " ".join(followup_residue.split())
                    if followup_residue is not None
                    else None
                )
                if topic_terms == [] and contextual_query is None:
                    topic_query = clean_p
                # EP-01/H1-A: un mensaje meta (marcadores cerrados de diálogo)
                # SIN match de KC propio no introduce términos temáticos: hereda
                # el referente académico de la conversación y se evalúa como
                # continuidad deíctica pura del evaluador D_C5_6. Sin esto, el
                # vocabulario meta ("entiendo", "explicámelo") se toma como
                # tema y el rescate del pack previo se rechaza con
                # incompatibilidad temática → QUERY_OUT_OF_SCOPE (repro EP-01).
                if _is_pure_meta_followup(clean_p, kcs_list):
                    topic_query = ""
                is_compat, compat_msg = evaluate_conversational_rescue_compatibility(
                    new_query=clean_p,
                    previous_context_pack=prev_pack,
                    previous_chunks=prev_chunks,
                    contextual_query=contextual_query,
                    topic_query=topic_query,
                )
                if is_compat:
                    if not _is_authorized_reusable_pack(
                        prev_pack,
                        prev_chunks,
                        store=store,
                        target_notebook_id=target_notebook_id,
                        global_folder_id=target_folder_id if global_scope else None,
                    ):
                        logger.info(
                            "Rescate conversacional rechazado por autorización o provenance no vigente (%s)",
                            epistemic_key,
                        )
                        if context_pack is None or not getattr(context_pack, "abstained", False):
                            context_pack = EpistemicContextPack(
                                formatted_context="",
                                citations=[],
                                chunks=[],
                                abstained=True,
                                abstention_reason="EVIDENCE_NOT_CURRENTLY_AUTHORIZED",
                                trust_status=EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
                                is_sufficient=False,
                            )
                        raw_chunks = []
                    else:
                        logger.info(
                            "Recuperando context_pack previo para continuidad conversacional (%s, estado=%s): %s",
                            epistemic_key, conv_state.value, compat_msg
                        )
                        context_pack = prev_pack
                        raw_chunks = list(prev_chunks)
                else:
                    logger.info(
                        "Rescate conversacional rechazado por incompatibilidad temática (%s): %s",
                        epistemic_key, compat_msg
                    )
                    if context_pack is None or not getattr(context_pack, "abstained", False):
                        context_pack = EpistemicContextPack(
                            formatted_context="",
                            citations=[],
                            chunks=[],
                            abstained=True,
                            abstention_reason="QUERY_OUT_OF_SCOPE",
                            trust_status=EpistemicTrustStatus.NO_EVIDENCE,
                            is_sufficient=False,
                        )
                    raw_chunks = []

        # Si el context_pack es válido, suficiente y tiene fragmentos, actualizar la caché del último pack epistémico
        if context_pack and not getattr(context_pack, "abstained", False) and getattr(context_pack, "is_sufficient", False) and raw_chunks:
            _LAST_EPISTEMIC_PACK[epistemic_key] = (context_pack, raw_chunks)

    # El pipeline SIEMPRE necesita un contrato (SocraticGuard, get_phase);
    # en scope global se usa el contrato neutral sintético.
    contract = (
        _global_default_contract()
        if target_notebook_id == GLOBAL_SCOPE_ID
        else store.get_pedagogical_contract(target_notebook_id)
    )

    # ConversationStyleRouter (Ola 5, E24)
    from study_engine.pedagogy.style_router import ConversationStyleRouter, ConversationStyle
    style_result = ConversationStyleRouter.detect_style(prompt_text)
    # En hilos técnicos activos o seguimientos deícticos, preservar siempre la profundidad formal
    if (is_followup or conv_state in (ConversationState.AMBIGUOUS_FOLLOWUP, ConversationState.ACTIVE_TECHNICAL_THREAD)) and style_result.style == ConversationStyle.CASUAL_CHAT:
        style_result = ConversationStyleRouter.detect_style("explicación formal y técnica detallada")

    matched_kc_id = _match_context_kc_id(
        kcs_list,
        prompt_text,
        retrieval_query,
        is_followup=is_followup,
        context_pack=context_pack,
    )

    from study_engine.pedagogy.student_context import (
        determine_pedagogical_context_mode,
        build_bkt_adaptation_directive,
    )
    context_mode, bkt_meta = determine_pedagogical_context_mode(
        target_kc_id=matched_kc_id,
        bkt_tracker=getattr(container, "bkt_tracker", None),
        kc_catalog=kc_catalog,
        notebook_id=None if target_notebook_id == GLOBAL_SCOPE_ID else target_notebook_id,
    )

    # Cold-Start C4: conservar la guía acelerada del ejercicio con el modo asignado por BKT.
    if context_pack and getattr(context_pack, "resolved_item", None) and bkt_meta.get("attempts", 0) == 0:
        bkt_directive = build_bkt_adaptation_directive(context_mode, bkt_meta)
        accelerated_proposal = (
            "=== PROPUESTA PEDAGÓGICA ACELERADA (COLD-START C4) ===\n"
            "- El estudiante solicita un ejercicio curricular nuevo sin intentos previos registrados.\n"
            "- Guiá al estudiante para plantear el ejercicio y verificar su razonamiento en un máximo de 2 intercambios.\n"
            "- No reveles la respuesta final ni el código de solución completo."
        )
        bkt_directive = f"{bkt_directive}\n\n{accelerated_proposal}" if bkt_directive else accelerated_proposal
    else:
        bkt_directive = build_bkt_adaptation_directive(context_mode, bkt_meta)

    # Protocolo de Lucha (Fase 5.3b): si el estudiante encadena >=3 fallos en
    # este KC, se inyecta la directiva estricta al prompt del siguiente turno.
    struggle = getattr(container, "struggle_tracker", None)
    struggle_storage = getattr(container, "student_storage", None)
    struggle_state = (
        struggle.confirmed_state(
            struggle_storage, student_id=CANONICAL_STUDENT_ID,
            session_id=request.session_id or "anon", notebook_id=target_notebook_id,
        )
        if struggle and struggle_storage else None
    )
    struggle_active = bool(
        struggle and matched_kc_id and struggle.is_struggling(matched_kc_id, state=struggle_state)
    )
    if struggle_active:
        logger.info("[STRUGGLE] KC %s con %s fallos consecutivos; inyectando protocolo.",
                    matched_kc_id, "3+")
        bkt_directive = (
            f"{bkt_directive}\n\n{struggle.directive(matched_kc_id, state=struggle_state)}"
            if bkt_directive else struggle.directive(matched_kc_id, state=struggle_state)
        )
    elif hasattr(container, "student_storage") and container.student_storage is not None:
        # M8 & M3: Si el Protocolo de Lucha NO está activo, inyectar directiva metacognitiva (fading)
        try:
            from study_engine.pedagogy.student_context import get_scaffolding_directive
            profile = container.student_storage.calculate_solution_dependency(CANONICAL_STUDENT_ID)
            p_val = bkt_meta.get("p_L") if bkt_meta else None
            scaffolding_directive = get_scaffolding_directive(profile, target_kc_id=matched_kc_id, p_L=p_val)
            if scaffolding_directive:
                bkt_directive = f"{bkt_directive}\n\n{scaffolding_directive}" if bkt_directive else scaffolding_directive
                # M6: Log estructurado JSON para auditoría forense
                logger.info(json.dumps({
                    "event": "METACOGNITIVE_SCAFFOLDING",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "student_id": CANONICAL_STUDENT_ID,
                    "classification": profile.get("classification"),
                    "ratio": round(float(profile.get("ratio", 0.0)), 2),
                    "autonomy_score": round(float(profile.get("autonomy_score", 0.5)), 2),
                    "directive_injected": True,
                }))
        except Exception as meta_err:
            logger.debug("Chat route: error generando directiva metacognitiva: %s", meta_err)

    # Currículo en Espiral (Fase 1 - Roadmap v1.1): profundización retroactiva determinista
    if matched_kc_id and not struggle_active and getattr(container, "bkt_tracker", None):
        try:
            from study_engine.pedagogy.spiral_curriculum import SpiralCurriculumEngine
            spiral_engine = SpiralCurriculumEngine(container.bkt_tracker)
            spiral_opps = spiral_engine.detect_spiral_opportunities(
                current_kc=matched_kc_id,
                student_id=CANONICAL_STUDENT_ID,
            )
            if spiral_opps:
                spiral_directive = spiral_engine.inject_spiral_directive(spiral_opps)
                if spiral_directive:
                    bkt_directive = f"{bkt_directive}\n\n{spiral_directive}" if bkt_directive else spiral_directive
                logger.info(json.dumps({
                    "event": "SPIRAL_OPPORTUNITY_DETECTED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "student_id": CANONICAL_STUDENT_ID,
                    "new_kc": spiral_opps[0]["new_kc"],
                    "retroactive_kc": spiral_opps[0]["retroactive_kc"],
                    "opportunities_count": len(spiral_opps),
                }))
        except Exception as spiral_err:
            logger.debug("Chat route: error generando directiva de currículo en espiral: %s", spiral_err)

    # Inyectar memoria soberana de largo plazo (Fase 6 - Mem0 Soberano)
    mem0_directive = ""
    try:
        mem0 = getattr(container, "mem0_manager", None)
        if mem0:
            mem0_directive = mem0.assemble_long_term_directive(
                student_id=CANONICAL_STUDENT_ID,
                active_kc=matched_kc_id,
                notebook_id=target_notebook_id,
            )
        else:
            tracker = getattr(container, "pedagogical_memory_tracker", None)
            if tracker is None and hasattr(container, "student_storage") and container.student_storage:
                from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
                tracker = PedagogicalMemoryTracker(container.student_storage)
            if tracker:
                mem0_directive = tracker.format_tutor_directive(
                    student_id=CANONICAL_STUDENT_ID,
                    kc_id=matched_kc_id,
                    limit=3,
                )
    except Exception as e:
        logger.debug("Chat route: unable to format mem0 directive: %s", e)

    if mem0_directive:
        bkt_directive = f"{bkt_directive}\n\n{mem0_directive}" if bkt_directive else mem0_directive

    return _pack_prepare_context(
        resolved_scope,
        contract=contract,
        context_pack=context_pack,
        raw_chunks=raw_chunks,
        context_mode=context_mode,
        bkt_directive=bkt_directive,
        style_result=style_result,
        matched_kc_id=matched_kc_id,
        bkt_meta=bkt_meta,
    )


# EP-01/H1-A: referencia a una actividad identificada (ejercicio/guía/
# problema/tp + número). El referente es la actividad, no el episodio activo;
# el pipeline del chat es quien debe resolverla. Patrón compartido por la
# delegación de diálogo y `_prepare_chat_context` (is_explicit_reference).
_ACTIVITY_REFERENCE_RE = re.compile(
    r"\b(?:ejercicio|gu[ií]a|problema|tp)\s+\d+\b", re.IGNORECASE
)

# M1-03 §5: marcadores de meta-discurso del diálogo (deterministas; misma
# clase de heurísticas keyword que usa DialogueEngine._propose_intent para
# CONFUSION/REFORMULATION/EXAMPLE_REQUEST). NO son detección de contenido:
# un mensaje con afirmación técnica ante un error conceptual no matchea y
# sigue el pipeline completo de chat (corrección fundada por retrieval+S4.4).
_DIALOGUE_META_MARKERS: Tuple[str, ...] = (
    "no entiendo",
    "no entendí",
    "no entiendo nada",
    "otra forma",
    "reformulá",
    "reformula eso",
    "explicá de nuevo",
    "explícame de otra forma",
    "me perdí",
    "dame un ejemplo",
    "otro ejemplo",
)

# Fases de sesión desde las que un turno meta del estudiante pertenece al
# diálogo del episodio activo (SUBMIT_MESSAGE es acción permitida del
# orquestador en DIALOGUE; el diálogo del episodio transiciona EXPLAINING
# fail-closed con su propio paso de inicio).
_DIALOGUE_DELEGATE_PHASES = {"EXPLAINING", "DIALOGUE"}


def _referent_kcs_list(
    container: Any,
    scope_notebook: Optional[str],
    episode_notebook: Optional[str],
) -> List[Dict[str, Any]]:
    """Catálogo KC aplicable a la resolución del referente del gate de diálogo.

    EP-01: el matching del referente se hace sobre el catálogo del cuaderno del
    episodio (donde vive el KC del packet) unido al del scope del chat cuando
    difiere; en scope folder/global se usa la unión de todos los catálogos
    (mismo criterio que `_prepare_chat_context` para scope global).
    """
    orch = getattr(container, "pedagogical_orchestrator", None)
    catalog = getattr(orch, "_kc_catalog", None) if orch is not None else None
    if not isinstance(catalog, dict):
        return []

    def _kcs(nb_id: Optional[str]) -> List[Dict[str, Any]]:
        entry = catalog.get(nb_id) if nb_id else None
        return list(entry.get("kcs", [])) if isinstance(entry, dict) else []

    if scope_notebook and episode_notebook and scope_notebook != episode_notebook:
        return _kcs(scope_notebook) + _kcs(episode_notebook)
    if scope_notebook or episode_notebook:
        return _kcs(scope_notebook or episode_notebook)
    return [
        kc
        for entry in catalog.values()
        if isinstance(entry, dict)
        for kc in entry.get("kcs", [])
    ]


def _dialogue_gate_cache_key(request: Any, session_id: Optional[str]) -> Optional[str]:
    """Clave de contexto de conversación para el gate de diálogo (EP-01).

    Réplica determinista de la clave del pipeline para scope notebook/folder,
    computable sin resolver el scope (el gate corre antes de
    `_prepare_chat_context`). Si la clave no coincide con la del pipeline, el
    gate degrada honestamente a los turnos del cliente.
    """
    if request is None:
        return None
    scope_type = getattr(request, "effective_scope_type", None)
    scope_id = getattr(request, "effective_scope_id", None)
    if not scope_type or not scope_id:
        return None
    notebook_id = scope_id if scope_type == "notebook" else GLOBAL_SCOPE_ID
    return _epistemic_cache_key(
        session_id=session_id,
        scope_type=scope_type,
        scope_id=scope_id,
        notebook_id=notebook_id,
        active_sources=getattr(request, "active_sources", None),
        requested_scope_id=getattr(request, "requested_scope_id", None),
    )


def _append_dialogue_turn(
    gate_key: Optional[str],
    role: str,
    content: str,
    *,
    episode_id: Optional[str] = None,
    kc_id: Optional[str] = None,
) -> None:
    """Registra un turno delegado/clarificación en el buffer de conversación.

    EP-01: sin este registro, la delegación volvería invisible para el
    pipeline (y para futuras resoluciones de referente) el hecho de que el
    último intercambio académico perteneció al diálogo del episodio. El
    marcado ``episode_id``/``kc_id`` sólo lo produce el servidor; los
    consumidores existentes usan role/content y lo ignoran sin cambio de
    contrato.
    """
    if not gate_key:
        return
    turns = _CONV_TURN_BUFFER.get(gate_key) or []
    entry: Dict[str, Any] = {"role": role, "content": (content or "")[:_MAX_RECENT_TURN_CHARS]}
    if episode_id:
        entry["episode_id"] = episode_id
        if kc_id:
            entry["kc_id"] = kc_id
    if turns and turns[-1].get("role") == role:
        turns[-1] = entry
    else:
        turns.append(entry)
    _CONV_TURN_BUFFER[gate_key] = turns[-_MAX_RECENT_MESSAGES:]


def _is_pure_meta_followup(prompt_text: str, kcs_list: List[Dict[str, Any]]) -> bool:
    """EP-01/H1-A: mensaje meta sin tema propio (marcador + sin match de KC).

    Un mensaje que matchea los marcadores cerrados de diálogo y NO matchea
    ningún KC del catálogo aplicable es discurso conversacional puro: hereda
    el referente académico de la conversación (no aporta vocabulario temático
    propio). Un mensaje con tema explícito («dame un ejemplo de punteros y
    malloc») matchea su KC y queda excluido por diseño.
    """
    if not kcs_list or not prompt_text:
        return False
    lowered = " ".join(prompt_text.lower().split())
    if not any(mk in lowered for mk in _DIALOGUE_META_MARKERS):
        return False
    return _match_kc_id(kcs_list, prompt_text) is None


def _referent_clarification_stream(
    *,
    requested_phase: Optional[str],
    gate_key: Optional[str],
    prompt_text: str,
) -> AsyncGenerator[str, None]:
    """C (EP-01): aclaración breve cuando el referente es ambiguo.

    No delega al episodio, no genera explicación académica y no inventa el
    referente: pide al estudiante la desambiguación explícita. La forma del
    evento replica la clarificación del pipeline (event_type=clarification)
    para que el cliente la presente sin cambios.
    """
    phase_id = requested_phase or "conceptual"

    async def _clarify_gen() -> AsyncGenerator[str, None]:
        _append_dialogue_turn(gate_key, "user", prompt_text)
        message = referent_clarification_message()
        yield (
            "data: "
            + json.dumps(
                {
                    "event_type": "phase_start",
                    "payload": {
                        "phase": phase_id,
                        "pedagogical_mode": "clarification_request",
                        "code_allowed": False,
                        "max_tokens": 0,
                    },
                }
            )
            + "\n\n"
        )
        yield (
            "data: "
            + json.dumps(
                {
                    "event_type": "clarification",
                    "payload": {
                        "phase": phase_id,
                        "abstained": True,
                        "reason": message,
                        "suggested_action": (
                            "Indicame qué explicación querés retomar (el episodio "
                            "o lo último del chat) y la continúo."
                        ),
                        "abstention_code": "CONTEXT_REFERENCE_REQUIRES_CLARIFICATION",
                    },
                }
            )
            + "\n\n"
        )
        _append_dialogue_turn(gate_key, "assistant", "Clarificación: referente ambiguo")

    return _clarify_gen()


def _maybe_dialogue_turn_stream(
    container: AppContainer,
    session_id: Optional[str],
    prompt_text: str,
    requested_phase: Optional[str],
    request: Optional["ChatQueryRequest"] = None,
) -> Optional[AsyncGenerator[str, None]]:
    """M1-03 §5 + EP-01/H1-A: delegación de meta-discurso con referente resuelto.

    Devuelve el stream del turno de diálogo SOLO si TODAS las condiciones
    deterministas se cumplen:
      1. El mensaje matchea marcadores de meta-discurso (listas cerradas).
      2. Existe sesión de estudio con snapshot accesible bajo session_id.
      3. El snapshot tiene episodio activo en fase EXPLAINING/DIALOGUE.
      4. Existe ConceptResponse APROBADA reutilizable para el episodio
         (fail-closed: sin packet aprobado no se genera contenido nuevo).
      5. EP-01: el referente académico inmediato queda VERIFICADO como el del
         episodio (identidad de estudiante/cuaderno/KC consistente; sin tema
         explícito distinto en el mensaje; sin referencia a actividad; sin
         intercambio académico más reciente del chat que compita; sin
         ambigüedad mismo-KC sin desempate). Ante tema distinto o contexto
         incompatible el pipeline del chat procesa la consulta (CHAT_ROUTE);
         ante ambigüedad se emite una aclaración breve (CLARIFY).

    En otro caso devuelve None (pipeline normal de chat). Una vez delegado,
    los errores técnicos se reportan como error SSE, nunca como abstinencia.
    """
    if not prompt_text or not prompt_text.strip():
        return None
    lowered = " ".join(prompt_text.lower().split())
    if not any(mk in lowered for mk in _DIALOGUE_META_MARKERS):
        return None
    if not session_id:
        return None
    orch = getattr(container, "study_session_orchestrator", None)
    if orch is None:
        return None
    try:
        snapshot = orch.get_snapshot(session_id)
    except Exception:
        return None
    episode_id = getattr(snapshot, "episode_id", None)
    episode_phase = getattr(snapshot, "episode_phase", None) or ""
    if not episode_id or episode_phase not in _DIALOGUE_DELEGATE_PHASES:
        return None
    # packet aprobado reutilizable (el turno de diálogo jamás produce
    # contenido fáctico nuevo; sin packet, la delegación no aporta el
    # contrato de continuidad → pipeline normal).
    try:
        from study_engine.web.routes.dialogue import _load_or_reuse_concept_response

        concept_resp = _load_or_reuse_concept_response(
            container.pedagogical_orchestrator, episode_id
        )
    except Exception:
        logger.exception("M1-03 §5: pre-chequeo de packet del episodio falló.")
        return None
    if concept_resp is None or getattr(concept_resp, "packet", None) is None:
        return None

    # EP-01/H1-A: resolver el referente académico ANTES de reutilizar el
    # episodio. La decisión ya no se toma por marcadores + episodio activo
    # solamente: se verifica la identidad del referente con evidencia
    # determinista (packet del episodio, snapshot de sesión, catálogo KC,
    # registro de conversación del servidor o historial sanitizado del
    # cliente). Una coincidencia aproximada nunca se convierte por sí sola
    # en autoridad sobre el referente.
    packet = getattr(concept_resp, "packet", None)
    episode_kc = getattr(packet, "kc_id", None)
    episode_nb = getattr(packet, "notebook_id", None)
    scope_notebook: Optional[str] = None
    if request is not None and getattr(request, "effective_scope_type", None) == "notebook":
        scope_notebook = getattr(request, "effective_scope_id", None) or None
    kcs_list = _referent_kcs_list(container, scope_notebook, episode_nb)
    gate_key = _dialogue_gate_cache_key(request, session_id)
    conversation_turns: List[Dict[str, Any]] = (
        list(_CONV_TURN_BUFFER.get(gate_key) or []) if gate_key else []
    )
    if not conversation_turns and request is not None:
        conversation_turns = _sanitize_recent_turns(
            getattr(request, "recent_turns", None),
            current_prompt=prompt_text,
        )
    recent_referent = resolve_recent_referent(
        conversation_turns,
        lambda text: (_match_kc_id(kcs_list, text) if kcs_list else None),
    )
    message_kc = _match_kc_id(kcs_list, prompt_text) if kcs_list else None
    decision = classify_dialogue_referent(
        message_kc=message_kc,
        recent_referent=recent_referent,
        active_episode_id=episode_id,
        episode_kc=episode_kc,
        episode_notebook=episode_nb,
        scope_notebook=scope_notebook,
        session_student=getattr(snapshot, "student_id", None),
        session_kc=getattr(snapshot, "current_kc_id", None),
        expected_student=CANONICAL_STUDENT_ID,
        activity_referenced=bool(_ACTIVITY_REFERENCE_RE.search(prompt_text)),
    )
    if decision is ReferentDecision.CHAT_ROUTE:
        # B/D: no reutilizar el episodio; el pipeline del chat procesa la
        # consulta por su ruta académica correspondiente.
        return None
    if decision is ReferentDecision.CLARIFY:
        return _referent_clarification_stream(
            requested_phase=requested_phase,
            gate_key=gate_key,
            prompt_text=prompt_text,
        )

    async def _dlg_gen() -> AsyncGenerator[str, None]:
        phase_id = requested_phase or "conceptual"
        # EP-01: registrar el turno delegado en la conversación del servidor
        # para que futuras resoluciones de referente vean que el intercambio
        # académico más reciente perteneció al diálogo de ESTE episodio.
        _append_dialogue_turn(gate_key, "user", prompt_text)
        try:
            from study_engine.web.routes.dialogue import (
                DialogueMessageRequest,
                process_dialogue_turn,
            )

            resp = await process_dialogue_turn(
                episode_id=episode_id,
                req=DialogueMessageRequest(message=prompt_text),
                container=container,
            )
        except Exception:
            logger.exception("M1-03 §5: turno de diálogo delegado falló (fail-closed).")
            _append_dialogue_turn(gate_key, "assistant", "Error técnico: turno no completado")
            yield (
                "data: "
                + json.dumps(
                    {
                        "event_type": "error",
                        "payload": {
                            "phase": phase_id,
                            "message": (
                                "TALOS no pudo completar la respuesta por un "
                                "error técnico. Reintentá la consulta."
                            ),
                        },
                    }
                )
                + "\n\n"
            )
            return

        status = resp.get("status") or ""
        answer = (resp.get("answer") or "").strip()
        abstention_reason = resp.get("abstention_reason")
        audit_verdict = resp.get("audit_verdict")
        sq = resp.get("socratic_question") or {}
        question_text = (sq.get("question_text") or "").strip() if isinstance(sq, dict) else ""

        yield (
            "data: "
            + json.dumps(
                {
                    "event_type": "phase_start",
                    "payload": {
                        "phase": phase_id,
                        "pedagogical_mode": "socratic_dialogue",
                        "code_allowed": False,
                        "max_tokens": 0,
                    },
                }
            )
            + "\n\n"
        )

        composed = answer if not question_text else f"{answer}\n\n{question_text}" if answer else question_text
        verdict = str(audit_verdict or "").upper()
        emitted_tokens = 0
        if status == "ABSTAINED":
            reason = abstention_reason or (
                "TALOS se abstiene de responder: no hay material aprobado para "
                "sostener este turno del diálogo con evidencia."
            )
            _append_dialogue_turn(gate_key, "assistant", f"Abstención: {reason}")
            yield (
                "data: "
                + json.dumps(
                    {
                        "event_type": "abstention",
                        "payload": {
                            "phase": phase_id,
                            "abstained": True,
                            "reason": reason,
                            "abstention_code": str(verdict or "ACADEMIC_OR_UNVERIFIED"),
                        },
                    }
                )
                + "\n\n"
            )
            return

        # Fail-closed de la via S4.4: solo texto con veredicto aprobatorio se
        # emite al estudiante (contrato DialogueEngine.generate: valores
        # válidos "APPROVED" / "AuditVerdict.APPROVED"; el prefijo de enum se
        # normaliza y el resto NUNCA aprueba).
        _verdict_raw = str(audit_verdict or "").upper()
        verdict = _verdict_raw.split(".")[-1] if _verdict_raw else ""
        approved = verdict == "APPROVED"
        if not composed:
            _append_dialogue_turn(gate_key, "assistant", "Error técnico: turno no completado")
            yield (
                "data: "
                + json.dumps(
                    {
                        "event_type": "error",
                        "payload": {
                            "phase": phase_id,
                            "message": (
                                "TALOS no pudo completar la respuesta por un "
                                "error técnico. Reintentá la consulta."
                            ),
                        },
                    }
                )
                + "\n\n"
            )
            return
        if not approved:
            _append_dialogue_turn(gate_key, "assistant", f"Abstención: {verdict or 'REJECTED_UNSUPPORTED'}")
            yield (
                "data: "
                + json.dumps(
                    {
                        "event_type": "abstention",
                        "payload": {
                            "phase": phase_id,
                            "abstained": True,
                            "reason": (
                                "La respuesta de este turno no obtuvo un "
                                "veredicto S4.4 válido y aprobatorio."
                            ),
                            "abstention_code": verdict or "REJECTED_UNSUPPORTED",
                        },
                    }
                )
                + "\n\n"
            )
            return

        # Emisión determinista por trozos (sin latencias artificiales).
        # Manifest de evidencia del turno para identidad de citas (los chips
        # [E#] se resuelven por citation_id/namespace, nunca por posición).
        citations_payload = resp.get("citations") or []
        if isinstance(citations_payload, list) and citations_payload:
            yield (
                "data: "
                + json.dumps(
                    {
                        "event_type": "evidence_manifest",
                        "payload": {
                            "citations": citations_payload,
                            "facet_coverage": {},
                            "abstained": False,
                            "abstention_reason": None,
                        },
                    }
                )
                + "\n\n"
            )
        CHUNK = 48
        for i in range(0, len(composed), CHUNK):
            yield (
                "data: "
                + json.dumps(
                    {
                        "event_type": "phase_token",
                        "payload": {"phase": phase_id, "token": composed[i : i + CHUNK]},
                    }
                )
                + "\n\n"
            )
            emitted_tokens += 1
        yield (
            "data: "
            + json.dumps(
                {
                    "event_type": "audit_verdict",
                    "payload": {
                        "phase": phase_id,
                        "verdict": verdict or "APPROVED",
                        "metrics": {"dialogue_episodio": episode_id},
                    },
                }
            )
            + "\n\n"
        )
        yield (
            "data: "
            + json.dumps(
                {
                    "event_type": "phase_complete",
                    "payload": {
                        "completed_phase": phase_id,
                        "tokens_produced": emitted_tokens,
                        "next_phases": ["pseudocode", "python_code"],
                        "decision": {"message": composed},
                    },
                }
            )
            + "\n\n"
        )
        # EP-01: el turno aprobado del episodio queda registrado como el
        # intercambio académico más reciente, con el marcado de episodio que
        # permite verificar futuras continuaciones sin ambigüedad.
        _append_dialogue_turn(
            gate_key,
            "assistant",
            composed,
            episode_id=episode_id,
            kc_id=episode_kc,
        )

    return _dlg_gen()


@router.post("/query")
async def chat_query(
    request: ChatQueryRequest,
    container: AppContainer = Depends(get_container),
) -> StreamingResponse:
    """Execute streaming phased pedagogical query using StructuredResponsePipeline."""
    raw_prompt = request.prompt or request.query or ""
    if not raw_prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'prompt' or 'query' must be provided and non-empty.",
        )
    if not request.session_id:
        request.session_id = f"chat-{uuid4().hex}"

    from study_engine.pedagogy.command_parser import CommandType, parse_student_command
    command = parse_student_command(raw_prompt)
    if command is not None and command.command_type == CommandType.DAME_UN_EJERCICIO:
        from study_engine.pedagogy.exercise_store import ExerciseStore
        exercise_store = getattr(container, "exercise_store", None)
        if exercise_store is None:
            exercise_store = ExerciseStore()

        exercise = None
        if exercise_store is not None:
            all_qual = [ex for ex in exercise_store.list_all() if ex.is_presentable()]
            target_topic = (command.target_arg or "").strip()
            if target_topic:
                norm_t = target_topic.lower().strip()
                matches = [
                    ex for ex in all_qual
                    if (ex.kc_id and norm_t in ex.kc_id.lower())
                    or (ex.prompt and norm_t in ex.prompt.lower())
                ]
                if matches:
                    exercise = matches[0]
            elif all_qual:
                exercise = all_qual[0]

        async def exercise_dispatch_stream() -> AsyncGenerator[str, None]:
            if exercise is None:
                yield f"data: {json.dumps({'event_type': 'evidence_manifest', 'payload': {'citations': [], 'facet_coverage': {}, 'abstained': True, 'abstention_reason': 'QUERY_OUT_OF_SCOPE', 'trust_status': 'NO_EVIDENCE'}})}\n\n"
                yield f"data: {json.dumps({'event_type': 'abstention', 'payload': {'phase': request.requested_phase or 'conceptual', 'abstained': True, 'reason': 'TALOS se abstiene de responder: No existe una práctica certificada y autorizada para este tema.', 'suggested_action': 'Consultá el catálogo de fuentes del cuaderno o reformulá la pregunta con términos del programa.', 'abstention_code': 'QUERY_OUT_OF_SCOPE', 'trust_status': 'NO_EVIDENCE', 'notebook_id': request.scope_id or request.scope_id}})}\n\n"
                return

            proposal_payload = {
                'exercise_id': exercise.exercise_id,
                'kc_id': exercise.kc_id,
                'title': (exercise.prompt or '')[:80],
                'prompt': exercise.prompt,
                'type': getattr(exercise.exercise_type, 'value', str(exercise.exercise_type)),
                'options': list(exercise.options) if exercise.options else None,
            }
            yield f"data: {json.dumps({'event_type': 'evidence_manifest', 'payload': {'citations': [], 'facet_coverage': {'exercise': exercise.kc_id}, 'abstained': False, 'trust_status': 'SUFFICIENT_EVIDENCE'}})}\n\n"
            yield f"data: {json.dumps({'event_type': 'exercise_proposal', 'payload': proposal_payload})}\n\n"
            yield f"data: {json.dumps({'event_type': 'phase_complete', 'payload': {'completed_phase': request.requested_phase or 'conceptual', 'status': 'EXERCISE_PROPOSED', 'exercise_id': exercise.exercise_id}})}\n\n"

        return StreamingResponse(
            exercise_dispatch_stream(),
            media_type="text/event-stream",
        )

    # Pre-flight DataSanitizer check for Accidental PII / Credentials (Ola 5, Fase 5.1)
    from study_engine.security.data_sanitizer import DataSanitizer
    data_sanitizer = DataSanitizer()
    scrub_res = data_sanitizer.scrub(raw_prompt)
    if scrub_res.has_pii:
        detected_str = ", ".join(scrub_res.detected_patterns)
        logger.warning("Accidental PII detected in prompt. Request blocked. Patterns: %s", detected_str)

        async def pii_blocked_stream() -> AsyncGenerator[str, None]:
            manifest = {
                "event_type": "evidence_manifest",
                "payload": {
                    "citations": [],
                    "facet_coverage": {},
                    "abstained": True,
                    "abstention_reason": "ACCIDENTAL_PII_BLOCKED",
                },
            }
            yield f"data: {json.dumps(manifest)}\n\n"

            msg = (
                "⚠️ **Aviso de Seguridad:** Detecté información sensible o credenciales en tu mensaje "
                f"({detected_str}).\n\n"
                "Por política de privacidad soberana de TALOS, no enviamos credenciales, claves API ni "
                "datos personales a proveedores externos.\n\n"
                "Por favor, eliminá la clave o reemplazala por un valor genérico (ej: `<MI_API_KEY>` o `00000000`) "
                "y volvé a consultar."
            )
            block_event = {
                "event_type": "phase_start",
                "payload": {"phase": "pii_guard", "max_tokens": 200, "code_allowed": False},
            }
            yield f"data: {json.dumps(block_event)}\n\n"
            for word in msg.split(" "):
                await asyncio.sleep(0.005)
                tok_event = {"event_type": "phase_token", "payload": {"phase": "pii_guard", "token": word + " "}}
                yield f"data: {json.dumps(tok_event)}\n\n"
            comp_event = {
                "event_type": "phase_complete",
                "payload": {"completed_phase": "pii_guard", "status": "BLOCKED_PII", "patterns": scrub_res.detected_patterns},
            }
            yield f"data: {json.dumps(comp_event)}\n\n"

        return StreamingResponse(pii_blocked_stream(), media_type="text/event-stream")

    # SANITIZACIÓN PREVIA (Fix 2.3)
    if hasattr(container, "sanitizer") and container.sanitizer:
        prompt_text = container.sanitizer.sanitize(raw_prompt)
    else:
        prompt_text = raw_prompt.strip()

    # M1-03 §5 (delegación de meta-discurso al diálogo del episodio activo):
    # en el cliente REAL los turnos del diálogo socrático (reformulaciones,
    # pedidos de ejemplo, señales de confusión) llegan por /api/chat/query
    # con el session_id de la sesión de estudio activa. Sin delegación, el
    # gate C5 los trata como consultas de contenido y abstenidos
    # QUERY_OUT_OF_SCOPE (hallazgo del escenario de 8 pasos en navegador:
    # "no entiendo, explícame de otra forma" → abstinencia, rompiendo la
    # continuidad pedagógica). La delegación es acotada y fail-closed:
    # solo mensajes meta (marcadores deterministas), solo si existe sesión
    # con episodio activo en fase de diálogo Y un ConceptPacket ya APROBADO
    # por S4.4 (no se genera contenido nuevo ni se re-audita lo aprobado).
    # Los mensajes de contenido (ej. afirmaciones erróneas sobre el tema)
    # conservan el pipeline completo de chat (retrieval + S4.4) que maneja
    # la corrección fundada. Un fallo técnico una vez comprometida la
    # delegación se reporta como error técnico, nunca como abstinencia.
    dialogue_stream = _maybe_dialogue_turn_stream(
        container=container,
        session_id=request.session_id,
        prompt_text=prompt_text,
        requested_phase=request.requested_phase,
        request=request,
    )
    if dialogue_stream is not None:
        return StreamingResponse(dialogue_stream, media_type="text/event-stream")

    store = container.knowledge_store
    resolver = getattr(container, "scope_resolver", None) or ScopeResolver(store)
    target_scope_type = request.effective_scope_type
    target_scope_id = request.effective_scope_id

    # Sincronización I/O en threadpool para no bloquear el event loop (Fix 1.2)
    try:
        resolved_scope, contract, context_pack, raw_chunks, folder_decision, context_mode, bkt_directive, style_result, conv_payload, matched_kc_id, bkt_meta = await asyncio.to_thread(
            _prepare_chat_context,
            store=store,
            resolver=resolver,
            container=container,
            prompt_text=prompt_text,
            request=request,
            target_scope_type=target_scope_type,
            target_scope_id=target_scope_id,
        )
    except ScopeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if folder_decision is not None:
        return _handle_folder_streaming(folder_decision)

    if conv_payload is not None:
        fastpath, route_kind, context = conv_payload
        llm_backend = _resolve_chat_backend(container)
        reply_text = await fastpath.generate_response(
            query=prompt_text,
            route_kind=route_kind,
            context=context,
            llm_backend=llm_backend,
        )
        return StreamingResponse(
            fastpath.stream_fastpath_events(reply_text, route_kind),
            media_type="text/event-stream",
        )

    target_notebook_id = (
        GLOBAL_SCOPE_ID
        if resolved_scope.scope_type == ScopeType.FOLDER
        else (resolved_scope.notebook_id or target_scope_id)
    )
    history_key = f"{request.session_id or 'anon'}:{target_notebook_id}"
    context_cache_key = _request_context_cache_key(
        request,
        resolved_scope,
        target_notebook_id,
    )

    from study_engine.pedagogy.solution_protection import is_protected_assessment

    resolved_item = getattr(context_pack, "resolved_item", None) if context_pack is not None else None
    if resolved_item is not None:
        if is_protected_assessment(resolved_item):
            _ACTIVE_PROTECTED_ASSESSMENTS[context_cache_key] = resolved_item.content_id
        else:
            _ACTIVE_PROTECTED_ASSESSMENTS.pop(context_cache_key, None)
    elif context_cache_key in _ACTIVE_PROTECTED_ASSESSMENTS:
        active_content_id = _ACTIVE_PROTECTED_ASSESSMENTS.get(context_cache_key)
        registry = getattr(store, "content_registry", None)
        resolved_item = registry.get(active_content_id) if registry and active_content_id else None
        if not is_protected_assessment(resolved_item):
            _ACTIVE_PROTECTED_ASSESSMENTS.pop(context_cache_key, None)

    protected_assessment = is_protected_assessment(resolved_item)
    protected_solutions = (
        _protected_solutions_for_item(store, resolved_item)
        if protected_assessment and resolved_item is not None
        else []
    )

    bkt_directive = maybe_inject_session_digest(container, history_key, bkt_directive)
    if request.requested_phase == "conceptual" and history_key in _ACTIVE_TURN_HISTORIES:
        _ACTIVE_TURN_HISTORIES[history_key].clear()

    phase_history = _ACTIVE_TURN_HISTORIES.setdefault(history_key, PhaseHistory())

    # Estimación rápida de tokens de entrada (1 token ≈ 4 caracteres en español)
    # Si supera los 5.000 tokens, _resolve_chat_backend prioriza Gemini / Cloudflare Direct
    # para evitar rebotar contra el límite estricto de 7.000 ITPM de la capa gratuita de Groq.
    ctx_len = len(context_pack.formatted_context) if context_pack and getattr(context_pack, "formatted_context", None) else 0
    sys_prompt_len = len(getattr(contract, "base_system_prompt", "")) if contract else 10000
    estimated_input_tokens = (sys_prompt_len + ctx_len + len(prompt_text)) // 4

    llm_backend = _resolve_chat_backend(container, estimated_tokens=estimated_input_tokens)

    # Memoria de corto plazo (Fase 2): recuperar buffer de turnos y registrar el turno actual del usuario.
    server_turns = _CONV_TURN_BUFFER.get(context_cache_key)
    conv_turns: list = _resolve_conversation_turns(
        server_turns=server_turns,
        client_turns=request.recent_turns,
        current_prompt=prompt_text,
    )
    conversation_context = _conversation_context_metadata(
        server_turns=server_turns,
        client_turns=request.recent_turns,
        resolved_turns=conv_turns,
        current_prompt=prompt_text,
    )
    # Registrar el turno del usuario en el buffer (se completa con la respuesta al finalizar)
    conv_turns.append({"role": "user", "content": prompt_text})

    pipeline = StructuredResponsePipeline(
        contract=contract,
        llm_backend=llm_backend,
        phase_history=phase_history,
        auditor=getattr(container, "auditor", None),
    )
    if hasattr(container, "last_abstention_decision"):
        pipeline._last_abstention_decision = getattr(container, "last_abstention_decision")
    elif hasattr(container.controller, "last_abstention_decision"):
        pipeline._last_abstention_decision = getattr(container.controller, "last_abstention_decision")

    async def sse_generator() -> AsyncGenerator[str, None]:
        try:
            # C5 Universal Trust Gate (Fail-Closed Absoluto - D_C5_4 & D_C5_5 & Addendum 2)
            is_sufficient = getattr(context_pack, "is_sufficient", False) if context_pack is not None else False
            is_abstained = getattr(context_pack, "abstained", True) if context_pack is not None else True
            trust_status = getattr(context_pack, "trust_status", EpistemicTrustStatus.NO_EVIDENCE) if context_pack is not None else EpistemicTrustStatus.RETRIEVAL_FAILURE

            if context_pack is None or is_abstained or not is_sufficient:
                _trigger_background_memory_extraction(
                    container=container,
                    student_id=CANONICAL_STUDENT_ID,
                    prompt_text=prompt_text,
                    response_text="",
                    active_kc=matched_kc_id,
                    pedagogical_mode=None,
                    llm_backend=None,
                    notebook_id=target_notebook_id,
                )

                reason = getattr(context_pack, "abstention_reason", None) or (
                    "RETRIEVAL_FAILURE" if (context_pack is None or trust_status == EpistemicTrustStatus.RETRIEVAL_FAILURE) else "QUERY_OUT_OF_SCOPE"
                )
                clarification_message = getattr(context_pack, "clarification_message", None) if context_pack is not None else None
                abstention_decision = getattr(pipeline, "_last_abstention_decision", None)
                if abstention_decision and getattr(abstention_decision, "abstention_reason", None):
                    reason = getattr(abstention_decision, "abstention_reason")

                manifest_payload = {
                    "event_type": "evidence_manifest",
                    "payload": {
                        "citations": [],
                        "facet_coverage": {},
                        "abstained": True,
                        "abstention_reason": reason,
                        "trust_status": trust_status.value if hasattr(trust_status, "value") else str(trust_status),
                    },
                }
                yield f"data: {json.dumps(manifest_payload)}\n\n"

                is_retrieval_err = (context_pack is None or trust_status == EpistemicTrustStatus.RETRIEVAL_FAILURE or reason == "RETRIEVAL_FAILURE")
                event_name = "error" if is_retrieval_err else ("clarification" if clarification_message else "abstention")
                abstention_payload = {
                    "event_type": event_name,
                    "payload": {
                        "phase": request.requested_phase or "conceptual",
                        "abstained": True,
                        "reason": (
                            "TALOS falló de forma segura (fail-closed): Ocurrió un error técnico al recuperar evidencias canónicas."
                            if is_retrieval_err
                            else (clarification_message or (
                                reason if reason and reason != "QUERY_OUT_OF_SCOPE" else
                                "TALOS se abstiene de responder: No se hallaron evidencias curriculares "
                                "verificables en las fuentes canónicas del cuaderno para fundamentar esta consulta."
                            ))
                        ),
                        "suggested_action": "Reintentá la consulta en unos instantes o consultá el catálogo del cuaderno." if is_retrieval_err else "Consultá el catálogo de fuentes del cuaderno o reformulá la pregunta con términos del programa.",
                        "abstention_code": reason,
                        "trust_status": trust_status.value if hasattr(trust_status, "value") else str(trust_status),
                        "notebook_id": target_notebook_id,
                    },
                }
                conv_turns.append({"role": "assistant", "content": f"Abstención: {reason}"})
                _CONV_TURN_BUFFER[context_cache_key] = conv_turns[-_MAX_RECENT_MESSAGES:]
                yield f"data: {json.dumps(abstention_payload)}\n\n"
                return

            from study_engine.pedagogy.structured_pipeline import (
                classify_pedagogical_intent,
                resolve_response_intent,
            )
            conv_intent = classify_pedagogical_intent(prompt_text)
            response_intent = resolve_response_intent(prompt_text, conv_intent)
            style_dir = _style_directive_for_task(style_result, response_intent.task)

            if protected_assessment and (
                protected_solutions is None
                or response_intent.task == "entregar solución completa solicitada"
            ):
                from study_engine.pedagogy.solution_protection import (
                    PROTECTED_ASSESSMENT_REFUSAL,
                    PROTECTED_ASSESSMENT_UNAVAILABLE,
                )

                refusal = (
                    PROTECTED_ASSESSMENT_UNAVAILABLE
                    if protected_solutions is None
                    else PROTECTED_ASSESSMENT_REFUSAL
                )
                phase_id = request.requested_phase or "conceptual"
                start_event = {
                    "event_type": "phase_start",
                    "payload": {
                        "phase": phase_id,
                        "code_allowed": False,
                        "protected_assessment": True,
                    },
                }
                token_event = {
                    "event_type": "phase_token",
                    "payload": {"phase": phase_id, "token": refusal},
                }
                complete_event = {
                    "event_type": "phase_complete",
                    "payload": {
                        "completed_phase": phase_id,
                        "status": (
                            "PROTECTED_ASSESSMENT_UNAVAILABLE"
                            if protected_solutions is None
                            else "PROTECTED_ASSESSMENT_BLOCKED"
                        ),
                        "protected_assessment": True,
                    },
                }
                for event in (start_event, token_event):
                    yield f"data: {json.dumps(event)}\n\n"
                conv_turns.append({"role": "assistant", "content": refusal})
                _CONV_TURN_BUFFER[context_cache_key] = conv_turns[-_MAX_RECENT_MESSAGES:]
                yield f"data: {json.dumps(complete_event)}\n\n"
                return

            # Mantener el presupuesto introductorio de basic acotado y el techo completo para los demás modos.
            if not request.requested_phase or request.requested_phase == "conceptual":
                live_max_tokens = 800 if context_mode == "basic" else 3500
            else:
                live_max_tokens = None
            accumulated_response_text = ""
            pending_ui_tokens: List[Dict[str, Any]] = []
            audited_verdict_payload: Optional[Dict[str, Any]] = None
            audited_content_hash: Optional[str] = None
            audited_binding_id: Optional[str] = None
            expected_binding_id = uuid4().hex

            # Validador de citas y buffer de streaming (Fase 2 + Commit 1 + Enmienda E-UX1)
            from study_engine.pedagogy.citation_validator import CitationValidator, StreamCitationBuffer
            citation_validator = CitationValidator()
            # Enmienda E-UX1: strip_invalid=True emite prosa limpia a la UI y guarda telemetría en backend
            stream_citation_buf = StreamCitationBuffer(
                citation_validator,
                raw_chunks,
                strip_invalid=True,
            )

            ref_disclaimer = getattr(context_pack, "reference_disclaimer", None) if context_pack else None

            # Slice 3: Construir bloque de perfil cognitivo dinámico (<120 tokens)
            prof_injector = getattr(container, "profile_injector", None)
            cognitive_block = _build_cognitive_profile_block(prof_injector, matched_kc_id)

            protected_solution_blocked = False
            async for event in pipeline.generate_phased_response(
                user_query=prompt_text,
                context_pack=context_pack,
                requested_phase=request.requested_phase or "conceptual",
                pedagogical_mode=conv_intent,
                # EP-02/H1-B: transporte de la directiva adaptativa compuesta
                # (BKT/dificultad/andamiaje/espiral/digest) al consumidor real
                # de generación. Calculada en `_prepare_chat_context` para el
                # KC matcheado de ESTE turno y esta sesión (identidad y scope
                # por construcción); el presupuesto C3 la contabiliza
                # (`enforce_c3_budget(bkt_directive=...)`) y S4.4 sigue
                # auditando el texto resultante (la directiva adapta, no
                # sustituye evidencia).
                bkt_directive=bkt_directive,
                style_directive=style_dir,
                override_max_tokens=live_max_tokens,
                recent_turns=conv_turns,
                cognitive_profile_block=cognitive_block,
                context_mode=context_mode,
                protected_assessment=protected_assessment,
                content_binding_id=expected_binding_id,
            ):
                payload = {
                    "event_type": event.event_type,
                    "payload": event.payload,
                }

                if event.event_type == "phase_token":
                    token_str = event.payload.get("token", "")
                    emitted_tokens = stream_citation_buf.process_token(token_str)
                    for em_tok in emitted_tokens:
                        accumulated_response_text += em_tok
                        pending_ui_tokens.append({
                            "event_type": "phase_token",
                            "payload": {**event.payload, "token": em_tok},
                        })
                    continue

                if event.event_type == "audit_verdict":
                    # The route must not release or transform content until it
                    # has retained the binding produced by the pipeline.
                    audited_verdict_payload = payload
                    event_payload = event.payload
                    if isinstance(event_payload, dict):
                        audited_content_hash = event_payload.get("content_sha256")
                        audited_binding_id = event_payload.get("content_binding_id")
                    continue

                if event.event_type == "abstention":
                    if audited_verdict_payload is not None:
                        bound_audit = _bind_audit_event(
                            audited_verdict_payload, session_id=request.session_id,
                            scope_type=target_scope_type, scope_id=target_scope_id, emission="blocked",
                        )
                        yield f"data: {json.dumps(bound_audit)}\n\n"
                    yield f"data: {json.dumps(payload)}\n\n"
                    continue

                if event.event_type == "phase_complete":
                    # 1. Flushear cualquier fragmento retenido en el lookahead buffer
                    for fl_tok in stream_citation_buf.flush():
                        accumulated_response_text += fl_tok
                        pending_ui_tokens.append({
                            "event_type": "phase_token",
                            "payload": {"phase": request.requested_phase or "conceptual", "token": fl_tok},
                        })

                    # 2. Reescritura canónica determinista de citas (Commit 1)
                    accumulated_response_text, invalid_citations = citation_validator.validate_and_rewrite(
                        text=accumulated_response_text,
                        chunks=raw_chunks,
                    )
                    if protected_assessment:
                        from study_engine.pedagogy.solution_protection import (
                            PROTECTED_ASSESSMENT_REFUSAL,
                            contains_protected_solution,
                        )

                        if contains_protected_solution(accumulated_response_text, protected_solutions or []):
                            protected_solution_blocked = True
                            logger.warning(
                                "Respuesta bloqueada por coincidencia con solucionario protegido (content_id=%s)",
                                getattr(resolved_item, "content_id", "unknown"),
                            )
                            accumulated_response_text = PROTECTED_ASSESSMENT_REFUSAL
                        if isinstance(payload.get("payload"), dict):
                            payload["payload"]["protected_assessment"] = True
                            if protected_solution_blocked:
                                payload["payload"]["status"] = "PROTECTED_ASSESSMENT_BLOCKED"
                        if accumulated_response_text:
                            pending_ui_tokens = [{
                                "event_type": "phase_token",
                                "payload": {
                                    "phase": request.requested_phase or "conceptual",
                                    "token": accumulated_response_text,
                                },
                            }]

                    # The pipeline's hash covers the exact text it audited.
                    # Any route-level rewrite, prefix, or substitution is a
                    # fail-closed mismatch and must not release buffered text.
                    approved_verdicts = {"APPROVED", "AuditVerdict.APPROVED"}
                    route_verdict = None
                    if audited_verdict_payload is not None:
                        route_payload = audited_verdict_payload.get("payload", {})
                        if isinstance(route_payload, dict):
                            route_verdict = route_payload.get("verdict")
                    final_content_hash = hashlib.sha256(
                        accumulated_response_text.encode("utf-8")
                    ).hexdigest()
                    if (
                        route_verdict not in approved_verdicts
                        or not _route_content_binding_matches(
                            audited_content_hash,
                            accumulated_response_text,
                            audited_binding_id,
                            expected_binding_id,
                        )
                    ):
                        rejection_payload = {
                            "event_type": "audit_verdict",
                            "payload": {
                                "phase": request.requested_phase or "conceptual",
                                "verdict": (
                                    "AUDIT_RESULT_MISSING"
                                    if audited_verdict_payload is None
                                    else "REJECTED_INPUT_MISMATCH"
                                ),
                                "content_sha256": final_content_hash,
                                "content_binding_id": expected_binding_id,
                            },
                        }
                        yield f"data: {json.dumps(rejection_payload)}\n\n"
                        abstention_payload = {
                            "event_type": "abstention",
                            "payload": {
                                "phase": request.requested_phase or "conceptual",
                                "abstained": True,
                                "reason": (
                                    "La respuesta no tiene un binding válido entre el contenido auditado y el emitido."
                                ),
                                "abstention_code": rejection_payload["payload"]["verdict"],
                            },
                        }
                        yield f"data: {json.dumps(abstention_payload)}\n\n"
                        return

                    valid_citations, _ = citation_validator.audit_only(
                        text=accumulated_response_text,
                        chunks=raw_chunks,
                    )
                    # Enmienda E-UX1: Telemetría de citas huérfanas / alucinadas detectadas
                    all_invalid = list(set(invalid_citations + getattr(stream_citation_buf, "stripped_citations", [])))
                    if all_invalid:
                        logger.warning(
                            "[TELEMETRY E-UX1] Citas huérfanas o alucinadas sanitizadas: %s (válidas: %s)",
                            all_invalid,
                            valid_citations,
                        )
                        audit_payload = {
                            "event_type": "citation_audit",
                            "payload": {
                                "valid_citations": valid_citations,
                                "invalid_citations": all_invalid,
                                "citation_count": len(valid_citations),
                                "stripped_from_stream": getattr(stream_citation_buf, "stripped_citations", []),
                            },
                        }
                        yield f"data: {json.dumps(audit_payload)}\n\n"

                    # Sanitizar buffer de memoria conversacional (eliminar tokens residuales para evitar contaminación in-context)
                    clean_saved_text = re.sub(r"\s*\[ref\. no verificada\]\s*", " ", accumulated_response_text)
                    clean_saved_text = re.sub(r"\s+([.,;:!?])", r"\1", clean_saved_text).strip()
                    clean_saved_text = re.sub(r"  +", " ", clean_saved_text)

                    # Guardar el historial conversacional acotado en el buffer efímero.
                    conv_turns.append({"role": "assistant", "content": clean_saved_text})
                    _CONV_TURN_BUFFER[context_cache_key] = conv_turns[-_MAX_RECENT_MESSAGES:]

                    # Enriquecer payload de phase_complete con telemetría cognitiva BKT (Fase 3)
                    if isinstance(payload.get("payload"), dict):
                        if bkt_meta is None:
                            logger.warning(
                                "bkt_meta is None on notebook path (%s); using empty BKT fallback",
                                target_notebook_id,
                            )
                        safe_bkt = bkt_meta if isinstance(bkt_meta, dict) else {}
                        payload["payload"]["bkt_context"] = {
                            "kc_id": matched_kc_id,
                            "context_mode": context_mode,
                            "p_L": safe_bkt.get("p_L", 0.5),
                            "unmet_prerequisites": safe_bkt.get("unmet_prerequisites", []),
                            # F3: True cuando ningún KC matcheó la query; los
                            # valores son neutrales (p_L=0.5) y NO corresponden
                            # a un KC real del catálogo.
                            "fallback": matched_kc_id is None,
                        }
                        payload["payload"]["fallback_disclaimer"] = (matched_kc_id is None)
                        payload["payload"]["conversation_context"] = conversation_context
                        payload["payload"]["evidence_provenance"] = [
                            {
                                "citation_id": chunk.get("citation_id") or chunk.get("id"),
                                "source_id": chunk.get("source_id"),
                                "source_title": chunk.get("source_title"),
                                "author": chunk.get("author"),
                                "page_start": chunk.get("page_start"),
                                "page_end": chunk.get("page_end"),
                                "document_id": chunk.get("document_id"),
                                "chunk_id": chunk.get("chunk_id"),
                                "doc_hash": chunk.get("doc_hash"),
                                "epistemic_role": chunk.get("epistemic_role"),
                                **({key: chunk.get(key) for key in (
                                    "notebook_id", "bridge_id", "plan_id", "content_hash",
                                )} if chunk.get("plan_id") else {}),
                            }
                            for chunk in raw_chunks
                        ]
                        payload["payload"]["evidence_discrepancies"] = _detect_evidence_discrepancies(raw_chunks)
                        if ref_disclaimer:
                            payload["payload"]["reference_disclaimer"] = ref_disclaimer

                    _update_curriculum_progress(
                        container=container,
                        target_notebook_id=target_notebook_id,
                        prompt_text=prompt_text,
                        raw_chunks=raw_chunks,
                    )
                    _trigger_background_memory_extraction(
                        container=container,
                        student_id=CANONICAL_STUDENT_ID,
                        prompt_text=prompt_text,
                        response_text=accumulated_response_text,
                        active_kc=matched_kc_id,
                        pedagogical_mode=conv_intent,
                        llm_backend=llm_backend,
                        notebook_id=target_notebook_id,
                    )

                    # Release only after every route-level transformation has
                    # been checked against the pipeline's audited digest.
                    # Keep the audit verdict before all released phase content.
                    if audited_verdict_payload is not None:
                        bound_audit = _bind_audit_event(
                            audited_verdict_payload, session_id=request.session_id,
                            scope_type=target_scope_type, scope_id=target_scope_id, emission="authorized",
                        )
                        yield f"data: {json.dumps(bound_audit)}\n\n"
                    if not protected_assessment:
                        for token_payload in pending_ui_tokens:
                            yield f"data: {json.dumps(token_payload)}\n\n"

                    # Fase 5.3: loop de evaluación — tras N turnos seguidos sobre
                    # el mismo KC, proponer ejercicio certificado (fail-closed).
                    if request.requested_phase in (None, "conceptual") and matched_kc_id:
                        streak = _KC_TURN_STREAKS.get(history_key) or {"kc_id": None, "count": 0}
                        if streak.get("kc_id") == matched_kc_id:
                            streak["count"] = int(streak.get("count", 0)) + 1
                        else:
                            streak = {"kc_id": matched_kc_id, "count": 1}
                        _KC_TURN_STREAKS[history_key] = streak

                        from study_engine.pedagogy.exercise_service import (
                            select_or_generate,
                            should_propose,
                            to_proposal_payload,
                        )
                        bkt_state = container.bkt_tracker.get_state(matched_kc_id) if getattr(container, "bkt_tracker", None) else None
                        attempts = getattr(bkt_state, "attempts", 0) if bkt_state else 0
                        if should_propose(streak["count"], attempts=attempts):
                            exercise = select_or_generate(
                                getattr(container, "exercise_store", None),
                                getattr(container, "generated_registry", None),
                                matched_kc_id,
                                catalog=getattr(getattr(container, "pedagogical_orchestrator", None), "_kc_catalog", None),
                            )
                            if exercise is not None:
                                _KC_TURN_STREAKS[history_key] = {"kc_id": matched_kc_id, "count": 0}
                                yield f"data: {json.dumps({'event_type': 'exercise_proposal', 'payload': to_proposal_payload(exercise)})}\n\n"

                yield f"data: {json.dumps(payload)}\n\n"
        except asyncio.CancelledError:
            # Fix 3.3: Cliente desconectado, registrar y salir sin emitir SSE a socket cerrado
            logger.info("Cliente desconectado durante streaming SSE de chat (%s)", target_notebook_id)
            return
        except Exception as e:
            logger.warning("Fallo en generación streaming de chat: %s", e, exc_info=True)
            err_payload = {
                "event_type": "error",
                "payload": {
                    "reason": (
                        "TALOS no pudo completar la respuesta por un error técnico. "
                        "Reintentá la consulta."
                    )
                },
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Fase 5.3 — Loop de evaluación determinista (graders + BKT)
# ---------------------------------------------------------------------------

class ExerciseEvaluateRequest(BaseModel):
    """Respuesta del estudiante a un ejercicio certificado."""

    model_config = ConfigDict(strict=True)

    exercise_id: str = Field(..., min_length=1, max_length=128)
    user_answer: str = Field(..., min_length=1, max_length=2000)
    notebook_id: Optional[str] = Field(default=None, description="Contexto opcional del cuaderno")
    session_id: Optional[str] = Field(default=None, min_length=1, description="ID de sesión para delimitar el intento")
    episode_id: Optional[str] = Field(default=None, min_length=1, description="Episodio activo asociado a la propuesta, si existe")
    attempt_id: Optional[str] = Field(default=None, min_length=1, description="Identidad estable del intento")


def _remediation_message(kc_id: str, exercise: Any, p_l: float) -> str:
    """Mensaje corto de remediación post-error (sin LLM)."""
    prompt_line = (getattr(exercise, "prompt", "") or "").split("\n")[0][:90]
    return (
        f"Revisemos el concepto de '{kc_id}': volvé a la explicación anterior y contrastala "
        f"con el ejercicio '{prompt_line}…'. Nivel actual estimado p_L={p_l:.2f}; "
        "cuando quieras, pedime una pista con ':hint' o un repaso del tema."
    )


@router.post("/evaluate")
async def evaluate_exercise_answer(
    req: ExerciseEvaluateRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Evaluate with a durable session/attempt key and fail closed if identity is missing."""
    storage = getattr(container, "student_storage", None)
    if not req.session_id or not req.attempt_id or storage is None:
        return {
            "status": "UNGRADED",
            "exercise_id": req.exercise_id,
            "is_correct": None,
            "p_L": None,
            "delta_p_L": 0.0,
            "remediation": None,
            "detail": "Se requieren session_id, attempt_id y persistencia para evaluar de forma idempotente.",
        }

    operation_scope = req.episode_id or "chat-exercise-evaluation"
    request_digest = hashlib.sha256(
        json.dumps(req.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    reservation, payload = storage.begin_operation_receipt(
        session_id=req.session_id,
        episode_id=operation_scope,
        exercise_id=req.exercise_id,
        attempt_id=req.attempt_id,
        request_digest=request_digest,
    )
    if reservation == "CONFLICT":
        raise HTTPException(status_code=409, detail="attempt_id ya fue usado con otro contenido.")
    if reservation == "REPLAY" and payload is not None:
        replay = json.loads(payload)
        replay.pop("_struggle_state", None)
        replay["was_idempotent_replay"] = True
        return replay
    if reservation == "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="El intento anterior quedó incompleto; no se reejecutará automáticamente.")
    if reservation != "STARTED":
        raise HTTPException(status_code=409, detail="No se pudo reservar la identidad del intento.")

    # The durable IN_PROGRESS marker is committed first. All subsequent SQLite
    # learning-state writes and receipt completion then share one outer transaction.
    with storage.transaction():
        container.study_session_orchestrator.require_open_session(req.session_id)
        result = await _evaluate_exercise_answer_once(req, container)
        result["was_idempotent_replay"] = False
        storage.complete_operation_receipt(
            session_id=req.session_id,
            episode_id=operation_scope,
            exercise_id=req.exercise_id,
            attempt_id=req.attempt_id,
            request_digest=request_digest,
            result_json=json.dumps(result, sort_keys=True),
        )
        result.pop("_struggle_state", None)
        return result


async def _evaluate_exercise_answer_once(
    req: ExerciseEvaluateRequest,
    container: AppContainer,
) -> Dict[str, Any]:
    """Califica una respuesta de ejercicio con grader determinista y muta BKT.

    Fail-closed (espeja dialogue.py): sin ejercicio certificado o sin clave,
    retorna UNGRADED y NO muta BKT. Nunca califica con LLM.
    """
    from study_engine.student.contracts import ExerciseFormat, ObservationSource

    exercise_store = getattr(container, "exercise_store", None)
    stored_exercise = exercise_store.get_exercise_by_id(req.exercise_id) if exercise_store else None
    exercise = exercise_store.get_evaluable_exercise_by_id(req.exercise_id) if exercise_store else None

    def ungraded(reason: str) -> Dict[str, Any]:
        return {
            "status": "UNGRADED",
            "exercise_id": req.exercise_id,
            "is_correct": None,
            "p_L": None,
            "delta_p_L": 0.0,
            "remediation": None,
            "detail": reason,
        }

    session_orchestrator = getattr(container, "study_session_orchestrator", None)
    if session_orchestrator is None:
        return ungraded("Sesión persistida no disponible; evaluación omitida.")
    try:
        session_snapshot = session_orchestrator.get_snapshot(req.session_id)
    except Exception:
        return ungraded("session_id no corresponde a una sesión persistida activa.")
    if req.notebook_id is not None and req.notebook_id != session_snapshot.notebook_id:
        return ungraded("notebook_id no coincide con el scope de la sesión persistida.")
    effective_notebook_id = session_snapshot.notebook_id

    bound_episode = None
    if req.episode_id is not None:
        if session_snapshot.episode_id != req.episode_id:
            return ungraded("episode_id no coincide con el episodio activo de la sesión.")
        pedagogical_orchestrator = getattr(container, "pedagogical_orchestrator", None)
        bound_episode = (
            pedagogical_orchestrator.get_episode(req.episode_id)
            if pedagogical_orchestrator is not None
            else None
        )
        if (
            bound_episode is None
            or bound_episode.episode_id != req.episode_id
            or bound_episode.session_id != req.session_id
            or bound_episode.notebook_id != effective_notebook_id
        ):
            return ungraded("El episodio no pertenece a la sesión y al cuaderno persistidos.")

    def episode_allows(exercise_id: str, kc_id: str) -> bool:
        if bound_episode is None:
            return True
        current_step = getattr(bound_episode, "current_step_id", None)
        episode_phase = getattr(bound_episode, "phase", None)
        episode_phase = getattr(episode_phase, "value", episode_phase)
        return (
            episode_phase == "EVALUATING"
            and bound_episode.kc_id == kc_id
            and (not current_step or current_step == f"step_eval_{exercise_id}")
        )

    def scope_contains(kc_ids: Sequence[str]) -> bool:
        catalog = getattr(getattr(container, "pedagogical_orchestrator", None), "_kc_catalog", None)
        if not isinstance(catalog, dict):
            return False
        notebook = catalog.get(effective_notebook_id)
        if not isinstance(notebook, dict):
            return False
        allowed = {
            item.get("kc_id") for item in notebook.get("kcs", [])
            if isinstance(item, dict) and isinstance(item.get("kc_id"), str)
        }
        return bool(allowed) and all(kc in allowed for kc in kc_ids)

    # Fase 6: ejercicios generados (oráculo propio) — path separado y explícito
    generated = None
    registry = getattr(container, "generated_registry", None)
    if stored_exercise is None and registry is not None:
        generated = registry.get(req.exercise_id)

    if generated is not None:
        from study_engine.pedagogy.generated_registry import GeneratedOracleGrader
        from study_engine.pedagogy.observation_admissibility import (
            admit_generated_observation,
        )
        from study_engine.student.contracts import ExerciseFormat as _Fmt

        kc_ids = generated.get("kc_ids")
        oracle = generated.get("oracle")
        oracle_types = {"multi_kc": "keyword_coverage", "debugging": "bug_class", "trace": "state_match"}
        oracle_shape_valid = isinstance(oracle, dict) and (
            (
                oracle.get("type") == "keyword_coverage"
                and isinstance(oracle.get("required"), list)
                and bool(oracle["required"])
                and all(
                    isinstance(item, dict)
                    and isinstance(item.get("name"), str)
                    and isinstance(item.get("accept"), list)
                    and bool(item["accept"])
                    and all(isinstance(alias, str) and alias.strip() for alias in item["accept"])
                    for item in oracle["required"]
                )
            )
            or (
                oracle.get("type") == "bug_class"
                and isinstance(oracle.get("accept"), list)
                and bool(oracle["accept"])
                and all(isinstance(alias, str) and alias.strip() for alias in oracle["accept"])
            )
            or (
                oracle.get("type") == "state_match"
                and isinstance(oracle.get("final_state"), dict)
                and bool(oracle["final_state"])
            )
        )
        if (
            generated.get("exercise_id") != req.exercise_id
            or generated.get("source") != "generated"
            or not isinstance(generated.get("prompt"), str)
            or not generated["prompt"].strip()
            or not isinstance(kc_ids, list)
            or not kc_ids
            or any(not isinstance(k, str) or not k.strip() for k in kc_ids)
            or len(set(kc_ids)) != len(kc_ids)
            or not isinstance(oracle, dict)
            or oracle_types.get(generated.get("kind")) != oracle.get("type")
            or not oracle_shape_valid
            or not scope_contains(kc_ids)
            or not episode_allows(req.exercise_id, kc_ids[0] if kc_ids else "")
        ):
            return ungraded("Identidad, tipo, KC o scope del ejercicio generado no verificable.")

        grade = GeneratedOracleGrader().grade(req.user_answer, oracle)
        is_correct = bool(grade["is_correct"])
        primary_kc = kc_ids[0]

        # H2-A (autorización propietaria 2026-10-21): admisibilidad de la
        # observación. El oráculo generado define el FEEDBACK del ejercicio;
        # los efectos académicos (BKT, dificultades, digest académico,
        # espiral) requieren una observación admisible — instrumento
        # autorizado que haya evaluado efectivamente el conocimiento
        # atribuido (regla H2-A). Los tres oráculos generados quedan
        # contenidos por contrato real (ver observation_admissibility.py);
        # feedback, registro forense del intento y remediación se conservan.
        admission = admit_generated_observation(
            kind=generated.get("kind"), kc_ids=kc_ids
        )

        # Registro forense de intento en student_exercise_attempts
        # (registro NEUTRO de interacción; se conserva íntegro — H2-A §7)
        if hasattr(container, "student_storage") and container.student_storage is not None:
            try:
                container.student_storage.record_exercise_attempt(
                    content_id=req.exercise_id,
                    student_id=CANONICAL_STUDENT_ID,
                    success=is_correct,
                    metadata={"source": "generated", "kc_ids": kc_ids, "kind": generated.get("kind")},
                )
            except Exception:
                raise

        # H2-A: la actualización de maestría BKT (históricamente "A5: a
        # través de TODOS los KCs") queda condicionada a la admisibilidad de
        # la observación; sin admisión no hay mutación de estado académico.
        struggle = getattr(container, "struggle_tracker", None)
        bkt_updates: Dict[str, Any] = {}
        primary_bkt_res = None
        primary_delta = 0.0

        if admission.academic_effects:
            for k in (kc_ids if kc_ids else [primary_kc]):
                s_consecutive = struggle.record(k, is_correct) if struggle else 0
                prior = container.bkt_tracker.get_state(k)
                bkt_res = container.bkt_tracker.update(
                    kc_id=k,
                    correct=is_correct,
                    source=ObservationSource.EXACT_CORRECTOR,
                    format_type=_Fmt.SYMBOLIC_OPEN,
                    n_options=None,
                )
                d = round(bkt_res.p_L - prior.p_L, 4)
                bkt_updates[k] = {
                    "p_L": round(bkt_res.p_L, 4),
                    "delta_p_L": d,
                    "attempts": bkt_res.attempts,
                    "struggle_consecutive_failures": s_consecutive,
                }
                if k == primary_kc or primary_bkt_res is None:
                    primary_bkt_res = bkt_res
                    primary_delta = d

                if prior.attempts == 0:
                    logger.info(
                        "[COLD_START_FIRST_ATTEMPT] Primer intento graded sobre KC cold-start: kc_id=%s is_correct=%s prior_p_L=%.4f new_p_L=%.4f delta_p_L=%.4f exercise_id=%s source=generated",
                        k, is_correct, prior.p_L, bkt_res.p_L, d, req.exercise_id,
                    )

                try:
                    from study_engine.pedagogy.session_digest import record_kc_attempt
                    record_kc_attempt(
                        storage=container.student_storage,
                        student_id=CANONICAL_STUDENT_ID,
                        session_id=req.session_id or "sess_default",
                        kc_id=k,
                        correct=is_correct,
                        struggled=bool(struggle and struggle.is_struggling(k)),
                    )
                except Exception:
                    raise

        if primary_bkt_res is None:
            primary_bkt_res = container.bkt_tracker.get_state(primary_kc)

        remediation = None
        if not is_correct or primary_bkt_res.p_L < 0.5:
            remediation = _remediation_message(primary_kc, SimpleNamespace(prompt=generated["prompt"]), primary_bkt_res.p_L)

        # H2-A: las recomendaciones de avance (espiral) también son efectos
        # derivados de la observación; quedan condicionadas a la admisibilidad.
        spiral_opps = []
        if (
            admission.academic_effects
            and is_correct
            and primary_bkt_res.p_L >= 0.6
            and getattr(container, "bkt_tracker", None)
        ):
            try:
                from study_engine.pedagogy.spiral_curriculum import SpiralCurriculumEngine
                spiral_engine = SpiralCurriculumEngine(container.bkt_tracker)
                spiral_opps = spiral_engine.detect_spiral_opportunities(
                    current_kc=primary_kc,
                    student_id=CANONICAL_STUDENT_ID,
                )
            except Exception as s_err:
                logger.debug("Chat route: error detectando oportunidades en espiral: %s", s_err)

        return {
            "status": "GRADED",
            "exercise_id": generated["exercise_id"],
            "kc_id": primary_kc,
            "kc_ids": kc_ids,
            "bkt_updates": bkt_updates,
            "is_correct": is_correct,
            "p_L": round(primary_bkt_res.p_L, 4),
            "delta_p_L": primary_delta,
            "attempts": primary_bkt_res.attempts,
            "remediation": remediation,
            "grader_detail": grade,
            "source": "generated",
            "struggle_mode": bool(struggle and struggle.is_struggling(primary_kc)),
            "struggle_consecutive_failures": bkt_updates.get(primary_kc, {}).get("struggle_consecutive_failures", 0),
            "spiral_opportunities": spiral_opps,
            # H2-A: estado de admisibilidad de la observación (sin texto de
            # política; sólo el hecho y su motivo para trazabilidad honesta).
            "academic_admission": {
                "admissible": admission.academic_effects,
                "reason": admission.reason,
            },
        }

    if exercise is None:
        # Misión Fail-closed: sin clave certificada no hay evaluación
        return ungraded("Ejercicio inexistente o sin clave certificada: evaluación omitida (fail-closed).")

    if getattr(session_snapshot, "student_id", CANONICAL_STUDENT_ID) != CANONICAL_STUDENT_ID:
        return ungraded("La sesión no pertenece al estudiante actual; evaluación omitida.")

    kc_id = exercise.kc_id
    if not episode_allows(exercise.exercise_id, kc_id):
        return ungraded("El ejercicio no corresponde al KC o paso activo del episodio.")
    if not scope_contains([kc_id]):
        return ungraded("KC ajeno al scope del cuaderno indicado; evaluación omitida.")
    is_mc = getattr(exercise.exercise_type, "value", str(exercise.exercise_type)) == "MC"
    if is_mc:
        grade_res = container.mc_grader.grade(req.user_answer, exercise.expected_answer)
    else:
        grade_res = container.exact_grader.grade(req.user_answer, exercise.expected_answer, exercise.exercise_type)
    is_correct = bool(getattr(grade_res, "is_correct", False))

    # EP-04A: persist difficulty with the receipt, never in mutable process memory.
    struggle = getattr(container, "struggle_tracker", None)
    struggle_state = (
        struggle.preview_certified(
            container.student_storage, kc_id=kc_id, correct=is_correct,
            student_id=CANONICAL_STUDENT_ID, session_id=req.session_id,
            notebook_id=effective_notebook_id,
        )
        if struggle else None
    )
    struggle_consecutive = struggle_state["consecutive_failures"] if struggle_state else 0
    struggle_active = bool(struggle and struggle.is_struggling(kc_id, state=struggle_state))

    prior = container.bkt_tracker.get_state(kc_id)
    fmt = ExerciseFormat.CLOSED_CHOICE if is_mc else ExerciseFormat.SYMBOLIC_OPEN
    bkt_res = container.bkt_tracker.update(
        kc_id=kc_id,
        correct=is_correct,
        source=ObservationSource.EXACT_CORRECTOR,
        format_type=fmt,
        n_options=len(exercise.options) if exercise.options else None,
    )
    delta = round(bkt_res.p_L - prior.p_L, 4)

    if prior.attempts == 0:
        logger.info(
            "[COLD_START_FIRST_ATTEMPT] Primer intento graded sobre KC cold-start: kc_id=%s is_correct=%s prior_p_L=%.4f new_p_L=%.4f delta_p_L=%.4f exercise_id=%s source=certified",
            kc_id, is_correct, prior.p_L, bkt_res.p_L, delta, req.exercise_id,
        )

    # Session Digest: acumular el intento en la actividad de sesión del KC
    # (la fuente del perfil cognitivo entre sesiones).
    try:
        from study_engine.pedagogy.session_digest import record_kc_attempt
        record_kc_attempt(
            storage=container.student_storage,
            student_id=CANONICAL_STUDENT_ID,
            session_id=req.session_id or "sess_default",
            kc_id=kc_id,
            correct=is_correct,
            struggled=struggle_active,
        )
    except Exception:
        raise

    remediation = None
    if not is_correct or bkt_res.p_L < 0.5:
        remediation = _remediation_message(kc_id, exercise, bkt_res.p_L)

    spiral_opps = []
    if is_correct and bkt_res.p_L >= 0.6 and getattr(container, "bkt_tracker", None):
        try:
            from study_engine.pedagogy.spiral_curriculum import SpiralCurriculumEngine
            spiral_engine = SpiralCurriculumEngine(container.bkt_tracker)
            spiral_opps = spiral_engine.detect_spiral_opportunities(
                current_kc=kc_id,
                student_id=CANONICAL_STUDENT_ID,
            )
        except Exception as s_err:
            logger.debug("Chat route: error detectando oportunidades en espiral: %s", s_err)

    return {
        "status": "GRADED",
        "exercise_id": exercise.exercise_id,
        "kc_id": kc_id,
        "is_correct": is_correct,
        "p_L": round(bkt_res.p_L, 4),
        "delta_p_L": delta,
        "attempts": bkt_res.attempts,
        "remediation": remediation,
        "struggle_mode": struggle_active,
        "struggle_consecutive_failures": struggle_consecutive,
        "spiral_opportunities": spiral_opps,
        **({"_struggle_state": struggle_state} if struggle_state else {}),
    }
