"""Structured Response Pipeline (Fase 5.8 / Refinamientos 1 & 3).

Orchestrates multi-phase pedagogical generation with independent token budgets,
continuous PhaseHistory accumulation across phases, SocraticGuard rolling buffer,
and robust cancellation (abort) handling.
"""

import asyncio
from datetime import datetime, timezone
import logging
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Sequence
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.socratic_guard import SocraticGuard
from study_engine.pedagogy.command_parser import parse_student_command
from study_engine.pedagogy.prompts import build_pedagogical_tone_directive

logger = logging.getLogger(__name__)


class StreamEventType(str):
    PHASE_START = "phase_start"
    PHASE_TOKEN = "phase_token"
    GUARD_BLOCKED = "guard_blocked"
    AUDIT_VERDICT = "audit_verdict"
    EVIDENCE_MANIFEST = "evidence_manifest"
    PHASE_COMPLETE = "phase_complete"
    STREAM_ABORTED = "stream_aborted"
    ERROR = "error"
    ABSTENTION = "abstention"
    TRUNCATED = "truncated"


class StreamEvent(BaseModel):
    """Event emitted over Server-Sent Events (SSE) stream during phased generation."""

    model_config = ConfigDict(strict=True, frozen=True)

    event_type: Literal[
        "phase_start",
        "phase_token",
        "guard_blocked",
        "audit_verdict",
        "evidence_manifest",
        "phase_complete",
        "stream_aborted",
        "error",
        "abstention",
        "truncated",
    ]
    payload: Dict[str, Any]


class PhaseOutput(BaseModel):
    """Authoritative output of a successfully completed generation phase."""

    model_config = ConfigDict(strict=True, frozen=True)

    phase_id: StrictStr
    text: StrictStr
    tokens_produced: int = 0
    audit_verdict: Optional[StrictStr] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PhaseHistory:
    """Accumulator of all completed phases within the current turn (Refinamiento 1).
    
    Ensures that Phase 3 (code) has full visibility into Phase 1 (analogy) and Phase 2 (pseudocode)
    without re-injecting raw chat history or uncurated documents.
    """

    def __init__(self, max_context_chars: int = 8000) -> None:
        self._history: List[PhaseOutput] = []
        self.max_context_chars = max_context_chars

    def append(self, output: PhaseOutput) -> None:
        self._history.append(output)

    def get_all(self) -> Sequence[PhaseOutput]:
        return tuple(self._history)

    def format_predecessors_context(self) -> str:
        """Format all completed predecessor phases into a compact context block."""
        if not self._history:
            return ""

        blocks: List[str] = []
        for item in self._history:
            blocks.append(
                f"=== FASE PREVIA COMPLETADA: [{item.phase_id.upper()}] ===\n{item.text.strip()}"
            )
        combined = "\n\n".join(blocks)
        if len(combined) > self.max_context_chars:
            # Keep most recent content up to limit
            combined = combined[-self.max_context_chars :]
        return combined

    def clear(self) -> None:
        self._history.clear()


# ==============================================================================
# FASE 7.4: CALIBRACIÓN POST-AUDITORÍA (ENTIDADES, THREAT INTEL, ARQUITECTURA)
# ==============================================================================

def extract_technical_checklist(user_query: str) -> List[str]:
    """Extrae entidades técnicas explícitas solicitadas en el query del estudiante.
    
    Ejemplo: 'FLAGS: Zero Flag, Carry Flag' -> ['Zero Flag', 'Carry Flag']
    """
    patterns = [
        r"(?:flags?|banderas?)\s*[:=]\s*([A-Za-z0-9_\s,\-]+?)(?:\.|\?|\)|$)",
        r"(?:flags?|banderas?)\s*\(([^)]+)\)",
        r"(?:registros?|registers?)\s*[:=]\s*([A-Za-z0-9_\s,\-]+?)(?:\.|\?|\)|$)",
        r"(?:registros?|registers?)\s*\(([^)]+)\)",
    ]
    entities: List[str] = []
    for pat in patterns:
        matches = re.findall(pat, user_query, re.IGNORECASE)
        for match in matches:
            parts = [p.strip() for p in re.split(r"[,;/]|\by\b|\band\b", match) if p.strip()]
            for p in parts:
                if len(p) > 1 and p not in entities:
                    entities.append(p)
    return entities


_CONTINUATION_PATTERNS = [
    re.compile(r"\b(?:se\s+cort[oó]|continu[aá]|segu[ií]|termin[aá])\b", re.IGNORECASE),
    re.compile(r"\bestabas\s+diciendo\b", re.IGNORECASE),
    re.compile(r"\bfalt[óo]\s+(?:el\s+final|la\s+[úu]ltima\s+parte)\b", re.IGNORECASE),
    re.compile(r"\bqued[oó]\s+(?:a\s+medias|incomplet[ao]|cortad[ao])\b", re.IGNORECASE),
]


def is_continuation_query(query: str) -> bool:
    """Return True if query is requesting to continue an interrupted or truncated prior response."""
    q = (query or "").strip()
    return any(p.search(q) for p in _CONTINUATION_PATTERNS)


def extract_requested_structural_components(user_query: str, notebook_id: Optional[str] = None) -> Dict[str, str]:
    """Detecta entregables y componentes estructurales explícitos solicitados por el estudiante.
    
    Identifica transversalmente para cualquier materia o cuaderno:
    - Diagramas Mermaid ('diagrama en mermaid', 'mermaid', 'diagrama de flujo')
    - Pytest / Tests automatizados ('tests', 'pytest', 'pruebas unitarias', 'suite de pruebas')
    - Código ejecutable en Python, C, SQL o el lenguaje canónico del cuaderno
    - Contratos formales ('contrato PRE/POST', 'pre/post', 'precondición', 'poscondición')
    - Pseudocódigo estructurado ('pseudocódigo', 'pseudocode')
    """
    directives: Dict[str, str] = {}
    q = user_query.lower()
    response_intent = resolve_response_intent(user_query)

    shortcut_match = bool(re.search(
        r"\b(?:(?:pasame|haceme|dame|escribime|generame)\s+(?:el\s+)?c[oó]digo|haceme\s+la\s+funci[oó]n|haceme\s+el\s+tp|para\s+que\s+lo\s+copie|para\s+copiar\s+y\s+pegar|para\s+copiarlo|c[oó]digo\s+completo\s+terminado|(?:pasame|dame)\s+la\s+soluci[oó]n)\b",
        q,
    )) and (
        response_intent.task != "entregar solución completa solicitada"
        and not response_intent.exclude_code
    )

    # 1. Mermaid / Diagramas de flujo: only inject a deliverable when requested.
    if re.search(
        r"\b(?:diagrama(?:s)?\s+(?:de\s+flujo\s+)?en\s+mermaid|gr[aá]fico\s+en\s+mermaid)\b|"
        r"\b(?:dame|pasame|haceme|hac[eé]|mostrame|mostr[aá]|inclu[ií]|agreg[aá]|gener[aá]|dibuj[aá]|"
        r"quiero|con)\b.{0,60}\b(?:diagrama|mermaid)\b",
        q,
    ):
        directives["mermaid"] = (
            "- DIAGRAMA DE FLUJO EN MERMAID (OBLIGATORIO):\n"
            "  Generá un bloque de código ```mermaid con sintaxis válida (`graph TD` o `flowchart TD`).\n"
            "  El diagrama debe modelar claramente los nodos de entrada, decisiones lógicas/bifurcaciones (Fail-Fast), "
            "bucles de validación y estados finales de aceptación o rechazo."
        )

    # 2. Pytest / Pruebas Automatizadas
    if not response_intent.exclude_code and re.search(
        r"\b(?:pytest|tests?|pruebas?(?:\s+unitarias|\s+automatizadas)?|suite\s+de\s+pruebas|bater[ií]a\s+de\s+pruebas)\b",
        q,
    ):
        directives["pytest"] = (
            "- BATERÍA DE PRUEBAS AUTOMATIZADAS CON PYTEST (OBLIGATORIA):\n"
            "  Generá un bloque completo de pruebas ejecutables en ```python usando `import pytest` (o casos de prueba asertivos en el lenguaje destino).\n"
            "  La suite debe estructurarse con funciones de test claras y descriptivas:\n"
            "    * `test_happy_path_*`: Entradas válidas estándar y casos canónicos.\n"
            "    * `test_edge_cases_*`: Valores límite y casos extremos (ej. valores mínimos, máximos, delimitadores).\n"
            "    * `test_invalid_inputs_*`: Entradas malformadas, fuera de rango, tipos incorrectos o vectores de ataque."
        )

    # Si hay solicitud de atajo para copiar, suprimir solo suites de prueba pesadas, preservando diagramas
    if shortcut_match:
        directives.pop("pytest", None)

    # 3. Código C (Para cuadernos de Lenguajes C o SO2)
    if response_intent.code_language == "c":
        if shortcut_match:
            directives["c_code"] = (
                "- ESQUELETO DEFENSIVO SOCRÁTICO EN C (ANTI-ATAJO Y FADING):\n"
                "  Dado que el estudiante solicitó el código terminado para copiarlo, NUNCA entregues la implementación completa resuelta.\n"
                "  Generá la firma de función, contratos PRE/POST y un esqueleto con comentarios `/* TODO: COMPLETAR LÓGICA DE INTERCAMBIO */`.\n"
                "  PROHIBIDO entregar la función resuelta, main() o suites Pytest. Cerrá con una pregunta de prueba de escritorio para que el estudiante dé el paso final."
            )
        else:
            directives["c_code"] = (
                "- CÓDIGO C ESTÁNDAR Y DEFENSIVO (OBLIGATORIO):\n"
                "  Generá la implementación completa en un bloque ```c con:\n"
                "    * Headers canónicos (`#include <stdio.h>`, `#include <stdlib.h>`, etc.) y prototipos de función.\n"
                "    * Validación estricta de punteros nulos (`NULL`) y límites de buffer en memoria.\n"
                "    * Manejo defensivo de valores de retorno y liberación de memoria dinámica sin fugas."
            )
    # 4. Código SQL (Para cuadernos de Bases de Datos / STD)
    elif response_intent.code_language == "sql":
        directives["sql_code"] = (
            "- CONSULTA O ESQUEMA SQL (OBLIGATORIO):\n"
            "  Generá las sentencias en un bloque ```sql estructurado con:\n"
            "    * Sintaxis SQL estándar, cláusulas declarativas limpias e integridad referencial.\n"
            "    * Parametrización defensiva (Prepared Statements) contra vectores de SQL Injection."
        )
    # 5. Código Python / Implementación general
    elif response_intent.code_language == "python":
        if shortcut_match:
            directives["python_code"] = (
                "- ESQUELETO DEFENSIVO SOCRÁTICO EN PYTHON (ANTI-ATAJO Y FADING):\n"
                "  Dado que el estudiante solicitó el código terminado para copiarlo, NUNCA entregues la implementación completa resuelta.\n"
                "  Generá la firma de función con Type Hints y un esqueleto con `# TODO: COMPLETAR LÓGICA`.\n"
                "  PROHIBIDO entregar la función resuelta o suites de test. Cerrá con una pregunta de prueba de escritorio para que el estudiante complete la lógica."
            )
        else:
            directives["python_code"] = (
                "- CÓDIGO PYTHON EJECUTABLE Y TIPADO (OBLIGATORIO):\n"
                "  Generá la implementación en un bloque ```python con:\n"
                "    * Type hints rigurosos (ej. `str`, `bool`, `int`, `List[str]`).\n"
                "    * Docstring técnico explicando contratos, complejidad temporal/espacial y excepciones.\n"
                "    * Cláusulas de guarda tempranas (Fail-Fast) para rebotar casos inválidos antes del cómputo principal.\n"
                "    * Algoritmo limpio y pedagógico (evitar librerías mágicas de alto nivel que oculten la lógica pedida)."
            )

    # 6. Contratos Formales PRE / POST
    if re.search(r"\b(?:contrato(?:s)?(?:\s+formal(?:es)?)?|pre\s*/\s*post|precondici[oó]n|poscondici[oó]n|precondiciones|postcondiciones)\b", q):
        directives["contracts"] = (
            "- CONTRATOS FORMALES PRE / POST (OBLIGATORIO):\n"
            "  Especificá una subsección explícita de contratos formales:\n"
            "    * **Precondición (Requires):** Tipo, formato, encoding, límites de memoria y estado esperado de las entradas.\n"
            "    * **Postcondición (Ensures):** Tipo de valor de retorno, invariantes de estado del sistema y garantías ante fallos."
        )

    # 7. Pseudocódigo Estructurado
    if re.search(
        r"\b(?:en\s+(?:pseudoc[oó]digo|pseudocode)|como\s+(?:pseudoc[oó]digo|pseudocode)|"
        r"(?:dame|mostrame|mostr[aá]|escribime|inclu[ií])\b.{0,40}"
        r"(?:pseudoc[oó]digo|pseudocode)|requisitos?\b.{0,160}"
        r"(?:pseudoc[oó]digo|pseudocode))\b",
        q,
    ):
        directives["pseudocode"] = (
            "- PSEUDOCÓDIGO ESTRUCTURADO (OBLIGATORIO):\n"
            "  Diseñá el algoritmo en pseudocódigo claro (estilo Joyanes Aguilar / Spraul) en un bloque ```text.\n"
            "  Usá nombres declarativos en español, control de flujo estructurado (SI/SINO/MIENTRAS/PARA) y comentarios sobre invariantes."
        )

    return directives


