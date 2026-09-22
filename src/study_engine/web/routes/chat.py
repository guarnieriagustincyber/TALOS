"""Interactive Chat & Streaming Phased Pedagogical Endpoints (Fase 5.8)."""

import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.hierarchy.scope_resolver import ScopeNotFoundError, ScopeResolver, ScopeType
from study_engine.pedagogy.structured_pipeline import (
    PhaseHistory,
    StructuredResponsePipeline,
    resolve_epistemic_role,
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

# Buffer de turnos conversacionales de corto plazo (Fase 2):
# Almacena los últimos 4 turnos {role, content} por history_key para inyectar
# continuidad conversacional real en el prompt sin inflar el contexto global.
_CONV_TURN_BUFFER: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)


class EpistemicContextPack:
    """Pack of epistemic context, citations and chunks for prompt augmentation."""

    def __init__(
        self,
        formatted_context: str,
        citations: list,
        chunks: list,
        abstained: bool = False,
        abstention_reason: Optional[str] = None,
    ):
        self.formatted_context = formatted_context
        self.citations = citations
        self.chunks = chunks
        self.abstained = abstained
        self.abstention_reason = abstention_reason


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
                if hasattr(self.store, "search_hybrid"):
                    results = self.store.search_hybrid(query, notebook_id=notebook_id, limit=5)
                elif hasattr(self.store, "search"):
                    results = self.store.search(query, notebook_id=notebook_id, limit=5)
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
                        # Buscar por coincidencia con kc_id o prompt
                        matches = [
                            ex for ex in all_qual
                            if norm_t in ex.kc_id.lower() or norm_t in ex.prompt.lower()
                        ]
                        if matches:
                            exercise = matches[0]
                    if not exercise and all_qual:
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


