"""Structured Response Pipeline (Fase 5.8 / Refinamientos 1 & 3).

Orchestrates multi-phase pedagogical generation with independent token budgets,
continuous PhaseHistory accumulation across phases, SocraticGuard rolling buffer,
and robust cancellation (abort) handling.
"""

import asyncio
from datetime import datetime, timezone
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Sequence
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.socratic_guard import SocraticGuard
from study_engine.pedagogy.command_parser import parse_student_command

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

    # 1. Mermaid / Diagramas de flujo
    if re.search(r"\b(?:mermaid|diagrama(?:\s+de\s+flujo)?(?:\s+en\s+mermaid)?)\b", q):
        directives["mermaid"] = (
            "- DIAGRAMA DE FLUJO EN MERMAID (OBLIGATORIO):\n"
            "  Generá un bloque de código ```mermaid con sintaxis válida (`graph TD` o `flowchart TD`).\n"
            "  El diagrama debe modelar claramente los nodos de entrada, decisiones lógicas/bifurcaciones (Fail-Fast), "
            "bucles de validación y estados finales de aceptación o rechazo."
        )

    # 2. Pytest / Pruebas Automatizadas
    if re.search(r"\b(?:pytest|tests?|pruebas?(?:\s+unitarias|\s+automatizadas)?|suite\s+de\s+pruebas|bater[ií]a\s+de\s+pruebas)\b", q):
        directives["pytest"] = (
            "- BATERÍA DE PRUEBAS AUTOMATIZADAS CON PYTEST (OBLIGATORIA):\n"
            "  Generá un bloque completo de pruebas ejecutables en ```python usando `import pytest` (o casos de prueba asertivos en el lenguaje destino).\n"
            "  La suite debe estructurarse con funciones de test claras y descriptivas:\n"
            "    * `test_happy_path_*`: Entradas válidas estándar y casos canónicos.\n"
            "    * `test_edge_cases_*`: Valores límite y casos extremos (ej. valores mínimos, máximos, delimitadores).\n"
            "    * `test_invalid_inputs_*`: Entradas malformadas, fuera de rango, tipos incorrectos o vectores de ataque."
        )

    # 3. Código C (Para cuadernos de Lenguajes C o SO2)
    if re.search(r"\b(?:c[oó]digo(?:\s+en|\s+de)?\s+c\b|en\s+c\b|programa\s+c\b)", q) or (notebook_id and "lenguajes" in notebook_id and "python" not in q and ("código" in q or "codigo" in q or "programa" in q)):
        directives["c_code"] = (
            "- CÓDIGO C ESTÁNDAR Y DEFENSIVO (OBLIGATORIO):\n"
            "  Generá la implementación completa en un bloque ```c con:\n"
            "    * Headers canónicos (`#include <stdio.h>`, `#include <stdlib.h>`, etc.) y prototipos de función.\n"
            "    * Validación estricta de punteros nulos (`NULL`) y límites de buffer en memoria.\n"
            "    * Manejo defensivo de valores de retorno y liberación de memoria dinámica sin fugas."
        )
    # 4. Código SQL (Para cuadernos de Bases de Datos / STD)
    elif re.search(r"\b(?:c[oó]digo(?:\s+en|\s+de)?\s+sql|consulta\s+sql|en\s+sql|query\s+sql|script\s+sql)\b", q) or (notebook_id and "std" in notebook_id and "python" not in q and ("sql" in q or "consulta" in q or "tabla" in q)):
        directives["sql_code"] = (
            "- CONSULTA O ESQUEMA SQL (OBLIGATORIO):\n"
            "  Generá las sentencias en un bloque ```sql estructurado con:\n"
            "    * Sintaxis SQL estándar, cláusulas declarativas limpias e integridad referencial.\n"
            "    * Parametrización defensiva (Prepared Statements) contra vectores de SQL Injection."
        )
    # 5. Código Python / Implementación general
    elif re.search(r"\b(?:c[oó]digo(?:\s+en|\s+de)?\s+python|en\s+python|implementaci[oó]n(?:\s+en\s+python)?|funci[oó]n\s+python|script\s+python|c[oó]digo\s+(?:python\s+)?con\s+tests|c[oó]digo\s+ejecutable|implementaci[oó]n)\b", q):
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
    if re.search(r"\b(?:pseudoc[oó]digo|pseudocode)\b", q):
        directives["pseudocode"] = (
            "- PSEUDOCÓDIGO ESTRUCTURADO (OBLIGATORIO):\n"
            "  Diseñá el algoritmo en pseudocódigo claro (estilo Joyanes Aguilar / Spraul) en un bloque ```text o ```pseudocode.\n"
            "  Usá nombres declarativos en español, control de flujo estructurado (SI/SINO/MIENTRAS/PARA) y comentarios sobre invariantes."
        )

    return directives