def build_security_evidence_instruction(user_query: str) -> str:
    """Add evidence constraints for security topics without asserting an incident."""
    q_lower = user_query.lower()
    if re.search(
        r"\b(?:cve[-\s]?\d{4}[-\s]?\d+|vulnerabil\w*|exploit|"
        r"ataque|inyecci[oó]n|inyeccion|desbordamiento|condici[oó]n de carrera|"
        r"race condition|ipv4|direcci[oó]n ip|dirección ip|heartbleed|dirty cow)\b",
        q_lower,
    ):
        return (
            "=== CRITERIOS DE EVIDENCIA PARA AFIRMACIONES DE SEGURIDAD ===\n"
            "- No agregues ni infieras un CVE o incidente histórico solo por palabras clave. Mencionalo únicamente si "
            "la evidencia autorizada disponible respalda la relación específica; si no, indicá que no fue verificada.\n"
            "- Al analizar un riesgo pertinente, separá precondiciones, mecanismo causal, impacto plausible y límites, "
            "y mitigación con sus trade-offs. No afirmes explotabilidad sin evidencia suficiente.\n"
        )
    return ""


ARCHITECTURAL_QUESTION_TEMPLATES: Dict[str, List[str]] = {
    "security_vs_performance": [
        "Como Arquitecto de Software: si tuvieras que diseñar el motor de validación para un pipeline que procesa 100.000 transacciones/segundo, ¿preferís forzar una validación profunda con desreferenciación defensiva previa en cada capa (segura pero con costo de ciclos de CPU) o confiar en el cortocircuito del compilador asumiendo que los invariantes del llamador nunca se romperán? ¿Cómo mitigarías el riesgo de DoS?",
        "Si una comprobación en un bucle crítico involucra una variable en memoria RAM vs. una consulta remota (I/O de red o Base de Datos), ¿en qué orden estricto colocarías los operandos en la condición compuesta y qué pasaría con la disponibilidad de tu servidor si un atacante satura la primera condición?",
    ],
    "memory_vs_cpu": [
        "En un sistema de alta concurrencia: ¿preferís pasar estructuras grandes por referencia garantizando cero copia pero requiriendo bloqueos/read-only primitives para evitar condiciones de carrera, o pasar por valor duplicando en el Stack a costa de saturar el ancho de banda del bus de memoria?",
    ],
}


AUTHOR_ROLES_BY_NOTEBOOK: Dict[str, Dict[str, List[str]]] = {
    "fadena-so2": {
        "pedagogical": ["tanenbaum", "tanenbaum_os_modernos"],
        "formal": ["silberschatz", "silberschatz_so"],
        "technical": ["stallings", "stallings_os_internals"],
    },
    "fadena-lenguajes": {
        "pedagogical": ["joyanes", "joyanes_fundamentos"],
        "formal": ["urrutia_landa", "urrutia_landa_c"],
        "technical": ["stallman", "stallman_gnu_c"],
    },
    "fadena-std": {
        "pedagogical": ["coronel_morris", "coronel_database_systems"],
        "formal": ["date", "date_intro_sistemas_bd"],
        "technical": ["elmasri_navathe", "elmasri_fundamentos_bd"],
    },
    "fadena-teleco": {
        "pedagogical": ["kurose", "kurose_top_down"],
        "formal": ["comer", "comer_tcp_ip"],
        "technical": ["stallings", "stallings_comunicaciones_redes"],
    },
    "fase0-soc": {
        "pedagogical": ["joyanes", "spraul"],
        "formal": ["rosen", "hammack"],
        "technical": ["sweigart", "goodrich"],
    },
}


def _find_notebook_roles(notebook_id: str) -> Dict[str, List[str]]:
    """Encuentra los roles de autor según el notebook sin falsos positivos en prefijos comunes."""
    nb_key = (notebook_id or "").lower().strip()
    # 1. Coincidencia exacta o contención directa (e.g. "fadena-std" == "fadena-std" o "std" in "fadena-std")
    for key, role_dict in AUTHOR_ROLES_BY_NOTEBOOK.items():
        if key == nb_key or (nb_key and (key in nb_key or nb_key in key)):
            return role_dict
    # 2. Coincidencia por palabras clave distintivas (excluyendo tokens comunes como 'fadena')
    generic = {"fadena", "nb", "curso", "materia", "fase0"}
    for key, role_dict in AUTHOR_ROLES_BY_NOTEBOOK.items():
        distinctive = [p for p in key.split("-") if p not in generic]
        if distinctive and any(p in nb_key for p in distinctive):
            return role_dict
    return AUTHOR_ROLES_BY_NOTEBOOK.get("fase0-soc", {})


def resolve_epistemic_role(
    source_id: str = "",
    source_title: str = "",
    author: str = "",
    notebook_id: str = "",
) -> str:
    """Resuelve el rol epistémico ('pedagogical', 'formal', 'technical') de una fuente."""
    matched_roles = _find_notebook_roles(notebook_id)
    target = f"{source_id} {source_title} {author}".lower()
    for role_name in ("pedagogical", "formal", "technical"):
        authors = matched_roles.get(role_name, [])
        if any(auth in target for auth in authors):
            return role_name
    return "pedagogical"


def classify_sources_by_role(context_pack: Optional[Any], notebook_id: str) -> Dict[str, List[str]]:
    """Clasifica las fuentes del context_pack en pedagógico / formal / técnico según el notebook."""
    classified: Dict[str, List[str]] = {
        "pedagogical": [],
        "formal": [],
        "technical": [],
        "other": [],
    }
    if context_pack is None:
        return classified

    chunks = getattr(context_pack, "chunks", None) or []
    matched_roles = _find_notebook_roles(notebook_id)

    seen_sources = set()
    for chk in chunks:
        s_id = str(chk.get("source_id", "")).lower()
        s_title = str(chk.get("source_title", "")).lower()
        if not s_id or s_id in seen_sources:
            continue
        seen_sources.add(s_id)

        target_cat = "other"
        for role_name in ("pedagogical", "formal", "technical"):
            authors = matched_roles.get(role_name, [])
            if any(auth in s_id or auth in s_title for auth in authors):
                target_cat = role_name
                break
        classified[target_cat].append(chk.get("source_title", s_id))

    return classified


def build_tri_layer_instruction(
    context_pack: Optional[Any],
    notebook_id: str,
) -> str:
    """Construye la directiva de síntesis dialéctica tri-capa (Feynman + Rigor + Máquina)."""
    classified = classify_sources_by_role(context_pack, notebook_id)

    ped_note = f" (Fuentes: {', '.join(classified['pedagogical'])})" if classified["pedagogical"] else ""
    form_note = f" (Fuentes: {', '.join(classified['formal'])})" if classified["formal"] else ""
    tech_note = f" (Fuentes: {', '.join(classified['technical'])})" if classified["technical"] else ""

    instruction = (
        "=== DIMENSIONES EXPLICATIVAS DISPONIBLES ===\n"
        f"- Intuición o analogía{ped_note}: usala solo si ayuda a esta pregunta; explicá qué representa y dónde deja de aplicar.\n"
        f"- Mecanismo o formalismo{form_note}: desarrollalo cuando sea necesario para responder con precisión. "
        "Cita las fuentes formales únicamente cuando estén disponibles en el contexto.\n"
        f"- Implementación o nivel de máquina{tech_note}: incluí esta capa solo si el tema o el pedido lo requiere; "
        "explicita el sistema, arquitectura o versión si se conocen y no los supongas si faltan.\n"
        "- Elegí y ordená las dimensiones pertinentes según la tarea; no conviertas esta lista en tres secciones obligatorias.\n"
        "- Agregá una pregunta de comprobación o continuación solo si es útil y compatible con el formato y la extensión pedidos.\n"
    )
    return instruction


RESPONSE_MODES: Dict[str, Dict[str, Any]] = {
    "explain_concept": {"layers": 3, "socratic": True, "max_words": 400, "format": "tri_layer"},
    "debug_crash": {"layers": 0, "socratic": True, "max_words": 900, "format": "debug_analysis"},
    "resolve_misconception": {"layers": 3, "socratic": True, "max_words": 1500, "format": "epistemic_scaffolding"},
    "compare": {"layers": 0, "socratic": True, "max_words": 300, "format": "table"},
    "give_example": {"layers": 0, "socratic": False, "max_words": 500, "format": "code"},
    "simplify": {"layers": 1, "socratic": False, "max_words": 200, "format": "feynman_simple"},
    "evaluate_code": {"layers": 3, "socratic": True, "max_words": 2500, "format": "forensic_audit"},
    "deep_dive": {"layers": 3, "socratic": True, "max_words": 2500, "format": "exhaustive_tri_layer"},
    "quick_answer": {"layers": 0, "socratic": False, "max_words": 100, "format": "concise"},
}


class ResponseIntent(BaseModel):
    """Resolved task and explicit output constraints for one learner turn."""

    model_config = ConfigDict(frozen=True)

    task: str
    mode: str
    depth: Optional[Literal["brief", "standard", "deep"]] = None
    max_sentences: Optional[int] = None
    max_lines: Optional[int] = None
    max_words: Optional[int] = None
    output_format: Optional[Literal["table", "list", "pseudocode", "diagram", "plain_text", "code"]] = None
    include: tuple[str, ...] = ()
    code_language: Optional[str] = None
    exclude_code: bool = False
    exclude_follow_up: bool = False

    @property
    def has_explicit_constraints(self) -> bool:
        return any(
            (
                self.depth is not None,
                self.max_sentences is not None,
                self.max_lines is not None,
                self.max_words is not None,
                self.output_format is not None,
                bool(self.include),
                self.code_language is not None,
                self.exclude_code,
                self.exclude_follow_up,
            )
        )

    def to_prompt_instruction(self) -> str:
        constraints: List[str] = []
        if self.max_sentences is not None:
            constraints.append(f"no excedas {self.max_sentences} frase(s)")
        if self.max_lines is not None:
            constraints.append(f"no excedas {self.max_lines} línea(s)")
        if self.max_words is not None:
            constraints.append(f"no excedas {self.max_words} palabra(s)")
        if self.depth == "deep":
            constraints.append("priorizá el mecanismo y los matices esenciales dentro del límite pedido")
        elif self.depth == "brief":
            constraints.append("mantené la respuesta breve y directa")

        lines = [
            "=== CONTRATO RESUELTO PARA ESTE TURNO ===",
            f"- Tarea principal: {self.task}.",
        ]
        if constraints:
            lines.append(f"- Restricciones explícitas del estudiante: {'; '.join(constraints)}.")
        if self.output_format is not None:
            lines.append(f"- Formato solicitado: {self.output_format}.")
        if self.include:
            lines.append(f"- Elementos pedidos explícitamente: {', '.join(self.include)}.")
        if self.task == "proponer o continuar un ejercicio guiado":
            lines.append(
                "- Conservá el tema del historial reciente, proponé un ejercicio claro y evaluable, "
                "y esperá el intento sin revelar la solución completa."
            )
        if self.code_language is not None:
            lines.append(
                f"- El estudiante pidió explícitamente un ejemplo en {self.code_language}; "
                "podés incluir el bloque de código necesario y explicarlo al nivel adecuado."
            )
        if self.exclude_code:
            lines.append(
                "- El estudiante excluyó el código ejecutable y las pruebas; no los incluyas. "
                "Si pidió pseudocódigo, usá un bloque ```text y mantenelo independiente de la sintaxis de un lenguaje."
            )
        if self.exclude_follow_up:
            lines.append("- No agregues una pregunta, ejercicio ni oferta de continuación al final.")
        if (
            self.task == "proponer o continuar un ejercicio guiado"
            or constraints
            or self.output_format is not None
            or self.include
            or self.code_language is not None
            or self.exclude_code
            or self.exclude_follow_up
        ):
            lines.extend(
                (
                    "- Este contrato prevalece solo sobre preferencias de extensión, formato y cierre que lo contradigan.",
                    "- Conservá exactitud técnica, límites de alcance, seguridad y requisitos de evidencia/fuentes.",
                    "- Si el límite impide cubrir todos los matices, no afirmes exhaustividad; priorizá lo esencial.",
                )
            )
        return "\n".join(lines)


_NEGATED_SYNTHESIS_PATTERNS = (
    re.compile(r"\bno\s+(?:(?:lo|me\s+lo)\s+)?resumas?\b", re.IGNORECASE),
    re.compile(r"\bno\s+hagas?\s+(?:un\s+)?resumen\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:quiero|necesito)\s+(?:que\s+me\s+)?(?:des?\s+)?(?:un\s+)?resumen\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:(?:lo|me\s+lo)\s+)?sintetices?\b", re.IGNORECASE),
    re.compile(r"\bno\s+hagas?\s+una?\s+s[ií]ntesis\b", re.IGNORECASE),
)


def _has_negated_synthesis_request(query: str) -> bool:
    return any(pattern.search(query) for pattern in _NEGATED_SYNTHESIS_PATTERNS)