def _resolve_chat_backend(container: AppContainer) -> Any:
    """Determine active LLM backend from container or fall back to offline oracle."""
    llm_backend = getattr(container, "llm_backend", None)
    if llm_backend is not None:
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

    - Consulta amplia (resumen, repaso de unidad, panorama): 14 chunks, >=4 fuentes.
    - Consulta específica (déficit de un concepto, cómo se hace X): 6 chunks, >=3 fuentes.
    """
    q = (prompt_text or "").strip()
    if len(q) >= 220 or _BROAD_QUERY_PATTERN.search(q):
        return 14, 4
    return 6, 3


def _assemble_epistemic_context(
    store: Any,
    container: AppContainer,
    prompt_text: str,
    target_notebook_id: str,
    active_sources: Optional[List[str]] = None,
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

        src_meta_cache: Dict[str, Dict[str, str]] = {}
        try:
            with store.engine.transaction() as conn:
                cur = conn.cursor()
                cur.execute("SELECT source_id, title, sha256, author FROM sources;")
                for row in cur.fetchall():
                    src_meta_cache[row[0]] = {
                        "title": row[1] or row[0],
                        "sha256": row[2] or "",
                        "author": row[3] or "",
                    }
        except Exception as meta_err:
            logger.warning("Fallo al consultar metadatos de fuentes: %s", meta_err)

        retrieval_limit, min_sources = _resolve_retrieval_depth(search_query)
        search_results = []
        if target_notebook_id == GLOBAL_SCOPE_ID:
            # Scope global (COMMIT 2): correr retrieval híbrido por cuaderno y
            # fundir por chunk_id preservando el mejor rank de cada uno. La
            # caché de matrices por cuaderno hace esto viable en CPU.
            try:
                with store.engine.transaction() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT DISTINCT notebook_id FROM notebook_sources ORDER BY notebook_id;"
                    )
                    all_notebooks = [r[0] for r in cur.fetchall()]
            except Exception as nb_err:
                logger.warning("No se pudo listar cuadernos para scope global: %s", nb_err)
                all_notebooks = []

            merged: Dict[str, Tuple[int, Any]] = {}
            for nb_id in all_notebooks:
                try:
                    nb_results = store.search_hybrid(
                        query=search_query,
                        notebook_id=nb_id,
                        limit=retrieval_limit,
                        min_sources=min_sources,
                    ) if hasattr(store, "search_hybrid") else store.search(
                        query=search_query, notebook_id=nb_id, limit=retrieval_limit
                    )
                except Exception as nb_search_err:
                    logger.debug("Scope global: fallo retrieval en %s: %s", nb_id, nb_search_err)
                    continue
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

        # Filtrar por active_sources si fue especificado (E25 / INV-W5-4)
        if active_sources:
            active_set = set(active_sources)
            search_results = [
                res for res in search_results
                if (
                    res.source_id in active_set
                    or (src_meta_cache.get(res.source_id, {}).get("sha256") in active_set)
                )
            ]

        # Enmienda E23 & E26: Expansión de sección mediante SectionExpander
        expanded_chunks = []
        expanded_context_text = ""
        if search_results and hasattr(store, "engine"):
            try:
                from study_engine.retrieval.expansion import SectionExpander
                expander = SectionExpander(engine=store.engine)
                expanded_chunks, expanded_context_text = expander.expand_results(
                    seed_results=search_results,
                    source_meta_cache=src_meta_cache,
                )
            except Exception as exp_err:
                logger.warning("Error durante SectionExpander: %s", exp_err)
                expanded_chunks = []
                expanded_context_text = ""

        citation_idx = 1
        for res in search_results:
            content_clean = getattr(res, "content", "").strip()
            if not content_clean:
                continue
            src_id = getattr(res, "source_id", "fuente")
            meta = src_meta_cache.get(src_id, {"title": src_id, "sha256": "", "author": ""})
            src_title = f"{meta['author']} - {meta['title']}" if meta.get("author") else meta.get("title", src_id)
            p_start = getattr(res, "page_start", 1) or 1
            doc_hash = meta.get("sha256") or ""
            chunk_id = getattr(res, "chunk_id", f"c_{citation_idx}")
            score_val = getattr(res, "score", 0.85)
            norm_score = round(min(1.0, max(0.1, abs(float(score_val)))), 2) if score_val else 0.85

            citations_formatted.append(
                f"[{citation_idx}] [E{citation_idx}] Fuente: {src_title} (Pág: {p_start}):\n\"{content_clean}\""
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
            ), []

        if citations_formatted:
            final_formatted = expanded_context_text if expanded_context_text else "\n\n".join(citations_formatted)
            pack = EpistemicContextPack(
                formatted_context=final_formatted,
                citations=search_results,
                chunks=raw_chunks,
                abstained=False,
            )
            setattr(pack, "expanded_chunks", expanded_chunks)
            setattr(pack, "expanded_context_text", expanded_context_text)
            return pack, raw_chunks
    except Exception as ctx_err:
        logger.warning("Advertencia al ensamblar evidencias epistémicas: %s", ctx_err, exc_info=True)

    return None, []


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
    if not extractor and not mem0:
        return

    async def _run_bg() -> None:
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
        if mem0:
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

    briefing_text = gen.generate_briefing(
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
        hit_terms = [t for t in _kc_search_terms(kc) if re.search(rf"\b{re.escape(t)}\b", q)]
        hits = len(hit_terms)
        if hits >= 2 and hits > best_hits:
            best_kc, best_hits = kid, hits
    return best_kc


# Marcador de scope global (COMMIT 2 fix/scope): una query técnica emitida con
# scope de carpeta (roadmap, Programación) no se desvía al usuario al cuaderno
# "correcto"; el roadmap es acceso global por defecto y el retrieval corre
# contra TODOS los cuadernos, fundiendo resultados por chunk_id.
GLOBAL_SCOPE_ID = "__global__"

# COMMIT 3 (fix/scope): intención no curricular — opinión personal, ficción,
# cotidiano, actualidad. Es INDEPENDIENTE del match léxico de contenido: el
# corpus menciona Star Wars (ejemplo didáctico) pero "¿Qué opinás de Star Wars?"
# no es consulta curricular. El umbral vectorial 0.87 no se toca.
_NON_CURRICULAR_INTENT_RE = re.compile(
    r"(qu[ée]\s+opin[áa]s|qu[ée]\s+pens[áa]s|te\s+gusta|te\s+copa|"
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
        from datetime import datetime, timezone
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
        context = fastpath.extract_student_context(container, target_notebook_id)
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
    if _is_non_curricular_intent(prompt_text, kcs_list):
        context_pack = EpistemicContextPack(
            formatted_context="",
            citations=[],
            chunks=[],
            abstained=True,
            abstention_reason=(
                "Consulta fuera del ámbito curricular (opinión, ficción, actualidad o vida cotidiana). "
                "TALOS está acotado a la bibliografía del roadmap; planteá la pregunta en términos del programa."
            ),
        )
        raw_chunks: List[Any] = []
        contract = None if target_notebook_id == GLOBAL_SCOPE_ID else store.get_pedagogical_contract(target_notebook_id)
    else:
        contract = None if target_notebook_id == GLOBAL_SCOPE_ID else store.get_pedagogical_contract(target_notebook_id)
        context_pack, raw_chunks = _assemble_epistemic_context(
            store=store,
            container=container,
            prompt_text=prompt_text,
            target_notebook_id=target_notebook_id,
            active_sources=request.active_sources,
        )

    # ConversationStyleRouter (Ola 5, E24)
    from study_engine.pedagogy.style_router import ConversationStyleRouter
    style_result = ConversationStyleRouter.detect_style(prompt_text)

    matched_kc_id = _match_kc_id(kcs_list, prompt_text) if kcs_list else None

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
    bkt_directive = build_bkt_adaptation_directive(context_mode, bkt_meta)

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

    target_notebook_id = resolved_scope.notebook_id or target_scope_id
    history_key = f"{request.session_id or 'anon'}:{target_notebook_id}"
    if request.requested_phase == "conceptual" and history_key in _ACTIVE_TURN_HISTORIES:
        _ACTIVE_TURN_HISTORIES[history_key].clear()

    phase_history = _ACTIVE_TURN_HISTORIES.setdefault(history_key, PhaseHistory())
    llm_backend = _resolve_chat_backend(container)

    # Memoria de corto plazo (Fase 2): recuperar buffer de turnos y registrar el turno actual del usuario.
    conv_turns: list = list(_CONV_TURN_BUFFER.get(history_key) or [])
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
            # Enmienda E5: Si context_pack indica abstención por falta de fuentes canónicas,
            # emitir evidence_manifest indicando abstención y luego evento 'abstention' sin invocar al LLM.
            # Nota: Si el backend es OfflinePedagogicalBackend (típico en pruebas offline del oráculo socrático),
            # permitimos que complete para emitir sus respuestas curriculares autorizadas u honestas.
            from study_engine.llm.offline_oracle import OfflinePedagogicalBackend
            is_offline_oracle = isinstance(llm_backend, OfflinePedagogicalBackend)
            if context_pack is not None and getattr(context_pack, "abstained", False) and not is_offline_oracle:
                # COMMIT 1 (fix/memory): las declaraciones meta del estudiante
                # ("prefiero analogías de...") no pueden morir en el gate de
                # abstención: persistimos memoria aunque el contenido abstenga.
                # process_turn_memories solo lee la query del usuario para
                # preferencias/patrones; no depende de chunks recuperados.
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

                reason = getattr(context_pack, "abstention_reason", "QUERY_OUT_OF_SCOPE")
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
                    },
                }
                yield f"data: {json.dumps(manifest_payload)}\n\n"

                abstention_payload = {
                    "event_type": "abstention",
                    "payload": {
                        "phase": request.requested_phase or "conceptual",
                        "abstained": True,
                        "reason": (
                            reason if reason and reason != "QUERY_OUT_OF_SCOPE" else
                            "TALOS se abstiene de responder: No se hallaron evidencias curriculares "
                            "verificables en las fuentes canónicas del cuaderno para fundamentar esta consulta."
                        ),
                        "suggested_action": "Consultá el catálogo de fuentes del cuaderno o reformulá la pregunta con términos del programa.",
                        "abstention_code": reason,
                        "notebook_id": target_notebook_id,
                    },
                }
                yield f"data: {json.dumps(abstention_payload)}\n\n"
                return

            style_dir = style_result.instruction_directive if style_result else None
            # Permitir respuesta exhaustiva con diagramas y patrones sin racionamiento de tokens (estilo NotebookLM)
            live_max_tokens = 3500 if (not request.requested_phase or request.requested_phase == "conceptual") else None
            from study_engine.pedagogy.structured_pipeline import classify_pedagogical_intent
            conv_intent = classify_pedagogical_intent(prompt_text)
            accumulated_response_text = ""
            async for event in pipeline.generate_phased_response(
                user_query=prompt_text,
                context_pack=context_pack,
                requested_phase=request.requested_phase or "conceptual",
                pedagogical_mode=conv_intent,
                bkt_directive=bkt_directive,
                style_directive=style_dir,
                override_max_tokens=live_max_tokens,
                recent_turns=conv_turns,
            ):
                payload = {
                    "event_type": event.event_type,
                    "payload": event.payload,
                }

                if event.event_type == "phase_token":
                    accumulated_response_text += event.payload.get("token", "")

                if event.event_type == "phase_complete":
                    # Validador de citas post-generación (Fase 2)
                    from study_engine.pedagogy.citation_validator import CitationValidator
                    validator = CitationValidator()
                    valid_citations, invalid_citations = validator.audit_only(
                        text=accumulated_response_text,
                        chunks=raw_chunks,
                    )
                    if invalid_citations:
                        logger.warning(
                            "Auditoría de citas detectó referencias no verificadas: %s (válidas: %s)",
                            invalid_citations,
                            valid_citations,
                        )
                        audit_payload = {
                            "event_type": "citation_audit",
                            "payload": {
                                "valid_citations": valid_citations,
                                "invalid_citations": invalid_citations,
                                "citation_count": len(valid_citations),
                            },
                        }
                        yield f"data: {json.dumps(audit_payload)}\n\n"

                    # Guardar historial conversacional (últimos 4 turnos) en _CONV_TURN_BUFFER
                    conv_turns.append({"role": "assistant", "content": accumulated_response_text})
                    _CONV_TURN_BUFFER[history_key] = conv_turns[-4:]

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

                yield f"data: {json.dumps(payload)}\n\n"
        except asyncio.CancelledError:
            # Fix 3.3: Cliente desconectado, registrar y salir sin emitir SSE a socket cerrado
            logger.info("Cliente desconectado durante streaming SSE de chat (%s)", target_notebook_id)
            return
        except Exception as e:
            logger.warning("Fallo en generación streaming de chat: %s", e, exc_info=True)
            err_payload = {
                "event_type": "error",
                "payload": {"message": f"Error interno en respuesta pedagógica: {str(e)}"},
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