ICONIC_VULNERABILITIES: Dict[str, Dict[str, str]] = {
    "buffer_overflow": {
        "case": "Morris Worm (1988)",
        "description": "Primer gusano de Internet que explotó un buffer overflow en gets() de fingerd",
        "impact": "Infectó el 10% de las computadoras conectadas a ARPANET/Internet en esa época.",
    },
    "out_of_bounds_read": {
        "case": "Heartbleed (2014, CVE-2014-0160)",
        "description": "Falla de validación de longitud en OpenSSL TLS Heartbeat que permitía leer 64KB de memoria adyacente",
        "impact": "Filtró claves privadas SSL/TLS, credenciales y sesiones de millones de servidores web.",
    },
    "race_condition": {
        "case": "Dirty COW (CVE-2016-5195) / TOCTOU",
        "description": "Condición de carrera en el subsistema de memoria Copy-On-Write del kernel Linux",
        "impact": "Permitió escalamiento local de privilegios a root sin dejar rastro en logs de auditoría.",
    },
    "integer_overflow": {
        "case": "Ariane 5 Flight 501 (1996)",
        "description": "Conversión de un flotante de 64 bits a entero con signo de 16 bits sin verificación de límites",
        "impact": "Autodestrucción del cohete a los 37 segundos del lanzamiento con pérdida de 370M USD.",
    },
    "null_dereference": {
        "case": "Ataques de Kernel NULL Pointer Dereference (CVE-2009-2692)",
        "description": "Mapeo de la página cero (mmap_min_addr) para ejecutar shellcode en anillo 0 al desreferenciar puntero nulo",
        "impact": "Compromiso total del kernel del sistema operativo mediante vectores locales.",
    },
    "sql_injection": {
        "case": "Inyección SQL y Bypass de Autenticación (Tautología ' OR '1'='1)",
        "description": "Concatenación no parametrizada de strings donde el motor SQL confunde datos del usuario con instrucciones de control",
        "impact": "Exfiltración masiva de credenciales y volcado no autorizado de bases de datos relacionales en producción.",
    },
    "command_injection": {
        "case": "finger.cgi y Shell Injection (Stallings Cap. 11 / Morris / Perl CGI)",
        "description": "Inyección de metacaracteres (; | &&) en llamadas al sistema (os.system / exec) sin sanitización de frontera",
        "impact": "Ejecución remota de comandos del sistema operativo (RCE) con los privilegios del servidor web.",
    },
    "tdd_edge_cases": {
        "case": "Heartbleed (CVE-2014-0160) por ausencia de test de longitud de frontera",
        "description": "Falta de un test unitario que verificara la coincidencia entre la longitud declarada y el tamaño real del búfer en OpenSSL Heartbeat",
        "impact": "Lectura masiva no autorizada de 64KB de memoria RAM contigua filtrando claves privadas SSL y credenciales en todo el mundo.",
    },
    "parser_differential": {
        "case": "Parser Differential en Validación de IP (CVE-2021-29921 / inet_addr Octal Bypass)",
        "description": "Ambigüedad semántica entre bibliotecas de alto nivel (Python/Go/Rust) que parsean octetos como decimal vs bibliotecas C del kernel (inet_addr) que interpretan ceros a la izquierda (ej. '010.0.0.1') en base 8 (octal)",
        "impact": "Bypass de firewalls, WAFs y filtros de red permitiendo Server-Side Request Forgery (SSRF), IP Spoofing y enrutamiento arbitrario no autorizado.",
    },
    "unicode_injection": {
        "case": "Unicode Digit Bypass e Incompatibilidad de Encoding (str.isdigit() vs ASCII)",
        "description": "Aceptación de caracteres numéricos de alfabetos extranjeros (arábigo, devanagari) que str.isdigit() considera dígitos válidos en Python, pero que provocan desbordamientos o crashes al ser consumidos por sockets del sistema operativo",
        "impact": "Denegación de Servicio (DoS), desincronización de estado y vulnerabilidades de inyección en capas de transporte.",
    },
}