def resolve_response_intent(
    user_query: str,
    pedagogical_mode: Optional[str] = None,
) -> ResponseIntent:
    """Resolve the requested task separately from explicit output constraints."""
    q = user_query.strip()
    q_lower = q.lower()
    synthesis_negated = _has_negated_synthesis_request(q)
    parsed_command = parse_student_command(q)
    explicit_solution_request = bool(
        parsed_command is not None
        and parsed_command.command_type.value == "DAME_SOLUCION_COMPLETA"
    ) or bool(re.search(r"(?<![\w]):solve(?![\w])", q_lower)) or bool(
        re.search(
            r"\b(?:dame|pasame|pasá|mostrame|mostrá|quiero)\s+(?:la\s+)?"
            r"soluci[oó]n\s+completa\b|\b(?:soluci[oó]n|c[oó]digo|"
            r"implementaci[oó]n)\s+complet[oa]\s+(?:del|de\s+este|de\s+la)\b|"
            r"\b(?:dame|pasame|pasá|mostrame|mostrá|quiero)\s+(?:el\s+)?"
            r"(?:c[oó]digo|implementaci[oó]n)\s+complet[oa](?:\s+terminad[oa])?\b",
            q_lower,
        )
    )

    exercise_request = bool(
        re.search(
            r"\b(?:hagamos|h[aá]game|dame|proponeme|prop[oó]n)\s+"
            r"(?:(?:el|un)\s+)?ejercicio\b|\bejercicio\s+para\s+(?:practicar|resolver)\b",
            q_lower,
        )
    )
    recommendation_request = bool(
        re.search(
            r"\b(?:qu[eé]\s+(?:tema|t[oó]pico|concepto)\s+(?:me\s+)?"
            r"(?:conviene|recomend[aá]s?|estudiar|seguir)|"
            r"(?:qu[eé]\s+sigue|por\s+d[oó]nde\s+seguimos|"
            r"qu[eé]\s+estudio\s+ahora|recomendame\s+(?:un\s+)?(?:tema|siguiente\s+paso)))\b",
            q_lower,
        )
    )
    laboratory_request = bool(
        re.search(
            r"\b(?:laboratorio|lab)\s+(?:conceptual|guiado|de\s+pr[aá]ctica)\b|"
            r"\b(?:armemos|diseñ[aá]|propon[eé])\s+(?:un\s+)?(?:laboratorio|lab)\b",
            q_lower,
        )
    )
    feedback_request = bool(
        re.search(
            r"\b(?:revis[aá]|correg[ií]|evalu[aá]|verific[aá])\s+"
            r"(?:mi\s+)?(?:respuesta|intento|soluci[oó]n|ejercicio|c[oó]digo)\b|"
            r"\b(?:qu[eé]\s+hice\s+mal|en\s+qu[eé]\s+me\s+equivoqu[eé]|"
            r"est[aá]\s+bien\s+mi\s+(?:respuesta|soluci[oó]n|c[oó]digo))\b",
            q_lower,
        )
    )
    reexplanation_request = bool(
        re.search(
            r"\b(?:no\s+entend[ií]|no\s+entiendo|no\s+comprendo|"
            r"no\s+me\s+queda\s+claro|explic[aá]melo?\s+de\s+otra\s+"
            r"(?:manera|forma)|otra\s+forma\s+de\s+explicarlo)\b",
            q_lower,
        )
    )

    if explicit_solution_request:
        mode = pedagogical_mode or classify_pedagogical_intent(q)
    elif exercise_request:
        mode = pedagogical_mode or "explain_concept"
    elif synthesis_negated:
        mode = pedagogical_mode or classify_pedagogical_intent(q)
        if mode == "quick_answer":
            mode = "explain_concept"
    elif re.search(
        r"\b(?:resum(?:e|í|i|ime|ir)|resumen|sintetiz(?:a|á|ame|ame)|s[ií]ntesis|"
        r"en\s+una\s+frase|en\s+pocas\s+palabras|brevemente|tl\s*;?\s*dr)\b",
        q_lower,
    ):
        mode = "quick_answer"
    else:
        mode = pedagogical_mode or classify_pedagogical_intent(q)

    if explicit_solution_request:
        task = "entregar solución completa solicitada"
    elif exercise_request:
        task = "proponer o continuar un ejercicio guiado"
    elif mode == "quick_answer":
        task = "sintetizar o responder brevemente"
    elif feedback_request:
        task = "revisar un intento o corregir una respuesta"
    elif reexplanation_request and not re.search(
        r"\b(?:pero|en\s+(?:matem[aá]ticas|realidad)|si\s+(?:el|la|un|una))\b",
        q_lower,
    ):
        task = "reexplicar con otro enfoque"
    elif recommendation_request:
        task = "recomendar el siguiente paso"
    elif laboratory_request:
        task = "diseñar un laboratorio conceptual"
    elif mode == "give_example":
        task = "proporcionar un ejemplo"
    elif mode == "compare":
        task = "comparar"
    elif mode == "resolve_misconception":
        task = "resolver una concepción errónea"
    elif mode == "evaluate_code":
        task = "evaluar código o una solución"
    elif mode == "deep_dive":
        task = "explicar en profundidad"
    elif mode == "simplify":
        task = "explicar de forma sencilla"
    else:
        task = "responder la consulta"

    depth: Optional[Literal["brief", "standard", "deep"]] = None
    if mode == "quick_answer":
        depth = "brief"
    elif re.search(
        r"\b(?:en\s+profundidad|a\s+fondo|exhaustiv[oa]|con\s+todos\s+los\s+detalles|paso\s+a\s+paso)\b",
        q_lower,
    ):
        depth = "deep"
    elif re.search(r"\b(?:breve|brevemente|conciso|concisa|corto|corta)\b", q_lower):
        depth = "brief"

    count_match = re.search(
        r"\b(?:en\s+)?(\d+)\s+(frases?|oraciones?|l[ií]neas?|palabras?)\b",
        q_lower,
    )
    max_sentences: Optional[int] = None
    max_lines: Optional[int] = None
    max_words: Optional[int] = None
    if count_match:
        count = int(count_match.group(1))
        unit = count_match.group(2)
        if unit.startswith(("frase", "oraci")):
            max_sentences = count
        elif unit.startswith("l"):
            max_lines = count
        else:
            max_words = count
    elif re.search(r"\ben\s+una\s+frase\b", q_lower):
        max_sentences = 1

    output_format: Optional[
        Literal["table", "list", "pseudocode", "diagram", "plain_text", "code"]
    ] = None
    if re.search(
        r"\b(?:en\s+(?:una?\s+)?(?:tabla|cuadro\s+comparativo)|"
        r"formato\s+tabular|(?:dame|mostrame|mostr[aá]|arm[aá]|hac[eé])\s+"
        r"(?:una?\s+)?tabla)\b",
        q_lower,
    ):
        output_format = "table"
    elif re.search(
        r"\b(?:en\s+(?:forma\s+de\s+)?lista|en\s+viñetas|en\s+vinetas|"
        r"bullet\s+points|(?:dame|mostrame|mostr[aá])\s+(?:una?\s+)?lista)\b",
        q_lower,
    ):
        output_format = "list"
    elif re.search(
        r"\b(?:en\s+(?:pseudoc[oó]digo|pseudocode)|como\s+(?:pseudoc[oó]digo|pseudocode)|"
        r"(?:dame|mostrame|mostr[aá]|escribime|inclu[ií])\b.{0,40}"
        r"(?:pseudoc[oó]digo|pseudocode)|requisitos?\b.{0,160}"
        r"(?:pseudoc[oó]digo|pseudocode))\b",
        q_lower,
    ):
        output_format = "pseudocode"
    elif re.search(
        r"\b(?:diagrama(?:\s+de\s+flujo)?\s+en\s+mermaid|"
        r"en\s+mermaid|con\s+(?:un\s+)?diagrama|"
        r"(?:dame|haceme|hac[eé]|mostrame|mostr[aá]|inclu[ií]|agreg[aá]|gener[aá])\b.{0,40}"
        r"\b(?:diagrama|esquema\s+visual))\b",
        q_lower,
    ):
        output_format = "diagram"
    elif re.search(r"\b(?:solo\s+texto|s[oó]lo\s+texto|en\s+prosa)\b", q_lower):
        output_format = "plain_text"

    requested_includes: List[str] = []
    if re.search(r"\b(?:con\s+(?:un\s+)?ejemplo|inclu[ií]\s+(?:un\s+)?ejemplo)\b", q_lower):
        requested_includes.append("ejemplo")
    if re.search(r"\b(?:con\s+(?:una\s+)?analog[ií]a|inclu[ií]\s+(?:una\s+)?analog[ií]a)\b", q_lower):
        requested_includes.append("analogía")
    if re.search(r"\b(?:paso\s+a\s+paso|explic[aá]\s+el\s+mecanismo)\b", q_lower):
        requested_includes.append("mecanismo paso a paso")
    if re.search(r"\b(?:conexi[oó]n|relaci[oó]n)\s+(?:con|a)\s+(?:la\s+)?ciberseguridad\b", q_lower):
        requested_includes.append("conexión con ciberseguridad")

    exclude_code = bool(
        re.search(
            r"\b(?:sin\s+(?:usar\s+|incluir\s+|mostrar\s+)?c[oó]digo|"
            r"no\s+(?:uses|incluyas|muestres|generes)\s+c[oó]digo)\b",
            q_lower,
        )
    )
    code_language: Optional[
        Literal["c", "python", "c++", "java", "javascript", "rust", "go", "sql", "php"]
    ] = None
    if not exclude_code:
        code_match = re.search(
            r"\b(?:dame|pasame|pasá|hacer|haceme|hacé|hace|mostrar|mostrame|mostr[aá]|escribime|escribí|escribe|generame|generá|"
            r"genera|incluí|inclui|incluye|agregá|agrega|implementá|implementa|programá|programa|"
            r"diseñar|diseñá|diseña|crear|crea|creá|traducí|traduci|convertí|converti)\b.{0,80}\b(?:c[oó]digo|ejemplo|programa|"
            r"script|implementaci[oó]n|funci[oó]n)?\b.{0,40}\b(c\+\+|python|java|javascript|rust|go|c|sql|php)\b|"
            r"\bcon\s+(?:un\s+)?(?:c[oó]digo|ejemplo|implementaci[oó]n)\s+(?:en\s+)?"
            r"(c\+\+|python|java|javascript|rust|go|c|sql|php)\b|"
            r"\b(?:c[oó]digo|implementaci[oó]n)\s+(?:en\s+)?"
            r"(c\+\+|python|java|javascript|rust|go|c|sql|php)\s+con\s+(?:tests?|pytest|pruebas?)\b",
            q_lower,
        )
        if code_match:
            code_language = next(group for group in code_match.groups() if group).lower()
            output_format = "code"
            requested_includes.append(f"código {code_language}")

    exclude_follow_up = bool(
        re.search(
            r"\b(?:sin\s+pregunta(?:s)?(?:\s+al\s+final)?|"
            r"no\s+(?:hagas|agregues|incluyas)\s+(?:una\s+)?preguntas?|"
            r"solo\s+la\s+respuesta|s[oó]lo\s+la\s+respuesta)\b",
            q_lower,
        )
    )
    if max_sentences == 1 or max_lines is not None or mode == "quick_answer":
        exclude_follow_up = True

    return ResponseIntent(
        task=task,
        mode=mode,
        depth=depth,
        max_sentences=max_sentences,
        max_lines=max_lines,
        max_words=max_words,
        output_format=output_format,
        include=tuple(requested_includes),
        code_language=code_language,
        exclude_code=exclude_code,
        exclude_follow_up=exclude_follow_up,
    )


def build_pedagogical_strategy_instruction(intent: ResponseIntent) -> str:
    """Build an adaptable task policy that takes precedence over legacy style defaults."""
    task_instructions = {
        "responder la consulta": (
            "- Contestá primero la pregunta de forma directa; definí solo los términos necesarios.\n"
            "- Explicá el mecanismo o agregá un ejemplo cuando ayude a entender, no por rutina.\n"
            "- Usá una analogía solo si aporta; no fuerces Python, código, secciones ni una pregunta final."
        ),
        "explicar en profundidad": (
            "- Desarrollá capas pertinentes: intuición, conceptos/prerrequisitos, mecanismo y matices técnicos "
            "que correspondan al tema y al pedido.\n"
            "- La profundidad no implica longitud ilimitada: respetá cualquier límite explícito y señalá lo que "
            "quede fuera sin afirmar exhaustividad."
        ),
        "sintetizar o responder brevemente": (
            "- Conservá el hecho central y la precisión dentro del formato y límite solicitados.\n"
            "- Omití introducciones, cierres, quizzes y preguntas adicionales que excedan el pedido."
        ),
        "proponer o continuar un ejercicio guiado": (
            "- Proponé una consigna clara, evaluable y vinculada al tema disponible; indicá un primer paso "
            "accionable y esperá el intento.\n"
            "- No reveles la solución completa salvo que el estudiante la pida explícitamente."
        ),
        "entregar solución completa solicitada": (
            "- Entregá la solución completa solicitada en el formato pedido, con explicación proporcional y "
            "verificaciones o casos límite pertinentes.\n"
            "- No apliques el andamiaje anti-atajo por defecto contra este pedido, salvo que el contexto identifique "
            "una evaluación activa/protegida; en ese caso, no reveles el solucionario canónico y ofrecé ayuda "
            "conceptual, feedback sobre el intento visible o un ejemplo análogo."
        ),
        "revisar un intento o corregir una respuesta": (
            "- Usá solo el intento disponible en la consulta o el historial reciente: señalá primero lo "
            "correcto, después el primer error concreto y por qué, y ofrecé un siguiente paso útil.\n"
            "- No inventes un intento ni repitas toda la solución si no hace falta; si no hay respuesta visible, "
            "decilo y pedile que comparta su respuesta."
        ),
        "resolver una concepción errónea": (
            "- Identificá la intuición o afirmación concreta del estudiante y separá qué parte es válida de "
            "dónde deja de aplicar.\n"
            "- Explicá el mecanismo y el contexto pertinente sin asumir una materia, versión, causa o analogía "
            "que no estén sustentadas."
        ),
        "reexplicar con otro enfoque": (
            "- Reconocé brevemente la dificultad y cambiá realmente la representación, escala o ejemplo; "
            "dividí el paso confuso y revisá un prerrequisito si hace falta.\n"
            "- No repitas literalmente la explicación anterior ni afirmes conocer qué falló si el historial no lo muestra."
        ),
        "recomendar el siguiente paso": (
            "- Basá la recomendación en los temas y preguntas visibles, como propuesta tentativa y explicando "
            "por qué conecta con ellos.\n"
            "- No afirmes dominio o progreso medido por una respuesta aislada; si falta contexto, reconocelo y "
            "pedí una aclaración breve."
        ),
        "diseñar un laboratorio conceptual": (
            "- Indicá objetivo, entorno o precondiciones relevantes, pasos seguros, resultado esperado e "
            "interpretación; adaptalos a la materia.\n"
            "- No ejecutes acciones reales ni propongas operaciones inseguras implícitamente."
        ),
    }
    instruction = task_instructions.get(intent.task)
    if instruction is None:
        return ""
    return (
        "=== ESTRATEGIA PEDAGÓGICA PARA ESTA TAREA ===\n"
        f"Tarea resuelta: {intent.task}.\n"
        f"{instruction}\n"
        "Estas reglas describen requisitos semánticos, no una plantilla textual fija. "
        "Respetá exactitud, seguridad, fuentes y límites superiores; el contrato explícito del turno "
        "prevalece sobre las preferencias de formato o cierre. No fuerces una pregunta socrática ni otro "
        "componente de plantilla salvo que la tarea o el estudiante lo requieran.\n"
    )