def inject_threat_intel(user_query: str) -> str:
    """Inyecta un caso histórico real y emblemático si la consulta involucra vulnerabilidades de bajo nivel."""
    q_lower = user_query.lower()
    selected_key = None
    if any(w in q_lower for w in ("parser differential", "octal", "ceros a la izquierda", "leading zero", "ipv4", "direccion ip", "dirección ip")):
        selected_key = "parser_differential"
    elif any(w in q_lower for w in ("unicode", "is_digit", "isdigit", "devanagari", "arábigo", "arabigo")):
        selected_key = "unicode_injection"
    elif any(w in q_lower for w in ("tdd", "test driven", "pruebas unitarias", "leyes del tdd", "edge cases", "testing defensivo")):
        selected_key = "tdd_edge_cases"
    elif any(w in q_lower for w in ("sql injection", "inyeccion sql", "inyección sql", "sqli", "prepared statement")):
        selected_key = "sql_injection"
    elif any(w in q_lower for w in ("command injection", "inyeccion de comandos", "inyección de comandos", "os command", "shell injection")):
        selected_key = "command_injection"
    elif any(w in q_lower for w in ("out of bound", "fuera de limites", "fuera de límites", "cortocircuito", "short-circuit", "lectura fuera")):
        selected_key = "out_of_bounds_read"
    elif any(w in q_lower for w in ("buffer overflow", "desbordamiento de buffer", "desbordamiento de búfer", "desbordamiento de pila")):
        selected_key = "buffer_overflow"
    elif any(w in q_lower for w in ("integer overflow", "desbordamiento de entero", "desbordamiento aritmético")):
        selected_key = "integer_overflow"
    elif any(w in q_lower for w in ("condicion de carrera", "condición de carrera", "toctou", "race condition")):
        selected_key = "race_condition"
    elif any(w in q_lower for w in ("puntero nulo", "null pointer", "desreferencia")):
        selected_key = "null_dereference"

    if selected_key and selected_key in ICONIC_VULNERABILITIES:
        info = ICONIC_VULNERABILITIES[selected_key]
        return (
            f"=== ANCLAJE A THREAT INTEL Y CASOS HISTÓRICOS REALES ===\n"
            f"- Conectá la vulnerabilidad teórica con el incidente real: **{info['case']}**.\n"
            f"- Contexto: {info['description']}.\n"
            f"- Impacto en el mundo real: {info['impact']}.\n"
            "- Explicá brevemente cómo la mala validación en el código o bucle habilita este vector de ataque concreto.\n"
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
        "=== DIRECTIVA DE SÍNTESIS DIALÉCTICA TRI-CAPA (ESTILO FEYNMAN + RIGOR) ===\n"
        "Estructurá tu respuesta integrando orgánicamente las siguientes tres dimensiones:\n"
        f"1. **Capa 1: Intuición Conceptual y Analogía{ped_note}**:\n"
        "   - Explicá la idea fundamental con estilo apasionado y directo (Richard Feynman).\n"
        "   - Usá una analogía vívida del mundo real ANTES de las definiciones formales.\n"
        f"2. **Capa 2: Mecanismo y Formalismo Riguroso{form_note}**:\n"
        "   - Explicá la teoría rigurosa, modelos matemáticos, algoritmos o invariantes formales.\n"
        "   - Respaldá con precisión terminológica y citas explícitas de las fuentes formales.\n"
        f"3. **Capa 3: Nivel de Máquina e Implementación Práctica{tech_note}**:\n"
        "   - Aterrizá el concepto a la realidad física: impacto en memoria, syscalls, registros o código idiomático.\n\n"
        "=== CIERRE SOCRÁTICO OBLIGATORIO ===\n"
        "- Toda respuesta DEBE culminar con una pregunta socrática contextual desafiante que interrogue el modelo mental del estudiante (ej: '¿Qué pasaría si...?', '¿Por qué preferimos X en lugar de Y?').\n"
    )
    return instruction


RESPONSE_MODES: Dict[str, Dict[str, Any]] = {
    "explain_concept": {"layers": 3, "socratic": True, "max_words": 400, "format": "tri_layer"},
    "resolve_misconception": {"layers": 3, "socratic": True, "max_words": 1500, "format": "epistemic_scaffolding"},
    "compare": {"layers": 0, "socratic": True, "max_words": 300, "format": "table"},
    "give_example": {"layers": 0, "socratic": False, "max_words": 500, "format": "code"},
    "simplify": {"layers": 1, "socratic": False, "max_words": 200, "format": "feynman_simple"},
    "evaluate_code": {"layers": 3, "socratic": True, "max_words": 2500, "format": "forensic_audit"},
    "deep_dive": {"layers": 3, "socratic": True, "max_words": 2500, "format": "exhaustive_tri_layer"},
    "quick_answer": {"layers": 0, "socratic": False, "max_words": 100, "format": "concise"},
}