def classify_pedagogical_intent(user_query: str) -> str:
    """Clasifica la intención pedagógica de la consulta para seleccionar el RESPONSE_MODE óptimo (Fix S4.1)."""
    q = user_query.strip().lower()

    # 1. Quick answer: explicit synthesis or very brief answer; ignore negated requests.
    if not _has_negated_synthesis_request(q) and re.search(
        r"\b(?:resum(?:e|í|i|ime|ir)|resumen|sintetiz(?:a|á|ame|ame)|s[ií]ntesis|"
        r"en\s+una\s+frase|en\s+pocas\s+palabras|brevemente|tl\s*;?\s*dr)\b",
        q,
    ):
        return "quick_answer"

    if any(p in q for p in (
        "en una frase", "en pocas palabras", "definicion rapida", "definición rápida",
        "respuesta rapida", "respuesta rápida", "brevemente", "en un renglon", "en un renglón",
        "directo al grano", "sólo decime si", "solo decime si"
    )):
        return "quick_answer"

    # 2. Debug crash / Análisis de caída y fallas de memoria (Prioridad alta sobre auditoría general)
    if any(p in q for p in (
        "crashea", "crasheo", "segmentation fault", "segfault", "por qué falla", "por que falla",
        "por qué crashea", "por que crashea", "qué le pasa a la memoria", "que le pasa a la memoria",
        "violación de segmento", "violacion de segmento", "memory leak", "se rompe"
    )):
        return "debug_crash"

    # 3. Evaluate / Audit code: auditoría forense o revisión de código/algoritmo
    if any(p in q for p in (
        "auditar", "audita", "auditoría", "auditoria", "auditor",
        "bugs sutiles", "bugs", "bug", "fallas", "falla", "vulnerabilidades", "vulnerabilidad", "defectos", "defecto",
        "evalua mi codigo", "evalúa mi código", "revisa este codigo", "revisa este código",
        "esta bien este codigo", "está bien este código", "corrige este codigo", "corrige este código",
        "analiza este algoritmo", "review de codigo", "review de código", "debuguear", "depurar",
        "qué fallas", "que fallas", "dónde falla", "donde falla", "señalar fallas", "señalar las fallas",
        "señala las fallas", "señala fallas", "casos de borde que no detecta", "edge cases que no detecta",
        "auditar la siguiente", "audita la siguiente", "auditar este", "audita este"
    )) or ("```" in q and any(w in q for w in ("bien", "error", "falla", "revisar", "opinas", "correccion", "qué tal", "auditar", "auditoría", "bugs", "bug", "vulnerabilidad"))):
        return "evaluate_code"

    # 3. Compare: comparación / contraste / tabla
    if any(p in q for p in (
        "compara", "compará", "comparar", "diferencia entre", "diferencias entre", " vs ", "versus",
        "cuadro comparativo", "tabla comparativa", "frente a", "contrastar", "en que se diferencia", "en qué se diferencia"
    )):
        return "compare"

    # 4. Give example: código práctico / ejemplo
    if any(p in q for p in (
        "dame un ejemplo", "dar un ejemplo", "mostrame un ejemplo",
        "mostrar un ejemplo", "podés mostrar un ejemplo", "podes mostrar un ejemplo",
        "podrias mostrar un ejemplo", "podrías mostrar un ejemplo", "ejemplo practico",
        "ejemplo práctico", "ejemplo de codigo", "ejemplo de código", "como se implementa",
        "cómo se implementa", "ejemplifica", "escribe un script", "escribir codigo", "escribir código"
    )):
        return "give_example"

    # 5. Simplify: analogía sencilla / ELI5 / Feynman simple
    if any(p in q for p in (
        "simplifica", "simplificar", "explicamelo simple", "explícamelo simple",
        "en palabras simples", "como si tuviera 5", "para un nino", "para un niño",
        "eli5", "muy simple", "feynman simple", "sin tecnicismos", "para principiantes"
    )):
        return "simplify"

    # 6. Deep dive: profundidad exhaustiva / formalismo completo
    if any(p in q for p in (
        "en profundidad", "deep dive", "analisis exhaustivo", "análisis exhaustivo",
        "detalle tecnico completo", "detalle técnico completo", "rigor formal exhaustivo",
        "todos los detalles", "paso a paso", "analisis riguroso a fondo", "análisis riguroso a fondo",
        "explicame mas", "explicamelo mas", "explicá más", "explica más", "explayate",
        "explayate más", "más detalles", "mas detalles", "a fondo", "quiero mas profundidad",
        "quiero más profundidad"
    )):
        return "deep_dive"

    # 7. Resolve misconception / Duda conceptual o conflicto epistémico
    if any(p in q for p in (
        "no logre entender", "no logré entender", "no entendí", "no entendi", "no comprendo", "no entiendo",
        "no entiendo por qué", "no entiendo porque", "no entiendo por que",
        "por qué decís que", "por que decis que", "por qué dices que", "por que dices que",
        "por qué decís", "por qué dices",
        "por qué es un error si", "por que es un error si",
        "por qué está mal si", "por que esta mal si",
        "por qué debería rechazarlo si", "por que deberia rechazarlo si",
        "por qué el código debería rechazarlo", "por que el codigo deberia rechazarlo",
        "por qué debería fallar si", "por que deberia fallar si",
        "por qué es un peligro si", "por que es un peligro si",
        "por qué es peligroso si", "por que es peligroso si",
        "pero en matemáticas", "pero en matematicas", "en la vida real un cero a la izquierda",
        "no me queda claro por qué", "no me queda claro porque", "no me queda claro",
        "no tiene sentido que sea un error", "no tiene sentido que falle",
        "por qué decís que es un error", "por qué decís que está mal",
        "si en matemáticas", "si en matematicas"
    )):
        return "resolve_misconception"

    # 8. Default: Explicación conceptual dialéctica
    return "explain_concept"


def build_mode_specific_instruction(
    mode: str,
    context_pack: Optional[Any],
    notebook_id: str,
    user_query: Optional[str] = None,
    context_mode: Optional[str] = None,
) -> str:
    """Construye la directiva pedagógica específica según el modo de respuesta seleccionado (Fix S4.1)."""
    mode_config = RESPONSE_MODES.get(mode, RESPONSE_MODES["explain_concept"])
    layers = mode_config.get("layers", 3)
    fmt = mode_config.get("format", "tri_layer")

    q_lower = (user_query or "").lower()
    is_debug_question = bool(re.search(
        r"\b(?:por\s+qu[eé]\s+(?:falla|crashea|da\s+segfault|se\s+rompe)|qu[eé]\s+le\s+pasa\s+a\s+la\s+memoria|por\s+qu[eé]\s+est[aá]\s+roto)\b",
        q_lower,
    ))

    if mode == "debug_crash" or is_debug_question:
        return (
            "=== ANÁLISIS PEDAGÓGICO DE FALLAS ===\n"
            "- Partí del síntoma y del código/entorno realmente provistos; si faltan, pedí el dato mínimo o separá hipótesis de hechos.\n"
            "- Explicá la secuencia causal y las condiciones necesarias para reproducir el fallo. No asumas lenguaje, memoria, arquitectura, "
            "señal, sistema operativo ni causa raíz sin evidencia.\n"
            "- Ofrecé una comprobación o corrección segura y proporcional al pedido. Usá código, diagramas o analogías solo si ayudan "
            "y respetá las restricciones explícitas."
        )

    if mode == "evaluate_code" or fmt in ("forensic_audit", "review"):
        return (
            "=== REVISIÓN DE CÓDIGO Y ANÁLISIS TÉCNICO ===\n"
            "- Analizá el código o intento realmente provisto; no inventes fragmentos ni defectos. Separá aciertos, problemas observables "
            "y preguntas que dependan de contexto ausente.\n"
            "- Para cada problema, indicá el fragmento y la condición que lo activa, el efecto plausible y un siguiente paso o corrección "
            "proporcional. No atribuyas vulnerabilidad, impacto o explotabilidad sin precondiciones y evidencia suficientes.\n"
            "- No fuerces CVE, ejemplos de ataque, arquitectura, lenguaje, código de reemplazo, complejidad o formato de informe si no son "
            "pertinentes o solicitados."
        )

    if mode == "resolve_misconception" or fmt == "epistemic_scaffolding":
        return (
            "=== REPARACIÓN DE CONFUSIÓN CONCEPTUAL ===\n"
            "- Respondé a la afirmación o intuición concreta del estudiante: reconocé qué parte puede ser válida y delimitá dónde cambia "
            "el significado o deja de aplicar.\n"
            "- Explicá el mecanismo y las condiciones relevantes para este concepto. Si la diferencia depende de lenguaje, plataforma, "
            "versión o configuración, hacé explícita esa dependencia en vez de asumir un caso.\n"
            "- Cambiá de representación solo si ayuda; explicá el límite de la analogía y no añadas incidentes, CVE o consecuencias de "
            "seguridad sin evidencia autorizada."
        )

    if context_mode == "basic" and mode == "explain_concept":
        return (
            "=== DIRECTIVA DE RESPUESTA INTRODUCTORIA ===\n"
            "- Explicá con analogías cotidianas simples y ejemplos concretos sostenidos.\n"
            "- Usá pseudocódigo legible con mensajes cotidianos (ej: ESCRIBIR 'Error: entrada inválida').\n"
            "- Evitá diagramas de hardware y detalles de bajo nivel salvo pedido explícito del estudiante.\n"
            "- Cerrá con una pregunta de verificación básica: pedí un ejemplo cotidiano con entrada, proceso y salida.\n"
        )

    if layers == 3:
        classified = classify_sources_by_role(context_pack, notebook_id)
        ped_note = f" (Fuentes: {', '.join(classified['pedagogical'])})" if classified["pedagogical"] else ""
        form_note = f" (Fuentes: {', '.join(classified['formal'])})" if classified["formal"] else ""
        tech_note = f" (Fuentes: {', '.join(classified['technical'])})" if classified["technical"] else ""

        depth_hint = (
            " Desarrollá las capas pertinentes con rigor, sin asumir una extensión ilimitada."
            if mode == "deep_dive"
            else " Ajustá la profundidad a la tarea y a las restricciones explícitas."
        )
        return (
            f"=== DIRECTIVA DE SÍNTESIS DIALÉCTICA DIMENSIONAL (ESTILO FEYNMAN + RIGOR){depth_hint} ===\n"
            "Estructurá tu respuesta con la máxima legibilidad y riqueza visual, combinando prosa fluida con jerarquía nítida. "
            "NO uses títulos de plantilla genéricos y rígidos como '1. Intuición Conceptual' o '2. Mecanismo Formal'. "
            "En su lugar, utilizá subtítulos contextuales vivos y descriptivos alusivos al tema (ej: '### 1. El modelo mental del acceso restringido', '### 2. Álgebra booleana y evaluación perezosa', '### 3. Anatomía en silicio y registros'), "
            "separando los bloques principales con líneas divisorias Markdown ('---') para que la lectura respire.\n"
            "Dale libertad y fluidez a la explicación sin recortar desarrollo conceptual ni forzar un límite artificial de párrafos por sección; explicá cada paso con naturalidad.\n\n"
            "REGLAS DE FORMATO Y PRESENTACIÓN VISUAL:\n"
            "- **DESGLOSE DE ENTIDADES EN LISTAS / BULLETS**: Al detallar registros, banderas, campos o parámetros, NO los amontones en un solo párrafo denso. Desglosalos con viñetas claras y negritas, por ejemplo:\n"
            "  * **`RIP / EIP` (*Instruction Pointer*):** Contiene la dirección física de la próxima instrucción...\n"
            "  * **`RSP / ESP` (*Stack Pointer*):** Marca la cima actual de la pila...\n"
            "  * **`FLAGS (ZF/CF)`:** Almacena el resultado eléctrico de la ALU...\n"
            "- **RIGOR EN LA ELECCIÓN DE ESTRUCTURAS DE CONTROL**: Al explicar o diseñar algoritmos, elegí la estructura que corresponda al problema y justificá el trade-off cuando sea relevante; no declares una forma universalmente óptima.\n"
            "- **DIAGRAMAS**: Usá Mermaid o un esquema de texto solo si aclara el flujo, los estados o la disposición que pregunta el estudiante.\n"
            "- **MAPAS DE MEMORIA/ARQUITECTURA**: Incluí una representación solo si el tema la requiere o el estudiante la pide; distinguí el modelo conceptual del layout dependiente de implementación.\n"
            "- **REGLA DE FAIL-CLOSED DIRECTO (TÉRMINOS APÓCRIFOS O INEXISTENTES)**: Si la consulta del alumno indaga sobre una supuesta directiva, opción, función o término apócrifo/inexistente (ej: `__fast_ptr_opt` u optimizaciones mágicas inventadas):\n"
            "  1. Tu primera frase de respuesta DEBE ser tajante y directa: 'Frenemos la pelota un segundo, che: la directiva [TÉRMINO] no existe.' (o '[TÉRMINO] no existe.').\n"
            "  2. Segunda frase: Explicá con concisión que no forma parte de ningún estándar oficial (C, POSIX, System V ABI ni compiladores GCC/Clang).\n"
            "  3. Tercera frase: Redirigí a lo que SÍ existe ('Lo que sí existe y se utiliza en la arquitectura real es...').\n"
            "  ESTRICTAMENTE PROHIBIDO dar rodeos diplomáticos como 'La supuesta directiva no forma parte de ninguna especificación estándar... por lo que no existe a nivel de optimización de silicio'. Sé directo: '[TÉRMINO] no existe'.\n"
            "- **EJEMPLOS DE CÓDIGO**: Incluí código ejecutable solo si se solicita o si es necesario para explicar la tarea. Respetá el lenguaje indicado y no bloquees una solución completa expresamente pedida.\n"
            "- **PRECISIÓN DE ARQUITECTURA Y REGISTROS**: No asumas ISA, OS, ABI, convención de llamada ni registros. Si el contexto no los especifica, presentá el principio general o declaralos como un ejemplo condicionado; no atribuyas un registro a un rol universal.\n"
            "- **SANITIZACIÓN ESTRICTA DE SALIDA**: Prohibido mostrar al usuario etiquetas internas del motor de búsqueda o de confianza. NUNCA imprimas texto como '[ref. no verificada]', '[E# missing]', o tags de probabilidad.\n"
            "- **TABLAS COMPARATIVAS**: Usá una tabla cuando facilite la comparación; una respuesta directa no la necesita por defecto.\n"
            "- **TONO RIOPLATENSE NATURAL Y DIRECTO**: Utilizá giros cercanos y naturales ('che', 'fijate', 'mirá cómo conmuta en la RAM', 'vamos paso a paso desarmando el silicio') manteniendo rigurosa seriedad técnica y sin saludos ni halagos iniciales.\n\n"
            "DIMENSIONES DISPONIBLES (ELEGÍ SOLO LAS PERTINENTES):\n"
            f"- Intuición o analogía opcional{ped_note}: usala solo si aclara el concepto y explicá su límite.\n"
            f"- Definición, mecanismo, formalismo o pseudocódigo{form_note}: incluí las partes que ayuden a responder el pedido.\n"
            f"- Detalle de implementación o máquina{tech_note}: agregalo solo cuando la pregunta lo requiera y con plataforma/ABI explícitas si se conocen.\n"
            "- Implicaciones de seguridad: conectalas solo cuando haya una relación causal defendible y evidencia para las afirmaciones específicas; no agregues incidentes por rutina.\n"
            "- Cerrá con pregunta o propuesta de continuación solo cuando sea útil y compatible con el contrato del turno.\n"
        )
    elif layers == 1:
        return (
            "=== DIRECTIVA DE SÍNTESIS SIMPLIFICADA (ESTILO FEYNMAN ACCESIBLE) ===\n"
            "- Explicá la intuición central con lenguaje sencillo; usá una analogía cotidiana solo si ayuda y delimitá su alcance.\n"
            "- Desmitificá cualquier complejidad innecesaria; priorizá la claridad absoluta sobre la jerga técnica.\n"
            "- No fuerces capas de formalismo matemático ni código de máquina salvo que sea indispensable para la intuición.\n"
        )
    else:  # layers == 0
        if fmt == "table":
            return (
                "=== DIRECTIVA DE COMPARACIÓN ESTRUCTURADA (FORMATO TABLA) ===\n"
                "- Construí una tabla comparativa en Markdown con columnas bien definidas (Criterio, Opción A, Opción B, Impacto/Trade-off).\n"
                "- Detallá debajo de la tabla un análisis sintético de pros, contras y escenarios recomendados para cada alternativa.\n"
                "- Mantené un tono directo, analítico y enfocado en la toma de decisiones técnicas.\n"
            )
        elif fmt == "code":
            return (
                "=== DIRECTIVA DE EJEMPLO PRÁCTICO (FORMATO CÓDIGO IDIOMÁTICO) ===\n"
                "- Proporcioná un bloque de código ejecutable, idiomático y autocontenido que ejemplifique la solución.\n"
                "- Comentá en el código las líneas críticas que definen la lógica o el patrón de diseño.\n"
                "- Explicá brevemente las entradas requeridas, la salida esperada y una advertencia sobre errores comunes.\n"
            )
        elif fmt == "review":
            return (
                "=== DIRECTIVA DE REVISIÓN Y EVALUACIÓN DE CÓDIGO ===\n"
                "- Analizá la correctitud del código, manejo de invariantes y edge cases (desbordamientos, valores nulos, condiciones de carrera).\n"
                "- Evaluá la complejidad algorítmica temporal y espacial (Big-O).\n"
                "- Presentá una versión refactorizada justificada y comentarios constructivos.\n"
            )
        elif fmt == "concise":
            return (
                "=== DIRECTIVA DE RESPUESTA RÁPIDA Y CONCISA ===\n"
                "- Respondé directamente en 1 o 2 oraciones con máxima precisión técnica.\n"
                "- Cero narrativa preliminar, cero analogías largas, información de alta densidad.\n"
            )
        else:
            return ""