def classify_pedagogical_intent(user_query: str) -> str:
    """Clasifica la intención pedagógica de la consulta para seleccionar el RESPONSE_MODE óptimo (Fix S4.1)."""
    q = user_query.strip().lower()

    # 1. Quick answer: muy breve / definición rápida
    if any(p in q for p in (
        "en una frase", "en pocas palabras", "definicion rapida", "definición rápida",
        "respuesta rapida", "respuesta rápida", "brevemente", "en un renglon", "en un renglón",
        "directo al grano", "sólo decime si", "solo decime si"
    )):
        return "quick_answer"

    # 2. Evaluate / Audit code: auditoría forense o revisión de código/algoritmo
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
        "compara", "comparar", "diferencia entre", "diferencias entre", " vs ", "versus",
        "cuadro comparativo", "tabla comparativa", "frente a", "contrastar", "en que se diferencia", "en qué se diferencia"
    )):
        return "compare"

    # 4. Give example: código práctico / ejemplo
    if any(p in q for p in (
        "dame un ejemplo", "dar un ejemplo", "mostrame un ejemplo", "ejemplo practico",
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
        "todos los detalles", "analisis riguroso a fondo", "análisis riguroso a fondo",
        "explicame mas", "explicamelo mas", "explicá más", "explica más", "explayate",
        "explayate más", "más detalles", "mas detalles", "a fondo", "quiero mas profundidad",
        "quiero más profundidad"
    )):
        return "deep_dive"

    # 7. Resolve misconception / Duda conceptual o conflicto epistémico
    if any(p in q for p in (
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
        "no me queda claro por qué", "no me queda claro porque",
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
) -> str:
    """Construye la directiva pedagógica específica según el modo de respuesta seleccionado (Fix S4.1)."""
    mode_config = RESPONSE_MODES.get(mode, RESPONSE_MODES["explain_concept"])
    layers = mode_config.get("layers", 3)
    fmt = mode_config.get("format", "tri_layer")

    if mode == "evaluate_code" or fmt in ("forensic_audit", "review"):
        return (
            "=== DIRECTIVA DE AUDITORÍA FORENSE DE CÓDIGO Y CIBERDEFENSA (PROTOCOLO TALOS) ===\n"
            "El estudiante te ha presentado una solución o código para auditar. "
            "NUNCA comiences reescribiendo la solución desde cero sin antes realizar una auditoría forense rigurosa, explícita y bug-por-bug del código del alumno.\n\n"
            "ESTRUCTURA OBLIGATORIA DE LA AUDITORÍA FORENSE:\n\n"
            "### 1. Auditoría Técnica y Análisis de Bugs (Diagnóstico Forense Específico)\n"
            "- **¿Qué está bien?**: Reconocé en 2 o 3 viñetas concisas qué aspectos estructurales o heurísticos de la solución del estudiante están correctamente encaminados (ej. separación en tokens, comprobación básica de longitud).\n"
            "- **¿Qué está incompleto, mal o vulnerable? (Edge Cases y Vulnerabilidades de Ciberseguridad)**:\n"
            "  Desglosá CADA falla de forma individual, con nombre técnico, citando la línea o fragmento vulnerable exacto:\n"
            "  * **[Nombre Técnico del Bug / Vector]**: (ej: 'Ceros a la izquierda -> Parser Differential / Ambigüedad Octal vs Decimal (CVE-2021-29921)', 'Inyección de Dígitos Unicode no ASCII en str.isdigit()', 'Agotamiento de Memoria en Heap por split() sin Cláusula Bouncer de longitud previa (Riesgo DoS)').\n"
            "  * **El Bug en el código**: Citá el fragmento exacto del alumno donde reside la falla.\n"
            "  * **Mecanismo de falla**: Explicá qué ocurre ante entradas maliciosas concretas (ej: qué retorna la función ante '010.0.0.1', '192.168.1.١', o una cadena de 10 MB de puntos).\n"
            "  * **Peligro en Ciberseguridad / CVE real**: Explicá cómo las librerías C de bajo nivel del sistema operativo (ej. inet_addr) o los sockets procesan este valor, y cómo un atacante puede eludir firewalls (WAF), provocar SSRF o voltear el servicio.\n\n"
            "### 2. Anatomía en Silicio y Memoria RAM (La Firma TALOS)\n"
            "- Bajá al hardware: mostrá cómo la CPU, la memoria RAM (Heap vs Stack), los registros de propósito general (RSI/RDI para punteros de strings), la ALU y las banderas de registro FLAGS (ZF, CF, SF) procesan la entrada y dónde la falla del código se manifiesta a nivel de máquina.\n"
            "- Incluí un diagrama visual limpio en bloque ```text con cajas Unicode (┌, ├, └, │, ─) representando la memoria o búfer en el Heap/Stack.\n\n"
            "### 3. Entregables de Ingeniería Certificados (Solución Defensiva)\n"
            "- **Contratos Formales PRE / POST**: Precondiciones estrictas (tipos, límites físicos, codificación) y Postcondiciones (invariantes de formato, no-mutabilidad, garantías de retorno).\n"
            "- **Diagrama de Flujo en Mermaid**: Diagrama visual estructurado (flowchart TD o graph TD) modelando el flujo de decisiones defensivo Fail-Fast.\n"
            "- **Pseudocódigo Estructurado**: Notación algorítmica rigurosa (tipo Joyanes / UPSAM) con cláusulas de guarda explícitas.\n"
            "- **Código de Producción con Fixes Explícitos**: Código limpio, fuertemente tipado (Type Hints) y con funciones auxiliares defensivas para evitar trampas sutiles del lenguaje.\n"
            "  * REGLA DE ORO DE SEGURIDAD EN PYTHON: NUNCA uses o aceptes 'str.isdigit()' para validar campos estrictamente decimales o de red (IPv4, puertos, IDs). En Python, 'str.isdigit()' retorna True para caracteres numéricos Unicode no ASCII de otros alfabetos (como arábigo '١٢٣' o devanagari '۱۲۳'). Implementá explícitamente una función auxiliar segura como 'es_digito_ascii(s)' usando 'all(\"0\" <= c <= \"9\" for c in s)' o 'c in string.digits'.\n"
            "  * CLÁUSULA BOUNCER DE FRONTERA DE LONGITUD (Fail-Fast Anti-DoS): En validación de IPv4 u otros protocolos, siempre aplicá una guardia de longitud física previa (ej. '7 <= len(ip) <= 15') ANTES de llamar a 'split()', para evitar ataques de agotamiento de memoria Heap ante strings maliciosos gigantes.\n"
            "  * AMBIGÜEDAD OCTAL (CVE-2021-29921 / Parser Differential): Explicá y bloqueá rigurosamente cualquier cero no significativo a la izquierda (ej. '010.0.0.1' o '192.168.01.1'), ya que las funciones C del sistema operativo (inet_addr) lo interpretan en base 8 (octal), habilitando bypass de firewalls y SSRF.\n"
            "- **Suite de Pruebas Automatizadas (Pytest)**: Batería exhaustiva de tests unitarios que incluya específicamente un test dedicado para cada vulnerabilidad y bug detectado en la auditoría:\n"
            "  * test_casos_felices_validos\n"
            "  * test_bloqueo_ceros_a_la_izquierda_parser_differential\n"
            "  * test_bloqueo_digitos_unicode_no_ascii\n"
            "  * test_octetos_fuera_de_rango\n"
            "  * test_estructura_incorrecta_y_puntos\n"
            "  * test_fronteras_de_longitud_y_tipos_invalidos (strings gigantes DoS, None, enteros)\n\n"
            "### 4. Cierre Socrático de Arquitectura de Misión Crítica\n"
            "- Rematá con una pregunta socrática de alto nivel de sistemas que confronte el rendimiento y la seguridad en entornos reales (ej. procesamiento Zero-Copy, kernel-bypass con DPDK/eBPF a 10M pps, o concurrencia multihilo).\n"
        )

    if mode == "resolve_misconception" or fmt == "epistemic_scaffolding":
        return (
            "=== DIRECTIVA DE RESOLUCIÓN DE CONFLICTO EPISTÉMICO Y ANDAMIAJE SOCRÁTICO (PROTOCOLO TALOS) ===\n"
            "El estudiante manifiesta una confusión o cuestiona una regla técnica basándose en su intuición previa "
            "(ej. 'en matemáticas 010 es 10, ¿por qué decís que es un peligro?').\n"
            "Tu misión como tutor epistémico senior es desarmar la confusión con empatía cognitiva, rigor formal y aterrizaje en silicio.\n\n"
            "ESTRUCTURA OBLIGATORIA DE LA RESPUESTA:\n\n"
            "### 1. Validación Cognitiva y Desarme de la Frustración (Empatía Pedagógica)\n"
            "- Comenzá reconociendo explícitamente que la intuición del alumno es 100% correcta en su propio marco de referencia:\n"
            "  * 'Tenés toda la razón desde la matemática decimal pura: en la vida diaria (base 10), un cero a la izquierda no altera la magnitud (010 = 10).'\n"
            "- Aclarale de inmediato que el problema surge cuando cruzamos la frontera hacia el software de sistemas y el silicio, donde rigen convenciones históricas de bajo nivel.\n\n"
            "### 2. Analogía Intrínseca al Mecanismo Real (Regla de Oro: Modelar el Mecanismo, No Metáforas Vacías)\n"
            "- NUNCA uses analogías desconectadas (como molinetes de boliche o aduanas si el tema es conversión de bases numéricas o tipos de datos).\n"
            "- La analogía DEBE modelar exactamente el agrupamiento/conteo por bloques:\n"
            "  * Ejemplo para Base 8 / Octal: Imaginate un restaurante donde las mesas están organizadas en filas de 8 mesas (o un odómetro que solo tiene dígitos del 0 al 7, o cajas que cierran al llegar a 8 unidades). Si alguien pide la 'Mesa 010', el mozo que cuenta en filas de 8 entiende: 1 fila completa (8 mesas) + 0 sueltas = Mesa 8 real. Vos, pensando en base 10, esperabas la mesa 10.\n\n"
            "### 3. Rigor Matemático y Tabla de Conteo\n"
            "- Mostrá la tabla de correspondencia entre el sistema Decimal (Base 10) y el sistema Octal (Base 8) en el punto de divergencia:\n"
            "  * Decimal 7 -> Octal 07\n"
            "  * Decimal 8 -> Octal 010 (¡aquí ocurre el salto de orden de magnitud!)\n"
            "  * Decimal 9 -> Octal 011\n"
            "  * Decimal 10 -> Octal 012\n"
            "- Demostrá la fórmula formal de polinomios de potencias en LaTeX:\n"
            "  $$\\text{Octal } 010 = (0 \\times 8^2) + (1 \\times 8^1) + (0 \\times 8^0) = 8 \\text{ decimal}$$\n\n"
            "### 4. La Viñeta del Ataque Real: Cómo se Explota la Ambigüedad (Parser Differential / CVE-2021-29921)\n"
            "- NO dejes el peligro como un enigma abstracto para que el alumno lo adivine; mostrá el cuadro de ataque con dos componentes hablando entre sí:\n"
            "  1. Tu WAF o Firewall en Python: usa `int('010')`, ve el número 10 en decimal. Como la IP 10.0.0.1 no está en la lista negra, permite el paso del paquete.\n"
            "  2. La Pila de Red del Sistema Operativo / Router (escrito en C con `inet_addr` o `inet_aton` de POSIX): lee el '0' inicial y asume base octal. Interpreta '010' como 8, y conecta directamente a la IP restringida 8.0.0.1 (servidor interno protegido / SSRF).\n"
            "  - Conclusión: El atacante elude el firewall explotando la ambigüedad sintáctica entre capas.\n\n"
            "### 5. Anatomía en Silicio y Memoria RAM (La Firma TALOS)\n"
            "- Diagrama ASCII de memoria RAM (búfer de entrada, puntero de lectura, registros de CPU RSI/RDI, y evaluación en la ALU).\n"
            "- Explicá cómo la función del kernel lee byte a byte desde el puntero y activa la rama de decodificación octal ante el byte ASCII '0' (0x30).\n\n"
            "### 6. Patrón Algorítmico Defensivo y Código / Pseudocódigo\n"
            "- Mostrá el algoritmo en pseudocódigo o código Python seguro que implementa la regla de Fail-Fast: rechazar octetos con ceros a la izquierda innecesarios (`len(p) > 1 and p[0] == '0'`).\n\n"
            "### 7. Pregunta Socrática de Verificación Guiada\n"
            "- Cerrá con una pregunta accesible para que el estudiante verifique que consolidó el concepto:\n"
            "  * 'Si una herramienta de red envía un paquete a 012.0.0.1, y el sistema operativo interpreta los octetos con cero inicial en base 8: ¿a qué dirección IP en formato decimal se conectará en realidad el kernel?'\n"
        )

    if layers == 3:
        classified = classify_sources_by_role(context_pack, notebook_id)
        ped_note = f" (Fuentes: {', '.join(classified['pedagogical'])})" if classified["pedagogical"] else ""
        form_note = f" (Fuentes: {', '.join(classified['formal'])})" if classified["formal"] else ""
        tech_note = f" (Fuentes: {', '.join(classified['technical'])})" if classified["technical"] else ""

        depth_hint = " Desarrollá con máxima exhaustividad enciclopédica (800-1500 palabras)." if mode == "deep_dive" else " Desarrollá con profundidad sólida y analítica (mínimo 600 palabras de prosa explicativa)."
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
            "- **RIGOR EN LA ELECCIÓN DE ESTRUCTURAS DE CONTROL**: Al explicar o diseñar algoritmos, seleccioná siempre la estructura canónica y óptima según la naturaleza del problema (ej: si la cantidad de iteraciones es conocida de antemano o acotada por un rango, priorizá la estructura `PARA ... HASTA ... [PASO ...] HACER` (`for`), contrastándola educativamente con el `MIENTRAS` manual y explicando por qué el `PARA` es la mejor práctica algorítmica y de ingeniería).\n"
            "- **DIAGRAMAS VISUALES INTERACTIVOS EN MERMAID**: Siempre que modeles flujos lógicos, bifurcaciones de control, estados de CPU o decisiones, generá un bloque ```mermaid (`flowchart TD` o `graph TD`) con sintaxis válida. El frontend lo renderiza nativamente como un diagrama vectorial interactivo.\n"
            "- **DIAGRAMA FÍSICO DE MEMORIA CON CAJAS UNICODE**: Para mapas de memoria (Stack Frames, buffers contiguos, registros x86), incluí un esquema visual limpio en bloque ```text utilizando caracteres de dibujo de caja (┌, ├, └, │, ─).\n"
            "- **EJEMPLOS CON SYNTAX HIGHLIGHTING (CÓDIGO REAL EJECUTABLE)**: Además del pseudocódigo formal, es OBLIGATORIO incluir bloques de código real en el lenguaje del cuaderno (```python para fase0-soc, ```c o ```python para fadena-lenguajes/so2) con comentarios claros inline explicando la precondición, la cláusula de guarda y la invocación segura.\n"
            "- **TABLAS COMPARATIVAS DE CONCEPTOS O NIVELES**: Siempre que compares conceptos (ej: Stack vs Heap, PARA vs MIENTRAS, Valor vs Referencia, o Pirámide de Testing), incluí una tabla Markdown compacta y clara.\n"
            "- **TONO RIOPLATENSE NATURAL Y DIRECTO**: Utilizá giros cercanos y naturales ('che', 'fijate', 'mirá cómo conmuta en la RAM', 'vamos paso a paso desarmando el silicio') manteniendo rigurosa seriedad técnica y sin saludos ni halagos iniciales.\n\n"
            "DIMENSIONES CONCEPTUALES OBLIGATORIAS:\n"
            f"- **Dimensión Intuitiva y Analógica (Estilo 'Feynman de Barrio'){ped_note}**:\n"
            "   * Creá libremente una analogía cotidiana, original y tangible que encaje con exactitud en la física del problema.\n"
            "   * REGLA DE ORO DE ANALOGÍAS: La analogía DEBE modelar el mecanismo físico/matemático real del concepto. Para bases numéricas o conteo, usá agrupamientos o cajas por bloques; para memoria/buffers, casilleros delimitados; para concurrencia, recursos físicos compartidos; para redes, logística o correspondencia. NUNCA fuerces molinetes o aduanas si el concepto es numérico o de tipos de datos.\n"
            "   * Explicá la idea intuitiva de forma directa antes de la formalización.\n"
            f"- **Dimensión Formal y Algorítmica{form_note}**:\n"
            "   * Teoría rigurosa, modelos matemáticos, invariantes y citas explícitas [E#].\n"
            "   * Mostrá la estructura canónica en pseudocódigo formal estructurado (tipo Joyanes / Cátedra FaDeNA).\n"
            f"- **Dimensión Física y de Máquina{tech_note}**:\n"
            "   * Bajá al silicio: transistores CMOS, ALU, instrucciones x86 (LOOP, CMP, TEST, JZ, JNZ), registros y banderas FLAGS.\n"
            "- **Capas Adicionales de Seguridad / Ciberdefensa**: Si el tema lo amerita, analizá la superficie de ataque o el impacto en disponibilidad (DoS por bucles infinitos, Buffer Overflow, etc.) anclándolo a incidentes reales con precisión forense.\n"
            "- **CIERRE SOCRÁTICO OBLIGATORIO**: Toda respuesta conceptual o técnica DEBE culminar con una pregunta socrática desafiante o un mini-escenario de borde (edge case) que invite al alumno a pensar y responder (ej: '¿Qué pasaría con la bandera ZF si el usuario ingresa N = 0?', '¿Por qué un compilador moderno reemplazaría un bucle contado por desenrollado (loop unrolling)?').\n"
        )
    elif layers == 1:
        return (
            "=== DIRECTIVA DE SÍNTESIS SIMPLIFICADA (ESTILO FEYNMAN ACCESIBLE) ===\n"
            "- Explicá la intuición central usando una analogía cotidiana directa y vívida.\n"
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
    ) -> str:
        """Assemble the specialized prompt for this phase with PhaseHistory, intent routing, and BKT adaptation."""
        predecessor_context = self.history.format_predecessors_context()
        active_mode = pedagogical_mode or classify_pedagogical_intent(user_query)

        # Phase prompt template formatting
        if active_mode == "evaluate_code":
            rendered_phase_instruction = (
                "AUDITORÍA FORENSE DE CÓDIGO DEL ESTUDIANTE: Analizá minuciosamente el código y la solución provista en la consulta. "
                "Identificá y señalá explícitamente cada bug, caso de borde omitido y riesgo de ciberseguridad antes de presentar la solución corregida. "
                "No comiences inventando analogías genéricas ni reescribiendo desde cero sin haber auditado primero los errores del alumno."
            )
        elif active_mode == "resolve_misconception":
            rendered_phase_instruction = (
                "RESOLUCIÓN DE CONFLICTO EPISTÉMICO Y ANDAMIAJE SOCRÁTICO: El estudiante expresa una duda o confronta un concepto "
                "basándose en su intuición previa (ej. '010 es igual a 10 en matemáticas, ¿por qué es un error?'). "
                "1. Validá de entrada su lógica previa para no frustrarlo ('Tenés razón en matemáticas decimales puras...'). "
                "2. Usá una analogía cotidiana que modele EXACTAMENTE el mecanismo físico real (ej. agrupamiento en filas de 8, odómetros de 8 posiciones), NUNCA analogías forzadas de molinetes. "
                "3. Explicá la divergencia semántica entre capas (abstracción matemática vs bajo nivel POSIX/C en silicio) con fórmulas y tablas. "
                "4. Mostrá la historia concreta del ataque o falla (ej. cómo el firewall ve 10 y el router ve 8 habilitando SSRF) ANTES de la pregunta socrática."
            )
        else:
            rendered_phase_instruction = phase.phase_prompt_template.format(
                user_query=user_query,
                concept=user_query,
            )

        notebook_id = getattr(self.contract, "notebook_id", "fase0-soc")
        structural_directives = extract_requested_structural_components(user_query, notebook_id=notebook_id)
        if active_mode in ("evaluate_code", "resolve_misconception") or any(k in structural_directives for k in ("python_code", "c_code", "sql_code", "pytest")):
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
        active_mode = pedagogical_mode or classify_pedagogical_intent(user_query)
        mode_config = RESPONSE_MODES.get(active_mode, RESPONSE_MODES["explain_concept"])

        mode_instruction = build_mode_specific_instruction(
            mode=active_mode,
            context_pack=context_pack,
            notebook_id=notebook_id,
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
        threat_intel_directive = inject_threat_intel(user_query)
        if threat_intel_directive:
            parts.append(threat_intel_directive)

        # 1.3 Checklist de entregables y componentes estructurales expresamente solicitados
        if structural_directives:
            directives_text = "\n\n".join(structural_directives.values())
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

        cmd = parse_student_command(user_query)
        if cmd is not None and cmd.is_structured:
            rules_block = (
                f"=== COMANDO ESTRUCTURADO DETECTADO: {cmd.command_type.value} ===\n"
                f"{cmd.template_instruction}\n\n"
                "REGLAS CRÍTICAS DE SALIDA:\n"
                "- NUNCA saludes ('Hola', 'Bienvenido', 'Saludos', etc.). Respondé directo a la consulta en la primera oración.\n"
                "- NUNCA halagues ('Excelente pregunta', 'Bien pensado', etc.).\n"
                "- Formato Markdown estricto (listas con guiones, negrita en términos clave, código inline ``, tablas y bloques de código).\n"
                f"- Extensión estructurada: hasta {cmd.max_words} palabras permitidas. Desarrollá cada sección paso a paso con chunking interno.\n"
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
                else "diagramas limpios en ```text con cajas Unicode (┌, ├, └, │, ─) o ```mermaid según corresponda"
            )
            rules_block = (
                "REGLAS CRÍTICAS DE SALIDA:\n"
                "- NUNCA saludes ('Hola', 'Bienvenido', 'Saludos', etc.). Respondé directo a la consulta en la primera oración.\n"
                "- NUNCA halagues ('Excelente pregunta', 'Bien pensado', etc.).\n"
                f"- Jerarquía visual Markdown nítida: organizá con subtítulos descriptivos (### y ####), listas con viñetas para enumerar registros/conceptos, código inline ``, bloques de código con syntax highlighting (```python o ```c) y {diagram_fmt}.\n"
                f"{extension_clause}\n"
                f"{socratic_rule}"
            )

        parts.append(
            f"=== CONSULTA DEL ESTUDIANTE ===\n{user_query}\n\n"
            f"=== INSTRUCCIÓN OBLIGATORIA PARA ESTA FASE ({phase.phase_id.upper()}) ===\n"
            f"{rendered_phase_instruction}\n\n"
            f"{rules_block}"
        )
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
    ) -> AsyncGenerator[StreamEvent, None]:
        """Generate response for a specific phase with streaming, guards, intent routing, and BKT adaptation.

        Refinamiento 3: Handles asyncio.CancelledError cleanly without corrupting PhaseHistory.
        Fase 2: Acepta recent_turns para memoria conversacional de corto plazo.
        """
        target_phase_id = requested_phase or "conceptual"
        phase = self.get_phase(target_phase_id)
        self.guard.reset()

        # Enmienda E5 & E25: Si el context_pack indica abstención por falta de fuentes canónicas,
        # emitir evento 'abstention' inmediatamente como PRIMER y ÚNICO evento sin phase_start ni invocar al LLM.
        # Nota: Si el backend es OfflinePedagogicalBackend, permitimos que proceda para emitir su respuesta offline.
        from study_engine.llm.offline_oracle import OfflinePedagogicalBackend
        is_offline_oracle = isinstance(self.llm, OfflinePedagogicalBackend)
        if context_pack is not None and getattr(context_pack, "abstained", False) and not is_offline_oracle:
            yield StreamEvent(
                event_type="abstention",
                payload={
                    "phase": phase.phase_id,
                    "abstained": True,
                    "reason": "TALOS se abstiene de responder: No hay evidencia verificada en las fuentes canónicas del cuaderno para fundamentar esta consulta.",
                    "suggested_action": "Consultá el catálogo de fuentes del cuaderno o reformulá la pregunta con términos del programa.",
                    "abstention_code": getattr(context_pack, "abstention_reason", "QUERY_OUT_OF_SCOPE"),
                },
            )
            return

        active_mode = pedagogical_mode or classify_pedagogical_intent(user_query)
        cmd = parse_student_command(user_query)
        target_notebook_id = getattr(self.contract, "notebook_id", None)
        structural_directives = extract_requested_structural_components(user_query, notebook_id=target_notebook_id)
        has_code_request = bool(any(k in structural_directives for k in ("python_code", "c_code", "sql_code", "pytest")))

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

        allow_code = (
            phase.code_allowed
            or has_code_request
            or (cmd is not None and cmd.command_type.value in ("TRADUCCION", "DAME_SOLUCION_COMPLETA"))
            or active_mode in ("give_example", "evaluate_code", "resolve_misconception")
        )
        effective_phase = ResponsePhase(
            phase_id=phase.phase_id,
            phase_prompt_template=phase.phase_prompt_template,
            max_tokens=effective_max_tokens,
            requires_user_approval=phase.requires_user_approval,
            code_allowed=allow_code,
        )

        system_prompt = f"{self.contract.base_system_prompt}\n\nFase actual: {phase.phase_id.upper()}."
        phase_user_prompt = self.build_phase_prompt(
            phase=phase,
            user_query=user_query,
            context_pack=context_pack,
            pedagogical_mode=active_mode,
            bkt_directive=bkt_directive,
            style_directive=style_directive,
            recent_turns=recent_turns,
        )

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
                )

                if guard_res.allowed:
                    accumulated_text += guard_res.emitted_token
                    yield StreamEvent(
                        event_type="phase_token",
                        payload={"phase": phase.phase_id, "token": guard_res.emitted_token},
                    )
                else:
                    guard_triggered = True
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
            audit_verdict = "APPROVED"
            if self.auditor is not None and not guard_triggered:
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
                    res_v = getattr(audit_res, "overall_verdict", getattr(audit_res, "verdict", "APPROVED"))
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