class StructuredResponsePipeline:
    """Multi-phase pedagogical response generator eliminating token rationing."""

    def __init__(
        self,
        contract: PedagogicalContract,
        llm_backend: Any,
        phase_history: Optional[PhaseHistory] = None,
        auditor: Optional[Any] = None,
    ) -> None:
        self.contract = contract
        self.llm = llm_backend
        self.history = phase_history or PhaseHistory()
        self.auditor = auditor
        self.guard = SocraticGuard(contract=contract)

    def get_phase(self, phase_id: str) -> ResponsePhase:
        """Retrieve phase configuration from contract."""
        return self.contract.get_phase(phase_id)

    def _get_available_next_phases(self, current_phase_id: str) -> List[str]:
        """Compute permissible subsequent phases in contract sequence."""
        phases: List[str] = [str(p.phase_id) for p in self.contract.response_phases]
        if current_phase_id not in phases:
            return phases
        idx = phases.index(current_phase_id)
        return phases[idx + 1 :]

    def build_phase_prompt(
        self,
        phase: ResponsePhase,
        user_query: str,
        context_pack: Optional[Any] = None,
        pedagogical_mode: Optional[str] = None,
        bkt_directive: Optional[str] = None,
        style_directive: Optional[str] = None,
        recent_turns: Optional[List[dict]] = None,
        metacognitive_profile: Optional[Dict[str, Any]] = None,
        cognitive_profile_block: Optional[str] = None,
        context_mode: Optional[str] = None,
    ) -> str:
        """Assemble the specialized prompt for this phase with PhaseHistory, intent routing, and BKT adaptation."""
        predecessor_context = self.history.format_predecessors_context()
        is_continuation = is_continuation_query(user_query)
        response_intent = resolve_response_intent(user_query, pedagogical_mode)
        active_mode = response_intent.mode

        # Phase prompt template formatting
        if is_continuation:
            rendered_phase_instruction = (
                "CONTINUACIÓN DE RESPUESTA INTERRUMPIDA O TRUNCADA: El estudiante indica que tu respuesta previa se cortó o pide continuarla. "
                "Observá atentamente el fragmento previo de TALOS en el historial reciente y continuá exactamente la sección u oración donde se produjo el corte, "
                "completando los puntos faltantes sin repetir contenido anterior y cerrando con la pregunta socrática."
            )
        elif response_intent.task == "entregar solución completa solicitada":
            rendered_phase_instruction = (
                "SOLUCIÓN COMPLETA SOLICITADA: Resolvé el ejercicio o consulta en el formato que pidió el estudiante. "
                "Explicá las decisiones relevantes y verificá el resultado con comprobaciones pertinentes, sin añadir "
                "componentes o lenguajes que no ayuden a completar la tarea. Si el contexto identifica una evaluación "
                "activa/protegida, no reveles su solucionario canónico: ofrecé explicación conceptual, feedback sobre "
                "el intento visible o un ejemplo análogo que no resuelva el ítem."
            )
        elif response_intent.task == "proponer o continuar un ejercicio guiado":
            rendered_phase_instruction = (
                "EJERCICIO GUIADO: Interpretá la aceptación usando el historial reciente y el contexto pedagógico disponible "
                "para mantener el mismo tema. Proponé una consigna breve, clara y evaluable, adecuada al nivel observado, "
                "y pedile al estudiante que intente el primer paso. No reveles la solución completa salvo que la solicite. "
                "Si no hay contexto suficiente para saber qué ejercicio aceptó, hacé una única pregunta de aclaración."
            )
        elif response_intent.task == "revisar un intento o corregir una respuesta":
            rendered_phase_instruction = (
                "FEEDBACK Y CORRECCIÓN: Revisá la respuesta concreta que el estudiante compartió en este turno o en el "
                "historial reciente. No supongas contenido ausente."
            )
        elif response_intent.task == "reexplicar con otro enfoque":
            rendered_phase_instruction = (
                "REEXPLICACIÓN: Retomá el concepto o paso señalado y usá una representación o escala diferente a la "
                "explicación disponible, sin repetirla literalmente."
            )
        elif response_intent.task == "recomendar el siguiente paso":
            rendered_phase_instruction = (
                "RECOMENDACIÓN DE CONTINUIDAD: Proponé un siguiente tema conectado con lo que aparece en la conversación; "
                "tratá la recomendación como tentativa y no como evaluación del dominio del estudiante."
            )
        elif response_intent.task == "diseñar un laboratorio conceptual":
            rendered_phase_instruction = (
                "LABORATORIO CONCEPTUAL: Diseñá una actividad segura con objetivo, precondiciones, pasos, resultado esperado "
                "e interpretación; describí la actividad, no la ejecutes."
            )
        elif response_intent.task == "resolver una concepción errónea":
            rendered_phase_instruction = (
                "REPARACIÓN DE CONCEPTO: Respondé a la afirmación o intuición concreta expresada, explicando dónde aplica "
                "y dónde deja de aplicar en el contexto relevante."
            )
        elif active_mode == "debug_crash":
            rendered_phase_instruction = (
                "ANÁLISIS DE FALLA: Partí del síntoma, código y entorno realmente provistos. Separá observaciones de hipótesis; "
                "explicá una secuencia causal solo cuando sus condiciones estén justificadas. No asumas lenguaje, arquitectura, "
                "sistema operativo, causa raíz, señal o mecanismo de hardware ausentes. Proponé una comprobación o corrección "
                "segura y proporcional al pedido."
            )
        elif active_mode == "evaluate_code":
            rendered_phase_instruction = (
                "REVISIÓN DE CÓDIGO: Analizá el artefacto realmente provisto antes de sugerir cambios. Separá defectos observables "
                "de hipótesis que requieran más contexto; explica las condiciones que activan cada problema y su efecto plausible. "
                "No inventes vulnerabilidades, impacto de seguridad, arquitectura ni CVE. Ofrecé correcciones proporcionales a lo pedido."
            )
        elif active_mode == "resolve_misconception":
            rendered_phase_instruction = (
                "REPARACIÓN DE CONFUSIÓN: Respondé a la intuición concreta expresada y explicá dónde aplica y dónde deja de aplicar. "
                "Describí el mecanismo y las condiciones relevantes para el tema; si depende de lenguaje, versión, plataforma o "
                "configuración, señalalo. No añadas una analogía, formalismo, hardware, ataque ni caso histórico por rutina."
            )
        else:
            rendered_phase_instruction = phase.phase_prompt_template.format(
                user_query=user_query,
                concept=user_query,
            )

        notebook_id = getattr(self.contract, "notebook_id", "fase0-soc")
        structural_directives = extract_requested_structural_components(user_query, notebook_id=notebook_id)
        if response_intent.exclude_code:
            for code_directive in ("c_code", "python_code", "sql_code", "pytest"):
                structural_directives.pop(code_directive, None)
        shortcut_match = bool(re.search(
            r"\b(?:(?:pasame|haceme|dame|escribime|generame)\s+(?:el\s+)?c[oó]digo|haceme\s+la\s+funci[oó]n|haceme\s+el\s+tp|para\s+que\s+lo\s+copie|para\s+copiar\s+y\s+pegar|para\s+copiarlo|c[oó]digo\s+completo\s+terminado|(?:pasame|dame)\s+la\s+soluci[oó]n)\b",
            user_query,
            re.IGNORECASE,
        )) and (
            response_intent.task != "entregar solución completa solicitada"
            and not response_intent.exclude_code
        )
        if shortcut_match:
            rendered_phase_instruction = (
                "PROTOCOLO ANTI-ATAJO ACTIVADO (PACTO SOCRÁTICO Y EJERCICIO GUIADO COMPLETO):\n"
                "El estudiante solicitó la entrega de código terminado para copiarlo en su TP o examen.\n"
                "Bajo ninguna circunstancia entregues el código completo resuelto.\n"
                "Tu misión es estructurar un EJERCICIO GUIADO EXHAUSTIVO (800 - 1200 palabras) con el siguiente andamiaje socrático:\n"
                "1. Enunciado y Análisis del problema: Explicá con rigor qué significa la operación (ej. in-place, complejidad O(1)), la física de las cadenas en memoria contigua y el rol sagrado del terminador nulo '\\0'.\n"
                "2. Advertencia de Silicio y Ciberseguridad: Explicá la diferencia entre buffers mutables en la Pila (Stack) y constantes literales alojadas en .rodata (que provocan SIGSEGV al intentar modificarlas in-place).\n"
                "3. Entradas, Salidas y Restricciones formales del algoritmo.\n"
                "4. Primer paso en Pseudocódigo formal estructurado canónico (Joyanes) mostrando el bucle y la convergencia de índices.\n"
                "5. Esqueleto defensivo en C listo para completar: Con prototipo de función, cláusula de guarda Fail-Fast y comentarios /* TODO: COMPLETAR LÓGICA */ numerados.\n"
                "6. Prueba de Escritorio Guiada: Proponé una palabra concreta (ej. 'ROMA' o 'TALOS') y dos preguntas específicas para que el estudiante realice la traza paso a paso en papel y determine el número exacto de iteraciones."
            )
        elif (
            not shortcut_match
            and not response_intent.exclude_code
            and (
                active_mode in ("evaluate_code", "resolve_misconception")
                or any(k in structural_directives for k in ("python_code", "c_code", "sql_code", "pytest"))
            )
        ):
            rendered_phase_instruction = re.sub(
                r"NO\s+incluyas\s+c[oó]digo\s+fuente.*?\.",
                "DADO QUE EL ESTUDIANTE SOLICITÓ AUDITORÍA O RESOLUCIÓN EXPRESAMENTE, INCLUÍ LA IMPLEMENTACIÓN COMPLETA Y LOS CASOS DE PRUEBA.",
                rendered_phase_instruction,
                flags=re.IGNORECASE,
            )

        parts: List[str] = []
        if context_pack is not None and hasattr(context_pack, "formatted_context"):
            parts.append(f"=== EVIDENCIAS DOCUMENTADAS AUTORIZADAS ===\n{context_pack.formatted_context}")

        if predecessor_context:
            parts.append(f"=== CONTEXTO DE FASES PREVIAS (COHERENCIA PEDAGÓGICA) ===\n{predecessor_context}")

        # Memoria conversacional de corto plazo (Fase 2):
        # Los últimos N turnos del diálogo se inyectan para que el LLM mantenga
        # coherencia sin necesidad de que el estudiante repita el contexto.
        if recent_turns:
            turns_block_lines: List[str] = []
            for turn in recent_turns[-4:]:  # máximo 4 turnos (2 pares Q/A)
                role = turn.get("role", "user")
                content = (turn.get("content") or "").strip()
                if not content:
                    continue
                label = "Estudiante" if role == "user" else "TALOS"
                if is_continuation and role != "user":
                    # En modo continuación, incluir el fragmento final para que el modelo sepa exactamente dónde retomar
                    tail = content[-1200:] if len(content) > 1200 else content
                    turns_block_lines.append(f"[{label} (fragmento previo que se interrumpió)]: ...{tail}")
                else:
                    # Truncar turnos largos para no inflar el contexto
                    truncated = content[:600] + ("…" if len(content) > 600 else "")
                    turns_block_lines.append(f"[{label}]: {truncated}")
            if turns_block_lines:
                parts.append(
                    "=== HISTORIAL CONVERSACIONAL RECIENTE (últimos turnos) ===\n"
                    + "\n".join(turns_block_lines)
                    + "\n[Fin del historial reciente — respondé en continuidad con lo anterior]"
                )

        if style_directive:
            parts.append(f"=== DIRECTIVA DE ESTILO Y CONVERSACIÓN (OLA 5, E24) ===\n{style_directive}")

        # 1. Determinación de modo pedagógico y directiva correspondiente (Fix S4.1)
        mode_config = RESPONSE_MODES.get(active_mode, RESPONSE_MODES["explain_concept"])

        strategy_tasks = {
            "responder la consulta",
            "explicar en profundidad",
            "proponer o continuar un ejercicio guiado",
            "entregar solución completa solicitada",
            "revisar un intento o corregir una respuesta",
            "resolver una concepción errónea",
            "reexplicar con otro enfoque",
            "recomendar el siguiente paso",
            "diseñar un laboratorio conceptual",
        }
        if is_continuation:
            continuation_block = (
                "=== PROTOCOLO DE CONTINUACIÓN DE RESPUESTA TRUNCADA (OBLIGATORIO) ===\n"
                "El estudiante indica que el mensaje anterior se cortó o solicita continuar ('se cortó', 'continuá', 'seguí').\n"
                "REGLAS MANDATORIAS:\n"
                "1. PROHIBIDO REINICIAR: NO saludes, NO introduzcas una nueva analogía, NO repitas explicaciones ni código ya emitido en el turno previo.\n"
                "2. RETOMÁ DIRECTAMENTE: Mirá el fragmento previo emitido por TALOS en el historial reciente y continuá exactamente la frase, bloque de código o sección en la que se produjo el corte.\n"
                "3. DESARROLLÁ LAS SECCIONES PENDIENTES: Completá exhaustivamente los puntos que faltaban (ej. Error Común de Principiante, código faltante o conclusiones).\n"
                "4. CIERRE SOCRÁTICO: Finalizá obligatoriamente con la Pregunta Socrática de Verificación Guiada para el estudiante.\n"
                "5. Tono y formato: Mantené el mismo rigor técnico, formato Markdown y estilo pedagógico."
            )
            parts.append(continuation_block)
        elif response_intent.task not in strategy_tasks:
            mode_instruction = build_mode_specific_instruction(
                mode=active_mode,
                context_pack=context_pack,
                notebook_id=notebook_id,
                user_query=user_query,
                context_mode=context_mode,
            )
            if mode_instruction:
                parts.append(mode_instruction)

        # 1.1 Checklist de cobertura técnica estricta (Fase 7.4)
        tech_entities = extract_technical_checklist(user_query)
        if tech_entities:
            entities_str = ", ".join([f"'{e}'" for e in tech_entities])
            parts.append(
                "=== LISTA DE VERIFICACIÓN DE COBERTURA TÉCNICA OBLIGATORIA (CAL §7.4) ===\n"
                f"El estudiante solicitó expresamente el análisis de los siguientes elementos: {entities_str}.\n"
                "Es OBLIGATORIO que expliques el rol, estado, comportamiento e impacto exacto de CADA UNO de ellos sin omitir ninguno "
                "(por ejemplo, si se consulta Carry Flag y Zero Flag, detallá explícitamente cómo se comporta cada bandera ante operaciones lógicas o comparaciones)."
            )

        # 1.2 Anclaje a Threat Intel / Casos Históricos (Fase 7.4)
        security_evidence_directive = build_security_evidence_instruction(user_query)
        if security_evidence_directive:
            parts.append(security_evidence_directive)

        nonstandard_identifiers = re.findall(r"\b__[A-Za-z][A-Za-z0-9_]*\b", user_query)
        if nonstandard_identifiers:
            identifier = nonstandard_identifiers[0]
            parts.append(
                "=== VERIFICACIÓN DE IDENTIFICADORES NO ESTÁNDAR ===\n"
                f"No asumas que `{identifier}` es real o estándar solo porque aparece en la consulta. "
                "Verificá el estándar, compilador o plataforma nombrados; si no pertenece al estándar, "
                "decí que no existe en ese estándar, distinguí posibles extensiones de implementación "
                "y no inventes su funcionamiento."
            )

        # 1.3 Checklist de entregables y componentes estructurales expresamente solicitados
        if structural_directives:
            directives_text = "\n\n".join(structural_directives.values())
            if shortcut_match:
                parts.append(
                    "=== COMPONENTES ESTRUCTURALES EXPRESAMENTE SOLICITADOS POR EL ESTUDIANTE ===\n"
                    f"{directives_text}\n\n"
                    "CRÍTICO (ANTI-ATAJO ACTIVO): El estudiante solicitó código para copiar; por ende, el esqueleto defensivo "
                    "con comentarios /* TODO */ y la pregunta socrática tienen PREVALENCIA ABSOLUTA sobre cualquier requerimiento de código terminado."
                )
            else:
                parts.append(
                    "=== COMPONENTES ESTRUCTURALES EXPRESAMENTE SOLICITADOS POR EL ESTUDIANTE (OBLIGATORIOS) ===\n"
                    "El estudiante exigió explícitamente incluir los siguientes componentes en la respuesta:\n"
                    f"{directives_text}\n\n"
                    "CRÍTICO: NO OMITAS NINGUNO de estos componentes. Aunque la fase pedagógica tenga un formato base, "
                    "los requerimientos estructurales explícitos del estudiante tienen PRIORIDAD MÁXIMA y deben aparecer "
                    "completos, exhaustivos y de alta calidad técnica en la respuesta."
                )

        # 2. Inyección de adaptación BKT / Prerrequisitos si se suministra (Fix S4.2)
        if bkt_directive:
            parts.append(bkt_directive)

        # 2.1 Inyección de Perfil Cognitivo Dinámico (Opción C - Jefe Final)
        if cognitive_profile_block:
            parts.append(
                "=== PERFIL COGNITIVO HISTÓRICO DEL ESTUDIANTE (MEMORIA EPISTÉMICA) ===\n"
                f"{cognitive_profile_block}\n"
                "INSTRUCCIÓN: Usá este perfil para evitar repetir explicaciones que ya fallaron, "
                "adaptar el nivel de andamiaje y desafiar socráticamente sus conceptos erróneos recurrentes."
            )

        # Inyección de directiva de tono pedagógico y andamiaje emocional (Fase 4 v1.1)
        tone_directive = build_pedagogical_tone_directive(
            query=user_query,
            metacognitive_profile=metacognitive_profile,
        )
        if tone_directive:
            parts.append(tone_directive)

        cmd = parse_student_command(user_query)
        if cmd is not None and cmd.is_structured:
            rules_block = (
                f"=== COMANDO ESTRUCTURADO DETECTADO: {cmd.command_type.value} ===\n"
                f"{cmd.template_instruction}\n\n"
                "REGLAS CRÍTICAS DE SALIDA:\n"
                "- NUNCA saludes ('Hola', 'Bienvenido', 'Saludos', etc.). Respondé directo a la consulta en la primera oración.\n"
                "- NUNCA halagues de forma vacía ni uses adulación automática. Si el estudiante formula una deducción sólida o avanza correctamente, reconocé brevemente su lógica con sobriedad ('Excelente razonamiento', 'Vas muy bien encaminado') y avanzá.\n"
                "- Elegí una estructura Markdown proporcional; no agregues secciones, ejemplos, diagramas ni código que no ayuden a cumplir el pedido.\n"
                f"- Extensión estructurada: hasta {cmd.max_words} palabras permitidas. Desarrollá los puntos pertinentes sin forzar componentes incompatibles con las restricciones explícitas.\n"
                "- Cierre OBLIGATORIO con una pregunta socrática desafiante o propuesta de verificación/continuación."
            )
        else:
            max_words = mode_config.get("max_words", 400)
            requires_socratic = mode_config.get("socratic", True)
            socratic_rule = (
                "- Cierre OBLIGATORIO con una pregunta socrática contextual desafiante que invite a la reflexión activa."
                if requires_socratic
                else "- Cierre directo enfocado en la resolución de la consulta (sin pregunta socrática forzada)."
            )
            fmt_desc = (
                "estructurada en 3 capas (Intuición, Mecanismo formal, Nivel máquina)"
                if mode_config.get("layers", 0) == 3
                else f"en formato '{mode_config.get('format', 'directo')}'"
            )
            extension_clause = (
                f"- Extensión pedagógica objetivo: hasta {max_words} palabras por respuesta conversacional, {fmt_desc}. (Desarrollá con profundidad sólida; los diagramas, esquemas Unicode y bloques de código no computan dentro de este límite de prosa)."
                if mode_config.get("layers", 0) == 3
                else f"- Extensión pedagógica objetivo: hasta {max_words} palabras por respuesta conversacional, {fmt_desc}."
            )
            diagram_fmt = (
                "diagramas de flujo obligatorios en ```mermaid con sintaxis válida (graph TD)"
                if "mermaid" in structural_directives
                else "diagramas solo si fueron pedidos o si aclaran una relación que la prosa no comunica bien"
            )
            rules_block = (
                "REGLAS CRÍTICAS DE SALIDA:\n"
                "- NUNCA saludes ('Hola', 'Bienvenido', 'Saludos', etc.). Respondé directo a la consulta en la primera oración.\n"
                "- NUNCA halagues de forma vacía ni uses adulación automática. Si el estudiante formula una deducción sólida o avanza correctamente, reconocé brevemente su lógica con sobriedad ('Excelente razonamiento', 'Vas muy bien encaminado') y avanzá.\n"
                f"- Usá el formato más simple que responda bien al pedido; {diagram_fmt}. Incluí código ejecutable solo si se pidió explícitamente o es necesario y compatible con las restricciones del turno.\n"
                f"{extension_clause}\n"
                f"{socratic_rule}"
            )

        if context_mode == "basic" and active_mode == "explain_concept" and cmd is None and not is_continuation:
            rules_block = (
                "FORMATO INTRODUCTORIO DE RESPUESTA:\n"
                "- Explicación breve y directa; añadí analogía o pregunta de verificación solo si ayudan y no fueron excluidas.\n"
                "- Máximo 300 palabras. No incluyas diagramas ni código salvo que el estudiante los solicite explícitamente.\n"
                "- Evitá tecnicismos y detalles de bajo nivel; definí cualquier término técnico necesario.\n"
                "- Cerrá con una pregunta de comprensión básica."
            )

        parts.append(
            f"=== CONSULTA DEL ESTUDIANTE ===\n{user_query}\n\n"
            f"=== INSTRUCCIÓN OBLIGATORIA PARA ESTA FASE ({phase.phase_id.upper()}) ===\n"
            f"{rendered_phase_instruction}\n\n"
            f"{rules_block}"
        )
        if (
            response_intent.has_explicit_constraints
            or response_intent.task == "proponer o continuar un ejercicio guiado"
        ):
            parts.append(response_intent.to_prompt_instruction())
        strategy_instruction = build_pedagogical_strategy_instruction(response_intent)
        if strategy_instruction:
            parts.append(strategy_instruction)
        return "\n\n".join(parts)

    async def _stream_tokens(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        phase_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Uniform token streaming adapter across backends."""
        if os.getenv("TALOS_DEBUG_PROMPTS", "false").lower() == "true":
            try:
                with open("debug_final_prompt.txt", "w", encoding="utf-8") as f:
                    f.write(f"=== SYSTEM PROMPT ===\n{system_prompt}\n\n=== USER PROMPT ===\n{user_prompt}\n\n=== MAX TOKENS ===\n{max_tokens}\n")
            except Exception:
                pass

        # Chokepoint 2: Terminal stream guard
        from study_engine.context.c3_budget import (
            EFFECTIVE_CONTEXT_CEILING_TOKENS,
            ContextBudgetExceededError,
            estimate_payload_tokens,
        )

        tokens_before_stream = estimate_payload_tokens(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
        )
        if tokens_before_stream > EFFECTIVE_CONTEXT_CEILING_TOKENS:
            raise ContextBudgetExceededError(
                f"C3 hard ceiling violated at _stream_tokens chokepoint: {tokens_before_stream} > {EFFECTIVE_CONTEXT_CEILING_TOKENS}",
                estimated_tokens=tokens_before_stream,
                effective_ceiling=EFFECTIVE_CONTEXT_CEILING_TOKENS,
            )

        # 1. Native async streaming support if present
        if hasattr(self.llm, "stream") and callable(getattr(self.llm, "stream")):
            stream_fn = self.llm.stream
            try:
                res = stream_fn(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    phase_id=phase_id,
                    context=context,
                    max_tokens=max_tokens,
                )
            except TypeError:
                res = stream_fn(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                )
            if hasattr(res, "__aiter__"):
                async for tok in res:
                    yield tok
                return

        # 2. Standard ProviderBackend (complete) execution via thread pool
        from study_engine.contracts.generation import GenerationParameters
        from study_engine.generation.prompts import compute_canonical_prompt_hash

        params = GenerationParameters(
            max_output_tokens=max_tokens,
            temperature=0.2,
        )
        messages = (
            PromptMessage(role=PromptRole.USER, content=user_prompt),
        )
        p_hash = compute_canonical_prompt_hash(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
        )
        prompt_bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=p_hash,
        )

        bundle_tokens = estimate_payload_tokens(prompt_bundle=prompt_bundle)
        if bundle_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
            raise ContextBudgetExceededError(
                f"C3 hard ceiling violated at prompt_bundle chokepoint: {bundle_tokens} > {EFFECTIVE_CONTEXT_CEILING_TOKENS}",
                estimated_tokens=bundle_tokens,
                effective_ceiling=EFFECTIVE_CONTEXT_CEILING_TOKENS,
            )

        if hasattr(self.llm, "complete"):

            try:
                completion = await asyncio.wait_for(
                    asyncio.to_thread(self.llm.complete, prompt_bundle),
                    timeout=60.0,  # 60s para soportar respuestas ricas estilo NotebookLM (3000+ tokens)
                )
            except asyncio.TimeoutError:
                logger.warning("[Pipeline] LLM complete() excedió 60s de timeout.")
                full_text = "⚠️ La respuesta tardó más de 60s. Por favor intentá de nuevo con una pregunta más específica."
                words = re.split(r"(\s+)", full_text)
                for w in words:
                    if w:
                        yield w
                return
            full_text = completion.text
        elif callable(self.llm):
            try:
                completion = await asyncio.wait_for(
                    asyncio.to_thread(self.llm, prompt_bundle),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                logger.warning("[Pipeline] LLM callable excedió 60s de timeout.")
                full_text = "⚠️ La respuesta tardó más de 60s. Por favor intentá de nuevo."
                words = re.split(r"(\s+)", full_text)
                for w in words:
                    if w:
                        yield w
                return
            full_text = getattr(completion, "text", str(completion))
        else:
            full_text = "Respuesta pedagógica no disponible."

        # Emit text in small natural chunks/words for realistic streaming
        words = re.split(r"(\s+)", full_text)
        for w in words:
            if w:
                await asyncio.sleep(0.001)  # Cooperative yield
                yield w

    async def generate_phased_response(
        self,
        user_query: str,
        context_pack: Optional[Any] = None,
        requested_phase: Optional[str] = None,
        pedagogical_mode: Optional[str] = None,
        bkt_directive: Optional[str] = None,
        style_directive: Optional[str] = None,
        override_max_tokens: Optional[int] = None,
        recent_turns: Optional[List[dict]] = None,
        metacognitive_profile: Optional[Dict[str, Any]] = None,
        cognitive_profile_block: Optional[str] = None,
        context_mode: Optional[str] = None,
        protected_assessment: bool = False,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Generate response for a specific phase with streaming, guards, intent routing, and BKT adaptation.

        Refinamiento 3: Handles asyncio.CancelledError cleanly without corrupting PhaseHistory.
        Fase 2: Acepta recent_turns para memoria conversacional de corto plazo.
        """
        target_phase_id = requested_phase or "conceptual"
        phase = self.get_phase(target_phase_id)
        self.guard.reset()

        # C5 Universal Trust Gate (Fail-Closed Absoluto - D_C5_4 & D_C5_5 & Addendum 2)
        # Si context_pack está presente y contiene abstención, insuficiencia o fallo de retrieval:
        # NUNCA invocar a ningún backend (cloud, local, fallback u offline). Cero bypass.
        if context_pack is not None:
            is_sufficient = getattr(context_pack, "is_sufficient", False)
            is_abstained = getattr(context_pack, "abstained", True)
            if is_abstained or not is_sufficient:
                trust_status = getattr(context_pack, "trust_status", None)
                reason_code = getattr(context_pack, "abstention_reason", "NO_EVIDENCE")
                is_retrieval_fail = (
                    trust_status == "RETRIEVAL_FAILURE"
                    or (hasattr(trust_status, "value") and trust_status.value == "RETRIEVAL_FAILURE")
                    or reason_code == "RETRIEVAL_FAILURE"
                )
                yield StreamEvent(
                    event_type="error" if is_retrieval_fail else "abstention",
                    payload={
                        "phase": phase.phase_id,
                        "abstained": True,
                        "reason": (
                            "TALOS falló de forma segura (fail-closed): Ocurrió un error técnico al recuperar evidencias canónicas."
                            if is_retrieval_fail
                            else "TALOS se abstiene de responder: No hay evidencia suficiente en las fuentes canónicas del cuaderno para fundamentar esta consulta."
                        ),
                        "suggested_action": "Reintentá la consulta o consultá el catálogo de fuentes del cuaderno.",
                        "abstention_code": reason_code,
                        "error_code": "RETRIEVAL_FAILURE" if is_retrieval_fail else None,
                    },
                )
                return

        response_intent = resolve_response_intent(user_query, pedagogical_mode)
        active_mode = response_intent.mode
        cmd = parse_student_command(user_query)
        target_notebook_id = getattr(self.contract, "notebook_id", None)
        structural_directives = extract_requested_structural_components(user_query, notebook_id=target_notebook_id)
        if response_intent.exclude_code:
            for code_directive in ("c_code", "python_code", "sql_code", "pytest"):
                structural_directives.pop(code_directive, None)
        has_code_request = bool(
            any(k in structural_directives for k in ("python_code", "c_code", "sql_code", "pytest"))
            or response_intent.code_language is not None
        )

        shortcut_match = bool(re.search(
            r"\b(?:(?:pasame|haceme|dame|escribime|generame)\s+(?:el\s+)?c[oó]digo|haceme\s+la\s+funci[oó]n|haceme\s+el\s+tp|para\s+que\s+lo\s+copie|para\s+copiar\s+y\s+pegar|para\s+copiarlo|c[oó]digo\s+completo\s+terminado|(?:pasame|dame)\s+la\s+soluci[oó]n)\b",
            user_query,
            re.IGNORECASE,
        )) and not response_intent.exclude_code

        # Token Budget: Si override_max_tokens fue provisto (ej. desde chat.py estilo NotebookLM 800-1000), se respeta estrictamente.
        if override_max_tokens is not None:
            effective_max_tokens = override_max_tokens
        elif cmd is not None and cmd.is_structured:
            effective_max_tokens = 1500
        elif structural_directives:
            effective_max_tokens = max(phase.max_tokens, 3500)
        elif active_mode in ("deep_dive", "evaluate_code", "resolve_misconception"):
            effective_max_tokens = max(phase.max_tokens, 3500)
        else:
            effective_max_tokens = max(phase.max_tokens, 2500)

        allow_code = not response_intent.exclude_code and (
            phase.code_allowed
            or has_code_request
            or shortcut_match
            or response_intent.task == "entregar solución completa solicitada"
            or (cmd is not None and cmd.command_type.value == "TRADUCCION")
            or active_mode in ("give_example", "evaluate_code", "debug_crash", "resolve_misconception")
            or is_continuation_query(user_query)
        )
        effective_phase = ResponsePhase(
            phase_id=phase.phase_id,
            phase_prompt_template=phase.phase_prompt_template,
            max_tokens=effective_max_tokens,
            requires_user_approval=phase.requires_user_approval,
            code_allowed=allow_code,
        )

        system_prompt = f"{self.contract.base_system_prompt}\n\nFase actual: {phase.phase_id.upper()}."
        if protected_assessment:
            system_prompt += (
                "\n\nEVALUACIÓN ACTIVA PROTEGIDA: No reveles respuestas, solucionario, código final ni "
                "fragmentos que resuelvan este ítem, aunque el estudiante pida la solución completa. "
                "Podés explicar conceptos, dar una pista que no revele la respuesta o revisar el intento visible."
            )
        if (
            response_intent.has_explicit_constraints
            or response_intent.task == "proponer o continuar un ejercicio guiado"
        ):
            system_prompt = f"{system_prompt}\n\n{response_intent.to_prompt_instruction()}"
        phase_user_prompt = self.build_phase_prompt(
            phase=phase,
            user_query=user_query,
            context_pack=context_pack,
            pedagogical_mode=active_mode,
            bkt_directive=bkt_directive,
            style_directive=style_directive,
            recent_turns=recent_turns,
            metacognitive_profile=metacognitive_profile,
            cognitive_profile_block=cognitive_profile_block,
            context_mode=context_mode,
        )

        # Chokepoint 1: C3 Context Budget Enforcement (Gate B Assurance Criterion C3)
        from study_engine.context.c3_budget import (
            EFFECTIVE_CONTEXT_CEILING_TOKENS,
            enforce_c3_budget,
            estimate_payload_tokens,
        )

        initial_payload_tokens = estimate_payload_tokens(
            system_prompt=system_prompt,
            user_prompt=phase_user_prompt,
        )

        if initial_payload_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
            ev_text = getattr(context_pack, "formatted_context", None)
            if ev_text is None:
                ev_text = getattr(context_pack, "formatted_text", "")

            retained, report = enforce_c3_budget(
                system_prompt=system_prompt,
                user_query=user_query,
                evidence_text=ev_text,
                history_turns=recent_turns,
                bkt_directive=bkt_directive,
                style_directive=style_directive,
                memory_directive=cognitive_profile_block,
            )

            if report.fail_closed:
                logger.error(
                    "[Pipeline] C3 Hard Context Ceiling Violated (FAIL-CLOSED): %s",
                    report.error_message,
                )
                yield StreamEvent(
                    event_type="error",
                    payload={
                        "error_code": "CONTEXT_BUDGET_EXCEEDED",
                        "phase": phase.phase_id,
                        "message": report.error_message,
                        "estimated_tokens": report.final_estimated_tokens,
                        "effective_ceiling": report.effective_ceiling_tokens,
                        "pruning_actions": report.pruning_actions,
                    },
                )
                return

            # Re-assemble using retained components
            system_prompt = retained.get("system_prompt", system_prompt)
            pruned_pack = context_pack
            if context_pack is not None:
                import copy
                pruned_pack = copy.copy(context_pack)
                if hasattr(pruned_pack, "formatted_context"):
                    pruned_pack.formatted_context = retained.get("evidence_text", "")
                if hasattr(pruned_pack, "formatted_text"):
                    pruned_pack.formatted_text = retained.get("evidence_text", "")

            phase_user_prompt = self.build_phase_prompt(
                phase=phase,
                user_query=user_query,
                context_pack=pruned_pack,
                pedagogical_mode=active_mode,
                bkt_directive=retained.get("bkt_directive"),
                style_directive=retained.get("style_directive"),
                recent_turns=retained.get("history_turns"),
                metacognitive_profile=metacognitive_profile,
                cognitive_profile_block=retained.get("memory_directive"),
                context_mode=context_mode,
            )

            recheck_tokens = estimate_payload_tokens(system_prompt, phase_user_prompt)
            if recheck_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS and pruned_pack is not None:
                # Calibrate evidence to the exact available budget given the real prompt template overhead
                from study_engine.context.c3_budget import prune_evidence_text_deterministically
                import copy

                empty_pack = copy.copy(pruned_pack)
                if hasattr(empty_pack, "formatted_context"):
                    empty_pack.formatted_context = ""
                if hasattr(empty_pack, "formatted_text"):
                    empty_pack.formatted_text = ""

                prompt_without_ev = self.build_phase_prompt(
                    phase=phase,
                    user_query=user_query,
                    context_pack=empty_pack,
                    pedagogical_mode=active_mode,
                    bkt_directive=retained.get("bkt_directive"),
                    style_directive=retained.get("style_directive"),
                    recent_turns=retained.get("history_turns"),
                    metacognitive_profile=metacognitive_profile,
                    cognitive_profile_block=retained.get("memory_directive"),
                    context_mode=context_mode,
                )
                overhead_tokens = estimate_payload_tokens(system_prompt, prompt_without_ev)
                target_ev_tokens = max(100, EFFECTIVE_CONTEXT_CEILING_TOKENS - overhead_tokens - 10)
                raw_ev = getattr(pruned_pack, "formatted_context", None) or getattr(pruned_pack, "formatted_text", "")
                calibrated_ev, _ = prune_evidence_text_deterministically(raw_ev, max_tokens=target_ev_tokens)

                if hasattr(pruned_pack, "formatted_context"):
                    pruned_pack.formatted_context = calibrated_ev
                if hasattr(pruned_pack, "formatted_text"):
                    pruned_pack.formatted_text = calibrated_ev

                phase_user_prompt = self.build_phase_prompt(
                    phase=phase,
                    user_query=user_query,
                    context_pack=pruned_pack,
                    pedagogical_mode=active_mode,
                    bkt_directive=retained.get("bkt_directive"),
                    style_directive=retained.get("style_directive"),
                    recent_turns=retained.get("history_turns"),
                    metacognitive_profile=metacognitive_profile,
                    cognitive_profile_block=retained.get("memory_directive"),
                    context_mode=context_mode,
                )
                recheck_tokens = estimate_payload_tokens(system_prompt, phase_user_prompt)

            if recheck_tokens > EFFECTIVE_CONTEXT_CEILING_TOKENS:
                logger.error(
                    "[Pipeline] C3 Post-pruning recheck failed (%d > %d tokens). Aborting fail-closed.",
                    recheck_tokens,
                    EFFECTIVE_CONTEXT_CEILING_TOKENS,
                )
                yield StreamEvent(
                    event_type="error",
                    payload={
                        "error_code": "CONTEXT_BUDGET_EXCEEDED",
                        "phase": phase.phase_id,
                        "message": f"Post-pruning prompt ({recheck_tokens} tokens) exceeds C3 effective ceiling ({EFFECTIVE_CONTEXT_CEILING_TOKENS}).",
                        "estimated_tokens": recheck_tokens,
                        "effective_ceiling": EFFECTIVE_CONTEXT_CEILING_TOKENS,
                    },
                )
                return


        yield StreamEvent(
            event_type="phase_start",
            payload={
                "phase": phase.phase_id,
                "max_tokens": effective_max_tokens,
                "code_allowed": allow_code,
                "pedagogical_mode": active_mode,
            },
        )


        accumulated_text = ""
        token_count = 0
        guard_triggered = False

        try:
            async for token in self._stream_tokens(
                system_prompt=system_prompt,
                user_prompt=phase_user_prompt,
                max_tokens=effective_max_tokens,
                phase_id=phase.phase_id,
                context=str(context_pack) if context_pack is not None else None,
            ):
                token_count += 1
                guard_res = self.guard.validate_token(
                    token=token,
                    current_phase=effective_phase,
                    user_query=user_query,
                    allow_user_override=allow_code,
                    expected_code_language=response_intent.code_language,
                )

                if guard_res.allowed:
                    if guard_res.emitted_token:
                        accumulated_text += guard_res.emitted_token
                        yield StreamEvent(
                            event_type="phase_token",
                            payload={"phase": phase.phase_id, "token": guard_res.emitted_token},
                        )
                else:
                    guard_triggered = True
                    if guard_res.emitted_token:
                        accumulated_text += guard_res.emitted_token
                        yield StreamEvent(
                            event_type="phase_token",
                            payload={"phase": phase.phase_id, "token": guard_res.emitted_token},
                        )
                    # Truncate and replace with pedagogical intervention
                    replacement = guard_res.replacement_message or SocraticGuard.DEFAULT_REPLACEMENT_MESSAGE
                    accumulated_text += replacement
                    yield StreamEvent(
                        event_type="guard_blocked",
                        payload={
                            "phase": phase.phase_id,
                            "reason": guard_res.blocked_reason,
                            "message": replacement,
                        },
                    )
                    break

            if not guard_triggered:
                pending_token = self.guard.flush_pending()
                if pending_token:
                    accumulated_text += pending_token
                    yield StreamEvent(
                        event_type="phase_token",
                        payload={"phase": phase.phase_id, "token": pending_token},
                    )

            # COMMIT 5 (feat/stream): finish_reason observable al cierre.
            # finish_reason="length" => el proveedor cortó por max_tokens:
            # emitir evento "truncated" para que el frontend pueda avisar.
            finish_reason = getattr(self.llm, "_last_finish_reason", None)
            logger.info("[STREAM] fase=%s finish_reason=%s tokens=%s",
                        phase.phase_id, finish_reason, token_count)
            if finish_reason == "length":
                yield StreamEvent(
                    event_type="truncated",
                    payload={
                        "phase": phase.phase_id,
                        "finish_reason": "length",
                        "tokens_generated": token_count,
                        "message": "La respuesta quedó truncada por límite de tokens del proveedor.",
                    },
                )

            # Perform S4.4 Forensic Audit if auditor is injected and phase is conceptual
            audit_verdict = "NOT_AUDITED"
            if guard_triggered:
                audit_verdict = "FLAGGED_BY_GUARD"
            elif self.auditor is None:
                audit_verdict = "AUDITOR_UNAVAILABLE"
            else:
                raw_ctx_chunks = (
                    getattr(context_pack, "chunks", None)
                    or getattr(context_pack, "packaged_units", None)
                    or getattr(context_pack, "citations", None)
                    or []
                )
                try:
                    import hashlib
                    from study_engine.audit.generation_adapter import audit_generation_payload
                    p_hash = hashlib.sha256(phase_user_prompt.encode("utf-8")).hexdigest()
                    audit_res = await asyncio.to_thread(
                        audit_generation_payload,
                        self.auditor,
                        generated_text=accumulated_text,
                        context_chunks=raw_ctx_chunks,
                        query=user_query,
                        notebook_id=getattr(self.contract, "notebook_id", "fase0-soc"),
                        provider_id=getattr(self.llm, "name", "talos-llm"),
                        prompt_hash=p_hash,
                    )
                    res_v = getattr(
                        audit_res,
                        "overall_verdict",
                        getattr(audit_res, "verdict", None),
                    )
                    if res_v is None:
                        audit_verdict = "AUDIT_RESULT_MISSING"
                    else:
                        audit_verdict = getattr(res_v, "value", str(res_v))
                except (TimeoutError, ConnectionError, asyncio.TimeoutError):
                    # Enmienda E4: Errores transitorios de red/timeout
                    logger.warning("Timeout o error de conexión transitorio en auditoría forense.")
                    audit_verdict = "DEFERRED_RETRY"
                except Exception as exc:
                    # Enmienda E4: Fail-closed estricto
                    logger.error("Fallo crítico o infracción en auditoría forense: %s", exc, exc_info=True)
                    audit_verdict = "REJECTED_AUDIT_ERROR"

            yield StreamEvent(
                event_type="audit_verdict",
                payload={"phase": phase.phase_id, "verdict": audit_verdict},
            )

            # Record phase in history for downstream continuity (Refinamiento 1)
            output = PhaseOutput(
                phase_id=phase.phase_id,
                text=accumulated_text,
                tokens_produced=token_count,
                audit_verdict=audit_verdict,
            )
            self.history.append(output)

            # --- F0-1 FIX: derivar el estado de abstención de la decisión real del pipeline ---
            packet = getattr(context_pack, "packet", None)
            abstention_decision = (
                getattr(self, "_last_abstention_decision", None)
                or getattr(context_pack, "abstention_decision", None)
            )

            is_abstained = False
            abstention_reason = None
            if abstention_decision is not None:
                is_abstained = bool(getattr(abstention_decision, "abstained", False))
                abstention_reason = (
                    getattr(abstention_decision, "abstention_reason", None)
                    if is_abstained else None
                )
            elif packet is not None:
                is_abstained = bool(getattr(packet, "abstention_required", False))
                abstention_reason = (
                    getattr(packet, "abstention_reason", None)
                    if is_abstained else None
                )
            elif getattr(context_pack, "abstained", False):
                is_abstained = True
                abstention_reason = getattr(context_pack, "abstention_reason", None)

            # --- F0-2 FIX: fail-closed en provenance. Nunca fabricar source_id ni doc_hash ---
            citations = []
            raw_chunks = (
                getattr(context_pack, "chunks", None)
                or getattr(context_pack, "packaged_units", None)
                or getattr(context_pack, "citations", None)
                or getattr(packet, "evidence_items", None)
                or []
            )
            for i, chunk in enumerate(raw_chunks):
                if isinstance(chunk, dict):
                    citations.append({
                        "id": chunk.get("id", f"E{i+1}"),
                        "citation_id": chunk.get("citation_id", f"E{i+1}"),
                        "source_id": chunk.get("source_id"),
                        "source_title": chunk.get("source_title") or chunk.get("source_id", "Documento Canónico"),
                        "page": chunk.get("page") or chunk.get("page_start", 1),
                        "page_start": chunk.get("page_start"),
                        "page_end": chunk.get("page_end"),
                        "chunk_text": chunk.get("chunk_text") or chunk.get("content", ""),
                        "chunk_id": chunk.get("chunk_id"),
                        "relevance_score": chunk.get("relevance_score", 0.85),
                        "doc_hash": chunk.get("doc_hash"),
                        "authority_weight": chunk.get("authority_weight", 1.0),
                        "namespace": chunk.get("namespace", "E"),
                    })
                    continue

                unit = getattr(chunk, "unit", None)
                source_id = getattr(chunk, "source_id", None) or (getattr(unit, "source_id", None) if unit else None)
                doc_hash = (
                    getattr(chunk, "doc_hash", None)
                    or getattr(chunk, "source_sha256", None)
                    or getattr(chunk, "document_hash", None)
                    or (getattr(unit, "doc_hash", None) if unit else None)
                    or None
                )
                citations.append({
                    "id": getattr(chunk, "id", f"E{i+1}"),
                    "citation_id": getattr(chunk, "citation_id", f"E{i+1}"),
                    "source_id": source_id,
                    "source_title": getattr(chunk, "source_title", source_id or "Documento Canónico"),
                    "page": getattr(chunk, "page", None) or getattr(chunk, "page_start", None) or (getattr(unit, "page_start", None) if unit else 1),
                    "page_start": getattr(chunk, "page_start", None) or (getattr(unit, "page_start", None) if unit else None),
                    "page_end": getattr(chunk, "page_end", None) or (getattr(unit, "page_end", None) if unit else None),
                    "chunk_text": getattr(chunk, "chunk_text", None) or getattr(chunk, "content", ""),
                    "chunk_id": getattr(chunk, "chunk_id", None) or (getattr(unit, "unit_id", None) if unit else None),
                    "relevance_score": getattr(chunk, "relevance_score", 0.85),
                    "doc_hash": doc_hash,
                    "authority_weight": getattr(chunk, "authority_weight", 1.0),
                    "namespace": getattr(chunk, "namespace", "E"),
                    "author": getattr(chunk, "author", "") or "",
                    "section": getattr(chunk, "section", "") or getattr(chunk, "section_path", "") or "",
                    "epistemic_role": getattr(chunk, "epistemic_role", None) or resolve_epistemic_role(
                        source_id=source_id or "",
                        source_title=getattr(chunk, "source_title", "") or "",
                        author=getattr(chunk, "author", "") or "",
                        notebook_id=getattr(self.contract, "notebook_id", "") or "",
                    ),
                })

            # --- F2-1 FIX: facet_coverage desde EvidenceCoverageEvaluator o report ---
            coverage_evaluator = getattr(context_pack, "coverage_evaluator", None)
            facet_coverage = {}
            if coverage_evaluator and hasattr(coverage_evaluator, "get_states"):
                facet_coverage = {
                    facet: getattr(state, "value", str(state))
                    for facet, state in coverage_evaluator.get_states().items()
                }
            else:
                cov_report = getattr(context_pack, "coverage_report", None) or (getattr(packet, "coverage_report", None) if packet else None)
                if cov_report and hasattr(cov_report, "coverage"):
                    for item in cov_report.coverage:
                        name = getattr(item, "sub_query_text", getattr(item, "sub_query_id", "facet"))
                        status_val = getattr(getattr(item, "status", None), "value", str(getattr(item, "status", "MISSING")))
                        facet_coverage[name] = status_val

            yield StreamEvent(
                event_type="evidence_manifest",
                payload={
                    "citations": citations,
                    "facet_coverage": facet_coverage,
                    "abstained": is_abstained,
                    "abstention_reason": abstention_reason,
                },
            )

            # Signal phase completion with available next phases
            yield StreamEvent(
                event_type="phase_complete",
                payload={
                    "completed_phase": phase.phase_id,
                    "tokens_produced": token_count,
                    "next_phases": self._get_available_next_phases(phase.phase_id),
                    "code_allowed": phase.code_allowed,
                },
            )

        except asyncio.CancelledError:
            # Refinamiento 3: User aborted generation from UI
            # Do NOT save partial output in PhaseHistory; report clean stream_aborted
            yield StreamEvent(
                event_type="stream_aborted",
                payload={
                    "phase": phase.phase_id,
                    "reason": "USER_ABORTED_OR_DISCONNECTED",
                    "tokens_generated_before_abort": token_count,
                },
            )
            raise
